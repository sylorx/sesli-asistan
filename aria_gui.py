import sys
import threading
import time
import os
import json
import winreg

try:
    import keyboard
except ImportError:
    os.system(f'"{sys.executable}" -m pip install keyboard')
    import keyboard

try:
    import customtkinter as ctk
    from CTkColorPicker import AskColor
    from PIL import Image
except ImportError:
    print("Kütüphaneler yükleniyor (CustomTkinter, CTkColorPicker, Pillow)...")
    os.system(f'"{sys.executable}" -m pip install customtkinter CTkColorPicker Pillow')
    import customtkinter as ctk
    from CTkColorPicker import AskColor
    from PIL import Image

from sesli_asistan import SesliAsistan, ASISTAN_ADI

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PrintRedirector:
    def __init__(self, ui_instance):
        self.ui = ui_instance
        self.buffer = ""

    def write(self, s):
        self.buffer += str(s)
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            for line in lines[:-1]:
                if line.strip():
                    # Thread güvenliği için GUI'ye gönder
                    self.ui.app.after(10, self.ui.handle_log, line.strip())
            self.buffer = lines[-1]

    def flush(self):
        pass

class AriaGUI:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria_config.json")
        self.load_config()
        
        self.app = ctk.CTk()
        self.app.title(f"{ASISTAN_ADI} - Akıllı Sesli Asistan Kontrol Paneli")
        
        # Konum ve Boyut Hatırlama (Pencereleri sıfırlanmaktan kurtar)
        w = self.config.get("width", 1000)
        h = self.config.get("height", 650)
        x = self.config.get("pos_x", None)
        y = self.config.get("pos_y", None)
        
        if x is not None and y is not None:
            self.app.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self.app.geometry(f"{w}x{h}")
            
        self.is_ui_visible = True
        self.current_hotkey = self.config.get("toggle_hotkey", "ctrl+alt+a")
        
        # Kısayol Tuşunu Kaydet
        try:
            keyboard.add_hotkey(self.current_hotkey, self.on_hotkey)
        except Exception as e:
            print(f"Kısayol bağlanamadı: {e}")
            
        # Önceden seçili temayı yükle
        ctk.set_appearance_mode(self.config.get("theme", "Dark"))
        
        # Arayüze Pürüzsüz Fade-In (Yumuşak Giriş) Animasyonu
        self.app.attributes("-alpha", 0.0)
        
        # Terminal Çıktılarını UI Yönlendirmesi
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = PrintRedirector(self)
        sys.stderr = PrintRedirector(self)

        self.setup_ui()
        
        # Start Fade In
        self.app.after(50, self.fade_in)
        
        # Arka plan resmi varsa yükle
        bg_path = self.config.get("bg_image", None)
        if bg_path: self.apply_bg(bg_path)
        
        self.attached_image = None
        
        self.asistan = None
        self.asistan_thread = threading.Thread(target=self.start_asistan, daemon=True)
        self.asistan_thread.start()

    def fade_in(self):
        c_alpha = self.app.attributes("-alpha")
        if c_alpha < 1.0:
            self.app.attributes("-alpha", min(1.0, c_alpha + 0.05))
            self.app.after(15, self.fade_in)

    def start_asistan(self):
        self.add_system_message("Sistem başlatılıyor, mikrofon kalibre ediliyor...")
        # COM init for Windows threading
        try:
            import comtypes
            comtypes.CoInitialize()
        except: pass
        
        self.asistan = SesliAsistan()
        # Başladıktan sonra ayar menülerini senkronize et
        self.app.after(1000, self.sync_settings)
        # Ana asistan sonsuz döngüsüne gir
        self.asistan.calistir() 

    def sync_settings(self):
        """Asistan arka planda yüklendiğinde modelleri ve dili ayarlar paneline çek."""
        if self.asistan:
            modeller = getattr(self.asistan, 'mevcut_ollama_modeller', [])
            if modeller:
                self.model_var.configure(values=modeller)
                self.model_var.set(self.asistan.model)
            else:
                self.model_var.set("(Ollama Model Yok)")
            self.dil_var.set("Türkçe" if self.asistan.dil == "tr" else "English")

    def handle_log(self, text):
        """Standard Print çıktılarını ayrıştırıp Renkli Chat Ekranına dök"""
        if not text: return
        
        # ── Tüm ham logları Geliştirici (Dev) paneline yansıt ──
        if hasattr(self, 'dev_textbox'):
            self.dev_textbox.configure(state="normal")
            self.dev_textbox.insert("end", text + "\n")
            self.dev_textbox.see("end")
            self.dev_textbox.configure(state="disabled")

        if "👤 Sen:" in text:
            msg = text.replace("👤 Sen:", "").strip()
            self.add_chat_bubble(msg, sender="user")
        elif f"🔊 {ASISTAN_ADI}:" in text:
            msg = text.replace(f"🔊 {ASISTAN_ADI}:", "").strip()
            self.add_chat_bubble(msg, sender="aria")
            self.status_label.configure(text=f"Durum: {ASISTAN_ADI} Konuşuyor...", text_color="#10eb44")
            self.stop_animation()
        elif "🎤 Dinliyorum..." in text:
            self.status_label.configure(text="Durum: Sizi Dinliyor...", text_color="#f1c40f")
            self.stop_animation()
        elif "⚙️ İşleniyor..." in text or "düşünüyor..." in text:
            self.status_label.configure(text="Durum: Yapay Zeka Düşünüyor...", text_color="#3498db")
            self.start_animation()
        elif "Uyku moduna" in text or "sizi duyamadım" in text:
            self.status_label.configure(text="Durum: Uyku Modunda (Arka plan dinleme)", text_color="#aaaaaa")
            self.stop_animation()
        elif "🔑 Şifre:" in text:
            self.add_chat_bubble(text, sender="system")
            self.stop_animation()
        else:
            # Diğer tüm önemsiz/sistem stringleri
            if "hata" in text.lower() or "error" in text.lower() or "kalibrasyonu tamamlandı" in text:
                self.add_system_message(text)

    def start_animation(self):
        if not getattr(self, '_anim_running', False):
            self.ai_progress.start()
            self._anim_running = True

    def stop_animation(self):
        if getattr(self, '_anim_running', False):
            self.ai_progress.stop()
            self.ai_progress.set(0)
            self._anim_running = False


    def add_system_message(self, text):
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.insert("end", f"\n🛠️ [SİSTEM]: {text}\n", "sistem")
        self.chat_textbox.configure(state="disabled")
        self.chat_textbox.see("end")

    def add_chat_bubble(self, text, sender):
        self.chat_textbox.configure(state="normal")
        if sender == "user":
            self.chat_textbox.insert("end", f"\n👤 SİZ:\n{text}\n", "user")
        elif sender == "aria":
            self.chat_textbox.insert("end", f"\n✨ {ASISTAN_ADI}:\n{text}\n", "aria")
        else:
            self.chat_textbox.insert("end", f"\n{text}\n", "system")
        self.chat_textbox.configure(state="disabled")
        self.chat_textbox.see("end")

    def setup_ui(self):
        # Ana Grid
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_columnconfigure(0, weight=0, minsize=260) # Sol menü genişliği statik, sarsılma yapmaz
        self.app.grid_rowconfigure(0, weight=1)

        # ── SOL MENÜ (Sidebar) ──
        self.sidebar = ctk.CTkFrame(self.app, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        # UI Marka / Logo
        self.logo_label = ctk.CTkLabel(self.sidebar, text=f"{ASISTAN_ADI} AI", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Status göstergesi (Sabit Genişlik: Taşmaları Önler)
        self.status_label = ctk.CTkLabel(self.sidebar, text="Durum: Başlangıç...", text_color="#aaaaaa", font=ctk.CTkFont(size=13, weight="normal"), width=220, wraplength=210)
        self.status_label.grid(row=1, column=0, padx=20, pady=5)
        
        # Animasyonlu Progress Bar (İşlem animasyonu)
        self.ai_progress = ctk.CTkProgressBar(self.sidebar, mode="indeterminate", height=6, corner_radius=3)
        self.ai_progress.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.ai_progress.set(0) # Başlangıçta inaktif göster

        # SOHBET Butonu
        self.btn_chat = ctk.CTkButton(self.sidebar, text="💬  Canlı Sohbet Merkezi", height=40, font=ctk.CTkFont(size=14), command=lambda: self.tab_view.set("Sohbet Merkezi"))
        self.btn_chat.grid(row=3, column=0, padx=20, pady=10)

        # AYARLAR Butonu
        self.btn_settings = ctk.CTkButton(self.sidebar, text="⚙️  Gelişmiş Ayarlar", height=40, font=ctk.CTkFont(size=14), fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=lambda: self.tab_view.set("Ayarlar"))
        self.btn_settings.grid(row=4, column=0, padx=20, pady=10)
        
        # UI Teması Seçici
        self.sidebar_theme_label = ctk.CTkLabel(self.sidebar, text="Görünüm Modu:", anchor="w")
        self.sidebar_theme_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.theme_btn = ctk.CTkOptionMenu(self.sidebar, values=["Dark", "Light", "System"], command=self.change_theme)
        self.theme_btn.grid(row=7, column=0, padx=20, pady=(10, 20))

        # ── SAĞ ALAN (Tab Gösterimi) ──
        self.tab_view = ctk.CTkTabview(self.app, corner_radius=15)
        self.tab_view.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        
        self.tab_view.add("Sohbet Merkezi")
        self.tab_view.add("Ayarlar")
        self.tab_view.add("Geliştirici")
        self.tab_view.set("Sohbet Merkezi")

        self.setup_chat_tab()
        self.setup_settings_tab()
        self.setup_dev_tab()

    def change_theme(self, choice):
        ctk.set_appearance_mode(choice)

    def setup_chat_tab(self):
        tab = self.tab_view.tab("Sohbet Merkezi")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.chat_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=15), wrap="word", corner_radius=10)
        self.chat_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        
        # TKinter Tag konfigürasyonu (Metin renklendirme)
        text_widget = self.chat_textbox._textbox
        text_widget.tag_config("user", foreground="#3498db", font=("Consolas", 14, "bold"))
        text_widget.tag_config("aria", foreground="#2ecc71", font=("Consolas", 14, "normal"))
        text_widget.tag_config("sistem", foreground="#e67e22", font=("Consolas", 12, "italic"))
        
        self.chat_textbox.configure(state="disabled")

        # ── Kullanıcı Manuel Metin Girişi ──
        self.chat_input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.chat_input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.chat_input_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_attach = ctk.CTkButton(self.chat_input_frame, text="📎", width=40, font=ctk.CTkFont(size=16, weight="bold"), command=self.attach_image, fg_color="#34495e", hover_color="#2c3e50")
        self.btn_attach.grid(row=0, column=0, padx=(0, 10))

        self.chat_entry = ctk.CTkEntry(self.chat_input_frame, placeholder_text="Aria'ya komut yazın (Resim yorumlatmak için ataş simgesini seçin)...", height=40, font=ctk.CTkFont(size=14))
        self.chat_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda event: self.send_manual_command())

        self.btn_send = ctk.CTkButton(self.chat_input_frame, text="Gönder ➔", width=90, height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.send_manual_command)
        self.btn_send.grid(row=0, column=2)

    def attach_image(self):
        filepath = ctk.filedialog.askopenfilename(filetypes=[("Görsel Dosyaları", "*.jpg *.png *.jpeg *.webp")])
        if filepath:
            self.attached_image = filepath
            # Geri bildirim (Kırmızı ve vurgulu renk)
            self.btn_attach.configure(fg_color="#e74c3c", text="📌")

    def send_manual_command(self):
        msg = self.chat_entry.get().strip()
        if not msg and not self.attached_image: return
        self.chat_entry.delete(0, "end")
        
        secili_resim = self.attached_image
        self.attached_image = None
        self.btn_attach.configure(fg_color="#34495e", text="📎") # Reset
        
        # UI donmaması için Asistanı Thread üzerinden çalıştırıyoruz
        def run_cmd():
            if self.asistan:
                print(f"👤 Sen: {msg if msg else '[Resim Gönderildi]'}")
                self.asistan.komut_isle(msg if msg else "Şu görsele dikkatlice bakıp ne gördüğünü analiz eder misin?", resim_yolu=secili_resim)
        
        threading.Thread(target=run_cmd, daemon=True).start()

    def setup_settings_tab(self):
        tab = self.tab_view.tab("Ayarlar")
        tab.grid_columnconfigure(0, weight=1, pad=20)
        tab.grid_columnconfigure(1, weight=3, pad=20)
        tab.grid_rowconfigure(6, weight=1)

        baslik_font = ctk.CTkFont(size=20, weight="bold")
        etiket_font = ctk.CTkFont(size=14)

        self.lbl_config = ctk.CTkLabel(tab, text="Asistan Yapılandırması", font=baslik_font)
        self.lbl_config.grid(row=0, column=0, columnspan=2, pady=20, padx=20, sticky="w")

        # 1. Ollama Model
        self.lbl_model = ctk.CTkLabel(tab, text="🧠 Yapay Zeka Modeli:", font=etiket_font)
        self.lbl_model.grid(row=1, column=0, padx=20, pady=12, sticky="w")
        self.model_var = ctk.CTkOptionMenu(tab, values=["(Ollama Başlatılıyor...)"], command=self.on_model_change, width=250)
        self.model_var.grid(row=1, column=1, padx=20, pady=12, sticky="w")

        # 2. Çalışma Dili
        self.lbl_lang = ctk.CTkLabel(tab, text="🌍 Konuşma Dili:", font=etiket_font)
        self.lbl_lang.grid(row=2, column=0, padx=20, pady=12, sticky="w")
        self.dil_var = ctk.CTkOptionMenu(tab, values=["Türkçe", "English"], command=self.on_lang_change, width=250)
        self.dil_var.grid(row=2, column=1, padx=20, pady=12, sticky="w")
        
        # 3. Vurgu Rengi
        self.lbl_accent = ctk.CTkLabel(tab, text="🎨 Özel Arayüz Rengi:", font=etiket_font)
        self.lbl_accent.grid(row=3, column=0, padx=20, pady=12, sticky="w")
        self.btn_renk = ctk.CTkButton(tab, text="Renk Daiesinden Seç...", command=self.pick_color, width=250, fg_color="#8e44ad", hover_color="#9b59b6")
        self.btn_renk.grid(row=3, column=1, padx=20, pady=12, sticky="w")
        
        # 4. Chat Arka Planı
        self.lbl_bg = ctk.CTkLabel(tab, text="🖼️ Sohbet Arka Planı:", font=etiket_font)
        self.lbl_bg.grid(row=4, column=0, padx=20, pady=12, sticky="w")
        bg_frame = ctk.CTkFrame(tab, fg_color="transparent")
        bg_frame.grid(row=4, column=1, padx=20, pady=12, sticky="w")
        self.btn_bg = ctk.CTkButton(bg_frame, text="Resim Yükle", command=self.choose_bg, width=150)
        self.btn_bg.grid(row=0, column=0, padx=(0, 10))
        self.btn_bg_clear = ctk.CTkButton(bg_frame, text="Kaldır ✖", command=self.clear_bg, width=90, fg_color="#c0392b", hover_color="#e74c3c")
        self.btn_bg_clear.grid(row=0, column=1)

        # 5. Kontrol Butonları
        self.lbl_controls = ctk.CTkLabel(tab, text="🛠️ Hızlı Aksiyonlar:", font=etiket_font)
        self.lbl_controls.grid(row=6, column=0, padx=20, pady=15, sticky="w")
        
        self.btn_clear_chat = ctk.CTkButton(tab, text="🗑️ Ekranı Temizle", command=self.clear_chat, width=120)
        self.btn_clear_chat.grid(row=6, column=1, padx=20, pady=15, sticky="w")
        
        self.btn_clear_mem = ctk.CTkButton(tab, text="🧠 Hafızayı Sıfırla", command=self.clear_memory, width=120, fg_color="#c0392b", hover_color="#e74c3c")
        self.btn_clear_mem.grid(row=6, column=1, padx=150, pady=15, sticky="w")
        
        # 6. Başlangıçta Çalıştır
        self.lbl_startup = ctk.CTkLabel(tab, text="🚀 Otomatik Başlatma:", font=etiket_font)
        self.lbl_startup.grid(row=7, column=0, padx=20, pady=12, sticky="w")
        
        self.boot_var = ctk.BooleanVar(value=self.config.get("run_on_boot", False))
        self.chk_boot = ctk.CTkCheckBox(tab, text="Windows açıldığında Aria'yı arka planda başlat", variable=self.boot_var, font=ctk.CTkFont(size=13), command=self.toggle_startup)
        self.chk_boot.grid(row=7, column=1, padx=20, pady=12, sticky="w")
        
        # 7. Gizle / Göster Kısayol Tuşu
        self.lbl_hotkey = ctk.CTkLabel(tab, text="⌨️ UI Gizle/Göster Kısayolu:", font=etiket_font)
        self.lbl_hotkey.grid(row=8, column=0, padx=20, pady=12, sticky="w")
        
        hotkey_frame = ctk.CTkFrame(tab, fg_color="transparent")
        hotkey_frame.grid(row=8, column=1, sticky="w", padx=20)
        
        self.hotkey_entry = ctk.CTkEntry(hotkey_frame, width=150)
        self.hotkey_entry.grid(row=0, column=0, padx=(0, 10))
        self.hotkey_entry.insert(0, self.current_hotkey)
        
        self.btn_save_hotkey = ctk.CTkButton(hotkey_frame, text="Kaydet", width=80, command=self.save_hotkey)
        self.btn_save_hotkey.grid(row=0, column=1)
        
        # UI Kapat Butonu Ek Özellik: Arayüzden gizleyebilmek için
        self.btn_hide_ui = ctk.CTkButton(tab, text="⏬ Arayüzü Arka Plana Gizle", width=250, fg_color="#f39c12", hover_color="#d35400", command=self.toggle_ui)
        self.btn_hide_ui.grid(row=9, column=1, padx=20, pady=12, sticky="w")

        # 8. Bilgi
        info_text = ("Bu ayarlar anlık olarak asistanınıza etki eder.\n\n"
                     "Mikrofon: Bilgisayarınızın ana (varsayılan) mikrofonu otomatik kullanılır.\n"
                     "Modeller: Local 'Ollama' modellerinizden biri seçilebilir.\n"
                     "Not: Arayüz devredeyken terminal arkaplanda kapalı modda izole edilir.")
        self.lbl_info = ctk.CTkLabel(tab, text=info_text, font=ctk.CTkFont(size=13, slant="italic"), text_color="#7f8c8d", justify="left")
        self.lbl_info.grid(row=10, column=0, columnspan=2, padx=20, pady=30, sticky="w")

        # Config'den kayıtlı rengi çek ve uygula
        kayitli_renk = self.config.get("accent_color", "#3498db")
        self.app.after(100, lambda: self.apply_accent_color(kayitli_renk))

    def pick_color(self):
        pick_color = AskColor()
        color = pick_color.get()
        if color:
            self.apply_accent_color(color)

    def apply_bg(self, path):
        if not os.path.exists(path): return
        img = Image.open(path)
        self.bg_image = ctk.CTkImage(light_image=img, dark_image=img, size=(2000, 1500))
        
        if not hasattr(self, 'bg_label'):
            self.bg_label = ctk.CTkLabel(self.tab_view.tab("Sohbet Merkezi"), text="", image=self.bg_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bg_label.lower() # En arkaya at
            # Textbox'ı Saydamlaştır
            self.chat_textbox.configure(fg_color="transparent")
            self.chat_input_frame.configure(fg_color="transparent")
        else:
            self.bg_label.configure(image=self.bg_image)

    def choose_bg(self):
        dosya = ctk.filedialog.askopenfilename(filetypes=[("Resimler", "*.jpg *.png *.jpeg *.webp")])
        if dosya:
            self.config["bg_image"] = dosya
            self.apply_bg(dosya)
            self.save_config()

    def clear_bg(self):
        if hasattr(self, 'bg_label'):
            self.bg_label.place_forget()
            del self.bg_label
        self.chat_textbox.configure(fg_color=["gray86", "gray17"])
        self.config.pop("bg_image", None)
        self.save_config()

    def clear_chat(self):
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.delete("1.0", "end")
        self.chat_textbox.configure(state="disabled")

    def clear_memory(self):
        if self.asistan:
            self.asistan.sohbet_gecmisi = []
            self.add_system_message("Yapay zeka (Ollama) sohbet hafızası sıfırlandı.")
            
    def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception:
            self.config = {}

    def save_config(self):
        try:
            # Pencere pozisyonunu güncelle
            geom = self.app.geometry()
            try:
                w_h, x, y = geom.split('+')
                w, h = w_h.split('x')
                self.config["width"] = int(w)
                self.config["height"] = int(h)
                self.config["pos_x"] = int(x)
                self.config["pos_y"] = int(y)
            except Exception: pass
            
            self.config["theme"] = ctk.get_appearance_mode()
            self.config["accent_color"] = getattr(self, "current_color", "#3498db")
            self.config["run_on_boot"] = self.boot_var.get()
            self.config["toggle_hotkey"] = self.current_hotkey
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print("Config kaydedilirken hata:", e)

    def on_hotkey(self):
        # Hotkey callback içinden Tkinter safe çalıştırmak için
        self.app.after(10, self.toggle_ui)

    def toggle_ui(self):
        if self.is_ui_visible:
            self.app.withdraw() # Pencereyi gizle
            self.is_ui_visible = False
        else:
            self.app.deiconify() # Pencereyi geri getir
            self.app.lift()
            self.app.focus_force()
            self.is_ui_visible = True

    def save_hotkey(self):
        new_hotkey = self.hotkey_entry.get().strip()
        if new_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except: pass
            
            try:
                keyboard.add_hotkey(new_hotkey, self.on_hotkey)
                self.current_hotkey = new_hotkey
                self.add_system_message(f"Arayüz gizleme/gösterme kısayolu '{new_hotkey}' olarak güncellendi.")
                self.save_config()
            except Exception as e:
                self.add_system_message(f"Kısayol ayarlanamadı: {e}")

    def toggle_startup(self):
        durum = self.boot_var.get()
        reg_yolu = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_adi = "AriaSesliAsistan"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_yolu, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
            if durum:
                # Arkaplanda sessizce çalışması için komut düzenlemesi
                dosya_yolu = os.path.abspath(__file__)
                python_exe = sys.executable
                if dosya_yolu.endswith(".exe"):
                    komut = f'"{dosya_yolu}"'
                else:
                    komut = f'"{python_exe}" "{dosya_yolu}"'
                winreg.SetValueEx(key, app_adi, 0, winreg.REG_SZ, komut)
                self.add_system_message("Aria Başlangıç'a eklendi. Windows açıldığında arkaplanda çalışacak.")
            else:
                try:
                    winreg.DeleteValue(key, app_adi)
                    self.add_system_message("Aria Başlangıç'tan kaldırıldı.")
                except WindowsError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.add_system_message(f"Başlangıç ayarı değiştirilirken kayıt defteri hatası: {e}")
        
        self.save_config()

    def apply_accent_color(self, hex_color):
        
        # Eski bozuk ayar dosyasındaki yazıları temizle ve salt Hex koduna çevir
        if "Mavi" in str(hex_color) or "#" not in str(hex_color):
            hex_color = "#3498db"
        elif "Yeşil" in str(hex_color):
            hex_color = "#2ecc71"
        elif "Mor" in str(hex_color):
            hex_color = "#9b59b6"
        elif "Kırmızı" in str(hex_color):
            hex_color = "#e74c3c"
            
        self.current_color = hex_color
        # Temel Butonları ve Widgetları Canlı Olarak Boyar:
        butons = [self.btn_chat, self.btn_settings, self.btn_bg, self.btn_send, self.btn_clear_chat, self.btn_save_hotkey, self.btn_renk]
        if hasattr(self, 'theme_btn'): butons.append(self.theme_btn)
        if hasattr(self, 'model_var'): butons.append(self.model_var)
        if hasattr(self, 'dil_var'): butons.append(self.dil_var)
        
        for widget in butons:
            try:
                widget.configure(fg_color=hex_color)
            except: pass
            
        try:
            self.ai_progress.configure(progress_color=hex_color)
            self.chk_boot.configure(fg_color=hex_color, hover_color=hex_color)
        except: pass
        
        self.save_config()
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.delete("1.0", "end")
        self.chat_textbox.configure(state="disabled")

    def clear_memory(self):
        if self.asistan:
            self.asistan.sohbet_gecmisi = []
            self.add_system_message("Yapay zeka (Ollama) sohbet hafızası sıfırlandı.")

    def setup_dev_tab(self):
        tab = self.tab_view.tab("Geliştirici")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.dev_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=13), wrap="none", corner_radius=10, fg_color="#1e1e1e", text_color="#d4d4d4")
        self.dev_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.dev_textbox.configure(state="disabled")
        
    def update_ui_language(self, lang):
        if lang == "en":
            self.btn_chat.configure(text="💬  Live Chat Center")
            self.btn_settings.configure(text="⚙️  Advanced Settings")
            self.sidebar_theme_label.configure(text="Appearance Mode:")
            self.app.title(f"{ASISTAN_ADI} - Smart Voice Assistant Control Panel")
            self.lbl_config.configure(text="Assistant Configuration")
            self.lbl_model.configure(text="🧠 AI Model:")
            self.lbl_lang.configure(text="🌍 Language:")
            self.lbl_accent.configure(text="🎨 Accent Color:")
            self.lbl_controls.configure(text="🛠️ Quick Actions:")
            self.btn_clear_chat.configure(text="🗑️ Clear Screen")
            self.btn_clear_mem.configure(text="🧠 Clear Memory")
            self.btn_send.configure(text="Send ➔")
            self.chat_entry.configure(placeholder_text="Type command for Aria...")
            self.lbl_info.configure(text="These settings immediately affect your assistant.\n\nMicrophone: Your default system microphone is used.\nModels: Choose from your local 'Ollama' models.\nNote: Terminal output is isolated in the background.")
        else:
            self.btn_chat.configure(text="💬  Canlı Sohbet Merkezi")
            self.btn_settings.configure(text="⚙️  Gelişmiş Ayarlar")
            self.sidebar_theme_label.configure(text="Görünüm Modu:")
            self.app.title(f"{ASISTAN_ADI} - Akıllı Sesli Asistan Kontrol Paneli")
            self.lbl_config.configure(text="Asistan Yapılandırması")
            self.lbl_model.configure(text="🧠 Yapay Zeka Modeli:")
            self.lbl_lang.configure(text="🌍 Konuşma Dili:")
            self.lbl_accent.configure(text="🎨 Arayüz Vurgu Rengi:")
            self.lbl_controls.configure(text="🛠️ Hızlı Aksiyonlar:")
            self.btn_clear_chat.configure(text="🗑️ Ekranı Temizle")
            self.btn_clear_mem.configure(text="🧠 Hafızayı Sıfırla")
            self.btn_send.configure(text="Gönder ➔")
            self.chat_entry.configure(placeholder_text="Aria'ya komut yazın...")
            self.lbl_info.configure(text="Bu ayarlar anlık olarak asistanınıza etki eder.\n\n"
                     "Mikrofon: Bilgisayarınızın ana (varsayılan) mikrofonu otomatik kullanılır.\n"
                     "Modeller: Local 'Ollama' modellerinizden biri seçilebilir.\n"
                     "Not: Arayüz devredeyken terminal arkaplanda kapalı modda izole edilir.")

    def on_model_change(self, secim):
        if self.asistan:
            # Sesli şekilde değiştirmesini de sağlar
            self.asistan.model_degistir(secim)

    def on_lang_change(self, secim):
        if self.asistan:
            dil_kodu = "tr" if secim == "Türkçe" else "en"
            self.asistan.dil_degistir(dil_kodu)
            self.update_ui_language(dil_kodu)

    def on_closing(self):
        """Uygulama tamamen kapatıldığında process'i öldür"""
        self.save_config()
        
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        
        # Sesi sustur (Eğer konuşuyorsa)
        if self.asistan and hasattr(self.asistan, 'tts'):
            try: self.asistan.tts.stop()
            except: pass
            
        self.app.destroy()
        sys.exit(0)

    def run(self):
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.app.mainloop()


if __name__ == "__main__":
    gui = AriaGUI()
    gui.run()
