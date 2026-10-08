"""Sipariş planlama: ilerleme, adam-gün ihtiyacı, tahmini bitiş ve termin riski (Mehmet, Selin).

Kurallar:
- 1 adam-gün = UPH x vardiya saati kadar adet.
- İş günleri Pazartesi-Cumartesi (Pazar tatil).
- Siparişler sırayla işlenir: önce öncelik (Yüksek > Normal > Düşük), sonra termin (en yakın önce).
- Her gün tüm ekibin kapasitesi (personel x UPH x vardiya) sırayla siparişlere dağıtılır.
"""
import numpy as np
import pandas as pd

import hesaplamalar as h

SUTUNLAR = ["siparis_no", "musteri", "adet", "tamamlanan", "termin", "oncelik"]
ONCELIK = {"Yüksek": 0, "Normal": 1, "Düşük": 2}
HAFTA = "1111110"


def bos():
    return pd.DataFrame({"siparis_no": pd.Series(dtype="str"), "musteri": pd.Series(dtype="str"),
                         "adet": pd.Series(dtype="float"), "tamamlanan": pd.Series(dtype="float"),
                         "termin": pd.Series(dtype="datetime64[ns]"), "oncelik": pd.Series(dtype="str")})


def _tarih(s):
    """ISO (2026-10-12) olduğu gibi; GG.AA.YYYY / GG/AA/YYYY gün-ay sırasıyla okunur."""
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s)
    iso = pd.to_datetime(s, errors="coerce", format="ISO8601")
    kalan = iso.isna() & s.notna()
    if kalan.any():
        iso[kalan] = pd.to_datetime(s[kalan], errors="coerce", format="mixed", dayfirst=True)
    return iso


def temizle(df):
    """Kullanıcıdan gelen tabloyu (eksik/hatalı hücreler dahil) güvenli biçime getirir."""
    d = df.copy()
    for c in SUTUNLAR:
        if c not in d:
            d[c] = None
    d = d[SUTUNLAR]
    d = d[d["siparis_no"].notna() & (d["siparis_no"].astype(str).str.strip() != "")].copy()
    d["siparis_no"] = d["siparis_no"].astype(str).str.strip()
    d["musteri"] = d["musteri"].fillna("").astype(str)
    d["adet"] = pd.to_numeric(d["adet"], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0).clip(lower=0)
    d["tamamlanan"] = (pd.to_numeric(d["tamamlanan"], errors="coerce").replace([np.inf, -np.inf], np.nan)
                       .fillna(0).clip(lower=0))
    d["tamamlanan"] = np.minimum(d["tamamlanan"], d["adet"])
    d["termin"] = _tarih(d["termin"]).dt.normalize()
    d["oncelik"] = d["oncelik"].where(d["oncelik"].isin(ONCELIK), "Normal")
    return d.reset_index(drop=True)


def _no(x):
    s = str(x).strip()
    return (s.lstrip("0") or "0") if s else ""


def eslestir(df, ham):
    """Sipariş numarası; Excel'deki teslimat / sevkiyat / sipariş numarasıyla eşleşirse
    tamamlanan adet gerçek sevkiyattan alınır. Önce birebir eşleşme aranır; baştaki sıfırlar
    yalnızca listede aynı sadeleşmiş numaraya sahip başka sipariş yoksa yok sayılır.
    (Eşleşen sayısı, yeni tablo) döner."""
    d = temizle(df)
    kaynak = [ham["teslimat"], ham["sevkiyat"], ham["siparis"].astype(str).str.split("_").str[0]]
    birebir = [ham.groupby(k.astype(str).str.strip())["adet"].sum() for k in kaynak]
    sade = [ham.groupby(k.astype(str).map(_no))["adet"].sum() for k in kaynak]
    tekil = d["siparis_no"].map(_no).value_counts()
    eslesen = 0
    for i, no in d["siparis_no"].items():
        v = max(float(t.get(no, 0)) for t in birebir)
        if v == 0 and tekil.get(_no(no), 0) == 1:
            v = max(float(t.get(_no(no), 0)) for t in sade)
        if v > 0:
            d.at[i, "tamamlanan"] = min(v, d.at[i, "adet"])
            eslesen += 1
    return eslesen, d


ALIAS = {"siparis_no": ["siparis_no", "siparis no", "sipariş no", "sipariş", "siparis", "sipariş numarası", "no"],
         "musteri": ["musteri", "müşteri", "müşteri adı", "musteri adi"],
         "adet": ["adet", "miktar", "toplam adet", "sipariş adedi"],
         "tamamlanan": ["tamamlanan", "tamamlanan adet", "sevk edilen", "hazırlanan"],
         "termin": ["termin", "termin tarihi", "teslim tarihi", "sevk tarihi"],
         "oncelik": ["oncelik", "öncelik"]}


def sutun_esle(df):
    """Yüklenen dosyanın başlıklarını (Türkçe/İngilizce varyantlar) standart sütunlara eşler.
    Sipariş no ve adet yoksa ValueError verir."""
    ad = {str(c).strip().lower(): c for c in df.columns}
    yeni = pd.DataFrame(index=df.index)
    for hedef, adaylar in ALIAS.items():
        for a in adaylar:
            if a in ad:
                yeni[hedef] = df[ad[a]]
                break
    eksik = [c for c in ("siparis_no", "adet") if c not in yeni]
    if eksik:
        raise ValueError("Zorunlu sütun bulunamadı: " + ", ".join(eksik) +
                         ". Başlıklar: " + ", ".join(map(str, df.columns[:8])))
    return yeni

