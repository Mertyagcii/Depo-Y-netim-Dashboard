"""'Ya şöyle olursa?' simülatörü ve kriz senaryoları (Mehmet - Veri & Analitik, Selin - Süreç).

Basit ama açıklanabilir bir kapasite modeli: önümüzdeki 7 günün talebi, kadro × UPH × 9 saat kapasitesine karşı akıtılır;
kapasiteyi aşan iş ertesi güne devreder (birikim / backlog). Forklift kapasitesi ve mal kabul gecikmesi de etkiyi artırır.
"""
import math

import numpy as np
import pandas as pd

import hesaplamalar as h
import maliyet as ml

HAFTA_CARPAN = {5: 0.7, 6: 0.2}             # Cumartesi %70, Pazar %20 kadro (diğer günler %100)
HAREKET_SAAT = 12                           # forklift başına saatte palet hareketi (al-götür, ~5 dk/çevrim)
HAREKET_PALET = 6                           # palet başına hareket: kabul 2 + çıkış 2 + ikmal/iç taşıma 2
KAMYON_PALET = 26

KRIZLER = {
    "kamyon": {"ad": "Kamyon gecikmesi", "ikon": "🚚", "kamyon_gecikme_sa": 3.0, "aciklama": "Mal kabul kamyonları 3 saat gecikti"},
    "forklift": {"ad": "Forklift arızası", "ikon": "🔧", "forklift_ariza": 4, "aciklama": "4 forklift arızalandı"},
    "siparis": {"ad": "Ani sipariş artışı", "ikon": "📈", "artis": 40, "aciklama": "Talep aniden %40 arttı"},
    "devamsiz": {"ad": "Personel devamsızlığı", "ikon": "🤒", "personel_eksik": 20, "aciklama": "Kadronun %20'si gelmedi"},
}


def hesapla(tahmin, kadro, uph, forklift, profil, artis=0.0, personel_eksik=0.0, forklift_ariza=0, kamyon_gecikme_sa=0.0,
            ort_siparis_adet=6000.0):
    """Senaryoyu hesaplar. tahmin: tarih + tahmin_adet (7 gün). Yüzdeler 0-100 değil oran (0.4 = %40) olarak verilir."""
    pb = profil["simulasyon"]["palet_basi_adet"]
    m = ml.varsayim(profil)
    talep = tahmin["tahmin_adet"].to_numpy(float) * (1 + artis)
    etkin = max(kadro * (1 - personel_eksik), 0.0)
    palet_gun = float(talep.mean() / pb * HAREKET_PALET)                       # günlük forklift hareketi
    fl_kap = max(forklift - forklift_ariza, 0) * h.VARDIYA_SAATI * HAREKET_SAAT
    fl_oran = min(1.0, fl_kap / palet_gun) if palet_gun else 1.0               # forklift darboğazı çarpanı
    kap_taban = etkin * uph * h.VARDIYA_SAATI * fl_oran
    rows, birikim = [], 0.0
    for t, d in zip(pd.to_datetime(tahmin["tarih"]), talep):
        c = kap_taban * HAFTA_CARPAN.get(t.dayofweek, 1.0)
        birikim = max(0.0, birikim + d - c)
        rows.append((t, float(d), float(c), float(birikim)))
    seri = pd.DataFrame(rows, columns=["tarih", "talep", "kapasite", "birikim"])
    kullanim = float(talep.sum() / seri["kapasite"].sum()) if seri["kapasite"].sum() else float("inf")
    birikim_son = float(seri["birikim"].iloc[-1])
    gunluk_kap = kap_taban if kap_taban else 1.0
    gecikme_gun = birikim_son / gunluk_kap
    # gereken kaynak
    gun_katsayi = sum(HAFTA_CARPAN.get(t.dayofweek, 1.0) for t in seri["tarih"])
    gereken_kadro = math.ceil(talep.sum() / (uph * h.VARDIYA_SAATI * gun_katsayi * max(fl_oran, 1e-9)))
    gereken_forklift = math.ceil(palet_gun / (h.VARDIYA_SAATI * HAREKET_SAAT))
    geciken_siparis = birikim_son / max(ort_siparis_adet, 1.0)
    mal_kabul_birikim = kamyon_gecikme_sa / 24 * (talep.mean() / pb)
    kapi_dol = float(talep.mean() / pb / KAMYON_PALET * profil["simulasyon"]["kamyon_bosaltma_dk"] / 60
                     / (max(profil["kapilar"]["mal_kabul"], 1) * profil["simulasyon"]["kapi_acik_saat"]) * 100)
    ek_kisi = max(gereken_kadro - etkin, 0)
    risk = "Yüksek" if (gecikme_gun > 1 or kullanim > 1.15) else "Orta" if (gecikme_gun > 0 or kullanim > 1.0) else "Düşük"
    return {
        "seri": seri, "kullanim": kullanim, "birikim": birikim_son, "gecikme_gun": gecikme_gun, "etkin_kadro": etkin,
        "gereken_kadro": gereken_kadro, "gereken_forklift": gereken_forklift, "ek_kisi": ek_kisi,
        "ek_forklift": max(gereken_forklift - max(forklift - forklift_ariza, 0), 0),
        "geciken_siparis": geciken_siparis, "gecikme_tl": geciken_siparis * m["gecikme_ceza_tl"],
        "ek_kadro_tl_gun": ek_kisi * m["adam_gun_tl"], "fl_oran": fl_oran, "palet_gun": palet_gun,
        "mal_kabul_birikim": mal_kabul_birikim, "kapi_doluluk": kapi_dol,
        "stok_riski": "Yüksek" if kamyon_gecikme_sa > 6 else "Orta" if kamyon_gecikme_sa > 2 else "Düşük", "risk": risk,
        "talep_gun": float(talep.mean()),
    }


def oneriler(s, kadro, forklift, forklift_ariza, kamyon_gecikme_sa):
    """Hesap sonucundan okunabilir, uygulanabilir öneriler."""
    o = []
    if s["ek_kisi"] > 0.5:
        o.append(f"👷 Birikimi sıfırlamak için günde **{math.ceil(s['ek_kisi'])} kişi** daha gerekli "
                 f"(ya da yaklaşık {s['birikim'] / max(1, s['seri']['kapasite'].mean()) * 9:.0f} saat fazla mesai).")
    if s["ek_forklift"] > 0 or s["fl_oran"] < 1:
        o.append(f"🚜 Forklift kapasitesi yetersiz: **{math.ceil(max(s['ek_forklift'], 1))} araç** kiralama/yedek öneriliyor "
                 f"(kapasite %{s['fl_oran'] * 100:.0f} seviyesinde).")
    if kamyon_gecikme_sa > 2:
        o.append(f"🚚 Mal kabul {kamyon_gecikme_sa:.0f} saat gecikirse ~{s['mal_kabul_birikim']:.0f} palet birikir; "
                 "toplama alanı stokunu kontrol edin, acil siparişleri mevcut stoktan karşılayın.")
    if s["gecikme_gun"] > 0.3:
        o.append(f"⏰ Yaklaşık **{s['geciken_siparis']:.0f} sipariş** termin riskinde (~{s['gecikme_gun']:.1f} gün birikim). "
                 "Öncelikli müşterilerin siparişlerini öne alın.")
    if not o:
        o.append("✅ Mevcut kaynaklar bu senaryoyu karşılıyor; birikim oluşmuyor.")
    return o
