#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime as dt
import json
import math
import os
import shutil
import sys
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from fc11_capture_pipeline import CapturePipeline
from lsl_bridge import LSLBridge
from scientific_qc import (
    ALGORITHM_VERSION as SCIENTIFIC_QC_VERSION,
    FC11_SCALING_STATUS,
    FC11_VENDOR_UV_PER_COUNT,
    analyze_windows,
    sha256_manifest,
)
from scientific_spectral import ALGORITHM_VERSION as SCIENTIFIC_SPECTRAL_VERSION, compute_spectral_windows
from scientific_longitudinal import ALGORITHM_VERSION as SCIENTIFIC_LONGITUDINAL_VERSION, update_longitudinal_outputs

try:
    from bleak import BleakClient, BleakScanner
except ModuleNotFoundError:  # pragma: no cover - user setup path
    BleakClient = None
    BleakScanner = None


SERVICE_UUID = "0d740001-d26f-4dbb-95e8-a4f5c55c57a9"
WRITE_UUID = "0d740002-d26f-4dbb-95e8-a4f5c55c57a9"
NOTIFY_UUID = "0d740003-d26f-4dbb-95e8-a4f5c55c57a9"
BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
BLE_WRITE_TIMEOUT_S = 4.0
BLE_NOTIFY_TIMEOUT_S = 4.0

CMD_PAIR = 1
CMD_VALIDATE_PAIR_INFO = 2
CMD_START = 3
CMD_STOP = 4
CMD_SET_LED_COLOR = 9
CMD_SET_SLEEP_IDLE_TIME = 10
CMD_SET_VIBRATION_INTENSITY = 12
CMD_GET_SYSTEM_INFO = 13
CMD_GET_LEAD_OFF_STATUS = 14
PAIR_INFO = "123e4567-e89b-12d3-a456-426614174000"

CAPTURE_ROOT = Path(os.environ.get("MINDTUNE_CAPTURE_ROOT", Path(__file__).resolve().parent)).resolve()
DEFAULT_OUTPUT = Path(os.environ.get("MINDTUNE_CAPTURE_OUTPUT", CAPTURE_ROOT / "sessions")).resolve()
DEFAULT_RUNTIME = Path(os.environ.get("MINDTUNE_CAPTURE_RUNTIME", CAPTURE_ROOT / "runtime")).resolve()
MINDTUNE_V2_OUTPUT = Path(os.environ.get("MINDTUNE_SESSION_OUTPUT", CAPTURE_ROOT / "mindtune_sessions")).resolve()
DEVICE_CACHE = DEFAULT_RUNTIME / "last_device.json"
MAC_DING = Path("/System/Library/Sounds/Glass.aiff")


def require_bleak() -> None:
    if BleakClient is None or BleakScanner is None:
        print("Modulo Python 'bleak' non installato.")
        print("Installa con: python3 -m pip install bleak")
        raise SystemExit(2)


_TARGET_LED_COLOR: str | None = None


def led_color_for_phase(phase: str, battery_percent: int | None) -> str:
    if battery_percent is not None and 0 < battery_percent < 3:
        return "red"
    if phase in ("error", "interrupted"):
        return "red"
    if phase in ("scan", "connecting", "ble_link", "handshake_sent"):
        return "blue"
    if phase in ("connected", "starting", "prep", "recording"):
        return "white"
    return "off"


LED_COLOR_RGB = {
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "off": (0, 0, 0),
}


async def apply_helmet_led(client, write_char, args, phase: str, battery_percent: int | None) -> None:
    """Aggiorna il LED del casco in base alla fase, se cambiato."""
    global _TARGET_LED_COLOR
    target = led_color_for_phase(phase, battery_percent)
    if target == _TARGET_LED_COLOR:
        return
    _TARGET_LED_COLOR = target
    r, g, b = LED_COLOR_RGB.get(target, (0, 0, 0))
    msg_id = int(getattr(args, "start_msg_id", 5) or 5)
    try:
        await send_frame(client, write_char, "SET_LED_COLOR", make_led_color(r, g, b, msg_id), quiet=getattr(args, "quiet", False))
        args.start_msg_id = msg_id + 1
        print(f"LED casco aggiornato: {target} ({r},{g},{b})", flush=True)
    except Exception as exc:
        print(f"LED casco update failed: {exc!r}", flush=True)


def write_status(args, phase: str, **extra) -> None:
    status_file = getattr(args, "status_file", None)
    if not status_file:
        return
    path = Path(status_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    phase_started_at = now
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
            if previous.get("phase") == phase:
                phase_started_at = float(previous.get("phase_started_at") or now)
        except Exception:
            pass
    battery = extra.get("battery_percent")
    payload = {
        "phase": phase,
        "phase_started_at": phase_started_at,
        "updated_at": now,
        "led_color": led_color_for_phase(phase, battery),
        **extra,
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def bluetooth_permission_message(exc: Exception) -> str | None:
    text = str(exc)
    if "Bluetooth is not authorized" not in text and "DENIED" not in text:
        return None
    return (
        "Bluetooth non autorizzato da macOS. Apri Impostazioni di Sistema > "
        "Privacy e Sicurezza > Bluetooth e abilita MindTune Lab. "
        "Poi chiudi MindTune Lab con Cmd-Q e riaprilo."
    )


def varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | 0x80 if n else b)
        if not n:
            return bytes(out)


def key(field: int, wire: int) -> bytes:
    return varint((field << 3) | wire)


def wrap(body: bytes) -> bytes:
    return b"CMSN" + len(body).to_bytes(2, "big") + body + b"PKED"


def sys_config_pair_payload(cmd: int, pair_info: str) -> bytes:
    p = pair_info.encode("utf-8")
    return key(1, 0) + varint(cmd) + key(6, 2) + varint(len(p)) + p


def sys_config_cmd_payload(cmd: int) -> bytes:
    return key(1, 0) + varint(cmd)


def sys_config_sleep_idle_payload(seconds: int) -> bytes:
    seconds = max(0, min(86_400, int(seconds)))
    return key(1, 0) + varint(CMD_SET_SLEEP_IDLE_TIME) + key(4, 0) + varint(seconds)


def sys_config_set_led_color_payload(r: int, g: int, b: int, color_encoding: str = "varint") -> bytes:
    """
    Costruisce il payload SysConfig per SET_LED_COLOR (cmd=9).
    Il formato colore e' 0xRRGGBB00 come nel native SDK (r<<24 | g<<16 | b<<8).
    Di default usa varint (uint32); provare fixed32 se il casco non risponde.
    """
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    color = (r << 24) | (g << 16) | (b << 8)
    payload = key(1, 0) + varint(CMD_SET_LED_COLOR)
    if color_encoding == "fixed32":
        payload += key(2, 5) + color.to_bytes(4, "little", signed=False)
    else:
        payload += key(2, 0) + varint(color)
    return payload


def sys_config_set_vibration_intensity_payload(intensity: int) -> bytes:
    """
    Costruisce il payload SysConfig per SET_VIBRATION_INTENSITY (cmd=12).
    intensity tra 0 e 100; viene mappato su un uint32.
    """
    intensity = max(0, min(100, int(intensity)))
    return key(1, 0) + varint(CMD_SET_VIBRATION_INTENSITY) + key(3, 0) + varint(intensity)


def crimson_packet(sys_cfg: bytes, msg_id: int) -> bytes:
    body = key(1, 0) + varint(msg_id) + key(2, 2) + varint(len(sys_cfg)) + sys_cfg
    return wrap(body)


def crimson_imu_packet(imu_cfg: bytes, msg_id: int) -> bytes:
    body = key(1, 0) + varint(msg_id) + key(4, 2) + varint(len(imu_cfg)) + imu_cfg
    return wrap(body)


def make_pair(cmd: int, msg_id: int) -> bytes:
    return crimson_packet(sys_config_pair_payload(cmd, PAIR_INFO), msg_id)


def make_cmd(cmd: int, msg_id: int) -> bytes:
    return crimson_packet(sys_config_cmd_payload(cmd), msg_id)


def make_sleep_idle(seconds: int, msg_id: int) -> bytes:
    return crimson_packet(sys_config_sleep_idle_payload(seconds), msg_id)


def make_led_color(r: int, g: int, b: int, msg_id: int, color_encoding: str = "varint") -> bytes:
    return crimson_packet(sys_config_set_led_color_payload(r, g, b, color_encoding=color_encoding), msg_id)


def make_vibration(intensity: int, msg_id: int) -> bytes:
    return crimson_packet(sys_config_set_vibration_intensity_payload(intensity), msg_id)


def make_imu_config(msg_id: int, sample_rate_code: int = 16) -> bytes:
    # Opt-in only. 16 is the native enum observed for 12.5 Hz acc/gyro.
    imu_cfg = (
        key(1, 0) + varint(sample_rate_code)
        + key(2, 0) + varint(sample_rate_code)
        + key(4, 0) + varint(1)
        + key(5, 0) + varint(1)
    )
    return crimson_imu_packet(imu_cfg, msg_id)


def ascii_fragments(data: bytes, min_len: int = 4) -> list[str]:
    fragments: list[str] = []
    current = bytearray()
    for b in data:
        if 32 <= b <= 126:
            current.append(b)
        else:
            if len(current) >= min_len:
                fragments.append(current.decode("ascii", errors="replace"))
            current.clear()
    if len(current) >= min_len:
        fragments.append(current.decode("ascii", errors="replace"))
    return fragments


def read_varint(buf: bytes, i: int) -> tuple[int, int]:
    shift = 0
    result = 0
    while i < len(buf):
        b = buf[i]
        result |= (b & 0x7F) << shift
        i += 1
        if not (b & 0x80):
            return result, i
        shift += 7
    raise ValueError("truncated varint")


def s24be(b3: bytes) -> int:
    v = int.from_bytes(b3, "big", signed=False)
    if v & 0x800000:
        v -= 0x1000000
    return v


def parse_afe_msg(sub: bytes) -> tuple[int | None, list[int]]:
    i = 0
    packet_index = None
    samples: list[int] = []
    while i < len(sub):
        k, i = read_varint(sub, i)
        field = k >> 3
        wire = k & 7
        if wire == 0:
            val, i = read_varint(sub, i)
            if field == 1:
                packet_index = val
        elif wire == 2:
            ln, i = read_varint(sub, i)
            payload = sub[i : i + ln]
            i += ln
            if field == 4 and len(payload) % 3 == 0:
                samples = [s24be(payload[j : j + 3]) for j in range(0, len(payload), 3)]
        else:
            break
    return packet_index, samples


def parse_afe_detail(sub: bytes) -> dict:
    i = 0
    detail: dict = {
        "seq_num": None,
        "sample_rate_code": None,
        "lead_off": None,
        "ch1": [],
        "ch2": [],
        "signal_type": None,
    }
    while i < len(sub):
        k, i = read_varint(sub, i)
        field = k >> 3
        wire = k & 7
        if wire == 0:
            val, i = read_varint(sub, i)
            if field == 1:
                detail["seq_num"] = val
            elif field == 2:
                detail["sample_rate_code"] = val
            elif field == 3:
                detail["lead_off"] = val
            elif field == 6:
                detail["signal_type"] = val
        elif wire == 2:
            ln, i = read_varint(sub, i)
            payload = sub[i : i + ln]
            i += ln
            if field in (4, 5) and len(payload) % 3 == 0:
                values = [s24be(payload[j : j + 3]) for j in range(0, len(payload), 3)]
                detail["ch1" if field == 4 else "ch2"] = values
        else:
            break
    return detail


def parse_simple_varint_message(sub: bytes) -> dict[int, int]:
    i = 0
    out: dict[int, int] = {}
    while i < len(sub):
        k, i = read_varint(sub, i)
        field = k >> 3
        wire = k & 7
        if wire == 0:
            out[field], i = read_varint(sub, i)
        elif wire == 2:
            ln, i = read_varint(sub, i)
            i += ln
        elif wire == 1:
            i += 8
        elif wire == 5:
            i += 4
        else:
            break
    return out


def parse_imu_detail(sub: bytes) -> dict:
    # The Android SDK exposes several optional IMU submessages. We keep this
    # deliberately conservative: sequence/sample-rate plus raw numeric fields
    # when the payload is present, without guessing units.
    i = 0
    detail: dict = {}
    names = {
        1: "acc",
        2: "gyro",
        3: "mag",
        4: "euler",
        5: "d6d",
        6: "temperature",
    }
    while i < len(sub):
        k, i = read_varint(sub, i)
        field = k >> 3
        wire = k & 7
        name = names.get(field, f"field_{field}")
        if wire == 2:
            ln, i = read_varint(sub, i)
            payload = sub[i : i + ln]
            i += ln
            detail[name] = parse_simple_varint_message(payload)
        elif wire == 0:
            detail[name], i = read_varint(sub, i)
        else:
            break
    return detail


def flatten_imu_numbers(value, prefix: str = "") -> dict[str, float]:
    numbers: dict[str, float] = {}
    if isinstance(value, dict):
        for key_name, child in value.items():
            path = f"{prefix}.{key_name}" if prefix else str(key_name)
            numbers.update(flatten_imu_numbers(child, path))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        numbers[prefix or "value"] = float(value)
    return numbers


def imu_motion_energy(previous: dict[str, float] | None, current: dict[str, float]) -> float | None:
    if not previous or not current:
        return None
    common = sorted(set(previous) & set(current))
    if not common:
        return None
    deltas = [current[key_name] - previous[key_name] for key_name in common]
    return math.sqrt(sum(delta * delta for delta in deltas) / len(deltas))


def parse_cmsn_detail(data: bytes) -> dict:
    detail: dict = {
        "msg_id": None,
        "afe": None,
        "imu": None,
        "sys_resp": None,
        "sys_info": None,
        "bstar_data": None,
        "lead_off_status": None,
        "raw_payload_len": len(data),
    }
    if not (data.startswith(b"CMSN") and data.endswith(b"PKED")):
        return detail
    body = data[6:-4]
    i = 0
    while i < len(body):
        k, i = read_varint(body, i)
        field = k >> 3
        wire = k & 7
        if wire == 0:
            val, i = read_varint(body, i)
            if field == 1:
                detail["msg_id"] = val
        elif wire == 2:
            ln, i = read_varint(body, i)
            sub = body[i : i + ln]
            i += ln
            if field == 2:
                detail["afe"] = parse_afe_detail(sub)
            elif field == 3:
                detail["imu"] = parse_imu_detail(sub)
            elif field == 6:
                detail["sys_resp"] = parse_simple_varint_message(sub)
            elif field == 7:
                detail["sys_info"] = parse_simple_varint_message(sub)
            elif field == 8:
                detail["bstar_data"] = parse_simple_varint_message(sub)
            elif field == 9:
                values = parse_simple_varint_message(sub)
                detail["lead_off_status"] = {
                    "center_rld": values.get(1),
                    "side_channels": values.get(2),
                }
        else:
            break
    return detail


def parse_cmsn(data: bytes) -> tuple[int | None, list[int]]:
    detail = parse_cmsn_detail(data)
    afe = detail.get("afe") or {}
    return afe.get("seq_num"), list(afe.get("ch1") or [])


def shallow_proto_fields(buf: bytes, limit: int = 64) -> list[dict]:
    fields = []
    i = 0
    while i < len(buf) and len(fields) < limit:
        start = i
        try:
            k, i = read_varint(buf, i)
        except Exception:
            fields.append({"offset": start, "error": "truncated_key"})
            break
        field = k >> 3
        wire = k & 7
        row = {"offset": start, "field": field, "wire": wire}
        try:
            if wire == 0:
                value, i = read_varint(buf, i)
                row["value"] = value
            elif wire == 1:
                row["hex"] = buf[i : i + 8].hex()
                i += 8
            elif wire == 2:
                ln, i = read_varint(buf, i)
                payload = buf[i : i + ln]
                i += ln
                row["len"] = ln
                row["hex_prefix"] = payload[:32].hex()
                text = ascii_fragments(payload)
                if text:
                    row["ascii"] = text[:6]
            elif wire == 5:
                row["hex"] = buf[i : i + 4].hex()
                i += 4
            else:
                row["error"] = "unsupported_wire"
                fields.append(row)
                break
        except Exception as exc:
            row["error"] = repr(exc)
            fields.append(row)
            break
        fields.append(row)
    return fields


def describe_frame(data: bytes) -> dict:
    payload = {
        "len": len(data),
        "hex": data.hex(),
        "ascii": ascii_fragments(data),
        "cmsn": data.startswith(b"CMSN") and data.endswith(b"PKED"),
    }
    if payload["cmsn"] and len(data) >= 10:
        declared_len = int.from_bytes(data[4:6], "big")
        body = data[6:-4]
        payload["declared_len"] = declared_len
        payload["body_len"] = len(body)
        payload["body_fields"] = shallow_proto_fields(body)
        try:
            packet_index, samples = parse_cmsn(data)
            payload["eeg_packet_index"] = packet_index
            payload["eeg_samples"] = len(samples)
        except Exception as exc:
            payload["parse_error"] = repr(exc)
    return payload


@dataclass
class StreamStats:
    packets: int = 0
    samples: int = 0
    packet_index_first: int | None = None
    packet_index_last: int | None = None
    packet_index_gaps: int = 0
    max_inter_packet_gap_s: float | None = None
    last_packet_time: float | None = None
    prev_packet_index: int | None = None

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


def utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_from_ts(ts: float) -> str:
    return dt.datetime.fromtimestamp(float(ts), dt.UTC).isoformat().replace("+00:00", "Z")


def local_tz_name() -> str:
    return time.tzname[0] if time.tzname else "local"


def safe_piece(value: str, fallback: str = "session") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:80] or fallback


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t" if path.suffix == ".tsv" else ",")
        writer.writeheader()
        writer.writerows(rows)


