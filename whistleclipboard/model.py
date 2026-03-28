from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from whistleclipboard.features import FeatureVector

ACTIONS = ("copy", "paste")
STD_FLOOR = np.array([0.03, 180.0, 0.05, 0.04], dtype=np.float32)


@dataclass
class ActionStats:
    action: str
    count: int
    mean: FeatureVector
    std: FeatureVector


class ProfileStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, list[FeatureVector]]:
        if not self.path.exists():
            return {action: [] for action in ACTIONS}

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        profiles = {action: [] for action in ACTIONS}
        for action, rows in payload.items():
            if action not in profiles:
                continue
            profiles[action] = [FeatureVector.from_dict(row) for row in rows]
        return profiles

    def save(self, profiles: dict[str, list[FeatureVector]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            action: [feature.to_dict() for feature in profiles.get(action, [])]
            for action in ACTIONS
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_sample(self, action: str, feature: FeatureVector) -> None:
        profiles = self.load()
        profiles.setdefault(action, []).append(feature)
        self.save(profiles)

    def reset_action(self, action: str) -> None:
        profiles = self.load()
        profiles[action] = []
        self.save(profiles)

class LearnedSoundModel:
    def __init__(self, store: ProfileStore) -> None:
        self.store = store
        self._profiles = self.store.load()

    def reload(self) -> None:
        self._profiles = self.store.load()

    def has_profiles(self) -> bool:
        return any(self._profiles.get(action) for action in ACTIONS)

    def sample_count(self, action: str) -> int:
        return len(self._profiles.get(action, []))

    def add_sample(self, action: str, feature: FeatureVector) -> None:
        self._profiles.setdefault(action, []).append(feature)
        self.store.save(self._profiles)

    def reset_action(self, action: str) -> None:
        self._profiles[action] = []
        self.store.save(self._profiles)
    def stats_for(self, action: str) -> ActionStats | None:
        samples = self._profiles.get(action, [])
        if not samples:
            return None

        matrix = np.stack([sample.as_array() for sample in samples])
        mean_row = np.mean(matrix, axis=0)
        std_row = np.std(matrix, axis=0)

        return ActionStats(
            action=action,
            count=len(samples),
            mean=_array_to_feature(mean_row),
            std=_array_to_feature(std_row),
        )

    def classify(self, feature: FeatureVector) -> tuple[str | None, float | None]:
        best_action: str | None = None
        best_distance: float | None = None
        vector = feature.as_array()

        for action in ACTIONS:
            stats = self.stats_for(action)
            if stats is None:
                continue

            mean = stats.mean.as_array()
            # A per-feature std floor keeps tiny sample sets from becoming
            # unrealistically strict and helps the dimensions stay comparable.
            std = np.maximum(stats.std.as_array(), STD_FLOOR)
            distance = float(np.linalg.norm((vector - mean) / std))

            if best_distance is None or distance < best_distance:
                best_action = action
                best_distance = distance

        if best_action is None:
            return None, None

        return best_action, best_distance


def _array_to_feature(values: np.ndarray) -> FeatureVector:
    return FeatureVector(
        rms=float(values[0]),
        dominant_frequency=float(values[1]),
        duration=float(values[2]),
        zero_crossing_rate=float(values[3]),
    )
