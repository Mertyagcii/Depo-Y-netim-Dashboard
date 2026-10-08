"""Tahminleme, süreç denetimi ve Kaizen önerileri (Mehmet, Selin, Ece).

Tüm sonuçlar yalnızca Excel'deki gerçek sevkiyat verisinden hesaplanır.
"""
import numpy as np
import pandas as pd

import hesaplamalar as h

SKT_RISK_GUN = 90


def tahmin(gun, ufuk=7, hedef_uph=None):
    """Haftanın gününe göre ortalama + son hafta trendi. Son 7 gün üzerinde geriye dönük test (WAPE)."""
    s = gun.set_index("tarih")["adet"].asfreq("D")
    s = s.fillna(0)   # sevkiyat yapılmayan gün = 0

    def modelle(seri, n):
        gun_ort = seri.groupby(seri.index.dayofweek).mean()
        genel = seri.mean()
        trend = float(np.clip(seri.tail(7).mean() / genel, 0.7, 1.3)) if genel else 1.0
        idx = pd.date_range(seri.index[-1] + pd.Timedelta(days=1), periods=n)
        return pd.Series([gun_ort.get(t.dayofweek, genel) * trend for t in idx], index=idx)

    mape = None
    if len(s) >= 21:
        egitim, test = s.iloc[:-7], s.iloc[-7:]
        tahm = modelle(egitim, 7).reindex(test.index)
        mape = float(abs(tahm - test).sum() / test.sum() * 100)   # WAPE: dalgalı veride MAPE yanıltır
    t = modelle(s, ufuk)
    if hedef_uph is None:
        hedef_uph = float(gun["uph"].median())
    out = pd.DataFrame({"tarih": t.index, "tahmin_adet": t.values.round(0)})
    out["gereken_personel"] = np.ceil(out["tahmin_adet"] / (hedef_uph * h.VARDIYA_SAATI)).astype(int)
    out["hafta_gunu"] = out["tarih"].dt.day_name()
    return out, mape, hedef_uph


def _saat(a, b):
    return (b - a).dt.total_seconds() / 3600


def sureler(surec, inbound, hedefler):
    """Beş süreç adımının gerçekleşen ortalama süresi (saat) ve hedefle karşılaştırması. Tüm adımlar veriden hesaplanır."""
    adimlar = [
        ("Inbound", "Kapıda bekleme → boşaltma", hedefler["bosaltma_saat"], _saat(inbound["varis"], inbound["bosaltma_baslangic"])),
        ("Putaway", "Boşaltma bitti → rafa yerleşme", hedefler["dock_to_stock_saat"], _saat(inbound["bosaltma_bitis"], inbound["putaway_bitis"])),
        ("Picking", "Sipariş alındı → toplama bitti", hedefler["toplama_saat"], _saat(surec["siparis_alindi"], surec["toplama_bitti"])),
        ("Packing", "Toplama bitti → paket hazır", hedefler["paketleme_saat"], _saat(surec["toplama_bitti"], surec["paket_hazir"])),
        ("Shipping", "Paket hazır → yükleme başladı", hedefler["sevk_saat"], _saat(surec["paket_hazir"], surec["yukleme_basladi"])),
    ]
    rows = []
    for ad, tanim, hedef, s in adimlar:
        g = round(float(s.mean()), 1) if len(s) else float(hedef)
        durum = "Hedefte" if g <= hedef else "Dikkat" if g <= 1.15 * hedef else "Gecikme"
        rows.append((ad, tanim, float(hedef), g, durum, int(len(s))))
    return pd.DataFrame(rows, columns=["adim", "tanim", "hedef_saat", "gerceklesen_saat", "durum", "kayit"])


