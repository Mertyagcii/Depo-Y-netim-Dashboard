"""Saha (mobil) toplama listesi: kişiye özel görevler, en yakın komşu rotası, mesafe ve süre tahmini (Deniz - Mobil UX, Mehmet).

Görevler seçilen kişinin en son işlediği satırlardan türetilir (demo); gerçek WMS bağlanınca açık görev listesiyle değişir.
"""
import pandas as pd

import hesaplamalar as h
import twin as tw

YURUME = 1.4          # m/sn
TOPLAMA_SN = 30       # bir satır toplama süresi


def gorevler(ham, kisi, l, profil, n=8):
    """Kişinin son gününden n satır alır, rotaya göre sıralar. (DataFrame, rota noktaları) döner."""
    k = ham[ham["personel"] == kisi]
    if k.empty:
        return pd.DataFrame(columns=["sira", "bolge", "sku", "urun", "adet", "mesafe_m", "eta_dk"]), []
    son = k[k["tarih"] == k["tarih"].max()].tail(60)
    son = son.assign(bolge=son["sku"].map(h.bolge_kodu)).drop_duplicates("sku").tail(n)
    g = tw.geometri(profil)
    xy = {r.bolge: tw._toplama_noktasi(r, g) for r in l.itertuples()}
    sira = tw.rota_siralama(l, son["bolge"].tolist(), profil)
    konum, rows, rota = g["dok"], [], [g["dok"]]
    for no, b in enumerate(sira, 1):
        for r in son[son["bolge"] == b].itertuples():
            mesafe = tw.mesafe(konum, xy[b])
            rows.append((no, b, r.sku, r.urun, int(r.adet), round(mesafe, 0), round((mesafe / YURUME + TOPLAMA_SN) / 60, 1)))
            konum = xy[b]
            rota.append(xy[b])
    rota.append(g["dok"])
    return pd.DataFrame(rows, columns=["sira", "bolge", "sku", "urun", "adet", "mesafe_m", "eta_dk"]), rota
