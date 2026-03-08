import sys
import threading
import time
import os

try:
    import customtkinter as ctk
except ImportError:
    print("CustomTkinter yüklenmemiş, lütfen bekleyin...")
    os.system(f"{sys.executable} -m pip install customtkinter")
    import customtkinter as ctk

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
        self.app = ctk.CTk()
        self.app.title(f"{ASISTAN_ADI} - Akıllı Sesli Asistan Kontrol Paneli")
        self.app.geometry("1000x650")
        
        # Terminal Çıktılarını UI Yönlendirmesi
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = PrintRedirector(self)
        sys.stderr = PrintRedirector(self)

        self.setup_ui()
        
        self.asistan = None
        self.asistan_thread = threading.Thread(target=self.start_asistan, daemon=True)
        self.asistan_thread.start()

    def start_asistan(self):
        self.add_system_message("Sistem başlatılıyor, mikrofon kalibre ediliyor...")
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
        
        if "👤 Sen:" in text:
            msg = text.replace("👤 Sen:", "").strip()
            self.add_chat_bubble(msg, sender="user")
        elif f"🔊 {ASISTAN_ADI}:" in text:
            msg = text.replace(f"🔊 {ASISTAN_ADI}:", "").strip()
            self.add_chat_bubble(msg, sender="aria")
            self.status_label.configure(text=f"Durum: {ASISTAN_ADI} Konuşuyor...", text_color="#10eb44")
        elif "🎤 Dinliyorum..." in text:
            self.status_label.configure(text="Durum: Sizi Dinliyor...", text_color="#f1c40f")
        elif "⚙️ İşleniyor..." in text or "düşünüyor..." in text:
            self.status_label.configure(text="Durum: Yapay Zeka Düşünüyor...", text_color="#3498db")
        elif "Uyku moduna" in text or "sizi duyamadım" in text:
            self.status_label.configure(text="Durum: Uyku Modunda (Arka plan dinleme)", text_color="#aaaaaa")
        elif "🔑 Şifre:" in text:
            self.add_chat_bubble(text, sender="system")
        else:
            # Diğer tüm önemsiz/sistem stringleri
            if "hata" in text.lower() or "error" in text.lower() or "kalibrasyonu tamamlandı" in text:
                self.add_system_message(text)

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
        self.app.grid_rowconfigure(0, weight=1)

        # ── SOL MENÜ (Sidebar) ──
        self.sidebar = ctk.CTkFrame(self.app, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # UI Marka / Logo
        self.logo_label = ctk.CTkLabel(self.sidebar, text=f"{ASISTAN_ADI} AI", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Status göstergesi
        self.status_label = ctk.CTkLabel(self.sidebar, text="Durum: Başlangıç...", text_color="#aaaaaa", font=ctk.CTkFont(size=13, weight="normal"))
        self.status_label.grid(row=1, column=0, padx=20, pady=10)

        # SOHBET Butonu
        self.btn_chat = ctk.CTkButton(self.sidebar, text="💬  Canlı Sohbet Merkezi", height=40, font=ctk.CTkFont(size=14), command=lambda: self.tab_view.set("Sohbet Merkezi"))
        self.btn_chat.grid(row=2, column=0, padx=20, pady=10)

        # AYARLAR Butonu
        self.btn_settings = ctk.CTkButton(self.sidebar, text="⚙️  Gelişmiş Ayarlar", height=40, font=ctk.CTkFont(size=14), fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=lambda: self.tab_view.set("Ayarlar"))
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10)
        
        # UI Teması Seçici
        self.sidebar_theme_label = ctk.CTkLabel(self.sidebar, text="Görünüm Modu:", anchor="w")
        self.sidebar_theme_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.theme_btn = ctk.CTkOptionMenu(self.sidebar, values=["Dark", "Light", "System"], command=self.change_theme)
        self.theme_btn.grid(row=6, column=0, padx=20, pady=(10, 20))

        # ── SAĞ ALAN (Tab Gösterimi) ──
        self.tab_view = ctk.CTkTabview(self.app, corner_radius=15)
        self.tab_view.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        
        self.tab_view.add("Sohbet Merkezi")
        self.tab_view.add("Ayarlar")
        self.tab_view.set("Sohbet Merkezi")

        self.setup_chat_tab()
        self.setup_settings_tab()

    def change_theme(self, choice):
        ctk.set_appearance_mode(choice)

    def setup_chat_tab(self):
        tab = self.tab_view.tab("Sohbet Merkezi")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.chat_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=15), wrap="word", corner_radius=10)
        self.chat_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # TKinter Tag konfigürasyonu (Metin renklendirme)
        text_widget = self.chat_textbox._textbox
        text_widget.tag_config("user", foreground="#3498db", font=("Consolas", 14, "bold"))
        text_widget.tag_config("aria", foreground="#2ecc71", font=("Consolas", 14, "normal"))
        text_widget.tag_config("sistem", foreground="#e67e22", font=("Consolas", 12, "italic"))
        
        self.chat_textbox.configure(state="disabled")

    def setup_settings_tab(self):
        tab = self.tab_view.tab("Ayarlar")
        tab.grid_columnconfigure(0, weight=1, pad=20)
        tab.grid_columnconfigure(1, weight=3, pad=20)
        tab.grid_rowconfigure(5, weight=1)

        baslik_font = ctk.CTkFont(size=20, weight="bold")
        etiket_font = ctk.CTkFont(size=14)

        ctk.CTkLabel(tab, text="Asistan Yapılandırması", font=baslik_font).grid(row=0, column=0, columnspan=2, pady=20, padx=20, sticky="w")

        # 1. Ollama Model
        ctk.CTkLabel(tab, text="🧠 Yapay Zeka Modeli:", font=etiket_font).grid(row=1, column=0, padx=20, pady=15, sticky="w")
        self.model_var = ctk.CTkOptionMenu(tab, values=["(Ollama Başlatılıyor...)"], command=self.on_model_change, width=250)
        self.model_var.grid(row=1, column=1, padx=20, pady=15, sticky="w")

        # 2. Çalışma Dili
        ctk.CTkLabel(tab, text="🌍 Konuşma Dili:", font=etiket_font).grid(row=2, column=0, padx=20, pady=15, sticky="w")
        self.dil_var = ctk.CTkOptionMenu(tab, values=["Türkçe", "English"], command=self.on_lang_change, width=250)
        self.dil_var.grid(row=2, column=1, padx=20, pady=15, sticky="w")
        
        # 3. Bilgi
        info_text = ("Bu ayarlar anlık olarak asistanınıza etki eder.\n\n"
                     "Mikrofon: Bilgisayarınızın ana (varsayılan) mikrofonu otomatik kullanılır.\n"
                     "Modeller: Local 'Ollama' modellerinizden biri seçilebilir.\n"
                     "Not: Arayüz devredeyken terminal arkaplanda kapalı modda izole edilir.")
        ayarlar_bilgi = ctk.CTkLabel(tab, text=info_text, font=ctk.CTkFont(size=13, slant="italic"), text_color="#7f8c8d", justify="left")
        ayarlar_bilgi.grid(row=3, column=0, columnspan=2, padx=20, pady=30, sticky="w")

    def on_model_change(self, secim):
        if self.asistan:
            # Sesli şekilde değiştirmesini de sağlar
            self.asistan.model_degistir(secim)

    def on_lang_change(self, secim):
        if self.asistan:
            dil_kodu = "tr" if secim == "Türkçe" else "en"
            self.asistan.dil_degistir(dil_kodu)

    def on_closing(self):
        """Uygulama tamamen kapatıldığında process'i öldür"""
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
