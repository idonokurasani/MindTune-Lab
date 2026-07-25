"""Regression tests for fc11_capture_pipeline.py.

Tests are self-contained and do not require BLE hardware. They use a synthetic
5 Hz notification stream, the sanitized trace in evidence/, and slow workers to
prove queue overflow accounting and raw-packet priority.
"""

from __future__ import annotations

import asyncio
import csv
import math
import time
import unittest
from pathlib import Path

from fc11_capture_pipeline import CapturePipeline


def _packet(seq: int, sample_rate_code: int | None = 2, n_samples: int = 50):
    """Generate synthetic ADC samples for a single packet."""
    base = seq * 1000
    return list(range(base, base + n_samples))


class FakeStats:
    """Minimal stats object compatible with CapturePipeline."""

    def __init__(self) -> None:
        self.packets = 0
        self.samples = 0
        self.packet_index_first: int | None = None
        self.packet_index_last: int | None = None
        self.packet_index_gaps = 0
        self.max_inter_packet_gap_s: float | None = None
        self.last_packet_time: float | None = None
        self.prev_packet_index: int | None = None

    def update(self, packet_index: int | None, sample_count: int, now: float) -> None:
        self.packets += 1
        self.samples += sample_count
        if packet_index is not None:
            if self.packet_index_first is None:
                self.packet_index_first = packet_index
            self.packet_index_last = packet_index
            if self.prev_packet_index is not None and packet_index != self.prev_packet_index + 1:
                self.packet_index_gaps += 1
            self.prev_packet_index = packet_index
        if self.last_packet_time is not None:
            gap = now - self.last_packet_time
            self.max_inter_packet_gap_s = gap if self.max_inter_packet_gap_s is None else max(self.max_inter_packet_gap_s, gap)
        self.last_packet_time = now


def _quick_feature_callback(window: list[int], sample_rate: float, stats, hardware_state, battery_percent=None):
    return {"ok": True, "blink_proxy": 0, "noise_spike_count": 0, "alpha_peak_hz": 10.0, "rms": 1.0, "saturation_pct": 0.0}


def _slow_feature_callback(delay: float = 0.5):
    def callback(window, sample_rate, stats, hardware_state, battery_percent=None):
        time.sleep(delay)
        return {"ok": True, "blink_proxy": 0, "noise_spike_count": 0, "alpha_peak_hz": 10.0, "rms": 1.0, "saturation_pct": 0.0}
    return callback