def ornek(ham, bugun, n=10, seed=3):
    """Gerçek sevkiyat gruplarından DEMO sipariş listesi üretir (deneme amaçlıdır)."""
    g = ham.groupby("teslimat").agg(adet=("adet", "sum"), musteri=("teslim_alan", "first")).reset_index()
    buyuk = g[g["adet"] >= 3000]                                # deneme için anlamlı büyüklükte siparişler
    g = (buyuk if len(buyuk) >= n else g[g["adet"] > 0]).sample(n, random_state=seed)
    rng = np.random.RandomState(seed)
    out = pd.DataFrame({
        "siparis_no": g["teslimat"].astype(str).values, "musteri": g["musteri"].fillna("").astype(str).values,
        "adet": g["adet"].values.astype(float),
        "tamamlanan": (g["adet"].values * rng.choice([0, 0, 0.25, 0.5, 0.8], len(g))).round(0),
        "termin": [pd.Timestamp(bugun) + pd.Timedelta(days=int(x)) for x in rng.randint(1, 8, len(g))],
        "oncelik": rng.choice(["Yüksek", "Normal", "Normal", "Düşük"], len(g)),
    })
    return temizle(out)


def _is_gunu(baslangic, i):
    d0 = np.busday_offset(pd.Timestamp(baslangic).date(), 0, roll="forward", weekmask=HAFTA)
    return pd.Timestamp(np.busday_offset(d0, i, weekmask=HAFTA))


def planla(df, baslangic, personel, uph, vardiya=h.VARDIYA_SAATI):
    """Planı hesaplar. (siparis_tablosu, gunluk_yuk, ozet) döner; tablo işlem sırasındadır."""
    d = temizle(df)
    adam_gun_adedi = uph * vardiya                       # 1 adam-günde kaç adet
    kap = personel * adam_gun_adedi
    d["kalan"] = d["adet"] - d["tamamlanan"]
    d["ilerleme"] = np.where(d["adet"] > 0, d["tamamlanan"] / d["adet"].where(d["adet"] > 0, 1), 1.0)
    d["adam_gun"] = d["kalan"] / adam_gun_adedi if adam_gun_adedi > 0 else np.nan
    d["_o"] = d["oncelik"].map(ONCELIK)
    d = d.sort_values(["_o", "termin"], na_position="last", kind="stable").drop(columns="_o").reset_index(drop=True)
    d["baslangic"] = pd.NaT
    d["bitis"] = pd.NaT
    yuk = {}
    ufuk_asildi = kap > 0 and d["kalan"].sum() / kap > 730      # 2 yıldan uzun plan: hesaplamayı kes
    if kap > 0 and not ufuk_asildi:
        gun_i, kullanilan = 0, 0.0
        for i in d.index[d["kalan"] > 0]:
            kalan = float(d.at[i, "kalan"])
            ilk = True
            while kalan > 1e-9:
                bos_kap = kap - kullanilan
                if bos_kap <= 1e-9:
                    gun_i, kullanilan = gun_i + 1, 0.0
                    continue
                al = min(bos_kap, kalan)
                t = _is_gunu(baslangic, gun_i)
                if ilk:
                    d.at[i, "baslangic"], ilk = t, False
                yuk[t] = yuk.get(t, 0.0) + al
                kalan -= al
                kullanilan += al
            d.at[i, "bitis"] = _is_gunu(baslangic, gun_i)
    d["baslangic"] = pd.to_datetime(d["baslangic"])
    d["bitis"] = pd.to_datetime(d["bitis"])

    # termine yetişmek için gereken asgari personel (sıralı birikimli iş yükü / kalan iş günü)
    d0 = pd.Timestamp(_is_gunu(baslangic, 0))
    kum = d["adam_gun"].fillna(0).cumsum()
    gunler = pd.Series([np.nan if pd.isna(t) else float(np.busday_count(d0.date(), (t + pd.Timedelta(days=1)).date(),
                                                                         weekmask=HAFTA)) for t in d["termin"]],
                       index=d.index, dtype="float64")
    d["asgari_personel"] = np.where((gunler > 0) & (d["kalan"] > 0), np.ceil(kum / gunler.where(gunler > 0, 1)), np.nan)

    def durum(r):
        if r["kalan"] <= 0:
            return "Tamamlandı"
        if pd.isna(r["bitis"]):
            return "Ufuk dışı" if ufuk_asildi else "Kapasite yok"
        if pd.isna(r["termin"]):
            return "Termin yok"
        if r["bitis"] > r["termin"]:
            return "Gecikir"
        return "Riskli" if r["bitis"] == r["termin"] else "Zamanında"

    d["durum"] = d.apply(durum, axis=1) if len(d) else pd.Series(dtype="str")
    y = pd.DataFrame({"tarih": list(yuk), "yuk": list(yuk.values())}).sort_values("tarih").reset_index(drop=True)
    y["kapasite"] = kap
    y["doluluk"] = y["yuk"] / kap * 100 if kap > 0 else np.nan

    acik = d[d["kalan"] > 0]
    gecikme_var = (d["durum"] == "Gecikir") | (d["termin"].notna() & (d["termin"] < d0) & (d["kalan"] > 0))
    ozet = {
        "siparis": len(d), "acik": len(acik), "kalan_adet": float(d["kalan"].sum()),
        "toplam_adet": float(d["adet"].sum()), "adam_gun": float(d["adam_gun"].sum()) if len(d) else 0.0,
        "ilerleme": float(d["tamamlanan"].sum() / d["adet"].sum()) if d["adet"].sum() > 0 else 1.0,
        "bitis": acik["bitis"].max() if len(acik) else pd.NaT,
        "asgari_personel": float(d["asgari_personel"].max()) if d["asgari_personel"].notna().any() else np.nan,
        "gecikir": int(gecikme_var.sum()), "riskli": int((d["durum"] == "Riskli").sum()),
        "kapasite_gun": kap,
    }
    return d, y, ozet




