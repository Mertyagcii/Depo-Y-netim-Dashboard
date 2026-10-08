"""Akıllı Depo Dijital İkizi & Kontrol Merkezi (Ayşe - Frontend). Koyu menü + açık panel tasarımı, mobil uyumlu."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import analitik as an
import hesaplamalar as h
import asistan
import bildirim
import canli
import demo_veri
import depolar
import guvenlik as gv
import maliyet as ml
import rapor
import saha
import senaryo as sn
import depo_profil as dp
import simulasyon as sim
import veri_kaynagi as vk
import siparis as sp
import twin as tw
from html import escape as esc

LIME, KOYU = "#d9f23b", "#1c1d20"

st.set_page_config(page_title="OPLOG Kontrol Merkezi", page_icon="📦", layout="wide")

pio.templates["depo"] = go.layout.Template(layout=dict(
    colorway=["#1c1d20", "#b5d11d", "#8d9097", "#f59e0b", "#ef4444", "#3b82f6"],
    font=dict(family="Outfit, Segoe UI, sans-serif", color="#555a61", size=12),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="#eeeeea", zeroline=False, linecolor="#e3e3df"),
    yaxis=dict(gridcolor="#eeeeea", zeroline=False),
    hoverlabel=dict(bgcolor=KOYU, font=dict(color="white")),
    title=dict(font=dict(size=14, color=KOYU)), margin=dict(l=8, r=8, t=36, b=8), height=270))
pio.templates.default = "depo"

st.markdown(
    """<style>
    html,body,[class*=css],.stApp{font-family:'Outfit','Segoe UI',sans-serif}
    .stApp{background:#1a1b1d}
    [data-testid=stHeader]{background:transparent}
    .stAppDeployButton,[data-testid=stMainMenu],[data-testid=stDecoration]{display:none!important}
    /* menü gizlenince geri açma düğmesi: her zaman görünür, belirgin limon rengi */
    [data-testid=stExpandSidebarButton]{position:fixed!important;top:14px;left:14px;z-index:1000001;background:#d9f23b!important;
        border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.35);width:40px;height:40px;display:flex!important;align-items:center;justify-content:center}
    [data-testid=stExpandSidebarButton] *{color:#1c1d20!important;fill:#1c1d20!important}
    [data-testid=stExpandSidebarButton]:hover{background:#c6e32a!important}
    .block-container{background:#f6f6f3;border-radius:26px;margin:.6rem .8rem;padding:1.4rem 1.5rem 2.5rem;
        max-width:100%!important;width:100%!important}
    h1,h2,h3{color:#1c1d20}
    /* ---- sol menü ---- */
    [data-testid=stSidebar]{background:#1c1d20}
    [data-testid=stSidebar] *{color:#d5d7da}
    [data-testid=stSidebar] [role=radiogroup]{gap:2px}
    [data-testid=stSidebar] [role=radiogroup] label{padding:6px 12px;border-radius:10px;width:100%;margin:0;
        border-left:3px solid transparent;cursor:pointer}
    [data-testid=stSidebar] label[data-testid=stRadioOption] > div > div:first-child{display:none}
    [data-testid=stSidebar] label[data-testid=stRadioOption] p{font-size:1rem}
    [data-testid=stSidebar] label[data-testid=stRadioOption]:hover{background:#25262a}
    [data-testid=stSidebar] label[data-testid=stRadioOption][data-selected=true]{background:#2a2b2f;border-left-color:#d9f23b}
    [data-testid=stSidebar] label[data-testid=stRadioOption][data-selected=true] *{color:#fff;font-weight:600}
    [data-testid=stSidebar] [data-testid=stExpander]{border:1px solid #2f3034;border-radius:12px;background:#222326}
    .marka{display:flex;align-items:center;gap:10px;font-size:1.35rem;font-weight:700;color:#fff;margin:.2rem 0 1rem}
    .marka b{background:#d9f23b;color:#1c1d20;width:34px;height:34px;border-radius:10px;display:grid;place-items:center}
    .mn{font-size:.7rem;letter-spacing:.12em;color:#7d8087;margin:.8rem 0 .3rem}
    .promo{background:#f6f6f3;border-radius:16px;padding:14px;margin-top:1rem}
    .promo *{color:#1c1d20!important}
    .promo b{font-size:1rem}.promo p{font-size:.78rem;margin:.3rem 0 0;color:#555!important}
    .kisi{display:flex;gap:10px;align-items:center;margin-top:1rem}
    .kisi i{background:#d9f23b;color:#1c1d20!important;width:36px;height:36px;border-radius:50%;display:grid;
        place-items:center;font-style:normal;font-weight:700}
    /* ---- üst başlık ---- */
    .ust{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:1rem}
    .baslik{font-size:1.55rem;font-weight:700;color:#1c1d20;margin:0}
    .chip{background:#fff;border:1px solid #e5e5e0;border-radius:12px;padding:8px 14px;font-size:.85rem;color:#444}
    .chip.k{background:#1c1d20;color:#fff;border-color:#1c1d20}
    /* ---- kartlar ---- */
    [data-testid=stVerticalBlockBorderWrapper]{background:#fff;border:1px solid #ececE8;border-radius:18px;padding:6px 10px}
    .kt{font-weight:600;color:#1c1d20;font-size:1rem;margin:.2rem 0 .4rem}
    .kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:.7rem}
    .kpi{background:#fff;border:1px solid #ececE8;border-radius:16px;padding:11px 15px;display:flex;
        justify-content:space-between;align-items:center;gap:10px;min-height:88px}
    .kpi.koyu{background:#1c1d20;border-color:#1c1d20}
    .kpi .bs{color:#6b7076;font-size:.88rem}.kpi.koyu .bs{color:#c9cbce}
    .kpi .dg{color:#1c1d20;font-size:1.5rem;font-weight:700;line-height:1.2}.kpi.koyu .dg{color:#fff}
    .dl{display:inline-block;font-size:.74rem;font-weight:600;border-radius:8px;padding:2px 8px;margin-top:4px}
    .dl.ok{background:#e4f6dc;color:#2f8a1d}.dl.kt{background:#fde4e4;color:#c43a3a}.dl.nt{background:#f0f0ec;color:#7d8087}
    .ring{--p:0;width:54px;height:54px;border-radius:50%;flex:none;display:grid;place-items:center;
        background:conic-gradient(#b5d11d calc(var(--p)*1%),#ecece8 0)}
    .ring span{width:41px;height:41px;border-radius:50%;background:#fff;display:grid;place-items:center;
        font-size:.72rem;font-weight:700;color:#1c1d20}
    table.tbl{width:100%;border-collapse:collapse;font-size:.86rem}
    table.tbl th{text-align:left;color:#8a8e94;font-weight:500;padding:6px 6px;border-bottom:1px solid #f0f0ec}
    table.tbl td{padding:7px 6px;border-bottom:1px solid #f6f6f3;color:#1c1d20}
    .tg{border-radius:8px;padding:2px 9px;font-size:.76rem;font-weight:600}
    .tg.g{background:#e4f6dc;color:#2f8a1d}.tg.o{background:#fff0d6;color:#b86e00}.tg.r{background:#fde4e4;color:#c43a3a}
    .tg.d{background:#1c1d20;color:#fff}.tg.l{background:#d9f23b;color:#1c1d20}.tg.n{background:#ececE8;color:#555}
    .uy{padding:10px 12px;border-radius:12px;margin-bottom:8px;font-size:.86rem}
    .uy.e{background:#fde4e4;color:#a82c2c}.uy.w{background:#fff0d6;color:#8a5200}.uy.s{background:#e4f6dc;color:#2f8a1d}
    /* ---- butonlar ---- */
    .stButton>button,[data-testid=stBaseButton-secondary]{background:#1c1d20;color:#fff;border-radius:999px;
        border:none;padding:.45rem 1.2rem;font-weight:600}
    .stButton>button:hover{background:#34353a;color:#d9f23b}
    [data-testid=stAlert]{border-radius:14px}
    @media (max-width:1000px){.kpi-grid{grid-template-columns:repeat(2,1fr)}}
    @media (max-width:900px){.block-container{padding-top:3.4rem!important}}
    @media (max-width:640px){.block-container{margin:.2rem;padding:1rem .8rem 2rem;border-radius:18px}
        .baslik{font-size:1.4rem}.kpi{padding:12px;min-height:96px}.kpi .dg{font-size:1.35rem}
        .ring{width:50px;height:50px}.ring span{width:37px;height:37px;font-size:.62rem}}
    </style>""",
    unsafe_allow_html=True,
)


def sifre_kontrol():
    """İsteğe bağlı şifre: sunucuda 'APP_SIFRE' secret'ı tanımlıysa giriş ister."""
    try:
        sifre = st.secrets.get("APP_SIFRE")
    except Exception:
        sifre = None
    if not sifre or st.session_state.get("giris"):
        return
    girilen = st.text_input("Şifre", type="password")
    if girilen and girilen == sifre:
        st.session_state["giris"] = True
        st.rerun()
    elif girilen:
        st.error("Şifre yanlış")
    st.stop()


sifre_kontrol()


@st.cache_resource(show_spinner="Veriler hazırlanıyor...", ttl=120)   # kopyalamadan paylaşılır (tablolar salt-okunur kullanılır)
def veri_paketi(dakika_damgasi, profil, ayar):
    """Demo ya da API verisi; 2 dakikada bir tazelenir (canlı kaynakta yeni kayıtlar gelir)."""
    return vk.paket(pd.Timestamp(dakika_damgasi), profil, ayar)


@st.cache_data(show_spinner=False)
def kroki_hesapla(anahtar, profil):
    """anahtar = veri imzası (50 bin satırlık tabloyu her çalıştırmada hash'lememek için)."""
    return tw.yerlesim(veri, profil)


@st.cache_data(show_spinner=False)
def rota_ozeti(anahtar, profil):
    """Rota optimizasyonu önbelleği: anahtar veri değişince değişir (ağır hesap tekrarlanmaz)."""
    son = veri[veri["tarih"] >= veri["tarih"].max() - pd.Timedelta(days=30)]      # uzun dönemde de hızlı: son 30 gün örneklenir
    return tw.rota_tasarruf(son, kroki, profil=profil)


@st.cache_resource(show_spinner=False)
def gunluk_tum(imza):
    """Tüm geçmişin günlük özeti (tahmin ve trend için; dönem seçiminden bağımsız)."""
    return h.gunluk_ozet(h.gunluk_personel(veri_tum))


@st.cache_data(show_spinner=False)
def yer_kiyas(anahtar, profil, strateji):
    """Yerleşim karşılaştırması: son 30 günde çok bölgeli sevkiyatlarda ortalama rota mesafesi (önerilen ABC vs seçilen mevcut)."""
    son = veri[veri["tarih"] >= veri["tarih"].max() - pd.Timedelta(days=30)]
    oneri_l, mevcut_l = tw.yerlesim(son, profil, "frekans"), tw.yerlesim(son, profil, strateji)
    ro, rm = tw.rota_tasarruf(son, oneri_l, ornek=300, profil=profil), tw.rota_tasarruf(son, mevcut_l, ornek=300, profil=profil)
    bolge_sayisi = son.assign(b=son["sku"].map(h.bolge_kodu)).groupby("sevkiyat")["b"].nunique()
    return {"oneri_m": float(ro["optimize_m"].mean()) if len(ro) else 0.0, "mevcut_m": float(rm["optimize_m"].mean()) if len(rm) else 0.0,
            "ornek": int(len(ro)), "cok_bolge_orani": float((bolge_sayisi > 1).mean())}


@st.cache_data(show_spinner=False)
def guvenlik_ozeti(anahtar, profil, saat0):
    return gv.yakin_gecis(kroki, profil, saat0=saat0, saat1=saat0 + 9)


@st.cache_data(show_spinner=False)
def skt_onb(anahtar):
    """SKT/FEFO analizi (300 bin satırda ~1 sn): veri imzası değişmedikçe yeniden hesaplanmaz."""
    return an.skt_analiz(veri)


def sayi(x):
    return f"{x:,.0f}".replace(",", ".")


def kart(baslik=None):
    k = st.container(border=True)
    if baslik:
        k.markdown(f'<div class="kt">{baslik}</div>', unsafe_allow_html=True)
    return k


def kpi(baslik, deger, alt="", alt_sinif="nt", koyu=False, halka=None):
    r = f'<div class="ring" style="--p:{halka:.0f}"><span>{halka:.0f}%</span></div>' if halka is not None else ""
    alt_html = f'<span class="dl {alt_sinif}">{alt}</span>' if alt != "" else ""
    return (f'<div class="kpi{" koyu" if koyu else ""}"><div><div class="bs">{baslik}</div>'
            f'<div class="dg">{deger}</div>{alt_html}</div>{r}</div>')


def tablo(basliklar, satirlar):
    th = "".join(f"<th>{b}</th>" for b in basliklar)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in s) + "</tr>" for s in satirlar)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


def etiket(metin, sinif):
    return f'<span class="tg {sinif}">{metin}</span>'


SAYFALAR = ["▦  Dashboard", "▤  Siparişler", "◈  Dijital İkiz", "◐  Senaryo", "⌖  Yerleşim", "₺  Maliyet & ROI", "✎  Asistan", "▣  Saha",
            "⌕  Takip", "⚠  SKT & FEFO", "◔  Günlük", "☺  Personel", "❖  SKU", "◉  Kanal", "↗  Tahmin", "✓  Süreç", "✦  Kaizen",
            "⌂  Depolar", "☰  Rapor", "▥  Depo Profili", "⇄  Entegrasyon"]
SUNUM_SAYFALARI = ["Dashboard", "Dijital İkiz", "Senaryo", "Yerleşim", "Maliyet & ROI", "Süreç"]

_q = st.query_params.get("sayfa")                      # ?sayfa=Siparişler ile doğrudan açılış
if _q and "sayfa" not in st.session_state:
    _e = [s for s in SAYFALAR if s.split("  ", 1)[1] == _q]
    if _e:
        st.session_state["sayfa"] = _e[0]

with st.sidebar:
    if "_sunum_git" in st.session_state:                       # sunum modu: bir sonraki sayfaya geç (radio oluşmadan önce)
        st.session_state["sayfa"] = SAYFALAR[st.session_state.pop("_sunum_git")]
    st.markdown('<div class="marka"><b>O</b>OPLOG</div><div class="mn">MENÜ</div>', unsafe_allow_html=True)
    sayfa = st.radio("Menü", SAYFALAR, key="sayfa", label_visibility="collapsed").split("  ", 1)[1]
    st.markdown('<div class="mn">GENEL</div>', unsafe_allow_html=True)
    ayar = st.expander("⚙ Ayarlar")
    with ayar:
        hedef_uph = st.number_input("Hedef UPH (adet/saat)", 0, 20000, 0,
                                    help="0 bırakırsan hedef karşılaştırması gösterilmez.")
        try:
            _ys = st.secrets.get("YONETICI_SIFRE")
        except Exception:
            _ys = None
        YONETICI_OK = True
        if _ys:                                   # sunucuda YONETICI_SIFRE tanımlıysa düzenleme/kaydetme şifreli olur
            YONETICI_OK = st.text_input("Yönetici şifresi (düzenleme için)", type="password") == _ys
    with ayar:
        sunum = st.toggle("📺 Sunum modu (sayfaları otomatik gez)", key="sunum", help="Seçili sayfaları sırayla gösterir; müşteri sunumu / kontrol odası ekranı için.")
        sunum_sn = st.slider("Sayfa süresi (sn)", 8, 90, 20, key="sunum_sn")
    donem_kutu = st.expander("📅 Dönem (tarih seçimi)", expanded=True)

SIMDI = pd.Timestamp.now()
profil = dp.yukle()
kaynak_ayar = vk.yukle_ayar()
paket, kaynak_bilgi = veri_paketi(SIMDI.floor("2min").isoformat(), profil, kaynak_ayar)
ham_tum, inbound_tum, surec_tum, kadro_tab = paket["ham"], paket["inbound"], paket["surec"], paket["personel"]
veri_tum = ham_tum[ham_tum["personel"] != "Atanmamış"]
BUGUN = SIMDI.normalize()
_dmin, _dmax = veri_tum["tarih"].min().normalize(), veri_tum["tarih"].max().normalize()

with donem_kutu:
    _secim = st.selectbox("Dönem", ["Son 7 gün", "Son 30 gün", "Son 90 gün", "Tüm geçmiş", "Özel aralık"], index=1,
                          label_visibility="collapsed", key="donem_secim")
    if _secim == "Özel aralık":
        _r = st.date_input("Tarih aralığı", value=(max(_dmin, _dmax - pd.Timedelta(days=29)).date(), _dmax.date()),
                           min_value=_dmin.date(), max_value=_dmax.date(), format="DD.MM.YYYY")
        _r = tuple(_r) if isinstance(_r, (list, tuple)) else (_r,)
        BAS, BIT = pd.Timestamp(_r[0]), pd.Timestamp(_r[-1])
    else:
        _n = {"Son 7 gün": 7, "Son 30 gün": 30, "Son 90 gün": 90}.get(_secim)
        BIT = _dmax
        BAS = _dmin if _n is None else max(_dmin, _dmax - pd.Timedelta(days=_n - 1))
    st.caption(f"{BAS:%d.%m.%Y} – {BIT:%d.%m.%Y} · {(BIT - BAS).days + 1} gün · veri: {_dmin:%d.%m.%Y}'den beri")

with ayar:
    kanallar = st.multiselect("Kanal", sorted(veri_tum["kanal"].dropna().unique()),
                              default=sorted(veri_tum["kanal"].dropna().unique()))
_g = veri_tum["tarih"]
_kanal_ok = veri_tum["kanal"].isin(kanallar)
veri = veri_tum[(_g >= BAS) & (_g <= BIT) & _kanal_ok]
ham = ham_tum[(ham_tum["tarih"] >= BAS) & (ham_tum["tarih"] <= BIT)]
inbound = inbound_tum[(inbound_tum["tarih"] >= BAS) & (inbound_tum["tarih"] <= BIT)]
_sd = surec_tum["sevk"].dt.normalize()
surec_tab = surec_tum[(_sd >= BAS) & (_sd <= BIT)]
if inbound.empty:
    inbound = inbound_tum
if surec_tab.empty:
    surec_tab = surec_tum
if veri.empty:
    st.warning("Seçilen dönemde gösterilecek veri yok. Yan menüden dönemi değiştirin.")
    st.stop()

# önceki dönem (aynı uzunlukta, hemen öncesi): karşılaştırma için
BIT_TAM = BIT - pd.Timedelta(days=1) if BIT >= BUGUN else BIT          # bugün yarım gün: karşılaştırmada hariç
_n_onc = (BIT_TAM - BAS).days + 1
gun_onc = None
if _n_onc >= 1 and BAS - pd.Timedelta(days=_n_onc) >= _dmin:
    _ob, _oe = BAS - pd.Timedelta(days=_n_onc), BAS - pd.Timedelta(days=1)
    _veri_onc = veri_tum[(_g >= _ob) & (_g <= _oe) & _kanal_ok]
    if len(_veri_onc):
        gun_onc = h.gunluk_ozet(h.gunluk_personel(_veri_onc))

gp = h.gunluk_personel(veri)
gun = h.gunluk_ozet(gp)
VERI_IMZA = (len(veri), str(veri["sevk_zamani"].max()), tuple(kanallar))
kroki = kroki_hesapla(VERI_IMZA, profil)
stok = sim.stok(kroki, profil)
filo_n = max(len(tw.filo(profil)), 1)
gunler = list(gun["tarih"].dt.date)
gun_tam = gun[gun["tarih"] <= BIT_TAM] if (gun["tarih"] <= BIT_TAM).any() else gun   # tamamlanmış günler
gun_hist = gunluk_tum((len(veri_tum), str(veri_tum["sevk_zamani"].max())))          # tüm geçmiş: tahmin için
gun_hist_tam = gun_hist[gun_hist["tarih"] < BUGUN] if (gun_hist["tarih"] == BUGUN).any() else gun_hist
_sayim = veri.groupby("tarih").size()
_varsayilan_gun = next((d.date() for d in reversed(list(_sayim.index)) if _sayim[d] >= 200), gunler[-1])

with st.sidebar:
    with st.expander("🕒 Canlı seçim (ikiz & uyarılar)", expanded=True):
        sec_gun = st.selectbox("Gün", gunler, index=gunler.index(_varsayilan_gun))
        tum_gun = st.checkbox("Tüm gün", value=False)
        _gv = veri[veri["tarih"] == pd.Timestamp(sec_gun)].dropna(subset=["sevk_zamani"])
        _tepe = int(_gv["sevk_zamani"].dt.hour.value_counts().idxmax()) if len(_gv) else 14
        saat = st.slider("Saat", 0, 23, _tepe, disabled=tum_gun, key=f"saat_{sec_gun}",
                         help=f"Varsayılan: seçili günün en yoğun saati ({_tepe}:00).")
        dakika = st.slider("Dakika", 0, 59, 0, disabled=tum_gun)
        n_flk = st.slider("Forklift sayısı", 1, max(filo_n, 2), filo_n,
                          help=f"Filoda toplam {filo_n} araç var (Depo Profili).")
    _kaynak = ("API bağlı" if kaynak_bilgi["mod"] == "api" else "Demo veri (sunum)")
    _alt = ("API'ye ulaşılamadı, demo gösteriliyor" if kaynak_bilgi["hata"] else
            ("Demo ile tamamlanan: " + ", ".join(kaynak_bilgi["demo_parcalar"]) if kaynak_bilgi["demo_parcalar"] else
             f'{sayi(len(ham_tum))} satır · {_dmin:%d.%m.%Y} – {_dmax:%d.%m.%Y}'))
    st.markdown(f'<div class="promo"><b>● {_kaynak}</b><p>{_alt}. Gerçek sisteme bağlanmak için Entegrasyon sayfası.</p></div>'
                '<div class="kisi"><i>DY</i><div><b>Depo Yönetimi</b><br>'
                '<span style="font-size:.75rem;color:#8a8e94">Operasyon</span></div></div>',
                unsafe_allow_html=True)

# ---- Canlı durum (Dashboard ve İkiz sayfaları ortak kullanır) -------------------------------
isi = tw.yogunluk(veri, sec_gun, None if tum_gun else saat)
flk = tw.forkliftler(kroki, n_flk, saat * 3600 + dakika * 60, profil=profil)
gun_veri = veri[veri["tarih"] == pd.Timestamp(sec_gun)].dropna(subset=["sevk_zamani"])
k_saat = None if tum_gun else saat
cur = gun_veri if k_saat is None else gun_veri[gun_veri["sevk_zamani"].dt.hour == k_saat]
aktif = cur["personel"].nunique()
ort_saat = len(gun_veri) / max(gun_veri["sevk_zamani"].dt.hour.nunique(), 1)


def uyarilar():
    u = []
    for r in flk[flk["pil"] < 25].itertuples():
        u.append(("e", f"🔋 {r.id} pili %{r.pil:.0f} — şarja gönder"))
    if k_saat is not None and ort_saat and len(cur) > 1.5 * ort_saat:
        u.append(("w", f"👷 {k_saat}:00 yükü gün ortalamasının {len(cur) / ort_saat:.1f} katı "
                       f"({aktif} personel) — destek ekle"))
    if len(isi) and isi.max() >= 20:
        sicak = isi[isi >= 0.8 * isi.max()].index.tolist()
        u.append(("w", f"🔥 Yoğun bölge(ler): {', '.join(sicak)} — trafik/sıkışma riski"))
    skt = int((gun_veri["skt"].notna() & ((gun_veri["skt"] - gun_veri["tarih"]).dt.days < an.SKT_RISK_GUN)).sum())
    if skt:
        u.append(("w", f"📅 Seçili günde SKT'ye {an.SKT_RISK_GUN} günden az kalan {skt} satır sevk edildi"))
    return u or [("s", "✅ Aktif uyarı yok")]


bildirim.otomatik(uyarilar())          # kritik uyarılar (ayarlıysa) webhook'a gider; aynı uyarı saatte bir kez


toplam_adet = gp["adet"].sum()
adam_gun = len(gp)
ort_uph = toplam_adet / (adam_gun * h.VARDIYA_SAATI)


def ust_baslik(metin):
    st.markdown(f'<div class="ust"><p class="baslik">{metin}</p><div>'
                f'<span class="chip">📅 {BAS:%d.%m.%Y} – {BIT:%d.%m.%Y}</span> '
                f'<span class="chip k">● Canlı</span></div></div>', unsafe_allow_html=True)


# =========================== SAYFALAR ===========================
if sayfa == "Dashboard":
    ust_baslik("Dashboard")
    if gun_onc is not None and gun_onc["adet"].sum() > 0:
        d = (gun_tam["adet"].sum() / gun_onc["adet"].sum() - 1) * 100
        d_metin, d_sinif = f"{'▲' if d >= 0 else '▼'} %{abs(d):.0f} önceki döneme göre", "ok" if d >= 0 else "kt"
    else:
        d_metin, d_sinif = f"{len(gun)} aktif gün", "nt"
    if hedef_uph:
        fark = ort_uph - hedef_uph
        u_alt, u_sinif = f"{'▲' if fark >= 0 else '▼'} {sayi(abs(fark))} hedefe göre", "ok" if fark >= 0 else "kt"
        u_halka = min(ort_uph / hedef_uph * 100, 100)
    else:
        u_alt, u_sinif, u_halka = "adet / saat", "nt", min(ort_uph / gun["uph"].max() * 100, 100)
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Toplam Çıkış (adet)", sayi(toplam_adet), d_metin, d_sinif, koyu=True),
        kpi("Ortalama UPH", sayi(ort_uph), u_alt, u_sinif, halka=u_halka),
        kpi("Toplam Adam/Gün", adam_gun, f"{len(gun)} aktif gün"),
        kpi("Günlük Ort. Personel", f"{gun['personel'].mean():.1f}", "kişi / gün",
            halka=gun["personel"].mean() / gun["personel"].max() * 100),
    ]) + "</div>", unsafe_allow_html=True)

    pozisyon, dolu = int(stok["pozisyon"].sum()), int(stok["dolu"].sum())
    st.markdown(f'<div class="ust" style="margin:.2rem 0 .4rem"><span class="chip">🏭 {esc(profil["ad"])} · {"canlı API" if kaynak_bilgi["mod"] == "api" else "demo veri"}</span></div>'
                '<div class="kpi-grid">' + "".join([
        kpi("Depo alanı", f"{dp.toplam(profil):,.0f} m²".replace(",", "."),
            f"{profil['bina_en_m']:.0f} × {tw.geometri(profil)['boy']:.0f} m"),
        kpi("Palet doluluğu", f"%{dolu / pozisyon * 100:.0f}", f"{sayi(dolu)} / {sayi(pozisyon)} göz",
            "ok" if dolu / pozisyon < 0.92 else "kt", halka=dolu / pozisyon * 100),
        kpi("Forklift / MHE", filo_n, f"{len(profil['forkliftler'])} tip"),
        kpi("Kadro", sum(k["kisi"] for k in profil["kadro"]),
            f"{profil['kapilar']['mal_kabul']} giriş · {profil['kapilar']['sevkiyat']} çıkış kapısı"),
    ]) + "</div>", unsafe_allow_html=True)

    sol, sag = st.columns([2, 1])
    with sol, kart("Günlük Çıkış Hacmi"):
        f = go.Figure(go.Scatter(x=gun["tarih"], y=gun["adet"], mode="lines", name="Bu dönem",
                                 line=dict(color="#a9c714", width=3, shape="spline"),
                                 fill="tozeroy", fillcolor="rgba(217,242,59,.25)",
                                 hovertemplate="%{x|%d %b}<br><b>%{y:,.0f}</b> adet<extra></extra>"))
        if gun_onc is not None:
            f.add_trace(go.Scatter(x=gun_onc["tarih"] + pd.Timedelta(days=_n_onc), y=gun_onc["adet"], mode="lines", name="Önceki dönem",
                                   line=dict(color="#8d9097", width=1.6, dash="dot"),
                                   customdata=gun_onc["tarih"].dt.strftime("%d.%m.%Y"),
                                   hovertemplate="Önceki dönem %{customdata}<br><b>%{y:,.0f}</b> adet<extra></extra>"))
        f.update_layout(height=290, showlegend=gun_onc is not None, legend=dict(orientation="h", y=1.12, x=1, xanchor="right"))
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with sag, kart("Bölge Etiketleri (ABC)"):
        sinif = {"A": "d", "B": "l", "C": "n"}
        st.markdown(tablo(["Bölge", "Satır", "Adet", "Sınıf"],
                          [(esc(str(r.bolge)), sayi(r.satir), sayi(r.adet), etiket(r.abc, sinif[r.abc]))
                           for r in kroki.head(7).itertuples()]), unsafe_allow_html=True)

    k1, k2, k3 = st.columns([1.3, 1, 1])
    with k1, kart("Personel Performansı"):
        kisi = gp.groupby("personel", as_index=False).agg(gun=("tarih", "nunique"), adet=("adet", "sum"))
        kisi["uph"] = kisi["adet"] / (kisi["gun"] * h.VARDIYA_SAATI)
        med = kisi["uph"].median()
        rows = []
        for r in kisi.sort_values("uph", ascending=False).head(6).itertuples():
            s = ("Yüksek", "g") if r.uph >= 1.1 * med else ("Orta", "o") if r.uph >= 0.8 * med else ("Düşük", "r")
            rows.append((esc(r.personel), r.gun, sayi(r.uph), etiket(*s)))
        st.markdown(tablo(["Personel", "Gün", "UPH", "Seviye"], rows), unsafe_allow_html=True)
    with k2, kart("7 Günlük Tahmin"):
        tah, mape, _ = an.tahmin(gun_hist_tam, hedef_uph=hedef_uph or None)
        f = go.Figure(go.Scatter(x=tah["tarih"], y=tah["tahmin_adet"], mode="lines+markers",
                                 line=dict(color="#2f9e44", width=3), marker=dict(size=7)))
        f.update_layout(height=170, showlegend=False)
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
        st.markdown(f"**{int(tah['gereken_personel'].max())}** kişi en yoğun gün için gerekli · "
                    f"toplam **{sayi(tah['tahmin_adet'].sum())}** adet")
    with k3, kart("Canlı Uyarılar"):
        st.markdown("".join(f'<div class="uy {t}">{m}</div>' for t, m in uyarilar()), unsafe_allow_html=True)
        st.button("Dijital İkize Git", on_click=lambda: st.session_state.update(sayfa=[s for s in SAYFALAR if "Dijital" in s][0]))

    with kart("Forklift Durumu"):
        st.markdown(tablo(["Araç", "Durum", "Pil"],
                          [(r.id, etiket(r.durum, "g" if r.durum == "Yüklü" else "n"),
                            etiket(f"%{r.pil:.0f}", "r" if r.pil < 25 else "g")) for r in flk.itertuples()]),
                    unsafe_allow_html=True)
    st.caption(f"UPH = sevk edilen adet ÷ (personel-gün × {h.VARDIYA_SAATI} saat). Çalışma saati veride olmadığı için "
               "sevkiyat yapan herkes o gün tam vardiya çalışmış sayıldı.")

elif sayfa == "Siparişler":
    ust_baslik("Sipariş Planlama")
    SIP_DOSYA = Path(__file__).parent / "siparisler.csv"
    if "sip_taban" not in st.session_state:
        try:
            ilk = (pd.read_csv(SIP_DOSYA, dtype={"siparis_no": str}, parse_dates=["termin"]) if SIP_DOSYA.exists()
                   else vk.siparisler(SIMDI, ham, kaynak_ayar))
        except Exception:
            ilk = sp.bos()
        st.session_state.update(sip_taban=sp.temizle(ilk), sip_v=0)

    def yeni_taban(df, mesaj=None):
        st.session_state["sip_taban"] = sp.temizle(df)
        st.session_state["sip_v"] += 1
        if mesaj:
            st.session_state["sip_mesaj"] = mesaj

    if st.session_state.get("sip_mesaj"):
        st.success(st.session_state.pop("sip_mesaj"))

    # ---- 1) Parametreler -------------------------------------------------------------------
    varsayilan_uph = float(hedef_uph or gp["uph"].median())
    n_pick = sum(k["kisi"] for k in profil["kadro"] if "Toplay" in k["rol"]) or round(gun["personel"].mean())
    with kart("1 · Kapasite varsayımları"):
        p1, p2, p3 = st.columns(3)
        personel = p1.number_input("Günlük personel sayısı", 1, 200, max(1, n_pick),
                                   help="Bu siparişlere her gün ayrılacak çalışan sayısı.")
        uph = p2.number_input("Kişi başı UPH (adet/saat)", 1, 100000, max(1, round(varsayilan_uph)),
                              help="Varsayılan: verideki personellerin medyan UPH'si (Ayarlar'dan hedef UPH girebilirsiniz).")
        baslangic = p3.date_input("Plan başlangıcı", value=pd.Timestamp.today().date())
        st.caption("İş günü: Pazartesi–Cumartesi · vardiya 9 saat · sıra: önce öncelik, sonra termin.")

    # ---- 2) Sipariş girişi -----------------------------------------------------------------
    with kart("2 · Siparişleri girin"):
        g1, g2, g3 = st.tabs(["✍ Tabloya yaz", "⬆ Excel / CSV yükle", "🧪 Demo siparişler"])
        with g2:
            sablon = pd.DataFrame({"siparis_no": ["SIP-001"], "musteri": ["Örnek Müşteri"], "adet": [5000],
                                   "tamamlanan": [0], "termin": [pd.Timestamp.today().normalize() + pd.Timedelta(days=5)],
                                   "oncelik": ["Normal"]})
            st.download_button("Şablonu indir (CSV)", sablon.to_csv(index=False).encode("utf-8-sig"),
                               "siparis_sablonu.csv", "text/csv")
            dosya = st.file_uploader("Sipariş listesi", type=["xlsx", "csv"], key=f"sip_up_{st.session_state['sip_v']}")
            if dosya is not None and st.button("Yüklenen listeyi kullan"):
                try:
                    ham_sip = (pd.read_csv(dosya, dtype=str, sep=None, engine="python", encoding="utf-8-sig")
                               if dosya.name.lower().endswith(".csv") else pd.read_excel(dosya, dtype=str))
                    okunan = sp.temizle(sp.sutun_esle(ham_sip))
                    sifir = int((okunan["adet"] <= 0).sum())
                    yeni_taban(okunan, f"{len(okunan)} sipariş yüklendi." +
                               (f" ⚠ {sifir} satırda adet okunamadı/0 (sayıları 1500 gibi yazın)." if sifir else ""))
                    st.rerun()
                except Exception as e:
                    st.error(f"Dosya okunamadı: {e}")
        with g3:
            st.caption("Demo veriden 10 örnek sipariş eklenir (mevcut liste silinir).")
            if st.button("Örnek siparişleri yükle"):
                yeni_taban(sp.ornek(ham, pd.Timestamp.today().normalize()), "Örnek siparişler yüklendi.")
                st.rerun()
        with g1:
            st.caption("Satır eklemek için tablonun altındaki + işaretini kullanın. 'Tamamlanan' sütununu güncelledikçe ilerleme yenilenir.")
            duzenlenen = st.data_editor(
                st.session_state["sip_taban"], num_rows="dynamic", width="stretch", hide_index=True,
                key=f"sip_editor_{st.session_state['sip_v']}",
                column_config={
                    "siparis_no": st.column_config.TextColumn("Sipariş No", required=True),
                    "musteri": st.column_config.TextColumn("Müşteri"),
                    "adet": st.column_config.NumberColumn("Adet", min_value=0, step=1, format="%d"),
                    "tamamlanan": st.column_config.NumberColumn("Tamamlanan", min_value=0, step=1, format="%d"),
                    "termin": st.column_config.DateColumn("Termin", format="DD.MM.YYYY"),
                    "oncelik": st.column_config.SelectboxColumn("Öncelik", options=list(sp.ONCELIK), default="Normal"),
                })
            b1, b2, b3 = st.columns(3)
            if b1.button("💾 Kaydet", disabled=not YONETICI_OK):
                temiz = sp.temizle(duzenlenen)
                temiz.to_csv(SIP_DOSYA, index=False, encoding="utf-8-sig")
                yeni_taban(temiz, f"{len(temiz)} sipariş kaydedildi.")
                st.rerun()
            if b2.button("🔄 Sevkiyat verisinden ilerlemeyi güncelle",
                         help="Sipariş no, sevkiyat verisindeki teslimat/sevkiyat/sipariş numarasıyla eşleşirse sevk edilen adet 'Tamamlanan' olur."):
                n, yeni = sp.eslestir(duzenlenen, ham)
                yeni_taban(yeni, f"{n} siparişin ilerlemesi sevkiyat verisinden güncellendi." if n
                           else "Eşleşen sipariş numarası bulunamadı.")
                st.rerun()
            if b3.button("🗑 Listeyi temizle"):
                yeni_taban(sp.bos(), "Liste temizlendi.")
                st.rerun()

    # ---- 3) Sonuçlar -----------------------------------------------------------------------
    plan_girdi = sp.temizle(duzenlenen)
    tekrar = plan_girdi["siparis_no"][plan_girdi["siparis_no"].duplicated()].unique()
    if len(tekrar):
        st.warning(f"Tekrarlı sipariş no: {', '.join(tekrar[:5])} — ayrı sipariş sayıldı.")
    if plan_girdi.empty:
        st.info("Henüz sipariş yok. Yukarıdan tabloya yazın, dosya yükleyin ya da örnek siparişleri deneyin.")
    else:
        plan, yuk, oz = sp.planla(plan_girdi, baslangic, personel, uph)
        bitis_m = f"{oz['bitis']:%d.%m.%Y}" if pd.notna(oz["bitis"]) else "—"
        asg = oz["asgari_personel"]
        st.markdown('<div class="kpi-grid">' + "".join([
            kpi("Genel ilerleme", f"%{oz['ilerleme'] * 100:.0f}", f"{oz['acik']} / {oz['siparis']} sipariş açık",
                koyu=True, halka=oz["ilerleme"] * 100),
            kpi("Kalan iş", f"{oz['adam_gun']:.1f} adam-gün", f"{sayi(oz['kalan_adet'])} adet kaldı"),
            kpi("Tahmini bitiş", bitis_m, f"{personel} kişi ile", "nt"),
            kpi("Termine yetişmek için", "—" if pd.isna(asg) else f"{asg:.0f} kişi/gün",
                f"{oz['gecikir']} gecikir · {oz['riskli']} riskli", "kt" if oz["gecikir"] else "ok" if oz["riskli"] == 0 else "nt"),
        ]) + "</div>", unsafe_allow_html=True)

        if oz["gecikir"]:
            st.warning(f"⏰ Mevcut {personel} kişiyle {oz['gecikir']} sipariş termine yetişemiyor. "
                       + (f"Hepsini zamanında bitirmek için günde en az **{asg:.0f} kişi** gerekir." if pd.notna(asg) else ""))
        elif oz["acik"]:
            st.success(f"✅ Mevcut {personel} kişiyle tüm termin tarihlerine yetişiliyor.")

        renk = {"Tamamlandı": "d", "Zamanında": "g", "Riskli": "o", "Gecikir": "r", "Termin yok": "n", "Kapasite yok": "r", "Ufuk dışı": "r"}
        with kart("Sipariş durumu (işlem sırasıyla)"):
            def cubuk(p):
                return (f'<div style="background:#ececE8;border-radius:99px;height:8px;min-width:90px">'
                        f'<div style="width:{p * 100:.0f}%;background:#b5d11d;height:8px;border-radius:99px"></div></div>'
                        f'<span style="font-size:.72rem;color:#6b7076">%{p * 100:.0f}</span>')
            satirlar = [(esc(r.siparis_no), esc((r.musteri or "—")[:26]), sayi(r.adet), cubuk(r.ilerleme), f"{r.adam_gun:.1f}",
                         f"{r.termin:%d.%m}" if pd.notna(r.termin) else "—",
                         f"{r.bitis:%d.%m}" if pd.notna(r.bitis) else "—", etiket(r.durum, renk[r.durum]))
                        for r in plan.itertuples()]
            st.markdown(tablo(["Sipariş", "Müşteri", "Adet", "İlerleme", "Adam-gün", "Termin", "Bitiş", "Durum"], satirlar),
                        unsafe_allow_html=True)

        gantt = plan[plan["bitis"].notna() & plan["baslangic"].notna()].copy()
        if len(gantt):
            gantt["bitis_g"] = gantt["bitis"] + pd.Timedelta(days=1)
            with kart("Zaman çizelgesi"):
                f = px.timeline(gantt, x_start="baslangic", x_end="bitis_g", y="siparis_no", color="durum",
                                color_discrete_map={"Zamanında": "#8fb413", "Riskli": "#f59e0b", "Gecikir": "#ef4444",
                                                    "Termin yok": "#8d9097", "Kapasite yok": "#ef4444"})
                f.update_yaxes(autorange="reversed", title=None)
                f.update_xaxes(title=None)
                for r in gantt[gantt["termin"].notna()].itertuples():
                    f.add_trace(go.Scatter(x=[r.termin + pd.Timedelta(days=1)], y=[r.siparis_no], mode="markers",
                                           marker=dict(symbol="diamond", size=9, color="#1c1d20"), showlegend=False,
                                           hovertemplate=f"Termin {r.termin:%d.%m}<extra></extra>"))
                f.update_layout(height=max(200, 26 * len(gantt) + 80), legend_title=None)
                st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
                st.caption("◆ = termin. Çubuk: siparişin planlanan başlangıç–bitiş günleri.")
        if len(yuk):
            with kart("Günlük kapasite kullanımı"):
                f = go.Figure(go.Bar(x=yuk["tarih"], y=yuk["doluluk"], marker_color="#b5d11d",
                                     hovertemplate="%{x|%d %b}<br>%{y:.0f}% dolu<extra></extra>"))
                f.update_layout(height=190, yaxis_title="% kapasite", showlegend=False)
                st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
        indir = plan.drop(columns=["ilerleme"]).assign(ilerleme_pct=(plan["ilerleme"] * 100).round(0))
        st.download_button("⬇ Planı indir (CSV)", indir.to_csv(index=False).encode("utf-8-sig"), "siparis_plani.csv",
                           "text/csv")

elif sayfa == "Dijital İkiz":
    ust_baslik("Dijital İkiz")
    _gorus = st.radio("Görünüm", ["🔴 Canlı akış", "⏪ Zaman makinesi", "🛡 Güvenlik radarı", "🗺 Isı haritası (2D / 3D)"], horizontal=True,
                      label_visibility="collapsed", key="ikiz_gorus")
    if _gorus.startswith("🔴"):
        st.caption("Araçlar, kamyonlar ve palet hareketleri gerçek zamanlı akar; sağdaki olay akışı o anda olanları gösterir. "
                   + ("Konumlar bağlı API'nin telemetrisinden gelir." if kaynak_bilgi["mod"] == "api" and vk.telemetri(kaynak_ayar) is not None
                      else "Akış demo simülasyonudur; API bağlandığında aynı ekran gerçek araç konumlarıyla çalışır."))
        _bugun = ham_tum[ham_tum["tarih"] == BUGUN]

        @st.fragment(run_every=(6 if kaynak_bilgi["mod"] == "api" else None))
        def canli_goster():
            _tel = vk.telemetri(kaynak_ayar)
            _liste = None if _tel is None else _tel.assign(pil=_tel["pil"].astype(float)).to_dict("records")
            _f = canli.feed(kroki, profil, n_flk, len(_bugun), int(_bugun["adet"].sum()), telemetri=_liste, kriz=st.session_state.get("kriz"))
            st.iframe(canli.html(_f), height=840)

        canli_goster()
    elif _gorus.startswith("⏪"):
        gunler_t = sorted(ham_tum["tarih"].dt.date.unique(), reverse=True)
        gun_t = st.selectbox("Oynatılacak gün", gunler_t, index=1 if len(gunler_t) > 1 else 0,
                             format_func=lambda d: f"{d:%d.%m.%Y}", key="zm_gun")
        st.caption("Seçilen günün GERÇEK sevkiyat, mal kabul ve yükleme kayıtları hızlandırılarak oynatılır: bölgeler sevk edildikçe ısınır, kamyonlar kayıtlı saatlerde yanaşır. "
                   "Kaydırıcıyla günün herhangi bir saatine atlayabilirsiniz. Araç hareketleri simülasyondur.")
        st.iframe(canli.html(canli.feed_replay(kroki, profil, n_flk, pd.Timestamp(gun_t), ham_tum, inbound_tum, surec_tum)), height=900)
    elif _gorus.startswith("🛡"):
        vard = st.radio("Vardiya", ["Gündüz (06:00-15:00)", "Akşam (15:00-24:00)"], horizontal=True, key="gv_vard")
        gs = guvenlik_ozeti(VERI_IMZA, profil, 6 if vard.startswith("Gündüz") else 15)
        st.caption("Forklift rotalarının kesişimlerinde 3 metreden yakın geçişler (yakın geçiş / near-miss) sayılır. Araç rotaları simülasyondur; "
                   "gerçek telemetri bağlanınca aynı analiz gerçek konumlarla çalışır.")
        kes, saat_g = gs["kesisim"], gs["saatlik"]
        en_riskli = kes.iloc[0] if len(kes) else None
        pik = saat_g.loc[saat_g["olay"].idxmax()] if len(saat_g) else None
        st.markdown('<div class="kpi-grid">' + "".join([
            kpi("Yakın geçiş (vardiya)", sayi(gs["olay"]), f"{gs['araclar']} araç · eşik {gs['esik']:.0f} m", "kt" if gs["olay"] > 500 else "ok", koyu=True),
            kpi("En riskli kesişim", f"x≈{en_riskli.cx:.0f}, y≈{en_riskli.cy:.0f} m" if en_riskli is not None else "—", f"{sayi(en_riskli.olay)} yakın geçiş" if en_riskli is not None else "", "kt"),
            kpi("Pik saat", f"{int(pik['saat'])}:00" if pik is not None else "—", f"{sayi(pik['olay'])} olay" if pik is not None else ""),
            kpi("Önerilen önlem", "Tek yönlü trafik", "koridor ayrımı + 5 km/s sınır", "nt"),
        ]) + "</div>", unsafe_allow_html=True)
        gc1, gc2 = st.columns([1.5, 1])
        with gc1, kart("Yakın geçiş yoğunluk haritası"):
            g_ = tw.geometri(profil)
            f = go.Figure()
            if len(gs["nokta"]):
                f.add_trace(go.Histogram2d(x=gs["nokta"]["x"], y=gs["nokta"]["y"], xbins=dict(start=0, end=g_["en"], size=5),
                                           ybins=dict(start=0, end=g_["boy"], size=5), colorscale=[[0, "rgba(255,255,255,0)"], [0.2, "#fde68a"], [1, "#dc2626"]],
                                           showscale=False, hovertemplate="%{z} yakın geçiş<extra></extra>"))
            f.add_shape(type="rect", x0=0, y0=0, x1=g_["en"], y1=g_["boy"], line=dict(color="#1c1d20", width=2))
            for r_ in kroki.itertuples():
                f.add_shape(type="rect", x0=r_.x, y0=r_.y, x1=r_.x + r_.w, y1=r_.y + r_.d, line=dict(color="#c6c9d0"), fillcolor="rgba(241,242,245,.55)", layer="below")
            f.update_xaxes(visible=False, scaleanchor="y", range=[-2, g_["en"] + 2])
            f.update_yaxes(visible=False, range=[-2, g_["boy"] + 2])
            f.update_layout(height=470, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="white")
            st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
        with gc2, kart("Kesişim noktaları ve öneriler"):
            st.markdown(tablo(["Konum", "Yakın geçiş"], [(esc(r.konum), etiket(sayi(r.olay), "r" if r.olay > kes["olay"].mean() else "o")) for r in kes.itertuples()]),
                        unsafe_allow_html=True)
            st.markdown('<div class="uy w">🚦 En riskli koridorlarda <b>tek yönlü trafik</b> uygulayın; mal kabul (giriş) ve sevkiyat (çıkış) araçlarını farklı koridorlara ayırın.</div>'
                        '<div class="uy w">🪞 Kör kesişimlere dönüş aynası ve yer işaretlemesi, hız sınırı 5 km/s.</div>', unsafe_allow_html=True)
            fh = px.bar(saat_g, x="saat", y="olay"); fh.update_traces(marker_color="#ef4444"); fh.update_layout(height=170, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fh, width="stretch", config={"displayModeBar": False})
    else:
        st.caption("Isı rengi seçili gün/saatteki sevkiyat satırlarından gelir. Gün/saat/forklift ayarı soldaki 'Canlı seçim' kutusundadır.")
        r1, r2 = st.columns(2)
        gorunum = r1.radio("Görünüm", ["2D", "3D"], horizontal=True)
        katman = r2.radio("Katman", ["Hareket", "Doluluk"], horizontal=True,
                          help="Hareket: seçili gün/saatteki sevk satırı. Doluluk: raf gözlerinin doluluk yüzdesi.")
        deger = isi if katman == "Hareket" else stok.set_index("bolge")["doluluk"]
        with kart():
            fig = (tw.fig_2d if gorunum == "2D" else tw.fig_3d)(kroki, deger, flk, profil, katman)
            st.plotly_chart(fig, width="stretch", config={"scrollZoom": True, "displaylogo": False})
        st.caption("Kutudaki yazı: bölge · ABC sınıfı · hareket (satır) ya da doluluk (%). Mavi kapılar sevkiyat, yeşil kapılar mal kabul. "
                   "Forklift rengi: mavi boş, yeşil yüklü, kırmızı pil < %25.")
    with kart("Canlı Uyarılar"):
        st.markdown("".join(f'<div class="uy {t}">{m}</div>' for t, m in uyarilar()), unsafe_allow_html=True)

elif sayfa == "Depo Profili":
    import pandas as _pd
    ust_baslik("Depo Profili")
    st.caption("Bu sayfadaki değerler sunum için ÖRNEKTİR (10.800 m² depo, 60 kişilik kadro). Gerçek değerleri tablolara yazıp Kaydet'e basın; "
               "kroki, kapasite ve simülasyonlar otomatik güncellenir.")
    g = tw.geometri(profil)
    for u in dp.uyarilar(profil):
        st.warning("⚠ " + u)
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Toplam alan", f"{dp.toplam(profil):,.0f} m²".replace(",", "."), f"{g['en']:.0f} × {g['boy']:.0f} m · tavan {profil['tavan_m']:.0f} m", koyu=True),
        kpi("Palet gözü", sayi(stok["pozisyon"].sum()), f"{profil['raf_seviye']} seviye raf · %{stok['dolu'].sum() / stok['pozisyon'].sum() * 100:.0f} dolu"),
        kpi("Depolama alanı", f"{dp.toplam(profil, ['depolama']):,.0f} m²".replace(",", "."),
            f"%{dp.toplam(profil, ['depolama']) / dp.toplam(profil) * 100:.0f} · {len(kroki)} bölge"),
        kpi("Filo & kadro", f"{filo_n} / {sum(k['kisi'] for k in profil['kadro'])}", "forklift / kişi"),
    ]) + "</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.4])
    with c1, kart("Alan dağılımı"):
        ad = _pd.DataFrame(profil["alanlar"])
        f = px.pie(ad, names="ad", values="alan_m2", hole=0.55,
                   color_discrete_sequence=["#1c1d20", "#b5d11d", "#8d9097", "#3b82f6", "#f59e0b", "#2f9e44", "#ef4444", "#6b7280"])
        f.update_traces(textposition="inside", textinfo="percent", insidetextorientation="horizontal")
        f.update_layout(height=320, legend=dict(orientation="h", y=-0.05, font=dict(size=10)), margin=dict(l=4, r=4, t=10, b=4))
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with c2, kart("Bölge bazında kapasite"):
        st.markdown(tablo(["Bölge", "Sınıf", "m²", "Palet gözü", "Dolu", "Doluluk"],
                          [(esc(str(r.bolge)), r.abc, sayi(r.alan_m2), sayi(r.pozisyon), sayi(r.dolu),
                            etiket(f"%{r.doluluk:.0f}", "r" if r.doluluk > 92 else "g" if r.doluluk >= 70 else "o"))
                           for r in stok.sort_values("adet", ascending=False).itertuples()]), unsafe_allow_html=True)

    with st.form("profil_form"):
        st.markdown("**Genel**")
        a1, a2, a3, a4 = st.columns(4)
        y_ad = a1.text_input("Depo adı", profil["ad"])
        y_toplam = a2.number_input("Toplam alan (m²)", 100, 1000000, int(profil["toplam_alan_m2"]), 100)
        y_en = a3.number_input("Bina eni (m)", 10.0, 1000.0, float(profil["bina_en_m"]), 1.0)
        y_boy = a4.number_input("Bina boyu (m)", 10.0, 1000.0, float(profil["bina_boy_m"]), 1.0)
        b1, b2, b3, b4 = st.columns(4)
        y_tavan = b1.number_input("Tavan yüksekliği (m)", 3.0, 40.0, float(profil["tavan_m"]), 0.5)
        y_raf = b2.number_input("Raf seviyesi", 1, 12, int(profil["raf_seviye"]))
        y_pt = b3.number_input("Palet taban alanı (m²/göz)", 0.5, 5.0, float(profil["palet_taban_m2"]), 0.1)
        y_dol = b4.number_input("Hedef doluluk (%)", 30, 100, round(profil["hedef_doluluk"] * 100))
        k1, k2, k3, k4 = st.columns(4)
        y_kx = k1.number_input("Dikey koridor (m)", 1.0, 10.0, float(profil["koridor_x_m"]), 0.5)
        y_ky = k2.number_input("Yatay koridor (m)", 1.0, 10.0, float(profil["koridor_y_m"]), 0.5)
        y_kg = k3.number_input("Mal kabul kapısı", 0, 60, int(profil["kapilar"]["mal_kabul"]))
        y_ks = k4.number_input("Sevkiyat kapısı", 0, 60, int(profil["kapilar"]["sevkiyat"]))
        st.markdown("**Alanlar** (tür: " + ", ".join(dp.TURLER) + ")")
        y_alan = st.data_editor(_pd.DataFrame(profil["alanlar"]), num_rows="dynamic", width="stretch", hide_index=True,
                                column_config={"ad": "Alan adı", "alan_m2": st.column_config.NumberColumn("m²", min_value=0, step=10),
                                               "tur": st.column_config.SelectboxColumn("Tür", options=dp.TURLER, required=True)})
        st.markdown("**Forklift / MHE filosu**")
        y_fl = st.data_editor(_pd.DataFrame(profil["forkliftler"]), num_rows="dynamic", width="stretch", hide_index=True,
                              column_config={"tip": "Tip", "adet": st.column_config.NumberColumn("Adet", min_value=0, step=1),
                                             "hiz_ms": st.column_config.NumberColumn("Hız (m/sn)", min_value=0.3, step=0.1),
                                             "pil_saat": st.column_config.NumberColumn("Pil ömrü (sa)", min_value=1, step=1)})
        e1, e2 = st.columns(2)
        with e1:
            st.markdown("**Vardiyalar**")
            y_vd = st.data_editor(_pd.DataFrame(profil["vardiyalar"]), num_rows="dynamic", width="stretch", hide_index=True,
                                  column_config={"ad": "Vardiya", "baslangic": "Başlangıç", "bitis": "Bitiş",
                                                 "kisi": st.column_config.NumberColumn("Kişi", min_value=0, step=1)})
        with e2:
            st.markdown("**Kadro (rol bazında)**")
            y_kd = st.data_editor(_pd.DataFrame(profil["kadro"]), num_rows="dynamic", width="stretch", hide_index=True,
                                  column_config={"rol": "Rol", "kisi": st.column_config.NumberColumn("Kişi", min_value=0, step=1)})
        st.markdown("**Süre hedefleri (saat) ve mal kabul varsayımları**")
        h1, h2, h3, h4, h5 = st.columns(5)
        y_h = {"bosaltma_saat": h1.number_input("Boşaltma", 0.1, 48.0, float(profil["hedefler"]["bosaltma_saat"]), 0.5),
               "dock_to_stock_saat": h2.number_input("Putaway (dock-to-stock)", 0.1, 48.0, float(profil["hedefler"]["dock_to_stock_saat"]), 0.5),
               "toplama_saat": h3.number_input("Toplama", 0.1, 72.0, float(profil["hedefler"]["toplama_saat"]), 0.5),
               "paketleme_saat": h4.number_input("Paketleme", 0.1, 48.0, float(profil["hedefler"]["paketleme_saat"]), 0.5),
               "sevk_saat": h5.number_input("Sevkiyat", 0.1, 48.0, float(profil["hedefler"]["sevk_saat"]), 0.5)}
        s1, s2, s3, s4 = st.columns(4)
        y_s = {"palet_basi_adet": s1.number_input("Palet başına adet", 1, 100000, int(profil["simulasyon"]["palet_basi_adet"])),
               "kamyon_palet": s2.number_input("Kamyon başına palet", 1, 100, int(profil["simulasyon"]["kamyon_palet"])),
               "kamyon_bosaltma_dk": s3.number_input("Kamyon boşaltma (dk)", 5, 480, int(profil["simulasyon"]["kamyon_bosaltma_dk"])),
               "kapi_acik_saat": s4.number_input("Kapı açık saat/gün", 1, 24, int(profil["simulasyon"]["kapi_acik_saat"]))}
        kaydet = st.form_submit_button("💾 Profili kaydet", disabled=not YONETICI_OK)
    if kaydet:
        yeni = {"ad": y_ad, "toplam_alan_m2": y_toplam, "bina_en_m": y_en, "bina_boy_m": y_boy, "tavan_m": y_tavan,
                "raf_seviye": y_raf, "palet_taban_m2": y_pt, "koridor_x_m": y_kx, "koridor_y_m": y_ky,
                "hedef_doluluk": y_dol / 100, "kapilar": {"mal_kabul": y_kg, "sevkiyat": y_ks},
                "alanlar": y_alan.dropna(subset=["ad", "tur"]).fillna({"alan_m2": 0}).to_dict("records"),
                "forkliftler": y_fl.dropna(subset=["tip"]).fillna({"adet": 0, "hiz_ms": 1.8, "pil_saat": 8}).to_dict("records"),
                "vardiyalar": y_vd.dropna(subset=["ad"]).fillna({"kisi": 0, "baslangic": "", "bitis": ""}).to_dict("records"),
                "kadro": y_kd.dropna(subset=["rol"]).fillna({"kisi": 0}).to_dict("records"),
                "hedefler": y_h, "simulasyon": y_s}
        hatalar = dp.hata_var(yeni)
        if hatalar:
            for m in hatalar:
                st.error(m)
        else:
            dp.kaydet(yeni)
            st.success("Profil kaydedildi. Sayfa yenileniyor…")
            st.rerun()
    if st.button("↩ Örnek (10.800 m²) değerlere dön", disabled=not YONETICI_OK):
        dp.kaydet(dp.varsayilan())
        st.rerun()

elif sayfa == "Entegrasyon":
    import json as _json
    import os as _os
    ust_baslik("Entegrasyon")
    st.caption("Uygulama verisini demo'dan ya da kendi sisteminizin (WMS / ERP / IoT) API'sinden alır. API bağlanınca tüm sayfalar "
               "canlı veriyle çalışır; ulaşılamayan ya da henüz bağlanmamış uç noktalar demo ile tamamlanır, hiçbir sayfa boş kalmaz.")
    ay = vk.yukle_ayar()
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Aktif kaynak", "API" if kaynak_bilgi["mod"] == "api" else "Demo", "sunum verisi" if kaynak_bilgi["mod"] == "demo" else "canlı", koyu=True),
        kpi("Sevkiyat satırı", sayi(len(ham)), f"{ham['tarih'].nunique()} gün"),
        kpi("Son kayıt", f"{ham['sevk_zamani'].max():%H:%M}", f"{ham['sevk_zamani'].max():%d.%m.%Y}"),
        kpi("Demo ile tamamlanan", len(kaynak_bilgi["demo_parcalar"]) or "–", ", ".join(kaynak_bilgi["demo_parcalar"]) or "yok"),
    ]) + "</div>", unsafe_allow_html=True)
    if kaynak_bilgi["hata"]:
        st.error(f"API'ye ulaşılamadı, demo veriyle devam ediliyor: {kaynak_bilgi['hata']}")
    if not YONETICI_OK:
        st.warning("Ayarları değiştirmek için yan menüde Ayarlar → yönetici şifresini girin.")

    with kart("1 · Bağlantı"):
        mod = st.radio("Kaynak", ["demo", "api"], index=["demo", "api"].index(ay["mod"]), horizontal=True,
                       format_func={"demo": "Demo (sunum verisi)", "api": "Gerçek API"}.get)
        c1, c2 = st.columns([2, 1])
        base = c1.text_input("API adresi (base URL)", ay["api"]["base_url"], placeholder="https://api.sirketiniz.com/v1")
        tok_ad = c2.text_input("Token ortam değişkeni", ay["api"]["token_env"],
                               help="Token dosyaya yazılmaz; sunucuda bu isimde bir ortam değişkeni olarak tanımlanır.")
        st.caption("Token: " + ("✓ tanımlı" if _os.environ.get(tok_ad or "") else "tanımlı değil (herkese açık/anahtarsız API için gerekmez)")
                   + " · istekler 'Authorization: Bearer <token>' başlığıyla gider.")
        u = st.columns(5)
        uclar = {k: u[i].text_input(f"{k} ucu", ay["api"]["uclar"][k]) for i, k in enumerate(vk.SEMA)}
        zt = st.number_input("Zaman aşımı (sn)", 1, 60, int(ay["api"]["zaman_asimi_sn"]))

    with kart("2 · Alan eşleme (API alan adı → standart alan)"):
        st.caption("API'nizin alan adları standart adlardan farklıysa sağ sütuna yazın; boş bırakırsanız alan adı aynı kabul edilir. "
                   "Zorunlu alanlar işaretlidir.")
        sek = st.tabs(list(vk.SEMA))
        yeni_alan = {}
        for tab, tur in zip(sek, vk.SEMA):
            with tab:
                satirlar = [{"standart": c, "zorunlu": "evet", "api_alani": ay["api"]["alanlar"].get(tur, {}).get(c, "")}
                            for c in vk.SEMA[tur]["zorunlu"]] + \
                           [{"standart": c, "zorunlu": "hayır", "api_alani": ay["api"]["alanlar"].get(tur, {}).get(c, "")}
                            for c in vk.SEMA[tur]["istege_bagli"]]
                ed = st.data_editor(pd.DataFrame(satirlar), hide_index=True, width="stretch", key=f"esle_{tur}",
                                    disabled=["standart", "zorunlu"],
                                    column_config={"standart": "Standart alan", "zorunlu": "Zorunlu", "api_alani": "API'deki alan adı"})
                yeni_alan[tur] = {r.standart: r.api_alani for r in ed.itertuples() if str(r.api_alani or "").strip()}

    yeni_ay = {"mod": mod, "api": {"base_url": base, "token_env": tok_ad, "zaman_asimi_sn": zt, "uclar": uclar, "alanlar": yeni_alan}}
    b1, b2, _ = st.columns([1, 1, 2])
    if b1.button("💾 Kaydet", disabled=not YONETICI_OK, key="kaynak_kaydet"):
        vk.kaydet_ayar(yeni_ay)
        st.cache_data.clear()
        st.success("Kaydedildi. Veriler yeniden yükleniyor…")
        st.rerun()
    if b2.button("🔌 Bağlantıyı test et", disabled=not base.strip(), key="kaynak_test"):
        sonuc = vk.ApiKaynak(yeni_ay).test()
        renk = {"tamam": "g", "alan eksik": "o", "ulaşılamadı": "r"}
        with kart("Test sonucu"):
            st.markdown(tablo(["Uç", "Durum", "Satır", "Gelen alanlar", "Not"],
                              [(k, etiket(v[0], renk[v[0]]), v[1], esc(v[2][:70]), esc(v[3][:110])) for k, v in sonuc.items()]),
                        unsafe_allow_html=True)

    with kart("3 · Beklenen veri sözleşmesi (örnek yük)"):
        st.caption("API'niz bu uç noktalardan JSON dizisi (ya da {\"data\": [...]}) dönmelidir. Aşağıda her uç için demo verinin örnek kaydı var; "
                   "ayrıntılı açıklama API_SOZLESME.md dosyasındadır.")
        ornekler = {"sevkiyat": ham.tail(2), "inbound": inbound.tail(2), "surec": surec_tab.tail(2),
                    "forklift": flk[["id", "tip", "x", "y", "durum", "pil"]].head(2),
                    "siparis": vk.siparisler(SIMDI, ham, vk.yukle_ayar()).head(2)}
        ts = st.tabs(list(ornekler))
        for tab, (tur, df) in zip(ts, ornekler.items()):
            with tab:
                js = _json.loads(df.to_json(orient="records", date_format="iso", force_ascii=False))
                st.json(js, expanded=1)
                st.download_button(f"⬇ {tur}_ornek.json", _json.dumps(js, ensure_ascii=False, indent=2).encode("utf-8"),
                                   f"{tur}_ornek.json", "application/json", key=f"dl_{tur}")

    with kart("4 · Bildirimler (Slack / Teams / webhook)"):
        bz = bildirim.yukle()
        st.caption("Kritik (kırmızı) uyarılar webhook'a otomatik gönderilir; aynı uyarı saatte bir tekrarlanmaz. "
                   "Webhook adresi dosyaya yazılmaz, sunucuda ortam değişkeni olarak tutulur.")
        turler = ["slack", "teams", "genel"]
        bz1, bz2, bz3 = st.columns(3)
        bz_aktif = bz1.toggle("Otomatik bildirim açık", bz["aktif"], key="bz_aktif")
        bz_tur = bz2.selectbox("Tür", turler, index=turler.index(bz["tur"]) if bz["tur"] in turler else 0, key="bz_tur")
        bz_env = bz3.text_input("Webhook ortam değişkeni", bz["webhook_env"], key="bz_env")
        st.caption("Webhook adresi: " + ("✓ tanımlı" if _os.environ.get(bz_env or "") else "tanımlı değil — sunucuda " + (bz_env or "OPLOG_WEBHOOK_URL") + " ortam değişkenini ayarlayın"))
        bk1, bk2, _ = st.columns([1, 1, 2])
        if bk1.button("💾 Kaydet", key="bz_kaydet", disabled=not YONETICI_OK):
            bildirim.kaydet({"aktif": bz_aktif, "webhook_env": bz_env, "tur": bz_tur, "tekrar_saat": bz["tekrar_saat"]})
            st.success("Bildirim ayarları kaydedildi.")
        if bk2.button("📨 Test mesajı gönder", key="bz_test"):
            ok_, msg_ = bildirim.gonder(_os.environ.get(bz_env or "", ""), "✅ OPLOG test mesajı: bildirim kanalı çalışıyor.", bz_tur)
            (st.success if ok_ else st.error)(("Gönderildi · " if ok_ else "Gönderilemedi · ") + msg_)

elif sayfa == "Senaryo":
    ust_baslik("Senaryo Merkezi")
    st.caption("“Ya şöyle olursa?” Önümüzdeki 7 günün tahmini talebi, seçtiğiniz kadro/ekipman/olaylara göre kapasiteye karşı akıtılır. "
               "Kriz düğmeleri tek tıkla hazır olay uygular; sonucu canlı ikize de gönderebilirsiniz.")
    tah_s, _, _ = an.tahmin(gun_hist_tam)
    n_pick = sum(k["kisi"] for k in profil["kadro"] if "Toplay" in k["rol"]) or 24
    uph_s = float(hedef_uph or gp["uph"].median() * 1.10)        # kapasite UPH: ortanca + %10 verimlilik hedefi
    ort_sip = float(veri.groupby("teslimat")["adet"].sum().mean())
    VARS = {"sn_kadro": n_pick, "sn_forklift": filo_n, "sn_artis": 0, "sn_eksik": 0, "sn_ariza": 0, "sn_kamyon": 0.0}
    for _k, _v in VARS.items():
        st.session_state.setdefault(_k, _v)

    def _kriz_uygula(anahtar):
        k = sn.KRIZLER[anahtar]
        for ad, ks in (("artis", "sn_artis"), ("personel_eksik", "sn_eksik"), ("forklift_ariza", "sn_ariza"), ("kamyon_gecikme_sa", "sn_kamyon")):
            if ad in k:
                st.session_state[ks] = k[ad]

    def _sn_sifirla():
        for _k, _v in VARS.items():
            st.session_state[_k] = _v
        st.session_state.pop("kriz", None)

    def _sn_hepsi():
        for a_ in sn.KRIZLER:
            _kriz_uygula(a_)

    bc = st.columns(len(sn.KRIZLER) + 2)
    for c_, (k_, v_) in zip(bc, sn.KRIZLER.items()):
        c_.button(f"{v_['ikon']} {v_['ad']}", on_click=_kriz_uygula, args=(k_,), key=f"kb_{k_}", width="stretch", help=v_["aciklama"])
    bc[-2].button("🔥 Hepsi birden", on_click=_sn_hepsi, width="stretch")
    bc[-1].button("↺ Sıfırla", on_click=_sn_sifirla, width="stretch")

    with kart("Senaryo ayarları"):
        s1, s2, s3 = st.columns(3)
        kadro_s = s1.slider("Günlük toplayıcı sayısı", 5, 80, key="sn_kadro")
        forklift_s = s2.slider("Forklift / MHE sayısı", 2, 40, key="sn_forklift")
        artis_s = s3.slider("Sipariş artışı (%)", 0, 100, key="sn_artis")
        s4, s5, s6 = st.columns(3)
        eksik_s = s4.slider("Personel devamsızlığı (%)", 0, 50, key="sn_eksik")
        ariza_s = s5.slider("Arızalı forklift", 0, 10, key="sn_ariza")
        kamyon_s = s6.slider("Mal kabul gecikmesi (saat)", 0.0, 12.0, step=0.5, key="sn_kamyon")

    taban = sn.hesapla(tah_s, n_pick, uph_s, filo_n, profil, ort_siparis_adet=ort_sip)
    senar = sn.hesapla(tah_s, kadro_s, uph_s, forklift_s, profil, artis=artis_s / 100, personel_eksik=eksik_s / 100,
                       forklift_ariza=ariza_s, kamyon_gecikme_sa=kamyon_s, ort_siparis_adet=ort_sip)
    rk = {"Düşük": "ok", "Orta": "nt", "Yüksek": "kt"}
    dk = senar["kullanim"] - taban["kullanim"]
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Kapasite kullanımı", f"%{senar['kullanim'] * 100:.0f}", f"taban %{taban['kullanim'] * 100:.0f}" + (f" · {'▲' if dk > 0.005 else '▼'}%{abs(dk) * 100:.0f}" if abs(dk) > 0.005 else ""),
            "kt" if senar["kullanim"] > 1.0 else "ok", koyu=True, halka=min(senar["kullanim"] * 100, 100)),
        kpi("Birikim (adet)", sayi(senar["birikim"]), f"≈ {senar['gecikme_gun']:.1f} gün gecikme", "kt" if senar["birikim"] > 0 else "ok"),
        kpi("Termin riski", senar["risk"], f"~{senar['geciken_siparis']:.0f} sipariş etkilenir", rk[senar["risk"]]),
        kpi("Gereken kaynak", f"{senar['gereken_kadro']} kişi", f"{senar['gereken_forklift']} forklift · {sn.ml.tl(senar['gecikme_tl'])} gecikme maliyeti", "nt"),
    ]) + "</div>", unsafe_allow_html=True)

    g1, g2 = st.columns([1.5, 1])
    with g1, kart("7 günlük talep · kapasite · birikim"):
        sr_ = senar["seri"]
        f = go.Figure()
        f.add_bar(x=sr_["tarih"], y=sr_["talep"], name="Talep", marker_color="#d9f23b")
        f.add_trace(go.Scatter(x=sr_["tarih"], y=sr_["kapasite"], name="Kapasite", mode="lines+markers", line=dict(color="#1c1d20", width=3)))
        f.add_trace(go.Scatter(x=sr_["tarih"], y=sr_["birikim"], name="Birikim", mode="lines", fill="tozeroy",
                               line=dict(color="#ef4444", width=2), fillcolor="rgba(239,68,68,.15)"))
        f.add_trace(go.Scatter(x=taban["seri"]["tarih"], y=taban["seri"]["kapasite"], name="Taban kapasite", mode="lines",
                               line=dict(color="#8d9097", width=1.5, dash="dot")))
        f.update_layout(height=290, legend=dict(orientation="h", y=1.15), barmode="overlay")
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with g2, kart("Sistem önerisi"):
        for m_ in sn.oneriler(senar, kadro_s, forklift_s, ariza_s, kamyon_s):
            st.markdown(f'<div class="uy {"s" if m_.startswith("✅") else "w"}">{m_}</div>'.replace("**", "").replace("\n", " "), unsafe_allow_html=True)
        st.caption(f"Model: kapasite = kadro × UPH ({uph_s:.0f}; ortanca UPH + %10 hedef) × 9 sa × forklift çarpanı; Cmt %70, Paz %20 kadro. "
                   f"Ek kadro maliyeti ≈ {sn.ml.tl(senar['ek_kadro_tl_gun'])}/gün.")
    kriz_var = any([artis_s, eksik_s, ariza_s, kamyon_s])
    ba, bb, _ = st.columns([1.2, 1, 2])

    def _canliya_uygula():
        st.session_state["kriz"] = {"arizali": ariza_s, "kamyon_gecikme_sa": kamyon_s, "artis": artis_s / 100}
        st.session_state["sayfa"] = [s for s in SAYFALAR if "Dijital" in s][0]
        st.session_state["ikiz_gorus"] = "🔴 Canlı akış"

    ba.button("🔴 Canlı ikize uygula", on_click=_canliya_uygula, disabled=not (ariza_s or kamyon_s or artis_s), width="stretch",
              help="Arızalı forkliftler, gecikmeli kamyonlar ve artan yoğunluk Dijital İkiz'de canlı görünür.")
    bb.button("Krizi ikizden kaldır", on_click=lambda: st.session_state.pop("kriz", None), disabled="kriz" not in st.session_state, width="stretch")

elif sayfa == "Yerleşim":
    ust_baslik("Raf Yerleşim Önerisi")
    st.caption("Hareketli bölgeleri sevkiyat kapısına yaklaştıran önerilen yerleşim (ABC), mevcut yerleşimle yan yana. Fark; yürüme mesafesi, süre, maliyet ve karbon olarak hesaplanır.")
    taban_ad = st.radio("Karşılaştırılacak mevcut yerleşim", ["Bölge kodu sırası", "Rastgele"], horizontal=True, key="yer_taban")
    strat = {"Bölge kodu sırası": "kod", "Rastgele": "rastgele"}[taban_ad]
    ky = yer_kiyas(VERI_IMZA, profil, strat)
    kroki_mevcut = tw.yerlesim(veri, profil, strat)
    sev_gun = float(veri.groupby("tarih")["sevkiyat"].nunique().mean())
    fark_m = max(ky["mevcut_m"] - ky["oneri_m"], 0.0)
    gun_m = fark_m * sev_gun * ky["cok_bolge_orani"]
    krb = ml.karbon(gun_m, profil)
    saat_gun = gun_m / ml.YURUME_HIZI / 3600
    yil_tl = saat_gun * ml.saat_tl(ml.varsayim(profil)) * ml.IS_GUNU_YIL
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Yürüme / sevkiyat", f"{ky['oneri_m']:.0f} m", f"mevcut {ky['mevcut_m']:.0f} m", "ok", koyu=True, halka=max(0, 100 - ky["oneri_m"] / max(ky["mevcut_m"], 1) * 100) if ky["mevcut_m"] else None),
        kpi("Günlük tasarruf", f"{gun_m / 1000:.1f} km", f"{saat_gun:.1f} saat/gün", "ok"),
        kpi("Yıllık maliyet etkisi", ml.tl(yil_tl), f"{ml.IS_GUNU_YIL} iş günü varsayımı", "ok"),
        kpi("Karbon", f"{krb['co2_kg_yil'] / 1000:.1f} t CO₂", f"{krb['kwh_yil']:,.0f} kWh/yıl".replace(",", "."), "ok"),
    ]) + "</div>", unsafe_allow_html=True)
    hareket = veri["sku"].map(h.bolge_kodu).value_counts()
    yc1, yc2 = st.columns(2)
    for kol, ad, krk, ksat in ((yc1, f"Mevcut · {taban_ad.lower()}", kroki_mevcut, "d"), (yc2, "Önerilen · hareket sıklığına göre (ABC)", kroki, "l")):
        with kol, kart(ad):
            fg = tw.fig_2d(krk, hareket, flk, profil, "Hareket")
            fg.update_layout(height=430)
            st.plotly_chart(fg, width="stretch", config={"displayModeBar": False})
    st.caption(f"Hesap: son 30 günde çok bölgeli sevkiyatlardan {ky['ornek']} örnek; her sevkiyat için en yakın komşu rotası. "
               f"Çok bölgeli sevkiyat oranı %{ky['cok_bolge_orani'] * 100:.0f}, günde ortalama {sev_gun:.0f} sevkiyat. Kutudaki sayı: dönemdeki satır.")

elif sayfa == "Maliyet & ROI":
    ust_baslik("Maliyet & ROI")
    mv = ml.varsayim(profil)
    mal = ml.donem(gun_tam, profil)
    yil_tl_personel = ml.yilliklastir(mal["personel_tl"], mal["gun"])
    ky = yer_kiyas(VERI_IMZA, profil, "kod")
    sev_gun = float(veri.groupby("tarih")["sevkiyat"].nunique().mean())
    yer_m_gun = max(ky["mevcut_m"] - ky["oneri_m"], 0.0) * sev_gun * ky["cok_bolge_orani"]
    sr_m = an.sureler(surec_tab, inbound, profil["hedefler"])
    den_m = an.surec_denetimi(ham, inbound, surec_tab, profil["hedefler"])
    asim = den_m[den_m["kontrol"].str.contains("Toplama")]["oran_%"].iloc[0] / 100
    gec_yil = asim * (veri["teslimat"].nunique() / max(veri["tarih"].nunique(), 1)) * ml.IS_GUNU_YIL * 0.10
    put_palet = inbound["palet"].sum() / max(inbound["tarih"].nunique(), 1)
    kal = ml.kalemler(profil, gun_tam, yer_m_gun, sr_m, gec_yil, put_palet)
    toplam_firsat = sum(k[1] for k in kal)
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Personel maliyeti (dönem)", ml.tl(mal["personel_tl"]), f"{mal['gun']} gün · yıllık ≈ {ml.tl(yil_tl_personel)}", koyu=True),
        kpi("Adet başına maliyet", f"{mal['birim_tl']:.2f} ₺", "personel / sevk edilen adet"),
        kpi("Fazla mesai riski", ml.tl(mal["fazla_tl"]), f"{mal['fazla_saat']:,.0f} saat kapasite üstü".replace(",", "."), "kt" if mal["fazla_tl"] > 0 else "ok"),
        kpi("Yıllık iyileştirme fırsatı", ml.tl(toplam_firsat), f"%{toplam_firsat / yil_tl_personel * 100:.0f} personel maliyeti", "ok"),
    ]) + "</div>", unsafe_allow_html=True)
    m1, m2 = st.columns([1.4, 1])
    with m1, kart("Kaizen kalemleri · yıllık TL karşılığı"):
        kd = pd.DataFrame(kal, columns=["Kalem", "Yıllık ₺", "Açıklama"]).sort_values("Yıllık ₺")
        f = px.bar(kd, x="Yıllık ₺", y="Kalem", orientation="h", text=kd["Yıllık ₺"].map(ml.tl))
        f.update_traces(marker_color="#b5d11d", textposition="outside", cliponaxis=False)
        f.update_layout(height=270, yaxis_title=None, xaxis_title=None, margin=dict(l=8, r=90, t=10, b=8))
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
        st.markdown(tablo(["Kalem", "Açıklama"], [(f"<b>{esc(k[0])}</b>", esc(k[2])) for k in kal]), unsafe_allow_html=True)
    with m2, kart("Birim maliyet varsayımları (örnek)"):
        st.caption("Aşağıdaki değerler ÖRNEKTİR; kendi değerlerinizi girin, tüm TL hesapları güncellenir.")
        with st.form("maliyet_form"):
            v1 = st.number_input("Tam yüklü adam-gün maliyeti (₺)", 500.0, 20000.0, float(mv["adam_gun_tl"]), 100.0)
            v2 = st.number_input("Fazla mesai çarpanı", 1.0, 3.0, float(mv["fazla_mesai_carpan"]), 0.1)
            v3 = st.number_input("Geciken sipariş başına maliyet (₺)", 0.0, 50000.0, float(mv["gecikme_ceza_tl"]), 100.0)
            v4 = st.number_input("Bekleyen palet maliyeti (₺/saat)", 0.0, 100.0, float(mv["palet_bekleme_tl_saat"]), 0.5)
            v5 = st.number_input("Forklift enerji (kWh/km)", 0.1, 5.0, float(mv["kwh_km"]), 0.1)
            v6 = st.number_input("Emisyon faktörü (kg CO₂/kWh)", 0.05, 1.5, float(mv["co2_kg_kwh"]), 0.01)
            if st.form_submit_button("💾 Kaydet", disabled=not YONETICI_OK):
                yeni = dp.yukle()
                yeni["maliyet"] = {"adam_gun_tl": v1, "fazla_mesai_carpan": v2, "gecikme_ceza_tl": v3, "palet_bekleme_tl_saat": v4,
                                   "kwh_km": v5, "co2_kg_kwh": v6}
                dp.kaydet(yeni)
                st.rerun()
    krb = ml.karbon(yer_m_gun, profil)
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Yerleşimden azalan mesafe", f"{krb['km_yil']:,.0f} km/yıl".replace(",", "."), "ABC yerleşimi vs bölge kodu sırası", "ok"),
        kpi("Enerji tasarrufu", f"{krb['kwh_yil']:,.0f} kWh".replace(",", "."), "yıllık", "ok"),
        kpi("CO₂ azalışı", f"{krb['co2_kg_yil'] / 1000:.1f} ton", "yıllık", "ok", koyu=True),
        kpi("Gecikme varsayımı", f"~{gec_yil:,.0f} sipariş/yıl".replace(",", "."), "toplama SLA aşımı × %10 ceza payı", "nt"),
    ]) + "</div>", unsafe_allow_html=True)

elif sayfa == "Asistan":
    ust_baslik("Operasyon Asistanı")
    anah = asistan.anahtar()
    st.caption(("🟢 Claude API bağlı: sorular ve özet veriler Anthropic API'ye gönderilir. " if anah else
                "🟡 Yerel asistan (Claude API anahtarı tanımlı değil; hiçbir veri dışarı çıkmaz). ")
               + "Anahtar için sunucuda ANTHROPIC_API_KEY ortam değişkeni ya da secret tanımlayın.")
    sip_ast = sp.temizle(pd.read_csv(Path(__file__).parent / "siparisler.csv", dtype={"siparis_no": str}, parse_dates=["termin"])) \
        if (Path(__file__).parent / "siparisler.csv").exists() else sp.temizle(vk.siparisler(SIMDI, ham_tum, kaynak_ayar))
    n_pick_a = sum(k["kisi"] for k in profil["kadro"] if "Toplay" in k["rol"]) or 24
    uph_a = float(hedef_uph or gp["uph"].median())
    plan_a, _, _ = sp.planla(sip_ast, SIMDI.normalize(), n_pick_a, uph_a)
    kisi_a = gp.groupby("personel").agg(gun=("tarih", "nunique"), adet=("adet", "sum"))
    kisi_a["uph"] = kisi_a["adet"] / (kisi_a["gun"] * h.VARDIYA_SAATI)
    kisi_a = kisi_a[kisi_a["gun"] >= 3].sort_values("uph")
    tah_a, _, _ = an.tahmin(gun_hist_tam)
    sr_a = an.sureler(surec_tab, inbound, profil["hedefler"])
    ctx = {"donem": f"{BAS:%d.%m.%Y}–{BIT:%d.%m.%Y}", "adet": float(toplam_adet), "uph": float(ort_uph), "personel": float(gun["personel"].mean()),
           "kadro": int(len(kadro_tab)), "toplayici": int(n_pick_a), "forklift": filo_n, "doluluk": float(stok["dolu"].sum() / stok["pozisyon"].sum() * 100),
           "saatlik": an.saatlik_yuk(veri), "bolge": kroki, "tahmin": tah_a, "sureler": sr_a, "plan": plan_a,
           "uyarilar": [m for _, m in uyarilar()], "en_iyi": (kisi_a.index[-1], float(kisi_a["uph"].iloc[-1])),
           "en_kotu": (kisi_a.index[0], float(kisi_a["uph"].iloc[0])), "skt_riskli": int(((veri["skt"] - veri["tarih"]).dt.days < an.SKT_RISK_GUN).sum()),
           "pil_dusuk": [r.id for r in flk[flk["pil"] < 25].itertuples()]}
    st.session_state.setdefault("sohbet", [("assistant", "Merhaba! Ben OPLOG asistanıyım. Operasyon verilerinizle ilgili soru sorabilirsiniz; örneğin *özet*, *geciken siparişler* ya da *yarın 80 bin adet gelirse kaç kişi lazım?*")])
    ornek_sorular = {"📋 Özet": "Durum özeti", "⏰ Geciken siparişler": "Geciken siparişler hangileri?", "🕒 En yoğun saat": "En yoğun saat hangisi?",
                     "👷 80 bin adet → kaç kişi?": "80 bin adet gelirse kaç kişi lazım?", "🔎 Darboğaz": "Süreçte darboğaz var mı?", "🔮 Yarınki tahmin": "Yarınki tahmin nedir?"}
    qc = st.columns(len(ornek_sorular))
    secilen = None
    for c_, (etk_, s_) in zip(qc, ornek_sorular.items()):
        if c_.button(etk_, key=f"q_{s_}", width="stretch"):
            secilen = s_
    for rol, metin in st.session_state["sohbet"]:
        with st.chat_message(rol):
            st.markdown(metin)
    soru = st.chat_input("Sorunuzu yazın…") or secilen
    if soru:
        st.session_state["sohbet"].append(("user", soru))
        with st.chat_message("user"):
            st.markdown(soru)
        with st.chat_message("assistant"):
            with st.spinner("Düşünüyor…"):
                cevap, kaynak = asistan.yanit(soru, ctx, [(r, m) for r, m in st.session_state["sohbet"][1:-1]])
            st.markdown(cevap)
            st.caption("Kaynak: " + ("Claude" if kaynak == "claude" else "yerel asistan"))
        st.session_state["sohbet"].append(("assistant", cevap))
    if len(st.session_state["sohbet"]) > 1:
        st.button("🗑 Sohbeti temizle", on_click=lambda: st.session_state.pop("sohbet", None))

elif sayfa == "Saha":
    ust_baslik("Saha · Mobil Toplama")
    st.markdown("<style>.stButton>button{min-height:52px;font-size:1.05rem}</style>", unsafe_allow_html=True)
    pickers = sorted(kadro_tab[kadro_tab["rol"].str.contains("Toplay")]["ad"].tolist())
    aktif_bugun = ham_tum[ham_tum["tarih"] == ham_tum["tarih"].max()]["personel"].value_counts()
    varsayilan_kisi = aktif_bugun.index[0] if len(aktif_bugun) else pickers[0]
    kisi_s = st.selectbox("Toplayıcı", pickers, index=pickers.index(varsayilan_kisi) if varsayilan_kisi in pickers else 0)
    gor, rota = saha.gorevler(ham_tum, kisi_s, kroki, profil)
    anahtar_t = f"saha_{kisi_s}"
    yapilan = st.session_state.setdefault(anahtar_t, set())
    if gor.empty:
        st.info("Bu kişi için görev bulunamadı.")
    else:
        toplam_m, toplam_dk = float(gor["mesafe_m"].sum()), float(gor["eta_dk"].sum())
        st.progress(len(yapilan) / len(gor), text=f"{len(yapilan)}/{len(gor)} görev tamam · toplam {toplam_m:.0f} m · tahmini {toplam_dk:.0f} dk")
        with kart("Rota"):
            g_ = tw.geometri(profil)
            fm = go.Figure()
            fm.add_shape(type="rect", x0=0, y0=0, x1=g_["en"], y1=g_["boy"], line=dict(color="#1c1d20", width=2))
            for r_ in kroki.itertuples():
                fm.add_shape(type="rect", x0=r_.x, y0=r_.y, x1=r_.x + r_.w, y1=r_.y + r_.d, line=dict(color="#c6c9d0"), fillcolor="#f1f2f5")
            xs, ys = [p_[0] for p_ in rota], [p_[1] for p_ in rota]
            fm.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#8fb413", width=3), hoverinfo="skip"))
            dur = gor.drop_duplicates("sira")
            xy_ = {r_.bolge: tw._toplama_noktasi(r_, g_) for r_ in kroki.itertuples()}
            fm.add_trace(go.Scatter(x=[xy_[b][0] for b in dur["bolge"]], y=[xy_[b][1] for b in dur["bolge"]], mode="markers+text",
                                    text=[str(s) for s in dur["sira"]], textfont=dict(color="white", size=11),
                                    marker=dict(size=22, color=["#16a34a" if s in yapilan else "#1c1d20" for s in dur["sira"]]), hoverinfo="skip"))
            fm.update_xaxes(visible=False, scaleanchor="y", range=[-4, g_["en"] + 4])
            fm.update_yaxes(visible=False, range=[-4, g_["boy"] + 4])
            fm.update_layout(height=330, showlegend=False, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="white")
            st.plotly_chart(fm, width="stretch", config={"displayModeBar": False})
        for i, r_ in enumerate(gor.itertuples()):
            tamam = i in yapilan
            with st.container(border=True):
                kc1, kc2 = st.columns([3, 1])
                kc1.markdown(f"**{r_.sira}. Bölge {esc(str(r_.bolge))}** · {r_.adet} adet<br><span style='color:#6b7076;font-size:.85rem'>{esc(r_.urun)} · {esc(r_.sku)}"
                             f"<br>{r_.mesafe_m:.0f} m · ~{r_.eta_dk:.1f} dk</span>", unsafe_allow_html=True)
                if tamam:
                    kc2.markdown('<div style="text-align:center;font-size:2rem">✅</div>', unsafe_allow_html=True)
                else:
                    kc2.button("✔ Tamam", key=f"tm_{kisi_s}_{i}", on_click=lambda i=i: yapilan.add(i), width="stretch")
        if len(yapilan) == len(gor):
            st.success("🎉 Tüm görevler tamamlandı. Sevkiyat kapısına dönün.")
        st.button("↺ Listeyi sıfırla", on_click=lambda: yapilan.clear())

elif sayfa == "Takip":
    ust_baslik("Sipariş Takip")
    st.caption("Müşteriye verilebilecek “siparişim nerede?” görünümü. Doğrudan link: ?sayfa=Takip&no=<teslimat no>")
    son_sip = surec_tum.sort_values("sevk").tail(40)["teslimat"].tolist()
    on_deger = st.query_params.get("no") or (son_sip[-1] if son_sip else "")
    no = st.text_input("Teslimat / sipariş numarası", on_deger, placeholder="örn. " + (son_sip[-1] if son_sip else "8000012345")).strip()
    no_n = no.split("_")[0]
    bul = surec_tum[surec_tum["teslimat"] == no_n]
    if not no:
        st.info("Bir teslimat numarası girin.")
    elif bul.empty:
        st.warning("Bu numara bulunamadı. Son siparişlerden biri: " + ", ".join(son_sip[-3:]))
    else:
        s = bul.iloc[0]
        satirlar_t = ham_tum[ham_tum["teslimat"] == no_n]
        adimlar = [("Sipariş alındı", s["siparis_alindi"]), ("Toplama tamam", s["toplama_bitti"]), ("Paketlendi", s["paket_hazir"]),
                   ("Araca yükleme", s["yukleme_basladi"]), ("Sevk edildi", s["sevk"])]
        simdi_ = SIMDI
        gecen = [t <= simdi_ for _, t in adimlar]
        durum = "Sevk edildi" if gecen[-1] else adimlar[max(sum(gecen) - 1, 0)][0] if sum(gecen) else "Sipariş alındı"
        st.markdown('<div class="kpi-grid">' + "".join([
            kpi("Durum", durum, f"{no_n}", "ok" if gecen[-1] else "nt", koyu=True),
            kpi("Müşteri", esc(str(satirlar_t["teslim_alan"].iloc[0])[:30]) if len(satirlar_t) else "—", esc(str(satirlar_t["il"].iloc[0])) if len(satirlar_t) else ""),
            kpi("Kalem / adet", f"{len(satirlar_t)} / {int(satirlar_t['adet'].sum())}" if len(satirlar_t) else "—", "satır / adet"),
            kpi("Toplam süre", f"{(s['sevk'] - s['siparis_alindi']).total_seconds() / 3600:.1f} sa", "sipariş → sevk"),
        ]) + "</div>", unsafe_allow_html=True)
        with kart("Sipariş yolculuğu"):
            satir_t = []
            for i, (ad_, t_) in enumerate(adimlar):
                sure_t = f"+{(t_ - adimlar[i - 1][1]).total_seconds() / 3600:.1f} sa" if i else "—"
                satir_t.append((("✅ " if gecen[i] else "⏳ ") + f"<b>{ad_}</b>", f"{t_:%d.%m.%Y %H:%M}", sure_t,
                                etiket("Tamam", "g") if gecen[i] else etiket("Bekliyor", "n")))
            st.markdown(tablo(["Adım", "Zaman", "Önceki adımdan", "Durum"], satir_t), unsafe_allow_html=True)
        if len(satirlar_t):
            with kart("Kalemler"):
                st.dataframe(satirlar_t[["sku", "urun", "adet", "parti"]].rename(columns={"sku": "SKU", "urun": "Ürün", "adet": "Adet", "parti": "Parti"}),
                             width="stretch", hide_index=True, height=220)

elif sayfa == "SKT & FEFO":
    ust_baslik("SKT & FEFO")
    st.caption("Son kullanma tarihi riski ve FEFO (ilk biten ilk çıkar) uyumu. FEFO ihlali: aynı SKU'da, aynı gün, daha geç SKT'li parti daha erken SKT'li partiden önce sevk edildi.")
    sk = skt_onb(VERI_IMZA)
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("SKT riskli satır", sayi(sk["riskli_satir"]), f"<{an.SKT_RISK_GUN} gün kala sevk", "kt" if sk["riskli_satir"] else "ok", koyu=True),
        kpi("Riskli parti", sayi(sk["riskli_parti"]), f"{sayi(sk['riskli_adet'])} adet"),
        kpi("FEFO uyumu", f"%{sk['fefo_uyum'] * 100:.1f}", f"{sayi(sk['ihlal'])} ihlal / {sayi(sk['toplam'])} satır", "ok" if sk["fefo_uyum"] > 0.95 else "kt", halka=sk["fefo_uyum"] * 100),
        kpi("Önerilen aksiyon", "Öncelikli sevk", "riskli partileri öne al / kampanya", "nt"),
    ]) + "</div>", unsafe_allow_html=True)
    s1, s2 = st.columns([1, 1.4])
    with s1, kart("Sevk anında kalan SKT dağılımı"):
        f = px.bar(x=sk["dagilim"].index.astype(str), y=sk["dagilim"].values, labels={"x": "", "y": "satır"})
        f.update_traces(marker_color=["#ef4444", "#ef4444", "#f59e0b", "#f59e0b", "#b5d11d", "#1c1d20"])
        f.update_layout(height=290)
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with s2, kart("En riskli partiler (sevk anında en az kalan gün)"):
        st.markdown(tablo(["Parti", "Ürün", "SKU", "Satır", "Adet", "Kalan gün"],
                          [(f"<b>{esc(str(r.parti))}</b>", esc(str(r.urun)), esc(str(r.sku)), sayi(r.satir), sayi(r.adet),
                            etiket(f"{r.kalan_gun} gün", "r" if r.kalan_gun < 45 else "o")) for r in sk["riskli"].head(8).itertuples()]), unsafe_allow_html=True)
    st.markdown('<div class="uy w">💡 Riskli partilerin toplama listesinde en üstte olması (FEFO sırası) ve 45 günün altına inen partiler için kampanya/iskonto planı önerilir.</div>', unsafe_allow_html=True)

elif sayfa == "Depolar":
    ust_baslik("Depolar · Karşılaştırma")
    st.caption("Ana depo ekrandaki verilerdir; diğer depolar SİMÜLASYONDUR (ana depodan türetilir). Gerçek çok depolu veri bağlandığında bu tablo gerçek değerlerle dolar.")
    sr_d = an.sureler(surec_tab, inbound, profil["hedefler"])
    ana = {"gunluk_cikis": float(gun["adet"].mean()), "uph": float(ort_uph), "doluluk": float(stok["dolu"].sum() / stok["pozisyon"].sum() * 100),
           "putaway_saat": float(sr_d.loc[sr_d["adim"] == "Putaway", "gerceklesen_saat"].iloc[0]),
           "sevk_saat": float(sr_d.loc[sr_d["adim"] == "Shipping", "gerceklesen_saat"].iloc[0]), "alan": dp.toplam(profil),
           "kadro": int(sum(k["kisi"] for k in profil["kadro"]))}
    dd = depolar.kiyas(ana)
    en_iyi = dd.sort_values("skor", ascending=False).iloc[0]
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Depo sayısı", len(dd), f"{sayi(dd['alan_m2'].sum())} m² toplam", koyu=True),
        kpi("Toplam günlük çıkış", sayi(dd["gunluk_cikis"].sum()), "adet / gün"),
        kpi("Ağırlıklı UPH", sayi((dd["uph"] * dd["kadro"]).sum() / dd["kadro"].sum()), "adet / saat"),
        kpi("En yüksek skor", esc(str(en_iyi["depo"])), f"{en_iyi['skor']:.0f} puan", "ok"),
    ]) + "</div>", unsafe_allow_html=True)
    d1, d2 = st.columns([1.2, 1])
    with d1, kart("Konum ve performans (balon: alan, renk: skor)"):
        TR = [(26.0, 40.0), (26.3, 41.7), (28.0, 41.9), (29.0, 41.2), (31.0, 41.1), (33.5, 42.0), (36.0, 41.7), (38.3, 40.9), (40.5, 41.0), (41.5, 41.5),
              (43.5, 41.1), (44.8, 39.7), (44.4, 38.3), (44.0, 37.2), (42.4, 37.1), (40.0, 36.9), (38.0, 36.8), (36.7, 36.2), (36.2, 35.9), (35.9, 36.7),
              (34.5, 36.8), (33.0, 36.1), (32.0, 36.2), (30.5, 36.3), (29.2, 36.3), (28.0, 36.7), (27.4, 37.0), (26.3, 38.2), (26.2, 39.3), (26.0, 40.0)]
        f = go.Figure(go.Scatter(x=[p_[0] for p_ in TR], y=[p_[1] for p_ in TR], mode="lines", fill="toself", fillcolor="#eef0ea",
                                 line=dict(color="#c6c9d0", width=1.5), hoverinfo="skip"))
        f.add_trace(go.Scatter(x=dd["lon"], y=dd["lat"], mode="markers+text", text=dd["depo"].str.replace(" (Ana)", " ★", regex=False), textposition="top center",
                               marker=dict(size=(dd["alan_m2"] / dd["alan_m2"].max() * 46 + 14), color=dd["skor"], colorscale="YlGn", cmin=80, cmax=100,
                                           line=dict(color="#1c1d20", width=1.5)),
                               customdata=dd[["alan_m2", "uph", "doluluk", "skor"]],
                               hovertemplate="<b>%{text}</b><br>%{customdata[0]:,.0f} m²<br>UPH %{customdata[1]:.0f}<br>Doluluk %{customdata[2]:.0f}%<br>Skor %{customdata[3]:.0f}<extra></extra>"))
        f.update_xaxes(visible=False, range=[24.5, 46.5])
        f.update_yaxes(visible=False, range=[35, 43.2], scaleanchor="x", scaleratio=1.3)
        f.update_layout(height=340, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, plot_bgcolor="white")
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with d2, kart("Depo sıralaması"):
        st.markdown(tablo(["Depo", "m²", "Kadro", "UPH", "Doluluk", "Putaway", "Skor"],
                          [(f"<b>{esc(str(r.depo))}</b>" + (" ★" if r.ana else ""), sayi(r.alan_m2), r.kadro, f"{r.uph:.0f}", f"%{r.doluluk:.0f}",
                            f"{r.putaway_saat:.1f} sa", etiket(f"{r.skor:.0f}", "g" if r.skor >= 90 else "o"))
                           for r in dd.sort_values("skor", ascending=False).itertuples()]), unsafe_allow_html=True)
    with kart("UPH ve dock-to-stock karşılaştırması"):
        f = go.Figure()
        f.add_bar(x=dd["depo"], y=dd["uph"], name="UPH (adet/saat)", marker_color="#b5d11d")
        f.add_trace(go.Scatter(x=dd["depo"], y=dd["putaway_saat"], name="Putaway (saat)", yaxis="y2", mode="lines+markers", line=dict(color="#1c1d20", width=3)))
        f.update_layout(height=250, yaxis2=dict(overlaying="y", side="right", showgrid=False), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})

elif sayfa == "Rapor":
    ust_baslik("Yönetici Raporu")
    st.caption("Ekrandaki dönem ve filtrelerle aynı verilerden tek tıkla rapor üretilir. HTML raporu tarayıcıdan PDF olarak yazdırılabilir (Ctrl+P).")
    sr_r = an.sureler(surec_tab, inbound, profil["hedefler"])
    kisi_r = gp.groupby("personel", as_index=False).agg(gun=("tarih", "nunique"), adet=("adet", "sum"))
    kisi_r["uph"] = (kisi_r["adet"] / (kisi_r["gun"] * h.VARDIYA_SAATI)).round(0)
    sk_r = skt_onb(VERI_IMZA)
    kal_r = []
    mal_r = ml.donem(gun_tam, profil)
    kpiler = [("Toplam çıkış (adet)", sayi(toplam_adet)), ("Ortalama UPH", sayi(ort_uph)), ("Toplam adam/gün", adam_gun),
              ("Personel maliyeti", ml.tl(mal_r["personel_tl"])), ("Adet başına maliyet", f"{mal_r['birim_tl']:.2f} ₺"),
              ("FEFO uyumu", f"%{sk_r['fefo_uyum'] * 100:.1f}"), ("Palet doluluğu", f"%{stok['dolu'].sum() / stok['pozisyon'].sum() * 100:.0f}")]
    gun_tbl = gun[["tarih", "adet", "personel", "uph"]].rename(columns={"tarih": "Tarih", "adet": "Adet", "personel": "Personel", "uph": "UPH"})
    gun_tbl[["Adet", "Personel", "UPH"]] = gun_tbl[["Adet", "Personel", "UPH"]].round(0)
    bolumler = {"Süreç süreleri": sr_r.rename(columns={"adim": "Adım", "tanim": "Tanım", "hedef_saat": "Hedef (sa)", "gerceklesen_saat": "Gerçekleşen (sa)", "durum": "Durum"})[["Adım", "Tanım", "Hedef (sa)", "Gerçekleşen (sa)", "Durum"]],
                "Toplayıcı performansı": kisi_r.sort_values("uph", ascending=False).rename(columns={"personel": "Personel", "gun": "Gün", "adet": "Adet", "uph": "UPH"}),
                "SKT riskli partiler": sk_r["riskli"].head(10)[["parti", "urun", "adet", "kalan_gun"]].rename(columns={"parti": "Parti", "urun": "Ürün", "adet": "Adet", "kalan_gun": "Kalan gün"}),
                "Günlük özet": gun_tbl.tail(31)}
    f1 = px.bar(gun, x="tarih", y="adet"); f1.update_traces(marker_color="#b5d11d"); f1.update_layout(height=300)
    f2 = px.bar(an.saatlik_yuk(veri), x="saat", y="satir_gun_ort"); f2.update_traces(marker_color="#1c1d20"); f2.update_layout(height=260)
    notlar = [m.replace("**", "") for _, m, _ in an.kaizen(veri, gp, gun_tam, sr_r, None)[:4]]
    donem_txt = f"{profil['ad']} · {BAS:%d.%m.%Y} – {BIT:%d.%m.%Y} · hazırlanma: {SIMDI:%d.%m.%Y %H:%M}"
    html_r = rapor.html_rapor("OPLOG Operasyon Raporu", donem_txt, kpiler, bolumler, notlar, [("Günlük çıkış (adet)", f1), ("Saatlik yük (günlük ortalama satır)", f2)])
    xls = rapor.excel({"Özet": pd.DataFrame(kpiler, columns=["Gösterge", "Değer"]), "Günlük": gun_tbl, **{k[:28]: v for k, v in bolumler.items() if k != "Günlük özet"},
                       "Siparişler": sp.temizle(vk.siparisler(SIMDI, ham_tum, kaynak_ayar))})
    st.markdown('<div class="kpi-grid">' + "".join([kpi(a_, b_) for a_, b_ in kpiler[:4]]) + "</div>", unsafe_allow_html=True)
    r1, r2, _ = st.columns([1, 1, 2])
    r1.download_button("📄 HTML raporu (PDF'e yazdır)", html_r.encode("utf-8"), f"oplog_rapor_{BIT:%Y%m%d}.html", "text/html", width="stretch")
    r2.download_button("📊 Excel çalışma kitabı", xls, f"oplog_rapor_{BIT:%Y%m%d}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    with kart("Rapor önizleme"):
        st.iframe(html_r, height=560)
    st.caption("E-posta ile otomatik gönderim için kurumsal SMTP/Graph bilgileri gerekir; bunlar sağlandığında bu rapor zamanlanmış e-postaya bağlanabilir.")

elif sayfa == "Günlük":
    ust_baslik("Günlük Analiz")
    _per = st.radio("Toplulaştırma", ["Gün", "Hafta", "Ay"], horizontal=True, key="gun_per")
    if _per == "Gün":
        _gp, _ad = gun[["tarih", "adet", "personel", "adam_saat"]].copy(), "Günlük"
    else:
        _gp = (gun.set_index("tarih").resample("W-MON" if _per == "Hafta" else "MS")
               .agg(adet=("adet", "sum"), personel=("personel", "sum"), adam_saat=("adam_saat", "sum")).reset_index())
        _ad = "Haftalık" if _per == "Hafta" else "Aylık"
    _gp["uph"] = _gp["adet"] / _gp["adam_saat"].where(_gp["adam_saat"] > 0, 1)
    _figler = [px.bar(_gp, x="tarih", y="adet", title=f"{_ad} çıkış (adet)"),
               px.line(_gp, x="tarih", y="uph", markers=True, title=f"{_ad} UPH (adet/saat)"),
               px.bar(_gp, x="tarih", y="personel", title=f"{_ad} adam/gün"),
               px.bar(an.saatlik_yuk(veri), x="saat", y="satir_gun_ort", title="Saatlik yük (günlük ort. satır)")]
    for _f in _figler:
        _f.update_layout(height=250)
        _f.update_xaxes(title=None)
        _f.update_yaxes(title=None)
        if _f.data[0].type == "bar":
            _f.update_traces(marker_color="#b5d11d")
    _kol = st.columns(2)
    for i, _f in enumerate(_figler):
        with _kol[i % 2], kart():
            st.plotly_chart(_f, width="stretch", config={"displayModeBar": False})

elif sayfa == "Personel":
    ust_baslik("Personel")
    kisi = gp.groupby("personel", as_index=False).agg(
        gun=("tarih", "nunique"), adet=("adet", "sum"), satir=("satir", "sum"))
    kisi["uph"] = kisi["adet"] / (kisi["gun"] * h.VARDIYA_SAATI)
    kisi = kisi.sort_values("adet", ascending=False)
    ko = an.kadro_ozet(kadro_tab, ham, inbound, profil)
    gund, aks = (kadro_tab["vardiya"] == profil["vardiyalar"][0]["ad"]).sum(), (kadro_tab["vardiya"] != profil["vardiyalar"][0]["ad"]).sum()
    bugun_pick = ham_tum[ham_tum["tarih"] == BUGUN]["personel"].nunique()
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Toplam kadro", len(kadro_tab), f"{kadro_tab['rol'].nunique()} rol", koyu=True),
        kpi("Vardiya dağılımı", f"{gund} / {aks}", f"{profil['vardiyalar'][0]['ad']} / {profil['vardiyalar'][-1]['ad']}"),
        kpi("Ort. devam oranı", f"%{ko['devam_%'].mean():.1f}", "dönem", "ok", halka=float(ko["devam_%"].mean())),
        kpi("Bugün aktif toplayıcı", bugun_pick, f"{(kadro_tab['rol'].str.contains('Toplay')).sum()} kişilik toplayıcı kadrosundan"),
    ]) + "</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.6])
    with c1, kart("Kadro · rol ve vardiya"):
        kd = kadro_tab.groupby(["rol", "vardiya"]).size().reset_index(name="kisi")
        f = px.bar(kd, x="kisi", y="rol", color="vardiya", orientation="h",
                   color_discrete_sequence=["#1c1d20", "#b5d11d"])
        f.update_layout(height=280, legend_title=None, yaxis_title=None, xaxis_title="kişi", legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with c2, kart("Toplayıcı performansı · UPH (adet/saat)"):
        f = px.bar(kisi, x="personel", y="uph")
        f.update_layout(height=280, xaxis_title=None)
        f.update_traces(marker_color="#b5d11d")
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with kart("Tüm kadro · dönem iş hacmi"):
        tbl = ko.rename(columns={"ad": "Ad", "rol": "Rol", "vardiya": "Vardiya", "devam_%": "Devam %",
                                 "aylik_hacim": "Dönem iş hacmi", "birim": "Birim"})
        st.dataframe(tbl, width="stretch", hide_index=True)

elif sayfa == "SKU":
    ust_baslik("SKU")
    sku = h.sku_uph(veri)
    st.caption("Lokasyon bilgisi olmadığı için 1 SKU = 1 lokasyon. Personelin 9 saati, o gün işlediği "
               "satır sayısına göre SKU'lara paylaştırıldı (tahmini değerdir).")
    sc1, sc2 = st.columns([1.2, 1])
    with sc1, kart():
        f = px.bar(sku.head(15), x="adet", y="sku", orientation="h", hover_data=["urun"], title="En çok çıkan 15 SKU")
        f.update_yaxes(autorange="reversed", title=None, type="category")
        f.update_xaxes(title=None)
        f.update_traces(marker_color="#b5d11d")
        f.update_layout(height=400)
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with sc2, kart():
        st.dataframe(sku.round(1), width="stretch", hide_index=True, height=400)

elif sayfa == "Kanal":
    ust_baslik("Kanal")
    kn = veri.groupby("kanal", as_index=False)["adet"].sum()
    kc1, kc2 = st.columns([1, 1])
    with kc1, kart():
        f = px.pie(kn, names="kanal", values="adet", hole=0.55, title="Kanal dağılımı",
                   color_discrete_sequence=["#1c1d20", "#b5d11d", "#8d9097", "#f59e0b", "#3b82f6"])
        f.update_layout(height=300, legend=dict(orientation="h", y=-0.05))
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with kc2, kart("Kanal özeti"):
        ko_ = veri.groupby("kanal").agg(satir=("adet", "size"), adet=("adet", "sum"), sevkiyat=("sevkiyat", "nunique")).reset_index()
        ko_["pay"] = ko_["adet"] / ko_["adet"].sum() * 100
        st.markdown(tablo(["Kanal", "Satır", "Sevkiyat", "Adet", "Pay"],
                          [(f"<b>{esc(str(r.kanal))}</b>", sayi(r.satir), sayi(r.sevkiyat), sayi(r.adet), f"%{r.pay:.0f}")
                           for r in ko_.sort_values("adet", ascending=False).itertuples()]), unsafe_allow_html=True)

elif sayfa == "Tahmin":
    ust_baslik("Tahmin & Rota")
    tah, mape, kullanilan_uph = an.tahmin(gun_hist_tam, hedef_uph=hedef_uph or None)
    st.caption(f"Önümüzdeki 7 gün: haftanın gününe göre ortalama × son hafta trendi. "
               f"Personel ihtiyacı {sayi(kullanilan_uph)} adet/saat UPH ile hesaplandı.")
    if mape is not None:
        st.info(f"Geriye dönük test hatası (WAPE): %{mape:.0f}. Veri tek ay ve ay sonu dalgalı olduğu için "
                "tahmin yön göstericidir; daha fazla ay yüklendikçe iyileşir.")
    GUNLER_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    tah_g = tah.assign(Gün=tah["tarih"].dt.dayofweek.map(lambda i: GUNLER_TR[i]), Tarih=tah["tarih"].dt.strftime("%d.%m.%Y"))
    tah_g = tah_g.rename(columns={"tahmin_adet": "Tahmini adet", "gereken_personel": "Gereken personel"})
    tc1, tc2 = st.columns([1.3, 1])
    with tc1, kart():
        f = px.bar(tah_g, x="Tarih", y="Tahmini adet", text="Gereken personel",
                   title="Tahmini çıkış (adet) · çubuk üstü: gereken personel")
        f.update_xaxes(title=None)
        f.update_yaxes(title=None)
        f.update_traces(marker_color="#b5d11d", textfont_color="#1c1d20", textposition="outside")
        f.update_layout(height=290)
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    with tc2, kart():
        st.dataframe(tah_g[["Tarih", "Gün", "Tahmini adet", "Gereken personel"]], width="stretch", hide_index=True, height=290)
    rt = rota_ozeti(VERI_IMZA, profil)
    if len(rt):
        kazan = 1 - rt["optimize_m"].sum() / rt["sirasiz_m"].sum()
        st.markdown('<div class="kpi-grid">' + kpi("Rota: örnek sevkiyat", len(rt), "çok bölgeli") +
                    kpi("Yürüme tasarrufu", f"%{kazan * 100:.0f}", "en yakın komşu rotası", "ok", koyu=True) +
                    "</div>", unsafe_allow_html=True)
        st.caption("Çok bölgeli sevkiyatlarda bölgeleri sırasız gezmek yerine en yakın komşu rotası kullanıldığında.")

elif sayfa == "Süreç":
    ust_baslik("Süreç Denetimi")
    st.caption("Mal kabul (Inbound) → yerleştirme (Putaway) → toplama (Picking) → paketleme (Packing) → sevkiyat (Shipping): "
               "beş adımın tamamı kayıtlardan hesaplanır. Hedefler Depo Profili'ndedir.")
    sr = an.sureler(surec_tab, inbound, profil["hedefler"])
    kt = {"Hedefte": "g", "Dikkat": "o", "Gecikme": "r"}
    with kart("Süreç süreleri · Inbound → Shipping"):
        st.markdown(tablo(["Adım", "Tanım", "Hedef (sa)", "Gerçekleşen (sa)", "Kayıt", "Durum"],
                          [(f"<b>{r.adim}</b>", r.tanim, f"{r.hedef_saat:.1f}", f"{r.gerceklesen_saat:.1f}", sayi(r.kayit),
                            etiket(r.durum, kt[r.durum])) for r in sr.itertuples()]), unsafe_allow_html=True)
    gun_n = max(inbound["tarih"].nunique(), 1)
    acik_saat = profil["simulasyon"]["kapi_acik_saat"] * max(profil["kapilar"]["mal_kabul"], 1) * gun_n
    kapi_dol = float((inbound["bosaltma_bitis"] - inbound["bosaltma_baslangic"]).dt.total_seconds().sum() / 3600 / acik_saat * 100)
    st.markdown('<div class="kpi-grid">' + "".join([
        kpi("Günlük ort. palet girişi", sayi(inbound["palet"].sum() / gun_n), "mal kabul"),
        kpi("Günlük ort. kamyon", f"{len(inbound) / gun_n:.1f}", f"{profil['kapilar']['mal_kabul']} giriş kapısı"),
        kpi("Giriş kapısı doluluğu", f"%{kapi_dol:.0f}", "boşaltma süresi / kapı saati", halka=min(kapi_dol, 100)),
        kpi("Dock-to-stock", f"{sr.loc[sr['adim'] == 'Putaway', 'gerceklesen_saat'].iloc[0]:.1f} sa",
            f"hedef {profil['hedefler']['dock_to_stock_saat']:.1f} sa", koyu=True),
    ]) + "</div>", unsafe_allow_html=True)
    ib_g = inbound.groupby("tarih", as_index=False)["palet"].sum()
    with kart("Günlük mal kabul · palet"):
        f = go.Figure(go.Bar(x=ib_g["tarih"], y=ib_g["palet"], marker_color="#b5d11d",
                             hovertemplate="%{x|%d %b}<br>%{y:.0f} palet<extra></extra>"))
        f.update_layout(height=210, showlegend=False)
        st.plotly_chart(f, width="stretch", config={"displayModeBar": False})
    den = an.surec_denetimi(ham, inbound, surec_tab, profil["hedefler"])
    dk = {"Normal": "g", "İzle": "o", "Aksiyon": "r"}
    with kart("Adım adım denetim"):
        st.markdown(tablo(["Adım", "Kontrol", "Bulgu", "Oran", "Durum"],
                          [(f"<b>{r.adim}</b>", r.kontrol, sayi(r.bulgu), f"%{r._4:.1f}", etiket(r.durum, dk[r.durum]))
                           for r in den.itertuples()]), unsafe_allow_html=True)

else:  # Kaizen
    ust_baslik("Kaizen Önerileri")
    _sr = an.sureler(surec_tab, inbound, profil["hedefler"])
    _gn = max(inbound["tarih"].nunique(), 1)
    _kd = float((inbound["bosaltma_bitis"] - inbound["bosaltma_baslangic"]).dt.total_seconds().sum() / 3600
                / (profil["simulasyon"]["kapi_acik_saat"] * max(profil["kapilar"]["mal_kabul"], 1) * _gn) * 100)
    oneriler = an.kaizen(veri, gp, gun_tam, _sr, _kd)
    if not oneriler:
        st.success("Belirgin bir iyileştirme fırsatı bulunmadı.")
    renk = {"Yüksek": "r", "Orta": "o", "Düşük": "g"}
    for baslik, detay, etki in oneriler:
        with kart():
            st.markdown(f"**{baslik}** &nbsp; {etiket('Etki: ' + etki, renk.get(etki, 'n'))}", unsafe_allow_html=True)
            st.write(detay)


# ---- Sunum modu: seçili sayfaları otomatik gez ------------------------------------------------
if sunum:
    st.markdown("<style>html{font-size:112%}.kpi .dg{font-size:1.85rem!important}</style>", unsafe_allow_html=True)

    @st.fragment(run_every=sunum_sn)
    def _sunum_tik():
        n = st.session_state.get("_sunum_n", 0)
        st.session_state["_sunum_n"] = n + 1
        if n == 0:                                   # sayfa yeni açıldı: süre dolana kadar bekle
            return
        mevcut = next((i for i, s in enumerate(SAYFALAR) if s.split("  ", 1)[1] == sayfa), 0)
        sira = [i for i, s in enumerate(SAYFALAR) if s.split("  ", 1)[1] in SUNUM_SAYFALARI]
        st.session_state["_sunum_git"] = next((i for i in sira if i > mevcut), sira[0])
        st.session_state["_sunum_n"] = 0
        st.rerun()

    _sunum_tik()
