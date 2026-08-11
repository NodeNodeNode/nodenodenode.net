#!/usr/bin/env node
/**
 * 零外部源检查 —— 这是本站最重要的一条约束。
 *
 * 页面里任何**自动加载**的第三方资源(字体、脚本、图床、统计)在墙内
 * 都可能直接吊死整个页面。用户主动点击的外链没问题,自动加载的不行。
 *
 * 所以这里只检查会触发请求的属性:src / href(stylesheet 等) / srcset /
 * url() / iframe。<a href> 是用户点了才走的,放行。
 *
 *   npm run build && npm run check:external
 */

import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const DIST = path.join(ROOT, 'dist')

/** 自己的域名 —— 出现这些是允许的 */
const OWN = [/^\/(?!\/)/, /^https?:\/\/nodenodenode\.net/, /^data:/, /^#/]

/**
 * 会自动发起请求的地方。<a href> 故意不在列。
 * <link href> 会加载(stylesheet/preload/icon),所以单独匹配。
 */
const PATTERNS = [
  { name: 'src', re: /\bsrc\s*=\s*["']([^"']+)["']/gi },
  { name: 'srcset', re: /\bsrcset\s*=\s*["']([^"']+)["']/gi },
  { name: 'link href', re: /<link\b[^>]*?\bhref\s*=\s*["']([^"']+)["']/gi },
  { name: 'css url()', re: /url\(\s*["']?([^"')]+)["']?\s*\)/gi },
  { name: 'import', re: /@import\s+["']([^"']+)["']/gi },
]

const IFRAME = /<iframe\b/gi

async function walk(dir) {
  const out = []
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) out.push(...(await walk(p)))
    else if (/\.(html|css|js)$/.test(e.name)) out.push(p)
  }
  return out
}

const isOwn = (u) => OWN.some((re) => re.test(u))

const files = await walk(DIST).catch(() => {
  console.error('dist/ 不存在,先跑 npm run build')
  process.exit(1)
})

const bad = []
let iframes = 0

for (const f of files) {
  const src = await readFile(f, 'utf8')
  const rel = path.relative(ROOT, f)

  for (const { name, re } of PATTERNS) {
    for (const m of src.matchAll(re)) {
      const url = m[1].trim().split(/\s+/)[0]
      if (!url || isOwn(url)) continue
      bad.push({ rel, name, url })
    }
  }

  iframes += (src.match(IFRAME) || []).length
}

if (iframes) {
  bad.push({ rel: 'dist/', name: 'iframe', url: `发现 ${iframes} 个 <iframe>` })
}

if (bad.length === 0) {
  console.log(`✓ 零外部源:检查了 ${files.length} 个文件,没有自动加载的第三方资源`)
  process.exit(0)
}

console.error(`✗ 发现 ${bad.length} 处会自动加载的外部资源:\n`)
for (const b of bad) console.error(`  ${b.rel}  [${b.name}]  ${b.url}`)
console.error(
  '\n这些在墙内可能加载失败并拖垮整页。自托管它们,或者去掉。' +
    '\n(用户主动点击的 <a href> 外链不在此列,是允许的)'
)
process.exit(1)
