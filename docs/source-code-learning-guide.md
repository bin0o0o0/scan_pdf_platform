# Scan PDF Platform 源码导读

## 1. 这份导读怎么用

这份文档的目标不是把所有代码逐行解释一遍，而是帮你按**最适合学习的顺序**读懂这个项目。

建议你边看边做三件事：

1. 打开对应源码文件，对照这里的说明往下读。
2. 尝试在脑子里回答“这一层负责什么，不负责什么”。
3. 每看完一个阶段，就自己把调用链复述一遍。

这个项目适合按下面 4 条主线学习：

- 应用如何启动
- 登录和权限如何工作
- 扫描转 PDF 如何工作
- 前端如何把整条链路串起来

---

## 2. 先建立全局地图

先看项目目录：

- `backend/`：Flask 后端
- `frontend/`：Vue 3 前端
- `docs/`：方案与学习文档
- `scripts/`：本机启动脚本
- `docker-compose.yml`：前后端和 MySQL 的容器编排

如果你第一次接触这种前后端分离项目，可以先建立一个简单认知：

- 前端负责页面、交互、发请求、接收结果
- 后端负责鉴权、权限、调用扫描算法、返回 PDF
- MySQL 负责保存用户账号和角色

---

## 3. 第一阶段：先看“项目是怎么启动起来的”

这一阶段只看入口，不急着深入业务。

### 3.1 后端入口

先看：

- `backend/run.py`
- `backend/app/__init__.py`

你要重点理解这几个点：

- `run.py` 只是启动 Flask 的最外层入口
- 真正创建应用的是 `create_app()`
- `create_app()` 里完成了：
  - 加载配置
  - 初始化扩展
  - 注册蓝图
  - 建表
  - 初始化默认管理员

这里对应菜鸟教程里的几个基础概念：

- `Flask(__name__)`：创建应用对象
- 路由：这里没有直接写在 `app` 上，而是拆到了 Blueprint
- 配置：通过 `app.config` 统一管理

### 3.2 前端入口

再看：

- `frontend/src/main.ts`
- `frontend/src/App.vue`

这里重点理解：

- `main.ts` 是 Vue 应用入口
- 它把根组件、Pinia、Router、全局样式串起来
- `App.vue` 很薄，主要就是渲染路由页面

你看完这一阶段后，应该能回答：

- 后端是谁创建的
- 前端是谁挂载到页面上的
- 为什么入口文件通常都很薄

---

## 4. 第二阶段：先把后端“骨架层”看懂

这一阶段不急着看扫描算法，先看 Flask 项目的基础结构。

### 4.1 配置层

看：

- `backend/app/core/config.py`

重点理解：

- 配置为什么集中放在一个类里
- JWT、MySQL、上传大小这些参数为什么都放配置里
- `Config` 和 `TestConfig` 的区别

你要特别注意：

- 开发、测试、生产的配置往往不一样
- 测试环境这里改成了 SQLite，更轻，更适合跑自动化测试

### 4.2 扩展层

看：

- `backend/app/db/extensions.py`

重点理解：

- `db = SQLAlchemy()`
- `jwt = JWTManager()`
- `cors = CORS()`

这类写法的核心思想是：

- 先创建扩展对象
- 再在 `create_app()` 里调用 `init_app(app)`

这就是常见的 Flask “扩展延迟绑定”模式。

### 4.3 错误处理层

看：

- `backend/app/core/errors.py`

重点理解：

- `ApiError` 是什么
- 为什么要统一注册错误处理器
- 为什么前端收到的错误要尽量保持统一格式

你可以把这一层理解成：

- 正常流程走正常返回
- 出错时统一走这里，最后都变成 `{ "message": "..." }`

---

## 5. 第三阶段：先学“登录与权限”这一条主线

这是最适合拿来练 Flask 分层思维的部分。

建议按这个顺序看：

1. `backend/app/models/user.py`
2. `backend/app/services/user_service.py`
3. `backend/app/auth/decorators.py`
4. `backend/app/api/auth.py`
5. `backend/app/api/admin.py`

### 5.1 先看数据模型

`backend/app/models/user.py`

重点理解：

- 用户表有哪些字段
- `role` 和 `status` 分别解决什么问题
- `to_dict()` 为什么只返回部分字段

这里最重要的意识是：

- 数据库存的是“原始事实”
- API 返回的是“允许前端看到的字段”

### 5.2 再看用户服务层

`backend/app/services/user_service.py`

这是非常值得慢慢读的文件，因为它体现了“把业务逻辑从接口层抽出去”的思想。

