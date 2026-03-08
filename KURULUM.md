# 🎙️ Türkçe Sesli Asistan — Kurulum Rehberi

## ⚡ Hızlı Kurulum

### 1. Python Kütüphanelerini Yükle
```bash
pip install SpeechRecognition pyttsx3 requests pyaudio psutil pyautogui pycaw screen-brightness-control wikipedia
```

> **PyAudio sorunu yaşarsanız:**
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 2. Ollama Kur (AI için)
- https://ollama.com adresinden indirin
- Terminal açın:
```bash
ollama pull llama3
# veya Türkçe için:
ollama pull mistral
```

### 3. Çalıştır
```bash
python sesli_asistan.py
```

---

## 🗣️ Sesli Komutlar

| Komut | Ne Yapar |
|-------|----------|
| "saat kaç" | Saati söyler |
| "bugün hangi gün" | Tarihi söyler |
| "günaydın" / "günlük özet" | Tarih, saat, CPU, RAM, pil özeti |
| "sistem bilgisi" | CPU/RAM/Disk durumu |
| "pil durumu" | Pil seviyesi |
| "wifi bilgisi" | Bağlı WiFi adını gösterir |
| "ip adresim" | Dış IP adresini söyler |
| "hız testi" | İnternet indirme hızını ölçer |
| "brave aç" | Brave tarayıcı açar |
| "steam aç" | Steam açar |
| "discord aç" | Discord açar |
| "notepad aç" | Not defteri açar |
| "chrome kapat" | Chrome'u kapatır |
| "not al: toplantı var" | Not kaydeder |
| "notlarımı oku" | Son notları okur |
| "20 dakika sonra hatırlat" | Alarm kurar |
| "30 saniye geri say" | Geri sayım başlatır |
| "sesi %50 yap" | Sistem sesini ayarlar |
| "parlaklığı %80 yap" | Ekran parlaklığını ayarlar |
| "YouTube'da müzik ara" | YouTube araması |
| "hava durumu istanbul" | Hava sayfası açar |
| "Atatürk kimdir" | Wikipedia'dan bilgi getirir |
| "merhaba ingilizceye çevir" | Ollama ile çeviri yapar |
| "dolar ne kadar" | Güncel döviz kuru |
| "altın fiyatı" | Altın fiyatını söyler |
| "25 çarpı 13 hesapla" | Matematik hesaplar |
| "şifre üret" | 16 haneli güvenli şifre üretir |
| "dosya ara rapor" | Masaüstü/Belgeler/İndirilenler'de arar |
| "klasör oluştur projelerim" | Masaüstünde klasör açar |
| "çöp kutusunu boşalt" | Geri dönüşüm kutusunu temizler |
| "ekran görüntüsü" | Ekran görüntüsü alır |
| "kod yaz fibonacci hesapla" | Python kodu yazar |
| "hangi modeller var" | Ollama modellerini listeler |
| "model değiştir mistral" | Modeli değiştirir |
| "geçmişi temizle" | Sohbet sıfırlar |
| "çıkış" | Asistanı kapatır |
| *Herhangi bir soru* | Ollama'ya sorar, sesli cevap verir |

---

## ⚙️ Yapılandırma

`sesli_asistan.py` dosyasının üst kısmını düzenleyin:

```python
DEFAULT_MODEL = "llama3"     # Varsayılan Ollama modeli
ASISTAN_ADI = "Aria"         # Asistanın adı
NOTES_FILE = "..."           # Not dosyası konumu
```

### Yeni Uygulama Eklemek
`UYGULAMALAR` sözlüğüne ekleyin:
```python
"uygulama adı": r"C:\Program Files\...\app.exe",
```

### Yeni Web Sitesi Eklemek
`WEB_SITELERI` sözlüğüne ekleyin:
```python
"twitch": "https://www.twitch.tv",
```

---

## 🔊 Türkçe Ses (TTS) Kurulumu

Windows'ta Türkçe ses için:
1. **Ayarlar → Zaman ve Dil → Konuşma**
2. Türkçe konuşma paketi indir
3. Asistan otomatik algılar

---

## 🚀 Özellikler

- ✅ Türkçe ses tanıma (Google STT)
- ✅ Türkçe ses sentezi (pyttsx3)
- ✅ Ollama entegrasyonu (tüm modeller)
- ✅ Sohbet geçmişi hafızası
- ✅ 25+ uygulama desteği
- ✅ Not alma ve okuma
- ✅ Alarm/hatırlatıcı
- ✅ Sistem izleme (CPU/RAM/Disk/Pil)
- ✅ Web arama ve site açma
- ✅ Uygulama aç/kapat
- ✅ Çalışan uygulamaları listele
- ✅ Ekran görüntüsü
- ✅ Hava durumu

---

## ❓ Sorun Giderme

**"Mikrofon çalışmıyor"** → Windows Ayarlar > Gizlilik > Mikrofon izinleri kontrol et

**"PyAudio yüklenmiyor"** → Python 3.11 kullanıyorsanız: `pipwin install pyaudio`

**"Ses tanıma çalışmıyor"** → İnternet bağlantısı gerekli (Google STT)

**"Ollama bağlanamıyor"** → `ollama serve` komutunu çalıştırın
