"""
Aria - Transparan Ses Dalgası Overlay
Küçük, şeffaf, nefes alabilen ses dalgası animasyonu
"""

import tkinter as tk
import math
import threading
import time

class SesOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")

        # Pencere boyutu ve konumu (sağ alt köşe)
        genislik  = 200
        yukseklik = 60
        ekran_g   = self.root.winfo_screenwidth()
        ekran_y   = self.root.winfo_screenheight()
        x = ekran_g - genislik - 20
        y = ekran_y - yukseklik - 50
        self.root.geometry(f"{genislik}x{yukseklik}+{x}+{y}")

        # Şeffaf pencere
        self.root.overrideredirect(True)          # Başlık çubuğu yok
        self.root.attributes("-topmost", True)    # Her zaman üstte
        self.root.attributes("-alpha", 0.85)      # %85 görünür
        self.root.configure(bg="#0a0a0a")

        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=genislik, height=yukseklik,
            bg="#0a0a0a", highlightthickness=0
        )
        self.canvas.pack()

        # Durum
        self.mod   = "bekleme"   # "bekleme" | "dinliyor" | "konuşuyor"
        self.faz   = 0.0
        self.calisiyor = True

        # Arka plan yuvarlak köşe (hafif panel)
        self._panel_ciz()

        # Animasyon döngüsü (ayrı thread)
        self.anim_thread = threading.Thread(target=self._anim_dongu, daemon=True)
        self.anim_thread.start()

    def _panel_ciz(self):
        """Yuvarlak köşeli arka plan"""
        self.canvas.create_rectangle(
            4, 4, 196, 56,
            fill="#111111", outline="#222222", width=1
        )

    # ── Genel API ────────────────────────────────────
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
        except: pass

    # ── Animasyon ────────────────────────────────────
    def _anim_dongu(self):
        fps_sure = 1 / 30
        while self.calisiyor:
            self.faz += 0.18
            try:
                self.root.after(0, self._ciz)
            except: break
            time.sleep(fps_sure)

    def _ciz(self):
        try:
            self.canvas.delete("dalga")
            self._panel_ciz()

            cx, cy = 100, 30
            n_bar  = 18
            bar_w  = 5
            gap    = 3
            toplam_gen = n_bar * (bar_w + gap) - gap
            baslangic_x = cx - toplam_gen // 2

            if self.mod == "bekleme":
                # Çok kısık, yavaş nefes efekti
                renk = "#334466"
                for i in range(n_bar):
                    x = baslangic_x + i * (bar_w + gap)
                    yuk = 3 + math.sin(self.faz * 0.4 + i * 0.5) * 2
                    self._bar_ciz(x, cy, bar_w, yuk, renk)

            elif self.mod == "dinliyor":
                # Yeşil, orta aktif dalga
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
                # Mor/mavi, hızlı ve yüksek dalga
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
        r  = min(genislik // 2, 3)
        self.canvas.create_rectangle(
            x, y1, x + genislik, y2,
            fill=renk, outline="", tags="dalga"
        )

    def baslat(self):
        self.root.mainloop()


# Test çalıştırması
if __name__ == "__main__":
    overlay = SesOverlay()
    def demo():
        time.sleep(1)
        overlay.dinliyor_modu()
        time.sleep(3)
        overlay.konusuyor_modu()
        time.sleep(3)
        overlay.bekleme_modu()
        time.sleep(2)
        overlay.kapat()
    threading.Thread(target=demo, daemon=True).start()
    overlay.baslat()
