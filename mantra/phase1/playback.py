"""Playback foundation with segment-aware events and Phase 2 extension hooks."""

from __future__ import annotations

import platform
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from .events import EventEmitter, MantraEventType
from .timeline import TimelineSegment


@runtime_checkable
class AudioPlayer(Protocol):
    """Pluggable audio player used by PlaybackController."""

    def play_file(self, wav_path: Path) -> None:
        """Start playing a WAV file. Must be non-blocking."""
        ...

    def stop(self) -> None:
        """Stop the currently playing file."""
        ...

    def is_playing(self) -> bool:
        """Return True if audio is still playing."""
        ...


class SubprocessAudioPlayer:
    """Audio player that invokes the host's native WAV player.

    Uses `afplay` on macOS and `aplay` on Linux. Playback is per-segment,
    so pause/resume/stop operate at segment boundaries.
    """

    def __init__(self) -> None:
        self._process: subprocess.Popen[Any] | None = None
        self._command = self._detect_command()

    def _detect_command(self) -> str:
        system = platform.system()
        if system == "Darwin":
            return "afplay"
        return "aplay"

    def play_file(self, wav_path: Path) -> None:
        self.stop()
        try:
            self._process = subprocess.Popen(
                [self._command, str(wav_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Host audio player {self._command!r} not found; install it or use NullAudioPlayer"
            ) from exc

    def stop(self) -> None:
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=1)
            except Exception:
                pass
            finally:
                self._process = None

    def is_playing(self) -> bool:
        return self._process is not None and self._process.poll() is None


class NullAudioPlayer:
    """Fake audio player for tests and headless environments.

    Does not emit sound; records which files were requested and returns
    immediately so playback events can be tested deterministically.
    """

    def __init__(self) -> None:
        self.played_files: list[Path] = []
        self._playing = False

    def play_file(self, wav_path: Path) -> None:
        self.played_files.append(wav_path)
        self._playing = True

    def stop(self) -> None:
        self._playing = False

    def is_playing(self) -> bool:
        return self._playing


@dataclass
class PlaybackState:
    """Current deterministic playback state."""

    current_segment_index: int = 0
    elapsed_time: float = 0.0
    paused: bool = False
    stopped: bool = False
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_segment_index": self.current_segment_index,
            "elapsed_time": self.elapsed_time,
            "paused": self.paused,
            "stopped": self.stopped,
            "completed": self.completed,
        }


class PlaybackController:
    """Play a built mantra timeline and emit segment-aware events.

    The controller traverses the compiled timeline. Each segment has a
    pre-computed actual duration and an associated per-segment WAV file.
    It emits `mantra_segment_started` and `mantra_segment_completed` events
    so Phase 2 can correlate EEG windows with the segment playing at that
    moment. Pause, resume, stop, and completion are supported.
    """

    def __init__(
        self,
        timeline: list[TimelineSegment],
        segments_dir: Path,
        audio_player: AudioPlayer | None = None,
        events: EventEmitter | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ):
        self.timeline = timeline
        self.segments_dir = Path(segments_dir)
        self.player = audio_player or SubprocessAudioPlayer()
        self.events = events or EventEmitter()
        self._sleep = sleep_fn or time.sleep
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self.state = PlaybackState()

    def start(self) -> None:
        """Start playback in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._pause_event.clear()
        self.state = PlaybackState()
        self._thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._thread.start()
        self.events.emit(
            MantraEventType.PLAYBACK_STARTED,
            {"total_segments": len(self.timeline), "total_duration": self._total_duration()},
        )

    def _total_duration(self) -> float:
        return sum(s.actual_duration or s.planned_duration for s in self.timeline)

    def _playback_loop(self) -> None:  # noqa: C901
        try:
            for index, segment in enumerate(self.timeline):
                if self._stop_event.is_set():
                    break

                # Wait while paused before the next segment.
                while self._pause_event.is_set() and not self._stop_event.is_set():
                    self._sleep(0.05)

                if self._stop_event.is_set():
                    break

                self.state.current_segment_index = index
                self.events.emit(
                    MantraEventType.SEGMENT_STARTED,
                    {
                        "segment_id": segment.segment_id,
                        "segment_type": segment.segment_type.value,
                        "index": index,
                        "elapsed_time": self.state.elapsed_time,
                    },
                )

                seg_path = self.segments_dir / f"{index:04d}_{segment.segment_id}.wav"
                if seg_path.exists():
                    self.player.play_file(seg_path)
                else:
                    # Headless / test fallback: just sleep for the duration.
                    pass

                duration = segment.actual_duration or segment.planned_duration
                start = time.monotonic()
                paused_total = 0.0
                while time.monotonic() - start - paused_total < duration:
                    if self._stop_event.is_set():
                        self.player.stop()
                        return
                    if self._pause_event.is_set():
                        pause_start = time.monotonic()
                        while self._pause_event.is_set() and not self._stop_event.is_set():
                            self._sleep(0.05)
                        paused_total += time.monotonic() - pause_start
                        continue
                    remaining = duration - (time.monotonic() - start - paused_total)
                    if remaining <= 0:
                        break
                    self._sleep(min(0.05, remaining))

                self.player.stop()
                self.state.elapsed_time += duration
                self.events.emit(
                    MantraEventType.SEGMENT_COMPLETED,
                    {
                        "segment_id": segment.segment_id,
                        "segment_type": segment.segment_type.value,
                        "index": index,
                        "elapsed_time": self.state.elapsed_time,
                    },
                )

            if not self._stop_event.is_set():
                self.state.completed = True
                self.events.emit(
                    MantraEventType.PLAYBACK_COMPLETED,
                    {"total_duration": self.state.elapsed_time},
                )
        finally:
            self.player.stop()

    def pause(self) -> None:
        """Pause playback at the next segment boundary."""
        if self.state.completed or self.state.stopped:
            return
        self.state.paused = True
        self._pause_event.set()
        self.events.emit(MantraEventType.PLAYBACK_PAUSED, self.state.to_dict())

    def resume(self) -> None:
        """Resume a paused playback."""
        if self.state.completed or self.state.stopped:
            return
        self.state.paused = False
        self._pause_event.clear()
        self.events.emit(MantraEventType.PLAYBACK_RESUMED, self.state.to_dict())

    def stop(self) -> None:
        """Stop playback and release audio resources."""
        self.state.stopped = True
        self._stop_event.set()
        self._pause_event.clear()
        self.player.stop()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self.events.emit(MantraEventType.PLAYBACK_STOPPED, self.state.to_dict())

    def wait_until_complete(self, timeout: float | None = None) -> bool:
        """Block until playback completes or is stopped."""
        if self._thread is None:
            return False
        self._thread.join(timeout=timeout)
        return not self._thread.is_alive()

    def current_segment(self) -> TimelineSegment | None:
        """Return the segment currently playing."""
        if not self.timeline or self.state.current_segment_index >= len(self.timeline):
            return None
        return self.timeline[self.state.current_segment_index]
