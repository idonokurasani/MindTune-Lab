"""Live windowing reusing the deterministic CLM-02B window policy."""

from __future__ import annotations

from dataclasses import dataclass

from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow
from mindtune_clm.replay.quality import QualityPolicy
from mindtune_clm.replay.windows import WindowPolicy, make_windows


@dataclass
class LiveWindowingPolicy:
    """Thin wrapper around the existing deterministic window maker."""

    window_policy: WindowPolicy

    def make_windows(
        self,
        session_id: str,
        samples: list[NormalizedSensorSample],
        assessments: list[QualityAssessment],
        quality_policy: QualityPolicy,
    ) -> list[ReplayWindow]:
        """Create half-open [start, end) replay windows for the live stream."""
        return make_windows(
            replay_id=session_id,
            samples=samples,
            sample_assessments=assessments,
            window_policy=self.window_policy,
            quality_policy=quality_policy,
        )
