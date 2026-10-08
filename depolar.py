"""Çok depolu karşılaştırma (Serdar - Mimari). Ana depo gerçek/ekrandaki verilerden; diğer depolar SİMÜLASYON (ana depodan türetilir).

Gerçek çok depolu veri bağlandığında her depo için ayrı API (ya da depo alanı) eklenir; bu tablo aynı şemada kalır.
"""
import zlib

import numpy as np
import pandas as pd

SITELER = [("İstanbul (Ana)", 41.01, 28.98, 10800, 60), ("Ankara", 39.93, 32.86, 6500, 38), ("İzmir", 38.42, 27.14, 8200, 47),
           ("Bursa", 40.19, 29.06, 4200, 24), ("Adana", 37.00, 35.32, 3600, 20), ("Samsun", 41.29, 36.33, 3000, 17)]


def kiyas(ana):
    """ana: dict(gunluk_cikis, uph, doluluk, putaway_saat, sevk_saat, alan, kadro). DataFrame döner (skor dahil)."""
    rows = []
    for i, (ad, lat, lon, alan, kadro) in enumerate(SITELER):
        if i == 0:
            rows.append((ad, lat, lon, ana["alan"], ana["kadro"], ana["gunluk_cikis"], ana["uph"], ana["doluluk"], ana["putaway_saat"], ana["sevk_saat"], True))
            continue
        r = np.random.RandomState(zlib.crc32(ad.encode()))
        oran = alan / ana["alan"]
        rows.append((ad, lat, lon, alan, kadro, ana["gunluk_cikis"] * oran * r.uniform(0.85, 1.1), ana["uph"] * r.uniform(0.86, 1.08),
                     float(np.clip(ana["doluluk"] + r.uniform(-12, 9), 55, 97)), ana["putaway_saat"] * r.uniform(0.8, 1.35),
                     ana["sevk_saat"] * r.uniform(0.85, 1.3), False))
    d = pd.DataFrame(rows, columns=["depo", "lat", "lon", "alan_m2", "kadro", "gunluk_cikis", "uph", "doluluk", "putaway_saat", "sevk_saat", "ana"])
    d["m2_basina_cikis"] = d["gunluk_cikis"] / d["alan_m2"]
    d["skor"] = (50 * (d["uph"] / d["uph"].max()) + 30 * (d["putaway_saat"].min() / d["putaway_saat"]) + 20 * (d["sevk_saat"].min() / d["sevk_saat"])).round(0)
    return d
