<template>
  <div class="home-page">
    <header class="hero">
      <nav class="hero__nav">
        <BrandMark />
        <div class="hero__actions">
          <RouterLink class="ghost-link" to="/login">登录</RouterLink>
          <RouterLink class="primary-button" to="/register">立即开始</RouterLink>
        </div>
      </nav>

      <section class="hero__content">
        <div class="hero__copy">
          <p class="eyebrow">Document scanning workspace</p>
          <h1>把零散图片，整理成一份干净、可下载、可管理的 PDF。</h1>
          <p class="hero__summary">
            为学习型项目设计的扫描平台示例：公开首页有品牌感，登录后有工作台，后端完成鉴权、权限控制与图片扫描转 PDF。
          </p>
          <div class="hero__cta-row">
            <RouterLink class="primary-button" to="/register">注册并体验</RouterLink>
            <RouterLink class="secondary-link" to="/login">已有账号，去登录</RouterLink>
          </div>
        </div>

        <div class="hero__visual" aria-hidden="true">
          <div class="paper-stack paper-stack--one" />
          <div class="paper-stack paper-stack--two" />
          <div class="paper-stack paper-stack--three" />
        </div>
      </section>
    </header>

    <main class="story-sections">
      <section class="story-grid">
        <article>
          <p class="eyebrow">Workflow</p>
          <h2>上传、矫正、下载，一条链路讲清楚。</h2>
        </article>
        <ol class="process-list">
          <li>
            <span>01</span>
            <div>
              <h3>上传图片</h3>
              <p>支持多张图片，按顺序合成一份多页 PDF。</p>
            </div>
          </li>
          <li>
            <span>02</span>
            <div>
              <h3>自动扫描</h3>
              <p>后端进行透视矫正和对比度增强，尽量把纸张边缘拉正。</p>
            </div>
          </li>
          <li>
            <span>03</span>
            <div>
              <h3>下载 PDF</h3>
              <p>生成后立即返回二进制文件，前端直接提供下载链接。</p>
            </div>
          </li>
        </ol>
      </section>

      <section class="feature-strip">
        <article>
          <p class="eyebrow">What you learn</p>
          <h2>这不是只会“能跑”的 demo，而是能看懂层次的教学型骨架。</h2>
        </article>
        <ul class="feature-list">
          <li>Flask 应用工厂、Blueprint、JWT 权限控制</li>
          <li>Vue 3 + Pinia + Vue Router 的标准 SPA 结构</li>
          <li>OpenCV + Pillow 的扫描转 PDF 处理流程</li>
          <li>Docker Compose 串联前端、后端与 MySQL</li>
        </ul>
      </section>

      <section class="final-cta">
        <div>
          <p class="eyebrow">Ready to start</p>
          <h2>先登录系统，再从工作台看完整数据流最直观。</h2>
        </div>
        <div class="hero__cta-row">
          <RouterLink class="primary-button" to="/login">进入登录页</RouterLink>
          <RouterLink class="secondary-link" to="/register">没有账号，先注册</RouterLink>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import BrandMark from "../components/BrandMark.vue";
</script>
