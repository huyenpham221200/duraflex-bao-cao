# -*- coding: utf-8 -*-
"""Gộp các báo cáo ngày Duraflex thành 1 trang web (index.html).

Cách dùng:
  python build.py                  -> dựng lại index.html từ thư mục nguon/
  python build.py --nhap <thư mục>  -> chép báo cáo mới từ <thư mục> (vd Downloads) vào nguon/ rồi dựng

Tên file báo cáo phải có dạng: duraflex-danh-gia-DDMMYYYY-day-du.html hoặc ...-so-bo.html
(file tải trùng tên kiểu "...-so-bo (1).html" vẫn nhận, lấy bản mới nhất).
"""
import html
import os
import re
import shutil
import sys
from datetime import datetime

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.join(GOC, "nguon")
MAU_TEN = re.compile(r"^duraflex-danh-gia-(\d{2})(\d{2})(\d{4})-(day-du|so-bo)(?: \(\d+\))?\.html$")
TEN_BAN = {"day-du": "bản đầy đủ", "so-bo": "bản sơ bộ"}


def nhap(thu_muc):
    """Chép file báo cáo từ thư mục tải về vào nguon/ (bản mới nhất theo thời gian sửa)."""
    moi_nhat = {}
    for ten in os.listdir(thu_muc):
        m = MAU_TEN.match(ten)
        if not m:
            continue
        chuan = "duraflex-danh-gia-%s%s%s-%s.html" % m.groups()
        duong = os.path.join(thu_muc, ten)
        if chuan not in moi_nhat or os.path.getmtime(duong) > os.path.getmtime(moi_nhat[chuan]):
            moi_nhat[chuan] = duong
    so_moi = 0
    for chuan, duong in moi_nhat.items():
        dich = os.path.join(NGUON, chuan)
        if os.path.exists(dich) and open(dich, "rb").read() == open(duong, "rb").read():
            continue
        shutil.copy2(duong, dich)
        so_moi += 1
        print("  + da chep:", chuan)
    print("So file moi/cap nhat:", so_moi)


def doc_bao_cao():
    ds = []
    for ten in sorted(os.listdir(NGUON)):
        m = re.match(r"^duraflex-danh-gia-(\d{2})(\d{2})(\d{4})-(day-du|so-bo)\.html$", ten)
        if not m:
            continue
        d, mo, y, ban = m.groups()
        ngay = datetime(int(y), int(mo), int(d))
        s = open(os.path.join(NGUON, ten), encoding="utf-8").read()
        a = s.find('<div class="mo-dau">')
        b = s.find('<div class="chan-trang">')
        if a < 0 or b < 0:
            print("  ! bo qua (sai cau truc):", ten)
            continue
        noi_dung = s[a:b].rstrip()
        if noi_dung.endswith("</div>"):
            noi_dung = noi_dung[: -len("</div>")]  # bỏ thẻ đóng khung ngoài
        # mỗi ô Trạng thái của ngày lấy từ tiêu đề tóm tắt
        tt = re.search(r'<div class="tom"><div class="chinh"><div class="lon">(.*?)</div>', s)
        chay = re.search(r'<div class="meta">(Chạy lúc [^<·]*)', s)
        ds.append({
            "ten": ten, "ngay": ngay, "ban": ban, "noi_dung": noi_dung, "nguon": s,
            "trang_thai": tt.group(1) if tt else "",
            "chay": chay.group(1).strip() if chay else "",
        })
    return ds


def bang_ngay(ds):
    """Gộp bảng 7 ngày của mọi báo cáo; báo cáo mới hơn (và bản đầy đủ) ghi đè số cũ."""
    thu_tu = sorted(ds, key=lambda r: (r["ngay"], r["ban"] == "day-du"))
    dong = {}
    tieu_de = None
    for r in thu_tu:
        m = re.search(r'<table class="bang-ngay"><thead><tr>(.*?)</tr></thead><tbody>(.*?)</tbody>', r["nguon"], re.S)
        if not m:
            continue
        tieu_de = m.group(1)
        for tr in re.findall(r"<tr>(.*?)</tr>", m.group(2), re.S):
            o = re.search(r"<td>(\d{2}/\d{2}/\d{4})</td>", tr)
            if o:
                dong[datetime.strptime(o.group(1), "%d/%m/%Y")] = tr
    return tieu_de, dong


def ma_ngay(r):
    return "ngay-%s-%s" % (r["ngay"].strftime("%d-%m-%Y"), r["ban"])


def nhan(r):
    return "%s (%s)" % (r["ngay"].strftime("%d/%m/%Y"), TEN_BAN[r["ban"]])


