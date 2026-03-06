import numpy as np
from inference.predictor import ECGPredictor
from preprocessing.preprocess import preprocess_window

predictor = ECGPredictor("model/ecg_model.tflite")

# synthetic window (same shape as training)
window = np.random.rand(360)

processed = preprocess_window(window)

prediction = predictor.predict(processed)

print(prediction)