"""Basit bir çalıştırılabilir demo.

Bu dosyayı çalıştırdığınızda kısa bir sesli mesaj ve sistem bilgisi
çıktısı alırsınız. Amacı kullanıcıya projenin hemen bir örnek
şekilde nasıl çalıştığını gösterme.

Kullanım:
    python demo.py

"""

import time
import threading
from sesli_asistan import SesliAsistan

def basit_animasyon(mesaj, sure=3):
    """Basit bir terminal animasyonu gösterir."""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    for _ in range(sure * 10):
        print(f"\r{spinner[i % len(spinner)]} {mesaj}", end='', flush=True)
        time.sleep(0.1)
        i += 1
    print(f"\r✓ {mesaj} tamamlandı!")

def konusma_animasyonu(mesaj, sure=2):
    """Konuşma sırasında basit bir animasyon."""
    print(f"\n🎤 {mesaj}")
    for i in range(sure * 5):
        print(".", end='', flush=True)
        time.sleep(0.2)
    print(" ✓")

if __name__ == '__main__':
    print("🎙️ Türkçe Sesli Asistan Demo Başlatılıyor...")
    
    # Animasyon ile başlatma
    basit_animasyon("Asistan yükleniyor", 2)
    
    # Asistanı başlat; bu otomatik olarak bir "Merhaba" mesajı
    # konuşur ve Ollama kontrolü yapar.
    asistan = SesliAsistan()
    
    # Demoyu devam ettirecek birkaç komut çağırıyoruz
    basit_animasyon("Sistem bilgisi alınıyor", 1)
    konusma_animasyonu("Aria konuşuyor: Bu basit demo programıdır", 1)
    asistan.konuş("Bu basit demo programıdır. Sistem bilgisi okuyorum.")
    asistan.sistem_bilgisi()
    
    # Son olarak kullanıcıya nasıl komut verebileceğini hatırlat
    basit_animasyon("Demo tamamlanıyor", 1)
    konusma_animasyonu("Aria konuşuyor: Ana dosyayı çalıştırmak için...", 1)
    asistan.konuş("Ana dosyayı çalıştırmak için python sesli_asistan.py yazabilirsiniz.")
    
    print("\n🎉 Demo tamamlandı! Gerçek asistanı denemek için 'python sesli_asistan.py' çalıştırın.")
