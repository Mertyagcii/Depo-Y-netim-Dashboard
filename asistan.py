"""Operasyon asistanı (sohbet): Claude API ile ya da anahtar yoksa yerel kural motoruyla (Ayşe, Mehmet).

- ANTHROPIC_API_KEY (ortam değişkeni ya da Streamlit secret) tanımlıysa soru + özet veri Claude'a gönderilir.
  DİKKAT: bu durumda özet operasyon verileri Anthropic API'ye gider. Anahtar yoksa hiçbir veri dışarı çıkmaz.
- Anahtar yoksa ya da API hata verirse yerel asistan aynı verilerle (kural tabanlı) cevap verir; sohbet hiç boş kalmaz.
"""
import json
import math
import os
import re
import urllib.error
import urllib.request

SISTEM = ("Sen OPLOG depo operasyon asistanısın. Yalnızca sana verilen veri özetine dayanarak Türkçe, kısa ve rakamlı cevap ver. "
          "Verilerde olmayan bir şeyi uydurma; bilmiyorsan 'bu veride yok' de. Gerekirse 2-4 maddelik öneri ekle.")


def anahtar():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def claude_sor(soru, baglam, gecmis=(), api_key=None, model=None, taban=None, zaman_asimi=40):
    """Claude Messages API'sine çağrı. Metin döner; hata olursa istisna fırlatır."""
    api_key = api_key or anahtar()
    if not api_key:
        raise RuntimeError("API anahtarı yok")
    model = model or os.environ.get("OPLOG_MODEL", "claude-sonnet-5-5")
    taban = (taban or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")).rstrip("/")
    mesajlar = [{"role": r, "content": m} for r, m in list(gecmis)[-6:]]
    mesajlar.append({"role": "user", "content": f"VERİ ÖZETİ:\n{baglam}\n\nSORU: {soru}"})
    govde = json.dumps({"model": model, "max_tokens": 800, "system": SISTEM, "messages": mesajlar}).encode()
    istek = urllib.request.Request(taban + "/v1/messages", data=govde, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as r:
            cevap = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API HTTP {e.code}") from e
    return "".join(b.get("text", "") for b in cevap.get("content", []) if b.get("type") == "text").strip()


def baglam_metni(c):
    """Bağlam sözlüğünü modele/yerel motora uygun kısa metne çevirir."""
    sat = [f"Dönem: {c['donem']}", f"Toplam çıkış: {c['adet']:,.0f} adet, ortalama UPH {c['uph']:.0f} adet/saat, günlük ort. personel {c['personel']:.1f}",
           f"Kadro: {c['kadro']} kişi ({c['toplayici']} toplayıcı), forklift {c['forklift']}, palet doluluğu %{c['doluluk']:.0f}"]
    sat.append("En yoğun saatler: " + ", ".join(f"{int(r.saat)}:00 ({r.satir_gun_ort:.0f} satır)" for r in c["saatlik"].nlargest(3, "satir_gun_ort").itertuples()))
    sat.append("En hareketli bölgeler: " + ", ".join(f"{r.bolge} ({r.satir} satır)" for r in c["bolge"].head(5).itertuples()))
    sat.append("7 gün tahmin: " + ", ".join(f"{r.tarih:%d.%m} {r.tahmin_adet:,.0f} adet / {r.gereken_personel} kişi" for r in c["tahmin"].itertuples()))
    sat.append("Süreç süreleri: " + ", ".join(f"{r.adim} {r.gerceklesen_saat:.1f}sa (hedef {r.hedef_saat:.1f}, {r.durum})" for r in c["sureler"].itertuples()))
    if len(c["plan"]):
        sat.append("Açık siparişler: " + "; ".join(f"{r.siparis_no} %{r.ilerleme * 100:.0f} termin {r.termin:%d.%m} {r.durum}" for r in c["plan"].head(10).itertuples()))
    sat.append("Uyarılar: " + " | ".join(re.sub(r"<[^>]+>", "", u) for u in c["uyarilar"]))
    return "\n".join(sat)


# ------------------------------------------------------------------ yerel (anahtarsız) asistan
def _sayi(metin):
    """'80 bin', '45.000', '1,2 milyon' gibi ifadeleri sayıya çevirir."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(bin|milyon|k|m)?", metin.lower())
    if not m:
        return None
    ham = m.group(1)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", ham):
        v = float(ham.replace(".", ""))
    else:
        v = float(ham.replace(",", "."))
    return v * {"bin": 1e3, "k": 1e3, "milyon": 1e6, "m": 1e6}.get(m.group(2), 1)


def yerel_yanit(soru, c):
    s = soru.lower()
    adet, uph = c["adet"], c["uph"]
    if any(k in s for k in ("kaç kişi", "kac kisi", "personel lazım", "kişi lazım", "kişi gerek", "kaç personel")):
        n = _sayi(s)
        if n and n > 100:
            gereken = math.ceil(n / (uph * 9))
            return (f"{n:,.0f} adetlik iş için {uph:.0f} adet/saat UPH ve 9 saatlik vardiyayla **{gereken} kişi-gün** gerekir. "
                    f"Mevcut {c['toplayici']} toplayıcıyla bu iş yaklaşık {n / (c['toplayici'] * uph * 9):.1f} günde biter.").replace(",", ".")
        return "Kaç adetlik işi soruyorsunuz? Örnek: *'Yarın 80 bin adet gelirse kaç kişi lazım?'*"
    if any(k in s for k in ("gecik", "termin", "sipariş", "siparis")):
        p = c["plan"]
        if not len(p):
            return "Şu an takip edilen açık sipariş yok."
        gec = p[p["durum"].isin(["Gecikir", "Riskli"])]
        if not len(gec):
            return f"{len(p)} açık siparişin hepsi termine yetişiyor görünüyor."
        sat = [f"- **{r.siparis_no}** ({r.musteri[:28]}): termin {r.termin:%d.%m}, planlanan bitiş {r.bitis:%d.%m}, durum {r.durum}" for r in gec.head(6).itertuples()]
        return (f"{len(gec)} sipariş risk altında. Ana neden kapasite: günlük kapasite yaklaşık {c['toplayici'] * uph * 9:,.0f} adet.\n".replace(",", ".")
                + "\n".join(sat) + "\n\nÖneri: öncelikli müşterileri öne alın ya da günlük kişi sayısını artırın (Senaryo sayfasında deneyebilirsiniz).")
    if any(k in s for k in ("yoğun saat", "en yoğun", "tepe", "hangi saat")):
        sy = c["saatlik"].nlargest(3, "satir_gun_ort")
        return "En yoğun saatler: " + ", ".join(f"**{int(r.saat)}:00** (~{r.satir_gun_ort:.0f} satır)" for r in sy.itertuples()) + \
               ". Mola ve vardiya başlangıcını bu saatlere göre kaydırmak yükü dengeler."
    if any(k in s for k in ("uph", "verim", "performans")):
        return (f"Dönem ortalama UPH **{uph:.0f} adet/saat**, günlük ortalama {c['personel']:.1f} personel. "
                f"En iyi toplayıcı {c['en_iyi'][0]} ({c['en_iyi'][1]:.0f}), en düşük {c['en_kotu'][0]} ({c['en_kotu'][1]:.0f}).")
    if any(k in s for k in ("tahmin", "yarın", "yarin", "gelecek", "hafta")):
        t = c["tahmin"]
        return "Önümüzdeki günler için tahmin:\n" + "\n".join(f"- {r.tarih:%d.%m %A}: {r.tahmin_adet:,.0f} adet → {r.gereken_personel} kişi".replace(",", ".") for r in t.itertuples())
    if any(k in s for k in ("bölge", "bolge", "raf", "abc")):
        b = c["bolge"].head(5)
        return "En hareketli bölgeler: " + ", ".join(f"**{r.bolge}** ({r.satir:,} satır)".replace(",", ".") for r in b.itertuples()) + \
               ". Bunların kapıya yakın olması yürüme mesafesini azaltır (Yerleşim sayfası)."
    if "skt" in s or "son kullanma" in s:
        return f"Dönemde SKT'ye 90 günden az kalan **{c['skt_riskli']} satır** sevk edildi. Ayrıntı: SKT & FEFO sayfası."
    if any(k in s for k in ("forklift", "pil", "şarj", "sarj")):
        d = c["pil_dusuk"]
        return ("Pili %25'in altında araç yok." if not d else "Pili düşük araçlar: " + ", ".join(d) + ". Şarja gönderin.")
    if any(k in s for k in ("süreç", "surec", "darboğaz", "darbogaz", "neden")):
        kot = c["sureler"][c["sureler"]["durum"] != "Hedefte"]
        if not len(kot):
            return "Tüm süreç adımları hedef içinde."
        return "Hedefi aşan adımlar: " + ", ".join(f"**{r.adim}** ({r.gerceklesen_saat:.1f} sa / hedef {r.hedef_saat:.1f})" for r in kot.itertuples()) + \
               ". Bu adımlarda bekleme noktalarını ve iş atamasını inceleyin."
    if any(k in s for k in ("özet", "ozet", "durum", "nasıl", "nasil")):
        return (f"{c['donem']} döneminde **{adet:,.0f} adet** sevk edildi, UPH **{uph:.0f}**, palet doluluğu **%{c['doluluk']:.0f}**. "
                f"Aktif uyarı sayısı: {len(c['uyarilar'])}.").replace(",", ".")
    return ("Şunları sorabilirsiniz: *özet*, *kaç kişi lazım (örn. 80 bin adet)*, *geciken siparişler*, *en yoğun saat*, *UPH*, "
            "*yarınki tahmin*, *en hareketli bölgeler*, *SKT*, *forklift pili*, *süreç darboğazı*.")


def yanit(soru, c, gecmis=()):
    """(metin, kaynak) döner; kaynak 'claude' ya da 'yerel'. Claude hata verirse yerel asistana düşer."""
    if anahtar():
        try:
            return claude_sor(soru, baglam_metni(c), gecmis), "claude"
        except Exception as e:
            return yerel_yanit(soru, c) + f"\n\n_(Claude API'ye ulaşılamadı: {e}; yerel asistan cevapladı.)_", "yerel"
    return yerel_yanit(soru, c), "yerel"
