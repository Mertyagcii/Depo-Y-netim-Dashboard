"""Alarm bildirimleri: Slack / Teams / genel webhook (Serdar - Mimari).

Webhook adresi dosyaya YAZILMAZ; sunucuda ortam değişkeni olarak tutulur (varsayılan: OPLOG_WEBHOOK_URL).
Ayarlar bildirim.json'dadır. Aynı uyarı 1 saat içinde tekrar gönderilmez (.onbellek/bildirim_log.json).
"""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

AYAR = Path(__file__).parent / "bildirim.json"
LOG = Path(__file__).parent / ".onbellek" / "bildirim_log.json"
VARSAYILAN = {"aktif": False, "webhook_env": "OPLOG_WEBHOOK_URL", "tur": "slack", "tekrar_saat": 1.0}


def yukle(dosya=AYAR):
    a = dict(VARSAYILAN)
    try:
        if Path(dosya).exists():
            a.update(json.loads(Path(dosya).read_text(encoding="utf-8")))
    except Exception:
        pass
    return a


def kaydet(a, dosya=AYAR):
    Path(dosya).write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding="utf-8")


def _govde(tur, metin):
    if tur == "teams":
        return {"@type": "MessageCard", "@context": "http://schema.org/extensions", "text": metin, "themeColor": "d9f23b"}
    return {"text": metin}                       # slack ve genel webhook


def gonder(url, metin, tur="slack", zaman_asimi=8):
    """Webhook'a mesaj gönderir. (başarılı_mı, mesaj) döner."""
    yerel = bool(re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?/", url or ""))
    if not url or not (url.lower().startswith("https://") or yerel):
        return False, "Webhook adresi https:// ile başlamalı."
    istek = urllib.request.Request(url, data=json.dumps(_govde(tur, metin)).encode("utf-8"),
                                   headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as r:
            return 200 <= r.status < 300, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _temiz(m):
    return re.sub(r"<[^>]+>", "", m)


def otomatik(uyarilar, ayar=None, log_dosya=LOG, simdi=None):
    """Kritik (kırmızı) uyarıları, son `tekrar_saat` içinde gönderilmemişse webhook'a yollar. Gönderilen sayıyı döner."""
    ayar = ayar or yukle()
    url = os.environ.get(ayar["webhook_env"] or "")
    if not ayar["aktif"] or not url:
        return 0
    simdi = time.time() if simdi is None else simdi
    try:
        gecmis = json.loads(Path(log_dosya).read_text(encoding="utf-8")) if Path(log_dosya).exists() else {}
    except Exception:
        gecmis = {}
    gonderilen = 0
    for tur, metin in uyarilar:
        if tur != "e":
            continue
        m = _temiz(metin)
        anahtar = hashlib.sha1(m.encode()).hexdigest()[:12]
        onceki = gecmis.get(anahtar)
        if onceki is not None and simdi - onceki < ayar["tekrar_saat"] * 3600:
            continue
        ok, _ = gonder(url, f"🚨 OPLOG kritik uyarı: {m}", ayar["tur"])
        if ok:
            gecmis[anahtar] = simdi
            gonderilen += 1
    try:
        Path(log_dosya).parent.mkdir(exist_ok=True)
        Path(log_dosya).write_text(json.dumps({k: v for k, v in gecmis.items() if simdi - v < 86400}), encoding="utf-8")
    except OSError:
        pass
    return gonderilen
