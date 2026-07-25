"""Bounded, non-blocking BLE notification pipeline for the FC11 diagnostic recorder.

The synchronous notification callback parses only the AFE protobuf record and
immediately schedules it onto an asyncio queue via ``loop.call_soon_threadsafe``.
A raw-writer consumer drains the queue and writes CSV rows; a separate live-
feature consumer may receive a copied rolling window.  If the live consumer is
late the feature computation is skipped, but the raw capture is never delayed.
"""

from __future__ import annotations

import asyncio
import csv
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from lsl_bridge import LSLBridge


@dataclass
class Packet:
    """Immutable AFE packet record produced by the notification callback."""

    arrival_ts: float
    callback_duration_us: float
    packet_index: int | None
    sample_rate_code: int | None
    samples: list[int]
    queue_depth_at_arrival: int = 0


@dataclass
class PipelineExtras:
    """Extra fields merged into session metadata."""

    queue_overflow_count: int = 0
    feature_overflow_count: int = 0
    incomplete_drain: bool = False
    packets_remaining_in_queue: int = 0
    callback_duration_p99_us: float | None = None
    callback_duration_max_us: float | None = None
    raw_queue_max_depth: int = 0
    live_features_enabled: bool = True
    quality_events: list[dict] = field(default_factory=list)
    last_live_features: dict = field(default_factory=dict)
    sample_rate_codes: list[int] = field(default_factory=list)
    recorded_samples: int = 0
    recorded_packets: int = 0
    recording_duration_s: float | None = None
    lsl_stats: dict | None = None


