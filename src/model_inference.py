from tensorflow import keras
import tensorflow as tf
import numpy as np
import cv2

class ModelInference:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.model = keras.models.load_model(self.model_path, compile=False)
    
    def process(self, frame:np.ndarray) -> np.ndarray:
        """Transform the frame before making inference."""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, (32, 32))
        frame = tf.keras.utils.img_to_array(frame)
        frame = tf.expand_dims(frame, 0)
        frame = frame / 255.0

        return frame

    def inference(self, frame: np.ndarray) -> bool:
        """Check a frame has fall event."""
        frame = self.process(frame)
        detect = self.model.predict(frame, verbose=0)[0]
        label = detect.argmax()
        # proba = max(detect)

        return label < 4

    