import numpy as np

def generate_ecg_stream(sampling_rate=360):
    """
    Continuous ECG generator (hardware-like)
    - HR variability
    - QRS spike
    - Baseline wander
    - Noise
    - No neurokit dependency
    """

    hr = 75

    while True:

        # --- Heart rate variability ---
        hr += np.random.normal(0, 1.2)
        hr = np.clip(hr, 55, 110)

        rr = 60 / hr  # seconds per beat
        samples = int(rr * sampling_rate)

        # time vector for this beat
        t = np.linspace(0, rr, samples)

        # --- Baseline wander ---
        baseline = 0.2 * np.sin(2 * np.pi * 0.25 * t)

        # --- QRS-like spike ---
        qrs = np.exp(-((t - rr/2) ** 2) / 0.0008) * 1.5

        # --- Low frequency P/T waves ---
        waves = 0.3 * np.sin(2 * np.pi * 1.2 * t)

        # --- Final ECG (no normalization) ---
        ecg = baseline + qrs + waves

        # --- Noise ---
        ecg += 0.05 * np.random.randn(len(ecg))

        # --- ADC-like scaling ---
        adc = (ecg * 200) + 2048  # mid-point around 2048

        adc = np.clip(adc, 1500, 2600)

        for sample in adc:
            yield int(sample)