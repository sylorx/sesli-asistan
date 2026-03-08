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
            self.root.geometry(f"{160}x{80}")
            self.canvas.config(width=160, height=80)
        else:
            self.root.geometry(f"{240}x{140}")
            self.canvas.config(width=240, height=140)

    # --- UI ÇİZİM ---
    def _panel_hazirla(self):
        """Metin ve temel UI elemanları"""
        self.canvas.delete("ui")
        # Saat ve Model Bilgisi (Normal Modda)
        if not self.mini_mod:
            self.canvas.create_text(10, 15, text="ARIA PRO", fill="#555", font=("Arial", 7, "bold"), anchor="w", tags="ui")

    def _animasyonu_baslat(self):
        if self.calisiyor:
            self._ciz()
            self.faz += self.faz_hiz
            self.root.after(30, self._animasyonu_baslat)

    def _ciz(self):
        self.canvas.delete("dalga", "part")
        w, h = (160, 80) if self.mini_mod else (240, 140)
        cx, cy = w // 2, h // 2
        
        # 1. Renk Fade Efekti
        hedef_renk = self.renkler[self.mod]["ana"]
        self.mevcut_ana_renk = self._renk_fade(self.mevcut_ana_renk, hedef_renk)
        
        # 2. Dairesel Ses Dalgası (Circular Wave)
        n_bars = 40
        radius = 25 if self.mini_mod else 35
        
        for i in range(n_bars):
            aci = math.radians((i / n_bars) * 360)
            
            # Dalga yüksekliği moda göre değişir
            if self.mod == "dinliyor":
                v = math.sin(self.faz*2 + i*0.5) * 15 + random.random()*5
            elif self.mod == "konuşuyor":
                v = math.sin(self.faz*3 + i*0.8) * 25 + random.random()*10
            else: # bekleme
                v = math.sin(self.faz*0.5 + i*0.3) * 3
            
            v = max(2, abs(v))
            x1 = cx + math.cos(aci) * radius
            y1 = cy + math.sin(aci) * radius
            x2 = cx + math.cos(aci) * (radius + v)
            y2 = cy + math.sin(aci) * (radius + v)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=self.mevcut_ana_renk, width=3, capstyle="round", tags="dalga")
            
            # 3. Partikül Efekti (Barların Ucundan)
            if (self.mod != "bekleme" or random.random() > 0.95) and i % 4 == 0:
                if len(self.partikuller) < 50:
                    self.partikuller.append({
                        "x": x2, "y": y2, 
                        "vx": math.cos(aci) * (random.random()*2), 
                        "vy": math.sin(aci) * (random.random()*2),
                        "life": 1.0, "color": self.renkler[self.mod]["p"]
                    })
        
        # Partikülleri güncelle ve çiz
        for p in self.partikuller[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.05
            if p["life"] <= 0:
                self.partikuller.remove(p)
            else:
                s = int(3 * p["life"])
                self.canvas.create_oval(p["x"]-s, p["y"]-s, p["x"]+s, p["y"]+s, fill=p["color"], outline="", tags="part")

        # 4. Bilgi Yazıları
        self._bilgi_ciz(cx, cy, w, h)

    def _bilgi_ciz(self, cx, cy, w, h):
        if self.mini_mod:
             self.canvas.create_text(cx, cy, text=self.mod.upper(), fill="white", font=("Arial", 6, "bold"), tags="dalga")
             return

        # Saat (Sağ Üst)
        simdi = datetime.now().strftime("%H:%M")
        self.canvas.create_text(w-10, 15, text=simdi, fill="#888", font=("Arial", 8), anchor="e", tags="dalga")
        
        # Durum Yazısı (Merkez)
        txt = "ARIA DİNLİYOR" if self.mod == "dinliyor" else "ARIA KONUŞUYOR" if self.mod == "konuşuyor" else "Aria Beklemede"
        self.canvas.create_text(cx, cy, text=txt, fill="white", font=("Arial", 8, "bold"), tags="dalga")
        
        # Son Komut (Alt)
        if self.son_komut:
            kisa = self.son_komut[:35] + ("..." if len(self.son_komut) > 35 else "")
            self.canvas.create_text(cx, h-25, text=kisa, fill="#aaa", font=("Arial", 7, "italic"), tags="dalga")

        # Model İsmi
        self.canvas.create_text(10, h-15, text=f"Model: {self.aktif_model}", fill="#555", font=("Arial", 6), anchor="w", tags="dalga")

        # CPU / RAM Bar (Küçük çubuklar)
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        # CPU Bar
        self.canvas.create_rectangle(w-60, h-15, w-10, h-12, fill="#222", outline="", tags="dalga")
        self.canvas.create_rectangle(w-60, h-15, w-60 + (cpu*0.5), h-12, fill="#00bcd4", outline="", tags="dalga")
        # RAM Bar
        self.canvas.create_rectangle(w-60, h-8, w-10, h-5, fill="#222", outline="", tags="dalga")
        self.canvas.create_rectangle(w-60, h-8, w-60 + (ram*0.5), h-5, fill="#ff9800", outline="", tags="dalga")

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
