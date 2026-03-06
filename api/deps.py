from inference.predictor import ECGPredictor

MODEL_PATH = "model/ecg_model.tflite"

predictor = ECGPredictor(MODEL_PATH)