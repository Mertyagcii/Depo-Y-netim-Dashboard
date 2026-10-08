"""Sunum (demo) verisi: 10.800 m², 60 kişilik kadro, tutarlı ve EKSİKSİZ bir operasyon (Ozan - IoT, Serdar - Mimari).

Bu modül gerçek bir WMS/ERP/IoT kaynağının yerine geçer. Çıktı tabloları, gerçek API'den gelecek verinin
BİREBİR aynı şemasındadır (bkz. API_SOZLESME.md); kaynak değişince uygulamanın geri kalanı değişmez.
Tüm veriler tohumludur (seed): aynı gün aynı sonucu verir. Ortalama değerler depo_profili.json'dan gelir.
"""
import os
import zlib

import numpy as np
import pandas as pd

import depo_profil as dp

BOLGELER = {"31": "Ruj & Dudak", "32": "Göz Makyajı", "33": "Fondöten & Yüz", "34": "Oje", "35": "Cilt Bakım",
            "36": "Parfüm & Deodorant", "41": "Saç Bakım", "42": "Vücut Bakım", "43": "Erkek Bakım",
            "45": "Güneş Ürünleri", "46": "Aksesuar & Fırça", "47": "Hediye Setleri", "49": "Mini Boy",
            "51": "Temizlik", "52": "Bebek Bakım", "61": "Ambalaj & Stant", "62": "Promosyon", "63": "Ek Ürünler"}
ERKEK = ["Ahmet", "Mehmet", "Mustafa", "Emre", "Burak", "Can", "Ozan", "Serkan", "Hakan", "Murat", "Kemal", "Yusuf",
         "Onur", "Barış", "Tolga", "Eren", "Kaan", "Selim", "Volkan", "Umut", "Cem", "Alper", "Furkan", "Oğuz",
         "Berk", "Taner", "Levent", "Erdem", "Gökhan", "Orhan"]
KADIN = ["Ayşe", "Fatma", "Zeynep", "Elif", "Merve", "Selin", "Esra", "Derya", "Seda", "Büşra", "Gizem", "Pınar",
         "Burcu", "Ece", "Özge", "Hande", "Sevgi", "Naz", "Dilara", "Aslı", "Cansu", "Tuğba", "Yasemin", "Melis"]
SOYAD = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Aydın", "Öztürk", "Arslan", "Doğan", "Kılıç", "Aslan",
         "Çetin", "Kara", "Koç", "Kurt", "Özdemir", "Polat", "Korkmaz", "Erdoğan", "Güneş", "Aksoy", "Tekin", "Bulut",
         "Avcı", "Türk", "Sarı", "Yavuz", "Acar", "Uçar", "Bayrak", "Taş", "Işık", "Duman", "Tunç", "Özkan"]
ZINCIR = ["Anadolu Market", "Yıldız Perakende", "Mavi Gross", "Güneş Kozmetik", "Lale Eczane Grubu", "Kardelen Mağazacılık",
          "Deniz Hipermarket", "Atlas Online", "Ege Kozmetik", "Bosphorus Retail", "Nil Mağazaları", "Doruk Toptan"]
ILLER = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep", "Kayseri", "Mersin",
         "Eskişehir", "Samsun", "Trabzon", "Denizli", "Tekirdağ", "Kocaeli"]
SAAT_AGIRLIK = np.array([0, 0, 0, 0, 0, 0, 2, 4, 6, 8, 9, 9, 8, 5, 5, 6, 7, 8, 8, 7, 6, 4, 2, 1], dtype=float)
HAFTA_KATSAYI = [1.0, 1.05, 1.0, 1.05, 1.1, 0.75, 0.12]        # Pzt..Paz
KANAL = ["Toptan", "E-Ticaret", "Perakende"]
SEZON = {1: 0.90, 2: 0.90, 3: 0.95, 4: 0.97, 5: 1.0, 6: 0.95, 7: 0.90, 8: 0.88, 9: 1.0, 10: 1.05, 11: 1.22, 12: 1.28}   # ay katsayısı


def personel(profil=None):
    """60 kişilik kadro listesi: ad, rol, vardiya (profil.kadro ve profil.vardiyalar oranına göre)."""
    p = profil or dp.varsayilan()
    rng = np.random.RandomState(21)
    toplam = sum(k["kisi"] for k in p["kadro"])
    gunduz_oran = p["vardiyalar"][0]["kisi"] / max(sum(v["kisi"] for v in p["vardiyalar"]), 1)
    adlar = []
    while len(adlar) < toplam:
        ad = f"{(ERKEK + KADIN)[rng.randint(0, len(ERKEK) + len(KADIN))]} {SOYAD[rng.randint(0, len(SOYAD))]}"
        if ad not in adlar:
            adlar.append(ad)
    satirlar, i = [], 0
    for k in p["kadro"]:
        n_g = round(k["kisi"] * gunduz_oran)
        for j in range(k["kisi"]):
            satirlar.append((adlar[i], k["rol"], p["vardiyalar"][0]["ad"] if j < n_g else p["vardiyalar"][-1]["ad"]))
            i += 1
    return pd.DataFrame(satirlar, columns=["ad", "rol", "vardiya"])


