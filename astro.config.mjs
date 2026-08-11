import { defineConfig } from 'astro/config'

// 纯静态输出。不加任何 integration —— 每多一个依赖就多一份构建产物里
// 混进外部 CDN 引用的风险,而这个站的第一原则是零外部源。
export default defineConfig({
  site: 'https://nodenodenode.net',
  output: 'static',
  build: {
    // 把样式全部内联进 <head>,省掉一次往返请求。
    // 墙内用户的瓶颈是 RTT 不是带宽,少一个请求比少几 KB 值钱。
    inlineStylesheets: 'always',
  },
  devToolbar: { enabled: false },
})
