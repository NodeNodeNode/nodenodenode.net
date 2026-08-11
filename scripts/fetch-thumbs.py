#!/usr/bin/env python3
"""
抓取 B 站视频封面,存成本地图。

为什么不能直接引 B 站图床:i*.hdslb.com 在墙外不一定通,而且那是替
B 站扛流量。本站的第一原则是零外部源 —— 页面里不能有任何自动加载的
第三方资源。所以封面必须下载到本地。

    python3 scripts/fetch-thumbs.py              # 只抓缺的
    python3 scripts/fetch-thumbs.py --force      # 全部重抓
    python3 scripts/fetch-thumbs.py --style color

产物按 BV 号命名存进 public/img/thumbs/,组件会自动按 BV 号找图 ——
所以 videos.yaml 里不用写图片路径,填 BV 号就行。

**每个系列只抓一张封面**(第一集里有 BV 号的那一集),不是每集都抓。
页面上只显示系列封面,把五十多集全抓下来纯属浪费。

顺带把 B 站上的原标题打印出来,方便核对 BV 号有没有填错。
(标题保持手写:自动抓来的标题往往带系列前缀和话题标签,不适合直接上墙。)
"""

import argparse
import json
import re
import sys
import urllib.request
from io import BytesIO
from pathlib import Path

import yaml
from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
VIDEOS_YAML = ROOT / "content/videos.yaml"
OUT_DIR = ROOT / "public/img/thumbs"

API = "https://api.bilibili.com/x/web-interface/view?bvid={}"
# B 站的图床和 API 都会看 UA / Referer,不带就可能被拒
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

SIZE = (640, 360)  # 2x 于卡片显示尺寸(320x180),高分屏也够清楚
INK = (14, 15, 16)  # --ink
PAPER = (216, 216, 216)  # --paper


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def filled(v):
    """YAML 里空字符串和缺字段都算"没填"(和 src/lib/content.js 的 filled 同义)"""
    return isinstance(v, str) and v.strip() != ""


def bvid_of(url):
    m = re.search(r"(BV[0-9A-Za-z]{10})", url or "")
    return m.group(1) if m else None


def youtube_cover(vid):
    """
    YouTube 封面兜底。

    有的系列整季都不在 B 站(比如「可视化编程的挑战」),没有兜底的话
    那张卡就是一块空占位。

    maxresdefault 不是每个视频都有(取决于上传时的源分辨率),没有时
    YouTube 会返回 404,退到 hqdefault —— 后者一定存在。
    """
    for quality in ("maxresdefault", "hqdefault"):
        try:
            return Image.open(BytesIO(get(f"https://i.ytimg.com/vi/{vid}/{quality}.jpg")))
        except Exception:  # noqa: BLE001,S112 - 404 是预期内的,继续退一级
            continue
    raise RuntimeError(f"YouTube 封面取不到: {vid}")


def treat(im, style):
    """
    裁成 16:9 再上色调。

    用 ImageOps.fit 居中裁切,不要直接 resize —— B 站封面常见 16:10,
    硬拉成 16:9 会把画面里的字压扁。
    """
    im = ImageOps.fit(im.convert("RGB"), SIZE, Image.LANCZOS)

    if style == "color":
        return im
    if style == "duotone":
        # 灰度映射到 墨黑 <-> 页面底色 之间,和整站配色完全同源
        return ImageOps.colorize(ImageOps.grayscale(im), black=INK, white=PAPER).convert("RGB")
    # gray(默认):封面本身就是深色 patch 截图,转灰度几乎不丢信息,
    # 只是去掉连线上那点红 —— 那个红会和站内唯一的信号蓝打架
    return ImageEnhance.Contrast(ImageOps.grayscale(im)).enhance(1.15).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="已存在的也重抓")
    ap.add_argument("--style", default="gray", choices=["gray", "color", "duotone"])
    args = ap.parse_args()

    data = yaml.safe_load(VIDEOS_YAML.read_text(encoding="utf-8")) or {}
    series = data.get("series") or []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ok = skipped = 0
    failed = []  # 真出错(网络/API),要非零退出
    notices = []  # 已知的正常情况,提醒一下就行,不算失败

    # 每个系列只要一张封面。优先 B 站(封面是 UP 主自己选的);整季都不在
    # B 站时退到 YouTube,文件名用 videoId —— 它是 11 位且不以 BV 开头,
    # 和 B 站的文件名天然不冲突,不需要额外前缀。
    wanted = []
    for s in series:
        eps = s.get("episodes") or []
        name = s.get("title", "?")
        bili = next((e for e in eps if bvid_of(e.get("bilibili"))), None)
        if bili:
            wanted.append((name, "bili", bvid_of(bili["bilibili"])))
            continue
        yt = next((e for e in eps if filled(e.get("youtube"))), None)
        if yt:
            wanted.append((name, "yt", yt["youtube"].strip()))
            notices.append((name, "整季不在 B 站,封面已用 YouTube 兜底"))
        else:
            notices.append((name, "既没有 B 站也没有 YouTube,封面需手动补"))

    for sname, source, ident in wanted:
        out = OUT_DIR / f"{ident}.jpg"
        if out.exists() and not args.force:
            skipped += 1
            continue

        try:
            if source == "bili":
                meta = json.loads(get(API.format(ident)))
                if meta.get("code") != 0:
                    failed.append((ident, f"B站 API: {meta.get('message')}"))
                    continue
                v = meta["data"]
                im = Image.open(BytesIO(get(v["pic"])))
                origin = f"B站原标题: {v['title']}"
            else:
                im = youtube_cover(ident)
                origin = "来源 YouTube"

            treat(im, args.style).save(out, quality=80, optimize=True)
            ok += 1
            print(f"  【{sname}】{ident}  {out.stat().st_size / 1024:5.1f}KB   {origin}")
        except Exception as e:  # noqa: BLE001 - 网络杂错太多,逐条报告即可
            failed.append((ident, str(e)))

    print(f"\n抓取 {ok} 张,跳过 {skipped} 张已存在({args.style} 风格)")

    if notices:
        print("\n提示(不是错误):")
        for who, why in notices:
            print(f"  {who}: {why}")

    if failed:
        print(f"\n以下 {len(failed)} 条抓取失败:")
        for who, why in failed:
            print(f"  {who}: {why}")
        sys.exit(1)


if __name__ == "__main__":
    main()
