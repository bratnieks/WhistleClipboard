from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from whistleclipboard.config import AppConfig


@dataclass
class DetectionMetrics:
    rms: float
    peak: float
    high_freq_ratio: float
    is_spike: bool


class SpikeDetector:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def analyze(self, samples: np.ndarray) -> DetectionMetrics:
        mono = np.asarray(samples, dtype=np.float32).reshape(-1)
        if mono.size == 0:
            return DetectionMetrics(0.0, 0.0, 0.0, False)

        rms = float(np.sqrt(np.mean(np.square(mono))))
        peak = float(np.max(np.abs(mono)))

        # A light spectral check helps favor bright whistle-like sounds
        # instead of triggering on any loud transient.
        window = np.hanning(mono.size)
        spectrum = np.abs(np.fft.rfft(mono * window))
        freqs = np.fft.rfftfreq(mono.size, d=1.0 / self.config.sample_rate)

        total_energy = float(np.sum(spectrum)) + 1e-9
        mask = (freqs >= self.config.high_freq_min_hz) & (
            freqs <= self.config.high_freq_max_hz
        )
        high_freq_ratio = float(np.sum(spectrum[mask]) / total_energy)

        is_spike = (
            rms >= self.config.threshold
            and peak >= self.config.peak_threshold
            and high_freq_ratio >= self.config.high_freq_ratio_threshold
        )

        return DetectionMetrics(
            rms=rms,
            peak=peak,
            high_freq_ratio=high_freq_ratio,
            is_spike=is_spike,
        )


class PatternDetector:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._pending_spike_at: float | None = None
        self._last_spike_at: float = -10.0
        self._last_action_at: float = -10.0

    def register_spike(self, when: float) -> str | None:
        if when - self._last_spike_at < self.config.min_spike_gap_s:
            return None
        if when - self._last_action_at < self.config.action_cooldown_s:
            return None

        self._last_spike_at = when

        if self._pending_spike_at is None:
            # First spike starts a short wait window for a possible double trigger.
            self._pending_spike_at = when
            return None

        delta = when - self._pending_spike_at
        if delta <= self.config.double_spike_window_s:
            self._pending_spike_at = None
            self._last_action_at = when
            return "paste"

        self._pending_spike_at = when
        return None

    def flush_pending(self, now: float) -> str | None:
        if self._pending_spike_at is None:
            return None
        if now - self._pending_spike_at < self.config.double_spike_window_s:
            return None
        if now - self._last_action_at < self.config.action_cooldown_s:
            self._pending_spike_at = None
            return None

        self._pending_spike_at = None
        self._last_action_at = now
        return "copy"
