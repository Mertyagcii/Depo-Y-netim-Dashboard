"""ÖRNEK veri üreticileri (Ozan - IoT/Sensör, Selin - Süreç).

Gerçek WMS/IoT verisi bağlanana kadar sayfaların dolu görünmesi için; tüm çıktılar sabit tohumla
(seed) üretilir, yani her açılışta aynıdır. Parametreler depo_profili.json'dan gelir.
"""
import numpy as np
import pandas as pd


def stok(l, profil, seed=11):
    """Bölge bazında palet gözü kapasitesi ve (simüle) doluluk."""
    rng = np.random.RandomState(seed)
    o = l[["bolge", "satir", "adet", "x", "y", "w", "d", "abc"]].copy()
    o["alan_m2"] = o["w"] * o["d"]
    o["pozisyon"] = (o["alan_m2"] * profil["raf_seviye"] / profil["palet_taban_m2"]).round().astype(int)
    sira = np.arange(len(o)) / max(len(o) - 1, 1)                 # hızlı dönen bölgeler biraz daha boş
    oran = np.clip(profil["hedef_doluluk"] + 0.02 - 0.05 * sira + rng.normal(0, 0.05, len(o)), 0.45, 0.99)
    o["dolu"] = (o["pozisyon"] * oran).round().astype(int)
    o["doluluk"] = o["dolu"] / o["pozisyon"] * 100
    return o


def inbound(gun, profil, seed=5):
    """Çıkış hacminden türetilmiş günlük mal kabul: palet, kamyon ve kapı doluluğu (simüle)."""
    s = profil["simulasyon"]
    rng = np.random.RandomState(seed)
    palet = gun["adet"].to_numpy() / s["palet_basi_adet"] * rng.uniform(0.75, 1.15, len(gun))
    kamyon = np.ceil(palet / s["kamyon_palet"])
    kapi = max(int(profil["kapilar"]["mal_kabul"]), 1)
    saat = kamyon * s["kamyon_bosaltma_dk"] / 60
    return pd.DataFrame({"tarih": gun["tarih"].to_numpy(), "palet": palet.round(0), "kamyon": kamyon,
                         "kapi_doluluk": np.minimum(saat / (kapi * s["kapi_acik_saat"]) * 100, 100)})


def surec_sureleri(profil, seed=9):
    """Süreç adımları için hedef süre ve (simüle) gerçekleşen ortalama süre, saat."""
    h = profil["hedefler"]
    rng = np.random.RandomState(seed)
    adimlar = [("Inbound", "Kapıda bekleme → boşaltma", h["bosaltma_saat"]),
               ("Putaway", "Boşaltma → rafa yerleşme", h["dock_to_stock_saat"]),
               ("Picking", "Sipariş serbest → toplama", h["toplama_saat"]),
               ("Packing", "Toplama → paket hazır", h["paketleme_saat"]),
               ("Shipping", "Paket → araca yükleme", h["sevk_saat"])]
    rows = []
    for ad, tanim, hedef in adimlar:
        gercek = round(float(hedef * rng.uniform(0.8, 1.3)), 1)
        durum = "Hedefte" if gercek <= hedef else "Dikkat" if gercek <= 1.15 * hedef else "Gecikme"
        rows.append((ad, tanim, float(hedef), gercek, durum))
    return pd.DataFrame(rows, columns=["adim", "tanim", "hedef_saat", "gerceklesen_saat", "durum"])
