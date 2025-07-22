# Historical_50K Veri Seti ile Splink Record Linkage Projesi
# Gerekli kütüphanelerin kurulumu için terminal'de şu komutları çalıştırın:
# pip install duckdb pandas splink

import pandas as pd
import duckdb
from splink.duckdb.linker import DuckDBLinker
from splink.duckdb.comparison_library import (
    exact_match,
    levenshtein_at_thresholds,
    jaro_winkler_at_thresholds,
)
import urllib.request
import os

def download_historical_data():
    # örnek veri seti
    url = "https://raw.githubusercontent.com/moj-analytical-services/splink/master/tests/datasets/fake_1000_from_splink_demos.csv"
    filename = "historical_data.csv"
    
    if not os.path.exists(filename):
        print("Veri seti indiriliyor...")
        urllib.request.urlretrieve(url, filename)
        print(f"{filename} başarıyla indirildi.")
    else:
        print(f"{filename} zaten mevcut.")
    
    return filename

def setup_duckdb_connection():
    # duckdb bağlantısı
    conn = duckdb.connect('database.duckdb')
    print("DuckDB bağlantısı kuruldu.")
    return conn

def load_data_to_duckdb(conn, csv_file):

    df = pd.read_csv(csv_file)
    
    conn.register('historical_data', df)
    
    result = conn.execute("SELECT COUNT(*) FROM historical_data").fetchone()
    print(f"DuckDB'ye {result[0]} kayıt yüklendi.")
    
    return df

def prepare_splink_settings():
    # konfigürasyon
    settings = {
        "link_type": "dedupe_only",
        "probability_two_random_records_match": 0.01,
        "blocking_rules_to_generate_predictions": [
            "l.first_name = r.first_name",
            "l.surname = r.surname",
            "l.dob = r.dob",
        ],
        "comparisons": [
            exact_match("unique_id"),
            
            jaro_winkler_at_thresholds("first_name", [0.9, 0.8]),
            
            jaro_winkler_at_thresholds("surname", [0.9, 0.8]),
            
            levenshtein_at_thresholds("dob", [1, 2]),
            
            exact_match("city", term_frequency_adjustments=True),
            
            exact_match("email"),
        ],
        "retain_matching_columns": True,
        "retain_intermediate_calculation_columns": True,
        "max_iterations": 10,
        "em_convergence": 0.01,
    }
    
    return settings

def perform_record_linkage(conn):
    # record linkage
    print("Record linkage başlatılıyor...")
    
    # linker'ı oluşturma
    settings = prepare_splink_settings()
    linker = DuckDBLinker("historical_data", settings, connection=conn)
    
    print("Model eğitimi başlatılıyor...")
    
    # model eğitimi
    linker.estimate_probability_two_random_records_match(
        "l.email = r.email", recall=0.8
    )
    
    # U parametrelerini tahmin et
    linker.estimate_u_using_random_sampling(max_pairs=1e6)
    
    # M parametrelerini tahmin et
    training_blocking_rule = "l.first_name = r.first_name AND l.surname = r.surname"
    linker.estimate_parameters_using_expectation_maximisation(training_blocking_rule)
    
    
    # predictions hesaplama
    predictions = linker.predict(threshold_match_probability=0.5)
    
    # sonuçları dataframe'e çevirme
    predictions_df = predictions.as_pandas_dataframe()
    
    print(f"Toplam {len(predictions_df)} benzerlik (linkage) bulundu.")
    print(f"Match probability >= 0.8 olan linkage sayısı: {len(predictions_df[predictions_df['match_probability'] >= 0.8])}")
    
    return predictions_df, linker

def save_results_to_duckdb(conn, predictions_df):
    # sonuçları duckdb'ye kaydetme
    
    conn.register('linkage_results', predictions_df)
    
    count = conn.execute("SELECT COUNT(*) FROM linkage_results").fetchone()[0]
    print(f"Linkage sonuçları DuckDB'ye kaydedildi. Toplam {count} kayıt.")
    
    # en yüksek skorlular
    top_matches = conn.execute("""
        SELECT match_probability, 
               unique_id_l, 
               unique_id_r,
               first_name_l,
               first_name_r,
               surname_l,
               surname_r
        FROM linkage_results 
        ORDER BY match_probability DESC 
        LIMIT 10
    """).fetchall()
    
    print("\nEn yüksek match probability'li 10 eşleşme:")
    for match in top_matches:
        print(f"Probability: {match[0]:.4f} - {match[1]} <-> {match[2]} | {match[3]} {match[5]} <-> {match[4]} {match[6]}")

def analyze_results(conn):
    
    # genel istatistikler
    stats = conn.execute("""
        SELECT 
            COUNT(*) as total_linkages,
            AVG(match_probability) as avg_probability,
            MIN(match_probability) as min_probability,
            MAX(match_probability) as max_probability,
            COUNT(CASE WHEN match_probability >= 0.8 THEN 1 END) as high_confidence_matches,
            COUNT(CASE WHEN match_probability >= 0.5 AND match_probability < 0.8 THEN 1 END) as medium_confidence_matches,
            COUNT(CASE WHEN match_probability < 0.5 THEN 1 END) as low_confidence_matches
        FROM linkage_results
    """).fetchone()
    
    print(f"Toplam linkage sayısı: {stats[0]}")
    print(f"Ortalama match probability: {stats[1]:.4f}")
    print(f"Min match probability: {stats[2]:.4f}")
    print(f"Max match probability: {stats[3]:.4f}")
    print(f"Yüksek güvenirlik (>=0.8): {stats[4]}")
    print(f"Orta güvenirlik (0.5-0.8): {stats[5]}")
    print(f"Düşük güvenirlik (<0.5): {stats[6]}")

def export_results(conn):
    # csv olarak sonuçları dışarı aktarma
    # yüksek skorlu eşleşmeler
    high_confidence_matches = conn.execute("""
        SELECT * FROM linkage_results 
        WHERE match_probability >= 0.8
        ORDER BY match_probability DESC
    """).df()
    
    high_confidence_matches.to_csv('high_confidence_linkages.csv', index=False)
    print(f"Yüksek güvenirlikli {len(high_confidence_matches)} eşleşme 'high_confidence_linkages.csv' dosyasına kaydedildi.")
    
    # tüm sonuçlar
    all_results = conn.execute("SELECT * FROM linkage_results").df()
    all_results.to_csv('all_linkage_results.csv', index=False)
    print(f"Tüm {len(all_results)} sonuç 'all_linkage_results.csv' dosyasına kaydedildi.")

def main():
    try:
        csv_file = download_historical_data()
        conn = setup_duckdb_connection()
        df = load_data_to_duckdb(conn, csv_file)
        predictions_df, linker = perform_record_linkage(conn)

        save_results_to_duckdb(conn, predictions_df)
        analyze_results(conn)
        export_results(conn)
        
        conn.close()
        
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
