"""Depo profili (Serdar - Mimari): fiziksel depo, kapılar, ekipman ve kadro tek bir JSON dosyasında tutulur.

Buradaki değerler ÖRNEK değerlerdir (10.800 m² depo). Gerçek verilerle 'Depo Profili' sayfasından ya da
depo_profili.json dosyasından düzeltilir; kroki, kapasite ve simülasyonlar otomatik buna göre güncellenir.
"""
import copy
import json
from pathlib import Path

DOSYA = Path(__file__).parent / "depo_profili.json"

TURLER = ["sevkiyat", "paketleme", "ofis", "mal_kabul", "kalite", "iade", "sarj", "depolama"]
TUR_AD = {"sevkiyat": "Sevkiyat", "paketleme": "Paketleme", "ofis": "Ofis/Sosyal", "mal_kabul": "Mal kabul",
          "kalite": "Kalite kontrol", "iade": "İade/Hasarlı", "sarj": "Şarj/Bakım", "depolama": "Depolama & toplama"}
ALT_SERIT = ["sevkiyat", "paketleme", "ofis"]          # çıkış (sevkiyat) tarafı
UST_SERIT = ["mal_kabul", "kalite", "iade", "sarj"]    # giriş (mal kabul) tarafı

VARSAYILAN = {
    "ad": "Ana Depo (örnek)",
    "toplam_alan_m2": 10800,
    "bina_en_m": 120,
    "bina_boy_m": 90,
    "tavan_m": 10,
    "raf_seviye": 5,
    "palet_taban_m2": 1.6,       # bir palet gözü için raf taban alanı (m²)
    "koridor_x_m": 3.0,          # raf blokları arası dikey koridor genişliği
    "koridor_y_m": 4.0,          # raf blokları arası yatay koridor genişliği
    "hedef_doluluk": 0.85,
    "alanlar": [
        {"ad": "Sevkiyat rampası & staging", "tur": "sevkiyat", "alan_m2": 900},
        {"ad": "Paketleme / konsolidasyon", "tur": "paketleme", "alan_m2": 700},
        {"ad": "Ofis, soyunma, yemekhane", "tur": "ofis", "alan_m2": 560},
        {"ad": "Mal kabul rampası & staging", "tur": "mal_kabul", "alan_m2": 1000},
        {"ad": "Kalite kontrol", "tur": "kalite", "alan_m2": 400},
        {"ad": "İade & hasarlı", "tur": "iade", "alan_m2": 360},
        {"ad": "Forklift şarj & bakım", "tur": "sarj", "alan_m2": 400},
        {"ad": "Depolama & toplama (raf)", "tur": "depolama", "alan_m2": 6480},
    ],
    "kapilar": {"mal_kabul": 6, "sevkiyat": 10},
    "forkliftler": [
        {"tip": "Reach truck", "adet": 5, "hiz_ms": 1.8, "pil_saat": 8},
        {"tip": "Karşı ağırlıklı forklift", "adet": 2, "hiz_ms": 2.2, "pil_saat": 8},
        {"tip": "Elektrikli transpalet", "adet": 8, "hiz_ms": 1.6, "pil_saat": 6},
        {"tip": "Order picker", "adet": 3, "hiz_ms": 1.4, "pil_saat": 7},
    ],
    "vardiyalar": [
        {"ad": "Gündüz", "baslangic": "06:00", "bitis": "15:00", "kisi": 34},
        {"ad": "Akşam", "baslangic": "15:00", "bitis": "24:00", "kisi": 26},
    ],
    "kadro": [
        {"rol": "Toplayıcı (picker)", "kisi": 24},
        {"rol": "Forklift operatörü", "kisi": 14},
        {"rol": "Paketleme", "kisi": 10},
        {"rol": "Mal kabul", "kisi": 6},
        {"rol": "Sevkiyat", "kisi": 6},
    ],
    "maliyet": {"adam_gun_tl": 2400.0, "fazla_mesai_carpan": 1.5, "gecikme_ceza_tl": 1500.0, "palet_bekleme_tl_saat": 6.0,
                "kwh_km": 1.1, "co2_kg_kwh": 0.45},
    "hedefler": {"dock_to_stock_saat": 4.0, "toplama_saat": 6.0, "paketleme_saat": 2.0, "sevk_saat": 3.0,
                 "bosaltma_saat": 1.0},
    "simulasyon": {"palet_basi_adet": 300, "kamyon_palet": 26, "kamyon_bosaltma_dk": 45, "kapi_acik_saat": 15},
}


def varsayilan():
    return copy.deepcopy(VARSAYILAN)


def _birlestir(taban, ek):
    for k, v in ek.items():
        if isinstance(v, dict) and isinstance(taban.get(k), dict):
            _birlestir(taban[k], v)
        else:
            taban[k] = v
    return taban


def yukle(dosya=DOSYA):
    """Kayıtlı profili okur; eksik anahtarlar varsayılanla tamamlanır, bozuk dosyada varsayılan döner."""
    p = varsayilan()
    try:
        if Path(dosya).exists():
            _birlestir(p, json.loads(Path(dosya).read_text(encoding="utf-8")))
    except Exception:
        return varsayilan()
    return p if not hata_var(p) else varsayilan()


def kaydet(p, dosya=DOSYA):
    Path(dosya).write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def toplam(p, tur=None):
    return float(sum(a["alan_m2"] for a in p["alanlar"] if tur is None or a["tur"] in tur))


def hata_var(p):
    """Kroki çizilemeyecek kadar bozuk profil: kritik hata mesajları (boşsa profil kullanılabilir)."""
    h = []
    if not p.get("bina_en_m", 0) > 0:
        h.append("Bina eni 0'dan büyük olmalı.")
    if toplam(p, ["depolama"]) <= 0:
        h.append("'depolama' türünde en az bir alan ve alan_m2 > 0 gerekli.")
    if p["bina_en_m"] > 0 and (toplam(p, ALT_SERIT) <= 0 or toplam(p, UST_SERIT) <= 0):
        h.append("Hem çıkış (sevkiyat/paketleme/ofis) hem giriş (mal kabul/kalite/iade/şarj) tarafında alan gerekli.")
    return h


def uyarilar(p):
    """Tutarsızlık uyarıları (kritik değil, düzeltilmesi önerilir)."""
    u = []
    t = toplam(p)
    if abs(t - p["toplam_alan_m2"]) > 1:
        u.append(f"Alanların toplamı ({t:,.0f} m²) ile toplam alan ({p['toplam_alan_m2']:,.0f} m²) tutmuyor.".replace(",", "."))
    if abs(p["bina_en_m"] * p["bina_boy_m"] - p["toplam_alan_m2"]) > 1:
        u.append(f"Bina en × boy ({p['bina_en_m'] * p['bina_boy_m']:,.0f} m²) toplam alanla tutmuyor.".replace(",", "."))
    ks, vs = sum(k["kisi"] for k in p["kadro"]), sum(v["kisi"] for v in p["vardiyalar"])
    if ks != vs:
        u.append(f"Kadro toplamı ({ks}) ile vardiya toplamı ({vs}) farklı.")
    return u