重点函数：

- `hash_password()`：密码哈希
- `verify_password()`：密码校验
- `validate_username_and_password()`：参数校验
- `create_user()`：注册
- `authenticate_user()`：登录校验
- `update_password()`：改密码
- `update_user_role()`：改角色
- `update_user_status()`：改状态

学习重点：

- 为什么密码不能明文存库
- 为什么参数校验不要散落在很多接口里
- 为什么“最后一个管理员不能被降权或禁用”

### 5.3 再看鉴权装饰器

`backend/app/auth/decorators.py`

这是理解 Flask 权限控制的关键文件。

重点理解：

- `current_user_required`
- `admin_required`
- `g.current_user`

这一层做的事是：

- 校验 token
- 根据 token 里的用户 id 去查数据库
- 检查账号是否可用
- 把当前用户挂到 `g` 上，供后续接口使用

这是一个典型的“把重复逻辑抽成装饰器”的例子。

### 5.4 最后看认证接口

`backend/app/api/auth.py`

重点理解四个接口：

- `POST /register`
- `POST /login`
- `GET /me`
- `PATCH /password`

建议你每个接口都按这个模板理解：

1. 请求进来拿什么参数
2. 调了哪个 service
3. 返回了什么 JSON

### 5.5 再看管理员接口

`backend/app/api/admin.py`

重点理解：

- 为什么管理员接口要额外套 `@admin_required`
- 为什么这里主要做“接口编排”，而不是堆很多业务逻辑

你看到这里时，应该已经能把“注册 -> 登录 -> 获取当前用户 -> 管理员修改用户”这条链路完整复述出来。

---

## 6. 第四阶段：学习“扫描转 PDF”这一条主线

这一条线建议按“先易后难”的顺序读：

1. `backend/app/api/scan.py`
2. `backend/app/scanner/service.py`
3. `backend/app/scanner/pipeline.py`

### 6.1 先看扫描接口

`backend/app/api/scan.py`

重点理解：

- 为什么文件上传要用 `request.files`
- 为什么前端字段名约定成 `files[]`
- 为什么用 `TemporaryDirectory`
- 为什么最后用 `send_file` 直接返回 PDF

这部分对应菜鸟教程里“请求对象、文件上传、响应返回”的基础能力。

### 6.2 再看 scanner service

`backend/app/scanner/service.py`

这个文件的作用是承上启下：

- 向上连接 Flask 接口
- 向下连接真正的图像处理 pipeline

重点理解：

- 为什么先验证文件后缀
- 为什么逐张保存再逐张处理
- 为什么 service 层比直接把逻辑写死在接口里更好维护

### 6.3 最后看图像处理 pipeline

`backend/app/scanner/pipeline.py`

这是整个项目最难的一块，建议最后看。

不要一上来试图全部看懂，先按模块理解：

- 文档轮廓检测
- 四点透视变换
- 背景清理与增强
- 页面排版到 A4
- 多图合成 PDF

你可以把它想成一个流水线：

1. 找纸张
2. 拉正纸张
3. 清理背景
4. 调整成适合阅读和打印的页面
5. 合并成 PDF

如果这一层看着吃力，很正常。你可以先结合测试文件一起看。

---

## 7. 第五阶段：再回到前端，理解“页面怎么把后端串起来”

前端建议按这个顺序读：

1. `frontend/src/router/index.ts`
2. `frontend/src/api/client.ts`
3. `frontend/src/api/auth.ts`
4. `frontend/src/api/scan.ts`
5. `frontend/src/stores/auth.ts`
6. `frontend/src/stores/scan.ts`
7. `frontend/src/views/*.vue`
8. `frontend/src/components/*.vue`

### 7.1 先看路由

`frontend/src/router/index.ts`

重点理解：

- 哪些页面是公开页
- 哪些页面必须登录
- 哪些页面必须管理员
- `beforeEach()` 在做什么

这一层最重要的作用是：

- 页面跳转之前先做权限判断

### 7.2 再看 API 层

看：

- `frontend/src/api/client.ts`
- `frontend/src/api/auth.ts`
- `frontend/src/api/scan.ts`
- `frontend/src/api/admin.ts`

重点理解：

- 为什么要有统一的 `apiClient`
- token 是怎么自动加到请求头里的
- 为什么上传文件要用 `FormData`
- 为什么下载 PDF 要用 `Blob`

### 7.3 再看状态管理

看：

- `frontend/src/stores/auth.ts`
- `frontend/src/stores/scan.ts`

这两个文件是前端最值得精读的部分。