def dung():
    ds = doc_bao_cao()
    if not ds:
        sys.exit("Chua co bao cao nao trong thu muc nguon/")
    theo_ngay = {}
    for r in ds:
        theo_ngay.setdefault(r["ngay"], {})[r["ban"]] = r
    cac_ngay = sorted(theo_ngay, reverse=True)
    chinh = lambda n: theo_ngay[n].get("day-du") or theo_ngay[n]["so-bo"]
    gan_nhat = cac_ngay[:2]
    cu = cac_ngay[2:]
    moi_nhat = chinh(cac_ngay[0])

    css = re.search(r"<style>.*</style>", ds[0]["nguon"], re.S).group(0)

    # ---- 2 ngày gần nhất
    khoi_gan = []
    for n in gan_nhat:
        r = chinh(n)
        khoi_gan.append('<section class="bao-cao-ngay" id="%s">%s</section>' % (ma_ngay(r), r["noi_dung"]))

    # ---- bảng tổng hợp mọi ngày
    tieu_de, dong = bang_ngay(ds)
    hang = []
    for n in sorted(dong, reverse=True):
        if n in theo_ngay:
            r = chinh(n)
            lien_ket = '<a href="#%s" class="xem" data-ngay="%s">%s</a>' % (
                ma_ngay(r), ma_ngay(r), "Xem " + TEN_BAN[r["ban"]])
        else:
            lien_ket = '<span class="rl">Chỉ có số tổng</span>'
        hang.append("<tr>%s<td>%s</td></tr>" % (dong[n], lien_ket))
    bang_tong = ""
    if tieu_de:
        bang_tong = ('<div class="bang-cuon"><table class="bang-ngay"><thead><tr>%s<th>Báo cáo chi tiết</th></tr></thead>'
                     "<tbody>%s</tbody></table></div>" % (tieu_de, "".join(hang)))

    # ---- lưu trữ: mọi bản của các ngày cũ + bản sơ bộ đã gửi của 2 ngày gần nhất
    luu_tru, nhom_cu, nhom_so_bo = [], [], []
    for n in cac_ngay:
        for ban in ("day-du", "so-bo"):
            r = theo_ngay[n].get(ban)
            if not r:
                continue
            if n in gan_nhat and r is chinh(n):
                continue  # đã hiện ở phần trên
            luu_tru.append('<section class="bao-cao-ngay luu" id="%s" hidden>%s</section>' % (ma_ngay(r), r["noi_dung"]))
            o = '<option value="%s">%s</option>' % (ma_ngay(r), html.escape(nhan(r)))
            # bản chính của ngày cũ lên trước; bản sơ bộ đã được thay bằng bản đầy đủ để nhóm riêng
            (nhom_cu if r is chinh(n) else nhom_so_bo).append(o)
    lua_chon = []
    if nhom_cu:
        lua_chon.append('<optgroup label="Các ngày trước">%s</optgroup>' % "".join(nhom_cu))
    if nhom_so_bo:
        lua_chon.append('<optgroup label="Bản sơ bộ đã gửi (đã có bản đầy đủ)">%s</optgroup>' % "".join(nhom_so_bo))

    nut = "".join('<a href="#%s" class="nut">%s</a>' % (ma_ngay(chinh(n)), html.escape(nhan(chinh(n)))) for n in gan_nhat)
    pham_vi = "%s – %s" % (cac_ngay[-1].strftime("%d/%m/%Y"), cac_ngay[0].strftime("%d/%m/%Y"))

    trang = TRANG.format(
        css=css, nut=nut, khoi_gan="\n".join(khoi_gan), bang_tong=bang_tong,
        lua_chon="".join(lua_chon), luu_tru="\n".join(luu_tru),
        cap_nhat=html.escape(moi_nhat["chay"].replace("Chạy lúc", "").strip()),
        so_ngay=len(cac_ngay), pham_vi=pham_vi,
        ngay_cuoi=cac_ngay[0].strftime("%d.%m.%Y"),
        co_luu="" if lua_chon else "hidden",
    )
    open(os.path.join(GOC, "index.html"), "w", encoding="utf-8").write(trang)
    print("Da dung index.html: %d ngay (%s), 2 ngay gan nhat: %s" % (
        len(cac_ngay), pham_vi, ", ".join(nhan(chinh(n)) for n in gan_nhat)))


