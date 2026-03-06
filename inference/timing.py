import time
import numpy as np
from inference.predictor import ECGPredictor
from preprocessing.preprocess import preprocess_window

predictor = ECGPredictor("model/ecg_model.tflite")

# synthetic window (same shape as training)
window = np.random.rand(360)

processed = preprocess_window(window)
processed = processed.reshape(1, 360, 1)    

start = time.perf_counter()
output = predictor.predict(processed)
end = time.perf_counter()

print("Inference time:", end - start)