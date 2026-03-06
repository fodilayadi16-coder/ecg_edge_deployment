import tensorflow as tf
import numpy as np

class ECGPredictor:
    def __init__(self, model_path):
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def predict(self, input_data):
        self.interpreter.set_tensor(
            self.input_details[0]['index'],
            input_data.astype(np.float32)
        )

        self.interpreter.invoke()

        output = self.interpreter.get_tensor(
            self.output_details[0]['index']
        )

        return output

# import tflite_runtime.interpreter as tflite (will be used in edge devices like Raspberry Pi)