"""
Bifurcation Sonification — Hearing the Road to Chaos

The logistic map x → rx(1-x) produces orbits that can be directly
converted to audio. The result makes the period-doubling cascade
and onset of chaos audible:

  Period 1:  Silence    (constant orbit → DC → filtered to zero)
  Period 2:  440 Hz     (orbit alternates between two values)
  Period 4:  220 Hz     (four-value cycle, one octave lower)
  Period 8:  110 Hz     (eight-value cycle, another octave)
  ...each period-doubling halves the pitch — descending octaves...
  Chaos:     Noise      (unpredictable orbit → aperiodic waveform)
  Period 3:  ~293 Hz    (three-value cycle in the famous window)

The base iteration rate is 880 Hz. This is the "sampling rate" of
the logistic map; an orbit of period P repeats every P iterations,
producing a tone at 880/P Hz. Period-doubling literally halves the
frequency, so you hear the cascade as a staircase of descending
octaves accelerating toward noise.

The onset of chaos is the moment music becomes noise. The period-3
window is a brief island of tone in the sea of noise — Li and Yorke's
"period three implies chaos" made audible.

Usage:
    python3 sonify.py                # Sweep r = 2.9→4.0 (20s WAV)
    python3 sonify.py cascade        # Step through key r values
    python3 sonify.py tone 3.5       # Single r value (5s WAV)
    python3 sonify.py waveforms      # Show orbit shapes in terminal
"""

import sys
import os
import struct
import array
import math
import time


# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

SAMPLE_RATE = 44100
BASE_FREQ = 880     # Logistic map iterations per second
                    # Period 2 → 440 Hz, Period 4 → 220 Hz, etc.


# ═══════════════════════════════════════════════════════════════
#  WAV file writer (pure Python, no dependencies)
# ═══════════════════════════════════════════════════════════════

