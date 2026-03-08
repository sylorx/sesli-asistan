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
from pathlib import Path

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

    # Medya
    "spotify":       r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "media player":  "wmplayer.exe",

    # Geliştirme
    "vscode":        r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code":       r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio": r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",

    # İletişim
    "zoom":          r"C:\Users\{user}\AppData\Roaming\Zoom\bin\Zoom.exe",
    "teams":         r"C:\Users\{user}\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "whatsapp":      r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
    "telegram":      r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe",

    # Diğer
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

        # TTS Motoru
        self.tts = pyttsx3.init()
        self._tts_ayarla()

        # STT
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        # Durum
        self.dinliyor = True
        self.model = DEFAULT_MODEL
        self.sohbet_gecmisi = []
        self.mevcut_ollama_modeller = []

        # Sistem promptu
        self.sistem_promptu = f"""Sen {ASISTAN_ADI} adlı Türkçe konuşan bir sesli asistansın.
Kullanıcının bilgisayarını yönetmesine yardımcı oluyorsun.
Cevaplarını kısa, net ve Türkçe ver. Sesli okunacak olduğundan 
emoji, madde işareti veya özel karakter kullanma. Sadece düz metin yaz.
Tarih/saat bilgisi: {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}"""

        self.konuş(f"Merhaba! Ben {ASISTAN_ADI}. Nasıl yardımcı olabilirim?")
        self._ollama_kontrol()

    def _tts_ayarla(self):
        """Türkçe ses ayarları"""
        sesler = self.tts.getProperty('voices')
        turkce_ses = None
        for ses in sesler:
            if 'turkish' in ses.name.lower() or 'tr' in ses.id.lower() or 'türk' in ses.name.lower():
                turkce_ses = ses.id
                break

        if turkce_ses:
            self.tts.setProperty('voice', turkce_ses)
        else:
            # İngilizce ses ama yine de çalışır
            if sesler:
                self.tts.setProperty('voice', sesler[0].id)

        self.tts.setProperty('rate', 175)    # Konuşma hızı
        self.tts.setProperty('volume', 0.95) # Ses seviyesi

    def konuş(self, metin: str):
        """Metni sesli oku"""
        print(f"\n🔊 {ASISTAN_ADI}: {metin}\n")
        # Markdown/özel karakterleri temizle
        temiz = re.sub(r'[*_`#\[\]()>~|]', '', metin)
        temiz = re.sub(r'\n+', '. ', temiz)
        self.tts.say(temiz)
        self.tts.runAndWait()

    def dinle(self, zaman_asimi: int = 7, tekrar: bool = True) -> str | None:
        """Mikrofondan ses al"""
        with sr.Microphone() as kaynak:
            print("🎤 Dinliyorum...")
            self.recognizer.adjust_for_ambient_noise(kaynak, duration=0.5)
            try:
                ses = self.recognizer.listen(kaynak, timeout=zaman_asimi, phrase_time_limit=30)
                print("⚙️  İşleniyor...")
                metin = self.recognizer.recognize_google(ses, language='tr-TR')
                print(f"👤 Sen: {metin}")
                return metin.lower()
            except sr.WaitTimeoutError:
                if tekrar:
                    print("⏱️  Ses algılanmadı.")
                return None
            except sr.UnknownValueError:
                print("❓ Anlaşılamadı.")
                return None
            except sr.RequestError as e:
                print(f"❌ Google STT hatası: {e}")
                self.konuş("İnternet bağlantısı yok, offline moda geçiyorum.")
                return None

    # ══════════════════════════════════════════
    #  OLLAMA ENTEGRASYONU
    # ══════════════════════════════════════════

    def _ollama_kontrol(self):
        """Ollama bağlantısını kontrol et"""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                data = r.json()
                self.mevcut_ollama_modeller = [m['name'].split(':')[0] for m in data.get('models', [])]
                print(f"✅ Ollama bağlı. Modeller: {', '.join(self.mevcut_ollama_modeller)}")
                if self.mevcut_ollama_modeller:
                    self.model = self.mevcut_ollama_modeller[0]
                    self.konuş(f"Ollama bağlantısı kuruldu. Aktif model: {self.model}")
                else:
                    self.konuş("Ollama bağlı ama hiç model yüklü değil. ollama pull llama3 komutunu çalıştırın.")
        except Exception:
            print("⚠️  Ollama bağlantısı yok.")
            self.konuş("Ollama şu an çalışmıyor. Sistem komutlarını kullanabilirsiniz.")

    def ollama_sor(self, soru: str, sistem: str = None) -> str:
        """Ollama'ya soru sor (streaming destekli)"""
        if not sistem:
            sistem = self.sistem_promptu

        self.sohbet_gecmisi.append({"role": "user", "content": soru})

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": sistem}] + self.sohbet_gecmisi,
            "stream": False
        }

        try:
            print(f"🤖 {self.model} düşünüyor...")
            r = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=60)
            if r.status_code == 200:
                cevap = r.json()['message']['content']
                self.sohbet_gecmisi.append({"role": "assistant", "content": cevap})
                # Geçmişi 20 mesajla sınırla
                if len(self.sohbet_gecmisi) > 20:
                    self.sohbet_gecmisi = self.sohbet_gecmisi[-20:]
                return cevap
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
            self.sohbet_gecmisi = []  # Geçmişi temizle
            self.konuş(f"Model {model_adi} olarak değiştirildi ve sohbet geçmişi temizlendi.")
        elif self.mevcut_ollama_modeller:
            benzer = [m for m in self.mevcut_ollama_modeller if model_adi in m]
            if benzer:
                self.model = benzer[0]
                self.konuş(f"Model {self.model} olarak ayarlandı.")
            else:
                self.konuş(f"Model bulunamadı. Mevcut modeller: {', '.join(self.mevcut_ollama_modeller)}")
        else:
            self.konuş("Hiç Ollama modeli yüklü değil.")

    # ══════════════════════════════════════════
    #  UYGULAMA KONTROLÜ
    # ══════════════════════════════════════════

    def uygulama_ac(self, isim: str) -> bool:
        """Uygulama aç"""
        isim_lower = isim.lower().strip()
        kullanici = os.environ.get('USERNAME', 'User')

        # Direkt eşleşme
        for anahtar, yol in UYGULAMALAR.items():
            if anahtar in isim_lower or isim_lower in anahtar:
                yol = yol.replace('{user}', kullanici)

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

    def ekran_goruntusu_al(self):
        """Ekran görüntüsü al"""
        try:
            import pyautogui
            dosya = Path.home() / "Desktop" / f"ekran_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            pyautogui.screenshot(str(dosya))
            self.konuş(f"Ekran görüntüsü masaüstüne kaydedildi.")
        except ImportError:
            # pyautogui yoksa Windows snipping tool aç
            subprocess.Popen("snippingtool.exe")
            self.konuş("Ekran alıntısı aracı açıldı.")

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

    def ses_ayarla(self, seviye: str):
        """Sistem ses seviyesini ayarla"""
        try:
            yuzde = int(re.search(r'\d+', seviye).group())
            yuzde = max(0, min(100, yuzde))
            # Windows ses kontrolü (nircmd veya powershell)
            subprocess.run(
                f'powershell -c "(New-Object -com wscript.shell).SendKeys([char]173)"',
                shell=True)  # Mute/unmute
            self.konuş(f"Ses yüzde {yuzde} olarak ayarlanmaya çalışıldı.")
        except Exception:
            self.konuş("Ses ayarlanamadı.")

    def dosya_ara(self, dosya_adi: str):
        """Dosya ara"""
        subprocess.Popen(f'explorer /select,"{dosya_adi}"', shell=True)
        arama = f'powershell -c "Get-ChildItem -Path C:\\ -Recurse -Name {dosya_adi} -ErrorAction SilentlyContinue | Select-Object -First 5"'
        self.konuş(f"{dosya_adi} dosyası aranıyor.")

    # ══════════════════════════════════════════
    #  KOMUT İŞLEYİCİ
    # ══════════════════════════════════════════

    def komut_isle(self, metin: str) -> bool:
        """Gelen komutu analiz et ve işle"""
        if not metin:
            return True

        m = metin.lower().strip()

        # ── Çıkış ──────────────────────────────
        if any(x in m for x in ['çıkış', 'kapat asistanı', 'görüşürüz', 'hoşça kal', 'exit', 'quit']):
            self.konuş("Hoşça kalın! İyi günler.")
            return False

        # ── Zaman/Tarih ────────────────────────
        elif any(x in m for x in ['saat kaç', 'saat nedir', 'ne zaman']):
            self.zaman_soyle()

        elif any(x in m for x in ['tarih', 'bugün ne', 'hangi gün', 'ayın kaçı']):
            self.tarih_soyle()

        # ── Sistem Bilgisi ─────────────────────
        elif any(x in m for x in ['sistem bilgi', 'cpu', 'ram', 'disk', 'bilgisayar durumu']):
            self.sistem_bilgisi()

        elif any(x in m for x in ['pil', 'batarya', 'şarj']):
            self.pil_durumu()

        elif any(x in m for x in ['ağ', 'internet hızı', 'bağlantı bilgi', 'veri kullanımı']):
            self.ag_bilgisi()

        # ── Uygulama Aç ───────────────────────
        elif 'aç' in m or 'başlat' in m or 'çalıştır' in m:
            # "brave aç", "steam'i aç", "notepad başlat"
            kelimeler = m.replace('ı aç', '').replace('yi aç', '').replace("'ı aç", '')
            kelimeler = kelimeler.replace(' aç', '').replace(' başlat', '').replace(' çalıştır', '').strip()
            if kelimeler:
                self.uygulama_ac(kelimeler)

        # ── Uygulama Kapat ─────────────────────
        elif 'kapat' in m and any(x in m for x in list(UYGULAMALAR.keys()) + ['uygulama']):
            for app in UYGULAMALAR.keys():
                if app in m:
                    self.uygulama_kapat(app)
                    break

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
                      "Saat ve tarih söylerim, sistem bilgisi veririm, "
                      "uygulama açar ve kapatırım, not alırım, "
                      "web sitesi açarım, YouTube'da ararım, "
                      "hava durumuna bakarım, alarm kurarım, "
                      "Ollama modelleriyle sohbet ederim. "
                      "Bir şeyler sormak için sadece konuşun!")
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

        devam = True
        while devam:
            try:
                metin = self.dinle()
                if metin:
                    devam = self.komut_isle(metin)
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
