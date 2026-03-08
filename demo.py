"""Basit bir çalıştırılabilir demo.

Bu dosyayı çalıştırdığınızda kısa bir sesli mesaj ve sistem bilgisi
çıktısı alırsınız. Amacı kullanıcıya projenin hemen bir örnek
şekilde nasıl çalıştığını gösterme.

Kullanım:
    python demo.py

"""

from sesli_asistan import SesliAsistan

if __name__ == '__main__':
    # Asistanı başlat; bu otomatik olarak bir "Merhaba" mesajı
    # konuşur ve Ollama kontrolü yapar.
    asistan = SesliAsistan()
    
    # Demoyu devam ettirecek birkaç komut çağırıyoruz
    asistan.konuş("Bu basit demo programıdır. Sistem bilgisi okuyorum.")
    asistan.sistem_bilgisi()
    
    # Son olarak kullanıcıya nasıl komut verebileceğini hatırlat
    asistan.konuş("Ana dosyayı çalıştırmak için python sesli_asistan.py yazabilirsiniz.")