def _urunler(rng):
    """Her bölge için 24 SKU (Zipf popülerlik)."""
    sku, urun, bolge, pop = [], [], [], []
    for b, ad in BOLGELER.items():
        for k in range(24):
            sku.append(f"{b}{rng.randint(100000, 999999)}-{300 + k}")
            urun.append(f"{ad} {['Mat', 'Parlak', 'Nude', 'Kırmızı', 'Pembe', 'Şeftali', 'Mercan', 'Bordo'][k % 8]} {k + 1:02d}")
            bolge.append(b)
            pop.append(1 / (k + 1) ** 0.8)
    return pd.DataFrame({"sku": sku, "urun": urun, "bolge": bolge, "pop": pop})


def _bolge_agirlik():
    sira = np.random.RandomState(5).permutation(len(BOLGELER))
    return dict(zip(BOLGELER, 1 / (sira + 1) ** 0.95))        # birkaç bölge baskın (Pareto)


_BELLEK = {}
ONBELLEK = None


def _onbellek_dizini():
    from pathlib import Path
    d = Path(__file__).parent / ".onbellek"
    try:
        d.mkdir(exist_ok=True)
        return d
    except OSError:
        return None


def _tam(son_gun, gun_sayisi, p, seed):
    """`son_gun` gününün SONUNA kadar olan tüm veri (vektörel üretim). Gün içi kesme uret()'te yapılır."""
    kadro = personel(p)
    pickers = kadro[kadro["rol"].str.contains("Toplay")]
    gunduz = pickers[pickers["vardiya"] == p["vardiyalar"][0]["ad"]]["ad"].tolist()
    aksam = pickers[pickers["vardiya"] != p["vardiyalar"][0]["ad"]]["ad"].tolist()
    rng = np.random.RandomState(seed)
    urunler = _urunler(rng)
    u_sku, u_urun = urunler["sku"].to_numpy(object), urunler["urun"].to_numpy(object)
    w = (urunler["bolge"].map(_bolge_agirlik()) * urunler["pop"]).to_numpy()
    urun_w = w / w.sum()
    mus = [f"{rng.choice(ZINCIR)} {rng.choice(ILLER)} {rng.randint(1, 40):02d}" for _ in range(160)]
    m_ad, m_il = np.array(mus, dtype=object), np.array([m.split()[-2] for m in mus], dtype=object)
    m_kod = np.array([f"M{zlib.crc32(m.encode()) % 90000 + 10000}" for m in mus], dtype=object)
    m_no = np.array([f"{zlib.crc32(m.encode()) % 9000000 + 1000000:010d}" for m in mus], dtype=object)
    KN = np.array(KANAL, dtype=object)
    saat_p = SAAT_AGIRLIK / SAAT_AGIRLIK.sum()
    h = p["hedefler"]

    ham_p, sr_p, sev_no, tes_no = [], [], 5_000_000, 8_000_000_000
    for gun_i in range(gun_sayisi):
        gun = son_gun - pd.Timedelta(days=gun_sayisi - 1 - gun_i)
        gun_ep = int(gun.timestamp())
        gr = np.random.RandomState(seed * 1000 + gun_i)
        dow = gun.dayofweek
        hedef = 2000 * HAFTA_KATSAYI[dow] * (1.15 if gun.day >= 28 else 1.0) * SEZON[gun.month] * (1 + 0.04 * np.sin(gun_i / 9)) * np.exp(gr.normal(0, 0.07))
        if dow == 6:
            mg, ma = list(gr.choice(gunduz, 3, replace=False)), list(gr.choice(aksam, 1, replace=False))
        else:
            oran = 0.92 if dow < 5 else 0.6
            mg = list(gr.choice(gunduz, max(2, int(len(gunduz) * oran)), replace=False))
            ma = list(gr.choice(aksam, max(2, int(len(aksam) * oran)), replace=False))
        ga, aa = np.array(mg, dtype=object), np.array(ma, dtype=object)
        # --- sevkiyatlar ---
        S = int(hedef / 5.4 * 1.5) + 30
        kan = gr.choice(3, size=S, p=[0.30, 0.50, 0.20])
        n = np.where(kan == 0, gr.randint(5, 15, S), np.where(kan == 1, gr.randint(1, 4, S), gr.randint(3, 9, S)))
        S = int(np.searchsorted(np.cumsum(n), hedef)) + 1
        kan, n = kan[:S], n[:S]
        saat = gr.choice(24, size=S, p=saat_p)
        t0 = gun_ep + saat * 3600 + gr.randint(0, 60, S) * 60 + gr.randint(0, 60, S)
        kisi = np.where(saat < 15, ga[gr.randint(0, len(ga), S)], aa[gr.randint(0, len(aa), S)])
        cust = gr.randint(0, len(mus), S)
        sevno = sev_no + 1 + np.arange(S)
        sev_no += S
        tesno = tes_no + np.cumsum(gr.randint(1, 9, S))
        tes_no = int(tesno[-1])
        # --- satırlar ---
        L = int(n.sum())
        sid = np.repeat(np.arange(S), n)
        k = np.arange(L) - np.repeat(np.cumsum(n) - n, n)
        kl = kan[sid]
        ui = gr.choice(len(urunler), size=L, p=urun_w)
        adet = np.where(kl == 0, gr.choice([12, 24, 36, 48, 72, 96, 144, 240], size=L, p=[.18, .2, .17, .15, .12, .08, .06, .04]),
                        np.where(kl == 1, gr.randint(1, 5, L), gr.choice([6, 12, 18, 24, 48], size=L)))
        eski = gr.rand(L) < 0.012                                   # yaşlı parti: SKT'ye 30-89 gün kaldı
        lot = gun_i // 28                                           # her ~4 haftada yeni parti: SKT partiyle tutarlı
        lot_basi = gun_ep - (gun_i % 28) * 86400
        skt_ep = np.where(eski, gun_ep + gr.randint(30, 90, L) * 86400, lot_basi + (540 + (ui % 5) * 30) * 86400)
        parti = np.where(eski, 100000 + ui, (ui * 13 + lot) % 9000 + 1000)
        zaman = t0[sid] + k * gr.randint(10, 60, L)
        tes_s = tesno[sid].astype(str)
        ci = cust[sid]
        ham_p.append(pd.DataFrame({
            "tarih": gun, "sevk_zamani": pd.to_datetime(zaman, unit="s"), "personel": kisi[sid],
            "sevkiyat": pd.Series(sevno[sid]).astype(str).str.zfill(10).to_numpy(), "teslimat": tes_s,
            "siparis": pd.Series(tes_s) + "_" + pd.Series(k + 1).astype(str), "kanal": KN[kl], "musteri_kodu": m_kod[ci],
            "musteri": m_no[ci], "teslim_alan": m_ad[ci], "il": m_il[ci], "sku": u_sku[ui], "urun": u_urun[ui],
            "malzeme_turu": "Mamul", "parti": np.where(eski, "HE", "HT") + pd.Series(parti).astype(str).to_numpy(), "skt": pd.to_datetime(skt_ep, unit="s"),
            "adet": adet}))
        sr_p.append(pd.DataFrame({"teslimat": tesno.astype(str), "kanal": KN[kan], "sevk": pd.to_datetime(t0 + n * 60, unit="s")}))
    ham = pd.concat(ham_p, ignore_index=True).sort_values("sevk_zamani", kind="stable").reset_index(drop=True)
    sr = pd.concat(sr_p, ignore_index=True)
    for c in ("sevk_zamani", "skt"):
        ham[c] = ham[c].astype("datetime64[us]")
    sr["sevk"] = sr["sevk"].astype("datetime64[us]")

    # ---- süreç tablosu: sipariş başına adım zaman damgaları (hedeflere yakın ortalama süreler) ----
    rs = np.random.RandomState(seed + 7)

    def sure(ort, sd, lo, hi):
        return pd.to_timedelta(np.clip(rs.normal(ort, sd, len(sr)), lo, hi), unit="h")

    sr["yukleme_basladi"] = sr["sevk"] - pd.Timedelta(minutes=20)
    sr["paket_hazir"] = sr["yukleme_basladi"] - sure(h["sevk_saat"] * 0.9, 0.6, 0.3, 8)
    sr["toplama_bitti"] = sr["paket_hazir"] - sure(h["paketleme_saat"] * 0.9, 0.4, 0.2, 5)
    sr["siparis_alindi"] = sr["toplama_bitti"] - sure(h["toplama_saat"] * 0.95, 1.1, 0.5, 14)
    sr = sr[["teslimat", "kanal", "siparis_alindi", "toplama_bitti", "paket_hazir", "yukleme_basladi", "sevk"]]

    # ---- inbound: mal kabul (kamyon bazında) ----
    ib, ri = [], np.random.RandomState(seed + 3)
    kapi_n = max(int(p["kapilar"]["mal_kabul"]), 1)
    plaka_no = 100
    for gun, adet in ham.groupby("tarih")["adet"].sum().items():
        palet = adet / p["simulasyon"]["palet_basi_adet"] * ri.uniform(0.85, 1.15)
        kamyon = max(int(np.ceil(palet / p["simulasyon"]["kamyon_palet"])), 1)
        for _ in range(kamyon):
            varis = gun + pd.Timedelta(hours=float(ri.uniform(6, 20)))
            bs = varis + pd.Timedelta(hours=float(np.clip(ri.normal(h["bosaltma_saat"] * 0.8, 0.3), 0.1, 4)))
            bb = bs + pd.Timedelta(minutes=int(p["simulasyon"]["kamyon_bosaltma_dk"] * ri.uniform(0.8, 1.2)))
            pt = bb + pd.Timedelta(hours=float(np.clip(ri.normal(h["dock_to_stock_saat"] * 1.05, 1.0), 0.5, 10)))
            plaka_no += 1
            ib.append((gun, f"{34 + ri.randint(0, 40):02d} DT {plaka_no}", int(ri.randint(1, kapi_n + 1)), varis, bs, bb, pt,
                       int(round(palet / kamyon))))
    inbound = pd.DataFrame(ib, columns=["tarih", "plaka", "kapi", "varis", "bosaltma_baslangic", "bosaltma_bitis",
                                        "putaway_bitis", "palet"])
    return {"ham": ham, "inbound": inbound, "surec": sr, "personel": kadro}


