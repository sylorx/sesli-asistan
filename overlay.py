"""
Aria Pro - Gelişmiş Ses Dalga Paneli (V2)
Sürüklenebilir, Konum Kaydeden, Dairesel Dalga ve Sistem Bilgili
"""

import tkinter as tk
from tkinter import messagebox
import math
import threading
import time
import json
import os
import random
import psutil
from datetime import datetime

KONUM_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay_konum_pro.json")

class SesOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Aria Overlay")

        # --- YAPILANDIRMA ---
        self.genislik = 240
        self.yukseklik = 140
        self.mini_mod = False
        self.sessiz_mod = False
        
        # Konum Yükle
        x, y = self._konum_yukle()
        self.root.geometry(f"{self.genislik}x{self.yukseklik}+{x}+{y}")
        
        # Pencere Özellikleri
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.90)
        self.root.configure(bg="#050505")
        
        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=self.genislik, height=self.yukseklik,
            bg="#050505", highlightthickness=0
        )
        self.canvas.pack()

        # --- DURUM VE ANA DEĞİŞKENLER ---
        self.mod = "bekleme" # bekleme, dinliyor, konuşuyor
        self.faz = 0.0
        self.faz_hiz = 0.1
        self.calisiyor = True
        self.partikuller = []
        self.son_komut = ""
        self.aktif_model = "llama3"
        
        # Renk Paleti (Geçişler İçin)
        self.renkler = {
            "bekleme":   {"ana": "#1a237e", "p": "#3f51b5", "bg": "#050505"},
            "dinliyor":  {"ana": "#00e676", "p": "#69ff9e", "bg": "#001a0a"},
            "konuşuyor": {"ana": "#d500f9", "p": "#ea80fc", "bg": "#1a001a"}
        }
        self.mevcut_ana_renk = self.renkler["bekleme"]["ana"]

        # --- MOUSE ETKİLEŞİMİ ---
        self._surukleme_x = 0
        self._surukleme_y = 0
        self.canvas.bind("<ButtonPress-1>", self._surukleme_basla)
        self.canvas.bind("<B1-Motion>", self._surukle)
        self.canvas.bind("<ButtonRelease-1>", self._surukleme_bitir)
        self.canvas.bind("<Double-Button-1>", self.toggle_mini)
        
        # Sağ Tık Menüsü
        self.menu = tk.Menu(self.root, tearoff=0, bg="#111", fg="white", activebackground="#333")
        self.menu.add_command(label="Mini Mod / Normal Mod", command=self.toggle_mini)
        self.menu.add_command(label="Sessiz Modu Aç/Kapat", command=self.toggle_sessiz)
        self.menu.add_separator()
        self.menu.add_command(label="Konumu Sıfırla", command=self._konum_sifirla)
        self.menu.add_command(label="Kapat", command=self.kapat)
        self.canvas.bind("<Button-3>", self._menu_goster)

        # Başlat
        self._panel_hazirla()
        self._animasyonu_baslat()

    # --- SİSTEM API ---
    def set_model(self, model_adi):
        self.aktif_model = model_adi

    def toggle_sessiz(self):
        self.sessiz_mod = not self.sessiz_mod
        m = "Açıldı" if self.sessiz_mod else "Kapatıldı"
        self.son_komut = f"Sessiz Mod {m}"

    def toggle_mini(self, event=None):
        self.mini_mod = not self.mini_mod
        if self.mini_mod:
            self.root.geometry(f"{160}x{40}")
            self.canvas.config(width=160, height=40)
        else:
            self.root.geometry(f"{200}x{60}")
            self.canvas.config(width=200, height=60)
    # --- GENEL API ---
    def dinliyor_modu(self): self.mod = "dinliyor"; self.faz_hiz = 0.2
    def konusuyor_modu(self): self.mod = "konuşuyor"; self.faz_hiz = 0.3
    def bekleme_modu(self, son_komut=None):
        self.mod = "bekleme"; self.faz_hiz = 0.05
        if son_komut: self.son_komut = son_komut

    def gorev_modu(self, metin, renk="#ff9800"):
        """Örn: Program açarken sarı renkte 'AÇILIYOR' yazar"""
        self.mod = "gorev"
        self.gorev_metni = metin
        self.gorev_renk = renk
        self.faz_hiz = 0.4
        # 2.5 saniye sonra bekleme moduna dön
        threading.Timer(2.5, self.bekleme_modu).start()

    def kapat(self):
        self.calisiyor = False
        self.root.quit()
    def _panel_hazirla(self):
        """Metin ve temel UI elemanları"""
        self.canvas.delete("ui")
        if not self.mini_mod:
            # Köşe Etiketleri
            self.canvas.create_text(5, 5, text="ARIA", fill="#444", font=("Arial", 6, "bold"), anchor="nw", tags="ui")

    def _animasyonu_baslat(self):
        if self.calisiyor:
            self._ciz()
            self.faz += self.faz_hiz
            self.root.after(30, self._animasyonu_baslat)

    def _ciz(self):
        self.canvas.delete("dalga", "part", "aura")
        w, h = (160, 40) if self.mini_mod else (200, 60)
        cx, cy = w // 2, h // 2
        
        # Moda göre ayarlar
        if self.mod == "dinliyor":
            renk = self.renkler["dinliyor"]["ana"]
            h_mult = 10; radius = 17; n_bars = 36
        elif self.mod == "konuşuyor":
            renk = self.renkler["konuşuyor"]["ana"]
            h_mult = 14; radius = 17; n_bars = 36
        elif self.mod == "gorev":
            renk = self.gorev_renk
            h_mult = 18; radius = 17; n_bars = 40
        else: # bekleme
            renk = self.renkler["bekleme"]["ana"]
            h_mult = 3; radius = 17; n_bars = 30

        # Renk Fade
        self.mevcut_ana_renk = self._renk_fade(self.mevcut_ana_renk, renk)
        
        for i in range(n_bars):
            aci = math.radians((i / n_bars) * 360)
            v = math.sin(self.faz * (3 if self.mod == "gorev" else 2) + i * 0.6) * h_mult + random.random() * 2
            v = max(1.2, abs(v))
            
            x1 = cx + math.cos(aci) * radius
            y1 = cy + math.sin(aci) * radius
            x2 = cx + math.cos(aci) * (radius + v)
            y2 = cy + math.sin(aci) * (radius + v)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=self.mevcut_ana_renk, width=2, capstyle="round", tags="dalga")

        self._bilgi_ciz(cx, cy, w, h)

    def _hsl_to_hex(self, h, s, l):
        """Basit HSL to Hex çevirici"""
        h /= 360; s /= 100; l /= 100
        if s == 0: r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))

    def _bilgi_ciz(self, cx, cy, w, h):
        if self.mini_mod: return

        # Saat (Sağ Üst Köşeye TAM YASLA)
        simdi = datetime.now().strftime("%H:%M")
        self.canvas.create_text(w-2, 2, text=simdi, fill="#444", font=("Arial", 6), anchor="ne", tags="dalga")
        
        # 1. DURUM YAZISI (DAİRE İÇİ)
        txt = ""
        if self.mod == "dinliyor": txt = "DİNLE"
        elif self.mod == "konuşuyor": txt = "ARIA"
        elif self.mod == "gorev": txt = self.gorev_metni

        if txt:
            self.canvas.create_text(cx, cy, text=txt, fill="white", font=("Arial", 5, "bold"), tags="dalga")
        
        # 2. SON KOMUT
        if self.son_komut and self.mod != "gorev":
            kisa = self.son_komut[:24].upper() + (".." if len(self.son_komut) > 24 else "")
            self.canvas.create_text(cx, 6, text=kisa, fill="#555", font=("Arial", 5, "italic"), tags="dalga")

        # 3. AKTİF MODEL (SOL ALT KÖŞEYE TAM YASLA)
        m_ad = self.aktif_model.split(":")[0] 
        self.canvas.create_text(2, h-2, text=m_ad, fill="#444", font=("Arial", 5), anchor="sw", tags="dalga")

        # 4. SİSTEM BARI (SAĞ ALT KÖŞEYE TAM YASLA)
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        # CPU & RAM 
        self.canvas.create_rectangle(w-32, h-9, w-2, h-8, fill="#111", outline="", tags="dalga")
        self.canvas.create_rectangle(w-32, h-9, w-32 + (cpu*0.3), h-8, fill="#00bcd4", outline="", tags="dalga")
        self.canvas.create_rectangle(w-32, h-6, w-2, h-5, fill="#111", outline="", tags="dalga")
        self.canvas.create_rectangle(w-32, h-6, w-32 + (ram*0.3), h-5, fill="#ff9800", outline="", tags="dalga")

    # --- YARDIMCI FONKSİYONLAR ---
    def _renk_fade(self, mevcut, hedef):
        """İki hex rengi arasında geçiş yapar"""
        try:
            r1, g1, b1 = int(mevcut[1:3], 16), int(mevcut[3:5], 16), int(mevcut[5:7], 16)
            r2, g2, b2 = int(hedef[1:3], 16), int(hedef[3:5], 16), int(hedef[5:7], 16)
            s = 10 # hız
            nr = r1 + (r2-r1)//s
            ng = g1 + (g2-g1)//s
            nb = b1 + (b2-b1)//s
            return f'#{nr:02x}{ng:02x}{nb:02x}'
        except: return hedef

    def _menu_goster(self, event):
        self.menu.post(event.x_root, event.y_root)

    def _konum_yukle(self):
        try:
            if os.path.exists(KONUM_DOSYA):
                with open(KONUM_DOSYA, 'r') as f:
                    d = json.load(f)
                    return d['x'], d['y']
        except: pass
        return self.root.winfo_screenwidth()-260, self.root.winfo_screenheight()-200

    def _konum_kaydet(self):
        try:
            with open(KONUM_DOSYA, 'w') as f:
                json.dump({'x': self.root.winfo_x(), 'y': self.root.winfo_y()}, f)
        except: pass

    def _konum_sifirla(self):
        self.root.geometry(f"+{self.root.winfo_screenwidth()-260}+{self.root.winfo_screenheight()-200}")
        self._konum_kaydet()

    def _surukleme_basla(self, e):
        self._surukleme_x, self._surukleme_y = e.x, e.y

    def _surukle(self, e):
        x = self.root.winfo_x() + (e.x - self._surukleme_x)
        y = self.root.winfo_y() + (e.y - self._surukleme_y)
        self.root.geometry(f"+{x}+{y}")

    def _surukleme_bitir(self, e):
        self._konum_kaydet()

    def dinliyor_modu(self): self.mod = "dinliyor"; self.faz_hiz = 0.2
    def konusuyor_modu(self): self.mod = "konuşuyor"; self.faz_hiz = 0.3
    def bekleme_modu(self, son_komut=None):
        self.mod = "bekleme"; self.faz_hiz = 0.05
        if son_komut: self.son_komut = son_komut

    def kapat(self):
        self.calisiyor = False
        self.root.quit()

    def baslat(self): self.root.mainloop()

if __name__ == "__main__":
    o = SesOverlay()
    threading.Thread(target=lambda: (time.sleep(2), o.dinliyor_modu(), time.sleep(3), o.konusuyor_modu(), time.sleep(3), o.bekleme_modu("Test Tamamlandı")), daemon=True).start()
    o.baslat()
