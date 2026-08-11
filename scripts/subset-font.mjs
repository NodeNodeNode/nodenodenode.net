#!/usr/bin/env node
/**
 * 像素字体子集化
 *
 * 全量 CJK 像素字 TTF 有 7MB,直接上网页不可接受。这个脚本从源码里
 * 自动推导出实际用到的字符集,只打包这些字形,产出 20-50KB 的 woff2。
 *
 * 字符集必须**自动推导**,不能手写字表 —— 子集漏字的表现是标题静默
 * 回退成系统字体,像素观感当场破功,而且很容易漏看。
 *
 *   npm run font        # 改完文案后重跑,产物 commit 进仓库
 *
 * 源字体 vendor/font/ 是 gitignore 的,缺失时会自动下载。
 */

import { readFile, writeFile, mkdir, readdir, stat } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import subsetFont from 'subset-font'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

const FONT_VERSION = '2026.07.20'
const FONT_FILE = 'fusion-pixel-12px-proportional-zh_hans.ttf'
const SRC_FONT = path.join(ROOT, 'vendor/font', FONT_FILE)
const OUT_FONT = path.join(ROOT, 'public/fonts/fusion-pixel-12-subset.woff2')

/** 扫描这些目录里的这些扩展名,取其全部字符 */
const SCAN_DIRS = ['src', 'content']
const SCAN_EXT = new Set(['.astro', '.yaml', '.yml', '.css', '.md'])

/**
 * 基线字符集:即使当前文案里没出现也要带上的。
 * 覆盖 ASCII 可打印区 + 中文常用标点,这样以后小改文案不必每次重跑。
 */
const BASELINE =
  Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i)).join('') +
  '，。、；：？！“”‘’（）《》〈〉【】—…·～￥　'

async function walk(dir) {
  const out = []
  let entries
  try {
    entries = await readdir(dir, { withFileTypes: true })
  } catch {
    return out
  }
  for (const e of entries) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) out.push(...(await walk(p)))
    else if (SCAN_EXT.has(path.extname(e.name))) out.push(p)
  }
  return out
}

async function ensureSourceFont() {
  if (existsSync(SRC_FONT)) return

  const url =
    `https://github.com/TakWolf/fusion-pixel-font/releases/download/${FONT_VERSION}/` +
    `fusion-pixel-font-12px-proportional-ttf-v${FONT_VERSION}.zip`

  console.error(
    `源字体缺失: ${path.relative(ROOT, SRC_FONT)}\n` +
      `请下载并解压到 vendor/font/ :\n  ${url}\n` +
      `(Fusion Pixel Font, SIL OFL 1.1)`
  )
  process.exit(1)
}

async function main() {
  await ensureSourceFont()

  const files = (await Promise.all(SCAN_DIRS.map((d) => walk(path.join(ROOT, d))))).flat()
  const chars = new Set(BASELINE)

  for (const f of files) {
    for (const ch of await readFile(f, 'utf8')) chars.add(ch)
  }

  // 控制字符不需要字形
  for (const ch of ['\n', '\r', '\t']) chars.delete(ch)

  const text = [...chars].sort().join('')
  const source = await readFile(SRC_FONT)
  const subset = await subsetFont(source, text, { targetFormat: 'woff2' })

  await mkdir(path.dirname(OUT_FONT), { recursive: true })
  await writeFile(OUT_FONT, subset)

  const kb = (n) => (n / 1024).toFixed(1) + 'KB'
  console.log(
    `扫描 ${files.length} 个文件 → ${chars.size} 个字形\n` +
      `${kb(source.length)} → ${kb(subset.length)}  ` +
      `(${((1 - subset.length / source.length) * 100).toFixed(1)}% 削减)\n` +
      `写入 ${path.relative(ROOT, OUT_FONT)}`
  )

  if (subset.length > 80 * 1024) {
    console.warn(`\n⚠ 子集超过 80KB —— 检查是不是把不该扫的文件也扫进来了`)
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
