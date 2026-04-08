# Scan PDF Platform

一个面向学习与实战演示的扫描转 PDF 平台。

它不是单纯“能跑就行”的 demo，而是按前后端分离思路拆开的完整示例项目：有公开首页、有登录注册、有基于 JWT 的权限控制、有普通用户工作台，也有管理员用户管理页。后端负责认证、角色权限、图片扫描与多页 PDF 生成；前端负责路由守卫、登录态管理、文件上传交互和最终下载体验。

## 项目目标

这个项目围绕一个非常具体的业务场景展开：

- 用户可以注册和登录
- 登录后进入工作台，上传一张或多张图片
- 后端对图片进行扫描增强和透视矫正
- 最终把多张图片合成为一个多页 PDF 返回给前端下载
- 管理员可以查看用户列表，并调整用户角色或状态

如果你正在学习 Flask + Vue 这类前后端分离项目，这个仓库适合用来理解下面几件事：

- Flask 项目如何做应用工厂、Blueprint 和业务分层
- Vue 3 项目如何组织 Router、Pinia、页面和 API 模块
- JWT 登录态如何在前后端之间协作
- 文件上传到服务端后，如何走扫描处理再返回二进制文件
- Docker Compose 如何串起前端、后端和 MySQL

## 技术栈

### 前端

- Vue 3
- Vite
- Pinia
- Vue Router
- Axios
- TypeScript

### 后端

- Flask
- Flask-JWT-Extended
- Flask-SQLAlchemy
- SQLAlchemy
- PyMySQL

### 图像与文件处理

- OpenCV
- Pillow

### 运行与部署

- Docker Compose
- MySQL 8.4

## 功能清单

当前 V1 已覆盖以下功能：

- 公开首页
- 用户注册
- 用户登录 / 退出
- JWT 鉴权
- 路由守卫
- 普通用户工作台
- 多图上传
- 同步扫描转多页 PDF
- 账户页修改密码
- 管理员用户列表
- 管理员切换角色
- 管理员启用 / 禁用用户

当前 V1 明确没有实现：

- 扫描历史
- 刷新令牌
- 异步任务队列
- 邮箱验证
- 找回密码
- 文件长期存储
- Redis、MQ、Nginx

## 界面设计思路

前端不是传统蓝灰后台风格，而是做成更偏“纸张 / 出版物 / 文档工作台”的视觉语言：

- 公共首页偏品牌展示，强调第一屏的气质和记忆点
- 登录注册页延续首页色调，但收束到表单本身
- 登录后的工作区回到工具化布局，保证操作效率
- 管理员页尽量克制，用表格和工具栏作为主信息组织方式

这套设计的核心不是炫技，而是让你能看到“展示页”和“业务页”如何共用一套设计 token，又不互相打架。

## 架构概览

项目采用前后端分离架构：

```text
Vue SPA  <----HTTP / JSON / Blob---->  Flask API  <----SQLAlchemy---->  MySQL
                                             |
                                             └---- OpenCV / Pillow ----> PDF
```

### 前端职责

- 提供页面路由和导航
- 管理 token 和当前用户状态
- 上传图片并处理下载 PDF 的交互
- 在页面层做权限入口控制

### 后端职责

- 处理注册、登录、获取当前用户、修改密码
- 校验 JWT
- 控制管理员权限
- 接收图片上传
- 执行扫描增强与 PDF 生成
- 管理数据库中的用户数据

## 目录结构