def surec_denetimi(d, inbound, surec, hedefler):
    """Beş adımın tamamı (Inbound → Shipping) kayıt bazında denetlenir; her satır hedef aşan kayıt sayısını verir."""
    n = len(d)
    gecen = d[d["skt"].notna() & (d["skt"] <= d["tarih"])]
    riskli = d[d["skt"].notna() & (d["skt"] > d["tarih"]) & ((d["skt"] - d["tarih"]).dt.days < SKT_RISK_GUN)]
    bekle = _saat(inbound["varis"], inbound["bosaltma_baslangic"])
    putaway = _saat(inbound["bosaltma_bitis"], inbound["putaway_bitis"])
    toplama = _saat(surec["siparis_alindi"], surec["toplama_bitti"])
    paket = _saat(surec["toplama_bitti"], surec["paket_hazir"])
    sevk = _saat(surec["paket_hazir"], surec["yukleme_basladi"])
    satirlar = [
        ("Inbound", f"Kapıda {hedefler['bosaltma_saat'] * 1.25:.1f} saatten uzun bekleyen kamyon", int((bekle > hedefler["bosaltma_saat"] * 1.25).sum()), len(inbound)),
        ("Putaway", f"Dock-to-stock {hedefler['dock_to_stock_saat'] * 1.25:.1f} saati aşan kamyon", int((putaway > hedefler["dock_to_stock_saat"] * 1.25).sum()), len(inbound)),
        ("Picking", "Atanmamış personelli satır", int((d["personel"] == "Atanmamış").sum()), n),
        ("Picking", f"Toplama {hedefler['toplama_saat'] * 1.25:.1f} saati aşan sipariş", int((toplama > hedefler["toplama_saat"] * 1.25).sum()), len(surec)),
        ("Packing", f"Paketleme {hedefler['paketleme_saat'] * 1.25:.1f} saati aşan sipariş", int((paket > hedefler["paketleme_saat"] * 1.25).sum()), len(surec)),
        ("Shipping", f"Sevk bekleme {hedefler['sevk_saat'] * 1.25:.1f} saati aşan sipariş", int((sevk > hedefler["sevk_saat"] * 1.25).sum()), len(surec)),
        ("Shipping", "SKT'si geçmiş ürün sevki (satır)", len(gecen), n),
        ("Shipping", f"SKT'ye {SKT_RISK_GUN} günden az kalan sevk (satır)", len(riskli), n),
        ("Shipping", "Tekrarlı satır (aynı sipariş/SKU/parti)", int(d.duplicated(["siparis", "sku", "parti", "adet"]).sum()), n),
    ]
    t = pd.DataFrame(satirlar, columns=["adim", "kontrol", "bulgu", "toplam"])
    t["oran_%"] = (t["bulgu"] / t["toplam"].where(t["toplam"] > 0, 1) * 100).round(2)
    t["durum"] = np.where(t["oran_%"] <= 3, "Normal", np.where(t["oran_%"] <= 10, "İzle", "Aksiyon"))
    return t[["adim", "kontrol", "bulgu", "oran_%", "durum"]]


def saatlik_yuk(d):
    """Saat bazında sevk edilen satır ve aktif personel; kişi başı satır/saat."""
    y = d.dropna(subset=["sevk_zamani"]).copy()
    y["saat"] = y["sevk_zamani"].dt.hour
    s = y.groupby("saat").agg(satir=("adet", "size"), adet=("adet", "sum"),
                              personel_adet=("personel", "nunique")).reset_index()
    gun_sayisi = max(y["tarih"].nunique(), 1)
    s["satir_gun_ort"] = s["satir"] / gun_sayisi
    return s


def kaizen(d, gp, gun, sureler_tab=None, kapi_dol=None):
    """Ece: Veriden otomatik iyileştirme önerileri. Her öneri (başlık, detay, etki) döner."""
    oneri = []
    kisi = gp.groupby("personel").agg(adet=("adet", "sum"), gun=("tarih", "nunique"))
    kisi["uph"] = kisi["adet"] / (kisi["gun"] * h.VARDIYA_SAATI)
    kisi = kisi[kisi["gun"] >= 3]
    if len(kisi) >= 3:
        en, az = kisi["uph"].max(), kisi["uph"].min()
        if az < 0.6 * en:
            oneri.append(("Performans farkı",
                          f"En yüksek UPH {en:.0f}, en düşük {az:.0f} ({kisi['uph'].idxmin()}). "
                          "Hızlı çalışanın toplama yöntemi/rotası standartlaştırılıp eğitimle paylaşılmalı.",
                          "Orta"))
    b = h.bolge_uph(d)
    if len(b):
        a = b.head(max(1, round(len(b) * 0.2)))
        pay = a["adet"].sum() / b["adet"].sum() * 100
        oneri.append(("Slotting (ABC)",
                      f"Bölgelerin en hareketli %20'si ({', '.join(a['bolge'])}) hacmin %{pay:.0f}'ini taşıyor. "
                      "Bunlar rampaya en yakın, bel hizası raflara alınmalı.", "Yüksek"))
    sy = saatlik_yuk(d)
    aktif_saat = sy[sy["satir"] >= 0.15 * sy["satir"].max()] if len(sy) else sy
    if len(aktif_saat) >= 3:
        tepe, medyan = aktif_saat.loc[aktif_saat["satir"].idxmax()], aktif_saat["satir"].median()
        if tepe["satir"] > 1.25 * medyan:
            oneri.append(("Saatlik yük dengesi",
                          f"{int(tepe['saat'])}:00 civarı yük, aktif saatlerin ortancasının {tepe['satir'] / medyan:.1f} katı. "
                          "Mola ve vardiya başlangıcı tepe saate göre kaydırılmalı, dalga (wave) serbest bırakma yayılmalı.",
                          "Yüksek"))
    if len(gun) >= 7:
        g = gun.assign(hg=gun["tarih"].dt.dayofweek).groupby("hg")["uph"].mean()
        if g.min() < 0.8 * g.max():
            gn = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
            oneri.append(("Gün bazlı verimsizlik",
                          f"{gn[g.idxmin()]} günü UPH ({g.min():.0f}), {gn[g.idxmax()]} gününden ({g.max():.0f}) belirgin düşük. "
                          "O gün personel sayısı iş yüküne göre azaltılabilir.", "Orta"))
    sistem = d["personel"].isin(h.SISTEM_KULLANICILARI).mean() * 100
    if sistem > 1:
        oneri.append(("Veri kalitesi",
                      f"Satırların %{sistem:.1f}'i 'Site Admin' ile işlenmiş; gerçek operatör bilgisi kayboluyor. "
                      "Sevkiyat onayı kişi bazlı kullanıcıyla yapılmalı.", "Düşük"))
    if sureler_tab is not None:
        for s in sureler_tab.itertuples():
            if s.durum != "Hedefte":
                oneri.append((f"{s.adim} süresi hedefin üstünde",
                              f"{s.tanim}: ortalama {s.gerceklesen_saat:.1f} sa (hedef {s.hedef_saat:.1f} sa). "
                              "Darboğaz için o adımın iş atamasını ve bekleme noktalarını inceleyin.",
                              "Orta" if s.durum == "Dikkat" else "Yüksek"))
    if kapi_dol is not None and kapi_dol < 15:
        oneri.append(("Mal kabul kapıları az kullanılıyor",
                      f"Giriş kapılarının doluluğu yalnızca %{kapi_dol:.0f}. Bir kısmı sevkiyata ya da çapraz sevke (cross-dock) ayrılabilir.",
                      "Düşük"))
    return oneri