def write_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Write mono 16-bit PCM WAV. Samples should be floats in [-1.0, 1.0]."""
    # Convert to 16-bit integers
    pcm = array.array('h', (
        max(-32768, min(32767, int(s * 32767)))
        for s in samples
    ))
    if sys.byteorder == 'big':
        pcm.byteswap()

    data_size = len(pcm) * 2  # 2 bytes per sample

    with open(filename, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')

        # fmt chunk (16 bytes of format data)
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))          # chunk data size
        f.write(struct.pack('<H', 1))           # PCM format
        f.write(struct.pack('<H', 1))           # mono
        f.write(struct.pack('<I', sample_rate)) # sample rate
        f.write(struct.pack('<I', sample_rate * 2))  # byte rate
        f.write(struct.pack('<H', 2))           # block align
        f.write(struct.pack('<H', 16))          # bits per sample

        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        pcm.tofile(f)


# ═══════════════════════════════════════════════════════════════
#  Logistic map
# ═══════════════════════════════════════════════════════════════

def logistic(r, x):
    return r * x * (1.0 - x)


def find_period(r, warmup=3000, tol=1e-8, max_period=256):
    """Detect the period of the orbit at parameter r."""
    x = 0.2
    for _ in range(warmup):
        x = logistic(r, x)
    orbit = [x]
    for _ in range(max_period):
        x = logistic(r, x)
        for p, val in enumerate(orbit):
            if abs(x - val) < tol:
                return len(orbit) - p
        orbit.append(x)
    return -1


# ═══════════════════════════════════════════════════════════════
#  Audio processing
# ═══════════════════════════════════════════════════════════════

def highpass(audio, cutoff_hz=15):
    """First-order IIR highpass filter to remove DC offset."""
    rc = 1.0 / (2.0 * math.pi * cutoff_hz)
    dt = 1.0 / SAMPLE_RATE
    alpha = rc / (rc + dt)

    out = [0.0] * len(audio)
    if len(audio) < 2:
        return out

    prev_out = 0.0
    prev_in = audio[0]
    for i in range(1, len(audio)):
        prev_out = alpha * (prev_out + audio[i] - prev_in)
        prev_in = audio[i]
        out[i] = prev_out
    return out


def normalize(audio, target=0.85):
    """Normalize peak amplitude to target level."""
    peak = max((abs(s) for s in audio), default=0.0)
    if peak < 1e-10:
        return audio
    scale = target / peak
    return [s * scale for s in audio]


def fade_ends(audio, fade_in_ms=10, fade_out_ms=100):
    """Apply gentle fade-in and fade-out."""
    n = len(audio)
    fi = min(int(fade_in_ms * SAMPLE_RATE / 1000), n)
    fo = min(int(fade_out_ms * SAMPLE_RATE / 1000), n)
    out = list(audio)
    for i in range(fi):
        out[i] *= i / fi
    for i in range(fo):
        out[n - 1 - i] *= i / fo
    return out


def section_fades(audio, n_sections, fade_ms=5):
    """Apply tiny fades at section boundaries to prevent clicks."""
    if n_sections <= 1:
        return audio
    out = list(audio)
    section_len = len(audio) // n_sections
    fade_n = int(fade_ms * SAMPLE_RATE / 1000)

    for s in range(1, n_sections):
        boundary = s * section_len
        # Fade out end of previous section
        for i in range(fade_n):
            idx = boundary - 1 - i
            if 0 <= idx < len(out):
                out[idx] *= i / fade_n
        # Fade in start of next section
        for i in range(fade_n):
            idx = boundary + i
            if 0 <= idx < len(out):
                out[idx] *= i / fade_n
    return out


# ═══════════════════════════════════════════════════════════════
#  Orbit generation
# ═══════════════════════════════════════════════════════════════

def generate_sweep_orbit(duration=20, r_start=2.9, r_end=4.0):
    """Generate logistic map orbit sweeping r linearly."""
    total_iters = int(duration * BASE_FREQ)
    x = 0.2
    orbit = []

    for k in range(total_iters):
        r = r_start + (r_end - r_start) * k / (total_iters - 1)
        x = logistic(r, x)
        orbit.append(x)

    return orbit


def generate_cascade_orbit(hold=2.5):
    """Generate orbit stepping through key r values."""
    r_values = [
        (2.9,    "Period 1 — silence"),
        (3.2,    "Period 2 — 440 Hz (A4)"),
        (3.5,    "Period 4 — 220 Hz (A3)"),
        (3.555,  "Period 8 — 110 Hz (A2)"),
        (3.8,    "Chaos — noise"),
        (3.83,   "Period 3 — ~293 Hz (D4)"),
        (3.57,   "Edge of chaos"),
        (3.9,    "Deep chaos"),
        (4.0,    "Full chaos — max entropy"),
    ]

    iters_per_section = int(hold * BASE_FREQ)
    orbit = []

    for r, _ in r_values:
        x = 0.2
        # Warmup: let orbit settle
        for _ in range(3000):
            x = logistic(r, x)
        # Record
        for _ in range(iters_per_section):
            x = logistic(r, x)
            orbit.append(x)

    return orbit, r_values


def generate_tone_orbit(r, duration=5):
    """Generate orbit at a single r value."""
    total_iters = int(duration * BASE_FREQ)
    x = 0.2
    for _ in range(3000):
        x = logistic(r, x)
    orbit = []
    for _ in range(total_iters):
        x = logistic(r, x)
        orbit.append(x)
    return orbit


# ═══════════════════════════════════════════════════════════════
#  Orbit → Audio conversion
# ═══════════════════════════════════════════════════════════════

def orbit_to_audio(orbit, duration):
    """Upsample orbit to audio rate using sample-and-hold."""
    total_samples = int(duration * SAMPLE_RATE)
    n_orbit = len(orbit)
    audio = [0.0] * total_samples

    for i in range(total_samples):
        idx = int(i * n_orbit / total_samples)
        if idx >= n_orbit:
            idx = n_orbit - 1
        audio[i] = orbit[idx]

    return audio


def process_audio(audio, n_sections=0):
    """Apply highpass, section fades, end fades, and normalization."""
    audio = highpass(audio)
    if n_sections > 1:
        audio = section_fades(audio, n_sections)
    audio = fade_ends(audio)
    audio = normalize(audio)
    return audio


# ═══════════════════════════════════════════════════════════════
#  Braille canvas (for terminal visualization)
# ═══════════════════════════════════════════════════════════════

BRAILLE_BASE = 0x2800
BRAILLE_BITS = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}


class BrailleCanvas:
    def __init__(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.dw, self.dh = cw * 2, ch * 4
        self.grid = [[0] * cw for _ in range(ch)]

    def set(self, dx, dy):
        if 0 <= dx < self.dw and 0 <= dy < self.dh:
            self.grid[dy // 4][dx // 2] |= BRAILLE_BITS[(dx % 2, dy % 4)]

    def plot_data(self, x, y, xr, yr):
        dx = int((x - xr[0]) / (xr[1] - xr[0] + 1e-15) * (self.dw - 1))
        dy = int((1 - (y - yr[0]) / (yr[1] - yr[0] + 1e-15)) * (self.dh - 1))
        self.set(dx, dy)

    def render(self):
        return ["".join(chr(BRAILLE_BASE + c) for c in row) for row in self.grid]


# ═══════════════════════════════════════════════════════════════
#  Terminal visualization
# ═══════════════════════════════════════════════════════════════

def show_orbit_snippet(r, n_iters=80, cw=65, ch=4, label=""):
    """Display an orbit waveform using braille characters."""
    x = 0.2
    for _ in range(2000):
        x = logistic(r, x)
    orbit = []
    for _ in range(n_iters):
        x = logistic(r, x)
        orbit.append(x)

    canvas = BrailleCanvas(cw, ch)
    y_lo, y_hi = min(orbit), max(orbit)
    if y_hi - y_lo < 1e-10:
        y_lo -= 0.1
        y_hi += 0.1

    for i, v in enumerate(orbit):
        canvas.plot_data(i, v, (0, n_iters - 1), (y_lo, y_hi))

    if label:
        print(f"    {label}")
    for line in canvas.render():
        print(f"    {line}")


def show_audio_snippet(audio, start_s, dur_s, cw=70, ch=3, label=""):
    """Display a section of audio waveform using braille."""
    i0 = int(start_s * SAMPLE_RATE)
    i1 = min(int((start_s + dur_s) * SAMPLE_RATE), len(audio))
    seg = audio[i0:i1]
    if not seg:
        return

    canvas = BrailleCanvas(cw, ch)
    y_lo, y_hi = min(seg), max(seg)
    if y_hi - y_lo < 1e-10:
        y_lo -= 0.1
        y_hi += 0.1

    for i, v in enumerate(seg):
        canvas.plot_data(i, v, (0, len(seg) - 1), (y_lo, y_hi))

    if label:
        print(f"    {label}")
    for line in canvas.render():
        print(f"    {line}")


def waveforms_mode():
    """Show orbit shapes at key r values — what the audio "looks like"."""
    print("  What the logistic map orbit looks like at each regime:")
    print("  (these orbit values become the audio waveform)")
    print()

    cases = [
        (2.9,    "r=2.9  Period 1:  constant → silence"),
        (3.2,    "r=3.2  Period 2:  square wave → 440 Hz (A4)"),
        (3.5,    "r=3.5  Period 4:  stepped wave → 220 Hz (A3)"),
        (3.555,  "r=3.56 Period 8:  complex step → 110 Hz (A2)"),
        (3.8,    "r=3.8  Chaos:     aperiodic → noise"),
        (3.83,   "r=3.83 Period 3:  triangle-ish → 293 Hz (D4)"),
        (4.0,    "r=4.0  Full chaos: fills [0,1] → max noise"),
    ]

    for r, label in cases:
        show_orbit_snippet(r, label=label)
        print()


# ═══════════════════════════════════════════════════════════════
#  Modes
# ═══════════════════════════════════════════════════════════════

def sweep_mode():
    """Generate a continuous r-sweep WAV file."""
    r_start, r_end, duration = 2.9, 4.0, 20
    filename = "bifurcation_sweep.wav"

    print(f"  Sweep: r = {r_start} → {r_end} over {duration}s")
    print(f"  Base iteration rate: {BASE_FREQ} Hz")
    print()
    print("  What you'll hear:")
    print("    Period 1  → silence          (constant orbit)")
    print("    Period 2  → 440 Hz / A4      (orbit alternates between 2 values)")
    print("    Period 4  → 220 Hz / A3      (one octave lower)")
    print("    Period 8  → 110 Hz / A2      (another octave)")
    print("    Period 16 →  55 Hz           (subsonic rumble)")
    print("    Chaos     → broadband noise  (aperiodic orbit)")
    print("    Period 3  → 293 Hz / D4      (brief tone in chaos)")
    print()

    t0 = time.time()
    sys.stdout.write("  Generating orbit...")
    sys.stdout.flush()
    orbit = generate_sweep_orbit(duration, r_start, r_end)
    sys.stdout.write(f" {len(orbit):,} iterations\n")

    sys.stdout.write("  Converting to audio...")
    sys.stdout.flush()
    audio = orbit_to_audio(orbit, duration)
    sys.stdout.write(f" {len(audio):,} samples\n")

    sys.stdout.write("  Processing (highpass + normalize)...")
    sys.stdout.flush()
    audio = process_audio(audio)
    elapsed = time.time() - t0
    sys.stdout.write(f" done ({elapsed:.1f}s)\n")

    sys.stdout.write(f"  Writing {filename}...")
    sys.stdout.flush()
    write_wav(filename, audio)
    filesize = os.path.getsize(filename)
    sys.stdout.write(f" {filesize // 1024} KB\n")
    print()

    # Timeline
    r_rate = (r_end - r_start) / duration
    print("  Timeline:")
    print("  ─────────────────────────────────────────────────────")

    events = [
        (3.000, "First bifurcation — a 440 Hz tone emerges from silence"),
        (3.449, "Period 4 — pitch drops to 220 Hz"),
        (3.544, "Period 8 — drops to 110 Hz"),
        (3.570, "Accumulation point — onset of chaos"),
        (3.679, "Full-band chaos"),
        (3.830, "Period-3 window — brief 293 Hz tone in the noise"),
        (4.000, "Maximum chaos — orbit fills [0, 1]"),
    ]

    for r, desc in events:
        t = (r - r_start) / r_rate
        print(f"    t={t:5.1f}s  r={r:.3f}  {desc}")
    print()

    # Show audio waveform at key moments
    print("  Audio waveform snapshots (15ms windows):")
    print()

    moments = [
        (3.2,    "r≈3.2 — Period 2 (square wave at 440 Hz)"),
        (3.5,    "r≈3.5 — Period 4 (stepped wave at 220 Hz)"),
        (3.8,    "r≈3.8 — Chaos (noise)"),
        (3.83,   "r≈3.83 — Period-3 window (293 Hz)"),
    ]

    for r, label in moments:
        t = (r - r_start) / r_rate
        show_audio_snippet(audio, t, 0.015, cw=70, ch=3, label=label)
        print()


def cascade_mode():
    """Generate a WAV stepping through key r values."""
    hold = 2.5
    filename = "bifurcation_cascade.wav"

    print(f"  Cascade: stepping through key r values ({hold}s each)")
    print()

    t0 = time.time()
    orbit, r_values = generate_cascade_orbit(hold=hold)
    duration = len(orbit) / BASE_FREQ
    audio = orbit_to_audio(orbit, duration)
    audio = process_audio(audio, n_sections=len(r_values))
    elapsed = time.time() - t0

    print(f"  Generated {len(audio):,} samples in {elapsed:.1f}s")

    write_wav(filename, audio)
    filesize = os.path.getsize(filename)
    print(f"  Wrote {filename} ({filesize // 1024} KB)")
    print()

    print("  Sections:")
    print("  ─────────────────────────────────────────────────────────")

    for i, (r, desc) in enumerate(r_values):
        t = i * hold
        period = find_period(r)
        if period > 0:
            freq = BASE_FREQ / period
            p_str = f"period {period}"
            f_str = f"{freq:.0f} Hz"
        else:
            p_str = "chaotic"
            f_str = "noise"
        print(f"    {t:5.1f}s  r={r:<7.4f}  {p_str:>10s}  {f_str:>7s}  {desc}")

    print()
    print(f"  Duration: {duration:.1f}s")


def tone_mode(r):
    """Generate a WAV at a single r value."""
    duration = 5
    filename = f"logistic_r{r:.3f}.wav"

    period = find_period(r)
    if period > 0:
        freq = BASE_FREQ / period
        p_str = f"period {period}"
        f_str = f"{freq:.0f} Hz"
    else:
        p_str = "chaotic"
        f_str = "noise"

    print(f"  Tone: r = {r:.4f} ({p_str}, {f_str}) for {duration}s")
    print()

    orbit = generate_tone_orbit(r, duration)
    audio = orbit_to_audio(orbit, duration)
    audio = process_audio(audio)

    write_wav(filename, audio)
    filesize = os.path.getsize(filename)
    print(f"  Wrote {filename} ({filesize // 1024} KB)")
    print()

    show_orbit_snippet(r, n_iters=80, cw=70, ch=5,
                       label=f"Orbit at r={r:.4f} ({p_str})")
    print()


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "sweep"

    print()
    print("  ═══════════════════════════════════════════════════════════")
    print("  \033[1m  BIFURCATION SONIFICATION\033[0m")
    print("  \033[1m  Hearing the Road to Chaos\033[0m")
    print("  ═══════════════════════════════════════════════════════════")
    print()
    print("  The logistic map orbit becomes audio. Period-doubling becomes")
    print("  descending pitch. The onset of chaos is the moment tone becomes")
    print("  noise. The period-3 window is a brief melody in the static.")
    print()

    if mode == "sweep":
        sweep_mode()
    elif mode == "cascade":
        cascade_mode()
    elif mode == "tone":
        r = float(args[1]) if len(args) > 1 else 3.2
        tone_mode(r)
    elif mode == "waveforms":
        waveforms_mode()
        return
    else:
        print(f"  Unknown mode: {mode}")
        print(f"  Modes: sweep, cascade, tone <r>, waveforms")
        return

    print("  ─────────────────────────────────────────────────────────")
    print(f"  Base frequency: {BASE_FREQ} Hz")
    print(f"  Each period-doubling halves the pitch — an octave descent.")
    print(f"  The Feigenbaum cascade accelerates through infinite octaves")
    print(f"  in finite time, converging at r ≈ 3.5699 where pitch reaches")
    print(f"  zero and noise begins.")
    print()


if __name__ == "__main__":
    main()
