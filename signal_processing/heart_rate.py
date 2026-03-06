import numpy as np
from collections import deque
from scipy.signal import find_peaks, butter, filtfilt

# Moving average history buffer (global inside module)
hr_history = deque(maxlen=5)


def _bandpass_filter(signal, lowcut=0.5, highcut=40.0, fs=360, order=3):
    """Apply a Butterworth bandpass filter to the signal."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    if low <= 0:
        low = 1e-6
    if high >= 1:
        high = 0.999999
    b, a = butter(order, [low, high], btype='band')
    try:
        return filtfilt(b, a, signal)
    except Exception:
        # fallback to unfiltered if filtfilt fails for short signals
        return signal


def estimate_hr(signal, fs=360):
    """
    Estimate heart rate using RR intervals computed from detected peaks.

    Improvements:
    - Bandpass filter the ECG to remove baseline wander/high-frequency noise
    - Increase refractory period to avoid multiple detections per beat
    - Use a combined prominence threshold for stability
    - Clamp BPM to a physiological range
    """

    if len(signal) < fs:
        return 0

    sig = np.asarray(signal)

    # Filter signal to improve peak detection
    filtered = _bandpass_filter(sig, fs=fs)

    # Peak detection parameters
    min_distance = int(0.35 * fs)  # 350 ms refractory period (reduces double-detection)

    # Robust prominence: require either relative to std or relative to peak amplitude
    max_amp = np.max(np.abs(filtered)) if filtered.size else 0.0
    prominence = max(0.5 * np.std(filtered), 0.1 * max_amp)

    peaks, _ = find_peaks(
        filtered,
        distance=min_distance,
        prominence=prominence
    )

    if len(peaks) < 2:
        return 0

    # Compute RR intervals in seconds
    rr_intervals = np.diff(peaks) / fs
    mean_rr = np.mean(rr_intervals)

    if mean_rr <= 0:
        return 0

    bpm = 60.0 / mean_rr

    # Clamp to reasonable physiological range to avoid spurious outliers
    bpm = float(np.clip(bpm, 30.0, 220.0))

    return bpm


def smooth_bpm(new_bpm):
    """Apply moving average smoothing to BPM readings."""

    if new_bpm > 0:
        hr_history.append(new_bpm)

    if len(hr_history) == 0:
        return 0

    return sum(hr_history) / len(hr_history)