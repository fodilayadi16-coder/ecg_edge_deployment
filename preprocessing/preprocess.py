import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

FS = 360  # change if needed

# -------- Bandpass Filter --------
def bandpass_filter(signal, lowcut=0.5, highcut=40, fs=FS, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, signal)

# -------- Notch Filter (50 Hz or 60 Hz) --------
def notch_filter(signal, freq=50, fs=FS, Q=30):
    b, a = iirnotch(freq / (fs/2), Q)
    return filtfilt(b, a, signal)

# -------- Z-Score Normalization --------
def zscore(signal):
    mean = np.mean(signal)
    std = np.std(signal)

    if std == 0:
        return signal

    return (signal - mean) / std

# -------- Full Pipeline --------
def preprocess_window(window):
    filtered = bandpass_filter(window)
    filtered = notch_filter(filtered)   # after bandpass
    normalized = zscore(filtered)

    # reshape for CNN (batch, length, channel)
    return normalized.reshape(1, -1, 1)