import cv2
import os
import numpy as np
import ctypes
import requests
import datetime

class RhemeDetector:
    def __init__(self):
        self.cam = cv2.VideoCapture(0)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.trainer_path = "core/trainer.yml"
        self.has_trainer = os.path.exists(self.trainer_path)
        if self.has_trainer:
            self.recognizer.read(self.trainer_path)

    def get_frame(self):
        ret, frame = self.cam.read()
        return cv2.flip(frame, 1) if ret else None

    def train_patron(self, progress_callback):
        if not os.path.exists("data/patron"): os.makedirs("data/patron")
        count, face_samples, ids = 0, [], []
        
        while count < 30:
            frame = self.get_frame()
            if frame is None: continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                count += 1
                face_img = gray[y:y+h, x:x+w]
                face_samples.append(face_img)
                ids.append(1)
                progress_callback(count / 30)
                cv2.imwrite(f"data/patron/user.{count}.jpg", face_img)
        
        self.recognizer.train(face_samples, np.array(ids))
        self.recognizer.write(self.trainer_path)
        self.has_trainer = True

    def process_security(self, frame, lock_enabled, webhook_url):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        alert_info = []
        
        for (x, y, w, h) in faces:
            label = "Yabanci"
            if self.has_trainer:
                id, conf = self.recognizer.predict(gray[y:y+h, x:x+w])
                if conf < 60: label = "Patron"
            
            alert_info.append((x, y, w, h, label))
            if label == "Yabanci":
                path = self.capture_intruder(frame)
                if webhook_url: self.send_to_discord(webhook_url, path)
                if lock_enabled: self.lock_pc()
        return alert_info

    def capture_intruder(self, frame):
        if not os.path.exists("logs"): os.makedirs("logs")
        fn = f"logs/ALARM_{datetime.datetime.now().strftime('%H%M%S')}.jpg"
        cv2.imwrite(fn, frame)
        return fn

    def send_to_discord(self, url, path):
        try:
            with open(path, 'rb') as f:
                requests.post(url, data={"content": "🚨 **ALARM:** İzinsiz giriş!"}, files={'file': f})
        except: pass

    def lock_pc(self):
        ctypes.windll.user32.LockWorkStation()

    def __del__(self):
        self.cam.release()