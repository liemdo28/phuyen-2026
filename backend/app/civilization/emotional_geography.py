from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EmotionalZone:
    name: str
    calm_score: float = 0.5
    stimulation_score: float = 0.5
    recovery_score: float = 0.5
    notes: list[str] = field(default_factory=list)


class EmotionalGeographyEngine:
    def classify(
        self,
        *,
        crowd_density: float,
        noise_level: float,
        shade_score: float,
        scenic_quality: float,
    ) -> EmotionalZone:
        calm = min(1.0, max(0.0, 0.65 - crowd_density * 0.25 - noise_level * 0.2 + shade_score * 0.2 + scenic_quality * 0.2))
        stimulation = min(1.0, max(0.0, crowd_density * 0.4 + noise_level * 0.35 + scenic_quality * 0.1))
        recovery = min(1.0, max(0.0, calm * 0.55 + shade_score * 0.2 + scenic_quality * 0.15 - noise_level * 0.1))
        zone = EmotionalZone(
            name="balanced_zone",
            calm_score=calm,
            stimulation_score=stimulation,
            recovery_score=recovery,
        )
        if recovery >= 0.6:
            zone.name = "recovery_zone"
            zone.notes.append("Emotionally restorative environment.")
        elif stimulation >= 0.65 and calm <= 0.35:
            zone.name = "overstimulating_zone"
            zone.notes.append("Likely to amplify fatigue or stress if energy is already low.")
        elif calm >= 0.55:
            zone.name = "calming_zone"
            zone.notes.append("Suitable for decompression, slower pacing, or recovery stops.")
        return zone