def _tam_onbellekli(son_gun, gun_sayisi, p, seed):
    """Üretim ~1 sn sürer; sonuç bellekte ve diske (.onbellek/) saklanır -> sonraki açılışlar anında."""
    anahtar = f"{son_gun:%Y%m%d}_{gun_sayisi}_{seed}_{zlib.crc32(repr((p['kadro'], p['vardiyalar'], p['hedefler'], p['simulasyon'], p['kapilar'])).encode()):x}"
    if anahtar in _BELLEK:
        return _BELLEK[anahtar]
    d = _onbellek_dizini()
    dosya = d / f"demo_{anahtar}.pkl" if d else None
    tam = None
    if dosya is not None and dosya.exists():
        try:
            tam = pd.read_pickle(dosya)
        except Exception:
            tam = None
    if tam is None:
        tam = _tam(son_gun, gun_sayisi, p, seed)
        if dosya is not None:
            try:
                for eski in d.glob("demo_*.pkl"):
                    eski.unlink()
                pd.to_pickle(tam, dosya)
            except OSError:
                pass
    _BELLEK.clear()
    _BELLEK[anahtar] = tam
    return tam


GECMIS_GUN = int(os.environ.get("OPLOG_GECMIS_GUN", "180"))   # bellek sınırlı sunucuda 90 yapılabilir


