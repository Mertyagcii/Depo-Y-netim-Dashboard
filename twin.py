"""Dijital ikiz çekirdeği (Serdar - Mimari, Ozan - IoT).

Gerçek veri: Excel'deki sevkiyat satırları (hangi bölgeden, ne zaman, ne kadar).
Profil verisi: Depo ölçüleri, alanlar, kapılar, forklift filosu -> depo_profili.json (şimdilik ÖRNEK değerler).
Simülasyon: Forklift konumları ve pilleri (gerçek IoT verisi bağlanana kadar).
Tüm geometri metre cinsindendir; orijin sol-alt köşe, sevkiyat tarafı altta, mal kabul tarafı üstte.
"""
import numpy as np
import pandas as pd
import plotly.colors as pc
import plotly.graph_objects as go

import depo_profil as dp
import hesaplamalar as h

KOLON = 6
RENK = {"sevkiyat": "#dbeafe", "paketleme": "#e0e7ff", "ofis": "#e5e7eb", "mal_kabul": "#dcfce7",
        "kalite": "#fef9c3", "iade": "#fee2e2", "sarj": "#ccfbf1", "depolama": "#f4f4f1"}


def _p(profil):
    return profil if profil is not None else dp.varsayilan()


def geometri(profil=None):
    """Profilden bina yerleşimi: alt şerit (sevkiyat), orta (raf), üst şerit (mal kabul)."""
    p = _p(profil)
    en = float(p["bina_en_m"])
    alt = [a for a in p["alanlar"] if a["tur"] in dp.ALT_SERIT]
    ust = [a for a in p["alanlar"] if a["tur"] in dp.UST_SERIT]
    alt_d = sum(a["alan_m2"] for a in alt) / en
    ust_d = sum(a["alan_m2"] for a in ust) / en
    orta_d = dp.toplam(p, ["depolama"]) / en
    bloklar, x = [], 0.0
    for a in alt:
        w = a["alan_m2"] / alt_d
        bloklar.append(dict(ad=a["ad"], tur=a["tur"], x=x, y=0.0, w=w, d=alt_d, alan=a["alan_m2"]))
        x += w
    x = 0.0
    for a in ust:
        w = a["alan_m2"] / ust_d
        bloklar.append(dict(ad=a["ad"], tur=a["tur"], x=x, y=alt_d + orta_d, w=w, d=ust_d, alan=a["alan_m2"]))
        x += w
    bloklar.append(dict(ad="Depolama & toplama", tur="depolama", x=0.0, y=alt_d, w=en, d=orta_d,
                        alan=dp.toplam(p, ["depolama"])))
    sev = next((b for b in bloklar if b["tur"] == "sevkiyat"), None)
    dok = (sev["x"] + sev["w"] / 2, alt_d / 2) if sev else (en / 2, alt_d / 2)
    return dict(en=en, boy=alt_d + orta_d + ust_d, alt_d=alt_d, orta_d=orta_d, ust_d=ust_d, bloklar=bloklar,
                dok=dok, ax=float(p["koridor_x_m"]), ay=float(p["koridor_y_m"]), koridor_y=alt_d + p["koridor_y_m"] / 2)


def _toplama_noktasi(r, g):
    """Bölgenin sağındaki dikey koridorda, bölge ortası."""
    return (r.x + r.w + g["ax"] / 2, r.y + r.d / 2)