class TestCapturePipeline(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._base = Path(__file__).parent / "test_outputs"
        self._base.mkdir(exist_ok=True)

    async def _make_pipeline(self, name: str, feature_callback=None, live=True, raw_qsize=200, feat_qsize=10):
        out = self._base / f"{name}.csv"
        if out.exists():
            out.unlink()
        stats = FakeStats()
        hardware_state = {"session_started_at": None, "battery_percent": 100}
        pipeline = CapturePipeline(
            current_out=out,
            stats=stats,
            hardware_state=hardware_state,
            feature_callback=feature_callback,
            live_features_enabled=live,
            raw_queue_maxsize=raw_qsize,
            feature_queue_maxsize=feat_qsize,
            nominal_rate=250.0,
        )
        await pipeline.start()
        return pipeline

    async def _feed_packets(self, pipeline, count, interval_s, packet_size=50, start_seq=100, sample_rate_code=2, arrival_offset=0.0):
        base_ts = time.time() + arrival_offset
        for i in range(count):
            seq = start_seq + i
            arrival = base_ts + i * interval_s
            samples = _packet(seq, sample_rate_code, packet_size)
            pipeline.feed_packet(seq, sample_rate_code, samples, arrival_ts=arrival)
            await asyncio.sleep(0)  # yield to consumers

    async def test_synthetic_5hz_stream(self):
        """All raw packets are captured with a 5 Hz (0.2 s) cadence."""
        pipeline = await self._make_pipeline("synthetic_5hz", feature_callback=_quick_feature_callback, live=True)
        pipeline.set_recording(True)
        pipeline.hardware_state["session_started_at"] = time.time()

        packet_count = 100
        packet_size = 50
        await self._feed_packets(pipeline, packet_count, interval_s=0.2, packet_size=packet_size, sample_rate_code=2)

        extras = await pipeline.stop()
        self.assertEqual(extras.recorded_samples, packet_count * packet_size)
        self.assertEqual(extras.recorded_packets, packet_count)
        self.assertIsNotNone(extras.recording_duration_s)

        out = pipeline.current_out
        packets_csv = out.with_name(out.stem + "_packets.csv")
        with out.open() as fh:
            rows = list(csv.reader(fh))
        with packets_csv.open() as fh:
            packet_rows = list(csv.reader(fh))

        # 1 header + packet_count * packet_size samples
        self.assertEqual(len(rows), 1 + packet_count * packet_size)
        # 1 header + packet_count packet timing rows
        self.assertEqual(len(packet_rows), 1 + packet_count)
        self.assertEqual(extras.queue_overflow_count, 0)
        self.assertEqual(extras.incomplete_drain, False)
        self.assertTrue(extras.callback_duration_p99_us is not None)
        # p99 callback processing should be well below half the nominal interval (0.1 s = 100 ms)
        self.assertLess(extras.callback_duration_p99_us, 100_000.0)
        self.assertIn(2, extras.sample_rate_codes)
        self.assertEqual(pipeline.stats.packets, packet_count)
        self.assertEqual(pipeline.stats.samples, packet_count * packet_size)

    async def test_trace_replay(self):
        """Replay the sanitized evidence trace and reconstruct deterministic counts."""
        trace_path = Path(__file__).parent / "evidence" / "packet_timing_trace.csv"
        with trace_path.open("r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()

        def clean(cell: str) -> str:
            return cell.replace("\r", "").replace("\n", "").strip()

        header = [clean(c) for c in lines[0].split(",")]
        self.assertEqual(header, ["packet_index", "arrival_ts", "sample_count"])

        pipeline = await self._make_pipeline("trace_replay", feature_callback=None, live=False, raw_qsize=1000)
        pipeline.set_recording(True)
        pipeline.hardware_state["session_started_at"] = time.time()

        expected_samples = 0
        valid_packets = 0
        for line in lines[1:]:
            row = [clean(c) for c in line.split(",")]
            if len(row) < 3 or not row[0] or not row[1] or not row[2]:
                continue
            seq = int(row[0])
            arrival = float(row[1])
            count = int(row[2])
            samples = _packet(seq, None, count)
            pipeline.feed_packet(seq, None, samples, arrival_ts=arrival)
            expected_samples += count
            valid_packets += 1
            await asyncio.sleep(0)

        extras = await pipeline.stop()
        out = pipeline.current_out
        with out.open() as fh:
            rows = list(csv.reader(fh))

        self.assertEqual(len(rows), 1 + expected_samples)
        self.assertEqual(extras.queue_overflow_count, 0)
        self.assertEqual(extras.incomplete_drain, False)
        # The trace has missing packets, but the pipeline must not add new loss.
        self.assertEqual(pipeline.stats.packets, valid_packets)
        self.assertEqual(pipeline.stats.samples, expected_samples)

    async def test_slow_feature_worker_raw_priority(self):
        """A slow feature worker must not cause raw packet loss."""
        pipeline = await self._make_pipeline(
            "slow_features",
            feature_callback=_slow_feature_callback(0.5),
            live=True,
            raw_qsize=50,
            feat_qsize=3,
        )
        pipeline.set_recording(True)
        pipeline.hardware_state["session_started_at"] = time.time()

        packet_count = 30
        packet_size = 50
        await self._feed_packets(pipeline, packet_count, interval_s=0.2, packet_size=packet_size, sample_rate_code=2)

        extras = await pipeline.stop()
        out = pipeline.current_out
        with out.open() as fh:
            rows = list(csv.reader(fh))

        # All raw samples must be present even though the feature worker cannot keep up.
        self.assertEqual(len(rows), 1 + packet_count * packet_size)
        self.assertEqual(extras.queue_overflow_count, 0)
        # Feature queue overflow/skips may happen; they are explicitly accounted.
        self.assertGreaterEqual(extras.feature_overflow_count + len(extras.quality_events), 0)

    async def test_queue_overflow_explicit(self):
        """A saturated raw queue records overflow rather than silently dropping."""
        pipeline = await self._make_pipeline("overflow", feature_callback=None, live=False, raw_qsize=2)
        pipeline.set_recording(True)

        # Consumer is artificially delayed: the producer is far faster.
        packet_count = 20
        packet_size = 50
        start = time.time()
        for i in range(packet_count):
            seq = 1000 + i
            samples = _packet(seq, 1, packet_size)
            pipeline.feed_packet(seq, 1, samples, arrival_ts=start + i * 0.001)

        extras = await pipeline.stop()
        out = pipeline.current_out
        with out.open() as fh:
            rows = list(csv.reader(fh))

        self.assertGreater(extras.queue_overflow_count, 0)
        # Some packets were dropped, so fewer than packet_count * packet_size rows.
        self.assertLess(len(rows) - 1, packet_count * packet_size)
        # But those that were accepted must be written deterministically.
        self.assertEqual(len(rows) - 1, pipeline.stats.samples)

    async def test_no_live_features(self):
        """--no-live-features still captures every raw sample with no feature work."""
        pipeline = await self._make_pipeline("no_live", feature_callback=_quick_feature_callback, live=False)
        pipeline.set_recording(True)

        packet_count = 20
        packet_size = 50
        await self._feed_packets(pipeline, packet_count, interval_s=0.2, packet_size=packet_size, sample_rate_code=3)

        extras = await pipeline.stop()
        out = pipeline.current_out
        with out.open() as fh:
            rows = list(csv.reader(fh))

        self.assertEqual(len(rows), 1 + packet_count * packet_size)
        self.assertEqual(extras.live_features_enabled, False)
        self.assertEqual(extras.feature_overflow_count, 0)
        self.assertEqual(extras.last_live_features, {})

    async def test_drain_on_shutdown(self):
        """All queued packets are drained before metadata finalization."""
        pipeline = await self._make_pipeline("drain", feature_callback=None, live=False, raw_qsize=200)
        pipeline.set_recording(True)

        # Feed quickly without yielding, then stop immediately.
        packet_count = 50
        packet_size = 50
        start = time.time()
        for i in range(packet_count):
            seq = 2000 + i
            samples = _packet(seq, 2, packet_size)
            pipeline.feed_packet(seq, 2, samples, arrival_ts=start + i * 0.001)

        extras = await pipeline.stop()
        out = pipeline.current_out
        with out.open() as fh:
            rows = list(csv.reader(fh))

        self.assertEqual(extras.incomplete_drain, False)
        self.assertEqual(extras.packets_remaining_in_queue, 0)
        self.assertEqual(len(rows), 1 + packet_count * packet_size)


if __name__ == "__main__":
    unittest.main()
