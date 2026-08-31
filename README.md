# AI-DLRC

Yapay Zeka Tabanli Deprem Sonrasi Akilli Lojistik, Rota ve Acil Iletisim Sistemi.

## Proje yapisi

```text
AI-DLRC/
├── data/       # Deprem, yol, depo, ekip ve ihtiyac verileri
├── src/        # Uygulama ve algoritma kaynak kodlari
├── models/     # Egitilmis yapay zeka modelleri
├── results/    # Rota, tahmin ve rapor ciktilari
└── README.md
```

## Hedeflenen moduller

- Hasar ve ihtiyac verilerinin toplanmasi
- Acil yardim taleplerinin onceliklendirilmesi
- Depo ve ekipler icin akilli gorevlendirme
- Yol durumu ve risklere gore dinamik rota planlama
- Acil durum ekipleri arasinda iletisim ve durum takibi
- Model tahminleri ile operasyon raporlarinin uretilmesi

## Gelistirme sirasi

1. Veri formatlarini ve ornek veri setini tanimla.
2. Temel rota planlama algoritmasini kur.
3. Ihtiyac onceliklendirme modelini egit.
4. Dinamik rota ve lojistik akislarini birlestir.
5. Acil iletisim panelini ve raporlama ciktilarini ekle.

## Not

`data`, `models` ve `results` klasorlerindeki buyuk veya hassas dosyalar surum kontrolune alinmadan once `.gitignore` kurallariyla korunmalidir.
