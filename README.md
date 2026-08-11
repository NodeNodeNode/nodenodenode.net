# nodenodenode.net

**连节社** —— vvvv gamma 中文社区的入口页。

一个纯静态单页站,把散落在 B 站、YouTube、灰皮书、GitHub 上的中文资源
归拢到一处。不加载任何第三方资源,页面关掉 JavaScript 也完全可用。

线上:<https://nodenodenode.net>

---

## 参与进来

**欢迎提 issue 和 PR,按 GitHub 上通常的方式来就行,不需要先打招呼。**

最需要人手的地方:

- **补内容** —— 加一条视频、一本书、一个学习资源。这是最容易上手的,
  基本只用改 YAML,见下面「改内容」。
- **报错** —— 链接失效了、文案写得不对、手机上排版坏了,开个 issue 说一声。
  死链是这类站最常见的毛病,发现了就值得报。
- **翻译** —— 灰皮书中文版在 [thegraybookcn](https://github.com/NodeNodeNode/thegraybookcn),
  认领一页、改一个错字都算数。

提 PR 的话:

1. Fork,建个分支
2. 改完本地跑一遍(**这两条必须过**):
   ```bash
   npm run build
   npm run check:external
   ```
3. 提 PR,说清楚改了什么。不用纠结 commit message 格式。

如果只是想加一条链接又不想折腾本地环境,直接开 issue 把链接贴上来也完全可以。

---

## 快速开始

```bash
npm install
npm run dev              # 本地开发,默认 :4321

npm run build            # 构建到 dist/
npm run check:external   # 零外部源检查(构建后跑,必须过)

npm run font             # 改完中文文案后重新生成字体子集
npm run thumbs           # 抓视频封面到本地(加完视频后跑)
npm run images           # 重新生成 logo 和 OG 图(换 logo 时才跑)
```

`thumbs` 和 `images` 是 Python 脚本(依赖 Pillow、PyYAML),因为图像处理
用 PIL 比在 Node 里装一套图形依赖干净得多。

---

## 第一原则:零外部源

**页面里不能有任何自动加载的第三方资源。**

目标读者在中国大陆,而站点部署在境外。一个加载失败的 Google Fonts 或
YouTube iframe 不只是"少个东西",它会让整页卡住甚至白屏。所以:

| 不行 | 用什么代替 |
| --- | --- |
| Google Fonts / gstatic | 自托管 woff2(见下) |
| YouTube / B 站 iframe 嵌入 | 静态本地缩略图 + 普通链接 |
| B 站 / YouTube 图床的缩略图 | `npm run thumbs` 抓到本地 |
| jsdelivr / unpkg 引 JS 或 CSS | 不引。这站不需要 JS |
| Google Analytics 等第三方统计 | 用 Vercel Web Analytics(第一方路径,见下) |

用户**主动点击**的外链没问题(B 站、GitHub、vvvv.org 都在页面上),
禁的是浏览器自动发起的请求。

两道防线:

1. **`npm run check:external`** —— 扫 `dist/` 里的 `src` / `srcset` /
   `<link href>` / `url()` / `<iframe>`,发现非本站来源就非零退出。
   PR 里改了任何资源引用都要跑一次。
2. **`vercel.json` 里的 CSP** —— 把这条约束固化到运行时。真漏了一个,
   浏览器会直接拦掉,而不是等墙来告诉我们。

   > `vercel.json` 的 schema 是严格的,多余的键会让部署直接失败,
   > 所以那个文件里不能写注释。它的三条 header 分别是:字体和图片
   > 长缓存、基础安全头、以及上面这条 CSP。两处 `'unsafe-inline'`
   > 都是必需的:`style-src`(CSS 内联在 `<head>` 里)和 `script-src`
   > (统计脚本是内联的,见下)。
   >
   > 放宽 `script-src` 不影响这条 CSP 在本项目里的**实际作用** ——
   > 它的目的是"禁止任何第三方来源",而 `script-src` 里没有列出任何
   > 外部域名、`connect-src 'self'` 也堵死了往外发数据,这两点没变。
   > 损失的是防 XSS 的强度,而本站不渲染任何用户输入。

### 访问统计

用 Vercel Web Analytics。它的脚本走**第一方路径** `/_vercel/insights/*`,
不是外部域名,所以不违反上面那条铁律,`check:external` 也据此放行。

三个坑:

1. **光在 Vercel 面板上点 Enable 是没用的。** 必须同时在
   `src/layouts/Base.astro` 里保留 `<Analytics />`(来自 `@vercel/analytics`)。
2. **CSP 必须是 `script-src 'self' 'unsafe-inline'`。** `@vercel/analytics`
   注入的是**内联** `<script type="module">`,只写 `'self'` 是不够的 ——
   `'self'` 只放行同源的外链脚本,内联照样被拦。表现是:面板显示已启用、
   构建没有任何报错、数据永远是 0。改 CSP 之后务必实测一次:
   ```bash
   # 把 CSP 塞成 meta 标签,看控制台有没有拦截
   google-chrome --headless=new --enable-logging=stderr --dump-dom <测试页> 2>&1 >/dev/null \
     | grep -i "violates the following content security policy"
   ```
3. **数据会系统性少算大陆读者。** 墙内本来就可能加载不全,信标发不出去。
   看数字时要知道它偏向海外。

页面本身不依赖这个脚本:关掉 JavaScript,所有内容和链接照常可用。

---

## 改内容

日常改站只需要动 `content/*.yaml`,不用碰组件:

| 文件 | 管什么 |
| --- | --- |
| `site.yaml` | 站名、标语、首屏那段介绍、meta、页脚 |
| `community.yaml` | 微信 / Discord / GitHub / QQ 等入口 |
| `resources.yaml` | 文档、下载、书、翻译参与 |
| `videos.yaml` | 视频系列 |
| `works.yaml` | 社区作品 |
| `about.yaml` | 关于、需要人手的地方 |

几条约定:

- **填了值才渲染。** `href` 留空的入口自动不出现,`works.items` 为空
  则整个作品板块隐藏,二维码图片没放进来则整条隐藏。空着比挂一个死
  链接好。
- **YAML 里的文本不是 Markdown。** 写 `**加粗**` 会原样显示成星号。
- **改完中文文案要跑 `npm run font`**,否则新字不在字体子集里,标题会
  静默回退成系统字体 —— 这个不报错,只是变难看,很容易漏掉。

### 加一条视频

在 `videos.yaml` 对应的系列下加一集,填 `bilibili`(BV 号)和/或
`youtube`(videoId),**填裸 ID,不填完整网址**。然后:

```bash
npm run thumbs
```

封面会自动抓到 `public/img/thumbs/`,按 BV 号 / videoId 命名,组件据此
找图 —— **不用手写图片路径**。整季都不在 B 站时会自动退到 YouTube 封面。

封面默认转灰度:这些封面本身就是深色 patch 截图,转灰度几乎不丢信息,
只是去掉连线上那点红 —— 那个红会和站内唯一的信号蓝打架。想要彩色用
`python3 scripts/fetch-thumbs.py --style color`。

---

## 字体

标题用 [Fusion Pixel Font](https://github.com/TakWolf/fusion-pixel-font)
(缝合怪像素字体)12px 比例版,SIL OFL 1.1,可商用。

> 没用 Zpix:它的商用授权是 $1000,而且不提供 woff2。

正文用系统字体栈,**不用像素字** —— 大段中文点阵字读不了,这是可用性
问题不是风格问题。

全量 CJK 像素字 TTF 有 7MB,所以 `scripts/subset-font.mjs` 扫描
`src/**` 和 `content/**`,只打包实际用到的字形,产出约 30KB 的 woff2。
字符集**自动从源码推导**,不要手写字表。

源字体 `vendor/font/` 是 gitignore 的(7MB),缺失时脚本会提示下载地址。
子集产物 `public/fonts/*.woff2` 要提交。

---

## 视觉规则

调色板锚定在 logo 的实际取色:纯黑 `#000` + VGA 银 `#C0C0C0`。全部
token 在 `src/styles/tokens.css`。

动手改样式前先读这几条,它们是这套观感的来源:

- **8px 网格。** 所有间距取 `--s1`…`--s12`。
- **零圆角、零阴影、零渐变。** tokens.css 里有一条 `!important` 兜底。
  分隔一律用 1px 实线。
- **像素字号只能是 12 的整数倍**(12 / 24 / 36 / 48),行高 4/3,
  这样每档都落在 8px 网格上。非整数倍会让点阵糊掉。
- **logo 只能按整数比例缩放。** 原生点阵 21×21,图片是 168×168,
  所以允许 168 / 84 / 42 / 21,不允许 160 或 40。
- **单一亮色主题,不做深色模式。** 银灰底就是这套视觉的身份。
- 节点图母题(竖线 + 方形端点)全部用 CSS 和内联 SVG 实现,不引 WebGL,
  不引图形库。

`scripts/make-images.py` 用来重新生成 logo 和 OG 图 —— 它把原始那张
JPEG 头像还原回 21×21 点阵再放大,去掉压缩噪点。

> 换 logo 的话,`GRID` 那个数要**重新量**,不能沿用。原图是非整数倍
> 放大的(160/21 = 7.62),网格数猜错一格,细笔画会被整条判成背景 ——
> 之前就是这么把「连」下面那一横弄丢的,而且肉眼很难当场发现。

---

## 部署

**Vercel + 自定义域名 `nodenodenode.net`**,push 即部署。

几件必须注意的事:

1. **一定要用自定义域名**,别让 `*.vercel.app` 成为主入口 —— Vercel
   官方也建议这么做,自定义域名被标记的概率低得多。
2. **DNS 记录以 Vercel 控制台当时给出的为准。** 社区里流传的"大陆友好"
   解析目标会变,别照抄任何文档里写死的 IP,包括这一份。
3. **`thegraybook.nodenodenode.net` 的 CNAME 不能动。** 灰皮书中文站
   是独立部署的,改 apex 解析时碰到这条记录会把它一起弄挂。
4. 老论坛那台 DigitalOcean(`188.166.208.97`)现在只在跑一个 nginx
   默认页,新站确认正常后再退掉。

Vercel 对大陆可用性**不作保证**,这是接受了的风险 —— 备案需要境内主体,
走不通。如果墙内反馈确实打不开,下一步是在前面加一层腾讯云 EdgeOne
国际版(港/新节点,不需要备案)。站是纯静态的,加镜像成本很低。

**不要**在 Vercel 前面套代理(官方明确不建议),也不要迁到 Netlify
(大陆被墙,自定义域名同样受影响)。

---

## 上线前检查

```bash
npm run build
npm run check:external     # 必须通过
du -sh dist                # 目前约 370K
```

外加:

- 关掉浏览器 JavaScript,页面应完全正常(包括所有链接)
- 确认标题没有回退成系统字体(回退 = 字体子集漏字,重跑 `npm run font`)
- 320 / 768 / 1440 三个宽度各看一遍
- 部署后用 itdog.cn 之类工具测大陆可达性,并请群里的人真机实测一次

### 会静默失效的东西

这类站最大的风险不是崩,是**链接悄悄死掉而没人知道**。定期检查:

- **Discord 邀请链接** —— 必须是"永不过期"。Discord 默认 30 天,
  过期后页面上的按钮就成了死链,不会有任何提醒。验证方法:
  ```bash
  curl -s "https://discord.com/api/v10/invites/<邀请码>?with_expiration=true"
  ```
  返回里 `expires_at` 必须是 `null`。
- **视频链接** —— UP 主删稿或转私密都会让链接失效。
- **微信群二维码** —— 有效期只有 7 天且扫满 200 次即失效,所以这个站
  **不放群二维码**,页面上只说明现状。

---

## 授权

**代码 [MIT](LICENSE)** —— Astro 组件、样式、构建脚本随便拿去用。

素材不在 MIT 范围内,各自遵循自己的授权:

- **标题字体** Fusion Pixel Font —— SIL OFL 1.1,可商用,须保留授权声明
- **视频封面** —— 版权归各视频作者,本站仅作索引缩略图使用
- **logo 与站上的文字内容** —— 归连节社

想拿这套东西搭自己社区的站,换掉 `content/`、`public/img/` 和字体就行。