def lead_state_name(value) -> str | None:
    names = {0: "unknown", 1: "connected", 2: "disconnected"}
    try:
        return names.get(int(value), str(value))
    except Exception:
        return None


def contact_state_from_lead(center, side) -> str | None:
    if center is None and side is None:
        return None
    if center == 1 and side == 1:
        return "ok"
    if center == 2 or side == 2:
        return "bad"
    return "partial_or_unknown"


FUSI_MEDITATION_FEATURE_MEANS = [
    -0.05641, 39.48397064, 7.97646999, 57.15618134, 2.8171401,
    2.73337007, 3.30445004, 4.26874018, 0.83094001, 0.59773999,
    0.66582, 0.91801, 0.42109999, 0.22157, 0.17930999, 0.29391,
    0.28714001, 0.14523, 0.10387, 0.18833999, 0.22983, 0.1145,
    0.0792, 0.14867, -44.93592072, -27.98477936, -17.33975983,
    -8.88665962, -1.12971997, 6.70075989, 15.52460003, 27.23867035,
    47.16249084,
]

FUSI_MEDITATION_FEATURE_SCALES = [
    8.9476099, 81.11836243, 66.70226288, 116.2179718, 6.41520023,
    6.34654999, 7.96815014, 10.23834038, 1.47298002, 0.77318001,
    0.69861001, 1.04591, 0.74685001, 0.40103999, 0.36950999,
    0.53460997, 0.48433, 0.2374, 0.16451, 0.29291999, 0.32758999,
    0.15448, 0.11005, 0.19426, 100.8527832, 72.90912628,
    45.32199097, 26.1967392, 11.49890995, 10.10270977, 25.58308983,
    58.23991013, 100.20300293,
]