def uret(bitis, gun_sayisi=GECMIS_GUN, profil=None, seed=42):
    """Son `gun_sayisi` günün (bitis dahil) eksiksiz operasyon verisi. {'ham','inbound','surec','personel'} döner.
    `bitis` bir Timestamp'tir; bitis anından sonraki kayıtlar kesilir (gelecekten kayıt olmaz)."""
    p = profil or dp.varsayilan()
    bitis = pd.Timestamp(bitis)
    tam = _tam_onbellekli(bitis.normalize(), gun_sayisi, p, seed)
    ham = tam["ham"]
    ham = ham[ham["sevk_zamani"] <= bitis].reset_index(drop=True)
    sr, ib = tam["surec"], tam["inbound"]
    return {"ham": ham, "inbound": ib[ib["varis"] <= bitis].reset_index(drop=True),
            "surec": sr[sr["sevk"] <= bitis].reset_index(drop=True), "personel": tam["personel"]}


def acik_siparisler(ham, bugun, n=12, seed=17):
    """Sunum için açık sipariş defteri (sipariş no, müşteri, adet, tamamlanan, termin, öncelik)."""
    rng = np.random.RandomState(seed)
    g = ham.groupby("teslimat").agg(adet=("adet", "sum"), musteri=("teslim_alan", "first")).reset_index()
    g = g[g["adet"] >= 400].sample(n, random_state=seed)
    adet = rng.uniform(14000, 70000, n).round(-2)                   # açık siparişler: birkaç günlük iş
    return pd.DataFrame({
        "siparis_no": "SP" + g["teslimat"].astype(str).str[-7:], "musteri": g["musteri"].values, "adet": adet,
        "tamamlanan": (adet * rng.choice([0, 0.1, 0.25, 0.4, 0.6, 0.85], n)).round(-1),
        "termin": [pd.Timestamp(bugun).normalize() + pd.Timedelta(days=int(x)) for x in rng.randint(1, 5, n)],
        "oncelik": rng.choice(["Yüksek", "Normal", "Normal", "Düşük"], n),
    })


