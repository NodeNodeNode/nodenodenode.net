#!/usr/bin/env python3
"""
生成 logo 和 OG 图。

手上的 logo 原图是 160x160 的 JPEG(从 YouTube 头像取的),两色图被 JPEG
压过,边缘全是噪点。原生点阵是 **21x21**,而 160/21 = 7.62 不是整数,
所以当初放大时做了重采样,笔画边缘全是过渡灰。
这个脚本把它还原回 21x21,再用最近邻放大到 168x168(21x8),
得到边缘干净的两色 PNG。

    python3 scripts/make-images.py

依赖 Pillow。产物 commit 进仓库,平时不用重跑 —— 只有换 logo 或改 OG
文案时才需要。
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC_LOGO = ROOT / "vendor/logo-source.png"
FONT = ROOT / "vendor/font/fusion-pixel-12px-proportional-zh_hans.ttf"
OUT_DIR = ROOT / "public/img"

# logo 的原生点阵尺寸与配色(取自原图实际取色)
#
# GRID=21 是量出来的,不是猜的:对 12..32 每个候选值算"每格离纯黑/纯白
# 有多远",21 的拟合分数 0.033,明显优于次好的 20(0.078)。
# 一旦换 logo,先重新量一次再改这个数。
GRID = 21
BLACK = (0, 0, 0)
SILVER = (192, 192, 192)
PAPER = (216, 216, 216)  # --paper
INK = (14, 15, 16)  # --ink
GREY = (109, 113, 117)  # --grey-500


def read_grid():
    """
    把原图还原成 21x21 的 0/1 点阵。1 = 银底,0 = 黑。

    判定方式:先在全分辨率上二值化,再看每格里**暗像素的面积占比**是否过半。

    不要用"格子中心区域的灰度均值 + 阈值"这种做法 —— 因为放大倍数不是整数,
    一条 1 像素宽的横画会被摊到相邻两格上,两格都不够黑,于是整条横画被
    判成背景。这正是之前 20x20 版本把「连」下面那一横整条吃掉的原因。
    """
    im = Image.open(SRC_LOGO).convert("L")
    w, _ = im.size
    px = im.load()
    # 背景是 192,前景是 0,取中点
    dark = [[px[x, y] < 96 for x in range(w)] for y in range(w)]

    cell = w / GRID
    grid = []
    for gy in range(GRID):
        row = []
        for gx in range(GRID):
            x0, x1 = int(gx * cell), int((gx + 1) * cell)
            y0, y1 = int(gy * cell), int((gy + 1) * cell)
            area = [dark[y][x] for y in range(y0, y1) for x in range(x0, x1)]
            row.append(0 if sum(area) / len(area) > 0.5 else 1)
        grid.append(row)
    return grid


def render_logo(grid, scale):
    im = Image.new("RGB", (GRID, GRID), SILVER)
    px = im.load()
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            if not v:
                px[x, y] = BLACK
    # 最近邻放大,保持硬边
    return im.resize((GRID * scale, GRID * scale), Image.NEAREST)


def render_og(grid):
    """
    OG 图 1200x630。
    先在 400x210 的画布上按 1:1 画,再整体最近邻放大 3 倍 —— 这样像素字
    是真的按点阵放大的,不会被字体渲染器的抗锯齿磨圆。
    """
    W, H = 400, 210
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)

    # 边框
    d.rectangle([8, 8, W - 9, H - 9], outline=INK, width=1)

    logo = render_logo(grid, 2)  # 40x40
    im.paste(logo, (32, 40))

    f_big = ImageFont.truetype(str(FONT), 24)
    f_small = ImageFont.truetype(str(FONT), 12)

    d.text((88, 44), "连节社", font=f_big, fill=INK)
    d.text((88, 76), "vvvv gamma 中文社区", font=f_small, fill=INK)
    d.text((88, 96), "nodenodenode.net", font=f_small, fill=GREY)

    # 底部一条连线 + 端点,呼应站内的节点母题
    d.line([32, 136, W - 32, 136], fill=GREY, width=1)
    d.rectangle([32, 134, 35, 137], fill=INK)

    d.text((32, 148), "中文文档 · 视频教程 · 社群入口", font=f_small, fill=GREY)

    return im.resize((W * 3, H * 3), Image.NEAREST)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid = read_grid()

    # 168 = 21x8。网页上只能按 21 的整数倍显示:168 / 84 / 42 / 21。
    logo = render_logo(grid, 8)
    logo.save(OUT_DIR / "logo.png", optimize=True)

    render_og(grid).save(OUT_DIR / "og.png", optimize=True)

    for f in ("logo.png", "og.png"):
        p = OUT_DIR / f
        print(f"{f}: {Image.open(p).size} {p.stat().st_size / 1024:.1f}KB")


if __name__ == "__main__":
    main()
