from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppConfig:
    sample_rate: int = 16_000
    block_size: int = 1024
    channels: int = 1
    threshold: float = 0.055
    high_freq_min_hz: float = 1_800.0
    high_freq_max_hz: float = 4_800.0
    high_freq_ratio_threshold: float = 0.34
    peak_threshold: float = 0.12
    min_spike_gap_s: float = 0.12
    double_spike_window_s: float = 0.50
    action_cooldown_s: float = 0.90
    calibration_seconds: float = 3.0
    release_threshold: float = 0.035
    release_peak_threshold: float = 0.08
    event_silence_s: float = 0.14
    max_event_duration_s: float = 0.90
    learn_sample_count: int = 6
    learn_timeout_s: float = 8.0
    learn_max_attempts: int = 18
    match_distance_threshold: float = 9.5
    profile_path: Path = field(
        default_factory=lambda: Path.home() / ".whistleclipboard" / "profiles.json"
    )
    debug: bool = False
