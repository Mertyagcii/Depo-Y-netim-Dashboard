"""Canlı dijital ikiz (Ayşe - Frontend, Ozan - IoT): tarayıcıda gerçek zamanlı akan depo görüntüsü.

Veri akışı sözleşmesi (feed): geometri + bölgeler + araç rotaları + kamyon planı. Tarayıcıdaki animasyon (canli_ikiz.html)
mutlak saatin (epoch) bir fonksiyonudur; bu yüzden sayfa yenilense de hareket kesintisiz devam eder ve sunucu ile
tarayıcı aynı sahneyi görür. Gerçek IoT/API verisi bağlandığında 'telemetri' alanı doldurulur (bkz. API_SOZLESME.md).
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import hesaplamalar as h
import twin as tw

SABLON = Path(__file__).parent / "canli_ikiz.html"
TZ_OFSET = 3 * 3600            # Türkiye saati (UTC+3, yaz/kış saati uygulaması yok)


def kamyon_plani(t0, g, profil, pencere=(-400, 4200), carpan=1.0, in_gecikme=0.0):
    """Mutlak saate bağlı, deterministik kamyon programı: giriş (mal kabul) ve çıkış (sevkiyat) kapıları.
    Sunum için gerçek hayattan sık tutulmuştur (canlı akış görülebilsin)."""
    kapilar = {"in": [k for k in tw.kapi_noktalari(profil, g) if k[0] == "mal_kabul"],
               "out": [k for k in tw.kapi_noktalari(profil, g) if k[0] == "sevkiyat"]}
    plan = []
    for tur, aralik in (("in", 50), ("out", 38 / max(carpan, 0.1))):
        n = max(len(kapilar[tur]), 1)
        for k in range(int((t0 + pencere[0]) // aralik), int((t0 + pencere[1]) // aralik) + 1):
            r = np.random.RandomState(k * 7 + (1 if tur == "in" else 2))
            t_k = float(k * aralik + r.uniform(0, aralik * 0.45))
            if tur == "in" and in_gecikme > 0 and t0 <= t_k <= t0 + in_gecikme:      # kriz: mal kabul kamyonları gecikti
                continue
            plan.append({"t": t_k, "tur": tur, "kapi": int(k % n),
                         "sure": float(r.uniform(55, 110)),
                         "plaka": f"{34 + k % 40:02d} {'DT' if tur == 'in' else 'FT'} {100 + k % 900}",
                         "palet": int(r.randint(14, 27))})
    return plan


def feed(l, profil, adet, bugun_satir=0, bugun_adet=0, t0=None, telemetri=None, kriz=None):
    """Tarayıcıya gönderilen akış paketi."""
    t0 = time.time() if t0 is None else t0
    g = tw.geometri(profil)
    araclar = [] if telemetri else (tw.filo(profil)[:max(adet, 1)] or [dict(tip="Forklift", hiz=1.8, pil_saat=8.0)])
    kriz = kriz or {}
    n_ariza = min(int(kriz.get("arizali", 0)), len(araclar))
    ariza_idx = set(range(0, len(araclar), max(1, len(araclar) // max(n_ariza, 1)))[:n_ariza]) if n_ariza else set()
    parcalar = []
    if n_ariza:
        parcalar.append(f"{n_ariza} forklift arızalı")
    if kriz.get("kamyon_gecikme_sa", 0) > 0:
        parcalar.append(f"mal kabul kamyonları {kriz['kamyon_gecikme_sa']:.0f} saat gecikmeli")
    if kriz.get("artis", 0) > 0:
        parcalar.append(f"sipariş yoğunluğu +%{kriz['artis'] * 100:.0f}")
    forklift = []
    for i, a in enumerate(araclar):
        nok, ev, yuk = tw.rota_olustur(l, g, profil, i)
        forklift.append({"id": f"FLK-{i + 1:02d}", "tip": a["tip"], "hiz": a["hiz"], "pil_saat": a["pil_saat"],
                         "nok": nok.round(2).tolist(), "ev": [None if e is None else [e[0], e[1]] for e in ev],
                         "yuk": [int(y) for y in yuk], "ariza": i in ariza_idx})
    kapilar = tw.kapi_noktalari(profil, g)
    return {
        "t0": t0, "tz_ofset": TZ_OFSET, "mod": "api" if telemetri else "demo",
        "tel": telemetri or [],
        "g": {"en": g["en"], "boy": g["boy"], "bloklar": g["bloklar"]},
        "zonlar": [{"b": r.bolge, "abc": r.abc, "x": float(r.x), "y": float(r.y), "w": float(r.w), "d": float(r.d)}
                   for r in l.itertuples()],
        "forklift": forklift,
        "kapi_in": [[x, y] for tur, x, y in kapilar if tur == "mal_kabul"],
        "kapi_out": [[x, y] for tur, x, y in kapilar if tur == "sevkiyat"],
        "kamyon": kamyon_plani(t0, g, profil, carpan=1 + kriz.get("artis", 0), in_gecikme=kriz.get("kamyon_gecikme_sa", 0) * 3600),
        "kriz": {"metin": "KRİZ SENARYOSU: " + " · ".join(parcalar)} if parcalar else None,
        "bugun": {"satir": int(bugun_satir), "adet": int(bugun_adet)},
    }


def _sn(seri):
    """Naif zaman damgası serisini sn'ye çevirir (yerel saat, UTC kabul edilerek; tz_ofset=0 ile gösterilir)."""
    return (pd.to_datetime(seri) - pd.Timestamp("1970-01-01")).dt.total_seconds()


