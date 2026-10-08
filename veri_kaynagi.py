"""Veri kaynağı katmanı (Serdar - Mimari): uygulama verisini DEMO'dan ya da GERÇEK bir API'den alır.

Uygulamanın geri kalanı yalnızca buradan dönen tabloları kullanır; kaynak değişince sayfalar değişmez.
Ayarlar kaynak.json'dadır (mod: "demo" | "api"). API ayrıntıları için bkz. API_SOZLESME.md.
API'ye ulaşılamazsa ya da bir uç nokta eksikse sayfalar boş kalmaz: ilgili kısım demo veriyle tamamlanır ve
kullanıcıya hangi kısmın demo olduğu söylenir.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

import demo_veri
import depo_profil as dp

DOSYA = Path(__file__).parent / "kaynak.json"

# Standart şema: zorunlu / isteğe bağlı sütunlar (API alanları 'alanlar' eşlemesiyle bunlara çevrilir)
SEMA = {
    "sevkiyat": {"zorunlu": ["sevk_zamani", "personel", "sevkiyat", "teslimat", "kanal", "sku", "urun", "adet"],
                 "istege_bagli": ["tarih", "siparis", "musteri_kodu", "musteri", "teslim_alan", "il", "malzeme_turu", "parti", "skt"]},
    "inbound": {"zorunlu": ["plaka", "kapi", "varis", "bosaltma_baslangic", "bosaltma_bitis", "putaway_bitis", "palet"],
                "istege_bagli": ["tarih"]},
    "surec": {"zorunlu": ["teslimat", "siparis_alindi", "toplama_bitti", "paket_hazir", "yukleme_basladi", "sevk"],
              "istege_bagli": ["kanal"]},
    "forklift": {"zorunlu": ["id", "x", "y"], "istege_bagli": ["tip", "durum", "pil"]},
    "siparis": {"zorunlu": ["siparis_no", "adet"], "istege_bagli": ["musteri", "tamamlanan", "termin", "oncelik"]},
}
ZAMAN = {"sevkiyat": ["sevk_zamani", "skt", "tarih"], "inbound": ["varis", "bosaltma_baslangic", "bosaltma_bitis", "putaway_bitis", "tarih"],
         "surec": ["siparis_alindi", "toplama_bitti", "paket_hazir", "yukleme_basladi", "sevk"], "forklift": [], "siparis": ["termin"]}
SAYISAL = {"sevkiyat": ["adet"], "inbound": ["kapi", "palet"], "surec": [], "forklift": ["x", "y", "pil"],
           "siparis": ["adet", "tamamlanan"]}

VARSAYILAN = {
    "mod": "demo",
    "api": {
        "base_url": "",
        "token_env": "DEPO_API_TOKEN",
        "zaman_asimi_sn": 8,
        "uclar": {"sevkiyat": "/shipments", "inbound": "/inbound", "surec": "/process", "forklift": "/forklifts",
                  "siparis": "/orders"},
        "alanlar": {t: {} for t in SEMA},          # {standart_sütun: apideki_alan_adı}; boşsa alan adları aynıdır
    },
}


def yukle_ayar(dosya=DOSYA):
    ayar = json.loads(json.dumps(VARSAYILAN))
    try:
        if Path(dosya).exists():
            ek = json.loads(Path(dosya).read_text(encoding="utf-8"))
            ayar["mod"] = ek.get("mod", "demo")
            for k, v in ek.get("api", {}).items():
                if isinstance(v, dict) and isinstance(ayar["api"].get(k), dict):
                    ayar["api"][k].update(v)
                else:
                    ayar["api"][k] = v
    except Exception:
        return json.loads(json.dumps(VARSAYILAN))
    return ayar


def kaydet_ayar(ayar, dosya=DOSYA):
    Path(dosya).write_text(json.dumps(ayar, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------------------------------
def _zaman(s):
    """Saat dilimi içeren (Z, +03:00) zaman damgaları Türkiye saatine çevrilir; diğerleri olduğu gibi okunur."""
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.tz_convert("Europe/Istanbul").dt.tz_localize(None) if s.dt.tz is not None else s
    metin = s.astype(str)
    if metin.str.contains(r"(?:Z|[+-]\d\d:?\d\d)$", regex=True).any():
        return pd.to_datetime(s, errors="coerce", utc=True).dt.tz_convert("Europe/Istanbul").dt.tz_localize(None)
    return pd.to_datetime(s, errors="coerce", format="mixed")


def normalize(df, tur, alanlar=None):
    """API'den gelen tabloyu standart şemaya çevirir. Zorunlu sütun yoksa ValueError; isteğe bağlılar doldurulur."""
    sema = SEMA[tur]
    ters = {v: k for k, v in (alanlar or {}).items() if v}
    d = df.rename(columns=ters).copy()
    eksik = [c for c in sema["zorunlu"] if c not in d]
    if eksik:
        raise ValueError(f"'{tur}' verisinde zorunlu alan yok: {', '.join(eksik)}. Gelen alanlar: {', '.join(map(str, df.columns[:12]))}")
    for c in ZAMAN[tur]:
        if c in d:
            d[c] = _zaman(d[c])
    for c in SAYISAL[tur]:
        if c in d:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if tur == "sevkiyat":
        d = d.dropna(subset=["sevk_zamani", "adet"])
        d["adet"] = d["adet"].clip(lower=0)
        d["personel"] = d["personel"].fillna("Atanmamış").astype(str)
        d["tarih"] = d["sevk_zamani"].dt.normalize()
        for c, v in (("siparis", None), ("musteri_kodu", ""), ("musteri", ""), ("teslim_alan", ""), ("il", ""),
                     ("malzeme_turu", "Mamul"), ("parti", "")):
            if c not in d:
                d[c] = (d["teslimat"].astype(str) + "_1") if c == "siparis" else v
            d[c] = d[c].fillna("" if c != "malzeme_turu" else "Mamul")
        d["skt"] = d["skt"] if "skt" in d else d["tarih"] + pd.Timedelta(days=720)
        d["skt"] = d["skt"].fillna(d["tarih"] + pd.Timedelta(days=720))
        d["sevkiyat"] = d["sevkiyat"].astype(str)
        d["teslimat"] = d["teslimat"].astype(str)
        d["sku"] = d["sku"].astype(str)
        d["kanal"] = d["kanal"].fillna("Diğer").astype(str)
        d = d.sort_values("sevk_zamani").reset_index(drop=True)
    elif tur == "inbound":
        d["tarih"] = d["varis"].dt.normalize()
    elif tur == "surec":
        if "kanal" not in d:
            d["kanal"] = "Diğer"
    elif tur == "forklift":
        for c, v in (("tip", "Forklift"), ("durum", "Boş"), ("pil", 100.0)):
            if c not in d:
                d[c] = v
            d[c] = d[c].fillna(v)
    elif tur == "siparis":
        for c, v in (("musteri", ""), ("tamamlanan", 0.0), ("oncelik", "Normal")):
            if c not in d:
                d[c] = v
            d[c] = d[c].fillna(v)
        if "termin" not in d:
            d["termin"] = pd.NaT
    return d


