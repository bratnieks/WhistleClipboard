from __future__ import annotations

import argparse
import statistics
from typing import Iterable

from voiceclipboard.config import AppConfig

LEARNABLE_ACTIONS = ("copy", "paste")


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
    parser.add_argument(
        "--learn",
        choices=LEARNABLE_ACTIONS,
        help="Record a set of training samples for the given action.",
    )
    parser.add_argument(
        "--feedback",
        action="store_true",
        help="Ask for interactive yes/no feedback after each learned detection.",
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


def run_learn_mode(config: AppConfig, action: str) -> int:
    from voiceclipboard.audio import MicrophoneListener
    from voiceclipboard.detector import SpikeDetector
    from voiceclipboard.learning import EventRecorder, learn_action_samples
    from voiceclipboard.model import LearnedSoundModel, ProfileStore

    listener = MicrophoneListener(config)
    spike_detector = SpikeDetector(config)
    recorder = EventRecorder(config, spike_detector)
    model = LearnedSoundModel(ProfileStore(config.profile_path))

    try:
        listener.start()
        print(f"[LEARN MODE] Recording samples for {action.upper()}")
        print(f"[LEARN MODE] Profiles will be stored at {config.profile_path}")
        model.reset_action(action)
        print(f"[LEARN MODE] Reset previous samples for {action.upper()}.")
        learned = learn_action_samples(
            action=action,
            listener=listener,
            recorder=recorder,
            model=model,
            sample_rate=config.sample_rate,
            sample_count=config.learn_sample_count,
            timeout=config.learn_timeout_s,
            max_attempts=config.learn_max_attempts,
        )
        if learned >= config.learn_sample_count:
            print(f"[LEARN MODE] {action.upper()} now has {model.sample_count(action)} samples.")
        else:
            print(
                f"[LEARN MODE] Finished early with {learned}/{config.learn_sample_count} "
                f"new samples for {action.upper()}."
            )
        return 0
    except KeyboardInterrupt:
        print("\n[STOPPED]")
        return 0
    finally:
        listener.stop()


def run_learned_detection(config: AppConfig, feedback_enabled: bool = False) -> int:
    from voiceclipboard.actions import ActionExecutor
    from voiceclipboard.audio import MicrophoneListener
    from voiceclipboard.detector import SpikeDetector
    from voiceclipboard.features import extract_features
    from voiceclipboard.learning import EventRecorder, format_feature_vector, resolve_feedback_action
    from voiceclipboard.model import LearnedSoundModel, ProfileStore

    # Delay audio imports until runtime so --help still works on machines
    # where native audio deps are not installed yet.
    listener = MicrophoneListener(config)
    spike_detector = SpikeDetector(config)
    recorder = EventRecorder(config, spike_detector)
    actions = ActionExecutor()
    model = LearnedSoundModel(ProfileStore(config.profile_path))

    try:
        listener.start()

        if config.calibration_seconds > 0:
            calibrate(listener, spike_detector, config.calibration_seconds)

        print("[LISTENING]")
        print(f"[MODEL] Loading profiles from {config.profile_path}")

        while True:
            event = recorder.wait_for_event(listener, timeout=None)
            if event is None:
                continue

            feature = extract_features(event.samples, config.sample_rate)
            action_name, distance = model.classify(feature)

            if action_name is None:
                print("[MODEL] No learned profiles found. Run with --learn copy or --learn paste first.")
                return 1

            print("[DETECTED SPIKE]")
            if config.debug:
                print(f"[MATCH] distance={distance:.3f}")
                print(f"[MATCH] {format_feature_vector(feature)}")

            if distance is not None and distance > config.match_distance_threshold:
                print(
                    "[MODEL] Closest profile was too far away "
                    f"(distance={distance:.3f}). Ignoring event."
                )
                continue

            if feedback_enabled:
                resolved_action = resolve_feedback_action(model, action_name, feature)
            else:
                resolved_action = action_name
            trigger_action(resolved_action, actions)

    except KeyboardInterrupt:
        print("\n[STOPPED]")
        return 0
    finally:
        listener.stop()


def run_classic_detection(config: AppConfig) -> int:
    from voiceclipboard.actions import ActionExecutor
    from voiceclipboard.audio import MicrophoneListener
    from voiceclipboard.detector import PatternDetector, SpikeDetector

    listener = MicrophoneListener(config)
    spike_detector = SpikeDetector(config)
    pattern_detector = PatternDetector(config)
    actions = ActionExecutor()

    try:
        listener.start()

        if config.calibration_seconds > 0:
            calibrate(listener, spike_detector, config.calibration_seconds)
        print("[LISTENING]")
        print("[MODEL] No learned profiles found, using classic single/double spike mode.")

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


def run(
    config: AppConfig, learn_action: str | None = None, feedback_enabled: bool = False
) -> int:
    from voiceclipboard.model import LearnedSoundModel, ProfileStore

    if learn_action is not None:
        return run_learn_mode(config, learn_action)

    model = LearnedSoundModel(ProfileStore(config.profile_path))
    if model.has_profiles():
        return run_learned_detection(config, feedback_enabled=feedback_enabled)
    return run_classic_detection(config)


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

    return run(config, learn_action=args.learn, feedback_enabled=args.feedback)