class CapturePipeline:
    """Async capture pipeline: bounded raw queue, raw writer, optional live worker."""

    def __init__(
        self,
        current_out: Path,
        stats: Any,
        hardware_state: dict,
        feature_callback: Callable | None = None,
        live_features_enabled: bool = True,
        raw_queue_maxsize: int = 200,
        feature_queue_maxsize: int = 10,
        nominal_rate: float = 250.0,
        lsl_bridge: "LSLBridge | None" = None,
    ) -> None:
        self.current_out = Path(current_out)
        self.stats = stats
        self.hardware_state = hardware_state
        self.feature_callback = feature_callback
        self.live_features_enabled = live_features_enabled and feature_callback is not None
        self.raw_queue_maxsize = raw_queue_maxsize
        self.feature_queue_maxsize = feature_queue_maxsize
        self.nominal_rate = nominal_rate
        self._lsl_bridge = lsl_bridge

        self._loop: asyncio.AbstractEventLoop | None = None
        self._raw_queue: asyncio.Queue[Packet] | None = None
        self._feature_queue: asyncio.Queue[Packet] | None = None
        self._tasks: list[asyncio.Task] = []

        self._sample_global = 0
        self._recording = False
        self._recording_started_monotonic: float | None = None
        self._recording_duration_s: float | None = None
        self._recorded_packets = 0
        self._rolling_values: list[int] = []
        self._last_live_feature_at = 0.0
        self._last_quality_event_features: dict = {}
        self._quality_events: list[dict] = []

        self._writer: csv.writer | None = None
        self._packets_writer: csv.writer | None = None
        self._sample_handle: Any = None
        self._packets_handle: Any = None

        self._callback_durations: list[float] = []
        self._raw_queue_max_depth = 0
        self._overflow_count = 0
        self._feature_overflow_count = 0
        self._incomplete_drain = False
        self._packets_remaining = 0
        self._packets_received = 0
        self._packets_processed = 0
        self._sample_rate_codes: set[int] = set()
        self._lsl_stats: Any = None

    async def start(self) -> None:
        """Open CSVs and start consumer tasks."""
        self._loop = asyncio.get_running_loop()
        self._raw_queue = asyncio.Queue(maxsize=self.raw_queue_maxsize)
        if self.live_features_enabled:
            self._feature_queue = asyncio.Queue(maxsize=self.feature_queue_maxsize)

        self.current_out.parent.mkdir(parents=True, exist_ok=True)
        self._sample_handle = self.current_out.open("w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._sample_handle)
        self._writer.writerow(["sample_global", "ts", "raw_s24", "packet_index", "sample_rate_code"])

        packets_path = self.current_out.with_name(self.current_out.stem + "_packets.csv")
        self._packets_handle = packets_path.open("w", newline="", encoding="utf-8")
        self._packets_writer = csv.writer(self._packets_handle)
        self._packets_writer.writerow(
            ["arrival_ts", "callback_duration_us", "packet_index", "sample_count", "queue_depth", "sample_rate_code"]
        )

        self._tasks.append(asyncio.create_task(self._raw_writer_worker(), name="raw-writer"))
        if self.live_features_enabled:
            self._tasks.append(asyncio.create_task(self._live_feature_worker(), name="live-features"))
        if self._lsl_bridge is not None:
            await self._lsl_bridge.start()

    def set_recording(self, recording: bool) -> None:
        if recording and not self._recording:
            self._recording_started_monotonic = time.monotonic()
        elif not recording and self._recording and self._recording_started_monotonic is not None:
            self._recording_duration_s = time.monotonic() - self._recording_started_monotonic
        self._recording = recording
        if recording:
            self._last_live_feature_at = time.monotonic()

    def feed_packet(
        self,
        packet_index: int | None,
        sample_rate_code: int | None,
        samples: list[int],
        arrival_ts: float | None = None,
    ) -> None:
        """Sync API called from the BLE notification callback.

        ``arrival_ts`` may be overridden by tests that replay a saved trace.
        """
        start_ts = time.perf_counter()
        if arrival_ts is None:
            arrival_ts = time.time()
        callback_duration_us = (time.perf_counter() - start_ts) * 1_000_000.0

        # Keep only the last timing samples; p99/max are enough for diagnostics.
        self._callback_durations.append(callback_duration_us)
        if len(self._callback_durations) > 1000:
            del self._callback_durations[0]

        if self._raw_queue is None or self._loop is None:
            return

        queue_depth = self._raw_queue.qsize()
        self._raw_queue_max_depth = max(self._raw_queue_max_depth, queue_depth)
        packet = Packet(
            arrival_ts=arrival_ts,
            callback_duration_us=callback_duration_us,
            packet_index=packet_index,
            sample_rate_code=sample_rate_code,
            samples=samples,
            queue_depth_at_arrival=queue_depth,
        )
        self._packets_received += 1
        self._loop.call_soon_threadsafe(self._enqueue_raw, packet)

    def _enqueue_raw(self, packet: Packet) -> None:
        """Executed in the event loop thread; handles overflow explicitly."""
        if self._raw_queue is None:
            return
        try:
            self._raw_queue.put_nowait(packet)
        except asyncio.QueueFull:
            self._overflow_count += 1

    def feed_marker(self, timestamp: float, marker: str) -> None:
        """Forward a timestamped marker without touching the BLE callback."""
        if self._lsl_bridge is not None:
            self._lsl_bridge.feed_marker(timestamp, marker)

    async def stop(self, drain_timeout: float = 5.0) -> PipelineExtras:
        """Cancel live worker and drain the raw queue before closing files."""
        if not self._tasks:
            return self._build_extras()

        # Cancel live feature worker first; raw capture has priority.
        for task in self._tasks:
            if task.get_name() == "live-features":
                task.cancel()
        await asyncio.gather(*[t for t in self._tasks if t.get_name() == "live-features"], return_exceptions=True)

        # Drain raw queue with a timeout.
        if self._raw_queue is not None:
            try:
                await asyncio.wait_for(self._drain_raw_queue(), timeout=drain_timeout)
            except asyncio.TimeoutError:
                self._incomplete_drain = True
                self._packets_remaining = self._raw_queue.qsize()

        # Cancel raw writer.
        for task in self._tasks:
            if task.get_name() == "raw-writer":
                task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        self._lsl_stats = None
        if self._lsl_bridge is not None:
            try:
                self._lsl_stats = await self._lsl_bridge.stop()
            except Exception as exc:
                print(f"lsl bridge stop error: {exc!r}", flush=True)

        if self._sample_handle is not None:
            self._sample_handle.flush()
            self._sample_handle.close()
        if self._packets_handle is not None:
            self._packets_handle.flush()
            self._packets_handle.close()

        return self._build_extras()

    async def _drain_raw_queue(self) -> None:
        while True:
            if not self._raw_queue.empty():
                packet = self._raw_queue.get_nowait()
                await self._process_packet(packet)
                self._raw_queue.task_done()
                continue
            # Yield so any pending call_soon_threadsafe callbacks can enqueue.
            await asyncio.sleep(0)
            if self._raw_queue.empty():
                break

    async def _raw_writer_worker(self) -> None:
        while True:
            packet = await self._raw_queue.get()
            if packet is None:
                break
            await self._process_packet(packet)
            self._raw_queue.task_done()

    async def _process_packet(self, packet: Packet) -> None:
        """Write raw samples + timing; forward to live feature worker if enabled."""
        self._packets_processed += 1
        if packet.sample_rate_code is not None:
            self._sample_rate_codes.add(packet.sample_rate_code)
        if packet.packet_index is not None and packet.samples:
            # StreamStats.update may be called; it is a known helper.
            if hasattr(self.stats, "update"):
                self.stats.update(packet.packet_index, len(packet.samples), packet.arrival_ts)

        if self._packets_writer is not None:
            self._packets_writer.writerow(
                [
                    f"{packet.arrival_ts:.6f}",
                    int(round(packet.callback_duration_us)),
                    packet.packet_index if packet.packet_index is not None else "",
                    len(packet.samples),
                    packet.queue_depth_at_arrival,
                    packet.sample_rate_code if packet.sample_rate_code is not None else "",
                ]
            )

        if self._recording and self._writer is not None:
            if packet.samples:
                self._recorded_packets += 1
            pi = "" if packet.packet_index is None else packet.packet_index
            src = "" if packet.sample_rate_code is None else packet.sample_rate_code
            sample_count = len(packet.samples)
            lsl_base_ts = (
                packet.arrival_ts - (sample_count - 1) / self.nominal_rate
                if sample_count
                else packet.arrival_ts
            )
            for sample_offset, value in enumerate(packet.samples):
                self._writer.writerow([self._sample_global, f"{packet.arrival_ts:.6f}", value, pi, src])
                if self._lsl_bridge is not None:
                    self._lsl_bridge.feed_sample(
                        lsl_base_ts + sample_offset / self.nominal_rate,
                        value,
                        packet.sample_rate_code,
                    )
                self._sample_global += 1
            if self._sample_global % 500 == 0:
                self._sample_handle.flush()

        if self._recording and self.live_features_enabled and self._feature_queue is not None:
            try:
                self._feature_queue.put_nowait(packet)
            except asyncio.QueueFull:
                self._feature_overflow_count += 1

    async def _live_feature_worker(self) -> None:
        while True:
            packet = await self._feature_queue.get()
            if packet is None:
                break
            self._rolling_values.extend(int(v) for v in packet.samples)
            if len(self._rolling_values) > 1800:
                del self._rolling_values[: len(self._rolling_values) - 1800]

            now = time.monotonic()
            if now - self._last_live_feature_at >= 1.0:
                await self._run_live_features(now)
                self._last_live_feature_at = now
            self._feature_queue.task_done()

    async def _run_live_features(self, now: float) -> None:
        session_start = self.hardware_state.get("session_started_at")
        if session_start is not None:
            elapsed = max(now - session_start, 1.0)
            sample_rate = getattr(self.stats, "samples", len(self._rolling_values)) / elapsed
            if not (100.0 <= sample_rate <= 500.0):
                sample_rate = self.nominal_rate
        else:
            sample_rate = self.nominal_rate

        window_len = max(32, min(len(self._rolling_values), int(round(sample_rate * 5.0))))
        if window_len <= 0:
            return
        window = self._rolling_values[-window_len:]

        # Offload the CPU-bound feature work to a thread to avoid blocking the loop.
        loop = asyncio.get_running_loop()
        try:
            live_features = await asyncio.wait_for(
                loop.run_in_executor(None, self.feature_callback, window, sample_rate, self.stats, self.hardware_state, self.hardware_state.get("battery_percent")),
                timeout=0.5,
            )

        except asyncio.TimeoutError:
            # Worker is late: skip this second; raw capture is unaffected.
            return

        self.last_live_features = live_features
        if not live_features.get("ok"):
            return

        prev = self._last_quality_event_features
        blink = int(live_features.get("blink_proxy") or 0)
        noise = int(live_features.get("noise_spike_count") or 0)
        alpha = live_features.get("alpha_peak_hz")
        rms = float(live_features.get("rms") or 0.0)
        saturation_pct = float(live_features.get("saturation_pct") or 0.0)
        ts = time.time()
        t_rel = ts - session_start if session_start is not None else None

        if blink >= 3 and (prev.get("blink_proxy") or 0) < 3:
            self._quality_events.append({
                "ts": ts, "event_time_utc": None, "t_rel_s": t_rel,
                "event_type": "blink_proxy", "blink_proxy": blink, "rms": rms, "source": "rolling_raw_eeg",
            })
        if noise >= 5 and (prev.get("noise_spike_count") or 0) < 5:
            self._quality_events.append({
                "ts": ts, "event_time_utc": None, "t_rel_s": t_rel,
                "event_type": "noise_spike", "noise_spike_count": noise, "rms": rms, "source": "rolling_raw_eeg",
            })
        if saturation_pct >= 5.0 and (prev.get("saturation_pct") or 0) < 5.0:
            self._quality_events.append({
                "ts": ts, "event_time_utc": None, "t_rel_s": t_rel,
                "event_type": "saturation_warning", "saturation_pct": saturation_pct, "source": "rolling_raw_eeg",
            })
        if alpha is not None and (prev.get("alpha_peak_hz") is None or abs(alpha - prev.get("alpha_peak_hz")) >= 0.5):
            self._quality_events.append({
                "ts": ts, "event_time_utc": None, "t_rel_s": t_rel,
                "event_type": "alpha_peak", "alpha_peak_hz": round(alpha, 3), "source": "rolling_raw_eeg",
            })
        self._last_quality_event_features = {
            "blink_proxy": blink, "noise_spike_count": noise, "alpha_peak_hz": alpha, "saturation_pct": saturation_pct,
        }

    def _build_extras(self) -> PipelineExtras:
        if self._recording_duration_s is None and self._recording_started_monotonic is not None:
            self._recording_duration_s = time.monotonic() - self._recording_started_monotonic
        sorted_durations = sorted(self._callback_durations) if self._callback_durations else []
        p99 = None
        max_us = None
        if sorted_durations:
            p99 = sorted_durations[int(0.99 * len(sorted_durations))]
            max_us = sorted_durations[-1]
        lsl_stats = None
        if self._lsl_stats is not None:
            try:
                lsl_stats = self._lsl_stats.as_dict()
            except Exception:
                lsl_stats = {}
        return PipelineExtras(
            queue_overflow_count=self._overflow_count,
            feature_overflow_count=self._feature_overflow_count,
            incomplete_drain=self._incomplete_drain,
            packets_remaining_in_queue=self._packets_remaining,
            callback_duration_p99_us=p99,
            callback_duration_max_us=max_us,
            raw_queue_max_depth=self._raw_queue_max_depth,
            live_features_enabled=self.live_features_enabled,
            quality_events=self._quality_events,
            last_live_features=getattr(self, "last_live_features", {}),
            sample_rate_codes=sorted(self._sample_rate_codes),
            recorded_samples=self._sample_global,
            recorded_packets=self._recorded_packets,
            recording_duration_s=self._recording_duration_s,
            lsl_stats=lsl_stats,
        )
