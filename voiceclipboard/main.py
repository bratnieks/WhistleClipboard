from __future__ import annotations

import argparse
import statistics
from typing import Iterable

from voiceclipboard.config import AppConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Whistle-driven clipboard shortcuts.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="RMS threshold for spike detection.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print RMS and frequency metrics for each audio chunk.",
    )
    parser.add_argument(
        "--calibrate",
        type=float,
        nargs="?",
        const=3.0,
        default=0.0,
        help="Listen to ambient sound for a few seconds and suggest thresholds.",
    )
    return parser


def calibrate(listener: MicrophoneListener, detector: SpikeDetector, seconds: float) -> None:
    rms_values: list[float] = []
    ratio_values: list[float] = []
    peak_values: list[float] = []
    print(f"[CALIBRATING] Listening for {seconds:.1f}s of ambient sound...")

    end_after = seconds
    observed = 0.0
    while observed < end_after:
        chunk = listener.read(timeout=1.0)
        metrics = detector.analyze(chunk.samples)
        rms_values.append(metrics.rms)
        ratio_values.append(metrics.high_freq_ratio)
        peak_values.append(metrics.peak)
        observed += len(chunk.samples) / listener.config.sample_rate

    if not rms_values:
        print("[CALIBRATION FAILED] No audio received.")
        return

    # Bias the suggestions above the observed ambient baseline so the tool
    # starts conservative and is easier to tighten by hand.
    suggested_rms = max(statistics.mean(rms_values) * 2.5, max(rms_values) * 1.2)
    suggested_peak = max(statistics.mean(peak_values) * 2.0, max(peak_values) * 1.1)
    suggested_ratio = min(max(statistics.mean(ratio_values) * 1.8, 0.30), 0.85)

    print("[CALIBRATION RESULT]")
    print(f"  RMS threshold suggestion: {suggested_rms:.3f}")
    print(f"  Peak threshold suggestion: {suggested_peak:.3f}")
    print(f"  High-frequency ratio suggestion: {suggested_ratio:.3f}")


def log_debug(rms: float, peak: float, ratio: float) -> None:
    print(f"[DEBUG] rms={rms:.3f} peak={peak:.3f} hf_ratio={ratio:.3f}")


def run(config: AppConfig) -> int:
    from voiceclipboard.actions import ActionExecutor
    from voiceclipboard.audio import MicrophoneListener
    from voiceclipboard.detector import PatternDetector, SpikeDetector

    # Delay audio imports until runtime so --help still works on machines
    # where native audio deps are not installed yet.
    listener = MicrophoneListener(config)
    spike_detector = SpikeDetector(config)
    pattern_detector = PatternDetector(config)
    actions = ActionExecutor()

    try:
        listener.start()

        if config.calibration_seconds > 0:
            calibrate(listener, spike_detector, config.calibration_seconds)
            print("[LISTENING]")
        else:
            print("[LISTENING]")

        while True:
            chunk = listener.read(timeout=1.0)
            metrics = spike_detector.analyze(chunk.samples)

            if config.debug:
                log_debug(metrics.rms, metrics.peak, metrics.high_freq_ratio)

            if metrics.is_spike:
                print("[DETECTED SPIKE]")
                action_name = pattern_detector.register_spike(chunk.captured_at)
                if action_name:
                    trigger_action(action_name, actions)

            pending_action = pattern_detector.flush_pending(chunk.captured_at)
            if pending_action:
                trigger_action(pending_action, actions)

    except KeyboardInterrupt:
        print("\n[STOPPED]")
        return 0
    finally:
        listener.stop()


def trigger_action(action_name: str, actions: ActionExecutor) -> None:
    if action_name == "copy":
        print("[ACTION: COPY]")
        actions.copy()
        return

    if action_name == "paste":
        print("[ACTION: PASTE]")
        actions.paste()
        return

    raise ValueError(f"Unknown action: {action_name}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = AppConfig(debug=args.debug)
    if args.threshold is not None:
        config.threshold = args.threshold
    if args.calibrate:
        config.calibration_seconds = args.calibrate
    else:
        config.calibration_seconds = 0.0

    return run(config)
