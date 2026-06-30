# Clap-to-Advance

Listens to your microphone for a finger snap / clap (a short, sharp,
high-energy sound) and sends a "Right Arrow" keypress to advance the
focused presentation (Slidev, browser slides, etc.) on Wayland/Linux.

## How it works

The script monitors the mic in small ~23ms blocks, tracks a rolling
"background noise" level, and triggers when a block is both:

- louder than an absolute threshold, and
- much louder than the recent background (a sharp transient)

When triggered, it sends a keypress via `ydotool` and then ignores
further snaps for a short cooldown period.

## Requirements

- Python 3 with `sounddevice` and `numpy`
- `ydotool` + its daemon (`ydotoold`) for sending keypresses on Wayland

Install:

```bash
pip install -r requirements.txt
sudo pacman -S ydotool   # or your distro's equivalent
```

## Running

Easiest way — use the provided script, which starts the ydotool
daemon, runs the listener, and cleans everything up on exit:

```bash
./run.sh
```

Press `Ctrl+C` to stop. This stops both the listener and the
`ydotoold` daemon it started.

### Manual run

If you'd rather manage `ydotoold` yourself:

```bash
sudo systemctl enable --now ydotool
python3 snap_advance.py
```

You may need to run with `sudo`, or adjust permissions on the
`ydotool` socket, depending on your setup.

## Tuning

Open `snap_advance.py` and adjust the constants at the top:

| Setting | What it does |
|---|---|
| `THRESHOLD` | Minimum peak volume (0–1) to count as a hit. Raise if it triggers on background noise. |
| `ATTACK_RATIO` | How much louder than recent background a sound must be to count as a snap. |
| `COOLDOWN_SECONDS` | Minimum time between two triggers. |
| `KEY` | Key sent on trigger (`Right`, `Left`, `space`). |
| `DEVICE` | Audio input device (default: `"pulse"`). |

Set `DEBUG = True` (default) to print live peak/background levels in
the terminal so you can see what values to use, then turn it off once
tuned.

List available audio devices:

```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

## Troubleshooting

- **No keypress happens**: make sure `ydotoold` is running and your
  user can access its socket.
- **Nothing detected / silent capture**: double check `DEVICE` matches
  a real input device from `sd.query_devices()`.
- **Too sensitive / not sensitive enough**: tune `THRESHOLD` and
  `ATTACK_RATIO` using the debug output.