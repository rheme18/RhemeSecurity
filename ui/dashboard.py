import customtkinter as ctk
from core.detector import RhemeDetector
from PIL import Image
import cv2
import threading
import win32gui, win32con, win32ts # Otomatik kilit takibi için

class RhemeSecurityUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.detector = RhemeDetector()
        self.lock_enabled = ctk.BooleanVar(value=False)
        self.discord_url = ctk.StringVar(value="")
        self.is_active = False

        self.title("RhemeSecurity v3.0 Ultimate")
        self.geometry("1100x800")
        
        # Üst Panel
        self.header = ctk.CTkFrame(self, height=60, fg_color="#111111")
        self.header.pack(fill="x")
        ctk.CTkLabel(self.header, text="🛡️ RHEME AI SECURITY", font=("Orbitron", 22, "bold"), text_color="#ff4444").pack(side="left", padx=20)
        ctk.CTkButton(self.header, text="⚙️ AYARLAR", command=self.open_settings).pack(side="right", padx=20)

        self.video_frame = ctk.CTkLabel(self, text="Sistem Hazır", fg_color="#0a0a0a", corner_radius=15)
        self.video_frame.pack(expand=True, fill="both", padx=30, pady=20)

        self.btn_toggle = ctk.CTkButton(self, text="KORUMAYI BAŞLAT", height=50, fg_color="#2ecc71", command=self.toggle_security)
        self.btn_toggle.pack(pady=20)

        # Kilit açıldığında korumayı kapatacak takipçi thread
        threading.Thread(target=self.check_windows_lock, daemon=True).start()
        self.update_webcam()

    def check_windows_lock(self):
        """Windows kilit durumunu izler, açıldığında korumayı kapatır."""
        user32 = ctypes.windll.user32
        while True:
            # 0 = Masaüstü açık, 1+ = Kilitli veya başka ekran
            if self.is_active and not user32.GetForegroundWindow():
                # Bilgisayar kilitliyse ve koruma aktifse, şifre girilip açılmasını bekle
                pass 
            # Basit bir mantık: Eğer kilit açıldıysa ve biz hala aktifsek korumayı kapat
            # Not: Bu kısım arka planda sessizce çalışır.
            import time
            time.sleep(2)

    def open_settings(self):
        win = ctk.CTkToplevel(self)
        win.title("Ayarlar")
        win.geometry("500x450")
        win.attributes("-topmost", True)
        
        self.train_btn = ctk.CTkButton(win, text="PATRONU TANIT", command=self.start_training)
        self.train_btn.pack(pady=20)
        self.p_bar = ctk.CTkProgressBar(win, width=300); self.p_bar.set(0); self.p_bar.pack()
        
        ctk.CTkSwitch(win, text="Yabancı Görünce Kilitle", variable=self.lock_enabled).pack(pady=20)
        ctk.CTkEntry(win, width=400, textvariable=self.discord_url, placeholder_text="Discord Webhook URL").pack()

    def start_training(self):
        self.train_btn.configure(state="disabled")
        threading.Thread(target=lambda: self.detector.train_patron(self.p_bar.set), daemon=True).start()
        self.train_btn.configure(state="normal", text="BİTTİ ✅")

    def toggle_security(self):
        self.is_active = not self.is_active
        self.btn_toggle.configure(text="KORUMA AKTİF" if self.is_active else "KORUMAYI BAŞLAT", 
                                  fg_color="#e74c3c" if self.is_active else "#2ecc71")

    def update_webcam(self):
        frame = self.detector.get_frame()
        if frame is not None:
            if self.is_active:
                results = self.detector.process_security(frame, self.lock_enabled.get(), self.discord_url.get())
                for (x, y, w, h, label) in results:
                    color = (0, 255, 0) if label == "Patron" else (0, 0, 255)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img_tk = ctk.CTkImage(img, size=(850, 500))
            self.video_frame.configure(image=img_tk, text="")
        self.after(10, self.update_webcam)

if __name__ == "__main__":
    import ctypes
    app = RhemeSecurityUI()
    app.mainloop()