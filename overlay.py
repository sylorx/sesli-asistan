"""
Aria - Transparan Ses Dalgası Overlay
Küçük, şeffaf, sürüklenebilir, konum kaydeden ses dalgası animasyonu
"""

import tkinter as tk
import math
import threading
import time
import json
import os

KONUM_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay_konum.json")


class SesOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")

        # Pencere boyutu
        self.genislik = 200
        self.yukseklik = 60

        # Kaydedilmiş konumu yükle veya varsayılan kullan
        x, y = self._konum_yukle()

        self.root.geometry(f"{self.genislik}x{self.yukseklik}+{x}+{y}")

        # Şeffaf pencere
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.configure(bg="#0a0a0a")

        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=self.genislik, height=self.yukseklik,
            bg="#0a0a0a", highlightthickness=0
        )
        self.canvas.pack()

        # Durum
        self.mod = "bekleme"
        self.faz = 0.0
        self.calisiyor = True

        # Sürükleme değişkenleri
        self._surukleme_x = 0
        self._surukleme_y = 0

        # Mouse olayları (sürükleme için)
        self.canvas.bind("<ButtonPress-1>", self._surukleme_basla)
        self.canvas.bind("<B1-Motion>", self._surukle)
        self.canvas.bind("<ButtonRelease-1>", self._surukleme_bitir)

        # Arka plan
        self._panel_ciz()

        # Animasyon (root.after ile - thread güvenli)
        self._animasyonu_baslat()

    # ── Konum Kaydetme / Yükleme ──────────────────
    def _konum_yukle(self):
        """Son kaydedilen konumu yükle"""
        try:
            if os.path.exists(KONUM_DOSYA):
                with open(KONUM_DOSYA, 'r') as f:
                    data = json.load(f)
                    return data.get('x', None), data.get('y', None)
        except:
            pass
        # Varsayılan: sağ alt köşe
        ekran_g = self.root.winfo_screenwidth()
        ekran_y = self.root.winfo_screenheight()
        return ekran_g - self.genislik - 20, ekran_y - self.yukseklik - 80

    def _konum_kaydet(self):
        """Mevcut pencere konumunu kaydet"""
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            with open(KONUM_DOSYA, 'w') as f:
                json.dump({'x': x, 'y': y}, f)
        except:
            pass

    # ── Sürükleme ─────────────────────────────────
    def _surukleme_basla(self, event):
        self._surukleme_x = event.x
        self._surukleme_y = event.y

    def _surukle(self, event):
        x = self.root.winfo_x() + (event.x - self._surukleme_x)
        y = self.root.winfo_y() + (event.y - self._surukleme_y)
        self.root.geometry(f"+{x}+{y}")

    def _surukleme_bitir(self, event):
        self._konum_kaydet()

    # ── Genel API ─────────────────────────────────
    def dinliyor_modu(self):
        self.mod = "dinliyor"

    def konusuyor_modu(self):
        self.mod = "konuşuyor"

    def bekleme_modu(self):
        self.mod = "bekleme"

    def kapat(self):
        self.calisiyor = False
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    # ── Panel ─────────────────────────────────────
    def _panel_ciz(self):
        self.canvas.create_rectangle(
            4, 4, 196, 56,
            fill="#111111", outline="#222222", width=1
        )

    # ── Animasyon (root.after kullanarak - thread güvenli) ──
    def _animasyonu_baslat(self):
        if self.calisiyor:
            self._ciz()
            self.faz += 0.18
            self.root.after(33, self._animasyonu_baslat)  # ~30 FPS

    def _ciz(self):
        try:
            self.canvas.delete("dalga")
            self._panel_ciz()

            cx, cy = 100, 30
            n_bar = 18
            bar_w = 5
            gap = 3
            toplam_gen = n_bar * (bar_w + gap) - gap
            baslangic_x = cx - toplam_gen // 2

            if self.mod == "bekleme":
                renk = "#334466"
                for i in range(n_bar):
                    x = baslangic_x + i * (bar_w + gap)
                    yuk = 3 + math.sin(self.faz * 0.4 + i * 0.5) * 2
                    self._bar_ciz(x, cy, bar_w, yuk, renk)

            elif self.mod == "dinliyor":
                renk = "#00e676"
                parlak = "#69ff9e"
                for i in range(n_bar):
                    x = baslangic_x + i * (bar_w + gap)
                    yuk = 6 + math.sin(self.faz + i * 0.6) * 10 \
                            + math.sin(self.faz * 1.7 + i * 0.3) * 5
                    yuk = max(3, abs(yuk))
                    r = parlak if i == n_bar // 2 else renk
                    self._bar_ciz(x, cy, bar_w, yuk, r)

            elif self.mod == "konuşuyor":
                renk = "#7c4dff"
                parlak = "#b47eff"
                for i in range(n_bar):
                    x = baslangic_x + i * (bar_w + gap)
                    yuk = 8 + math.sin(self.faz * 1.4 + i * 0.5) * 12 \
                            + math.sin(self.faz * 2.1 + i * 0.9) * 6
                    yuk = max(3, abs(yuk))
                    r = parlak if abs(i - n_bar // 2) <= 1 else renk
                    self._bar_ciz(x, cy, bar_w, yuk, r)

        except tk.TclError:
            pass

    def _bar_ciz(self, x, cy, genislik, yukseklik, renk):
        y1 = cy - yukseklik / 2
        y2 = cy + yukseklik / 2
        self.canvas.create_rectangle(
            x, y1, x + genislik, y2,
            fill=renk, outline="", tags="dalga"
        )

    def baslat(self):
        self.root.mainloop()


# ── Test Çalıştırması ─────────────────────────
if __name__ == "__main__":
    overlay = SesOverlay()

    def demo():
        """Modları 3'er saniye göster, sonra bekleme modunda kal"""
        time.sleep(2)
        print("🟢 Dinliyor modu...")
        overlay.dinliyor_modu()
        time.sleep(4)
        print("🟣 Konuşuyor modu...")
        overlay.konusuyor_modu()
        time.sleep(4)
        print("🔵 Bekleme modu... (Pencereyi istediğin yere sürükle!)")
        overlay.bekleme_modu()
        # Artık kapanmıyor, bekleme modunda çalışmaya devam eder
        # Kapatmak için terminalde Ctrl+C

    threading.Thread(target=demo, daemon=True).start()
    overlay.baslat()