def describe_values(values: list[float]) -> tuple[float, float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0, 0.0
    n = len(values)
    mean = sum(values) / n
    centered = [value - mean for value in values]
    variance = sum(value * value for value in centered) / n
    std = math.sqrt(variance)
    if std <= 1e-12:
        return mean, 0.0, 0.0, 0.0
    skew = sum((value / std) ** 3 for value in centered) / n
    kurtosis = sum((value / std) ** 4 for value in centered) / n
    return mean, std, skew, kurtosis


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * pct
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    if low == high:
        return sorted_values[low]
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (pos - low)


def dft_power_bins(values: list[float], sample_rate: float, max_bin: int) -> list[tuple[float, float]]:
    n = len(values)
    if n <= 1:
        return []
    bins: list[tuple[float, float]] = []
    usable_max = min(max_bin, n // 2)
    for k in range(1, usable_max + 1):
        real = 0.0
        imag = 0.0
        for idx, value in enumerate(values):
            angle = -2.0 * math.pi * k * idx / n
            real += value * math.cos(angle)
            imag += value * math.sin(angle)
        freq = k * sample_rate / n
        power = (real * real + imag * imag) / n
        bins.append((freq, power))
    return bins


def compute_native_band_rows(samples_rows: list[dict], sample_rate: float, session_id: str) -> list[dict]:
    if not samples_rows:
        return []
    values = [float(row["raw_s24"]) for row in samples_rows]
    n_window = max(64, int(round(sample_rate * 5.0)))
    n_step = n_window
    if len(values) < n_window:
        return []
    bands = [
        ("delta", 0.5, 4.0),
        ("theta", 4.0, 8.0),
        ("alpha", 8.0, 12.0),
        ("low_beta", 12.0, 22.0),
        ("high_beta", 22.0, 32.0),
        ("gamma", 32.0, 45.0),
    ]
    max_freq = max(high for _, _, high in bands)
    k_min = max(1, int(math.ceil(0.5 * n_window / sample_rate)))
    k_max = min(n_window // 2, int(math.floor(max_freq * n_window / sample_rate)))
    rows: list[dict] = []
    for start in range(0, len(values) - n_window + 1, n_step):
        window = values[start : start + n_window]
        mean = sum(window) / n_window
        centered = [v - mean for v in window]
        powers: dict[str, float] = {name: 0.0 for name, _, _ in bands}
        total_power = 0.0
        for k in range(k_min, k_max + 1):
            freq = k * sample_rate / n_window
            real = 0.0
            imag = 0.0
            for idx, value in enumerate(centered):
                angle = -2.0 * math.pi * k * idx / n_window
                real += value * math.cos(angle)
                imag += value * math.sin(angle)
            power = (real * real + imag * imag) / n_window
            for name, low, high in bands:
                if low <= freq < high:
                    powers[name] += power
                    total_power += power
                    break
        row = {
            "session_id": session_id,
            "window_index": len(rows),
            "start_t_rel_s": start / sample_rate,
            "end_t_rel_s": (start + n_window) / sample_rate,
            "sample_count": n_window,
            "sample_rate_hz": sample_rate,
            "source": "derived_from_raw_eeg_local_dft",
        }
        for name, _, _ in bands:
            row[f"{name}_power"] = powers[name]
        beta_power = powers["low_beta"] + powers["high_beta"]
        row["beta_power"] = beta_power
        for name, _, _ in bands:
            row[f"{name}_rel"] = powers[name] / total_power if total_power else None
        row["beta_rel"] = beta_power / total_power if total_power else None
        row["alpha_theta"] = powers["alpha"] / powers["theta"] if powers["theta"] else None
        row["theta_beta"] = powers["theta"] / beta_power if beta_power else None
        row["low_high_beta"] = powers["low_beta"] / powers["high_beta"] if powers["high_beta"] else None
        rows.append(row)
    return rows


def compute_brainlab_feature_rows(samples_rows: list[dict], sample_rate: float, session_id: str) -> list[dict]:
    if not samples_rows:
        return []
    values = [float(row["raw_s24"]) for row in samples_rows]
    n_window = max(64, int(round(sample_rate * 5.0)))
    n_step = n_window
    if len(values) < n_window:
        return []
    rows: list[dict] = []
    for start in range(0, len(values) - n_window + 1, n_step):
        sample_window = samples_rows[start : start + n_window]
        raw_window = values[start : start + n_window]
        sorted_raw = sorted(raw_window)
        median = percentile(sorted_raw, 0.5)
        centered = [value - median for value in raw_window]
        fusi_window = centered[-800:] if len(centered) >= 800 else centered
        clipped = [max(-2000.0, min(2000.0, value)) for value in fusi_window]
        time_features = list(describe_values(clipped))

        spectrum = dft_power_bins(clipped, sample_rate, 200)
        log_powers = [math.log10(1.0 + max(0.0, power)) for _, power in spectrum[:200]]
        while len(log_powers) < 200:
            log_powers.append(0.0)
        freq_features: list[float] = []
        for block_start in range(0, 200, 40):
            freq_features.extend(describe_values(log_powers[block_start : block_start + 40]))

        sorted_clipped = sorted(clipped)
        percentile_features = [percentile(sorted_clipped, pct / 10.0) for pct in range(1, 10)]
        fusi_features = (time_features + freq_features + percentile_features)[:33]
        while len(fusi_features) < 33:
            fusi_features.append(0.0)

        raw_spectrum = dft_power_bins(centered, sample_rate, int(max(1, math.floor(45.0 * n_window / sample_rate))))
        alpha_candidates = [(freq, power) for freq, power in raw_spectrum if 7.0 <= freq <= 13.0]
        alpha_peak_hz = max(alpha_candidates, key=lambda item: item[1])[0] if alpha_candidates else None

        _, raw_std, _, _ = describe_values(centered)
        blink_threshold = max(1.0, raw_std * 4.0)
        blink_proxy = sum(1 for value in centered if abs(value) > blink_threshold)
        diffs = [centered[idx] - centered[idx - 1] for idx in range(1, len(centered))]
        _, diff_std, _, _ = describe_values(diffs)
        spike_threshold = max(1.0, diff_std * 5.0)
        noise_spike_count = sum(1 for value in diffs if abs(value) > spike_threshold)
        peak_to_peak = max(raw_window) - min(raw_window)
        saturation_pct = 100.0 * sum(1 for value in raw_window if abs(int(value)) >= 8_300_000) / len(raw_window)

        sequences = []
        for row in sample_window:
            seq = row.get("sequence_num")
            if seq is None:
                continue
            try:
                seq_int = int(seq)
            except (TypeError, ValueError):
                continue
            if not sequences or sequences[-1] != seq_int:
                sequences.append(seq_int)
        packet_gap_count = 0
        for prev, current in zip(sequences, sequences[1:]):
            if current > prev + 1:
                packet_gap_count += 1

        row = {
            "session_id": session_id,
            "window_index": len(rows),
            "start_t_rel_s": start / sample_rate,
            "end_t_rel_s": (start + n_window) / sample_rate,
            "sample_count": n_window,
            "sample_rate_hz": sample_rate,
            "source": "fusi_like_median_centered_local",
            "alpha_peak_hz": round(alpha_peak_hz, 3) if alpha_peak_hz is not None else None,
            "blink_proxy": blink_proxy,
            "noise_spike_count": noise_spike_count,
            "artifact_waveform_spike": bool(noise_spike_count > 0 or blink_proxy > 0),
            "artifact_noise": bool(saturation_pct > 0.0 or packet_gap_count > 0 or peak_to_peak > 7000),
            "peak_to_peak": int(peak_to_peak),
            "saturation_pct": round(saturation_pct, 3),
            "packet_gap_count": packet_gap_count,
            "center_median": round(median, 3),
        }
        for idx, value in enumerate(fusi_features):
            scale = FUSI_MEDITATION_FEATURE_SCALES[idx] or 1.0
            row[f"fusi_meditation_feature_{idx:02d}"] = round(value, 6)
            row[f"fusi_meditation_norm_{idx:02d}"] = round((value - FUSI_MEDITATION_FEATURE_MEANS[idx]) / scale, 6)
        rows.append(row)
    return rows


def compute_live_feature_snapshot(values: list[int], sample_rate: float, stats: StreamStats, hardware_state: dict, battery_percent: int | None) -> dict:
    if not values:
        return {
            "ok": False,
            "source": "rolling_raw_eeg",
            "message": "no_samples",
        }
    window = values[-max(32, min(len(values), int(round(sample_rate * 5.0)))) :]
    count = len(window)
    mean = sum(window) / count
    centered = [float(value) - mean for value in window]
    rms = math.sqrt(sum(value * value for value in centered) / count)
    peak_to_peak = max(window) - min(window)
    saturation_count = sum(1 for value in window if abs(int(value)) >= 8_300_000)
    live_spectrum = dft_power_bins(centered, sample_rate, int(max(1, math.floor(45.0 * count / sample_rate))))
    alpha_candidates = [(freq, power) for freq, power in live_spectrum if 7.0 <= freq <= 13.0]
    alpha_peak_hz = max(alpha_candidates, key=lambda item: item[1])[0] if alpha_candidates else None
    blink_threshold = max(1.0, rms * 4.0)
    blink_proxy = sum(1 for value in centered if abs(value) > blink_threshold)
    diffs = [centered[idx] - centered[idx - 1] for idx in range(1, len(centered))]
    _, diff_std, _, _ = describe_values(diffs)
    spike_threshold = max(1.0, diff_std * 5.0)
    noise_spike_count = sum(1 for value in diffs if abs(value) > spike_threshold)
    bands = compute_native_band_rows(
        [
            {
                "sample_global": index,
                "raw_s24": value,
            }
            for index, value in enumerate(window)
        ],
        sample_rate,
        "live",
    )
    band_snapshot = bands[-1] if bands else {}
    return {
        "ok": True,
        "source": "rolling_raw_eeg",
        "window_s": round(count / sample_rate, 3) if sample_rate else None,
        "sample_count": count,
        "sample_rate_hz": round(sample_rate, 2),
        "rms": round(rms, 3),
        "peak_to_peak": int(peak_to_peak),
        "saturation_pct": round(100.0 * saturation_count / count, 3),
        "alpha_peak_hz": round(alpha_peak_hz, 3) if alpha_peak_hz is not None else None,
        "blink_proxy": blink_proxy,
        "noise_spike_count": noise_spike_count,
        "packet_count": stats.packets,
        "packet_index_gaps": stats.packet_index_gaps,
        "max_inter_packet_gap_s": round(stats.max_inter_packet_gap_s, 3) if stats.max_inter_packet_gap_s is not None else None,
        "contact_state": hardware_state.get("contact_state"),
        "lead_off_center": hardware_state.get("lead_off_center"),
        "lead_off_side": hardware_state.get("lead_off_side"),
        "battery_percent": battery_percent,
        "imu_motion_energy": hardware_state.get("imu_motion_energy"),
        "imu_event_count": hardware_state.get("imu_event_count"),
        "delta_rel": band_snapshot.get("delta_rel"),
        "theta_rel": band_snapshot.get("theta_rel"),
        "alpha_rel": band_snapshot.get("alpha_rel"),
        "low_beta_rel": band_snapshot.get("low_beta_rel"),
        "high_beta_rel": band_snapshot.get("high_beta_rel"),
        "gamma_rel": band_snapshot.get("gamma_rel"),
        "theta_beta": band_snapshot.get("theta_beta"),
        "alpha_theta": band_snapshot.get("alpha_theta"),
    }


def maybe_write_parquet(path: Path, rows: list[dict]) -> bool:
    if not rows:
        return False
    try:
        import pyarrow as pa  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except Exception:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)
    return True


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def safe_ratio(numerator: float, denominator: float) -> float | None:
    return None if denominator <= 0 else numerator / denominator


def cognitive_load_for_context(study_context: dict, condition: str, difficulty: float | None = None) -> float:
    task_id = str(study_context.get("task_id") or study_context.get("test") or condition).lower()
    domain = str(study_context.get("domain_system") or "").lower()
    base = 0.35
    if "baseline" in task_id or "eyes_" in task_id:
        base = 0.18
    elif "flashcard" in task_id or "lexical" in domain:
        base = 0.52
    elif "coniug" in task_id or "grammar" in domain:
        base = 0.64
    elif "stroop" in task_id or "simon" in task_id or "go_nogo" in task_id:
        base = 0.72
    elif "tracking" in task_id or "hand_eye" in task_id or "visuomotor" in domain:
        base = 0.70
    elif "tachistoscope" in task_id:
        base = 0.68
    elif "piano" in task_id:
        base = 0.74
    elif "breathing" in task_id or "meditation" in task_id or "mantra" in task_id:
        base = 0.42
    if isinstance(difficulty, (int, float)) and difficulty > 0:
        base = clamp(base + min(float(difficulty), 10.0) * 0.025)
    adaptive = study_context.get("adaptive_level")
    if isinstance(adaptive, (int, float)):
        base = clamp(base + (float(adaptive) - 1.0) / 12.0 * 0.18)
    return round(clamp(base), 3)


def summarize_behavioral_outcome(study_context: dict) -> dict:
    score = study_context.get("score") if isinstance(study_context.get("score"), dict) else {}
    correct = float(score.get("correct") or score.get("ok") or 0)
    partial = float(score.get("partial") or 0)
    miss = float(score.get("miss") or 0)
    false_start = float(score.get("falseStart") or score.get("false_start") or 0)
    total = correct + partial + miss + false_start
    if total <= 0:
        try:
            total = float(study_context.get("trial_count") or study_context.get("prompt_count") or 0)
        except (TypeError, ValueError):
            total = 0
    accuracy = safe_ratio(correct + partial * 0.5, total)
    latency_values: list[float] = []
    if isinstance(study_context.get("mean_latency_s"), (int, float)):
        latency_values.append(float(study_context["mean_latency_s"]))
    for event in study_context.get("recent_events") or []:
        if isinstance(event, dict) and isinstance(event.get("reaction_ms"), (int, float)):
            latency_values.append(float(event["reaction_ms"]) / 1000.0)
    return {
        "family": study_context.get("family") or "",
        "test": study_context.get("test") or study_context.get("task_id") or "",
        "domain_system": study_context.get("domain_system"),
        "primary_outcomes": study_context.get("primary_outcomes") or [],
        "trial_count": int(total) if total else 0,
        "correct_count": int(correct),
        "partial_count": int(partial),
        "miss_count": int(miss),
        "false_start_count": int(false_start),
        "accuracy": None if accuracy is None else round(clamp(accuracy), 4),
        "performance_score": None if accuracy is None else round(100.0 * clamp(accuracy), 2),
        "mean_latency_s": round(sum(latency_values) / len(latency_values), 3) if latency_values else None,
        "source": "behavioral_task_context" if study_context else "not_recorded",
        "principle": "primary endpoint; biomarkers may contextualize but never override this layer",
    }


def infer_hardware_readiness(
    *,
    sample_completeness: float | None,
    packet_gap_count: int,
    saturation_pct: float,
    packet_rows: list[dict],
    quality_event_rows: list[dict],
    metadata: dict,
) -> dict:
    """Infer the vendor-style headband state ladder from the data we can observe."""
    signal_quality_warning_count = len([row for row in quality_event_rows if row.get("signal_quality_warning")])
    lead_off_events = [row for row in quality_event_rows if row.get("event_type") == "lead_off_status"]
    contact_ok = metadata.get("contact_ok_pct")
    sample_quality = clamp(sample_completeness) if isinstance(sample_completeness, (int, float)) else None
    packet_integrity = clamp(1.0 - (packet_gap_count / max(len(packet_rows), 1)) * 8.0)
    saturation_quality = clamp(1.0 - (float(saturation_pct) / 3.0))
    blockers: list[str] = []
    evidence: dict = {
        "packet_count": len(packet_rows),
        "packet_gap_count": packet_gap_count,
        "sample_completeness": None if sample_quality is None else round(sample_quality, 4),
        "saturation_pct": round(float(saturation_pct), 4),
        "contact_ok_pct": contact_ok,
        "lead_off_event_count": len(lead_off_events),
        "signal_quality_warning_count": signal_quality_warning_count,
        "interrupted": bool(metadata.get("interrupted")),
    }

    if not packet_rows:
        blockers.append("no_eeg_packets")
    if sample_quality is None:
        blockers.append("unknown_sample_completeness")
    elif sample_quality < 0.75:
        blockers.append("low_sample_completeness")
    if packet_gap_count:
        blockers.append("packet_gaps")
    if saturation_pct >= 1.0:
        blockers.append("saturation")
    if signal_quality_warning_count:
        blockers.append("signal_quality_warning")
    if metadata.get("interrupted"):
        blockers.append("interrupted_session")

    contact_score: float | None
    if isinstance(contact_ok, (int, float)):
        contact_score = clamp(float(contact_ok) / 100.0)
        if contact_ok < 70:
            blockers.append("contact_unstable")
        elif contact_ok < 90:
            blockers.append("contact_not_consistently_ok")
    else:
        contact_score = None
        blockers.append("contact_state_not_observed")

    parts = [
        0.20 if packet_rows else 0.0,
        0.25 * (sample_quality if sample_quality is not None else 0.0),
        0.15 * packet_integrity,
        0.15 * saturation_quality,
        0.20 * contact_score if contact_score is not None else 0.05,
        0.05 if not metadata.get("interrupted") else 0.0,
    ]
    readiness_score = clamp(sum(parts) - min(0.20, signal_quality_warning_count * 0.04))

    if not packet_rows:
        inferred_state = "connected_no_eeg_stream"
    elif contact_score is not None and contact_score < 0.70:
        inferred_state = "no_contact_or_unstable_contact"
    elif sample_quality is not None and sample_quality >= 0.90 and packet_gap_count == 0 and saturation_pct < 1.0 and not signal_quality_warning_count:
        inferred_state = "analysis_ready"
    elif contact_score is not None and contact_score >= 0.90:
        inferred_state = "contacted_signal_present"
    elif sample_quality is not None and sample_quality >= 0.60:
        inferred_state = "connected_signal_present"
    else:
        inferred_state = "connected_low_confidence"

    return {
        "source": "local_inference_from_vendor_state_ladder",
        "vendor_state_ladder_reference": [
            "disconnected",
            "connecting",
            "connected",
            "no_contact",
            "contacting",
            "contacted",
            "analyzed",
        ],
        "inferred_state": inferred_state,
        "score": round(readiness_score, 4),
        "display_percent": round(100.0 * readiness_score, 1),
        "blockers": blockers,
        "evidence": evidence,
        "policy": {
            "pause_on_not_contact": False,
            "rule": "poor contact lowers confidence and analysis validity; raw data are kept for diagnostics",
        },
    }


def build_session_manifest_v2(
    *,
    session_id: str,
    condition: str,
    session_json: dict,
    metadata: dict,
    study_context: dict,
    sample_completeness: float | None,
    packet_gap_count: int,
    saturation_pct: float,
    packet_rows: list[dict],
    quality_event_rows: list[dict],
    imu_rows: list[dict],
) -> dict:
    outcome = summarize_behavioral_outcome(study_context)
    duration_min = max(float(session_json.get("duration_s") or 0.0) / 60.0, 0.0)
    contact_ok = metadata.get("contact_ok_pct")
    contact_quality = clamp(float(contact_ok) / 100.0) if isinstance(contact_ok, (int, float)) else None
    sample_quality = clamp(sample_completeness) if isinstance(sample_completeness, (int, float)) else None
    packet_integrity = clamp(1.0 - (packet_gap_count / max(len(packet_rows), 1)) * 8.0)
    saturation_quality = clamp(1.0 - (float(saturation_pct) / 3.0))
    eeg_parts = [value for value in [sample_quality, packet_integrity, saturation_quality, contact_quality] if value is not None]
    eeg_quality = sum(eeg_parts) / len(eeg_parts) if eeg_parts else 0.0
    context_state = study_context.get("state_context") if isinstance(study_context.get("state_context"), dict) else {}
    context_keys = ["sleep", "hrv", "readiness", "glucose", "training_load", "mood", "stress", "subjective_effort"]
    context_completeness = sum(1 for key in context_keys if context_state.get(key) not in (None, "")) / len(context_keys)
    task_total = outcome.get("trial_count") or 0
    task_compliance = 1.0
    if metadata.get("interrupted"):
        task_compliance *= 0.55
    if sample_quality is not None:
        task_compliance *= clamp(0.45 + 0.55 * sample_quality)
    if study_context and task_total <= 0 and not condition.startswith("eyes_"):
        task_compliance *= 0.75
    task_compliance = clamp(task_compliance)
    load = cognitive_load_for_context(study_context, condition, metadata.get("difficulty"))
    cognitive_dose = round(duration_min * load * task_compliance, 4)
    performance_score = outcome.get("performance_score")
    effective_dose = None if performance_score is None else round(cognitive_dose * (performance_score / 100.0), 4)
    subjective_effort = context_state.get("subjective_effort")
    efficiency = None
    if isinstance(subjective_effort, (int, float)) and subjective_effort > 0 and performance_score is not None:
        efficiency = round(performance_score / float(subjective_effort), 4)
    observable = 1.0 if outcome.get("trial_count") else (0.35 if condition.startswith("eyes_") else 0.15)
    hardware_readiness = infer_hardware_readiness(
        sample_completeness=sample_completeness,
        packet_gap_count=packet_gap_count,
        saturation_pct=saturation_pct,
        packet_rows=packet_rows,
        quality_event_rows=quality_event_rows,
        metadata=metadata,
    )
    readiness_component = float(hardware_readiness.get("score") or 0.0)
    confidence = clamp(0.32 * eeg_quality + 0.18 * readiness_component + 0.25 * task_compliance + 0.15 * observable + 0.10 * context_completeness)
    if metadata.get("interrupted"):
        confidence *= 0.75
    return {
        "schema_version": "mindtune_session_manifest_v2",
        "session_id": session_id,
        "condition": condition,
        "created_at_utc": utc_now_iso(),
        "principles": [
            "observable performance is the primary endpoint",
            "state variables contextualize performance",
            "biomarkers qualify interpretation but never override outcomes",
            "confidence describes trust in interpretation, not success",
        ],
        "level_1_outcome": outcome,
        "level_2_state": {
            "context": context_state,
            "context_completeness": round(context_completeness, 4),
            "known_state_keys": [key for key in context_keys if context_state.get(key) not in (None, "")],
        },
        "level_3_biomarkers": {
            "eeg_quality": round(100.0 * eeg_quality, 2),
            "eeg_quality_components": {
                "sample_completeness": None if sample_quality is None else round(sample_quality, 4),
                "packet_integrity": round(packet_integrity, 4),
                "saturation_quality": round(saturation_quality, 4),
                "contact_quality": None if contact_quality is None else round(contact_quality, 4),
            },
            "motion_quality": 82.0 if imu_rows else None,
            "motion_source": "imu_present_unscaled" if imu_rows else "imu_absent",
            "quality_event_count": len(quality_event_rows),
            "imu_event_count": len(imu_rows),
            "biomarker_note": "biomarkers are reliability/context signals, not final performance targets",
        },
        "hardware_readiness": hardware_readiness,
        "dose": {
            "duration_min": round(duration_min, 4),
            "cognitive_load": load,
            "task_compliance": round(task_compliance, 4),
            "cognitive_dose": cognitive_dose,
            "effective_dose": effective_dose,
            "formula": "cognitive_dose = minutes * cognitive_load * task_compliance; effective_dose multiplies by performance_score",
        },
        "efficiency": {
            "performance_per_subjective_effort": efficiency,
            "subjective_effort": subjective_effort,
            "note": "available once subjective effort is collected consistently",
        },
        "confidence": {
            "score": round(confidence, 4),
            "display_percent": round(100.0 * confidence, 1),
            "components": {
                "signal_quality": round(eeg_quality, 4),
                "hardware_readiness": round(readiness_component, 4),
                "task_compliance": round(task_compliance, 4),
                "outcome_observability": round(observable, 4),
                "context_completeness": round(context_completeness, 4),
            },
        },
        "longitudinal_tags": {
            "candidate_indices": [
                "learning_velocity",
                "retention_index",
                "re_entry_index",
                "recovery_index",
                "cognitive_resilience",
                "consistency_score",
                "fatigue_resistance",
            ],
            "requires_history": True,
        },
    }


def create_mindtune_v2_package(args, csv_path: Path, metadata: dict) -> Path:
    sample_rate = float(metadata.get("sample_rate_est_hz") or 247.0)
    if not (100.0 <= sample_rate <= 500.0):
        sample_rate = 247.0
    condition = safe_piece(str(metadata.get("condition") or args.condition), "session")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    session_id = f"mtl_{stamp}_{condition}_fc11"
    session_dir = MINDTUNE_V2_OUTPUT / f"{stamp}__{condition}__{session_id}"
    counter = 2
    while session_dir.exists():
        session_dir = MINDTUNE_V2_OUTPUT / f"{stamp}__{condition}__{session_id}_{counter}"
        counter += 1
    session_dir.mkdir(parents=True, exist_ok=False)

    samples_rows: list[dict] = []
    packets: dict[int, dict] = {}
    first_ts: float | None = None
    last_ts: float | None = None
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                sample_global = int(row.get("sample_global") or 0)
                ts = float(row.get("ts") or 0)
                raw_s24 = int(row.get("raw_s24") or 0)
            except (TypeError, ValueError):
                continue
            packet_value = row.get("packet_index")
            try:
                sequence_num = int(packet_value) if packet_value not in (None, "") else None
            except (TypeError, ValueError):
                sequence_num = None
            if first_ts is None:
                first_ts = ts
            last_ts = ts
            packet_index = sequence_num if sequence_num is not None else -1
            if sequence_num is not None and sequence_num not in packets:
                packets[sequence_num] = {
                    "session_id": session_id,
                    "packet_index": len(packets),
                    "sequence_num": sequence_num,
                    "packet_time_utc": utc_from_ts(ts),
                    "sample_rate_hz": sample_rate,
                    "packet_sample_count": 0,
                    "packet_gap": None,
                    "contact_state": None,
                    "lead_off_center": None,
                    "lead_off_side": None,
                    "signal_quality_warning": None,
                    "orientation": None,
                    "raw_payload_len": None,
                }
            if sequence_num is not None:
                packets[sequence_num]["packet_sample_count"] += 1
            t_rel = sample_global / sample_rate
            samples_rows.append(
                {
                    "session_id": session_id,
                    "sample_global": sample_global,
                    "packet_index": packet_index,
                    "sequence_num": sequence_num,
                    "sample_in_packet": packets[sequence_num]["packet_sample_count"] - 1 if sequence_num is not None else None,
                    "t_rel_s": t_rel,
                    "t_abs_utc": utc_from_ts((first_ts or ts) + t_rel),
                    "raw_s24": raw_s24,
                    "eeg_value": round(raw_s24 * FC11_VENDOR_UV_PER_COUNT, 9),
                    "eeg_unit": "vendor_inferred_uV",
                    "physical_scaling_status": FC11_SCALING_STATUS,
                    "quality_flag": "unreviewed",
                }
            )

    packet_rows = [packets[key] for key in sorted(packets)]
    prev_seq: int | None = None
    packet_gap_count = 0
    max_packet_gap = 0
    for row in packet_rows:
        seq = int(row["sequence_num"])
        if prev_seq is None:
            row["packet_gap"] = None
        else:
            gap = max(0, seq - prev_seq - 1)
            row["packet_gap"] = gap
            if gap:
                packet_gap_count += 1
                max_packet_gap = max(max_packet_gap, gap)
        prev_seq = seq

    expected_samples = int(round((metadata.get("duration_requested_s") or 0) * sample_rate))
    saturation_count = sum(1 for row in samples_rows if abs(int(row["raw_s24"])) >= 8_300_000)
    saturation_pct = (100.0 * saturation_count / len(samples_rows)) if samples_rows else 0.0
    started_utc = utc_from_ts(first_ts) if first_ts else utc_now_iso()
    ended_utc = utc_from_ts(last_ts) if last_ts else started_utc
    validity = "diagnostic" if metadata.get("interrupted") or not samples_rows else "unknown_until_quality_check"
    parquet_written = {
        "samples": maybe_write_parquet(session_dir / "samples.parquet", samples_rows),
        "packets": maybe_write_parquet(session_dir / "packets.parquet", packet_rows),
    }
    write_csv_rows(session_dir / "samples.csv", list(samples_rows[0].keys()) if samples_rows else [
        "session_id", "sample_global", "packet_index", "sequence_num", "sample_in_packet",
        "t_rel_s", "t_abs_utc", "raw_s24", "eeg_value", "eeg_unit",
        "physical_scaling_status", "quality_flag",
    ], samples_rows)
    write_csv_rows(session_dir / "packets.csv", list(packet_rows[0].keys()) if packet_rows else [
        "session_id", "packet_index", "sequence_num", "packet_time_utc", "sample_rate_hz",
        "packet_sample_count", "packet_gap", "contact_state", "lead_off_center",
        "lead_off_side", "signal_quality_warning", "orientation", "raw_payload_len",
    ], packet_rows)
    event_rows = [
        {
            "session_id": session_id,
            "event_time_utc": started_utc,
            "t_rel_s": 0.0,
            "event_type": "start",
            "task_id": condition,
            "block_id": "",
            "trial_id": "",
            "raw_value": "",
            "derived_value": "",
            "response": "",
            "correct": "",
            "confidence": "",
        },
        {
            "session_id": session_id,
            "event_time_utc": ended_utc,
            "t_rel_s": len(samples_rows) / sample_rate if samples_rows else 0.0,
            "event_type": "interrupted" if metadata.get("interrupted") else "stop",
            "task_id": condition,
            "block_id": "",
            "trial_id": "",
            "raw_value": "",
            "derived_value": "",
            "response": "",
            "correct": "",
            "confidence": "",
        },
    ]
    maybe_write_parquet(session_dir / "events.parquet", event_rows)
    write_csv_rows(session_dir / "events.csv", list(event_rows[0].keys()), event_rows)

    quality_event_rows: list[dict] = []
    for item in metadata.get("quality_events") or []:
        if not isinstance(item, dict):
            continue
        row = {
            "session_id": session_id,
            "event_time_utc": item.get("event_time_utc") or utc_from_ts(item.get("ts") or time.time()),
            "t_rel_s": item.get("t_rel_s"),
            "event_type": item.get("event_type"),
            "contact_state": item.get("contact_state"),
            "lead_off_center": item.get("lead_off_center"),
            "lead_off_side": item.get("lead_off_side"),
            "signal_quality_warning": item.get("signal_quality_warning"),
            "battery_percent": item.get("battery_percent"),
            "source": item.get("source") or "cmsn_proprietary_payload",
            "raw_value": item.get("raw_value"),
        }
        quality_event_rows.append(row)
    if quality_event_rows:
        maybe_write_parquet(session_dir / "quality_events.parquet", quality_event_rows)
        write_csv_rows(session_dir / "quality_events.csv", list(quality_event_rows[0].keys()), quality_event_rows)
    else:
        write_csv_rows(session_dir / "quality_events.csv", [
            "session_id", "event_time_utc", "t_rel_s", "event_type", "contact_state",
            "lead_off_center", "lead_off_side", "signal_quality_warning",
            "battery_percent", "source", "raw_value",
        ], [])

    imu_rows: list[dict] = []
    for item in metadata.get("imu_rows") or []:
        if not isinstance(item, dict):
            continue
        imu_rows.append({
            "session_id": session_id,
            "event_time_utc": item.get("event_time_utc") or utc_from_ts(item.get("ts") or time.time()),
            "t_rel_s": item.get("t_rel_s"),
            "packet_index": item.get("packet_index"),
            "source": "cmsn_imu_payload",
            "motion_energy": item.get("motion_energy"),
            "imu_json": json.dumps(item.get("imu") or {}, ensure_ascii=False, sort_keys=True),
        })
    if imu_rows:
        maybe_write_parquet(session_dir / "imu.parquet", imu_rows)
        write_csv_rows(session_dir / "imu.csv", list(imu_rows[0].keys()), imu_rows)
    else:
        write_csv_rows(session_dir / "imu.csv", [
            "session_id", "event_time_utc", "t_rel_s", "packet_index", "source", "motion_energy", "imu_json",
        ], [])

    native_band_rows = compute_native_band_rows(samples_rows, sample_rate, session_id)
    if native_band_rows:
        parquet_written["native_bands"] = maybe_write_parquet(session_dir / "native_bands.parquet", native_band_rows)
        write_csv_rows(session_dir / "native_bands.csv", list(native_band_rows[0].keys()), native_band_rows)
    else:
        parquet_written["native_bands"] = False
        write_csv_rows(session_dir / "native_bands.csv", [
            "session_id", "window_index", "start_t_rel_s", "end_t_rel_s", "sample_count",
            "sample_rate_hz", "source", "delta_power", "theta_power", "alpha_power",
            "low_beta_power", "high_beta_power", "gamma_power", "beta_power",
            "delta_rel", "theta_rel", "alpha_rel", "low_beta_rel", "high_beta_rel",
            "gamma_rel", "beta_rel", "alpha_theta", "theta_beta", "low_high_beta",
        ], [])

    brainlab_feature_rows = compute_brainlab_feature_rows(samples_rows, sample_rate, session_id)
    if brainlab_feature_rows:
        parquet_written["brainlab_features"] = maybe_write_parquet(session_dir / "brainlab_features.parquet", brainlab_feature_rows)
        write_csv_rows(session_dir / "brainlab_features.csv", list(brainlab_feature_rows[0].keys()), brainlab_feature_rows)
    else:
        parquet_written["brainlab_features"] = False
        feature_headers = [f"fusi_meditation_feature_{idx:02d}" for idx in range(33)]
        norm_headers = [f"fusi_meditation_norm_{idx:02d}" for idx in range(33)]
        write_csv_rows(session_dir / "brainlab_features.csv", [
            "session_id", "window_index", "start_t_rel_s", "end_t_rel_s", "sample_count",
            "sample_rate_hz", "source", "alpha_peak_hz", "blink_proxy", "noise_spike_count",
            "artifact_waveform_spike", "artifact_noise", "peak_to_peak", "saturation_pct",
            "packet_gap_count", "center_median", *feature_headers, *norm_headers,
        ], [])

    raw_values = [int(row["raw_s24"]) for row in samples_rows]
    scientific_qc_rows, scientific_qc = analyze_windows(raw_values, sample_rate)
    for row in scientific_qc_rows:
        row["session_id"] = session_id
    write_csv_rows(
        session_dir / "scientific_qc_windows.csv",
        list(scientific_qc_rows[0].keys()) if scientific_qc_rows else [
            "window_index", "start_t_rel_s", "end_t_rel_s", "sample_count",
            "median_adc_count", "mad_adc_count", "robust_sigma_adc_count",
            "peak_to_peak_adc_count", "median_vendor_inferred_uV",
            "robust_sigma_vendor_inferred_uV", "peak_to_peak_vendor_inferred_uV",
            "clipped_fraction", "repeated_sample_fraction",
            "abrupt_jump_fraction", "line_noise_50hz_ratio", "qc_pass", "qc_flags", "qc_warnings", "session_id",
        ],
        scientific_qc_rows,
    )
    (session_dir / "scientific_qc.json").write_text(
        json.dumps(scientific_qc, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    scientific_spectral_rows, scientific_spectral = compute_spectral_windows(
        raw_values, sample_rate, scientific_qc_rows
    )
    for row in scientific_spectral_rows:
        row["session_id"] = session_id
    spectral_headers = [
        "window_index", "start_t_rel_s", "end_t_rel_s", "sample_count", "sample_rate_hz",
        "frequency_resolution_hz", "psd_unit", "physical_scaling_status", "qc_pass",
        "qc_flags", "qc_warnings", "alpha_peak_hz", "delta_power_uV2", "delta_relative",
        "theta_power_uV2", "theta_relative", "alpha_power_uV2", "alpha_relative",
        "low_beta_power_uV2", "low_beta_relative", "high_beta_power_uV2", "high_beta_relative",
        "gamma_power_uV2", "gamma_relative", "total_0_5_45_power_uV2", "session_id",
    ]
    write_csv_rows(
        session_dir / "scientific_spectral_windows.csv",
        list(scientific_spectral_rows[0].keys()) if scientific_spectral_rows else spectral_headers,
        scientific_spectral_rows,
    )
    (session_dir / "scientific_spectral.json").write_text(
        json.dumps(scientific_spectral, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_csv_rows(session_dir / "channels.tsv", [
        "name", "type", "unit", "status", "description",
    ], [{
        "name": "FC11_single_channel",
        "type": "EEG",
        "unit": "vendor_inferred_uV",
        "status": FC11_SCALING_STATUS,
        "description": f"FC11 single channel; raw signed 24-bit counts retained in samples.csv; converted with {FC11_VENDOR_UV_PER_COUNT:.12f} uV/count matched to BrainCo Crimson SDK 1.4.9. Not independently calibrated.",
    }])

    session_json = {
        "schema_version": "mindtune_session_v2",
        "session_id": session_id,
        "app": "MindTune Lab",
        "device_family": "FC11_Crimson",
        "vendor_app_reference": "vendor native app / SDK only",
        "protocol": condition,
        "condition": condition,
        "started_at_utc": started_utc,
        "ended_at_utc": ended_utc,
        "duration_s": len(samples_rows) / sample_rate if samples_rows else 0.0,
        "duration_requested_s": metadata.get("duration_requested_s"),
        "sample_rate_hz": sample_rate,
        "sample_rate_source": "estimated_from_received_sample_count_and_monotonic_session_duration",
        "sample_count": len(samples_rows),
        "packet_count": len(packet_rows),
        "quality_event_count": len(quality_event_rows),
        "imu_event_count": len(imu_rows),
        "native_band_window_count": len(native_band_rows),
        "brainlab_feature_window_count": len(brainlab_feature_rows),
        "scientific_spectral_window_count": len(scientific_spectral_rows),
        "timezone": local_tz_name(),
        "operator": "Andrea",
        "notes_file": "notes.md",
        "validity": validity,
        "legacy_csv_source": str(csv_path),
        "parquet_written": parquet_written,
        "csv_fallback_written": True,
        "signal_units": {
            "raw_stored": "adc_count",
            "eeg_value": "vendor_inferred_uV",
            "vendor_inferred_uV_per_count": FC11_VENDOR_UV_PER_COUNT,
            "physical_scaling_status": FC11_SCALING_STATUS,
        },
        "scientific_qc": "scientific_qc.json",
        "scientific_qc_windows": "scientific_qc_windows.csv",
        "scientific_spectral": "scientific_spectral.json",
        "scientific_spectral_windows": "scientific_spectral_windows.csv",
    }
    if isinstance(metadata.get("study_context"), dict) and metadata.get("study_context"):
        session_json["study_context"] = metadata["study_context"]
    quality = {
        "session_id": session_id,
        "packet_count": len(packet_rows),
        "sample_count": len(samples_rows),
        "expected_samples": expected_samples,
        "packet_gap_count": packet_gap_count,
        "max_packet_gap": max_packet_gap,
        "contact_ok_pct": metadata.get("contact_ok_pct"),
        "lead_off_events": len([row for row in quality_event_rows if row.get("event_type") == "lead_off_status"]),
        "signal_quality_warning_count": len([row for row in quality_event_rows if row.get("signal_quality_warning")]),
        "saturation_pct": saturation_pct,
        "imu_event_count": len(imu_rows),
        "native_band_window_count": len(native_band_rows),
        "brainlab_feature_window_count": len(brainlab_feature_rows),
        "scientific_spectral_window_count": len(scientific_spectral_rows),
        "scientific_spectral_clean_window_count": scientific_spectral.get("clean_window_count"),
        "artifact_windows": sum(1 for row in scientific_qc_rows if not row["qc_pass"]),
        "clean_window_fraction": scientific_qc.get("clean_window_fraction"),
        "qc_warning_windows": scientific_qc.get("warning_window_count"),
        "qc_warning_window_fraction": scientific_qc.get("warning_window_fraction"),
        "valid_for_analysis": bool(
            samples_rows
            and not metadata.get("interrupted")
            and packet_gap_count == 0
            and not any(row.get("contact_state") == "bad" for row in quality_event_rows)
        ),
        "validity": validity,
        "quality_notes": [
            "Mac recorder v2 package generated from BLE payload parsed locally.",
            "lead_off/IMU/proprietary status are decoded when present in CMSN notifications.",
            "native_bands.csv contains local raw-EEG derived bands, not vendor model scores.",
            "brainlab_features.csv contains transparent fusi-like local features, not vendor model scores.",
            "scientific_spectral files contain QC-gated Hann PSD and band powers in vendor-inferred physical units; no focus or mental-state score.",
            f"Raw ADC counts are retained; eeg_value uses {FC11_VENDOR_UV_PER_COUNT:.12f} vendor-inferred uV/count matched to BrainCo Crimson SDK 1.4.9.",
            "The uV conversion is vendor-matched but not an independent metrological calibration.",
            "QC thresholds are engineering defaults, versioned and not yet clinically validated.",
            "Parquet files are written only when pyarrow is available; CSV fallback is always present.",
        ],
    }
    sample_completeness = None if expected_samples <= 0 else safe_ratio(len(samples_rows), expected_samples)
    study_context = session_json.get("study_context") if isinstance(session_json.get("study_context"), dict) else {}
    manifest_v2 = build_session_manifest_v2(
        session_id=session_id,
        condition=condition,
        session_json=session_json,
        metadata=metadata,
        study_context=study_context,
        sample_completeness=sample_completeness,
        packet_gap_count=packet_gap_count,
        saturation_pct=saturation_pct,
        packet_rows=packet_rows,
        quality_event_rows=quality_event_rows,
        imu_rows=imu_rows,
    )
    quality["hardware_readiness"] = manifest_v2["hardware_readiness"]
    quality["valid_for_analysis"] = bool(
        quality["valid_for_analysis"]
        and (sample_completeness is None or sample_completeness >= 0.95)
        and (scientific_qc.get("clean_window_fraction") is not None)
        and float(scientific_qc.get("clean_window_fraction") or 0.0) >= 0.80
        and int((metadata.get("pipeline_extras") or {}).get("queue_overflow_count") or 0) == 0
        and not bool((metadata.get("pipeline_extras") or {}).get("incomplete_drain"))
        and manifest_v2["hardware_readiness"].get("inferred_state") in {"analysis_ready", "contacted_signal_present"}
        and float(manifest_v2["hardware_readiness"].get("score") or 0.0) >= 0.75
    )
    quality["analysis_gate"] = {
        "passed": quality["valid_for_analysis"],
        "requirements": {
            "sample_completeness_gte": 0.95,
            "clean_window_fraction_gte": 0.80,
            "packet_gap_count_eq": 0,
            "raw_queue_overflow_count_eq": 0,
            "incomplete_drain_eq": False,
            "hardware_readiness_score_gte": 0.75,
        },
        "scope": "research-analysis eligibility; not medical-device certification",
    }
    score_row = {
        "session_id": session_id,
        "condition": condition,
        "performance_score": manifest_v2["level_1_outcome"].get("performance_score"),
        "accuracy": manifest_v2["level_1_outcome"].get("accuracy"),
        "trial_count": manifest_v2["level_1_outcome"].get("trial_count"),
        "mean_latency_s": manifest_v2["level_1_outcome"].get("mean_latency_s"),
        "context_completeness": manifest_v2["level_2_state"].get("context_completeness"),
        "eeg_quality": manifest_v2["level_3_biomarkers"].get("eeg_quality"),
        "motion_quality": manifest_v2["level_3_biomarkers"].get("motion_quality"),
        "hardware_readiness_state": manifest_v2["hardware_readiness"].get("inferred_state"),
        "hardware_readiness_score": manifest_v2["hardware_readiness"].get("score"),
        "cognitive_load": manifest_v2["dose"].get("cognitive_load"),
        "task_compliance": manifest_v2["dose"].get("task_compliance"),
        "cognitive_dose": manifest_v2["dose"].get("cognitive_dose"),
        "effective_dose": manifest_v2["dose"].get("effective_dose"),
        "efficiency": manifest_v2["efficiency"].get("performance_per_subjective_effort"),
        "confidence": manifest_v2["confidence"].get("score"),
        "confidence_percent": manifest_v2["confidence"].get("display_percent"),
    }
    write_csv_rows(session_dir / "session_scores.csv", list(score_row.keys()), [score_row])
    session_json["session_manifest_v2"] = "session_manifest_v2.json"
    session_json["session_scores"] = "session_scores.csv"
    (session_dir / "session.json").write_text(json.dumps(session_json, indent=2), encoding="utf-8")
    (session_dir / "quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    (session_dir / "session_manifest_v2.json").write_text(json.dumps(manifest_v2, indent=2, ensure_ascii=False), encoding="utf-8")
    provenance = {
        "schema_version": "mindtune_provenance_v1",
        "created_at_utc": utc_now_iso(),
        "recorder": "MindTune Lab FC11 macOS capture",
        "python_version": sys.version.split()[0],
        "scientific_qc_algorithm_version": SCIENTIFIC_QC_VERSION,
        "scientific_spectral_algorithm_version": SCIENTIFIC_SPECTRAL_VERSION,
        "scientific_longitudinal_algorithm_version": SCIENTIFIC_LONGITUDINAL_VERSION,
        "raw_signal_immutable_principle": True,
        "signal_unit": "adc_count",
        "physical_scaling": {
            "status": FC11_SCALING_STATUS,
            "vendor_inferred_uV_per_count": FC11_VENDOR_UV_PER_COUNT,
            "evidence": "BrainCo Crimson SDK 1.4.9 simultaneous raw notification/eegData comparison, 7150 samples, passband coherence >0.99998",
        },
        "derived_files": {
            "native_bands.csv": "local DFT; 5 s non-overlapping windows; amplitudes in squared ADC-count domain",
            "brainlab_features.csv": "experimental transparent local features; not vendor scores",
            "scientific_qc_windows.csv": "engineering QC; formulas and thresholds in scientific_qc.json",
            "scientific_spectral_windows.csv": "periodic-Hann one-sided PSD; 2 s non-overlapping windows; uV^2/Hz; QC flags retained",
            "scientific_spectral.json": "clean-window descriptive aggregation only; no cognitive-state inference",
        },
        "known_limitations": [
            "single-channel montage/electrode reference not independently confirmed",
            "volts-per-count is matched to the vendor SDK but not independently confirmed with a calibrated signal generator",
            "no clinical or diagnostic claim",
            "artifact thresholds require validation on labelled FC11 datasets",
        ],
    }
    (session_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8")
    update_longitudinal_outputs(MINDTUNE_V2_OUTPUT)
    (session_dir / "notes.md").write_text(
        "# Session notes\n\n"
        f"Protocol: {condition}\n"
        f"Started: {started_utc}\n"
        f"Ended: {ended_utc}\n\n"
        "## Subjective state before\n\n"
        "## Subjective state after\n\n"
        "## Did I fall asleep?\n\n"
        "- no\n- maybe\n- yes\n- unknown\n\n"
        "## Interruptions / movements\n\n"
        "## Headband contact notes\n\n"
        "## Other context\n",
        encoding="utf-8",
    )
    checksum_rows = sha256_manifest(session_dir, {"checksums.sha256"})
    with (session_dir / "checksums.sha256").open("w", encoding="utf-8") as handle:
        for item in checksum_rows:
            handle.write(f'{item["sha256"]}  {item["file"]}\n')
    metadata["mindtune_session_v2_dir"] = str(session_dir)
    metadata["mindtune_session_id"] = session_id
    return session_dir


def device_summary(device) -> dict:
    details = getattr(device, "details", None)
    return {
        "name": device.name,
        "address_or_identifier": device.address,
        "details_type": type(details).__name__ if details is not None else "",
    }


def load_cached_device() -> dict | None:
    try:
        payload = json.loads(DEVICE_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not payload.get("address_or_identifier"):
        return None
    return payload


def save_cached_device(device) -> None:
    if isinstance(device, str):
        return
    payload = {
        **device_summary(device),
        "seen_at": time.time(),
        "seen_at_label": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    DEVICE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DEVICE_CACHE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def play_ding() -> None:
    afplay = shutil.which("afplay")
    if afplay and MAC_DING.exists():
        subprocess.Popen([afplay, str(MAC_DING)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def wait_for_start_signal(args, csv_path: Path, battery_percent: int | None, is_connected=None, refresh_status=None, client=None, write_char=None) -> int | None:
    signal_file = getattr(args, "start_signal_file", None)
    if not signal_file:
        return battery_percent
    path = Path(signal_file)
    if path.exists():
        path.unlink()
    write_status(
        args,
        "connected",
        condition=args.condition,
        duration=args.duration,
        prep=args.prep,
        csv=str(csv_path),
        battery_percent=battery_percent,
        waiting_for_start=True,
        samples=0,
        packets=0,
    )
    if client and write_char:
        await apply_helmet_led(client, write_char, args, "connected", battery_percent)
    print("CONNESSIONE STABILITA: in attesa di Start dalla console.", flush=True)
    last_refresh_at = 0.0
    refresh_extra = {}
    while not path.exists():
        if is_connected is not None and not is_connected():
            message = "Casco disconnesso prima dello Start."
            write_status(
                args,
                "error",
                condition=args.condition,
                duration=args.duration,
                prep=args.prep,
                csv=str(csv_path),
                battery_percent=None,
                waiting_for_start=False,
                samples=0,
                packets=0,
                error=message,
            )
            raise RuntimeError(message)
        if refresh_status is not None and time.time() - last_refresh_at >= 5.0:
            last_refresh_at = time.time()
            try:
                refreshed = await refresh_status()
            except Exception as exc:
                refreshed = {"link_warning": f"controllo BLE fallito: {exc!r}"}
            if isinstance(refreshed, dict):
                new_battery = refreshed.get("battery_percent")
                if isinstance(new_battery, int):
                    battery_percent = max(0, min(100, new_battery))
                refresh_extra = {k: v for k, v in refreshed.items() if k != "battery_percent"}
        write_status(
            args,
            "connected",
            condition=args.condition,
            duration=args.duration,
            prep=args.prep,
            csv=str(csv_path),
            battery_percent=battery_percent,
            waiting_for_start=True,
            samples=0,
            packets=0,
            **refresh_extra,
        )
        await asyncio.sleep(0.2)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        condition = str(payload.get("condition") or args.condition)
        if condition and all(ch.isalnum() or ch in "_-" for ch in condition):
            args.condition = condition[:64]
        try:
            args.duration = max(5, min(7200, int(payload.get("duration", args.duration))))
        except (TypeError, ValueError):
            pass
        try:
            args.prep = max(0, min(600, int(payload.get("prep", args.prep))))
        except (TypeError, ValueError):
            pass
        if isinstance(payload.get("study_context"), dict):
            args.study_context = payload.get("study_context")
    write_status(
        args,
        "starting",
        condition=args.condition,
        duration=args.duration,
        prep=args.prep,
        csv=str(csv_path),
        battery_percent=battery_percent,
        waiting_for_start=False,
        samples=0,
        packets=0,
    )
    if client and write_char:
        await apply_helmet_led(client, write_char, args, "starting", battery_percent)
    print("START RICEVUTO: preparo lo streaming.", flush=True)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return battery_percent


def next_session_paths(args) -> tuple[Path, Path]:
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    base = outdir / f"session_{args.condition}_{stamp}"
    out = base.with_suffix(".csv")
    counter = 2
    while out.exists() or out.with_suffix(".json").exists():
        out = outdir / f"{base.name}_{counter}.csv"
        counter += 1
    return out, out.with_suffix(".json")


def consume_stop_signal(args) -> bool:
    signal_file = getattr(args, "stop_signal_file", None)
    if not signal_file:
        return False
    path = Path(signal_file)
    if not path.exists():
        return False
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return True


async def consume_command_signal(args, client, write_char, msg_id: int, quiet: bool = False) -> int:
    """
    Controlla --command-signal-file e invia comandi hardware opzionali.
    Ritorna il msg_id aggiornato.
    """
    signal_file = getattr(args, "command_signal_file", None)
    if not signal_file:
        return msg_id
    path = Path(signal_file)
    if not path.exists():
        return msg_id
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"COMMAND signal parse error: {exc!r}", flush=True)
        payload = {}
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    if not isinstance(payload, dict):
        return msg_id
    cmd_type = payload.get("type")
    try:
        if cmd_type == "led_color":
            r = int(payload.get("r", 0))
            g = int(payload.get("g", 0))
            b = int(payload.get("b", 0))
            enc = payload.get("encoding", "varint")
            await send_frame(client, write_char, "SET_LED_COLOR", make_led_color(r, g, b, msg_id, color_encoding=enc), quiet=quiet)
            msg_id += 1
            print(f"LED color inviato: r={r} g={g} b={b} encoding={enc}", flush=True)
        elif cmd_type == "vibration":
            intensity = int(payload.get("intensity", 50))
            await send_frame(client, write_char, "SET_VIBRATION_INTENSITY", make_vibration(intensity, msg_id), quiet=quiet)
            msg_id += 1
            print(f"Vibration inviata: intensity={intensity}", flush=True)
    except Exception as exc:
        print(f"COMMAND send failed: {exc!r}", flush=True)
    return msg_id


def looks_like_fc11(device, advertisement_data) -> bool:
    uuids = {u.lower() for u in (advertisement_data.service_uuids or [])}
    name = (device.name or "").lower()
    return (
        SERVICE_UUID.lower() in uuids
        or "focus" in name
        or "brainco" in name
        or "fc11" in name
        or "crimson" in name
    )


async def discover_device(seconds: float, requested: str | None = None):
    require_bleak()

    # On macOS an FC11 that is already connected no longer advertises, so a
    # scanner-only lookup cannot find it.  CoreBluetooth can still retrieve a
    # previously seen peripheral by its stable UUID.  Return a BLEDevice with
    # the native peripheral details so BleakClient does not start another scan.
    candidate_id = requested
    if not candidate_id:
        cached = load_cached_device()
        candidate_id = cached["address_or_identifier"] if cached else None
    if candidate_id and sys.platform == "darwin":
        try:
            from Foundation import NSArray, NSUUID
            from bleak.backends.device import BLEDevice

            scanner = BleakScanner()
            backend = scanner._backend
            manager = backend._manager.central_manager.delegate()
            identifier = NSUUID.alloc().initWithUUIDString_(candidate_id)
            identifiers = NSArray.alloc().initWithArray_([identifier])
            peripherals = backend._manager.central_manager.retrievePeripheralsWithIdentifiers_(identifiers)
            if peripherals:
                peripheral = peripherals[0]
                device = BLEDevice(
                    peripheral.identifier().UUIDString(),
                    peripheral.name(),
                    (peripheral, manager),
                    rssi=0,
                )
                save_cached_device(device)
                return device
        except Exception as exc:
            print(f"CoreBluetooth cached-device lookup failed: {exc!r}", flush=True)

    if requested:
        return requested

    cached = load_cached_device()
    if cached:
        cached_id = cached["address_or_identifier"]
        cached_timeout = min(max(1.0, seconds), 5.0)
        try:
            device = await BleakScanner.find_device_by_address(cached_id, timeout=cached_timeout)
        except Exception:
            device = None
        if device:
            save_cached_device(device)
            return device

    found = []

    def on_detect(device, advertisement_data):
        if looks_like_fc11(device, advertisement_data):
            found.append((device, advertisement_data))

    scanner = BleakScanner(detection_callback=on_detect)
    await scanner.start()
    await asyncio.sleep(seconds)
    await scanner.stop()

    if found:
        save_cached_device(found[0][0])
        return found[0][0]

    devices = await BleakScanner.discover(timeout=max(1.0, seconds))
    for device in devices:
        if device.name and any(token in device.name.lower() for token in ("focus", "brainco", "fc11", "crimson")):
            save_cached_device(device)
            return device
    raise RuntimeError("Casco FC11 non trovato. Accendilo, tieni spenta l'app ufficiale sul telefono e riprova.")


async def get_services(client):
    try:
        return client.services
    except Exception:
        backend = getattr(client, "_backend", None)
        get_services = getattr(backend, "_get_services", None)
        if get_services is None:
            raise
        return await get_services()


async def read_battery_percent(client) -> int | None:
    try:
        services = await get_services(client)
        battery_char = services.get_characteristic(BATTERY_UUID)
        if battery_char is None:
            return None
        raw = await client.read_gatt_char(battery_char)
    except Exception:
        return None
    if not raw:
        return None
    return max(0, min(100, int(raw[0])))


async def resolve_gatt(client):
    services = await get_services(client)

    write_char = services.get_characteristic(WRITE_UUID)
    notify_char = services.get_characteristic(NOTIFY_UUID)
    if write_char is None or notify_char is None:
        available = sorted({getattr(char, "uuid", "") for char in services.characteristics.values()})
        raise RuntimeError(
            "Caratteristiche FC11 non trovate. "
            f"WRITE={WRITE_UUID} NOTIFY={NOTIFY_UUID} disponibili={available}"
        )
    return write_char, notify_char


async def send_frame(client, write_char, label: str, frame: bytes, quiet: bool = False) -> None:
    if not quiet:
        print("SEND", label, flush=True)
    try:
        await asyncio.wait_for(
            client.write_gatt_char(WRITE_UUID, frame, response=False),
            timeout=BLE_WRITE_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        print(f"SEND {label} timeout senza risposta; riprovo con conferma GATT.", flush=True)
        await asyncio.wait_for(
            client.write_gatt_char(WRITE_UUID, frame, response=True),
            timeout=BLE_WRITE_TIMEOUT_S,
        )
    except Exception as exc:
        if "Service Discovery has not been performed yet" not in str(exc):
            raise
        await get_services(client)
        await asyncio.wait_for(
            client.write_gatt_char(WRITE_UUID, frame, response=False),
            timeout=BLE_WRITE_TIMEOUT_S,
        )
    await asyncio.sleep(2.0)


async def _write_frame_with_service_retry(client, write_char, frame: bytes) -> None:
    try:
        await client.write_gatt_char(WRITE_UUID, frame, response=False)
    except Exception as exc:
        if "Service Discovery has not been performed yet" not in str(exc):
            raise
        await get_services(client)
        await client.write_gatt_char(WRITE_UUID, frame, response=False)


async def send_frame_unconfirmed(client, write_char, label: str, frame: bytes, quiet: bool = False) -> asyncio.Task:
    if not quiet:
        print("SEND", label, "(senza attesa conferma CoreBluetooth)", flush=True)
    task = asyncio.create_task(_write_frame_with_service_retry(client, write_char, frame))

    def report_result(done: asyncio.Task) -> None:
        try:
            done.result()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            print(f"SEND {label} background failed: {exc!r}", flush=True)

    task.add_done_callback(report_result)
    await asyncio.sleep(0.2)
    return task


async def scan(args) -> int:
    require_bleak()
    rows = []

    def on_detect(device, advertisement_data):
        rows.append(
            {
                **device_summary(device),
                "rssi": getattr(advertisement_data, "rssi", None),
                "service_uuids": advertisement_data.service_uuids or [],
                "fc11_candidate": looks_like_fc11(device, advertisement_data),
            }
        )

    scanner = BleakScanner(detection_callback=on_detect)
    await scanner.start()
    await asyncio.sleep(args.seconds)
    await scanner.stop()

    seen = {}
    for row in rows:
        seen[row["address_or_identifier"]] = row
    result = sorted(seen.values(), key=lambda row: (not row["fc11_candidate"], row["name"] or ""))
    for row in result:
        if row["fc11_candidate"]:
            class SeenDevice:
                pass

            seen_device = SeenDevice()
            seen_device.name = row["name"]
            seen_device.address = row["address_or_identifier"]
            seen_device.details = None
            save_cached_device(seen_device)
            break
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if any(row["fc11_candidate"] for row in result) else 1


async def smoke(args) -> int:
    device = await discover_device(args.scan_seconds, args.device)
    stats = StreamStats()
    t_stream = None

    def notify_cb(_sender, data):
        try:
            packet_index, samples = parse_cmsn(bytes(data))
        except Exception:
            return
        if samples:
            stats.update(packet_index, len(samples), time.time())

    async with BleakClient(device, timeout=args.timeout) as client:
        print("connected:", bool(client.is_connected), device_summary(device) if not isinstance(device, str) else device)
        write_char, notify_char = await resolve_gatt(client)
        await client.start_notify(NOTIFY_UUID, notify_cb)
        await send_frame(client, write_char, "PAIR", make_pair(CMD_PAIR, 1), args.quiet)
        if args.validate_pair:
            await send_frame(client, write_char, "VALIDATE_PAIR_INFO", make_pair(CMD_VALIDATE_PAIR_INFO, 2), args.quiet)
        await send_frame(client, write_char, "START", make_cmd(CMD_START, 3), args.quiet)
        t_stream = time.time()
        while time.time() - t_stream < args.seconds:
            await asyncio.sleep(0.2)
        try:
            await send_frame(client, write_char, "STOP", make_cmd(CMD_STOP, 4), args.quiet)
        except Exception as exc:
            print("STOP failed:", repr(exc))

    sample_rate = stats.samples / max(args.seconds, 1)
    metrics = {
        "ok": stats.samples > 0 and sample_rate >= args.min_sample_rate and stats.packet_index_gaps == 0,
        "samples": stats.samples,
        "packets": stats.packets,
        "sample_rate_est_hz": sample_rate,
        "packet_rate_est_hz": stats.packets / max(args.seconds, 1),
        "packet_index_first": stats.packet_index_first,
        "packet_index_last": stats.packet_index_last,
        "packet_index_gaps": stats.packet_index_gaps,
        "max_inter_packet_gap_s": stats.max_inter_packet_gap_s,
    }
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0 if metrics["ok"] else 1


async def battery(args) -> int:
    device = await discover_device(args.scan_seconds, args.device)
    async with BleakClient(device, timeout=args.timeout) as client:
        percent = await read_battery_percent(client)
        payload = {
            "ok": percent is not None,
            "battery_percent": percent,
            "device": device_summary(device) if not isinstance(device, str) else device,
            "source": "ble_standard_2a19" if percent is not None else None,
            "message": None if percent is not None else "Servizio batteria BLE standard non esposto dal casco.",
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if percent is not None else 1


async def handshake_dump(args) -> int:
    device = await discover_device(args.scan_seconds, args.device)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.output or (DEFAULT_RUNTIME / f"handshake_dump_{stamp}.jsonl")).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    events = []
    started_at = time.time()

    def append_event(kind: str, **extra) -> None:
        row = {
            "t": round(time.time() - started_at, 6),
            "kind": kind,
            **extra,
        }
        events.append(row)
        with out.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def notify_cb(sender, data):
        raw = bytes(data)
        append_event(
            "notify",
            sender=str(sender),
            **describe_frame(raw),
        )

    print("DIAGNOSTICA HANDSHAKE:", out, flush=True)
    async with BleakClient(device, timeout=args.timeout) as client:
        append_event(
            "connected",
            connected=bool(client.is_connected),
            device=device_summary(device) if not isinstance(device, str) else device,
        )
        write_char, notify_char = await resolve_gatt(client)
        battery_percent = await read_battery_percent(client)
        append_event(
            "gatt_ready",
            write_uuid=getattr(write_char, "uuid", WRITE_UUID),
            notify_uuid=getattr(notify_char, "uuid", NOTIFY_UUID),
            battery_percent=battery_percent,
        )
        await client.start_notify(NOTIFY_UUID, notify_cb)

        msg_id = 1
        if not args.skip_pair:
            pair_frame = make_pair(CMD_PAIR, msg_id)
            append_event("write", label="PAIR", **describe_frame(pair_frame))
            await send_frame(client, write_char, "PAIR", pair_frame, args.quiet)
            await asyncio.sleep(args.after_pair)
            msg_id += 1

        if not args.skip_validate:
            validate_frame = make_pair(CMD_VALIDATE_PAIR_INFO, msg_id)
            append_event("write", label="VALIDATE_PAIR_INFO", **describe_frame(validate_frame))
            await send_frame(client, write_char, "VALIDATE_PAIR_INFO", validate_frame, args.quiet)
            await asyncio.sleep(args.after_validate)
            msg_id += 1

        if args.start:
            start_frame = make_cmd(CMD_START, msg_id)
            append_event("write", label="START", **describe_frame(start_frame))
            await send_frame(client, write_char, "START", start_frame, args.quiet)
            await asyncio.sleep(args.after_start)
            try:
                msg_id += 1
                stop_frame = make_cmd(CMD_STOP, msg_id)
                append_event("write", label="STOP", **describe_frame(stop_frame))
                await send_frame(client, write_char, "STOP", stop_frame, args.quiet)
            except Exception as exc:
                append_event("stop_error", error=repr(exc))

    summary = {
        "ok": True,
        "path": str(out),
        "events": len(events),
        "notifications": sum(1 for event in events if event.get("kind") == "notify"),
        "cmsn_notifications": sum(1 for event in events if event.get("kind") == "notify" and event.get("cmsn")),
        "ascii_fragments": sorted(
            {
                fragment
                for event in events
                for fragment in event.get("ascii", [])
                if len(fragment) >= 4
            }
        )[:80],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


async def record(args) -> int:
    write_status(
        args,
        "scan",
        condition=args.condition,
        duration=args.duration,
        prep=args.prep,
        samples=0,
        packets=0,
    )
    device = await discover_device(args.scan_seconds, args.device)
    write_status(
        args,
        "connecting",
        condition=args.condition,
        duration=args.duration,
        prep=args.prep,
        device=device_summary(device) if not isinstance(device, str) else device,
        samples=0,
        packets=0,
    )
    stats = StreamStats()
    recording = False
    started_at = None
    pipeline: CapturePipeline | None = None
    current_out = None
    current_meta = None
    disconnected = False
    completed_sessions = 0
    battery_percent = None
    current_quality_events: list[dict] = []
    current_imu_rows: list[dict] = []
    current_session_started_at: float | None = None
    last_quality_event_features: dict = {}
    hardware_state = {
        "contact_state": None,
        "lead_off_center": None,
        "lead_off_side": None,
        "signal_quality_warning": None,
        "sleep_idle_time_sec": None,
        "vibration_intensity": None,
        "imu_motion_energy": None,
        "imu_event_count": 0,
        "session_started_at": None,
    }
    last_imu_numbers: dict[str, float] | None = None

    def on_disconnect(_client):
        nonlocal disconnected
        disconnected = True
        print("DISCONNECTED", flush=True)

    def notify_cb(_sender, data):
        nonlocal battery_percent, last_imu_numbers
        try:
            detail = parse_cmsn_detail(bytes(data))
            afe = detail.get("afe") or {}
            packet_index = afe.get("seq_num")
            sample_rate_code = afe.get("sample_rate_code")
            samples = list(afe.get("ch1") or [])
        except Exception:
            return
        now = time.time()
        lead = detail.get("lead_off_status")
        if lead:
            center = lead.get("center_rld")
            side = lead.get("side_channels")
            contact_state = contact_state_from_lead(center, side)
            changed = (
                hardware_state.get("lead_off_center") != lead_state_name(center)
                or hardware_state.get("lead_off_side") != lead_state_name(side)
                or hardware_state.get("contact_state") != contact_state
            )
            hardware_state["lead_off_center"] = lead_state_name(center)
            hardware_state["lead_off_side"] = lead_state_name(side)
            hardware_state["contact_state"] = contact_state
            if changed:
                current_quality_events.append({
                    "ts": now,
                    "event_time_utc": utc_from_ts(now),
                    "t_rel_s": (now - current_session_started_at) if current_session_started_at else None,
                    "event_type": "lead_off_status",
                    "contact_state": contact_state,
                    "lead_off_center": hardware_state["lead_off_center"],
                    "lead_off_side": hardware_state["lead_off_side"],
                    "source": "cmsn_lead_off_status",
                    "raw_value": json.dumps(lead, sort_keys=True),
                })
        sys_info = detail.get("sys_info") or detail.get("sys_resp") or {}
        if sys_info:
            if 3 in sys_info:
                hardware_state["vibration_intensity"] = sys_info.get(3)
            if 4 in sys_info:
                hardware_state["sleep_idle_time_sec"] = sys_info.get(4)
        bstar = detail.get("bstar_data") or {}
        if 3 in bstar:
            try:
                battery_percent = max(0, min(100, int(bstar[3])))
            except Exception:
                pass
        imu = detail.get("imu")
        if imu:
            imu_numbers = flatten_imu_numbers(imu)
            motion = imu_motion_energy(last_imu_numbers, imu_numbers)
            last_imu_numbers = imu_numbers or last_imu_numbers
            hardware_state["imu_event_count"] = int(hardware_state.get("imu_event_count") or 0) + 1
            if motion is not None:
                hardware_state["imu_motion_energy"] = round(float(motion), 3)
            current_imu_rows.append({
                "ts": now,
                "event_time_utc": utc_from_ts(now),
                "t_rel_s": (now - current_session_started_at) if current_session_started_at else None,
                "packet_index": packet_index,
                "motion_energy": hardware_state.get("imu_motion_energy"),
                "imu": imu,
            })
        if samples and pipeline is not None:
            pipeline.feed_packet(packet_index, sample_rate_code, samples)

    async with BleakClient(device, timeout=args.timeout, disconnected_callback=on_disconnect) as client:
        print("connected:", bool(client.is_connected), device_summary(device) if not isinstance(device, str) else device)
        write_char, notify_char = await resolve_gatt(client)
        battery_percent = await read_battery_percent(client)
        current_out, current_meta = next_session_paths(args)
        write_status(
            args,
            "ble_link",
            condition=args.condition,
            duration=args.duration,
            prep=args.prep,
            csv=str(current_out),
            battery_percent=battery_percent,
            samples=0,
            packets=0,
            message="Canale BLE aperto. Attendo pairing applicativo del casco.",
        )
        try:
            await asyncio.wait_for(client.start_notify(NOTIFY_UUID, notify_cb), timeout=BLE_NOTIFY_TIMEOUT_S)
            msg_id = 1
            if not args.skip_pair:
                await send_frame(client, write_char, "PAIR", make_pair(CMD_PAIR, msg_id), args.quiet)
                msg_id += 1
            await send_frame(client, write_char, "VALIDATE_PAIR_INFO", make_pair(CMD_VALIDATE_PAIR_INFO, msg_id), args.quiet)
            args.start_msg_id = msg_id + 1
            if getattr(args, "sleep_idle_seconds", 0):
                try:
                    await send_frame(client, write_char, "SET_SLEEP_IDLE_TIME", make_sleep_idle(args.sleep_idle_seconds, args.start_msg_id), args.quiet)
                    hardware_state["sleep_idle_time_sec"] = args.sleep_idle_seconds
                    args.start_msg_id += 1
                except Exception as exc:
                    print("SET_SLEEP_IDLE_TIME failed:", repr(exc), flush=True)
            try:
                await send_frame_unconfirmed(client, write_char, "GET_SYSTEM_INFO", make_cmd(CMD_GET_SYSTEM_INFO, args.start_msg_id), args.quiet)
                args.start_msg_id += 1
            except Exception as exc:
                print("GET_SYSTEM_INFO failed:", repr(exc), flush=True)
            if getattr(args, "lead_off_check", True):
                try:
                    await send_frame_unconfirmed(client, write_char, "GET_LEAD_OFF_STATUS", make_cmd(CMD_GET_LEAD_OFF_STATUS, args.start_msg_id), args.quiet)
                    args.start_msg_id += 1
                except Exception as exc:
                    print("GET_LEAD_OFF_STATUS failed:", repr(exc), flush=True)
            if getattr(args, "enable_imu", False):
                try:
                    await send_frame_unconfirmed(client, write_char, "IMU_CONFIG", make_imu_config(args.start_msg_id), args.quiet)
                    args.start_msg_id += 1
                except Exception as exc:
                    print("IMU_CONFIG failed:", repr(exc), flush=True)
        except Exception as exc:
            message = f"Handshake casco non riuscito: {exc!r}"
            print(message, flush=True)
            write_status(
                args,
                "error",
                condition=args.condition,
                duration=args.duration,
                prep=args.prep,
                csv=str(current_out),
                battery_percent=battery_percent,
                samples=0,
                packets=0,
                **hardware_state,
                error=message,
            )
            return 1

        write_status(
            args,
            "handshake_sent",
            condition=args.condition,
            duration=args.duration,
            prep=args.prep,
            csv=str(current_out),
            battery_percent=battery_percent,
            samples=0,
            packets=0,
            **hardware_state,
            message=(
                "Validazione inviata. Quando arriva lo stream EEG la connessione e confermata."
                if args.skip_pair
                else "PAIR/VALIDATE inviati. Attendo conferma dal casco."
            ),
        )

        while True:
            if disconnected or not client.is_connected:
                raise RuntimeError("Casco disconnesso.")

            current_out, current_meta = next_session_paths(args)
            current_quality_events = []
            current_imu_rows = []
            current_session_started_at = None
            live_features = {}
            last_imu_numbers = None
            hardware_state["imu_motion_energy"] = None
            hardware_state["imu_event_count"] = 0
            hardware_state["session_started_at"] = None

            async def refresh_idle_status():
                if disconnected or not client.is_connected:
                    raise RuntimeError("canale BLE non connesso")
                refreshed_battery = await read_battery_percent(client)
                if getattr(args, "lead_off_check", True):
                    try:
                        msg_id = int(getattr(args, "start_msg_id", 5) or 5)
                        await send_frame_unconfirmed(client, write_char, "GET_LEAD_OFF_STATUS", make_cmd(CMD_GET_LEAD_OFF_STATUS, msg_id), True)
                        args.start_msg_id = msg_id + 1
                    except Exception:
                        pass
                return {"battery_percent": refreshed_battery, "ble_idle_check_at": time.time(), **hardware_state, "live_features": live_features}

            try:
                battery_percent = await wait_for_start_signal(
                    args,
                    current_out,
                    battery_percent,
                    lambda: bool(client.is_connected) and not disconnected,
                    refresh_idle_status,
                    client,
                    write_char,
                )
            except Exception as exc:
                message = f"Attesa Start interrotta: {exc!r}"
                print(message, flush=True)
                write_status(
                    args,
                    "error",
                    condition=args.condition,
                    duration=args.duration,
                    prep=args.prep,
                    csv=str(current_out),
                    battery_percent=None,
                    samples=0,
                    packets=stats.packets,
                    **hardware_state,
                    live_features=live_features,
                    error=message,
                )
                await apply_helmet_led(client, write_char, args, "error", None)
                return 0 if completed_sessions else 1

            # The console may change condition/duration while the BLE process is
            # kept connected.  Build the immutable session filename only after
            # consuming that start payload, otherwise data can be scientifically
            # mislabelled with the condition used when the daemon first armed.
            current_out, current_meta = next_session_paths(args)

            stats = StreamStats()
            recording = False
            last_contact_state = None
            if pipeline is not None:
                pipeline.set_recording(False)
            started_at = None
            session_cancelled = False
            lsl_bridge = None
            env_lsl = (os.environ.get("MINDTUNE_ENABLE_LSL") or "").strip().lower()
            lsl_enabled = getattr(args, "lsl", False) or env_lsl in ("1", "true", "yes", "on")
            if lsl_enabled:
                lsl_bridge = LSLBridge(
                    enabled=True,
                    source_id="mindtune_fc11",
                    session_id=current_out.stem,
                    algorithm_version=SCIENTIFIC_QC_VERSION,
                )
            pipeline = CapturePipeline(
                current_out=current_out,
                stats=stats,
                hardware_state=hardware_state,
                feature_callback=compute_live_feature_snapshot,
                live_features_enabled=not args.no_live_features,
                raw_queue_maxsize=200,
                feature_queue_maxsize=10,
                nominal_rate=250.0,
                lsl_bridge=lsl_bridge,
            )
            await pipeline.start()
            marker_time = time.time()
            pipeline.feed_marker(marker_time, f"condition:{args.condition}")
            pipeline.feed_marker(marker_time, "start")
            pipeline.feed_marker(marker_time, "block:1")
            pipeline.feed_marker(marker_time, "trial:1")

            print("=" * 80)
            print("SESSIONE:", args.condition)
            print("DURATA:", args.duration, "secondi")
            print("PREPARAZIONE:", args.prep, "secondi")
            print("FILE:", current_out)
            print("=" * 80)

            try:
                try:
                    write_char, notify_char = await resolve_gatt(client)
                    packets_before_start = stats.packets
                    start_write_task = None
                    start_msg_id = int(getattr(args, "start_msg_id", 3) or 3)
                    args.start_msg_id = start_msg_id + 2
                    if getattr(args, "start_signal_file", None):
                        start_write_task = await send_frame_unconfirmed(client, write_char, "START", make_cmd(CMD_START, start_msg_id), args.quiet)
                    else:
                        await send_frame(client, write_char, "START", make_cmd(CMD_START, start_msg_id), args.quiet)
                    write_status(
                        args,
                        "starting",
                        condition=args.condition,
                        duration=args.duration,
                        prep=args.prep,
                        csv=str(current_out),
                        battery_percent=battery_percent,
                        samples=stats.samples,
                        packets=stats.packets,
                        **hardware_state,
                        live_features=live_features,
                    )
                    await apply_helmet_led(client, write_char, args, "starting", battery_percent)
                    stream_deadline = time.time() + 4.0
                    while time.time() < stream_deadline and stats.packets <= packets_before_start:
                        await asyncio.sleep(0.1)
                    if stats.packets <= packets_before_start:
                        if start_write_task:
                            start_write_task.cancel()
                        raise RuntimeError("START inviato, ma non arrivano pacchetti EEG dal casco.")
                except Exception as exc:
                    message = f"Avvio streaming non riuscito: {exc!r}"
                    print(message, flush=True)
                    write_status(
                        args,
                        "error",
                        condition=args.condition,
                        duration=args.duration,
                        prep=args.prep,
                        csv=str(current_out),
                        battery_percent=battery_percent,
                        samples=stats.samples,
                        packets=stats.packets,
                        **hardware_state,
                        live_features=live_features,
                        error=message,
                    )
                    await apply_helmet_led(client, write_char, args, "error", battery_percent)
                    return 0 if completed_sessions else 1

                if args.prep:
                    print("Preparazione: il casco streamma, ma il CSV non registra ancora.")
                    write_status(
                        args,
                        "prep",
                        condition=args.condition,
                        duration=args.duration,
                        prep=args.prep,
                        csv=str(current_out),
                        battery_percent=battery_percent,
                        samples=0,
                        packets=0,
                    )
                    await apply_helmet_led(client, write_char, args, "prep", battery_percent)
                    for remaining in range(args.prep, 0, -1):
                        if disconnected or not client.is_connected:
                            raise RuntimeError("Casco disconnesso durante la preparazione.")
                        if consume_stop_signal(args):
                            print("\nStop ricevuto durante la preparazione.", flush=True)
                            session_cancelled = True
                            break
                        write_status(
                            args,
                            "prep",
                            condition=args.condition,
                            duration=args.duration,
                            prep=args.prep,
                            csv=str(current_out),
                            battery_percent=battery_percent,
                            samples=stats.samples,
                            packets=stats.packets,
                        )
                        print(f"inizio registrazione tra {remaining}s", end="\r", flush=True)
                        await asyncio.sleep(1)
                    print()

                if not session_cancelled:
                    print("REGISTRAZIONE ATTIVA")
                    recording = True
                    if pipeline is not None:
                        pipeline.set_recording(True)
                        pipeline.feed_marker(time.time(), "recording_active")
                    started_at = time.time()
                    current_session_started_at = started_at
                    hardware_state["session_started_at"] = started_at
                    write_status(
                        args,
                        "recording",
                        condition=args.condition,
                        duration=args.duration,
                        prep=args.prep,
                        csv=str(current_out),
                        battery_percent=battery_percent,
                        samples=0,
                        packets=0,
                        **hardware_state,
                        live_features=live_features,
                    )
                    await apply_helmet_led(client, write_char, args, "recording", battery_percent)
                    play_ding()
                    while time.time() - started_at < args.duration:
                        if disconnected or not client.is_connected:
                            raise RuntimeError("Casco disconnesso durante la registrazione.")
                        if consume_stop_signal(args):
                            print("\nStop ricevuto: chiudo questa sessione e tengo il casco collegato.", flush=True)
                            session_cancelled = True
                            break
                        try:
                            args.start_msg_id = await consume_command_signal(
                                args, client, write_char, int(getattr(args, "start_msg_id", 5) or 5), quiet=args.quiet
                            )
                        except Exception as exc:
                            print(f"command check error: {exc!r}", flush=True)
                        elapsed = int(time.time() - started_at)
                        remaining = args.duration - elapsed
                        current_contact = hardware_state.get("contact_state")
                        if current_contact != last_contact_state:
                            last_contact_state = current_contact
                            if pipeline is not None and current_contact is not None:
                                pipeline.feed_marker(time.time(), f"contact:{current_contact}")
                        print(f"samples={stats.samples} packets={stats.packets} remaining={remaining}s", end="\r", flush=True)
                        if elapsed % 5 == 0:
                            write_status(
                                args,
                                "recording",
                                condition=args.condition,
                                duration=args.duration,
                                prep=args.prep,
                                csv=str(current_out),
                                battery_percent=battery_percent,
                                samples=stats.samples,
                                packets=stats.packets,
                                **hardware_state,
                                live_features=live_features,
                            )
                        await asyncio.sleep(1)

            finally:
                if pipeline is not None:
                    pipeline.feed_marker(time.time(), "stop")
                pipeline_extras = None
                if pipeline is not None:
                    try:
                        pipeline_extras = await pipeline.stop()
                    except Exception as exc:
                        print(f"pipeline stop error: {exc!r}", flush=True)
                    if pipeline_extras is not None:
                        live_features = pipeline_extras.last_live_features
                        current_quality_events.extend(pipeline_extras.quality_events)
                recording = False

            elapsed = max((time.time() - started_at) if started_at else args.duration, 0.001)
            contact_events = [event for event in current_quality_events if event.get("contact_state")]
            contact_ok_pct = None
            if contact_events:
                contact_ok_pct = 100.0 * sum(1 for event in contact_events if event.get("contact_state") == "ok") / len(contact_events)
            recorded_samples = pipeline_extras.recorded_samples if pipeline_extras else stats.samples
            recorded_packets = pipeline_extras.recorded_packets if pipeline_extras else stats.packets
            recording_duration_s = (
                pipeline_extras.recording_duration_s if pipeline_extras and pipeline_extras.recording_duration_s else elapsed
            )
            metadata = {
                "condition": args.condition,
                "duration_requested_s": args.duration,
                "prep_s": args.prep,
                "samples": recorded_samples,
                "packets": recorded_packets,
                "sample_rate_est_hz": recorded_samples / max(recording_duration_s, 0.001),
                "recording_duration_s": recording_duration_s,
                "packet_index_first": stats.packet_index_first,
                "packet_index_last": stats.packet_index_last,
                "packet_index_gaps": stats.packet_index_gaps,
                "max_inter_packet_gap_s": stats.max_inter_packet_gap_s,
                "csv": str(current_out),
                "battery_percent": battery_percent,
                "interrupted": session_cancelled,
                "hardware_state": dict(hardware_state),
                "last_live_features": live_features,
                "quality_events": current_quality_events,
                "imu_rows": current_imu_rows,
                "contact_ok_pct": contact_ok_pct,
                "sleep_idle_seconds_requested": getattr(args, "sleep_idle_seconds", None),
                "lead_off_check_enabled": bool(getattr(args, "lead_off_check", True)),
                "imu_enabled": bool(getattr(args, "enable_imu", False)),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "sample_rate_codes": pipeline_extras.sample_rate_codes if pipeline_extras else None,
                "pipeline_extras": pipeline_extras.__dict__ if pipeline_extras else None,
            }
            study_context = getattr(args, "study_context", None)
            if isinstance(study_context, dict) and study_context:
                metadata["study_context"] = study_context
            try:
                session_v2_dir = create_mindtune_v2_package(args, current_out, metadata)
                print("mindtune_session_v2:", session_v2_dir)
            except Exception as exc:
                metadata["mindtune_session_v2_error"] = repr(exc)
                print("MindTune session v2 package failed:", repr(exc), flush=True)
            current_meta.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            write_status(args, "done", **metadata)
            await apply_helmet_led(client, write_char, args, "done", battery_percent)
            play_ding()
            print("\nRegistrazione conclusa.")
            try:
                await send_frame(client, write_char, "STOP", make_cmd(CMD_STOP, int(getattr(args, "start_msg_id", 5) or 5)), args.quiet)
                args.start_msg_id = int(getattr(args, "start_msg_id", 5) or 5) + 1
            except Exception as exc:
                print("STOP failed:", repr(exc))
            completed_sessions += 1
            print("saved:", current_out)
            print("meta:", current_meta)
            print(json.dumps(metadata, indent=2))

            if not getattr(args, "start_signal_file", None):
                return 0 if stats.samples > 0 else 1

            write_status(
                args,
                "connected",
                condition=args.condition,
                duration=args.duration,
                prep=args.prep,
                csv=str(current_out),
                battery_percent=battery_percent,
                waiting_for_start=True,
                samples=0,
                packets=0,
                **hardware_state,
                live_features=live_features,
                last_session=str(current_out),
                message="Sessione conclusa. Casco ancora collegato, pronto per un nuovo Start.",
            )
            await apply_helmet_led(client, write_char, args, "connected", battery_percent)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MindTune Lab FC11 local Mac BLE capture.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Cerca dispositivi BLE FC11 visibili dal Mac.")
    scan_p.add_argument("--seconds", type=float, default=10.0)

    smoke_p = sub.add_parser("smoke", help="Connette, avvia brevemente lo stream e conta campioni.")
    smoke_p.add_argument("--device", default=None, help="Identificatore BLE macOS opzionale se gia noto.")
    smoke_p.add_argument("--scan-seconds", type=float, default=10.0)
    smoke_p.add_argument("--seconds", type=int, default=12)
    smoke_p.add_argument("--timeout", type=float, default=15.0)
    smoke_p.add_argument("--min-sample-rate", type=float, default=180.0)
    smoke_p.add_argument("--validate-pair", action="store_true")
    smoke_p.add_argument("--quiet", action="store_true")

    battery_p = sub.add_parser("battery", help="Legge la batteria BLE standard del casco, se esposta.")
    battery_p.add_argument("--device", default=None, help="Identificatore BLE macOS opzionale se gia noto.")
    battery_p.add_argument("--scan-seconds", type=float, default=10.0)
    battery_p.add_argument("--timeout", type=float, default=15.0)

    dump_p = sub.add_parser("handshake-dump", help="Salva i pacchetti grezzi della stretta di mano PAIR/VALIDATE.")
    dump_p.add_argument("--device", default=None, help="Identificatore BLE macOS opzionale se gia noto.")
    dump_p.add_argument("--scan-seconds", type=float, default=10.0)
    dump_p.add_argument("--timeout", type=float, default=15.0)
    dump_p.add_argument("--after-pair", type=float, default=1.0)
    dump_p.add_argument("--after-validate", type=float, default=2.0)
    dump_p.add_argument("--skip-pair", action="store_true")
    dump_p.add_argument("--skip-validate", action="store_true")
    dump_p.add_argument("--start", action="store_true", help="Invia anche START/STOP dopo la validazione.")
    dump_p.add_argument("--after-start", type=float, default=2.0)
    dump_p.add_argument("--output", default=None)
    dump_p.add_argument("--quiet", action="store_true")

    record_p = sub.add_parser("record", help="Registra CSV raw_s24 compatibile BrainLab.")
    record_p.add_argument("--condition", required=True)
    record_p.add_argument("--duration", type=int, required=True)
    record_p.add_argument("--prep", type=int, default=30)
    record_p.add_argument("--device", default=None, help="Identificatore BLE macOS opzionale se gia noto.")
    record_p.add_argument("--scan-seconds", type=float, default=10.0)
    record_p.add_argument("--timeout", type=float, default=15.0)
    record_p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    record_p.add_argument("--status-file", default=None)
    record_p.add_argument("--start-signal-file", default=None)
    record_p.add_argument("--stop-signal-file", default=None)
    record_p.add_argument("--command-signal-file", default=None, help="JSON file con comandi hardware: led_color/vibration.")
    record_p.add_argument("--validate-pair", action="store_true")
    record_p.add_argument("--skip-pair", action="store_true")
    record_p.add_argument("--sleep-idle-seconds", type=int, default=1800, help="Imposta idle/sleep proprietario del casco durante la sessione; 0 disabilita.")
    record_p.add_argument("--no-lead-off-check", dest="lead_off_check", action="store_false", help="Disabilita richieste diagnostiche GET_LEAD_OFF_STATUS.")
    record_p.add_argument("--enable-imu", action="store_true", help="Abilita configurazione IMU sperimentale a bassa frequenza.")
    record_p.add_argument("--no-live-features", action="store_true", help="Disabilita compute_live_feature_snapshot nel callback per test A/B.")
    record_p.add_argument("--lsl", action="store_true", help="Abilita gli stream LSL EEG e marker.")
    record_p.set_defaults(lead_off_check=True, no_live_features=False, lsl=False)
    record_p.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            return asyncio.run(scan(args))
        if args.command == "smoke":
            return asyncio.run(smoke(args))
        if args.command == "battery":
            return asyncio.run(battery(args))
        if args.command == "handshake-dump":
            return asyncio.run(handshake_dump(args))
        if args.command == "record":
            return asyncio.run(record(args))
    except KeyboardInterrupt:
        if getattr(args, "command", None) == "record":
            write_status(
                args,
                "interrupted",
                condition=getattr(args, "condition", None),
                error="interrotto dall'utente",
            )
        print("Interrotto dall'utente.", flush=True)
        return 130
    except Exception as exc:
        permission_message = bluetooth_permission_message(exc)
        if permission_message:
            print(permission_message, flush=True)
            if getattr(args, "command", None) == "record":
                write_status(
                    args,
                    "error",
                    condition=getattr(args, "condition", None),
                    error=permission_message,
                )
            return 64
        if getattr(args, "command", None) == "record":
            write_status(args, "error", condition=getattr(args, "condition", None), error=str(exc))
        print(f"Errore: {exc}", flush=True)
        return 1
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