`auth store` 重点理解：

- token 放在哪里
- `bootstrap()` 为什么存在
- 页面刷新后怎么恢复登录态
- `isAuthenticated` 和 `isAdmin` 是怎么计算出来的

`scan store` 重点理解：

- 已选文件怎么保存
- 提交时为什么先清理旧结果
- 为什么 `createObjectURL()` 后要记得 `revokeObjectURL()`

### 7.4 最后看页面和组件

建议先看页面，再看组件：

- `frontend/src/views/HomeView.vue`
- `frontend/src/views/LoginView.vue`
- `frontend/src/views/WorkspaceView.vue`
- `frontend/src/views/AccountView.vue`
- `frontend/src/views/admin/UsersAdminView.vue`

然后再看组件：

- `frontend/src/components/AppShell.vue`
- `frontend/src/components/AuthCard.vue`
- `frontend/src/components/FileUploadPanel.vue`
- `frontend/src/components/UserAdminTable.vue`
- `frontend/src/components/BrandMark.vue`

页面负责：

- 组织数据流
- 调 store
- 触发 API

组件负责：

- 把界面拆小
- 提高复用性

---

## 8. 第六阶段：一定要结合测试来看

很多同学读项目会忽略测试，但这个项目非常适合把测试当“说明书”来读。

建议顺序：

1. `backend/tests/test_auth_api.py`
2. `backend/tests/test_admin_api.py`
3. `backend/tests/test_scan_api.py`
4. `backend/tests/test_scan_pipeline.py`
5. `backend/tests/conftest.py`

你可以把测试理解成：

- 这个项目最重要的行为保证了什么
- 作者希望这些接口和算法至少满足什么条件

尤其是：

- 权限接口怎么测
- 扫描接口怎么测
- 图像处理算法怎么测

这会帮助你把“代码怎么写”和“代码应该保证什么”联系起来。

---

## 9. 推荐的源码学习顺序

如果你只想按一条最顺的路线走，直接按这个顺序：

1. `backend/run.py`
2. `backend/app/__init__.py`
3. `backend/app/core/config.py`
4. `backend/app/db/extensions.py`
5. `backend/app/core/errors.py`
6. `backend/app/models/user.py`
7. `backend/app/services/user_service.py`
8. `backend/app/auth/decorators.py`
9. `backend/app/api/auth.py`
10. `backend/app/api/admin.py`
11. `backend/app/api/scan.py`
12. `backend/app/scanner/service.py`
13. `backend/app/scanner/pipeline.py`
14. `frontend/src/main.ts`
15. `frontend/src/router/index.ts`
16. `frontend/src/api/client.ts`
17. `frontend/src/stores/auth.ts`
18. `frontend/src/stores/scan.ts`
19. `frontend/src/views/LoginView.vue`
20. `frontend/src/views/WorkspaceView.vue`
21. `backend/tests/test_auth_api.py`
22. `backend/tests/test_admin_api.py`
23. `backend/tests/test_scan_api.py`
24. `backend/tests/test_scan_pipeline.py`

---

## 10. 每一轮学习时，你可以问自己的问题

### 看后端时

- 这个函数是接口层、服务层，还是底层工具层？
- 这个逻辑为什么不直接写在路由里？
- 这个错误应该在哪里处理最合理？

### 看前端时

- 这段状态应该放页面里，还是放 store 里？
- 这段逻辑是界面逻辑，还是请求逻辑？
- 这里为什么要用路由守卫，而不是进页面后再判断？

### 看扫描算法时

- 输入是什么
- 输出是什么
- 中间每一步在修正什么问题

---

## 11. 你现在最适合的实操方式

建议你按下面的节奏学：

1. 先读一小段源码
2. 本地跑起来点一下页面或接口
3. 再回头看对应测试
4. 最后自己改一个小点验证理解

最推荐你动手改的练习：

- 把密码长度从 6 改成 8
- 给用户列表加一个按用户名排序选项
- 给上传文件列表加一个“移动顺序”按钮
- 给首页再补一个产品说明区块

这些改动都不大，但会逼着你真正走一遍“前端 -> 后端 -> 测试”的链路。

---

## 12. 最后一句建议

不要一开始就试图把 `pipeline.py` 全看懂。

这个项目最值得你先吃透的，不是图像算法，而是这套非常标准的全栈结构：

- Flask 应用工厂
- Blueprint 路由拆分
- Service 分层
- JWT 鉴权
- Vue Router + Pinia + API Client 的前端组织方式

等这套结构你吃透了，再回头看扫描算法，理解速度会快很多。
