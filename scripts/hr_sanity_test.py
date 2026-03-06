import numpy as np
from signal_processing.heart_rate import estimate_hr, smooth_bpm

fs=360
# synthetic ECG: 5 seconds, R-peaks every 0.48s (~ 60/0.48 bpm)
t=np.arange(0,5,1/fs)
signal=np.random.normal(0,0.02,len(t))
for i in range(0,len(t),int(0.48*fs)):
    if i<len(t):
        signal[i]+=1.0

print('len signal', len(signal))
print('estimate_hr ->', estimate_hr(signal, fs))
print('smooth_bpm ->', smooth_bpm(estimate_hr(signal, fs)))
