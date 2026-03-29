# WhistleClipboard

WhistleClipboard is a small, clean, hackable Python CLI that listens to the microphone, detects short whistle-like spikes, and maps them to clipboard shortcuts.

This is an early-stage alpha project. Suggestions, experiments, bug reports, and contributions are very welcome.

Current macOS behavior:

- Classic mode without learned profiles:
  one spike -> `Cmd+C`
  two spikes in quick sequence -> `Cmd+V`
- Learned mode with profiles:
  the closest learned sound triggers `copy` or `paste`

The project is intentionally simple:

- local-only
- no ML models
- fast startup
- low dependency count
- easy to tune

## Quick Links

- Quick start: [QUICKSTART.md](/Users/brunoratnieks/dark-agent/WhistleClipboard/QUICKSTART.md)
- Architecture: [docs/ARCHITECTURE.md](/Users/brunoratnieks/dark-agent/WhistleClipboard/docs/ARCHITECTURE.md)
- Tuning guide: [docs/TUNING.md](/Users/brunoratnieks/dark-agent/WhistleClipboard/docs/TUNING.md)
- Roadmap: [docs/ROADMAP.md](/Users/brunoratnieks/dark-agent/WhistleClipboard/docs/ROADMAP.md)

## Features

- Continuous microphone listening with `sounddevice`
- Lightweight frequency-aware spike detection with `numpy`
- Classic pattern detection for single and double triggers
- Interactive learning mode for custom sound triggers
- Feature extraction using RMS, dominant frequency, duration and zero crossing rate
- Local profile storage in `~/.whistleclipboard/profiles.json`
- Learned detection with a lightweight statistical distance model
- Optional feedback loop to reinforce or correct detections
- Cooldown protection to avoid repeated accidental shortcuts
- Debug logging for live tuning
- Basic ambient calibration mode

## Requirements

- Python 3.9+
- macOS for the current shortcut executor
- A working microphone

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage

Installed CLI:

```bash
whistleclipboard
```

Convenience script:

```bash
./run.sh help
```

Wrapper commands:

```bash
./run.sh run
./run.sh debug
./run.sh learn copy
./run.sh learn paste
./run.sh feedback
```

Useful CLI options:

```bash
python main.py --debug
python main.py --threshold 0.09
python main.py --calibrate 4
python main.py --learn copy
python main.py --learn paste
```

CLI flags:

- `--threshold`
  Overrides the default RMS spike threshold.
- `--debug`
  Prints per-chunk RMS, peak and high-frequency ratio values.
- `--calibrate [seconds]`
  Samples the environment first and prints suggested thresholds.
- `--learn {copy,paste}`
  Records a set of training samples for the given action.
- `--feedback`
  Enables interactive reinforcement prompts after learned detections.

## macOS Permissions

The terminal app used to run the CLI needs:

- Microphone permission
- Accessibility permission

Accessibility permission is required because the app uses `osascript` with `System Events` to send `Cmd+C` and `Cmd+V`.

## How Detection Works

Each microphone chunk is analyzed with three simple signals:

- RMS energy
- peak amplitude
- ratio of spectral energy in a whistle-friendly high-frequency band

A chunk is considered a spike only when all three thresholds pass. This helps reject many low-frequency noises and broad ambient sounds.

Classic mode then applies timing rules:

- first spike starts a short waiting window
- second spike inside the window triggers paste
- if no second spike arrives in time, copy is fired
- cooldown suppresses repeated accidental activations

Learned mode captures short whistle events and compares feature vectors using:

- RMS
- dominant frequency
- duration
- zero crossing rate

Profiles are stored locally in `~/.whistleclipboard/profiles.json`.

## Example Output

```text
[LISTENING]
[DETECTED SPIKE]
[ACTION: COPY]
[DETECTED SPIKE]
[DETECTED SPIKE]
[ACTION: PASTE]
```

## Project Structure

```text
WhistleClipboard/
├── main.py
├── QUICKSTART.md
├── README.md
├── requirements.txt
├── run.sh
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── TUNING.md
└── whistleclipboard/
    ├── actions.py
    ├── audio.py
    ├── config.py
    ├── detector.py
    ├── features.py
    ├── learning.py
    ├── main.py
    └── model.py
```
