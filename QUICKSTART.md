# Quickstart

This guide is the fastest way to get WhistleClipboard running on macOS.

## 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 2. Grant macOS Permissions

Give your terminal app:

- Microphone permission
- Accessibility permission

Accessibility is required so the app can send `Cmd+C` and `Cmd+V`.

## 3. Learn Your Two Whistles

Teach `copy`:

```bash
./run.sh learn copy
```

Teach `paste`:

```bash
./run.sh learn paste
```

Each learn run resets the previous samples for that action and records a fresh set.

## 4. Run It

Normal mode:

```bash
./run.sh run
```

Debug mode:

```bash
./run.sh debug
```

Feedback mode:

```bash
./run.sh feedback
```

In normal mode there is no terminal prompt after detections, so you can keep focus on another app and use copy/paste normally.

## 5. What To Expect

If learned profiles exist:

- the closest learned whistle triggers `copy` or `paste`

If no learned profiles exist yet:

- one spike -> `Cmd+C`
- two quick spikes -> `Cmd+V`

## 6. Troubleshooting

If whistles are too hard to trigger:

```bash
./run.sh debug
```

Then tune thresholds in [whistleclipboard/config.py](/Users/brunoratnieks/dark-agent/WhistleClipboard/whistleclipboard/config.py) or run:

```bash
python main.py --calibrate 4
```

More tuning help is in [docs/TUNING.md](/Users/brunoratnieks/dark-agent/WhistleClipboard/docs/TUNING.md).