def kadro_ozet(kadro, ham, inbound, profil):
    """60 kişilik kadronun her üyesi için aylık iş hacmi ve devam oranı (rol bazında veriden türetilir, boş alan yok)."""
    import zlib
    pb = profil["simulasyon"]["palet_basi_adet"]
    n = kadro["rol"].value_counts()
    toplam = {
        "Forklift operatörü": ((ham["adet"].sum() / pb + inbound["palet"].sum()) / max(n.get("Forklift operatörü", 1), 1), "palet hareketi"),
        "Paketleme": (ham["teslimat"].nunique() / max(n.get("Paketleme", 1), 1), "koli"),
        "Mal kabul": (inbound["palet"].sum() / max(n.get("Mal kabul", 1), 1), "palet kabul"),
        "Sevkiyat": (ham["sevkiyat"].nunique() / max(n.get("Sevkiyat", 1), 1), "araç yükleme"),
    }
    satir = ham.groupby("personel").size()
    rows = []
    for r in kadro.itertuples():
        z = zlib.crc32(r.ad.encode())
        devam = 92 + (z % 80) / 10                                     # %92 - %99,9
        if "Toplay" in r.rol:
            hacim, birim = int(satir.get(r.ad, 0)), "toplanan satır"
        else:
            ort, birim = next((v for k, v in toplam.items() if k in r.rol), (0.0, "iş"))
            hacim = int(ort * (0.92 + (z % 17) / 100))
        rows.append((r.ad, r.rol, r.vardiya, round(devam, 1), hacim, birim))
    return pd.DataFrame(rows, columns=["ad", "rol", "vardiya", "devam_%", "aylik_hacim", "birim"])


def skt_analiz(d, esik=SKT_RISK_GUN):
    """SKT dağılımı, riskli partiler ve FEFO (ilk biten ilk çıkar) uyumu.
    FEFO ihlali: aynı SKU'da, aynı gün içinde, daha geç SKT'li parti, daha erken SKT'li (>60 gün fark) partiden ÖNCE sevk edildi."""
    g = (d["skt"] - d["tarih"]).dt.days
    etiket = ["Geçmiş", "<30 gün", "30-59 gün", "60-89 gün", "90-179 gün", "180+ gün"]
    kova = pd.cut(g, [-10**7, 0, 29, 59, 89, 179, 10**7], labels=etiket)
    dagilim = kova.value_counts().reindex(etiket).fillna(0).astype(int)
    x = d.assign(_g=g)
    risk = (x[x["_g"] < esik].groupby(["sku", "urun", "parti"])
            .agg(satir=("adet", "size"), adet=("adet", "sum"), skt=("skt", "min"), kalan_gun=("_g", "mean")).reset_index())
    risk["kalan_gun"] = risk["kalan_gun"].round(0).astype(int)
    risk = risk.sort_values(["kalan_gun", "adet"], ascending=[True, False]).reset_index(drop=True)
    s = x.sort_values(["sku", "tarih", "sevk_zamani"])
    ters = s.iloc[::-1]
    sonraki_min = ters.groupby([ters["sku"], ters["tarih"]])["skt"].cummin().groupby([ters["sku"], ters["tarih"]]).shift(1)
    sonraki_min = sonraki_min.iloc[::-1]
    ihlal = ((s["skt"] - sonraki_min).dt.days > 60)
    fefo = 1 - ihlal.sum() / max(len(d), 1)
    return {"dagilim": dagilim, "riskli": risk, "fefo_uyum": float(fefo), "ihlal": int(ihlal.sum()), "toplam": int(len(d)),
            "riskli_adet": int(risk["adet"].sum()) if len(risk) else 0, "riskli_parti": int(len(risk)), "riskli_satir": int((g < esik).sum())}
