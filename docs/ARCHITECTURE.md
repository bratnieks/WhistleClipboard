# Architecture

## Overview

WhistleClipboard is split into small modules so the audio pipeline stays easy to understand and modify.

Flow:

```text
Microphone -> Audio chunks -> Spike detector -> Event capture -> Features -> Model -> Shortcut action
```

## Modules

### `main.py`

Small root entrypoint that forwards execution into the package.

### `whistleclipboard/config.py`

Central configuration values for:

- sample rate
- block size
- detection thresholds
- timing windows
- debug mode

### `whistleclipboard/audio.py`

Owns microphone capture.

Responsibilities:

- open the `sounddevice.InputStream`
- receive chunks from the callback
- store them in a bounded queue
- drop the oldest chunk if the consumer falls behind

This keeps the listener responsive and prevents unbounded memory growth.

### `whistleclipboard/detector.py`

Contains the signal and timing logic.

`SpikeDetector`:

- computes RMS
- computes peak amplitude
- runs an FFT
- estimates how much energy sits in the configured high-frequency band
- decides whether a chunk looks like a whistle-like spike

`PatternDetector`:

- tracks pending spikes
- detects single-spike and double-spike gestures
- applies a debounce gap between spikes
- applies an action cooldown

### `whistleclipboard/features.py`

Turns a captured sound event into a compact feature vector:

- RMS energy
- dominant frequency
- duration
- zero crossing rate

These features are cheap to compute and expressive enough for a lightweight local matcher.

### `whistleclipboard/model.py`

Owns learned profile storage and classification.

Responsibilities:

- load and save JSON profiles from `~/.whistleclipboard/profiles.json`
- keep per-action sample vectors
- compute per-action mean and standard deviation
- classify new events using normalized feature distance

### `whistleclipboard/learning.py`

Owns the interactive learning flow.

Responsibilities:

- capture a short event after spike onset
- gather training samples for `copy` and `paste`
- run the post-trigger feedback loop
- reinforce or correct profiles over time

### `whistleclipboard/actions.py`

Owns OS-level actions.

Current implementation:

- macOS via `osascript`

Future ports should extend only this module and keep the rest of the app unchanged.

### `whistleclipboard/main.py`

Coordinates the full runtime:

- parse CLI args
- optionally calibrate
- optionally run learn mode
- choose learned or classic detection flow
- trigger copy or paste

## Runtime Notes

- Audio is captured in small blocks for low latency.
- Detection is chunk-based, not stream-ML-based.
- Imports for audio-heavy modules happen inside `run()` so `python main.py --help` works even when audio dependencies are not fully available.
- Learned profile storage stays local and JSON-based for easy inspection and editing.

## Design Goals

- hackable first
- easy to tune
- low CPU usage
- minimal dependencies
- portable audio and detection core