def yerlesim(d, profil=None, strateji="frekans"):
    """Bölgeleri raf alanına dizer.
    strateji: 'frekans' (çok hareket eden bölge kapıya en yakın = ABC yerleşimi), 'kod' (bölge kodu sırasıyla),
    'rastgele' (karşılaştırma tabanı)."""
    g = geometri(profil)
    x = d.assign(bolge=d["sku"].map(h.bolge_kodu)).groupby("bolge").agg(
        satir=("adet", "size"), adet=("adet", "sum")).sort_values("satir", ascending=False)
    n = len(x)
    satir_sayisi = -(-n // KOLON)
    hw, hd = g["en"] / KOLON, g["orta_d"] / satir_sayisi
    slotlar = [(k * hw, g["alt_d"] + r * hd) for r in range(satir_sayisi) for k in range(KOLON)]

    def uzaklik(s):
        return abs(s[0] + hw - g["ax"] / 2 - g["dok"][0]) + abs(s[1] + g["ay"] + (hd - g["ay"]) / 2 - g["dok"][1])

    slotlar.sort(key=uzaklik)
    s = slotlar[:n]
    sira = {"frekans": list(range(n)), "kod": sorted(range(n), key=lambda i: str(x.index[i])),
            "rastgele": [int(i) for i in np.random.RandomState(3).permutation(n)]}[strateji]
    xs, ys = [0.0] * n, [0.0] * n
    for slot_j, i in enumerate(sira):               # j. en yakın slot, yerleşim sırasındaki j. bölgeye gider
        xs[i], ys[i] = s[slot_j][0], s[slot_j][1] + g["ay"]
    x["x"] = xs
    x["y"] = ys
    x["w"] = hw - g["ax"]
    x["d"] = hd - g["ay"]
    pay = x["adet"].cumsum() / x["adet"].sum()
    x["abc"] = np.where(pay <= 0.70, "A", np.where(pay <= 0.90, "B", "C"))
    x.iloc[0, x.columns.get_loc("abc")] = "A"          # sınırı aşan ilk bölge de A
    return x.reset_index()


def merkez(l):
    return l["x"] + l["w"] / 2, l["y"] + l["d"] / 2


def yogunluk(d, tarih=None, saat=None):
    """Seçilen gün/saat için bölge başına sevk edilen satır sayısı."""
    y = d.dropna(subset=["sevk_zamani"])
    if tarih is not None:
        y = y[y["tarih"] == pd.Timestamp(tarih)]
    if saat is not None:
        y = y[y["sevk_zamani"].dt.hour == saat]
    return y["sku"].map(h.bolge_kodu).value_counts()


def mesafe(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _noktalar(l, g):
    return {r.bolge: _toplama_noktasi(r, g) for r in l.itertuples()}


def rota_siralama(l, bolgeler, profil=None):
    """Mehmet: en yakın komşu rotası. Sevkiyat kapısından çıkıp bölgeleri gezip döner."""
    g = geometri(profil)
    xy = _noktalar(l, g)
    kalan = [b for b in dict.fromkeys(bolgeler) if b in xy]
    konum, sira = g["dok"], []
    while kalan:
        s = min(kalan, key=lambda b: mesafe(konum, xy[b]))
        sira.append(s)
        konum = xy[s]
        kalan.remove(s)
    return sira


def rota_mesafe(l, sira, profil=None):
    g = geometri(profil)
    xy = _noktalar(l, g)
    konum, top = g["dok"], 0.0
    for b in sira:
        top += mesafe(konum, xy[b])
        konum = xy[b]
    return top + mesafe(konum, g["dok"])


def rota_tasarruf(d, l, ornek=300, seed=1, profil=None):
    """Sevkiyat bazında: bölge koduna göre sıralı toplama vs optimize rota (metre).
    Geometri ve bölge koordinatları bir kez hesaplanır (yüzlerce sevkiyatta hızlı)."""
    g = geometri(profil)
    xy = _noktalar(l, g)
    dok = g["dok"]

    def mes(sira):
        konum, top = dok, 0.0
        for b in sira:
            top += mesafe(konum, xy[b])
            konum = xy[b]
        return top + mesafe(konum, dok)

    def en_yakin(bolgeler):
        kalan, konum, sira = [b for b in dict.fromkeys(bolgeler) if b in xy], dok, []
        while kalan:
            s = min(kalan, key=lambda b: mesafe(konum, xy[b]))
            sira.append(s)
            konum = xy[s]
            kalan.remove(s)
        return sira

    s = d.assign(bolge=d["sku"].map(h.bolge_kodu)).groupby("sevkiyat")["bolge"].agg(list)
    s = s[s.map(lambda v: len(set(v)) > 1)]
    if s.empty:
        return pd.DataFrame(columns=["sevkiyat", "bolge_sayisi", "sirasiz_m", "optimize_m"])
    s = s.sample(min(ornek, len(s)), random_state=seed)
    satirlar = []
    for sev, b in s.items():
        naif = sorted(set(b))
        satirlar.append((sev, len(naif), mes([x for x in naif if x in xy]), mes(en_yakin(naif))))
    return pd.DataFrame(satirlar, columns=["sevkiyat", "bolge_sayisi", "sirasiz_m", "optimize_m"])


def filo(profil=None):
    """Profildeki forklift filosunu tek tek araç listesine açar."""
    p = _p(profil)
    return [dict(tip=f["tip"], hiz=float(f["hiz_ms"]), pil_saat=float(f["pil_saat"]))
            for f in p["forkliftler"] for _ in range(int(f["adet"]))]


def kapi_noktalari(profil, g):
    """Kapı merkezleri: ('mal_kabul' | 'sevkiyat', x, y) listesi (y: duvar üzerinde)."""
    return [(tur, x, y) for x, y, tur in _kapilar(profil, g)]


def rota_olustur(l, g, profil, i, seed=7, gorev=16):
    """Bir aracın çevrimsel görev rotası (Ozan). Tek/çift görev dönüşümlü:
    çift  = ÇIKIŞ  : bölgeden palet al -> sevkiyat kapısına götür
    tek   = GİRİŞ  : mal kabul kapısından palet al -> bölgeye yerleştir
    Döner: noktalar [n,2], olaylar [n] (None | (kod, arg)), yük [n-1] (segment yüklü mü)."""
    rng = np.random.RandomState(seed + i)
    zonlar = l.sort_values("satir", ascending=False)
    pay = (zonlar["satir"] / zonlar["satir"].sum()).to_numpy()
    hedefler = zonlar.iloc[rng.choice(len(zonlar), gorev, p=pay)]
    dx, dy = g["dok"]
    yc = g["koridor_y"]
    girisler = [(x, y) for tur, x, y in kapi_noktalari(profil, g) if tur == "mal_kabul"] or [(g["en"] / 2, g["boy"])]
    gx0 = float(l["x"].min()) + float(l["w"].iloc[0]) + g["ax"] / 2
    iy = g["alt_d"] + g["orta_d"] + 3.0
    nok, olay, yuk = [(dx, dy)], [None], []

    def ekle(x, y, ev=None, yuklu=0):
        nok.append((x, y)); olay.append(ev); yuk.append(yuklu)

    for n, r in enumerate(hedefler.itertuples()):
        gx, zy = r.x + r.w + g["ax"] / 2, r.y + r.d / 2
        if n % 2 == 0:
            ekle(dx, yc); ekle(gx, yc); ekle(gx, zy, ("topla", r.bolge))
            ekle(gx, yc, None, 1); ekle(dx, yc, None, 1); ekle(dx, dy, ("sevk", None), 1)
        else:
            kx, _ = girisler[(i + n) % len(girisler)]
            ekle(dx, yc); ekle(gx0, yc); ekle(gx0, iy); ekle(kx, iy, ("al", None))
            ekle(gx, iy, None, 1); ekle(gx, zy, ("yerlestir", r.bolge), 1)
            ekle(gx, iy); ekle(gx0, iy); ekle(gx0, yc); ekle(dx, yc); ekle(dx, dy)
    return np.array(nok, dtype=float), olay, yuk


def forkliftler(l, adet, t_sn, seed=7, profil=None):
    """Ozan: Zamanın fonksiyonu olarak deterministik forklift simülasyonu (filo profilden gelir)."""
    g = geometri(profil)
    araclar = filo(profil) or [dict(tip="Forklift", hiz=1.8, pil_saat=8.0)]
    kayit = []
    for i in range(adet):
        a = araclar[i % len(araclar)]
        nokta, _, yuk = rota_olustur(l, g, profil, i, seed)
        seg = np.abs(np.diff(nokta, axis=0)).sum(axis=1)
        toplam = seg.sum()
        yol = (t_sn * a["hiz"] + i * toplam / max(adet, 1)) % toplam
        k = min(int(np.searchsorted(np.cumsum(seg), yol, side="right")), len(seg) - 1)
        oran = (yol - seg[:k].sum()) / seg[k] if seg[k] else 0
        pos = nokta[k] + (nokta[k + 1] - nokta[k]) * oran
        dongu = a["pil_saat"] * 60
        pil = 100 - ((t_sn / 60 + i * 47) % dongu) / dongu * 80      # her döngüde %100 -> %20
        kayit.append({"id": f"FLK-{i + 1:02d}", "tip": a["tip"], "x": pos[0], "y": pos[1],
                      "durum": "Yüklü" if yuk[k] else "Boş", "pil": float(pil)})
    return pd.DataFrame(kayit)


def _renk(v, vmax, skala="YlOrRd"):
    return pc.sample_colorscale(skala, [0.05 + 0.9 * (v / vmax if vmax else 0)])[0]


def _kapilar(profil, g):
    p = _p(profil)
    out = []
    for tur, adet, y in (("sevkiyat", p["kapilar"]["sevkiyat"], 0.0), ("mal_kabul", p["kapilar"]["mal_kabul"], g["boy"])):
        b = next((b for b in g["bloklar"] if b["tur"] == tur), None)
        if not b or adet <= 0:
            continue
        for i in range(int(adet)):
            out.append((b["x"] + (i + 0.5) * b["w"] / adet, y, tur))
    return out


def fig_2d(l, deger, fl, profil=None, katman="Hareket"):
    """katman: 'Hareket' (deger = bölge başına satır) veya 'Doluluk' (deger = bölge başına % doluluk)."""
    g = geometri(profil)
    fig = go.Figure()
    for b in g["bloklar"]:
        if b["tur"] == "depolama":
            fig.add_shape(type="rect", x0=b["x"], y0=b["y"], x1=b["x"] + b["w"], y1=b["y"] + b["d"],
                          fillcolor=RENK["depolama"], line=dict(width=0), layer="below")
            continue
        fig.add_shape(type="rect", x0=b["x"], y0=b["y"], x1=b["x"] + b["w"], y1=b["y"] + b["d"],
                      fillcolor=RENK[b["tur"]], line=dict(color="#94a3b8", width=1), layer="below")
        fig.add_annotation(x=b["x"] + b["w"] / 2, y=b["y"] + b["d"] / 2, showarrow=False, align="center",
                           text=f"<b>{b['ad']}</b><br>{b['alan']:,.0f} m²".replace(",", "."),
                           font=dict(size=10, color="#334155"))
    vmax = max(float(deger.max()), 1.0) if len(deger) else 1.0
    if katman == "Doluluk":
        vmax = 100.0
    for r in l.itertuples():
        v = float(deger.get(r.bolge, 0))
        yaz = f"{v:.0f}%" if katman == "Doluluk" else f"{int(v)}"
        dolgu = (_renk(v, vmax, "Blues") if katman == "Doluluk" else _renk(v, vmax)) if v else "#e2e8f0"
        fig.add_shape(type="rect", x0=r.x, y0=r.y, x1=r.x + r.w, y1=r.y + r.d, line=dict(color="#475569", width=1),
                      fillcolor=dolgu)
        koyu_zemin = v / vmax > 0.65 if v else False
        fig.add_annotation(x=r.x + r.w / 2, y=r.y + r.d / 2, text=f"<b>{r.bolge}</b><br>{r.abc}·{yaz}",
                           showarrow=False, font=dict(size=10, color="white" if koyu_zemin else "#0f172a"))
    fig.add_shape(type="rect", x0=0, y0=0, x1=g["en"], y1=g["boy"], line=dict(color="#1c1d20", width=3))
    for kx, ky, tur in _kapilar(profil, g):
        fig.add_shape(type="rect", x0=kx - 1.6, x1=kx + 1.6, y0=ky - 1.0, y1=ky + 1.0,
                      fillcolor="#2563eb" if tur == "sevkiyat" else "#16a34a", line=dict(color="white", width=1))
    renk = np.where(fl["pil"] < 25, "#dc2626", np.where(fl["durum"] == "Yüklü", "#16a34a", "#2563eb"))
    fig.add_trace(go.Scatter(x=fl["x"], y=fl["y"], mode="markers", marker=dict(
        size=11, symbol="square", color=renk, line=dict(color="white", width=1)),
        customdata=fl[["id", "tip", "durum", "pil"]],
        hovertemplate="%{customdata[0]} · %{customdata[1]}<br>%{customdata[2]} · Pil %{customdata[3]:.0f}%<extra></extra>"))
    fig.add_annotation(x=g["en"] / 2, y=-5, showarrow=False, font=dict(size=11, color="#64748b"),
                       text=f"◀ {g['en']:.0f} m ▶  ·  {g['en'] * g['boy']:,.0f} m²  ·  sevkiyat tarafı (mavi kapılar)".replace(",", "."))
    fig.update_xaxes(visible=False, scaleanchor="y", range=[-4, g["en"] + 4])
    fig.update_yaxes(visible=False, range=[-8, g["boy"] + 4])
    fig.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, dragmode="pan",
                      plot_bgcolor="white")
    return fig


def _kutu(x, y, z, dx, dy, dz):
    vx = [x, x + dx, x + dx, x, x, x + dx, x + dx, x]
    vy = [y, y, y + dy, y + dy, y, y, y + dy, y + dy]
    vz = [z, z, z, z, z + dz, z + dz, z + dz, z + dz]
    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    k = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]
    return vx, vy, vz, i, j, k


