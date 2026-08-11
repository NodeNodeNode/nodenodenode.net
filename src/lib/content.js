/**
 * YAML 内容加载。
 *
 * 日常改站只需要动 content/*.yaml,不必碰组件。
 *
 * 这里用 import.meta.glob 而不是 fs.readFileSync —— 后者能构建成功,但
 * Vite 不会把那些 YAML 当成模块依赖,于是改完 content/*.yaml 之后
 * dev server 什么反应都没有,必须重启才看得到。而"改 YAML"正是这个站
 * 唯一的日常操作,那样等于没有热更新。
 */

import { load } from 'js-yaml'

const files = import.meta.glob('/content/*.yaml', {
  query: '?raw',
  import: 'default',
  eager: true,
})

function read(name) {
  const key = `/content/${name}.yaml`
  const raw = files[key]
  if (raw === undefined) {
    throw new Error(`找不到 ${key} —— content/ 下有:${Object.keys(files).join(', ')}`)
  }
  return load(raw)
}

export const site = read('site')
export const community = read('community')
export const resources = read('resources')
export const videos = read('videos')
export const works = read('works')
export const about = read('about')

/** 填了值才算数 —— 空字符串的入口要自动隐藏,而不是渲染成一个死按钮 */
export const filled = (v) => typeof v === 'string' && v.trim().length > 0

/**
 * 图片实际存在才渲染 <img>。
 * 二维码、缩略图这些素材是后补的,文件没到位时应该退化成占位块,
 * 而不是在页面上挂一个碎图 —— 碎图比占位块更像"这站没人管"。
 *
 * 这个用 glob 列 public/ 下的文件名,同样是为了让 Vite 跟踪 ——
 * 新放进一张二维码,dev server 要能立刻显示出来。
 */
const assets = import.meta.glob('/public/**/*.{png,jpg,jpeg,svg,webp}', { eager: true })
const assetPaths = new Set(Object.keys(assets).map((p) => p.replace(/^\/public/, '')))

export const hasAsset = (p) => filled(p) && assetPaths.has(p)
