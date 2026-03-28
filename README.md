# VoiceClipboard

VoiceClipboard is a small, clean, hackable Python CLI that listens to the microphone, detects short whistle-like spikes, and maps them to clipboard shortcuts.

Current macOS behavior:

- One spike -> `Cmd+C`
- Two spikes in quick sequence -> `Cmd+V`

The project is intentionally simple:

- local-only
- no ML models
- fast startup
- low dependency count
- easy to tune

## MVP Features

- Continuous microphone listening with `sounddevice`
- Lightweight frequency-aware spike detection with `numpy`
- Pattern detection for single and double triggers
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
    └── main.py
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

Useful options:

```bash
python main.py --debug
python main.py --threshold 0.09
python main.py --calibrate 4
```

CLI flags:

- `--threshold`
  Overrides the default RMS spike threshold.
- `--debug`
  Prints per-chunk RMS, peak and high-frequency ratio values.
- `--calibrate [seconds]`
  Samples the environment first and prints suggested thresholds.

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

## Tuning

Most useful knobs live in `voiceclipboard/config.py`:

- `threshold`
- `peak_threshold`
- `high_freq_ratio_threshold`
- `double_spike_window_s`
- `action_cooldown_s`

Start with:

```bash
python main.py --calibrate 4
python main.py --debug
```

Then whistle a few times and adjust thresholds based on the logs.

## Portability Notes

The audio and detection parts are already cross-platform friendly.

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