TRANG = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>DURAflex - Báo cáo hằng ngày</title>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400..700&display=swap" rel="stylesheet">{css}
<style>
html {{ scroll-behavior: smooth; }}
.thanh {{ position: sticky; top: 0; z-index: 5; background: var(--sg-trang); border-bottom: 1px solid var(--sg-vien); padding: 10px 0; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
.thanh .nut {{ display: inline-block; border: 1px solid var(--sg-blue); color: var(--sg-blue); border-radius: 999px; padding: 4px 14px; font-size: 13px; font-weight: 600; text-decoration: none; }}
.thanh .nut:hover {{ background: var(--sg-blue-nhat); }}
.thanh .nut.dam {{ background: var(--sg-blue); color: var(--sg-trang); }}
.phan {{ margin-top: 36px; }}
.phan > h2.lon {{ font-size: 24px; border-bottom: 3px solid var(--sg-green); padding-bottom: 6px; display: inline-block; }}
.bao-cao-ngay {{ border: 1px solid var(--sg-vien); border-radius: var(--sg-bo-goc); padding: 4px 24px 24px; margin: 22px 0 34px; scroll-margin-top: 64px; }}
.bao-cao-ngay .mo-dau {{ margin: 20px 0; padding: 22px 26px; }}
.bao-cao-ngay .mo-dau h1 {{ font-size: 22px; }}
.bao-cao-ngay h2 {{ margin-top: 30px; }}
.chon-ngay {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; background: var(--sg-blue-nhat); border-radius: var(--sg-bo-goc); padding: 14px 18px; margin: 12px 0; }}
.chon-ngay select {{ font-family: var(--sg-font); font-size: 15px; padding: 6px 10px; border: 1px solid var(--sg-blue); border-radius: 8px; color: var(--sg-den); background: var(--sg-trang); min-width: 240px; }}
a.xem {{ color: var(--sg-blue); font-weight: 600; white-space: nowrap; }}
#tong-hop, #luu-tru {{ scroll-margin-top: 64px; }}
@media (max-width: 560px) {{ .bao-cao-ngay {{ padding: 4px 12px 16px; }} .khung {{ padding: 0 16px; }} }}
@media print {{ .thanh, .chon-ngay {{ display: none; }} .luu[hidden] {{ display: none; }} }}
</style></head><body><div class="khung">
<div class="dau-trang"><div class="logo">SEONGON</div><div class="tagline"><b>AI-First</b> Search Marketing Growth Partner</div></div>
<div class="mo-dau"><h1>duraflex.com.vn: báo cáo đánh giá bất thường traffic hằng ngày</h1>
<div class="meta">Cập nhật lần cuối: {cap_nhat} · Lưu {so_ngay} ngày báo cáo chi tiết ({pham_vi})</div>
<div class="meta">Phần đầu trang là báo cáo đầy đủ của 2 ngày gần nhất. Các ngày trước xem ở mục “Xem lại các ngày trước”.</div></div>
<nav class="thanh">{nut}<a href="#tong-hop" class="nut">Tổng hợp theo ngày</a><a href="#luu-tru" class="nut dam" {co_luu}>Xem lại các ngày trước</a></nav>

<div class="phan"><h2 class="lon">Báo cáo 2 ngày gần nhất</h2>
{khoi_gan}
</div>

<div class="phan" id="tong-hop"><h2 class="lon">Tổng hợp theo ngày</h2>
<p class="chu-thich">Số của mỗi ngày lấy theo báo cáo mới nhất có chứa ngày đó (bản đầy đủ ưu tiên hơn bản sơ bộ). Bấm “Xem” để mở báo cáo chi tiết của ngày.</p>
{bang_tong}
</div>

<div class="phan" id="luu-tru" {co_luu}><h2 class="lon">Xem lại các ngày trước</h2>
<div class="chon-ngay"><label for="chon"><b>Chọn ngày báo cáo:</b></label><select id="chon">{lua_chon}</select></div>
{luu_tru}
</div>
</div><div class="chan-trang"><div class="trai">Đánh giá bất thường hằng ngày · duraflex.com.vn</div><div class="phai">{ngay_cuoi}</div></div>
<script>
(function () {{
  var chon = document.getElementById('chon');
  function hien(id) {{
    var cac = document.querySelectorAll('section.luu');
    var co = false;
    for (var i = 0; i < cac.length; i++) {{ var dung = cac[i].id === id; cac[i].hidden = !dung; if (dung) co = true; }}
    if (co && chon) chon.value = id;
    return co;
  }}
  function theoHash() {{
    var id = decodeURIComponent(location.hash.slice(1));
    if (id && document.querySelector('section.luu#' + CSS.escape(id))) {{
      hien(id);
      document.getElementById(id).scrollIntoView();
    }}
  }}
  if (chon) {{
    if (chon.options.length) hien(chon.value);
    chon.addEventListener('change', function () {{ hien(chon.value); history.replaceState(null, '', '#' + chon.value); }});
  }}
  window.addEventListener('hashchange', theoHash);
  theoHash();
}})();
</script>
</body></html>
"""

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(NGUON, exist_ok=True)
    if len(sys.argv) >= 3 and sys.argv[1] == "--nhap":
        nhap(sys.argv[2])
    dung()
