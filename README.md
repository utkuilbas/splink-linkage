# Splink Record Linkage Projesi

Bu proje, Splink kütüphanesi kullanarak kişi kayıtları üzerinde record linkage (kayıt bağlama) işlemi gerçekleştiren bir Python uygulamasıdır. DuckDB ile hızlı veri işleme ve çoklu karşılaştırma algoritmaları kullanarak duplicate kayıtları tespit eder.

## 🚀 Özellikler

- **DuckDB entegrasyonu** ile hızlı veri işleme
- **Çoklu karşılaştırma algoritmaları** (Jaro-Winkler, Levenshtein)
- **Otomatik model eğitimi** ve parametre optimizasyonu
- **CSV export** desteği
- **Konfigürasyon tabanlı** esnek yapı

## 🔧 Kurulum

1. **Repoyu klonlayın:**
```bash
git clone https://github.com/utkuilbas/splink-linkage.git
```

2. **Sanal ortam oluşturun (önerilen):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Gerekli kütüphaneleri yükleyin:**
```bash
pip install -r requirements.txt
```


### Temel Kullanım
```bash
python main.py
```

Program otomatik olarak:
1. Demo veri setini indirir (1000 kayıt)
2. DuckDB veritabanını kurar
3. Record linkage işlemini gerçekleştirir
4. Sonuçları analiz eder
5. CSV formatında raporlar oluşturur


### Dosyalar
- **`high_confidence_linkages.csv`** - Yüksek güvenirlikli eşleşmeler
- **`all_linkage_results.csv`** - Tüm linkage sonuçları
- **`linkage_database.duckdb`** - DuckDB veritabanı


### Yaygın Hatalar

**Import Error**
   - `pip install -r requirements.txt` komutunu tekrar çalıştırın
   - Python versiyonunu kontrol edin (3.8+ gerekli, 3.12 altı, tercihen 3.11)

## 📚 Kaynaklar

- [Splink Documentation](https://moj-analytical-services.github.io/splink/)
- [DuckDB Documentation](https://duckdb.org/docs/)

