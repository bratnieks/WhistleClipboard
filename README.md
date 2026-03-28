# VoiceClipboard

VoiceClipboard is a small, clean, hackable Python CLI that listens to the microphone, detects short whistle-like spikes, and maps them to clipboard shortcuts.

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

## Features

- Continuous microphone listening with `sounddevice`
- Lightweight frequency-aware spike detection with `numpy`
- Classic pattern detection for single and double triggers
- Interactive learning mode for custom sound triggers
- Feature extraction using RMS, dominant frequency, duration and zero crossing rate
- Local profile storage in `~/.voiceclipboard/profiles.json`
- Learned detection with a lightweight statistical distance model
- Feedback loop to reinforce or correct detections
- Cooldown protection to avoid repeated accidental shortcuts
- Debug logging for live tuning
- Basic ambient calibration mode

## Project Structure

```text
VoiceClipboard/
├── main.py
├── requirements.txt
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── TUNING.md
└── voiceclipboard/
    ├── actions.py
    ├── audio.py
    ├── config.py
    ├── detector.py
    ├── features.py
    ├── learning.py
    ├── main.py
    └── model.py
```

## Requirements

- Python 3.9+
- macOS for the current shortcut executor
- A working microphone

## Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## macOS Permissions

On macOS, the terminal app used to run the CLI needs:

- Microphone permission
- Accessibility permission

Accessibility permission is required because the app uses `osascript` with `System Events` to send `Cmd+C` and `Cmd+V`.

## Usage

Run the tool:

```bash
python main.py
```

Installed CLI:

```bash
voiceclipboard
```

Useful options:

```bash
python main.py --debug
python main.py --threshold 0.09
python main.py --calibrate 4
python main.py --learn copy
python main.py --learn paste
voiceclipboard --learn copy
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

## Learn Mode

Teach the tool a custom sound for `copy`:

```bash
python main.py --learn copy
```

Teach the tool a custom sound for `paste`:

```bash
python main.py --learn paste
```

During learning the app:

- records 6 samples by default
- waits for a short spike-like sound each round
- extracts the same feature vector used during detection
- stores samples locally in `~/.voiceclipboard/profiles.json`

Stored JSON shape:

```json
{
  "copy": [
    {
      "rms": 0.11,
      "dominant_frequency": 2142.4,
      "duration": 0.31,
      "zero_crossing_rate": 0.22
    }
  ],
  "paste": []
}
```

## Example Output

```text
[LISTENING]
[DETECTED SPIKE]
[ACTION: COPY]
[DETECTED SPIKE]
[DETECTED SPIKE]
[ACTION: PASTE]
```

## How Detection Works

Each microphone chunk is analyzed with three simple signals:

- RMS energy
- peak amplitude
- ratio of spectral energy in a whistle-friendly high-frequency band

A chunk is considered a spike only when all three thresholds pass. This helps reject many low-frequency noises and broad ambient sounds.

Then the pattern detector applies timing rules:

- first spike starts a short waiting window
- second spike inside the window triggers paste
- if no second spike arrives in time, copy is fired
- cooldown suppresses repeated accidental activations

## Learned Detection

If learned profiles exist, VoiceClipboard switches to learned mode automatically.

For each captured sound event it:

- captures the short event after spike onset
- extracts:
  RMS
  dominant frequency
  duration
  zero crossing rate
- compares that vector against the learned `copy` and `paste` profiles
- triggers the closest valid match

The model stays intentionally lightweight:

- local JSON storage
- raw sample vectors per action
- per-action mean and standard deviation
- normalized distance matching

## Feedback Loop

After each learned trigger the CLI asks:

```text
Detected: COPY
Correct? (y/n)
```

If the answer is:

- `y`
  the detected sample reinforces the predicted action
- `n`
  the CLI asks whether the sample should belong to `copy` or `paste` and updates the saved profiles

## Tuning

Most useful knobs live in `voiceclipboard/config.py`:

- `threshold`
- `peak_threshold`
- `high_freq_ratio_threshold`
- `release_threshold`
- `release_peak_threshold`
- `double_spike_window_s`
- `action_cooldown_s`
- `match_distance_threshold`

Start with:

```bash
python main.py --calibrate 4
python main.py --debug
```

Then whistle a few times and adjust thresholds based on the logs.

## Portability Notes

The audio, feature extraction and model parts are already cross-platform friendly.

The only platform-specific part is shortcut execution in `voiceclipboard/actions.py`.

To support Linux and Windows later, extend that file with alternative key simulation backends such as:

- `xdotool` or `ydotool` on Linux
- PowerShell or a Python automation backend on Windows

## Limitations

- Detection is heuristic-based, not semantic audio recognition
- Very noisy environments may require manual tuning
- Current shortcut execution is implemented only for macOS
- The app assumes the active app should receive `Cmd+C` or `Cmd+V`

## Development

Quick sanity check:

```bash
python main.py --help
```

Recommended next improvements:

- input device selection
- configurable action mapping
- better per-machine calibration persistence
- Linux and Windows shortcut support

## Documentation

- `docs/ARCHITECTURE.md` for module responsibilities and flow
- `docs/TUNING.md` for tuning guidance
- `docs/ROADMAP.md` for next steps
