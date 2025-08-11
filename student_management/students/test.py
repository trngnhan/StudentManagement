import dlib
import numpy as np
import cv2
import streamlit as st
import matplotlib.pyplot as plt

class LandmarkExtractor:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    
    def extract_landmarks(self, image):
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            st.write(f"Grayscale image shape: {gray.shape}, dtype: {gray.dtype}")
            if gray.dtype != 'uint8':
                gray = gray.astype('uint8')
                st.write(f"Converted grayscale image dtype to uint8")
            faces = self.detector(gray)
            st.write(f"Number of faces detected: {len(faces)}")
            if len(faces) == 0:
                return None
            for face in faces:
                landmarks = self.predictor(image=gray, box=face)
                return np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in range(68)])
        except Exception as e:
            st.error(f"Error in extract_landmarks: {e}")
        return None
    
    def visualize_landmarks(self, image, landmarks):
        if landmarks is None:
            print("No landmarks to visualize.")
            return
        plt.figure(figsize=(8, 8))
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.scatter(landmarks[:, 0], landmarks[:, 1], s=20, marker='.', c='c')
        plt.show()


        