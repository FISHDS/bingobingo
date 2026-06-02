from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

# ── 紙箱尺寸 ──────────────────────────────────────────────
L, W, H, G = 700, 400, 200, 35
FD = W // 2  # 蓋/底片深度 = W/2 = 200

TW = L + W + L + W + G   # 2235 mm
TH = FD + H + FD          # 600  mm

MARGIN_TOP    = 30   # mm  給標題用
MARGIN_BOTTOM = 20   # mm  給圖例用

page_w = TW * mm
page_h = (TH + MARGIN_TOP + MARGIN_BOTTOM) * mm

c = canvas.Canvas("/home/user/bingobingo/carton_RSC_700x400x200_1to1.pdf",
                  pagesize=(page_w, page_h))

# 座標轉換：原點定在繪圖區左上角 (y 向下為正)
def px(x_mm): return x_mm * mm
def py(y_mm): return page_h - (MARGIN_TOP + y_mm) * mm

# ── 顏色 & 線寬 ──────────────────────────────────────────
CUT   = colors.HexColor('#CC0000')
FOLD  = colors.HexColor('#0055AA')
BLACK = colors.black

CUT_W  = 0.7
FOLD_W = 0.7
DASH   = [4 * mm, 2.5 * mm]   # 4 mm on / 2.5 mm off

# ── 切割線 (紅色，實線) ─────────────────────────────────────
c.setStrokeColor(CUT)
c.setLineWidth(CUT_W)
c.setDash([])

# 外輪廓 (含膠邊凹口)
c.lines([
    # 頂邊 (蓋片區，不含膠邊)
    (px(0),    py(0),    px(L+W+L+W), py(0)),
    # 頂邊右側垂直 → 膠邊上邊
    (px(L+W+L+W), py(0),  px(L+W+L+W), py(FD)),
    # 膠邊上水平
    (px(L+W+L+W), py(FD), px(TW),        py(FD)),
    # 膠邊右垂直
    (px(TW),      py(FD), px(TW),        py(FD+H)),
    # 膠邊下水平
    (px(TW),      py(FD+H), px(L+W+L+W), py(FD+H)),
    # 底片區右垂直
    (px(L+W+L+W), py(FD+H), px(L+W+L+W), py(TH)),
    # 底邊
    (px(L+W+L+W), py(TH), px(0),          py(TH)),
    # 左邊
    (px(0),       py(TH), px(0),          py(0)),
])

# 槽口 (slit) ── 蓋片
for x in [L, L+W, L+W+L]:
    c.line(px(x), py(0), px(x), py(FD))

# 槽口 ── 底片
for x in [L, L+W, L+W+L]:
    c.line(px(x), py(FD+H), px(x), py(TH))

# ── 折線 (藍色，虛線) ─────────────────────────────────────
c.setStrokeColor(FOLD)
c.setLineWidth(FOLD_W)
c.setDash(DASH)

# 垂直折線 (主體段)
for x in [L, L+W, L+W+L]:
    c.line(px(x), py(FD), px(x), py(FD+H))

# 膠邊折線 (主體段)
c.line(px(L+W+L+W), py(FD), px(L+W+L+W), py(FD+H))

# 水平折線 (上下各一，橫跨主體+蓋/底片交界)
for y in [FD, FD+H]:
    c.line(px(0), py(y), px(L+W+L+W), py(y))

c.setDash([])

# ── 文字標注 ──────────────────────────────────────────────

def txt(text, x_mm, y_mm, size=32, color=BLACK, align='c'):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    yt = py(y_mm) - size * 0.35
    if align == 'c':
        c.drawCentredString(px(x_mm), yt, text)
    elif align == 'l':
        c.drawString(px(x_mm), yt, text)
    elif align == 'r':
        c.drawRightString(px(x_mm), yt, text)

# ── 主體面標籤 ──────────────────────────────────────────
body_y = FD + H / 2

txt(f"L = {L} mm",       L/2,           body_y, 38)
txt(f"W = {W} mm",       L + W/2,       body_y, 38)
txt(f"L = {L} mm",       L+W + L/2,     body_y, 38)
txt(f"W = {W} mm",       L+W+L + W/2,   body_y, 38)

# H 標注 (左側主體，垂直旋轉)
c.saveState()
c.translate(px(18), py(body_y))
c.rotate(90)
c.setFont("Helvetica-Bold", 32)
c.setFillColor(BLACK)
c.drawCentredString(0, -11, f"H = {H} mm")
c.restoreState()

# ── 蓋片 / 底片 標籤 ─────────────────────────────────────
top_y = FD / 2
bot_y = FD + H + FD / 2
flap_size = 24

for x_c in [L/2, L+W/2, L+W+L/2, L+W+L+W/2]:
    txt(f"W/2={FD}", x_c, top_y, flap_size)
    txt(f"W/2={FD}", x_c, bot_y, flap_size)

# ── 膠邊標籤 (旋轉) ──────────────────────────────────────
c.saveState()
c.translate(px(TW - G/2), py(FD + H/2))
c.rotate(90)
c.setFont("Helvetica-Bold", 22)
c.setFillColor(BLACK)
c.drawCentredString(0, -8, f"Glue {G}mm")
c.restoreState()

# ── 標題 ─────────────────────────────────────────────────
c.setFont("Helvetica-Bold", 34)
c.setFillColor(BLACK)
title = f"RSC  L={L} × W={W} × H={H} mm  (1:1)    Glue flap={G} mm"
c.drawCentredString(px(TW / 2), page_h - 22 * mm, title)

# ── 圖例 ─────────────────────────────────────────────────
leg_y = page_h - (MARGIN_TOP + TH + 13) * mm

c.setFont("Helvetica-Bold", 26)
# 切割線樣本
c.setStrokeColor(CUT)
c.setLineWidth(1.5)
c.line(px(20), leg_y, px(60), leg_y)
c.setFillColor(CUT)
c.drawString(px(65), leg_y - 9, "Cut Line（切割線）")

# 折線樣本
c.setStrokeColor(FOLD)
c.setLineWidth(1.5)
c.setDash(DASH)
c.line(px(280), leg_y, px(320), leg_y)
c.setDash([])
c.setFillColor(FOLD)
c.drawString(px(325), leg_y - 9, "Fold Line（折線）")

# 尺寸提示
c.setFont("Helvetica", 22)
c.setFillColor(colors.HexColor('#555555'))
c.drawRightString(px(TW - 10), leg_y - 9,
                  f"Blank size: {TW} × {TH} mm  |  Scale 1:1")

c.save()
print("✓ PDF 已產生")
