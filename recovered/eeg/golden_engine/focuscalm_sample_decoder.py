"""FocusCalm BLE EEG sample decoder.

Reconstructs the conversion performed by the native `parse_content`
function in libfusi.so (ARM64, address 0x16574).

Packet format
-------------
The BLE payload is a sequence of TLV chunks followed by a 4-byte footer:

    [type: 2 bytes BE][length: 2 bytes BE][length bytes of payload]
    ...
    footer = b"PKED"   (0x50 0x4b 0x45 0x44)

`parse_content` verifies the last 4 bytes are exactly "PKED" and then
loops over the remaining bytes as chunks.  The only chunk required for
EEG is type 0x4547 (big-endian "EG").

EEG sample encoding
-------------------
Each EEG chunk payload is a sequence of 3-byte, big-endian, signed
24-bit integers.  `parse_content` reconstructs the 32-bit signed value
as:

    raw24 = (b0 << 16) | (b1 << 8) | b2
    if raw24 & 0x800000:
        raw24 |= 0xff000000

and then converts to the double stored in `this+0x70`:

    sample = raw24 * 0.040690104166666664 / 128.0

The two constants are the floating-point literals stored at the
`.rodata` addresses 0x75b30 and used as `this+0x10` in the disassembly.
"""

from __future__ import annotations

import struct
from collections import deque


# Verified from libfusi.so .rodata (little-endian double at file 0x75b30).
EEG_SCALE_NUMERATOR = 0.040690104166666664
# this+0x10 is initialised to 128 in device_data_create.
EEG_SCALE_DIVISOR = 128.0

EEG_PACKET_FOOTER = b"PKED"
EEG_CHUNK_TYPE = 0x4547  # big-endian "EG"


def scale_raw_s24(raw24: int) -> float:
    """Convert a signed 24-bit EEG integer to the native double value."""
    return raw24 * EEG_SCALE_NUMERATOR / EEG_SCALE_DIVISOR


def signed_be24_to_int(b: bytes) -> int:
    """Convert 3 big-endian bytes into a sign-extended 32-bit integer."""
    if len(b) != 3:
        raise ValueError("signed_be24_to_int expects exactly 3 bytes")
    value = (b[0] << 16) | (b[1] << 8) | b[2]
    if value & 0x800000:
        value |= 0xFF000000
    # reinterpret as signed 32-bit
    return int.from_bytes(struct.pack(">I", value & 0xFFFFFFFF), "big", signed=True)


def decode_eeg_chunk(payload: bytes) -> list[float]:
    """Decode all 24-bit signed big-endian samples in a chunk payload.

    `parse_content` only processes `floor(len(payload) / 3)` complete
    samples (the division by 3 truncates), so leftover bytes are ignored.
    """
    samples: list[float] = []
    for i in range(0, len(payload) - 2, 3):
        raw = signed_be24_to_int(payload[i : i + 3])
        samples.append(scale_raw_s24(raw))
    return samples


def parse_ble_payload(payload: bytes, strict_footer: bool = True) -> tuple[list[float], list[tuple[int, bytes]]]:
    """Parse a FocusCalm BLE payload and return EEG samples + other chunks.

    Parameters
    ----------
    payload
        Raw BLE bytes (without any framing such as MTU headers).
    strict_footer
        If True, require the last 4 bytes to be ``b'PKED'``.

    Returns
    -------
    eeg_samples
        All EEG samples found in chunks of type 0x4547, in order.
    other_chunks
        List of (type, payload) for every non-EEG chunk encountered.
    """
    if strict_footer:
        if len(payload) < 4 or payload[-4:] != EEG_PACKET_FOOTER:
            raise ValueError("payload does not end with 'PKED' footer")
        data = payload[:-4]
    else:
        data = payload

    eeg_samples: list[float] = []
    other_chunks: list[tuple[int, bytes]] = []

    i = 0
    while i + 4 <= len(data):
        chunk_type = struct.unpack(">H", data[i : i + 2])[0]
        chunk_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
        i += 4

        if i + chunk_len > len(data):
            break

        chunk_payload = data[i : i + chunk_len]
        i += chunk_len

        if chunk_type == EEG_CHUNK_TYPE:
            eeg_samples.extend(decode_eeg_chunk(chunk_payload))
        else:
            other_chunks.append((chunk_type, chunk_payload))

    return eeg_samples, other_chunks


class EEGWindow:
    """Maintain the 800-sample EEG window used by the native pipeline.

    The native code keeps an 800-sample circular buffer (`this+0x80`) and
    updates it every time an EEG packet is parsed.  This Python class
    provides the same sliding-window behaviour: append newly decoded
    samples and expose the latest 800 samples as a contiguous numpy-ready
    list/array.
    """

    WINDOW_SIZE = 800

    def __init__(self, size: int = WINDOW_SIZE) -> None:
        self.size = size
        self._buf: deque[float] = deque(maxlen=size)

    def extend(self, samples: list[float]) -> None:
        """Append samples to the window, dropping the oldest."""
        self._buf.extend(samples)

    def full(self) -> bool:
        return len(self._buf) >= self.size

    def to_array(self) -> list[float]:
        """Return the current window contents in chronological order."""
        return list(self._buf)

    def __len__(self) -> int:
        return len(self._buf)


def demo() -> None:
    import numpy as np
    from reconstruct_meditation_features import meditation_features

    # Synthetic example: one EEG chunk with 20 samples whose 24-bit values
    # are around 248300 (similar to the real CSV column).
    base = 248300
    payload = struct.pack(">HH", EEG_CHUNK_TYPE, 60)  # 20 samples * 3 bytes
    for k in range(20):
        raw = base + (k % 7) - 3
        payload += struct.pack(">i", raw & 0xFFFFFF)[1:]  # 3 BE bytes
    payload += EEG_PACKET_FOOTER

    eeg, _ = parse_ble_payload(payload)
    print("decoded samples:", len(eeg))
    print("first 5:", eeg[:5])

    # A real window would accumulate many packets; here we just show scaling.
    win = EEGWindow()
    win.extend(eeg)
    print("window samples:", len(win.to_array()))

    # If the window were full you could feed it to the network pipeline:
    # features = meditation_features(np.array(win.to_array(), dtype=np.float64))


if __name__ == "__main__":
    demo()