```text
flask_study/
├─ docs/
│  └─ superpowers/
│     └─ plans/
├─ frontend/
│  ├─ public/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ router/
│  │  ├─ stores/
│  │  ├─ styles/
│  │  └─ views/
│  ├─ package.json
│  ├─ package-lock.json
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
│  │  └─ services/
│  ├─ tests/
│  ├─ requirements.txt
│  ├─ run.py
│  └─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## 后端代码怎么读

如果你想借这个项目学习 Flask，我建议按下面顺序阅读：

1. [backend/app/__init__.py](/D:/work/2026/code/life/flask_study/backend/app/__init__.py)
   这里是应用工厂，能看清 Flask 应用是怎么创建、怎么注册扩展、怎么挂 Blueprint 的。

2. [backend/app/core/config.py](/D:/work/2026/code/life/flask_study/backend/app/core/config.py)
   这里集中管理环境变量和基础配置，能帮助你理解为什么不要把 `os.getenv` 散落在业务代码里。

3. [backend/app/auth/decorators.py](/D:/work/2026/code/life/flask_study/backend/app/auth/decorators.py)
   这里是认证和管理员权限控制的关键入口，能看懂“受保护接口”是怎么实现的。

4. [backend/app/api/auth.py](/D:/work/2026/code/life/flask_study/backend/app/api/auth.py)
   这里能看到注册、登录、获取当前用户、修改密码等最典型的 REST 写法。

5. [backend/app/services/user_service.py](/D:/work/2026/code/life/flask_study/backend/app/services/user_service.py)
   这里是业务逻辑层，适合学习为什么 API 层应该尽量保持轻薄。

6. [backend/app/api/scan.py](/D:/work/2026/code/life/flask_study/backend/app/api/scan.py)
   这里是上传接口，负责收文件、交给扫描服务处理、把 PDF 返回给前端。

7. [backend/app/scanner/service.py](/D:/work/2026/code/life/flask_study/backend/app/scanner/service.py)
   这里是上传文件到扫描流程之间的中间层，体现“HTTP 层”和“处理层”的解耦。

8. [backend/app/scanner/pipeline.py](/D:/work/2026/code/life/flask_study/backend/app/scanner/pipeline.py)
   这里是图像处理核心：边缘检测、轮廓查找、透视变换、自适应阈值和 PDF 合成。

## 前端代码怎么读

如果你想借这个项目学习 Vue 3 + Pinia + Router，我建议按下面顺序阅读：

1. [frontend/src/main.ts](/D:/work/2026/code/life/flask_study/frontend/src/main.ts)
   先看入口，理解为什么要先挂 Pinia 再挂 Router。

2. [frontend/src/router/index.ts](/D:/work/2026/code/life/flask_study/frontend/src/router/index.ts)
   这里是权限路由守卫的核心，可以学到公开页、登录页、受保护页、管理员页之间的控制方式。

3. [frontend/src/stores/auth.ts](/D:/work/2026/code/life/flask_study/frontend/src/stores/auth.ts)
   这里是前端登录态的核心，包含 token 的保存、恢复、清理，以及 `bootstrap` 初始化逻辑。

4. [frontend/src/api/client.ts](/D:/work/2026/code/life/flask_study/frontend/src/api/client.ts)
   这里能看懂为什么要用 Axios 拦截器统一挂 token、统一做错误处理。

5. [frontend/src/stores/scan.ts](/D:/work/2026/code/life/flask_study/frontend/src/stores/scan.ts)
   这里能看到文件队列、上传状态、错误信息和下载链接是如何被组织起来的。

6. [frontend/src/views/HomeView.vue](/D:/work/2026/code/life/flask_study/frontend/src/views/HomeView.vue)
   这里是公开首页，适合看视觉结构和信息层次怎么搭。

7. [frontend/src/views/WorkspaceView.vue](/D:/work/2026/code/life/flask_study/frontend/src/views/WorkspaceView.vue)
   这里是业务核心页，最适合串起“上传 -> 请求 -> 结果 -> 下载”的完整前端流程。

8. [frontend/src/views/admin/UsersAdminView.vue](/D:/work/2026/code/life/flask_study/frontend/src/views/admin/UsersAdminView.vue)
   这里可以看到管理员页如何和后端权限接口对接。

## 扫描转 PDF 流程

用户上传图片后，整条链路大致如下：

1. 前端把文件放进 `FormData`
2. 请求 `POST /api/scan`
3. 后端把上传文件临时保存到临时目录
4. 用 OpenCV 做边缘检测和四边形文档轮廓查找
5. 如果找到了文档边缘，就做透视矫正
6. 再做灰度化和自适应阈值处理，生成更适合阅读/打印的效果
7. 所有处理后的图片按顺序合成一个多页 PDF
8. 直接以二进制流形式返回给前端
9. 前端创建 `blob url`，生成下载链接

当前扫描算法偏向教学和可读性，不追求最复杂的工业级识别精度，但已经足够展示文档扫描的典型技术路线。

## API 概览

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PATCH /api/auth/password`

### Scan

- `POST /api/scan`

### Admin

- `GET /api/admin/users`
- `PATCH /api/admin/users/:id/status`
- `PATCH /api/admin/users/:id/role`

### Health

- `GET /api/health`

## 环境变量

项目根目录使用 `.env`：

```env
MYSQL_DATABASE=scan_pdf
MYSQL_USER=scan_user
MYSQL_PASSWORD=scan_pass
MYSQL_ROOT_PASSWORD=root_pass
MYSQL_HOST=mysql
MYSQL_PORT=3306
JWT_SECRET_KEY=change-me
FLASK_ENV=development
FLASK_APP=run.py
VITE_API_BASE_URL=http://localhost:5000
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123456
```

默认管理员会在后端首次启动时自动补齐：

- 用户名：`admin`
- 密码：`admin123456`

## 本地运行

### 方式一：Docker Compose

1. 复制环境变量文件

```powershell
Copy-Item .env.example .env
```

2. 启动服务

```powershell
docker compose up --build
```

3. 打开页面

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端健康检查：[http://localhost:5000/api/health](http://localhost:5000/api/health)

### 方式二：分别启动

#### 前端

```powershell
cd frontend
npm install
npm run dev
```

#### 后端

```powershell
cd backend
python -m pip install -r requirements.txt
python run.py
```

> 注意：后端默认使用 MySQL 连接串。如果你本地不走 Docker，需要自行准备 MySQL，或者在开发阶段换成测试数据库配置。

## 已完成的验证

当前仓库已经完成过这些验证：

- 前端依赖安装完成
- 前端生产构建通过：`npm run build`
- 后端源码语法校验通过：`python -m compileall backend`
- `docker compose config` 通过，Compose 配置结构正确

由于当前机器环境里存在 Python 出站代理异常，以及 Docker Desktop 引擎未正常启动，后端 `pytest` 与整套 `docker compose up` 的运行验证还依赖你本机环境配合。

## 适合继续扩展的方向

如果你准备继续把这个项目往下做，可以按下面的顺序扩展：

1. 增加扫描历史记录
2. 增加文件长期存储
3. 增加刷新令牌
4. 增加异步任务队列与处理进度
5. 增加用户资料页和头像
6. 增加更强的扫描检测策略
7. 补齐更系统的后端测试和前端组件测试

## 为什么注释比较多

这个仓库的目标之一就是“可学习”。所以很多关键文件里都故意写了较详细的中文注释，尤其是：

- Flask 应用工厂
- JWT 和权限装饰器
- 前端路由守卫
- Pinia 登录态管理
- 上传与扫描状态流转
- 视觉 token 的设计意图

如果你是第一次系统接触这类项目，建议一边看注释，一边顺着接口调用和页面跳转实际跑一遍，理解会比只看代码快很多。
