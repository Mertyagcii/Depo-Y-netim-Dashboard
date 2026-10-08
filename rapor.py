"""Yönetici raporu: tek tıkla Excel çalışma kitabı ve yazdırılabilir HTML (tarayıcıdan PDF'e çevrilir) (Ayşe, Ece).

Rapor, ekrandaki dönem ve filtrelerle aynı verilerden üretilir; dışarıya veri göndermez.
"""
import html as _html
import io

import pandas as pd

CSS = """
body{font-family:'Segoe UI',Arial,sans-serif;color:#1c1d20;max-width:1000px;margin:24px auto;padding:0 18px}
h1{margin:0 0 4px} .alt{color:#6b7076;margin:0 0 18px} h2{margin:26px 0 8px;border-bottom:2px solid #d9f23b;padding-bottom:4px}
.kpi{display:flex;gap:12px;flex-wrap:wrap}.kpi div{flex:1 1 180px;border:1px solid #e5e5e0;border-radius:12px;padding:10px 14px}
.kpi b{display:block;font-size:1.5rem}.kpi span{color:#6b7076;font-size:.85rem}
table{border-collapse:collapse;width:100%;font-size:.88rem}th{text-align:left;color:#6b7076;border-bottom:1px solid #ddd;padding:5px}
td{padding:5px;border-bottom:1px solid #f0f0ec}.not{background:#fff8d6;border-radius:10px;padding:8px 12px;margin:10px 0;font-size:.85rem}
@media print{body{margin:0}h2{break-after:avoid}table,.kpi{break-inside:avoid}}
"""


def excel(sayfalar):
    """{sayfa_adı: DataFrame} -> .xlsx baytları."""
    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as yazar:
        for ad, df in sayfalar.items():
            d = df.copy()
            for c in d.columns:
                if pd.api.types.is_datetime64_any_dtype(d[c]):
                    d[c] = d[c].dt.strftime("%d.%m.%Y %H:%M").where(d[c].notna(), "")
            d.to_excel(yazar, sheet_name=str(ad)[:31], index=False)
            ws = yazar.sheets[str(ad)[:31]]
            for i, c in enumerate(d.columns, 1):
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(max(12, len(str(c)) + 4), 40)
    return tampon.getvalue()


def html_rapor(baslik, donem, kpiler, bolumler, notlar=(), grafikler=()):
    """kpiler: [(ad, değer)], bolumler: {başlık: DataFrame}, grafikler: [(başlık, plotly figure)]."""
    e = _html.escape
    g = []
    for i, (b, fig) in enumerate(grafikler):
        g.append(f"<h2>{e(b)}</h2>" + fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False,
                                                 config={"displayModeBar": False}))
    b = "".join(f"<h2>{e(ad)}</h2>" + df.head(25).to_html(index=False, border=0, escape=True) for ad, df in bolumler.items())
    k = "".join(f"<div><b>{e(str(v))}</b><span>{e(ad)}</span></div>" for ad, v in kpiler)
    n = "".join(f"<div class='not'>{e(x)}</div>" for x in notlar)
    return (f"<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>{e(baslik)}</title><style>{CSS}</style></head><body>"
            f"<h1>{e(baslik)}</h1><p class='alt'>{e(donem)}</p><div class='kpi'>{k}</div>{n}{''.join(g)}{b}</body></html>")
