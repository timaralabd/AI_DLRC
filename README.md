# AI-DLRC

Yapay zekâ tabanlı deprem sonrası akıllı lojistik, risk analizi ve acil durum rota planlama projesi.

Proje; deprem verilerini, hasar bilgilerini ve yol ağlarını kullanarak etkilenen bölgeleri analiz etmeyi, kurtarma önceliklerini belirlemeyi ve ekipler için uygun rotalar oluşturmayı hedefler.

Önceliklendirme akışında artık `scikit-learn` tabanlı bir `RandomForestRegressor` bulunur. Model; kişi sayısı, yaralı sayısı, aciliyet, konum ve ihtiyaç türlerinden özellik çıkarır. İlk eğitim, mevcut uzman kural skorlarını bootstrap etiketi olarak kullanır; gerçek operasyon sonuçları biriktikçe bu etiketlerle yeniden eğitilmelidir.

Model ayrıca `data/turkey_syria_earthquake_risk.json` içindeki gerçek USGS olaylarından her talebe en yakın depremi bulur ve uzaklık, büyüklük, derinlik ve risk skorunu AI özelliklerine ekler.

Gerçek sonuçlarla yeniden eğitim için `requests` listesinde her kayda `observed_priority` alanı eklenir ve `train_from_labeled_data()` çağrılır. Eğitim çıktısı `models/priority_model.joblib`, okunabilir metadata ise aynı klasördeki JSON dosyasıdır.

AI modelini web paneli olmadan eğitmek için:

```powershell
python -m src.ai_priority --input data/emergency_requests.json --output models/priority_model.joblib
```

Projenin ana giriş noktası artık kökteki `main.py` dosyasıdır:

```powershell
python main.py
```

Komut ayrıca AI öncelik sıralamasını `results/ai_priority_ranked.json` dosyasına yazar.

AI ekip önerileri de `results/ai_team_assignments.json` dosyasına yazılır.
Model ölçümleri ayrıca `results/model_evaluation.json` dosyasına yazılır.

İlk uzman etiketleri `data/priority_training.json` dosyasındadır. Bu dosya gerçek saha sonucu değildir; saha doğrulaması geldikçe `observed_priority` değerleri güncellenmelidir. Dört veya daha fazla etiketli kayıt olduğunda `main.py` veriyi eğitim/test olarak ayırır ve test `MAE`, `R2` ve öncelik sıralama doğruluğunu raporlar. Daha az kayıtta sahte metrik üretmek yerine veri yetersizliği bildirir.

Doğrulanmış ekip sonuçları `data/team_outcomes.json` dosyasına eklenir:

```json
{
	"request_id": "REQ-001",
	"team_id": "TEAM-ALPHA",
	"team_success": true,
	"intervention_minutes": 42,
	"rescued_people": 18,
	"resolved": true
}
```

Bu alanlarla ekip başarısı, müdahale süresi, kurtarılan kişi sayısı ve çözülme durumu ölçülebilir.

Gerçek sonuçları komut satırından kaydetmek için:

```powershell
python -m src.record_outcome --request-id REQ-001 --priority 92
python -m src.record_outcome --request-id REQ-001 --team-id TEAM-ALPHA --team-success --intervention-minutes 42 --rescued-people 18 --resolved
```

Gerçek saha verisi yokken yalnızca geliştirme akışını denemek için açıkça sentetik olarak işaretlenmiş veri üretilebilir:

```powershell
python -m src.generate_simulation
python main.py --input data/simulated_requests.json --training-data data/simulated_priority_training.json --team-outcomes data/simulated_team_outcomes.json --model models/simulated_priority_model.joblib --output results/simulated_priority_ranked.json
```

Bu komutun metrikleri gerçek saha başarısı olarak yorumlanmamalıdır; sentetik verinin teknik testidir.
İlk komut `observed_priority` değerini, ikinci komut ekip operasyon sonucunu günceller. Ardından `python main.py` ile modeller yeniden eğitilir.

`main.py` çalışmadan önce bu iki etiket dosyasını doğrular. Eksik alan, negatif süre/kişi sayısı veya sayısal olmayan değer varsa model eğitimi başlatılmaz.

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
- `ai_priority.py`: Acil talepler için makine öğrenmesi tabanlı öncelik modeli.

## Kurulum ve bağımlılıklar

Python 3.10 veya daha yeni bir sürüm önerilir.

```bash
python -m venv .venv

# Windows PowerShell ortamını etkinleştirme
.venv\Scripts\Activate.ps1

pip install requests networkx osmnx
```

Bağımlılıkları proje dosyasından kurmak için:

```bash
pip install -r requirements.txt
```

## Kullanım

Hasar verilerini Copernicus EMS kaynağından almak için:

```bash
python src/prepare_damage_data.py
```

Bu komut API üst verilerini `data/damage/EMSR648_metadata.json` dosyasına kaydeder. Uygun bir vektör paketi bulunursa paketi indirir ve `data/damage/extracted/` altına çıkarır.

Diğer analiz ve rota modülleri `src/` altında bağımsız Python modülleri olarak bulunur. Çalıştırmadan önce ilgili modülü ve kullandığı veri dosyalarını kontrol edin.

Canlı operasyon panelini başlatmak için:

```powershell
.\.venv\Scripts\Activate.ps1
python src/dashboard_server.py
```

Paneli tarayıcıda `http://127.0.0.1:8765` adresinden açabilirsiniz. Panel; acil talepleri, ekip durumlarını, atamaları, operasyon kayıtlarını ve öncelikli rota üretimini tek ekranda sunar.

Temel API uçları:

- `GET /api/requests`: Önceliklendirilmiş acil talepleri döndürür.
- `GET /api/teams`: Ekip listesini ve durumlarını döndürür.
- `GET /api/dispatch`: Güncel ekip atama planını döndürür.
- `GET /api/operations`: Son operasyon hareketlerini döndürür.
- `POST /api/requests`: Yeni acil talep oluşturur.
- `POST /api/dispatch/next`: En öncelikli bekleyen talebe hazır ekip atar.

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
