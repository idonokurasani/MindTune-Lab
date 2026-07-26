"""Live sensor quality assessment reusing CLM-02B FC11 quality."""

from __future__ import annotations

from dataclasses import dataclass

from mindtune_clm.replay.fc11.quality import FC11QualityPolicy
from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment


@dataclass(frozen=True)
class LiveQualityPolicy(FC11QualityPolicy):
    """FC11 quality policy adapted for the live packet stream.

    Reuses the exact sample and window assessment logic from
    ``mindtune_clm.replay.fc11.quality.FC11QualityPolicy``.
    """

    policy_id: str = "mindtune_clm.live.fc11.quality.v1"
    version: str = "1.0.0"

    def assess_samples(
        self,
        samples: list[NormalizedSensorSample],
    ) -> list[QualityAssessment]:
        """Assess a sequence of normalized samples in deterministic order."""
        assessments: list[QualityAssessment] = []
        previous: NormalizedSensorSample | None = None
        for sample in samples:
            assessment = self.assess(sample, previous)
            assessments.append(assessment)
            previous = sample
        return assessments
