#!/usr/bin/env python3
"""
Clap-to-advance for presentations (Wayland/Linux).

Listens to the microphone, detects a finger snap (a short, sharp
high-energy transient), and sends a "Right Arrow" keypress to advance
the focused Slidev/browser slide.

Requirements:
  pip install -r requirements.txt
  sudo pacman -S ydotool

ydotool needs its daemon running. Either:
  sudo systemctl enable --now ydotool
or run manually in another terminal:
  sudo ydotool

Then run this script (may need sudo too, depending on your ydotool
socket permissions):
  python3 snap_advance.py
"""

import subprocess
import sys
import time

import numpy as np
import sounddevice as sd

# ---- Tunables -------------------------------------------------------------
SAMPLE_RATE = 44100
BLOCK_SIZE = 1024          # ~23ms per block, good time resolution for snaps
THRESHOLD = 0.35           # peak amplitude (0-1) to count as a "hit" — raise if too sensitive
ATTACK_RATIO = 6.0         # how much louder than recent background to count as a transient
COOLDOWN_SECONDS = 0.8     # ignore further snaps for this long after a trigger
BACKGROUND_DECAY = 0.97    # how fast the rolling background level adapts
KEY = "Right"              # key sent to advance Slidev (Right / space both work)
DEBUG = True                # print live peak levels — turn off once tuned
DEVICE = "pulse"            # use the PipeWire/Pulse virtual device, not raw ALSA hw — avoids silent capture

# ---- State ------------------------------------------------------------------
background_level = 0.01
last_trigger_time = 0.0


def send_key(key: str) -> None:
    """Send a keypress via ydotool."""
    try:
        subprocess.run(["ydotool", "key", f"{KEYCODES[key]}:1", f"{KEYCODES[key]}:0"], check=True)
    except FileNotFoundError:
        print("ERROR: ydotool not found. Install it with: sudo pacman -S ydotool", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ydotool failed: {e}. Is ydotool running? Try: sudo systemctl start ydotool", file=sys.stderr)


# Linux input-event keycodes ydotool expects (evdev codes)
KEYCODES = {
    "Right": 106,
    "Left": 105,
    "space": 57,
}


def audio_callback(indata, frames, time_info, status):
    global background_level, last_trigger_time

    if status:
        print(status, file=sys.stderr)

    samples = indata[:, 0]
    peak = float(np.max(np.abs(samples)))

    now = time.monotonic()

    # Update a slow-moving "background noise" estimate when things are quiet
    if peak < background_level * 1.5:
        background_level = background_level * BACKGROUND_DECAY + peak * (1 - BACKGROUND_DECAY)
        background_level = max(background_level, 0.005)  # floor so silence doesn't make threshold 0

    is_loud_enough = peak > THRESHOLD
    is_sharp_transient = peak > background_level * ATTACK_RATIO
    is_off_cooldown = (now - last_trigger_time) > COOLDOWN_SECONDS

    if DEBUG:
        # Print every block's peak so you can see real levels and tune THRESHOLD/ATTACK_RATIO
        bar = "#" * int(peak * 50)
        print(f"peak={peak:.3f} bg={background_level:.3f} {bar}")

    if is_loud_enough and is_sharp_transient and is_off_cooldown:
        last_trigger_time = now
        print(f"Clap detected (peak={peak:.3f}, bg={background_level:.3f}) -> sending {KEY}")
        send_key(KEY)


def main():
    print("Listening for claps... (Ctrl+C to stop)")
    print(f"Threshold={THRESHOLD}, attack_ratio={ATTACK_RATIO}, cooldown={COOLDOWN_SECONDS}s")
    try:
        with sd.InputStream(
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            device=DEVICE,
            callback=audio_callback,
        ):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Audio stream error: {e}", file=sys.stderr)
        print("Tip: list input devices with `python3 -c \"import sounddevice as sd; print(sd.query_devices())\"`")


if __name__ == "__main__":
    main()