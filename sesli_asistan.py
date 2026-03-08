"""
╔══════════════════════════════════════════════════════════════╗
║           TÜRKÇE SESLİ ASİSTAN - WINDOWS EDİSYON            ║
║         Ollama Destekli • Sesli Komut • Tam Kontrol          ║
╚══════════════════════════════════════════════════════════════╝

KURULUM:
  pip install SpeechRecognition pyttsx3 requests pyaudio psutil

ÇALIŞTIRMA:
  python sesli_asistan.py

"""

import speech_recognition as sr
import pyttsx3
import requests
import json
import os
import subprocess
import psutil
import datetime
import webbrowser
import sys
import time
import threading
import re
import glob
import io

# --- KODLAMA DÜZELTME (Türkçe Karakter Sorunu İçin) ---
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass
# ----------------------------------------------------

from pathlib import Path
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

# Overlay ses dalgası
try:
    from overlay import SesOverlay
    HAS_OVERLAY = True
except ImportError:
    HAS_OVERLAY = False

# Yeni yetenekler için modüller
try:
    import pyautogui
    import wikipedia
    import screen_brightness_control as sbc
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_EXTRA_MODULES = True
except ImportError:
    HAS_EXTRA_MODULES = False

# ══════════════════════════════════════════
#  YAPILANDIRMA
# ══════════════════════════════════════════

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3"       # Değiştirin: mistral, phi3, gemma, vs.
ASISTAN_ADI = "Aria"
NOTES_FILE = str(Path.home() / "Desktop" / "asistan_notlar.txt")

# ══════════════════════════════════════════
#  UYGULAMA HARİTASI (Yeni uygulamalar ekleyebilirsiniz)
# ══════════════════════════════════════════

UYGULAMALAR = {
    # Tarayıcılar
    "brave":         r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    # Oyun / Platform
    "steam":         r"C:\Program Files (x86)\Steam\steam.exe",
    "epic":          r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    "discord":       r"C:\Users\{user}\AppData\Local\Discord\app-*\Discord.exe",

    # Ofis
    "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":    r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "notepad":       "notepad.exe",
    "not defteri":   "notepad.exe",

    # Sistem
    "görev yöneticisi": "taskmgr.exe",
    "task manager":     "taskmgr.exe",
    "hesap makinesi":   "calc.exe",
    "calculator":       "calc.exe",
    "dosya gezgini":    "explorer.exe",
    "explorer":         "explorer.exe",
    "denetim masası":   "control.exe",
    "ayarlar":          "ms-settings:",
    "komut istemi":     "cmd.exe",
    "powershell":       "powershell.exe",

    # Medya & Eğlence
    "spotify":       r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vlc media":     r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "netflix":       r"ms-windows-store://pdp/?ProductId=9WZDNCRFJ3TJ",
    "media player":  "wmplayer.exe",

    # Geliştirme
    "vscode":        r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code":       r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio": r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",

    # İletişim
    "zoom":          r"C:\Users\{user}\AppData\Roaming\Zoom\bin\Zoom.exe",
    "teams":         r"C:\Users\{user}\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "whatsapp":      r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
    "discord":       r"C:\Users\{user}\AppData\Local\Discord\app-*\Discord.exe",
    "telegram":      r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe",

    # Araçlar & Tasarım
    "photoshop":     r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe",
    "7-zip":         r"C:\Program Files\7-Zip\7zFM.exe",
    "7zip":          r"C:\Program Files\7-Zip\7zFM.exe",
    "winrar":        r"C:\Program Files\WinRAR\WinRAR.exe",
    "drive":         r"C:\Program Files\Google\Drive File Stream\*\GoogleDriveFS.exe",
    "google drive":  r"C:\Program Files\Google\Drive File Stream\*\GoogleDriveFS.exe",
    "paint":         "mspaint.exe",
    "wordpad":       "wordpad.exe",
    "snipping tool": "snippingtool.exe",
    "ekran alıntısı":"snippingtool.exe",
}

WEB_SITELERI = {
    "youtube":      "https://www.youtube.com",
    "google":       "https://www.google.com",
    "github":       "https://www.github.com",
    "gmail":        "https://mail.google.com",
    "twitter":      "https://www.twitter.com",
    "x":            "https://www.x.com",
    "instagram":    "https://www.instagram.com",
    "linkedin":     "https://www.linkedin.com",
    "netflix":      "https://www.netflix.com",
    "reddit":       "https://www.reddit.com",
    "wikipedia":    "https://www.wikipedia.org",
    "chatgpt":      "https://chat.openai.com",
    "drive":        "https://drive.google.com",
    "hava durumu":  "https://www.mgm.gov.tr",
}

# ══════════════════════════════════════════
#  TEMEL SINIF
# ══════════════════════════════════════════

