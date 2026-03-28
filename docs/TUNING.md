# Tuning Guide

## First Run

Start with:

```bash
python main.py --calibrate 4
python main.py --debug
```

The calibration pass listens to the ambient environment and prints suggested threshold values. The debug run then shows live per-chunk metrics.

## Metrics

### RMS

Average chunk energy.

- increase threshold if random room noise causes triggers
- decrease threshold if whistles are not detected

### Peak

Instantaneous amplitude ceiling for the chunk.

- increase if plosives or desk bumps trigger too often
- decrease if soft whistles are missed

### High-Frequency Ratio

Share of spectral energy in the configured high-frequency band.

- increase if low or mid-frequency sounds trigger false positives
- decrease if real whistles are being rejected

## Most Important Config Values

Located in `whistleclipboard/config.py`:

- `threshold`
- `peak_threshold`
- `high_freq_ratio_threshold`
- `high_freq_min_hz`
- `high_freq_max_hz`
- `release_threshold`
- `release_peak_threshold`
- `max_event_duration_s`
- `double_spike_window_s`
- `action_cooldown_s`
- `match_distance_threshold`

## Common Scenarios

### Too many false positives

Try:

- higher `threshold`
- higher `peak_threshold`
- higher `high_freq_ratio_threshold`
- narrower high-frequency band

### Whistles rarely register

Try:

- lower `threshold`
- lower `peak_threshold`
- lower `high_freq_ratio_threshold`
- wider high-frequency band

### Double whistle is too hard to trigger

Increase:

- `double_spike_window_s`

### Actions repeat too often

Increase:

- `action_cooldown_s`
- `min_spike_gap_s`

### Learned matches are wrong too often

Try:

- recording cleaner samples with `--learn`
- collecting more samples for both actions
- lowering `match_distance_threshold` to reject uncertain matches
- using more distinct sounds for `copy` and `paste`

## Practical Advice

- tune in the same room where you will actually use it
- keep one variable change at a time
- use `--debug` while testing
- prefer slightly conservative thresholds at first