def fig_3d(l, deger, fl, profil=None, katman="Hareket"):
    g = geometri(profil)
    vmax = 100.0 if katman == "Doluluk" else max(float(deger.max()), 1.0) if len(deger) else 1.0
    X, Y, Z, I, J, K, C = [], [], [], [], [], [], []
    for r in l.itertuples():
        v = float(deger.get(r.bolge, 0))
        vx, vy, vz, i, j, k = _kutu(r.x, r.y, 0, r.w, r.d, 1.5 + 10 * v / vmax)
        o = len(X)
        X += vx; Y += vy; Z += vz
        I += [a + o for a in i]; J += [a + o for a in j]; K += [a + o for a in k]
        C += [v] * 8
    fig = go.Figure()
    for b in g["bloklar"]:
        if b["tur"] == "depolama":
            continue
        vx, vy, vz, i, j, k = _kutu(b["x"], b["y"], 0, b["w"], b["d"], 0.4)
        fig.add_trace(go.Mesh3d(x=vx, y=vy, z=vz, i=i, j=j, k=k, color=RENK[b["tur"]], flatshading=True,
                                hovertext=b["ad"], hoverinfo="text", showscale=False))
    vx, vy, vz, i, j, k = _kutu(0, g["alt_d"], -0.2, g["en"], g["orta_d"], 0.2)
    fig.add_trace(go.Mesh3d(x=vx, y=vy, z=vz, i=i, j=j, k=k, color="#e7e7e2", hoverinfo="skip"))
    fig.add_trace(go.Mesh3d(x=X, y=Y, z=Z, i=I, j=J, k=K, intensity=C, colorscale="Blues" if katman == "Doluluk" else "YlOrRd",
                            cmin=0, cmax=vmax, showscale=False, flatshading=True, hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=fl["x"], y=fl["y"], z=[1.0] * len(fl), mode="markers",
                               marker=dict(size=4, color="#2563eb"), hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=l["x"] + l["w"] / 2, y=l["y"] + l["d"] / 2, z=[13.5] * len(l), mode="text",
                               text=l["bolge"], textfont=dict(size=9), hoverinfo="skip"))
    fig.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      scene=dict(aspectmode="manual", aspectratio=dict(x=g["en"] / g["boy"], y=1, z=0.22),
                                 xaxis_visible=False, yaxis_visible=False, zaxis_visible=False,
                                 camera=dict(eye=dict(x=0.15, y=-1.55, z=0.95))))
    return fig
