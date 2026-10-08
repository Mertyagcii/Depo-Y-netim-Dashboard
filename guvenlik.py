"""Güvenlik radarı (Ozan - IoT): forklift trafiğinde yakın geçiş (near-miss) ve kesişim noktası analizi.

Araç rotaları simülasyondur (gerçek telemetri bağlanınca aynı analiz gerçek konumlarla çalışır).
Yakın geçiş: iki aracın aralarındaki mesafenin eşikten (varsayılan 3 m) küçük olduğu her ayrı karşılaşma.
"""
import numpy as np
import pandas as pd

import twin as tw


def konumlar(l, profil, zamanlar, adet=None, seed=7):
    """Tüm araçların `zamanlar` (sn) anındaki konumları: [T, n, 2] dizisi."""
    g = tw.geometri(profil)
    araclar = tw.filo(profil)
    n = adet or len(araclar)
    out = np.zeros((len(zamanlar), n, 2))
    for i in range(n):
        a = araclar[i % len(araclar)]
        nok, _, _ = tw.rota_olustur(l, g, profil, i, seed)
        seg = np.abs(np.diff(nok, axis=0)).sum(axis=1)
        cum = np.concatenate([[0], np.cumsum(seg)])
        yol = (np.asarray(zamanlar) * a["hiz"] + i * cum[-1] / max(n, 1)) % cum[-1]
        k = np.clip(np.searchsorted(cum, yol, side="right") - 1, 0, len(seg) - 1)
        oran = np.where(seg[k] > 0, (yol - cum[k]) / np.where(seg[k] > 0, seg[k], 1), 0)
        out[:, i, :] = nok[k] + (nok[k + 1] - nok[k]) * oran[:, None]
    # araçlar bütün gün aralıksız çalışmaz: 10 dakikalık bloklarla ~%40 görev oranı (kalan zamanda beklemede)
    aktif = ((np.asarray(zamanlar)[:, None] // 600 + np.arange(n) * 7) % 5) < 2
    out[~aktif] = np.nan
    return out


def yakin_gecis(l, profil, saat0=6, saat1=15, adim=10, esik=3.0, adet=None):
    """Vardiya boyunca yakın geçişleri sayar. Döner: dict(olay, nokta DataFrame, saatlik DataFrame, kesisim DataFrame)."""
    g = tw.geometri(profil)
    z = np.arange(saat0 * 3600, saat1 * 3600, adim)
    p = konumlar(l, profil, z, adet)
    n = p.shape[1]
    iu, ju = np.triu_indices(n, 1)
    d = np.linalg.norm(p[:, iu, :] - p[:, ju, :], axis=2)                  # [T, pairs]
    # kapıya çok yakın bölgeler (rampa) hariç: orada yakın durmak normal
    dok = np.array(g["dok"])
    yakin_dok = (np.linalg.norm(p[:, iu, :] - dok, axis=2) < 8) | (np.linalg.norm(p[:, ju, :] - dok, axis=2) < 8)
    yakin = (d < esik) & ~yakin_dok
    baslangic = yakin & ~np.vstack([np.zeros((1, yakin.shape[1]), bool), yakin[:-1]])     # ayrı karşılaşmanın ilk anı
    t_idx, pair_idx = np.nonzero(baslangic)
    mx = (p[t_idx, iu[pair_idx], 0] + p[t_idx, ju[pair_idx], 0]) / 2
    my = (p[t_idx, iu[pair_idx], 1] + p[t_idx, ju[pair_idx], 1]) / 2
    nokta = pd.DataFrame({"x": mx, "y": my, "t": z[t_idx], "saat": (z[t_idx] // 3600).astype(int),
                          "a": [f"FLK-{i + 1:02d}" for i in iu[pair_idx]], "b": [f"FLK-{j + 1:02d}" for j in ju[pair_idx]]})
    if len(nokta):                                   # aynı çift 90 sn içinde tekrar yaklaşırsa tek olay say
        nokta = nokta.sort_values(["a", "b", "t"])
        ayni = (nokta["a"] == nokta["a"].shift()) & (nokta["b"] == nokta["b"].shift()) & (nokta["t"].diff() < 90)
        nokta = nokta[~ayni].reset_index(drop=True)
    saatlik = (nokta.groupby("saat").size().reindex(range(saat0, saat1), fill_value=0).rename("olay").reset_index()
               if len(nokta) else pd.DataFrame({"saat": range(saat0, saat1), "olay": 0}))
    if len(nokta):
        h = nokta.assign(cx=(nokta["x"] // 10 * 10 + 5).round(0), cy=(nokta["y"] // 10 * 10 + 5).round(0))
        kes = h.groupby(["cx", "cy"]).size().rename("olay").reset_index().sort_values("olay", ascending=False).head(6)
        kes["konum"] = [f"x≈{r.cx:.0f} m, y≈{r.cy:.0f} m" for r in kes.itertuples()]
    else:
        kes = pd.DataFrame(columns=["cx", "cy", "olay", "konum"])
    return {"olay": int(len(nokta)), "nokta": nokta, "saatlik": saatlik, "kesisim": kes.reset_index(drop=True), "esik": esik,
            "araclar": n, "saat0": saat0, "saat1": saat1}
