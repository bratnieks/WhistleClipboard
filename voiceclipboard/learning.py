from __future__ import annotations

from dataclasses import dataclass
from queue import Empty

import numpy as np

from voiceclipboard.config import AppConfig
from voiceclipboard.features import FeatureVector, extract_features
from voiceclipboard.model import ACTIONS, LearnedSoundModel


@dataclass
class CapturedEvent:
    samples: np.ndarray
    started_at: float
    ended_at: float


class EventRecorder:
    def __init__(self, config: AppConfig, spike_detector) -> None:
        self.config = config
        self.spike_detector = spike_detector

    def wait_for_event(self, listener, timeout: float | None = None) -> CapturedEvent | None:
        chunks: list[np.ndarray] = []
        recording = False
        started_at = 0.0
        silence_chunks = 0
        max_chunks = max(
            1,
            int(self.config.max_event_duration_s * self.config.sample_rate / self.config.block_size),
        )
        needed_silence_chunks = max(
            1,
            int(self.config.event_silence_s * self.config.sample_rate / self.config.block_size),
        )
        remaining = timeout

        while True:
            chunk_timeout = 1.0 if remaining is None else max(0.1, min(1.0, remaining))
            try:
                chunk = listener.read(timeout=chunk_timeout)
            except Empty:
                return None

            if remaining is not None:
                remaining -= len(chunk.samples) / self.config.sample_rate
                if remaining <= 0 and not recording:
                    return None

            metrics = self.spike_detector.analyze(chunk.samples)
            chunk_samples = np.asarray(chunk.samples, dtype=np.float32).reshape(-1)

            if not recording:
                if not metrics.is_spike:
                    continue
                # Start recording on the first confident spike and then keep
                # collecting until the sound decays back into silence.
                recording = True
                started_at = chunk.captured_at

            chunks.append(chunk_samples)

            quiet_chunk = (
                metrics.rms < self.config.release_threshold
                and metrics.peak < self.config.release_peak_threshold
            )
            silence_chunks = silence_chunks + 1 if quiet_chunk else 0

            if silence_chunks >= needed_silence_chunks or len(chunks) >= max_chunks:
                return CapturedEvent(
                    samples=np.concatenate(chunks),
                    started_at=started_at,
                    ended_at=chunk.captured_at,
                )


def learn_action_samples(
    action: str,
    listener,
    recorder: EventRecorder,
    model: LearnedSoundModel,
    sample_rate: int,
    sample_count: int,
    timeout: float,
) -> int:
    learned = 0

    while learned < sample_count:
        print(f"[LEARN] Sample {learned + 1}/{sample_count} for {action.upper()}")
        print("[LEARN] Make the sound now...")
        event = recorder.wait_for_event(listener, timeout=timeout)
        if event is None:
            print("[LEARN] Timed out waiting for a sound, trying again.")
            continue

        feature = extract_features(event.samples, sample_rate)
        model.add_sample(action, feature)
        learned += 1
        print(f"[LEARNED] {format_feature_vector(feature)}")

    return learned


def feedback_loop(model: LearnedSoundModel, predicted_action: str, feature: FeatureVector) -> None:
    try:
        answer = input("Correct? (y/n) ").strip().lower()
    except EOFError:
        print("[FEEDBACK] Skipped because stdin is not interactive.")
        return

    if answer == "y":
        model.add_sample(predicted_action, feature)
        print(f"[MODEL] Reinforced {predicted_action.upper()} profile.")
        return

    if answer != "n":
        print("[FEEDBACK] Skipped.")
        return

    while True:
        try:
            corrected_action = input("Which action was correct? (copy/paste) ").strip().lower()
        except EOFError:
            print("[FEEDBACK] Skipped because stdin is not interactive.")
            return

        if corrected_action in ACTIONS:
            model.add_sample(corrected_action, feature)
            print(f"[MODEL] Added sample to {corrected_action.upper()}.")
            return

        print("Please type 'copy' or 'paste'.")


def format_feature_vector(feature: FeatureVector) -> str:
    return (
        f"rms={feature.rms:.3f} "
        f"freq={feature.dominant_frequency:.1f}Hz "
        f"duration={feature.duration:.3f}s "
        f"zcr={feature.zero_crossing_rate:.3f}"
    )
