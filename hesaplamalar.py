"""Depo KPI hesaplamaları (Mehmet - Veri Uzmanı).

Kurallar (Selim - Lojistik Uzmanı):
- Vardiya 9 saat.
- Veride çalışma saati yok; bir personel bir günde sevkiyat yaptıysa o gün 9 saat çalışmış sayılır.
- UPH = sevk edilen adet / (personel-gün x 9 saat)
- Lokasyon bilgisi yok: bir SKU = bir lokasyon. Personelin 9 saati, o gün
  işlediği satır sayısına göre SKU'lara paylaştırılır.
"""
import re

import pandas as pd

VARDIYA_SAATI = 9
SISTEM_KULLANICILARI = ["Site Admin"]

SUTUNLAR = ["tarih", "sevk_zamani", "personel", "sevkiyat", "teslimat", "siparis", "kanal", "musteri_kodu",
            "musteri", "teslim_alan", "il", "sku", "urun", "malzeme_turu", "parti", "skt", "adet"]


def _isim_duzelt(ad):
    """'Mert Yagci' ve 'Mert Yağcı' gibi aynı kişinin farklı yazımlarını birleştirir."""
    if pd.isna(ad):
        return "Atanmamış"
    ad = str(ad).strip()
    harita = str.maketrans("ğĞıİşŞçÇöÖüÜ", "gGiIsScCoOuU")
    ad = ad.translate(harita)
    ad = re.sub(r"[^A-Za-z ]", "?", ad)          # bozuk karakterler
    ad = re.sub(r"\s+", " ", ad).title()
    if re.fullmatch(r"Mert Ya.{0,2}c.{0,2}", ad, re.I):
        ad = "Mert Yagci"
    return ad


def veri_oku(dosya):
    d = pd.read_excel(dosya, sheet_name=0)
    d = d.iloc[:, : len(SUTUNLAR)]
    d.columns = SUTUNLAR
    d["personel"] = d["personel"].map(_isim_duzelt)
    d["sku"] = d["sku"].astype(str)
    d["tarih"] = pd.to_datetime(d["tarih"]).dt.normalize()
    return d


def gunluk_personel(d):
    """Her satır = bir personelin bir günü."""
    g = d.groupby(["tarih", "personel"], as_index=False).agg(
        adet=("adet", "sum"), satir=("adet", "size"), sevkiyat=("sevkiyat", "nunique"),
        ilk=("sevk_zamani", "min"), son=("sevk_zamani", "max"),
    )
    g["calisma_saati"] = VARDIYA_SAATI
    g["uph"] = g["adet"] / g["calisma_saati"]
    g["aktif_saat"] = (g["son"] - g["ilk"]).dt.total_seconds() / 3600
    return g


def gunluk_ozet(g):
    o = g.groupby("tarih", as_index=False).agg(adet=("adet", "sum"), personel=("personel", "nunique"),
                                                satir=("satir", "sum"))
    o["adam_saat"] = o["personel"] * VARDIYA_SAATI
    o["uph"] = o["adet"] / o["adam_saat"]
    o["satir_uph"] = o["satir"] / o["adam_saat"]
    return o


def sku_uph(d):
    """Personelin 9 saati, o gün işlediği satır sayısına göre SKU'lara paylaştırılır."""
    x = d.groupby(["tarih", "personel", "sku"], as_index=False).agg(
        adet=("adet", "sum"), satir=("adet", "size"), urun=("urun", "first"))
    x["saat"] = VARDIYA_SAATI * x["satir"] / x.groupby(["tarih", "personel"])["satir"].transform("sum")
    s = x.groupby("sku", as_index=False).agg(urun=("urun", "first"), adet=("adet", "sum"),
                                              satir=("satir", "sum"), saat=("saat", "sum"))
    s["uph"] = s["adet"] / s["saat"]
    return s.sort_values("adet", ascending=False)


def bolge_kodu(sku):
    """Lokasyon verisi gelene kadar: SKU kodunun ilk 2 hanesi = toplama bölgesi (ürün grubu)."""
    return str(sku)[:2]


def bolge_uph(d, sistem_dahil=False):
    """Bölge bazında UPH (SKU'ya paylaştırılan saatlerden) ve toplam yoğunluk."""
    if not sistem_dahil:
        d = d[~d["personel"].isin(SISTEM_KULLANICILARI)]
    x = d.groupby(["tarih", "personel", "sku"], as_index=False).agg(adet=("adet", "sum"), satir=("adet", "size"))
    x["saat"] = VARDIYA_SAATI * x["satir"] / x.groupby(["tarih", "personel"])["satir"].transform("sum")
    x["bolge"] = x["sku"].map(bolge_kodu)
    b = x.groupby("bolge", as_index=False).agg(adet=("adet", "sum"), satir=("satir", "sum"), saat=("saat", "sum"))
    b["uph"] = b["adet"] / b["saat"]
    b["satir_saat"] = b["satir"] / b["saat"]
    return b.sort_values("adet", ascending=False)


def bolge_saat_yogunluk(d, sistem_dahil=False):
    """Bölge x saat matrisi: o saatte kaç satır sevk edildi (yoğunluk haritası)."""
    if not sistem_dahil:
        d = d[~d["personel"].isin(SISTEM_KULLANICILARI)]
    y = d.dropna(subset=["sevk_zamani"]).copy()
    y["bolge"] = y["sku"].map(bolge_kodu)
    y["saat"] = y["sevk_zamani"].dt.hour
    return y.pivot_table(index="bolge", columns="saat", values="adet", aggfunc="size", fill_value=0)