def _kapi_ata(basla, sure, kapi_sayisi):
    """Greedy kapı ataması: en erken boşalan kapı."""
    bos, out = [-1e18] * kapi_sayisi, []
    for t0, s in zip(basla, sure):
        k = min(range(kapi_sayisi), key=lambda i: (bos[i] > t0 - 15, bos[i]))
        bos[k] = t0 + s
        out.append(k)
    return out


def feed_replay(l, profil, adet, gun, ham, inbound, surec):
    """Geçmiş bir günün GERÇEK kayıtlarıyla oynatma paketi: sevk satırları (ısı/olay), mal kabul ve sevkiyat kamyonları.
    Araç hareketleri simülasyondur."""
    gun = pd.Timestamp(gun).normalize()
    t0 = float(_sn(pd.Series([gun])).iloc[0])
    hg = ham[ham["tarih"] == gun].sort_values("sevk_zamani")
    base = feed(l, profil, adet, len(hg), int(hg["adet"].sum()), t0=t0 + 6 * 3600)
    olaylar = [{"t": float(t), "b": h.bolge_kodu(s), "n": int(n), "k": str(k)}
               for t, s, n, k in zip(_sn(hg["sevk_zamani"]), hg["sku"], hg["adet"], hg["personel"])]
    ib = inbound[inbound["tarih"] == gun].sort_values("bosaltma_baslangic")
    n_in = max(len(base["kapi_in"]), 1)
    kam = []
    for r, t in zip(ib.itertuples(), _sn(ib["bosaltma_baslangic"])):
        kam.append({"t": float(t), "tur": "in", "kapi": int((r.kapi - 1) % n_in), "sure": float((r.bosaltma_bitis - r.bosaltma_baslangic).total_seconds()),
                    "plaka": str(r.plaka), "palet": int(r.palet)})
    sg = surec[surec["yukleme_basladi"].dt.normalize() == gun].sort_values("yukleme_basladi")
    n_out = max(len(base["kapi_out"]), 1)
    bas = _sn(sg["yukleme_basladi"]).tolist()
    sure = (sg["sevk"] - sg["yukleme_basladi"]).dt.total_seconds().tolist()
    for i, (t, s, k) in enumerate(zip(bas, sure, _kapi_ata(bas, sure, n_out))):
        kam.append({"t": float(t), "tur": "out", "kapi": int(k), "sure": float(s), "plaka": f"{34 + i % 40:02d} FT {100 + i % 900}",
                    "palet": 14 + i % 13})
    base.update({"mod": "replay", "tz_ofset": 0, "kamyon": kam, "tel": [], "kriz": None,
                 "replay": {"t0": t0, "t1": t0 + 86400, "gun": f"{gun:%d.%m.%Y}", "olaylar": olaylar}})
    return base


def html(feed_paketi):
    veri = json.dumps(feed_paketi, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")   # <script> kaçışını engelle
    return SABLON.read_text(encoding="utf-8").replace("__FEED__", veri)
