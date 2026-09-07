# AI-DLRC

Yapay zekâ tabanlı deprem sonrası akıllı lojistik, risk analizi ve acil durum rota planlama projesi.

Proje; deprem verilerini, hasar bilgilerini ve yol ağlarını kullanarak etkilenen bölgeleri analiz etmeyi, kurtarma önceliklerini belirlemeyi ve ekipler için uygun rotalar oluşturmayı hedefler.

## Proje yapısı

```text
AI-DLRC/
├── data/       # Deprem, risk ve yol ağı verileri
├── src/        # Analiz, önceliklendirme ve rota modülleri
├── models/     # Model dosyalari
├── results/    # Üretilen analiz ve rota çıktıları
└── README.md
```

## Kaynak modülleri

- `earthquake_data.py`: Deprem verilerini alma ve JSON biçiminde kaydetme.
- `prepare_damage_data.py`: Copernicus EMS API'sinden hasar verisi indirme ve arşivleri çıkarma.
- `earthquake_risk.py`: Deprem verilerini kullanarak risk analizi yapma.
- `affected_area.py`: Etkilenen alanları ve mesafeleri hesaplama.
- `rescue_priority.py`: Kurtarma ve yardım taleplerini önceliklendirme.
- `road_network.py`: Yol ağı üzerinde temel rota işlemleri.
- `real_road_network.py`: Gerçek yol ağlarını OpenStreetMap verileriyle oluşturma.
- `disaster_route.py`: Afet koşullarına göre rota hesaplama.
- `smart_route.py`: Risk ve yol durumunu dikkate alan akıllı rota planlama.

## Kurulum ve bağımlılıklar

Python 3.10 veya daha yeni bir sürüm önerilir.

```bash
python -m venv .venv

# Windows PowerShell ortamını etkinleştirme
.venv\Scripts\Activate.ps1

pip install requests networkx osmnx
```

## Kullanım

Hasar verilerini Copernicus EMS kaynağından almak için:

```bash
python src/prepare_damage_data.py
```

Bu komut API üst verilerini `data/damage/EMSR648_metadata.json` dosyasına kaydeder. Uygun bir vektör paketi bulunursa paketi indirir ve `data/damage/extracted/` altına çıkarır.

Diğer analiz ve rota modülleri `src/` altında bağımsız Python modülleri olarak bulunur. Çalıştırmadan önce ilgili modülü ve kullandığı veri dosyalarını kontrol edin.

## Veri kaynakları

- `data/earthquakes.json`: Deprem verileri.
- `data/turkey_syria_earthquakes.json`: Türkiye-Suriye deprem verileri.
- `data/turkey_syria_earthquake_risk.json`: Risk analizi çıktıları.
- `data/*.graphml`: Yol ağı verileri.
- Copernicus EMS EMSR648: Hasar verisi ve etkinleştirme üst verileri.

## Geliştirme notları

- API'den indirilen büyük dosyalar ve üretilen çıktılar sürüm kontrolüne alınmadan önce gözden geçirilmelidir.
- `data/damage/` altında oluşan dosyaların boyutunu ve hassas veri içerip içermediğini kontrol edin.
- Yeni modüller eklenirken veri giriş ve çıkış biçimlerini README'de belgeleyin.
