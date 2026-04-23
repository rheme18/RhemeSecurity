import cv2
import os
import numpy as np
import ctypes
import threading
import time
import customtkinter as ctk
from PIL import Image

class RhemeSecurityUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- KAMERA VE YAPAY ZEKA AYARLARI ---
        self.cam = cv2.VideoCapture(0)
        # Yüz ve Yan Profil kütüphanelerini yüklüyoruz
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.trainer_path = "trainer.yml"
        
        # Durum Kontrolleri
        self.is_active = False
        self.is_training = False
        self.has_trainer = os.path.exists(self.trainer_path)
        if self.has_trainer:
            try: self.recognizer.read(self.trainer_path)
            except: self.has_trainer = False

        # --- UI TASARIMI (MODERN DARK) ---
        self.title("RhemeSecurity v3.4 - Ultimate")
        self.geometry("1000x800")
        ctk.set_appearance_mode("dark")

        # Header
        self.header = ctk.CTkFrame(self, height=70, fg_color="#111111")
        self.header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.header, text="🛡️ RHEME SECURITY AI", font=("Orbitron", 22, "bold"), text_color="#ff4444").pack(side="left", padx=20)

        # Ana Görüntü Paneli
        self.video_frame = ctk.CTkLabel(self, text="SİSTEM BEKLEMEDE", fg_color="black", corner_radius=20)
        self.video_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Kontrol Paneli
        self.control_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.control_panel.pack(fill="x", pady=20)

        self.btn_train = ctk.CTkButton(self.control_panel, text="👤 PATRONU (BENİ) TANIT", fg_color="#3498db", hover_color="#2980b9", width=250, height=50, font=("Segoe UI", 14, "bold"), command=self.start_training_logic)
        self.btn_train.pack(side="left", padx=50)

        self.btn_toggle = ctk.CTkButton(self.control_panel, text="🛡️ KORUMAYI BAŞLAT", fg_color="#2ecc71", hover_color="#27ae60", width=250, height=50, font=("Segoe UI", 14, "bold"), command=self.toggle_security)
        self.btn_toggle.pack(side="right", padx=50)

        self.p_bar = ctk.CTkProgressBar(self, width=800, height=15, progress_color="#3498db")
        self.p_bar.set(0)
        self.p_bar.pack(pady=10)

        self.status_lbl = ctk.CTkLabel(self, text="Durum: Hazır", text_color="gray")
        self.status_lbl.pack()

        # Ana döngüyü başlat
        self.update_loop()

    def start_training_logic(self):
        if self.is_active: self.toggle_security()
        self.is_training = True
        self.btn_train.configure(state="disabled", text="KAYIT YAPILIYOR (50 KARE)...")
        self.status_lbl.configure(text="Durum: Yüzünüzü sağa-sola yavaşça çevirin...", text_color="#3498db")
        threading.Thread(target=self.train_process, daemon=True).start()

    def train_process(self):
        try:
            # Yetki sorununu aşmak için mutlak yol kullanımı
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data", "patron")
            if not os.path.exists(data_dir): os.makedirs(data_dir, exist_ok=True)
            
            count, samples, ids = 0, [], []
            while count < 50:
                ret, frame = self.cam.read()
                if not ret: continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Hem ön hem yan profil taraması
                f_faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
                p_faces = self.profile_cascade.detectMultiScale(gray, 1.2, 5)
                all_faces = list(f_faces) + list(p_faces)

                for (x, y, w, h) in all_faces:
                    count += 1
                    face_img = gray[y:y+h, x:x+w]
                    samples.append(face_img)
                    ids.append(1)
                    self.p_bar.set(count / 50)
                    cv2.imwrite(os.path.join(data_dir, f"u.{count}.jpg"), face_img)
                    time.sleep(0.05)
                if count >= 50: break

            if len(samples) > 0:
                self.recognizer.train(samples, np.array(ids))
                self.recognizer.write(self.trainer_path)
                self.has_trainer = True
                print("[+] Eğitim tamamlandı.")
            
            self.is_training = False
            self.btn_train.configure(state="normal", text="TANITMA TAMAM ✅", fg_color="green")
            self.status_lbl.configure(text="Durum: Tanıtma Başarılı! Korumayı başlatabilirsiniz.", text_color="green")
        except Exception as e:
            print(f"Hata: {e}")
            self.is_training = False
            self.btn_train.configure(state="normal", text="HATA ❌", fg_color="red")

    def toggle_security(self):
        if not self.has_trainer:
            self.status_lbl.configure(text="Önce kendini tanıt Patron!", text_color="red")
            return
        self.is_active = not self.is_active
        self.btn_toggle.configure(text="KORUMA AKTİF 🚨" if self.is_active else "🛡️ KORUMAYI BAŞLAT", 
                                  fg_color="#e74c3c" if self.is_active else "#2ecc71")
        self.status_lbl.configure(text="SİSTEM NÖBETTE!" if self.is_active else "Sistem Beklemede.")

    def update_loop(self):
        ret, frame = self.cam.read()
        if ret:
            frame = cv2.flip(frame, 1)
            if self.is_active and not self.is_training:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Analiz yaparken hem düz hem yan profili tara
                f_faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
                p_faces = self.profile_cascade.detectMultiScale(gray, 1.2, 5)
                detects = list(f_faces) + list(p_faces)

                for (x, y, w, h) in detects:
                    id, conf = self.recognizer.predict(gray[y:y+h, x:x+w])
                    # Hassasiyet: 80 üstü yabancıdır
                    label = "Patron" if conf < 80 else "Yabanci"
                    color = (0, 255, 0) if label == "Patron" else (0, 0, 255)
                    
                    if label == "Yabanci":
                        # WINDOWS KİLİTLEME PROTOKOLÜ
                        ctypes.windll.user32.LockWorkStation()
                        self.is_active = False
                        self.btn_toggle.configure(text="🛡️ KORUMAYI BAŞLAT", fg_color="#2ecc71")
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, f"{label} ({int(conf)})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img_tk = ctk.CTkImage(img, size=(850, 550))
            self.video_frame.configure(image=img_tk, text="")

        self.after(10, self.update_loop)

if __name__ == "__main__":
    app = RhemeSecurityUI()
    app.mainloop()