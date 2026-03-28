from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FeatureVector:
    rms: float
    dominant_frequency: float
    duration: float
    zero_crossing_rate: float

    def to_dict(self) -> dict[str, float]:
        return {
            "rms": self.rms,
            "dominant_frequency": self.dominant_frequency,
            "duration": self.duration,
            "zero_crossing_rate": self.zero_crossing_rate,
        }

    def as_array(self) -> np.ndarray:
        return np.array(
            [
                self.rms,
                self.dominant_frequency,
                self.duration,
                self.zero_crossing_rate,
            ],
            dtype=np.float32,
        )

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "FeatureVector":
        return cls(
            rms=float(data["rms"]),
            dominant_frequency=float(data["dominant_frequency"]),
            duration=float(data["duration"]),
            zero_crossing_rate=float(data["zero_crossing_rate"]),
        )


def extract_features(samples: np.ndarray, sample_rate: int) -> FeatureVector:
    mono = np.asarray(samples, dtype=np.float32).reshape(-1)
    if mono.size == 0:
        return FeatureVector(0.0, 0.0, 0.0, 0.0)

    rms = float(np.sqrt(np.mean(np.square(mono))))
    duration = float(mono.size / sample_rate)

    centered = mono - np.mean(mono)
    sign_changes = np.count_nonzero(np.diff(np.signbit(centered)))
    zero_crossing_rate = float(sign_changes / max(mono.size - 1, 1))

    window = np.hanning(mono.size)
    spectrum = np.abs(np.fft.rfft(centered * window))
    freqs = np.fft.rfftfreq(mono.size, d=1.0 / sample_rate)

    useful_band = freqs >= 300.0
    if np.any(useful_band):
        dominant_frequency = float(freqs[useful_band][np.argmax(spectrum[useful_band])])
    else:
        dominant_frequency = 0.0

    return FeatureVector(
        rms=rms,
        dominant_frequency=dominant_frequency,
        duration=duration,
        zero_crossing_rate=zero_crossing_rate,
    )
