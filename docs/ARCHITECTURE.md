# Architecture

## Overview

VoiceClipboard is split into small modules so the audio pipeline stays easy to understand and modify.

Flow:

```text
Microphone -> Audio chunks -> Spike detector -> Pattern detector -> Shortcut action
```

## Modules

### `main.py`

Small root entrypoint that forwards execution into the package.

### `voiceclipboard/config.py`

Central configuration values for:

- sample rate
- block size
- detection thresholds
- timing windows
- debug mode

### `voiceclipboard/audio.py`

Owns microphone capture.

Responsibilities:

- open the `sounddevice.InputStream`
- receive chunks from the callback
- store them in a bounded queue
- drop the oldest chunk if the consumer falls behind

This keeps the listener responsive and prevents unbounded memory growth.

### `voiceclipboard/detector.py`

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

### `voiceclipboard/actions.py`

Owns OS-level actions.

Current implementation:

- macOS via `osascript`

Future ports should extend only this module and keep the rest of the app unchanged.

### `voiceclipboard/main.py`

Coordinates the full runtime:

- parse CLI args
- optionally calibrate
- start the microphone listener
- analyze chunks
- run pattern detection
- trigger copy or paste

## Runtime Notes

- Audio is captured in small blocks for low latency.
- Detection is chunk-based, not stream-ML-based.
- Imports for audio-heavy modules happen inside `run()` so `python main.py --help` works even when audio dependencies are not fully available.

## Design Goals

- hackable first
- easy to tune
- low CPU usage
- minimal dependencies
- portable audio and detection core