class ApiHata(Exception):
    pass


class ApiKaynak:
    def __init__(self, ayar):
        self.a = ayar["api"]

    def _istek(self, uc):
        taban = self.a["base_url"].strip().rstrip("/")
        if not taban.lower().startswith(("http://", "https://")):
            raise ApiHata("base_url http:// veya https:// ile başlamalı.")
        istek = urllib.request.Request(taban + "/" + self.a["uclar"][uc].lstrip("/"),
                                       headers={"Accept": "application/json"})
        token = os.environ.get(self.a.get("token_env") or "")
        if token:
            istek.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(istek, timeout=float(self.a.get("zaman_asimi_sn", 8))) as r:
                govde = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise ApiHata(f"{uc}: HTTP {e.code}") from e
        except Exception as e:
            raise ApiHata(f"{uc}: {type(e).__name__}: {e}") from e
        if isinstance(govde, dict):
            govde = next((govde[k] for k in ("data", "items", "results") if k in govde), None)
        if not isinstance(govde, list):
            raise ApiHata(f"{uc}: JSON dizi (liste) bekleniyordu.")
        return govde

    def tablo(self, uc):
        veri = self._istek(uc)
        return normalize(pd.DataFrame(veri), uc, self.a["alanlar"].get(uc))

    def test(self):
        """Her uç nokta için (durum, satır, alanlar, hata) döner."""
        sonuc = {}
        for uc in SEMA:
            try:
                veri = self._istek(uc)
                df = pd.DataFrame(veri)
                try:
                    normalize(df, uc, self.a["alanlar"].get(uc))
                    sonuc[uc] = ("tamam", len(df), ", ".join(map(str, df.columns[:10])), "")
                except ValueError as e:
                    sonuc[uc] = ("alan eksik", len(df), ", ".join(map(str, df.columns[:10])), str(e))
            except ApiHata as e:
                sonuc[uc] = ("ulaşılamadı", 0, "", str(e))
        return sonuc


def paket(simdi, profil=None, ayar=None):
    """Uygulamanın kullandığı veri paketini döner: ({'ham','inbound','surec','personel'}, bilgi).
    bilgi = {'mod': 'demo'|'api', 'demo_parcalar': [...], 'hata': str|None}"""
    ayar = ayar or yukle_ayar()
    p = profil or dp.varsayilan()
    bilgi = {"mod": "demo", "demo_parcalar": [], "hata": None}
    if ayar["mod"] == "api" and ayar["api"]["base_url"].strip():
        api = ApiKaynak(ayar)
        try:
            ham = api.tablo("sevkiyat")
            demo = demo_veri.uret(simdi, profil=p)
            out = {"ham": ham, "personel": demo["personel"]}
            for parca in ("inbound", "surec"):
                try:
                    out[parca] = api.tablo(parca)
                except (ApiHata, ValueError):
                    out[parca] = demo[parca]
                    bilgi["demo_parcalar"].append(parca)
            bilgi["mod"] = "api"
            return out, bilgi
        except (ApiHata, ValueError) as e:
            bilgi["hata"] = str(e)                      # API çalışmıyor: sunum bozulmasın, demoya dön
    return demo_veri.uret(simdi, profil=p), bilgi


def siparisler(simdi, ham, ayar=None):
    """Açık sipariş defteri: API'den (varsa) ya da demo."""
    ayar = ayar or yukle_ayar()
    if ayar["mod"] == "api" and ayar["api"]["base_url"].strip():
        try:
            return ApiKaynak(ayar).tablo("siparis")
        except (ApiHata, ValueError):
            pass
    return demo_veri.acik_siparisler(ham, simdi)


def telemetri(ayar=None):
    """Canlı forklift telemetrisi (id, tip, x, y, durum, pil) ya da None (demo: simülasyon kullanılır)."""
    ayar = ayar or yukle_ayar()
    if ayar["mod"] == "api" and ayar["api"]["base_url"].strip():
        try:
            return ApiKaynak(ayar).tablo("forklift")
        except (ApiHata, ValueError):
            return None
    return None
