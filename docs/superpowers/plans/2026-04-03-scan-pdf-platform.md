# Scan PDF Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> 本计划面向后续多 agent 协作，默认各 agent 先阅读本文件，再按任务边界各自领取不重叠的模块。

**Goal:** 构建一个带登录与权限控制的扫描转 PDF 网站，公开首页有品牌感，登录后提供图片扫描、多页 PDF 生成、账户管理和管理员用户管理能力。

**Architecture:** 采用前后端分离架构。前端使用 Vue 3 + Vite + Pinia + Vue Router 构建标准 SPA；后端使用 Flask 提供认证、权限和扫描接口；MySQL 存储用户与权限数据；Docker Compose 统一编排 `frontend`、`backend`、`mysql` 三个服务；扫描核心复用 `davide710/scanner`，由 Flask 封装成同步上传转 PDF 接口。

**Tech Stack:** Vue 3, Vite, Pinia, Vue Router, Axios, Flask, SQLAlchemy, JWT, MySQL, Docker Compose, OpenCV/Pillow

---

## 1. 产品范围与默认决策

### 1.1 V1 范围

- 公开首页
- 注册 / 登录 / 退出
- JWT 鉴权
- 普通用户工作台
- 多图上传并生成多页 PDF
- 账户页，仅支持查看基本信息和修改密码
- 管理员用户管理页
- Docker Compose 本地开发与部署

### 1.2 明确不做

- 扫描历史记录
- 异步任务队列
- 进度轮询
- 找回密码
- 邮箱验证
- 刷新令牌
- 菜单级 / 按钮级复杂权限系统
- 对象存储
- Redis / 消息队列 / Nginx

### 1.3 已锁定的产品决策

- 拼接含义固定为：多张图片分别扫描矫正后，合成为一个多页 PDF
- 登录方式固定为：JWT + 前端路由守卫
- 权限模型固定为：`user` 与 `admin`
- 用户注册开放，管理员通过初始化脚本预置
- 扫描接口为同步接口
- 页面视觉系统全站统一，但公开首页使用更强的展示型版式
- 登录后页面继承首页的配色、圆角、控件形状和留白节奏，不继承展示型版式
- 关键代码添加中文注释，重点解释数据流和设计原因

## 2. 推荐目录结构

本仓库目前为空，建议直接建立如下结构：