class SesliAsistan:
    def __init__(self):
        print(f"\n{'═'*60}")
        print(f"  {ASISTAN_ADI} - Sesli Asistan Başlatılıyor...")
        print(f"{'═'*60}\n")

        self.dil = "tr"  # "tr" veya "en"
        self.tts = pyttsx3.init()
        self._tts_ayarla()

        # STT - Maksimum hassasiyet ayarları
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.8
        self.recognizer.non_speaking_duration = 0.5

        # Varsayılan mikrofonu otomatik algıla ve göster
        self.mikrofon_index = None
        try:
            varsayilan = sr.Microphone()
            self.mikrofon_index = varsayilan.device_index if varsayilan.device_index is not None else 0
            mic_listesi = sr.Microphone.list_microphone_names()
            
            # Mikrofon ismindeki bozuk karakterleri temizle
            mic_adi = mic_listesi[self.mikrofon_index]
            try:
                mic_adi = mic_adi.encode('cp1252').decode('utf-8')
            except:
                try:
                    mic_adi = mic_adi.encode('utf-8').decode('utf-8')
                except:
                    pass

            print(f"🎙️ Varsayılan mikrofon: [{self.mikrofon_index}] {mic_adi}")
            with sr.Microphone(device_index=self.mikrofon_index) as m_init:
                self.recognizer.adjust_for_ambient_noise(m_init, duration=0.5)
            print(f"🔊 Ortam sesi kalibrasyonu tamamlandı (threshold: {self.recognizer.energy_threshold})")
        except Exception as e:
            print(f"⚠️ Mikrofon algılama hatası: {e}")
            try:
                for i, ad in enumerate(sr.Microphone.list_microphone_names()):
                    print(f"  [{i}] {ad}")
            except: pass

        self.son_sifre = ""
        self.dinliyor = True
        self.model = DEFAULT_MODEL
        self.sohbet_gecmisi = []
        self.mevcut_ollama_modeller = []

        # Overlay - Thread güvenli başlatma
        self.overlay = None
        if HAS_OVERLAY:
            def overlay_baslatici():
                try:
                    # Tkinter nesnesi ve mainloop AYNI thread'de olmalı
                    from overlay import SesOverlay
                    self.overlay = SesOverlay()
                    if hasattr(self.overlay, 'set_model'):
                        self.overlay.set_model(self.model)
                    self.overlay.baslat()
                except Exception as e:
                    print(f"Overlay hatası (Thread): {e}")

            ot = threading.Thread(target=overlay_baslatici, daemon=True)
            ot.start()
            # Overlay nesnesinin oluşması için bekle
            time.sleep(1.0)

        # Sistem promptu (Dinamik)
        self._prompt_guncelle()

        # Ek modüller
        if HAS_EXTRA_MODULES:
            wikipedia.set_lang("tr")

        self.konuş(f"Merhaba! Ben {ASISTAN_ADI}. Nasıl yardımcı olabilirim?")
        self._ollama_kontrol()

    def _tts_ayarla(self, dil=None):
        """TTS Ses ayarları (Türkçe/İngilizce destekli)"""
        hedef_dil = dil if dil else self.dil
        sesler = self.tts.getProperty('voices')
        uygun_ses = None
        
        for ses in sesler:
            s_name = ses.name.lower()
            s_id = ses.id.lower()
            
            if hedef_dil == "tr":
                if 'turkish' in s_name or 'tr' in s_id or 'türk' in s_name:
                    uygun_ses = ses.id
                    break
            else: # English
                if 'english' in s_name or 'en' in s_id or 'united states' in s_name:
                    uygun_ses = ses.id
                    break

        if uygun_ses:
            self.tts.setProperty('voice', uygun_ses)
        elif sesler:
            self.tts.setProperty('voice', sesler[0].id)

        self.tts.setProperty('rate', 185 if hedef_dil == "en" else 175)
        self.tts.setProperty('volume', 0.95)

    def _prompt_guncelle(self):
        """Dile göre sistem promptunu güncelle"""
        tarih = datetime.datetime.now().strftime('%d %B %Y, %H:%M')
        if self.dil == "tr":
            self.sistem_promptu = f"""Sen {ASISTAN_ADI} adlı Türkçe konuşan bir sesli asistansın.
Kullanıcının bilgisayarını yönetmesine yardımcı oluyorsun.
Cevaplarını kısa, net ve Türkçe ver. Sadece düz metin yaz (emoji/markdown kullanma).
Tarih: {tarih}"""
        else:
            self.sistem_promptu = f"""You are {ASISTAN_ADI}, an English speaking AI assistant.
You help the user manage their Windows computer.
Keep answers short, clear, and in English. Use only plain text (no emojis/markdown).
Date: {tarih}"""

    def dil_degistir(self, yeni_dil: str):
        """Asistan dilini değiştir (tr <-> en)"""
        if yeni_dil == self.dil: return
        
        self.dil = yeni_dil
        self._tts_ayarla()
        self._prompt_guncelle()
        
        if HAS_EXTRA_MODULES:
            wikipedia.set_lang("tr" if self.dil == "tr" else "en")
            
        if self.dil == "en":
            self.konuş("Language switched to English. How can I help you?")
        else:
            self.konuş("Dil Türkçe olarak değiştirildi. Size nasıl yardımcı olabilirim?")

    def konuş(self, metin: str):
        """Metni sesli oku"""
        print(f"\n🔊 {ASISTAN_ADI}: {metin}\n")
        temiz = re.sub(r'[*_`#\[\]()>~|]', '', metin)
        temiz = re.sub(r'\n+', '. ', temiz)
        # Overlay'i konuşuyor moduna al
        if self.overlay:
            try: self.overlay.konusuyor_modu()
            except: pass
        self.tts.say(temiz)
        self.tts.runAndWait()
        # Konuşma bitti, bekleme moduna dön
        if self.overlay:
            try: self.overlay.bekleme_modu()
            except: pass

    def dinle(self, zaman_asimi: int = 7, tekrar: bool = True) -> str | None:
        """Mikrofondan ses al - Varsayılan mikrofonu kullanır"""
        with sr.Microphone(device_index=self.mikrofon_index) as kaynak:
            if self.overlay:
                try: self.overlay.dinliyor_modu()
                except: pass
            print("🎤 Dinliyorum...")
            try:
                # listen başladığında ortam sesini her seferinde analiz etmeye GEREK YOK
                # bu durum konuşmanın başını kaçırabilir
                ses = self.recognizer.listen(
                    kaynak,
                    timeout=zaman_asimi,
                    phrase_time_limit=15
                )
                print("⚙️ İşleniyor...")
                metin = self.recognizer.recognize_google(
                    ses, language='tr-TR' if self.dil == "tr" else 'en-US',
                    show_all=False
                )
                if self.overlay:
                    try: self.overlay.bekleme_modu(son_komut=metin)
                    except: pass
                metin_sonuc = metin.lower()
                print(f"👤 Sen: {metin}")
                return metin_sonuc
            except sr.WaitTimeoutError:
                if self.overlay:
                    try: self.overlay.bekleme_modu()
                    except: pass
                return None
            except sr.UnknownValueError:
                print("❓ Anlaşılamadı.")
                if self.overlay:
                    try: self.overlay.bekleme_modu()
                    except: pass
                return None
            except sr.RequestError as e:
                print(f"❌ Google STT hatası: {e}")
                if self.overlay:
                    try: self.overlay.bekleme_modu()
                    except: pass
                self.konuş("İnternet bağlantısı sorunu var.")
                return None

    # ══════════════════════════════════════════
    #  OLLAMA ENTEGRASYONU
    # ══════════════════════════════════════════

    def _ollama_kontrol(self):
        """Ollama bağlantısını kontrol et ve en iyi modeli seç"""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                data = r.json()
                self.mevcut_ollama_modeller = [m['name'] for m in data.get('models', [])]
                print(f"✅ Ollama bağlı. Modeller: {', '.join(self.mevcut_ollama_modeller)}")
                
                if self.mevcut_ollama_modeller:
                    # Akıllı model seçimi: llama, mistral veya gemma varsa onları tercih et
                    oncelikli = ["llama3", "llama2", "mistral", "gemma", "phi3"]
                    secilen = None
                    
                    for p in oncelikli:
                        for m in self.mevcut_ollama_modeller:
                            if p in m.lower():
                                secilen = m
                                break
                        if secilen: break
                    
                    self.model = secilen if secilen else self.mevcut_ollama_modeller[0]
                    self.konuş(f"Ollama bağlantısı kuruldu. Aktif model: {self.model}")
                else:
                    self.konuş("Ollama bağlı ama hiç model yüklü değil.")
        except Exception:
            print("⚠️ Ollama bağlantısı yok.")
            self.konuş("Ollama şu an çalışmıyor.")

    def ollama_sor(self, soru: str, sistem: str = None, ozel_model: str = None) -> str:
        """Ollama'ya soru sor"""
        if not sistem:
            sistem = self.sistem_promptu

        aktif_model = ozel_model if ozel_model else self.model
        
        # Modeli doğrula
        if self.mevcut_ollama_modeller and aktif_model not in self.mevcut_ollama_modeller:
            aktif_model = self.model

        self.sohbet_gecmisi.append({"role": "user", "content": soru})

        payload = {
            "model": aktif_model,
            "messages": [{"role": "system", "content": sistem}] + self.sohbet_gecmisi,
            "stream": False
        }

        try:
            print(f"🤖 {aktif_model} düşünüyor...")
            r = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=20)
            if r.status_code == 200:
                cevap = r.json()['message']['content']
                self.sohbet_gecmisi.append({"role": "assistant", "content": cevap})
                if len(self.sohbet_gecmisi) > 20:
                    self.sohbet_gecmisi = self.sohbet_gecmisi[-20:]
                return cevap
            elif r.status_code == 404:
                return f"Hata 404: {aktif_model} bulunamadı."
            else:
                return f"Ollama hata kodu: {r.status_code}"
        except requests.exceptions.ConnectionError:
            return "Ollama'ya bağlanılamıyor. Lütfen Ollama'nın çalıştığından emin olun."
        except Exception as e:
            return f"Hata oluştu: {str(e)}"

    def model_degistir(self, model_adi: str):
        """Aktif modeli değiştir"""
        if model_adi in self.mevcut_ollama_modeller:
            self.model = model_adi
            if self.overlay and hasattr(self.overlay, 'set_model'):
                try: self.overlay.set_model(self.model)
                except: pass
            self.sohbet_gecmisi = []  # Geçmişi temizle
            self.konuş(f"Model {model_adi} olarak değiştirildi ve sohbet geçmişi temizlendi.")
        elif self.mevcut_ollama_modeller:
            benzer = [m for m in self.mevcut_ollama_modeller if model_adi in m]
            if benzer:
                self.model = benzer[0]
                if self.overlay and hasattr(self.overlay, 'set_model'):
                    try: self.overlay.set_model(self.model)
                    except: pass
                self.konuş(f"Model {self.model} olarak ayarlandı.")
            else:
                self.konuş(f"Model bulunamadı. Mevcut modeller: {', '.join(self.mevcut_ollama_modeller)}")
        else:
            self.konuş("Hiç Ollama modeli yüklü değil.")

    # ══════════════════════════════════════════
    #  UYGULAMA KONTROLÜ
    # ══════════════════════════════════════════

    def uygulama_ac(self, isim: str) -> bool:
        """Uygulama aç (Daha hassas eşleşme ve ek temizleme ile)"""
        # Türkçe ekleri temizle (YouTube'u -> YouTube, Spotify'ı -> Spotify)
        isim_temiz = re.sub(r'[\'\"].*$', '', isim.lower().strip()) # Suffixleri at (YouTube'u -> youtube)
        isim_temiz = re.sub(r'(yu|yı|yi|ya|ye|u|ı|i|a|e|nu|nı)$', '', isim_temiz) # Kelime sonundaki ekleri temizle
        
        kullanici = os.environ.get('USERNAME', 'User')

        # 1. Tam Eşleşme veya Uygulama Haritası Kontrolü
        hedef_yol = None
        for anahtar, yol in UYGULAMALAR.items():
            if anahtar == isim_temiz or anahtar in isim_temiz:
                hedef_yol = yol
                break
        
        if hedef_yol:
            yol = hedef_yol.replace('{user}', kullanici)

            # Wildcard desteği
            if '*' in yol:
                import glob
                eslesmeler = glob.glob(yol)
                if eslesmeler:
                    yol = eslesmeler[-1]
                else:
                    self.konuş(f"{isim} bulunamadı.")
                    return False

            try:
                if self.overlay and hasattr(self.overlay, 'gorev_modu'):
                    self.overlay.gorev_modu("AÇILIYOR", "#00e5ff") # Turkuaz
                    
                if yol.startswith('ms-'):
                    os.startfile(yol)
                elif os.path.exists(yol):
                    subprocess.Popen([yol])
                else:
                    subprocess.Popen(yol, shell=True)
                self.konuş(f"{isim} açılıyor.")
                return True
            except Exception as e:
                self.konuş(f"{isim} açılamadı: {str(e)}")
                return False

        self.konuş(f"{isim} uygulaması tanımlanmamış. Aramaya çalışıyorum.")
        return self._uygulama_ara_ac(isim)

    def _uygulama_ara_ac(self, isim: str) -> bool:
        """Windows arama ile uygulama aç"""
        try:
            subprocess.Popen(f'start "" "{isim}"', shell=True)
            return True
        except Exception:
            return False

    def uygulama_kapat(self, isim: str):
        """Uygulama kapat"""
        kapatildi = False
        for proc in psutil.process_iter(['name', 'pid']):
            if isim.lower() in proc.info['name'].lower():
                try:
                    proc.terminate()
                    kapatildi = True
                except Exception:
                    pass
        if kapatildi:
            if self.overlay and hasattr(self.overlay, 'gorev_modu'):
                self.overlay.gorev_modu("KAPATILDI", "#ff1744") # Kırmızı
            self.konuş(f"{isim} kapatıldı.")
        else:
            self.konuş(f"{isim} çalışmıyor.")

    def calisan_uygulamalar(self):
        """Çalışan uygulamaları listele"""
        uygulamalar = set()
        for proc in psutil.process_iter(['name']):
            try:
                ad = proc.info['name'].replace('.exe', '')
                if ad and ad not in ['svchost', 'System', 'Registry', 'smss',
                                      'csrss', 'wininit', 'services', 'lsass',
                                      'winlogon', 'fontdrvhost', 'dwm']:
                    uygulamalar.add(ad)
            except Exception:
                pass
        liste = sorted(list(uygulamalar))[:15]
        self.konuş(f"Çalışan uygulamalar: {', '.join(liste)}")

    # ══════════════════════════════════════════
    #  SİSTEM BİLGİLERİ
    # ══════════════════════════════════════════

    def sistem_bilgisi(self):
        """Sistem durumunu oku"""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')

        bilgi = (f"İşlemci kullanımı yüzde {cpu}. "
                 f"RAM: {ram.used // (1024**3)} GB kullanılan, toplam {ram.total // (1024**3)} GB. "
                 f"Disk: {disk.used // (1024**3)} GB kullanılan, toplam {disk.total // (1024**3)} GB. "
                 f"Yüzde {disk.percent} dolu.")
        self.konuş(bilgi)

    def pil_durumu(self):
        """Pil durumunu kontrol et"""
        try:
            pil = psutil.sensors_battery()
            if pil:
                durum = "şarj oluyor" if pil.power_plugged else "şarjda değil"
                self.konuş(f"Pil yüzde {int(pil.percent)} dolu, {durum}.")
            else:
                self.konuş("Pil bilgisi alınamadı veya bu cihazda pil yok.")
        except Exception:
            self.konuş("Pil bilgisi alınamadı.")

    def ag_bilgisi(self):
        """Ağ bağlantısı bilgisi"""
        ag = psutil.net_io_counters()
        indirilen = ag.bytes_recv // (1024**2)
        yuklenen = ag.bytes_sent // (1024**2)
        self.konuş(f"Bu oturumda {indirilen} MB indirildi, {yuklenen} MB yüklendi.")

    # ══════════════════════════════════════════
    #  YENİ YETENEKLER
    # ══════════════════════════════════════════

    def ses_seviyesi_ayarla(self, yuzde: int):
        """Sistem sesini ayarla (pycaw kullanarak)"""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(yuzde / 100, None)
            self.konuş(f"Ses seviyesi yüzde {yuzde} yapıldı.")
        except Exception as e:
            print(f"Ses hatası: {e}")
            self.konuş("Ses seviyesi ayarlanamadı.")

    def parlaklik_ayarla(self, yuzde: int):
        """Ekran parlaklığını ayarla"""
        try:
            sbc.set_brightness(yuzde)
            self.konuş(f"Parlaklık yüzde {yuzde} yapıldı.")
        except Exception as e:
            print(f"Parlaklık hatası: {e}")
            self.konuş("Parlaklık ayarlanamadı.")

    def wikipedia_ara(self, sorgu: str):
        """Wikipedia'da ara ve özetle"""
        try:
            print(f"📖 Wikipedia: {sorgu} araştırılıyor...")
            ozet = wikipedia.summary(sorgu, sentences=2)
            self.konuş(ozet)
        except wikipedia.exceptions.DisambiguationError as e:
            self.konuş(f"Birden fazla {sorgu} bulundu. Lütfen daha spesifik söyleyin.")
        except Exception:
            self.konuş(f"{sorgu} hakkında bilgi bulamadım.")

    def cevir(self, metin: str, hedef: str = 'en'):
        """Ollama kullanarak çevir (translategemma öncelikli)"""
        if not self.mevcut_ollama_modeller:
            self.konuş("Çeviri için Ollama yüklü olmalı.")
            return
            
        try:
            dil_adi = "İngilizce"
            if hedef == 'de': dil_adi = 'Almanca'
            elif hedef == 'fr': dil_adi = 'Fransızca'
            elif hedef == 'ru': dil_adi = 'Rusça'
            
            # Çeviri için özel model seçimi
            ceviri_modeli = self.model
            for m in self.mevcut_ollama_modeller:
                if 'translategemma' in m.lower():
                    ceviri_modeli = m
                    break
            
            prompt = f"Şu metni sadece {dil_adi} diline çevir, açıklama yapma, sadece metni ver: {metin}"
            print(f"🌍 Çevriliyor ({ceviri_modeli}): {metin} -> {dil_adi}")
            sonuc = self.ollama_sor(prompt, 
                                   sistem="Sen profesyonel bir çevirmensin. Sadece istenen dildeki karşılığını ver.",
                                   ozel_model=ceviri_modeli)
            self.konuş(f"Çevirisi şöyle: {sonuc}")
        except Exception:
            self.konuş("Çeviri yapılamadı.")

    def doviz_bilgisi(self, tip: str = "dolar"):
        """Dolar/Euro bilgisi getir (Google Scraper)"""
        try:
            url = f"https://www.google.com/search?q={tip}+kaç+tl"
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers)
            # Basit regex ile fiyatı bul (Örn: "1 Dolar = 32,50 Türk Lirası")
            match = re.search(r'(\d+,\d+)\s+Türk Lirası', r.text)
            if match:
                fiyat = match.group(1)
                self.konuş(f"Şu an 1 {tip} yaklaşık {fiyat} Türk Lirası.")
            else:
                self.konuş(f"{tip} fiyatını şu an getiremiyorum.")
        except Exception:
            self.konuş("Döviz bilgisi alınamadı.")

    def ekran_goruntusu_al(self):
        """Ekran görüntüsü al"""
        try:
            dosya = Path.home() / "Desktop" / f"ekran_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            pyautogui.screenshot(str(dosya))
            self.konuş(f"Ekran görüntüsü masaüstüne kaydedildi.")
        except Exception:
            subprocess.Popen("snippingtool.exe")
            self.konuş("Ekran alıntısı aracı açıldı.")

    # ══════════════════════════════════════════
    #  GELİŞMİŞ YETENEKLER
    # ══════════════════════════════════════════

    def pano_kopyala(self, metin: str):
        """Panoya metin kopyala"""
        try:
            subprocess.run(['clip'], input=metin.encode('utf-8'), check=True)
            self.konuş("Metin panoya kopyalandı.")
        except Exception:
            self.konuş("Panoya kopyalanamadı.")

    def sifre_uret(self, uzunluk: int = 16):
        """Rastgele güvenli şifre üret ve hafızaya al"""
        import string, random
        karakterler = string.ascii_letters + string.digits + "!@#$%&*"
        sifre = ''.join(random.choice(karakterler) for _ in range(uzunluk))
        self.son_sifre = sifre # Hafızaya al
        
        print(f"🔑 Şifre: {sifre}")
        try:
            # Panoya kopyala
            subprocess.run(['clip'], input=sifre.encode('utf-8'), check=True)
            self.konuş(f"{uzunluk} karakterlik şifre oluşturuldu, kopyalandı.")
            
            # Hafif gecikme ile yapıştır
            threading.Timer(0.5, lambda: self.sifreyi_yapistir(konus=False)).start()
        except Exception as e:
            print(f"Şifre hatası: {e}")
            self.konuş(f"Şifre oluşturuldu: {sifre}")

    def sifreyi_yapistir(self, konus=True):
        """Hafızadaki son şifreyi ekrana yapıştır"""
        if not self.son_sifre:
            if konus: self.konuş("Henüz bir şifre oluşturulmadı.")
            return

        try:
            if HAS_EXTRA_MODULES:
                import pyautogui
                # Panodan bağımsız doğrudan yazdır (daha güvenli)
                pyautogui.typewrite(self.son_sifre)
                if konus: self.konuş("Şifre yazdırıldı.")
            else:
                # Pano üzerinden dene
                subprocess.run(['clip'], input=self.son_sifre.encode('utf-8'), check=True)
                if konus: self.konuş("Şifre panoda, yapıştırabilirsiniz.")
        except Exception as e:
            print(f"Yapıştırma hatası: {e}")
            if konus: self.konuş("Şifre yazılamadı.")

    def matematik_hesapla(self, ifade: str):
        """Matematik hesapla"""
        try:
            temiz = re.sub(r'[^0-9+\-*/().,%^ ]', '', ifade)
            temiz = temiz.replace(',', '.').replace('^', '**').replace('%', '/100')
            sonuc = eval(temiz)
            if isinstance(sonuc, float):
                sonuc = round(sonuc, 4)
            self.konuş(f"Sonuç: {sonuc}")
        except Exception:
            if self.mevcut_ollama_modeller:
                cevap = self.ollama_sor(f"Şu matematik sorusunu çöz, sadece sonucu yaz: {ifade}",
                                        sistem="Matematik uzmanısın. Sadece sayısal sonucu ver.")
                self.konuş(cevap)
            else:
                self.konuş("Hesaplayamadım.")

    def ip_bilgisi(self):
        """Dış IP adresini göster"""
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            ip = r.json()['ip']
            self.konuş(f"Dış IP adresiniz: {ip}")
        except Exception:
            self.konuş("IP adresi alınamadı.")

    def hiz_testi(self):
        """Basit internet hız testi"""
        self.konuş("İnternet hızı test ediliyor, lütfen bekleyin.")
        try:
            baslangic = time.time()
            r = requests.get("https://speed.cloudflare.com/__down?bytes=10000000", timeout=30)
            sure = time.time() - baslangic
            boyut_mb = len(r.content) / (1024 * 1024)
            hiz = boyut_mb / sure * 8
            self.konuş(f"İndirme hızınız yaklaşık {hiz:.1f} megabit saniye.")
        except Exception:
            self.konuş("Hız testi yapılamadı.")

    def geri_sayim(self, saniye_str: str):
        """Geri sayım başlat"""
        try:
            saniye = int(re.search(r'\d+', saniye_str).group())
            self.konuş(f"{saniye} saniyelik geri sayım başladı.")
            def sayac():
                time.sleep(saniye)
                import winsound
                self.konuş("Geri sayım tamamlandı!")
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            threading.Thread(target=sayac, daemon=True).start()
        except Exception:
            self.konuş("Geri sayım başlatılamadı.")

    def gunluk_ozet(self):
        """Günlük özet ver"""
        simdi = datetime.datetime.now()
        GUNLER = ['Pazartesi','Salı','Çarşamba','Perşembe','Cuma','Cumartesi','Pazar']
        AYLAR = ['','Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık']
        gun = GUNLER[simdi.weekday()]
        tarih = f"{simdi.day} {AYLAR[simdi.month]} {simdi.year}"
        saat = simdi.strftime('%H:%M')
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        pil_txt = ""
        try:
            pil = psutil.sensors_battery()
            if pil:
                pil_txt = f" Pil yüzde {int(pil.percent)}."
        except: pass
        ozet = (f"Günaydın! Bugün {gun}, {tarih}. Saat {saat}. "
                f"İşlemci yüzde {cpu}, RAM yüzde {ram.percent} kullanımda.{pil_txt}")
        self.konuş(ozet)

    def dosya_bul(self, dosya_adi: str):
        """Masaüstü ve Belgeler'de dosya ara"""
        self.konuş(f"{dosya_adi} aranıyor.")
        bulunanlar = []
        arama_yerleri = [Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "Downloads"]
        for yer in arama_yerleri:
            if yer.exists():
                for dosya in yer.rglob(f"*{dosya_adi}*"):
                    bulunanlar.append(str(dosya))
                    if len(bulunanlar) >= 5:
                        break
        if bulunanlar:
            self.konuş(f"{len(bulunanlar)} dosya bulundu. İlk sonuç: {bulunanlar[0]}")
            for b in bulunanlar:
                print(f"  📄 {b}")
        else:
            self.konuş(f"{dosya_adi} bulunamadı.")

    def metin_ozetle(self, metin: str):
        """Ollama ile metin özetle"""
        if not self.mevcut_ollama_modeller:
            self.konuş("Özetleme için Ollama gerekli.")
            return
        cevap = self.ollama_sor(f"Şu metni 2 cümleyle özetle: {metin}",
                                sistem="Özetleme uzmanısın. Kısa ve net özetle.")
        self.konuş(cevap)

    def kod_yaz(self, aciklama: str):
        """Ollama ile kod yaz"""
        if not self.mevcut_ollama_modeller:
            self.konuş("Kod yazmak için Ollama gerekli.")
            return
        cevap = self.ollama_sor(f"Şu işi yapan Python kodu yaz: {aciklama}",
                                sistem="Python programcısısın. Temiz, çalışır kod yaz.")
        print(f"\n💻 Kod:\n{cevap}\n")
        self.konuş("Kodu ekrana yazdım, terminale bakabilirsiniz.")

    def wifi_bilgisi(self):
        """Bağlı WiFi bilgisini göster"""
        try:
            sonuc = subprocess.run(['netsh','wlan','show','interfaces'],
                                   capture_output=True, text=True, encoding='utf-8')
            for satir in sonuc.stdout.split('\n'):
                if 'SSID' in satir and 'BSSID' not in satir:
                    ag_adi = satir.split(':',1)[1].strip()
                    self.konuş(f"Bağlı olduğunuz WiFi: {ag_adi}")
                    return
            self.konuş("WiFi bağlantısı bulunamadı.")
        except Exception:
            self.konuş("WiFi bilgisi alınamadı.")

    def klasor_olustur(self, ad: str):
        """Masaüstünde klasör oluştur"""
        yol = Path.home() / "Desktop" / ad
        try:
            yol.mkdir(exist_ok=True)
            self.konuş(f"Masaüstünde {ad} klasörü oluşturuldu.")
        except Exception:
            self.konuş("Klasör oluşturulamadı.")

    def cop_kutusu_bosalt(self):
        """Geri dönüşüm kutusunu boşalt"""
        self.konuş("Geri dönüşüm kutusunu boşaltmak istediğinizden emin misiniz?")
        onay = self.dinle(zaman_asimi=5)
        if onay and 'evet' in onay:
            try:
                from ctypes import windll
                windll.shell32.SHEmptyRecycleBinW(None, None, 0x07)
                self.konuş("Geri dönüşüm kutusu boşaltıldı.")
            except Exception:
                self.konuş("Geri dönüşüm kutusu boşaltılamadı.")
        else:
            self.konuş("İptal edildi.")

    # ══════════════════════════════════════════
    #  NOT ALMA
    # ══════════════════════════════════════════

    def not_al(self, icerik: str = None):
        """Not ekle"""
        if not icerik:
            self.konuş("Not içeriğini söyleyin:")
            icerik = self.dinle(zaman_asimi=15)
            if not icerik:
                self.konuş("Not alınamadı.")
                return

        zaman = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
        not_satiri = f"[{zaman}] {icerik}\n"

        with open(NOTES_FILE, 'a', encoding='utf-8') as f:
            f.write(not_satiri)

        self.konuş(f"Not kaydedildi: {icerik}")

    def notlari_oku(self):
        """Tüm notları oku"""
        if not os.path.exists(NOTES_FILE):
            self.konuş("Henüz hiç not yok.")
            return

        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            satirlar = f.readlines()

        if not satirlar:
            self.konuş("Not defteri boş.")
            return

        son_notlar = satirlar[-5:]  # Son 5 notu oku
        self.konuş(f"Son {len(son_notlar)} not:")
        for satir in son_notlar:
            # Zaman damgasını çıkar
            temiz = re.sub(r'\[\d{2}/\d{2}/\d{4} \d{2}:\d{2}\] ', '', satir.strip())
            self.konuş(temiz)
            time.sleep(0.3)

    def notlari_temizle(self):
        """Notları temizle"""
        self.konuş("Tüm notları silmek istediğinizden emin misiniz? Evet deyin.")
        onay = self.dinle(zaman_asimi=5)
        if onay and 'evet' in onay:
            open(NOTES_FILE, 'w').close()
            self.konuş("Tüm notlar silindi.")
        else:
            self.konuş("İptal edildi.")

    # ══════════════════════════════════════════
    #  ZAMAN / TARİH
    # ══════════════════════════════════════════

    def zaman_soyle(self):
        saat = datetime.datetime.now().strftime('%H:%M')
        self.konuş(f"Saat {saat}.")

    def tarih_soyle(self):
        simdi = datetime.datetime.now()
        AYLAR = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        GUNLER = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        gun = GUNLER[simdi.weekday()]
        self.konuş(f"Bugün {gun}, {simdi.day} {AYLAR[simdi.month]} {simdi.year}.")

    def alarm_kur(self, dakika_str: str):
        """Dakika sonra hatırlatıcı"""
        try:
            dakika = int(re.search(r'\d+', dakika_str).group())
            mesaj_al = None

            def alarm_thread():
                time.sleep(dakika * 60)
                self.konuş(mesaj_al or f"{dakika} dakika doldu! Alarm!")
                # Windows bildirim sesi
                import winsound
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

            t = threading.Thread(target=alarm_thread, daemon=True)
            t.start()
            self.konuş(f"{dakika} dakika sonraya alarm kuruldu.")
        except Exception:
            self.konuş("Alarm ayarlanamadı. Kaç dakika söyleyin.")

    # ══════════════════════════════════════════
    #  WEB / ARAMA
    # ══════════════════════════════════════════

    def web_ac(self, site: str):
        """Web sitesi aç"""
        for anahtar, url in WEB_SITELERI.items():
            if anahtar in site.lower():
                webbrowser.open(url)
                self.konuş(f"{anahtar} açılıyor.")
                return

        # Google'da ara
        sorgu = site.replace(' ', '+')
        webbrowser.open(f"https://www.google.com/search?q={sorgu}")
        self.konuş(f"{site} için Google'da arama yapıyorum.")

    def youtube_ara(self, sorgu: str):
        """YouTube'da ara"""
        q = sorgu.replace(' ', '+')
        webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
        self.konuş(f"YouTube'da {sorgu} aranıyor.")

    # ══════════════════════════════════════════
    #  HAVA DURUMU
    # ══════════════════════════════════════════

    def hava_durumu(self, sehir: str = "istanbul"):
        """Hava durumu sayfasını aç"""
        webbrowser.open(f"https://www.mgm.gov.tr/tahmin/il-ve-ilceler.aspx?m={sehir}")
        self.konuş(f"{sehir} için hava durumu tarayıcıda açıldı.")

    # ══════════════════════════════════════════
    #  SİSTEM KONTROLÜ
    # ══════════════════════════════════════════

    def bilgisayar_kapat(self):
        """Bilgisayarı kapat"""
        self.konuş("Bilgisayarı kapatmak istediğinizden emin misiniz? Evet deyin.")
        onay = self.dinle(zaman_asimi=5)
        if onay and 'evet' in onay:
            self.konuş("Bilgisayar kapatılıyor. Güle güle!")
            subprocess.run(["shutdown", "/s", "/t", "10"])
        else:
            self.konuş("İptal edildi.")

    def bilgisayar_yeniden_baslat(self):
        self.konuş("Yeniden başlatmak istediğinizden emin misiniz?")
        onay = self.dinle(zaman_asimi=5)
        if onay and 'evet' in onay:
            self.konuş("Yeniden başlatılıyor.")
            subprocess.run(["shutdown", "/r", "/t", "10"])
        else:
            self.konuş("İptal edildi.")

    def dosya_ara(self, dosya_adi: str):
        """Dosya ara"""
        subprocess.Popen(f'explorer /select,"{dosya_adi}"', shell=True)
        arama = f'powershell -c "Get-ChildItem -Path C:\\ -Recurse -Name {dosya_adi} -ErrorAction SilentlyContinue | Select-Object -First 5"'
        self.konuş(f"{dosya_adi} dosyası aranıyor.")

    def komut_isle(self, metin: str) -> bool:
        """Gelen komutu analiz et ve işle"""
        if not metin:
            return True

        m = metin.lower().strip()
        kelimeler = m.split()

        # Yardımcı: Kelimenin TAM OLARAK eşleşip eşleşmediğini kontrol et
        def tam_esles(anahtar):
            """'tarih' kelimesi 'tarihi' ile eşleşMEZ, sadece 'tarih' ile eşleşir"""
            return anahtar in kelimeler

        def herhangi_esles(liste):
            """Listedeki ifadelerden biri cümlede GEÇİYORSA True"""
            return any(x in m for x in liste)

        def tam_herhangi_esles(liste):
            """Listedeki kelimelerden biri TAM KELIME olarak varsa True"""
            return any(k in kelimeler for k in liste)

        # ── Çıkış ──────────────────────────────
        if herhangi_esles(['çıkış', 'kapat asistanı', 'asistanı kapat', 'görüşürüz', 'hoşça kal', 'exit', 'quit', 'bay bay', 'güle güle', 'programı kapat']):
            self.konuş("Hoşça kalın! İyi günler.")
            return False

        # ── Zaman/Tarih ────────────────────────
        # "saat kaç" tam ifade olmalı
        elif herhangi_esles(['saat kaç', 'saat nedir', 'vakit ne', 'şu anki saat']):
            self.zaman_soyle()

        # "tarih" TEK BAŞINA veya "bugün ne, hangi gün" gibi net sorular
        elif herhangi_esles(['bugün ne', 'hangi gün', 'ayın kaçı', 'bugünün tarihi']) or \
             (tam_esles('tarih') and len(kelimeler) <= 3 and not any(x in m for x in ['tarihi', 'tarihçe', 'tarihini'])):
            self.tarih_soyle()

        # ── Sistem Bilgisi ─────────────────────
        elif herhangi_esles(['sistem bilgi', 'bilgisayar durumu', 'pc durumu']) or \
             tam_herhangi_esles(['cpu', 'ram', 'disk', 'işlemci']):
            self.sistem_bilgisi()

        elif tam_herhangi_esles(['pil', 'batarya', 'şarj']):
            self.pil_durumu()

        elif herhangi_esles(['veri kullanımı', 'bağlantı bilgi']):
            self.ag_bilgisi()

        # ── Ses Ayarla ────────────────────────
        elif 'ses' in m and any(x in m for x in ['yap', 'ayarla', 'seviye']):
            try:
                seviye = int(re.search(r'\d+', m).group())
                self.ses_seviyesi_ayarla(seviye)
            except:
                self.konuş("Hangi seviyeye ayarlayayım?")

        # ── Parlaklık Ayarla ──────────────────
        elif 'parlaklık' in m or ('ışık' in m and any(x in m for x in ['yap', 'ayarla'])):
            try:
                seviye = int(re.search(r'\d+', m).group())
                self.parlaklik_ayarla(seviye)
            except:
                self.konuş("Parlaklık yüzde kaç olsun?")

        # ── Wikipedia ─────────────────────────
        elif herhangi_esles(['kimdir', 'nedir', 'hakkında bilgi', 'wikipedia']):
            sorgu = re.sub(r'kimdir|nedir|hakkında bilgi|wikipedia|\?', '', m).strip()
            self.wikipedia_ara(sorgu)

        # ── Çeviri ────────────────────────────
        elif 'çevir' in m:
            # "merhaba'yı ingilizceye çevir" veya "çevir: nasılsın"
            hedef = 'en'
            if 'almanca' in m: hedef = 'de'
            elif 'fransızca' in m: hedef = 'fr'
            elif 'rusça' in m: hedef = 'ru'
            
            metin_to_translate = m.replace('çevir', '').replace('ingilizceye', '').replace('almancaya', '').strip()
            self.cevir(metin_to_translate, hedef)

        # ── Döviz ─────────────────────────────
        elif 'dolar' in m:
            self.doviz_bilgisi("dolar")
        elif 'euro' in m:
            self.doviz_bilgisi("euro")
        elif 'altın' in m:
            self.doviz_bilgisi("gram altın")

        # ── Uygulama Aç ───────────────────────
        elif 'aç' in m or 'başlat' in m or 'çalıştır' in m:
            # "brave aç", "steam'i aç", "notepad başlat"
            kelimeler = m.replace('ı aç', '').replace('yi aç', '').replace("'ı aç", '').replace('u aç', '')
            kelimeler = kelimeler.replace(' aç', '').replace(' başlat', '').replace(' çalıştır', '').strip()
            if kelimeler:
                self.uygulama_ac(kelimeler)

        # ── Dil Değiştirme ────────────────────
        elif self.dil == "tr" and ('ingilizce yap' in m or 'switch to english' in m or 'ingilizceye geç' in m):
            self.dil_degistir("en")
            return True
        elif self.dil == "en" and ('türkçe yap' in m or 'switch to turkish' in m or 'türkçeye geç' in m):
            self.dil_degistir("tr")
            return True

        # ── Uygulama Kapat ─────────────────────
        elif 'kapat' in m and any(x in m for x in list(UYGULAMALAR.keys()) + ['uygulama']):
            for app in UYGULAMALAR.keys():
                if app in m:
                    self.uygulama_kapat(app)
                    break
            else:
                self.konuş("Hangi uygulamayı kapatmamı istersiniz?")

        # ── Çalışan Uygulamalar ────────────────
        elif any(x in m for x in ['hangi uygulamalar', 'çalışan uygulamalar', 'açık uygulamalar']):
            self.calisan_uygulamalar()

        # ── Not Al ────────────────────────────
        elif 'not al' in m or 'not yaz' in m or 'kaydet' in m:
            # "not al: bugün toplantı var" formatı
            icerik = None
            for ayrac in ['not al:', 'not yaz:', 'kaydet:']:
                if ayrac in m:
                    icerik = m.split(ayrac, 1)[1].strip()
                    break
            self.not_al(icerik)

        elif any(x in m for x in ['notlarımı oku', 'notları oku', 'notlarım neler', 'not defteri']):
            self.notlari_oku()

        elif 'notları temizle' in m or 'notları sil' in m:
            self.notlari_temizle()

        # ── Alarm ─────────────────────────────
        elif 'alarm' in m or 'hatırlat' in m or 'dakika sonra' in m:
            self.alarm_kur(m)

        # ── Web / Arama ───────────────────────
        elif any(x in m for x in ['youtube ara', "youtube'da ara"]):
            sorgu = m.replace('youtube ara', '').replace("youtube'da ara", '').strip()
            self.youtube_ara(sorgu)

        elif any(x in m for x in ['aç youtube', 'youtubeyi aç', "youtube'u aç"]):
            webbrowser.open("https://www.youtube.com")
            self.konuş("YouTube açılıyor.")

        elif 'ara' in m and any(x in m for x in ['google', 'internette', 'web']):
            sorgu = re.sub(r'google(da|\'da|de)?|internette|web(de)?|ara', '', m).strip()
            self.web_ac(sorgu)

        elif any(x in m for x in list(WEB_SITELERI.keys())):
            for site in WEB_SITELERI.keys():
                if site in m:
                    webbrowser.open(WEB_SITELERI[site])
                    self.konuş(f"{site} açılıyor.")
                    break

        # ── Hava Durumu ───────────────────────
        elif 'hava durumu' in m:
            sehirler = ['istanbul', 'ankara', 'izmir', 'antalya', 'bursa',
                        'adana', 'konya', 'trabzon', 'samsun', 'eskişehir']
            sehir = 'istanbul'
            for s in sehirler:
                if s in m:
                    sehir = s
                    break
            self.hava_durumu(sehir)

        # ── Ekran Görüntüsü ───────────────────
        elif any(x in m for x in ['ekran görüntüsü', 'screenshot', 'ekran al']):
            self.ekran_goruntusu_al()

        # ── Şifre Üret ───────────────────────
        elif any(x in m for x in ['şifre üret', 'şifre oluştur', 'parola üret', 'şifre öğret', 'şifre süret', 'şifre süretim', 'parola yap', 'şifre yap']):
            try:
                # Metin içindeki sayıyı bul (örn: "20 karakterlik şifre üret")
                sayi_match = re.search(r'\d+', m)
                uzunluk = int(sayi_match.group()) if sayi_match else 16
            except:
                uzunluk = 16
                
            if self.overlay and hasattr(self.overlay, 'gorev_modu'):
                self.overlay.gorev_modu("ÜRETİLDİ", "#ffea00") # Sarı/Altın
            self.sifre_uret(uzunluk)

        elif any(x in m for x in ['aynı şifreyi yaz', 'şifreyi yapıştır', 'yine yaz', 'şifreyi tekrarla']):
            self.sifreyi_yapistir()

        # ── Matematik ─────────────────────────
        elif any(x in m for x in ['hesapla', 'kaç eder', 'kaçtır', 'topla', 'çarp', 'böl']):
            self.matematik_hesapla(m)

        # ── IP Bilgisi ────────────────────────
        elif any(x in m for x in ['ip adresim', 'ip nedir', 'ip bilgisi']):
            self.ip_bilgisi()

        # ── WiFi ──────────────────────────────
        elif any(x in m for x in ['wifi', 'wi-fi', 'kablosuz ağ']):
            self.wifi_bilgisi()

        # ── Hız Testi ─────────────────────────
        elif any(x in m for x in ['hız testi', 'internet hızı test', 'speed test']):
            self.hiz_testi()

        # ── Geri Sayım ────────────────────────
        elif 'geri say' in m or 'sayaç' in m:
            self.geri_sayim(m)

        # ── Günlük Özet ──────────────────────
        elif any(x in m for x in ['günlük özet', 'günaydın', 'günün özeti', 'brifing']):
            self.gunluk_ozet()

        # ── Dosya Bul ─────────────────────────
        elif any(x in m for x in ['dosya bul', 'dosya ara', 'dosyayı bul']):
            sorgu = re.sub(r'dosya bul|dosya ara|dosyayı bul', '', m).strip()
            if sorgu:
                self.dosya_bul(sorgu)
            else:
                self.konuş("Hangi dosyayı arayayım?")

        # ── Özetle ────────────────────────────
        elif 'özetle' in m:
            metin = m.replace('özetle', '').strip()
            if metin:
                self.metin_ozetle(metin)
            else:
                self.konuş("Neyi özetleyeyim?")

        # ── Kod Yaz ───────────────────────────
        elif any(x in m for x in ['kod yaz', 'program yaz', 'script yaz']):
            aciklama = re.sub(r'kod yaz|program yaz|script yaz', '', m).strip()
            if aciklama:
                self.kod_yaz(aciklama)
            else:
                self.konuş("Ne tür bir kod yazayım?")

        # ── Klasör Oluştur ────────────────────
        elif any(x in m for x in ['klasör oluştur', 'klasör yap', 'dosya oluştur', 'yeni klasör', 'dizin oluştur']):
            ad = re.sub(r'klasör oluştur|klasör yap|dosya oluştur|yeni klasör|dizin oluştur|masaüstünde|masaüstüne', '', m).strip()
            if ad:
                self.klasor_olustur(ad)
            else:
                self.konuş("Klasör adı söyleyin.")

        # ── Çöp Kutusu ───────────────────────
        elif any(x in m for x in ['çöp kutusu', 'geri dönüşüm', 'çöplüğü boşalt']):
            self.cop_kutusu_bosalt()

        # ── Panoya Kopyala ────────────────────
        elif 'kopyala' in m and 'pano' in m:
            metin = m.replace('panoya kopyala', '').replace('kopyala', '').strip()
            self.pano_kopyala(metin)

        # ── Bilgisayar Kapat/Yeniden Başlat ──
        elif any(x in m for x in ['bilgisayarı kapat', 'shutdown', 'kapat bilgisayarı']):
            self.bilgisayar_kapat()

        elif any(x in m for x in ['yeniden başlat', 'restart', 'reboot']):
            self.bilgisayar_yeniden_baslat()

        # ── Ollama Model ──────────────────────
        elif 'model değiştir' in m or 'modeli değiştir' in m or 'model seç' in m:
            for model_adi in self.mevcut_ollama_modeller:
                if model_adi in m:
                    self.model_degistir(model_adi)
                    return True
            self.konuş(f"Mevcut modeller: {', '.join(self.mevcut_ollama_modeller) if self.mevcut_ollama_modeller else 'yok'}. Hangi modeli kullanayım?")
            cevap = self.dinle()
            if cevap:
                self.model_degistir(cevap.strip())

        elif any(x in m for x in ['hangi model', 'aktif model', 'mevcut model', 'modeller neler']):
            if self.mevcut_ollama_modeller:
                self.konuş(f"Aktif model: {self.model}. Mevcut modeller: {', '.join(self.mevcut_ollama_modeller)}.")
            else:
                self.konuş("Ollama modeli yüklü değil.")

        elif 'sohbet geçmişini temizle' in m or 'geçmişi temizle' in m or 'konuşmayı sıfırla' in m:
            self.sohbet_gecmisi = []
            self.konuş("Sohbet geçmişi temizlendi.")

        # ── Yardım ───────────────────────────
        elif any(x in m for x in ['yardım', 'ne yapabilirsin', 'komutlar', 'help']):
            yardim = ("Şunları yapabilirim: "
                      "Saat, tarih ve günlük özet söylerim. "
                      "Sistem bilgisi, pil, WiFi ve IP adresi gösteririm. "
                      "Uygulama açar, kapatır ve dosya bulurum. "
                      "Not alır, alarm ve geri sayım kurarım. "
                      "Ses ve parlaklık ayarlarım. "
                      "Wikipedia'da arar, çeviri yapar, matematik hesaplarım. "
                      "Şifre üretir, internet hızı test eder, kod yazarım. "
                      "Klasör oluşturur, çöp kutusunu boşaltırım. "
                      "Döviz ve altın fiyatı söylerim. "
                      "YouTube, Google ve web sitesi açarım. "
                      "Ollama modelleriyle sohbet ederim.")
            self.konuş(yardim)

        # ── Ollama'ya Sor (varsayılan) ────────
        else:
            if self.mevcut_ollama_modeller:
                cevap = self.ollama_sor(metin)
                self.konuş(cevap)
            else:
                self.konuş("Ollama çalışmıyor. Sistem komutu veya yardım deyin.")

        return True

    # ══════════════════════════════════════════
    #  ANA DÖNGÜ
    # ══════════════════════════════════════════

    def calistir(self):
        """Ana asistan döngüsü"""
        print("\n" + "═"*60)
        print("  Konuşmaya başlayın. 'Çıkış' demek için: 'çıkış' deyin")
        print("═"*60 + "\n")

    # ══════════════════════════════════════════
    #  ANA DÖNGÜ (Wake Word Desteği ile)
    # ══════════════════════════════════════════

    def calistir(self):
        """Asistanı uyandırma kelimesi ile çalıştır"""
        print("\n" + "═"*60)
        print(f"  {ASISTAN_ADI} Uyku Modunda... ('Aria' veya 'Arya' diyerek uyandırın)")
        print("═"*60 + "\n")

        uyandirma_kelimeleri = ["aria", "arya", "hadi aria", "hadi arya", "merhaba aria", "merhaba arya", "alo aria"]

        while True:
            try:
                # 1. Aşama: Uyandırma Kelimesini Dinle
                metin = self.dinle(zaman_asimi=None) # Pasif dinleme
                
                if metin:
                    # Uyandırma kelimesi kontrolü
                    uyandi = False
                    for kelime in uyandirma_kelimeleri:
                        if kelime in metin:
                            uyandi = True
                            break
                    
                    if uyandi:
                        # UYANDI!
                        self.konuş("Evet, dinliyorum?")
                        
                        # 2. Aşama: Komut Dinle
                        komut = self.dinle(zaman_asimi=7)
                        if komut:
                            devam = self.komut_isle(komut)
                            if not devam:
                                break
                        else:
                            self.konuş("Sizi duyamadım, tekrar uyku moduna geçiyorum.")
                    
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.konuş("Görüşürüz!")
                break
            except Exception as e:
                print(f"Hata: {e}")
                time.sleep(1)


# ══════════════════════════════════════════
#  BAŞLATICI
# ══════════════════════════════════════════

def main():
    asistan = SesliAsistan()
    asistan.calistir()


if __name__ == "__main__":
    main()
