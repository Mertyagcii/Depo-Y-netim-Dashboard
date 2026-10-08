"""TL cinsinden yönetici görünümü: maliyet, fazla mesai, gecikme, Kaizen tasarrufu ve karbon (Mehmet - Veri & Analitik).

Birim maliyetler depo_profili.json > "maliyet" altındadır. Varsayılan değerler ÖRNEKTİR; gerçek değerlerle
Maliyet & ROI sayfasından güncellenir.
"""
import numpy as np

import hesaplamalar as h

IS_GUNU_YIL = 312                    # Pazartesi-Cumartesi, resmi tatiller düşülmüş yaklaşık değer
YURUME_HIZI = 1.4                    # m/sn (toplayıcı/forklift ortalama)

VARSAYILAN = {
    "adam_gun_tl": 2400.0,           # tam yüklü günlük personel maliyeti (maaş+SGK+yemek+servis)
    "fazla_mesai_carpan": 1.5,
    "gecikme_ceza_tl": 1500.0,       # geciken sipariş başına ceza/iskonto
    "palet_bekleme_tl_saat": 6.0,    # mal kabulde bekleyen palet başına saatlik maliyet
    "kwh_km": 1.1,                   # forklift enerji tüketimi (kWh/km)
    "co2_kg_kwh": 0.45,              # şebeke emisyon faktörü (kg CO₂/kWh)
}


def varsayim(profil):
    m = dict(VARSAYILAN)
    m.update(profil.get("maliyet", {}))
    return m


def saat_tl(m):
    return m["adam_gun_tl"] / h.VARDIYA_SAATI


def donem(gun, profil):
    """Dönem maliyet özeti: personel, birim maliyet, fazla mesai (günlük özet tablosundan)."""
    m = varsayim(profil)
    adet = float(gun["adet"].sum())
    personel_tl = float(gun["adam_saat"].sum() * saat_tl(m))
    uph = float(gun["uph"].median())
    kap = float(gun["personel"].median() * uph * h.VARDIYA_SAATI)
    fazla_adet = float((gun["adet"] - kap).clip(lower=0).sum())
    fazla_saat = fazla_adet / uph if uph else 0.0
    fazla_tl = fazla_saat * saat_tl(m) * m["fazla_mesai_carpan"]
    return {"adet": adet, "personel_tl": personel_tl, "birim_tl": personel_tl / adet if adet else 0.0,
            "fazla_saat": fazla_saat, "fazla_tl": fazla_tl, "gun": int(len(gun)), "kapasite_gun": kap}


def yilliklastir(tutar, gun_sayisi):
    """Dönem tutarını yıllık iş gününe ölçekler."""
    return tutar * IS_GUNU_YIL / max(gun_sayisi, 1)


def karbon(metre_gun, profil):
    """Günlük azalan yürüme/sürüş mesafesinden (m) enerji ve CO₂ (yıllık)."""
    m = varsayim(profil)
    km_yil = metre_gun / 1000 * IS_GUNU_YIL
    kwh = km_yil * m["kwh_km"]
    return {"km_yil": km_yil, "kwh_yil": kwh, "co2_kg_yil": kwh * m["co2_kg_kwh"]}


def kalemler(profil, gun, yer_tasarruf_m_gun, sureler_tab, geciken_siparis_yil=0.0, put_palet_gun=0.0):
    """Kaizen kalemlerinin yıllık TL karşılığı. [(ad, yıllık_tl, açıklama)] döner."""
    m = varsayim(profil)
    d = donem(gun, profil)
    out = []
    saat_gun = yer_tasarruf_m_gun / YURUME_HIZI / 3600
    out.append(("Raf yerleşimi (ABC)", saat_gun * saat_tl(m) * IS_GUNU_YIL,
                f"günde {yer_tasarruf_m_gun:,.0f} m daha az yürüme ({saat_gun:.1f} saat)".replace(",", ".")))
    if len(sureler_tab):
        p = sureler_tab[sureler_tab["adim"] == "Putaway"]
        if len(p) and p.iloc[0]["gerceklesen_saat"] > p.iloc[0]["hedef_saat"]:
            fark = p.iloc[0]["gerceklesen_saat"] - p.iloc[0]["hedef_saat"]
            out.append(("Putaway süresini hedefe çekme", fark * put_palet_gun * m["palet_bekleme_tl_saat"] * IS_GUNU_YIL,
                        f"palet başına {fark:.1f} saat daha az bekleme"))
    out.append(("Saatlik yük dengeleme (%30 fazla mesai azalışı)", yilliklastir(d["fazla_tl"], d["gun"]) * 0.30,
                f"fazla mesai yıllık {yilliklastir(d['fazla_tl'], d['gun']):,.0f} ₺".replace(",", ".")))
    if geciken_siparis_yil > 0:
        out.append(("Gecikmeleri önleme", geciken_siparis_yil * m["gecikme_ceza_tl"] * 0.5,
                    f"yılda ~{geciken_siparis_yil:,.0f} geciken siparişin yarısı".replace(",", ".")))
    return out


def tl(x):
    """1.234.567 ₺ biçimi."""
    return f"{x:,.0f} ₺".replace(",", ".")