```text
flask_study/
├─ docs/
│  └─ superpowers/
│     └─ plans/
│        └─ 2026-04-03-scan-pdf-platform.md
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ assets/
│  │  ├─ components/
│  │  ├─ router/
│  │  ├─ stores/
│  │  ├─ styles/
│  │  ├─ views/
│  │  ├─ App.vue
│  │  └─ main.ts
│  ├─ public/
│  ├─ package.json
│  ├─ vite.config.ts
│  └─ Dockerfile
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ auth/
│  │  ├─ core/
│  │  ├─ db/
│  │  ├─ models/
│  │  ├─ scanner/
│  │  ├─ schemas/
│  │  └─ services/
│  ├─ tests/
│  ├─ run.py
│  ├─ requirements.txt
│  └─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

### 2.1 目录职责

- `frontend/`：Vue3 前端应用
- `backend/`：Flask API、JWT、数据库、扫描封装
- `docs/`：设计文档、实现计划、协作文档
- `docker-compose.yml`：统一启动三服务
- `.env.example`：环境变量模板

## 3. 前端设计方案

### 3.1 视觉系统

前端需要先抽一套全站通用设计 token，再分配到首页和登录后页面：

- 背景色：奶白、浅米、浅灰绿一类的柔和底色
- 主文字色：偏深棕黑或炭灰
- 强调色：单一主强调色，用于按钮、链接、状态高亮
- 形状语言：中大圆角，输入框和按钮统一圆润形态
- 留白规则：大块留白，少描边，少重阴影
- 组件语义：上传区、面板、表格工具栏可以有浅底，但不做厚重后台卡片

### 3.2 页面分工

#### 公开首页

- Hero 区：产品名、品牌文案、注册/登录 CTA、主视觉插画或抽象图形
- 流程说明：上传 -> 扫描 -> 下载 PDF
- 功能说明：多图上传、自动矫正、多页 PDF、Docker 部署
- CTA 收尾：再次引导注册或登录

#### 登录页 / 注册页

- 延续首页视觉气质
- 保持布局简洁，聚焦表单
- 允许使用一张轻插画或背景色块，不使用复杂展示区

#### 工作台页

- 顶部导航：品牌名、当前用户、退出入口
- 中心区域：上传区、文件列表、处理操作区、结果下载区
- 结构服务于操作效率，不做宣传性布局
- 继承品牌色和圆角语言

#### 管理页

- 使用工具型布局：筛选栏 + 表格 + 操作按钮
- 继承品牌色、圆角和轻边界
- 不使用传统后台蓝灰模板样式

### 3.3 前端路由

建议路由如下：

- `/`：公开首页
- `/login`：登录页
- `/register`：注册页
- `/workspace`：用户工作台，需登录
- `/account`：账户页，需登录
- `/admin/users`：用户管理页，需管理员角色

### 3.4 前端状态

建议最小 Pinia store：

- `authStore`
  - token
  - currentUser
  - isAuthenticated
  - login / logout / fetchMe
- `scanStore`
  - selectedFiles
  - isSubmitting
  - errorMessage
  - pdfBlobUrl
  - addFiles / removeFile / clearFiles / submitFiles / resetResult

## 4. 后端设计方案

### 4.1 Flask 模块职责

- `auth/`：注册、登录、JWT、当前用户解析
- `models/`：数据库模型
- `db/`：连接、迁移、初始化、种子数据
- `services/`：用户服务、角色校验、密码处理
- `scanner/`：对接 `davide710/scanner` 的中间层
- `api/`：对外 HTTP 接口

### 4.2 数据库设计

V1 只做 `users` 表：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | bigint/int | 主键 |
| username | varchar | 用户名，唯一 |
| password_hash | varchar | 密码哈希 |
| role | varchar | `user` / `admin` |
| status | varchar | `active` / `disabled` |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 4.3 鉴权规则

- 注册成功默认创建 `user`
- 登录成功返回 JWT
- 前端后续请求带 `Authorization: Bearer <token>`
- 后端统一解析当前用户
- 管理员接口统一校验 `role == admin`
- 被禁用用户不可登录，也不可继续使用旧 token 访问受保护接口

### 4.4 扫描接口

#### `POST /api/scan`

- 请求：`multipart/form-data`
- 字段：`files[]`
- 处理流程：
  1. 保存上传文件到临时目录
  2. 逐张调用扫描逻辑做透视矫正与清理
  3. 将处理后的图片按顺序生成多页 PDF
  4. 返回 PDF 二进制
  5. 清理临时文件

#### 成功响应

- `200 OK`
- `Content-Type: application/pdf`
- 响应体为 PDF 文件流

#### 失败响应

```json
{
  "message": "扫描失败原因"
}
```

### 4.5 管理接口

- `GET /api/admin/users`
- `PATCH /api/admin/users/:id/status`
- `PATCH /api/admin/users/:id/role`

管理员只管理用户状态和角色，不做菜单权限与资源权限。

## 5. Docker 与环境变量

### 5.1 Compose 服务

- `frontend`
  - Vue 开发服务或构建产物运行环境
- `backend`
  - Flask API 服务
- `mysql`
  - 用户数据库

### 5.2 环境变量建议

根目录 `.env.example` 中至少包含：

```env
MYSQL_DATABASE=scan_pdf
MYSQL_USER=scan_user
MYSQL_PASSWORD=scan_pass
MYSQL_ROOT_PASSWORD=root_pass
JWT_SECRET_KEY=change-me
FLASK_ENV=development
VITE_API_BASE_URL=http://localhost:5000
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123456
```

### 5.3 初始化要求

- MySQL 启动后可被 Flask 成功连接
- Flask 首次启动自动建表
- 若管理员不存在，则自动创建默认管理员

## 6. API 契约

### 6.1 Auth

- `POST /api/auth/register`
  - 输入：`username`, `password`
  - 输出：成功消息或错误消息

- `POST /api/auth/login`
  - 输入：`username`, `password`
  - 输出：`token`, `user`

- `GET /api/auth/me`
  - 输出：当前登录用户基础信息

- `PATCH /api/auth/password`
  - 输入：`old_password`, `new_password`
  - 输出：成功消息

### 6.2 Admin

- `GET /api/admin/users`
  - 输出：用户列表

- `PATCH /api/admin/users/:id/status`
  - 输入：`status`
  - 输出：更新后的用户信息

- `PATCH /api/admin/users/:id/role`
  - 输入：`role`
  - 输出：更新后的用户信息

### 6.3 Health

- `GET /api/health`
  - 输出：后端服务与数据库状态

## 7. 中文注释要求

### 7.1 前端重点注释位置

- `main.ts`
  - 解释应用入口、为什么先注册哪些插件
- `router/index.ts`
  - 解释公开页与受保护页的区别
  - 解释管理员路由守卫逻辑
- `stores/auth.ts`
  - 解释 token 生命周期和当前用户状态来源
- `stores/scan.ts`
  - 解释文件选择、提交、下载 PDF 的状态流转
- `api/auth.ts` / `api/scan.ts`
  - 解释表单上传、二进制下载、错误处理
- `views/*`
  - 解释页面的职责和组件之间的数据流
- `styles/*`
  - 解释全局设计 token 为什么这样定义

### 7.2 后端重点注释位置

- JWT 生成与解析
- 密码哈希与校验
- 管理员权限校验
- 文件上传临时目录
- 调用 scanner 的中间层
- 多张图片生成 PDF 的流程

### 7.3 注释原则

- 解释“为什么”
- 解释“这一层负责什么”
- 解释“前后端如何配合”
- 不对显而易见的赋值和循环做重复注释

## 8. 多 Agent 协作拆分

推荐拆成 6 个不重叠工作流，便于并行：

### Workstream A: 项目脚手架与基础环境

**Ownership**
- 根目录结构
- Docker Compose
- `.env.example`
- README 初稿

**Deliverables**
- 前后端目录结构初始化
- 三服务可启动
- 基础文档齐备

### Workstream B: 后端认证与用户模型

**Ownership**
- `backend/app/auth/`
- `backend/app/models/`
- `backend/app/services/user*`

**Deliverables**
- 注册、登录、获取当前用户、修改密码
- 用户表模型与管理员初始化

### Workstream C: 后端扫描与 PDF 接口

**Ownership**
- `backend/app/scanner/`
- `backend/app/api/scan*`

**Deliverables**
- 上传多图
- 调用 `davide710/scanner`
- 输出多页 PDF

### Workstream D: 前端公开页与认证页

**Ownership**
- `frontend/src/views/Home*`
- `frontend/src/views/Login*`
- `frontend/src/views/Register*`
- 品牌视觉 token

**Deliverables**
- 公开首页
- 登录页
- 注册页
- 统一视觉系统

### Workstream E: 前端工作台与账户页

**Ownership**
- `frontend/src/views/Workspace*`
- `frontend/src/views/Account*`
- `frontend/src/stores/scan.ts`
- `frontend/src/api/scan.ts`

**Deliverables**
- 多图上传、删除、清空、提交、下载
- 账户页修改密码

### Workstream F: 管理员页与联调

**Ownership**
- `frontend/src/views/admin/*`
- 路由守卫
- 前后端联调与验收

**Deliverables**
- 用户管理页
- 管理员权限控制
- 三服务联调通过

## 9. 执行顺序

推荐顺序如下：

1. Workstream A
2. Workstream B
3. Workstream D
4. Workstream C
5. Workstream E
6. Workstream F

原因：
- 先把目录、容器、环境打稳
- 再做认证与用户数据
- 再做公开页和登录页
- 扫描接口与工作台随后对接
- 最后做管理员页和整体联调

## 10. 验收标准

### 10.1 用户侧

- 未登录访问工作台会跳转登录页
- 用户可注册、登录、退出
- 用户可修改密码
- 用户可上传 1 张或多张图片
- 后端成功返回多页 PDF
- 用户可下载 PDF

### 10.2 管理员侧

- 管理员能登录
- 管理员能查看用户列表
- 管理员能启用/禁用用户
- 管理员能修改用户角色

### 10.3 系统侧

- `docker compose up` 能启动全部服务
- 后端能连接 MySQL
- 初始化后自动存在管理员账号
- 前端与后端接口联通
- 扫描失败时前端能收到明确错误提示

### 10.4 视觉侧

- 首页明显体现参考站的气质：大留白、强标题、柔和背景、主视觉驱动
- 登录后页面延续统一颜色、圆角、控件形状
- 工作台与管理页保持工具化和高可用性，不因为视觉风格牺牲操作效率

## 11. 后续可选扩展

V2 再考虑以下能力：

- 扫描历史记录
- 异步任务与进度轮询
- PDF 下载历史
- 头像与个人资料
- 文件长期存储
- 按钮级权限系统
- 刷新令牌

