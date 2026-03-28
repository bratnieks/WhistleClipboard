from dataclasses import dataclass


@dataclass
class AppConfig:
    sample_rate: int = 16_000
    block_size: int = 1024
    channels: int = 1
    threshold: float = 0.08
    high_freq_min_hz: float = 1_800.0
    high_freq_max_hz: float = 4_800.0
    high_freq_ratio_threshold: float = 0.45
    peak_threshold: float = 0.18
    min_spike_gap_s: float = 0.12
    double_spike_window_s: float = 0.50
    action_cooldown_s: float = 0.90
    calibration_seconds: float = 3.0
    debug: bool = False
