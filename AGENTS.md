# Project Agent Notes

## 背景与结论

这个项目的后端环境，实际遇到的核心问题只有两个：

1. Windows 系统代理指向了 `127.0.0.1:7890`，但代理程序并没有稳定运行。
   结果是 `pip` 会自动读取系统代理，随后在装依赖时失败。

2. MySQL 8.4 默认使用 `caching_sha2_password` 鉴权。
   `PyMySQL` 在这种模式下需要额外安装 `cryptography`，否则 Docker 里的后端会启动失败并进入重启循环。

结论是：

- 本机 Python 依赖安装要主动绕过失效代理
- Docker 后端镜像必须包含 `cryptography`
- 本机直跑 Flask 时，数据库主机不能继续使用容器内服务名 `mysql`

## 最短成功路径

如果目标只是把后端环境最快跑通，按下面顺序做，不要先自己改全局代理，不要先改数据库配置文件。

### 方式一：Windows 本机直跑

在项目根目录执行：

```powershell
.\scripts\backend-bootstrap.ps1
docker compose up -d mysql
.\scripts\backend-run.ps1
```

成功标志：

- 访问 `http://localhost:5000/api/health`
- 返回：

```json
{
  "checks": {
    "database": "ok"
  },
  "status": "ok"
}
```

### 方式二：Docker 运行

在项目根目录执行：

```powershell
docker compose up --build -d mysql backend
```

成功标志：

- `docker compose ps` 里 `mysql` 是 `healthy`
- `backend` 是 `Up`
- `http://localhost:5000/api/health` 返回 `status=ok`

## 当前推荐的拉起流程

截至这次排查，项目里最稳、最省事、最适合本机测试的组合是：

- `mysql` 用 Docker
- `backend` 在 Windows 主机本机运行
- `frontend` 在 Windows 主机本机运行

原因很简单：

- MySQL 用 Docker 最省心，数据和初始化都稳定
- 后端本机运行时，已经有现成脚本自动绕过失效代理并改用 `127.0.0.1:3306`
- 前端本机 `vite` 直跑最稳，避免 Docker Desktop 在 `5173` 端口转发上偶发异常

### 启动步骤

在项目根目录执行：

```powershell
.\scripts\backend-bootstrap.ps1
docker compose up -d mysql
Start-Process powershell -ArgumentList '-ExecutionPolicy','Bypass','-File','.\\scripts\\backend-run.ps1'
Start-Process powershell -ArgumentList '-NoProfile','-Command','Set-Location .\\frontend; npm run dev'
```

### 访问地址

- 前端：http://localhost:5173
- 后端健康检查：http://localhost:5000/api/health

### 验证顺序

建议按这个顺序确认服务是否真的起来：

1. 打开 `http://localhost:5000/api/health`
2. 确认返回 `status=ok`
3. 打开 `http://localhost:5173`
4. 确认页面标题是 `Scan PDF Platform`

### 停止方式

如果只是结束当前测试，按下面方式停：

```powershell
Get-NetTCPConnection -LocalPort 5000,5173 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique
docker compose stop mysql
```

注意：

- `5000` 和 `5173` 通常是本机 Python / Node 进程，不是容器
- `mysql` 则是 Docker 容器
- 如果只停 Docker，不停本机进程，页面和接口可能还会继续响应

## 两种运行方式的区别

### 本机直跑

本机直跑使用：

- [scripts/backend-bootstrap.ps1](D:/work/2026/code/life/flask_study/scripts/backend-bootstrap.ps1)
- [scripts/backend-run.ps1](D:/work/2026/code/life/flask_study/scripts/backend-run.ps1)

这两个脚本已经帮你做了三件事：

- 仅在当前 PowerShell 进程内清掉代理影响
- 用 Python 3.11 创建 `.venv`
- 本机运行 Flask 时，把数据库主机改成 `127.0.0.1:3306`

### Docker 运行

Docker 方式依赖：

- [docker-compose.yml](D:/work/2026/code/life/flask_study/docker-compose.yml)
- [backend/requirements.txt](D:/work/2026/code/life/flask_study/backend/requirements.txt)

这里要特别记住：

- Compose 里的 `MYSQL_HOST=mysql` 是正确的
- 这个 `mysql` 只对容器网络有效
- 对 Windows 主机本身无效

## 注意事项

### 1. 不要先改全局代理

这次已经验证过，真正的问题不是“必须删掉系统代理”，而是“pip 会继承系统代理，而该代理当前不可用”。

项目内最稳的做法是：

- 用 `backend-bootstrap.ps1`
- 用 `backend-run.ps1`
- 让脚本只影响当前终端进程

不要把这类问题第一反应写成“去控制面板删代理配置”。

### 2. 本机与 Docker 不能共用同一套数据库主机名

根目录 `.env` 里的：

```env
MYSQL_HOST=mysql
```

这是给 Compose 容器用的，不是给 Windows 本机进程用的。

如果直接在本机执行：

```powershell
cd backend
python run.py
```

很容易报这类错误：

```text
Can't connect to MySQL server on 'mysql'
getaddrinfo failed
```

所以本机运行一定优先走：

```powershell
.\scripts\backend-run.ps1
```

### 3. Docker 后端重启循环时，先看是不是 `cryptography`

如果你看到：

- `docker compose ps` 里 `backend` 一直 `Restarting`
- `mysql` 已经是 `healthy`

优先执行：

```powershell
docker compose logs backend --tail=200
```

如果日志里出现：

```text
'cryptography' package is required for sha256_password or caching_sha2_password auth methods
```

说明不是数据库没起来，而是镜像缺依赖。

### 4. 本机直跑后，Flask 调试重载可能留下残留进程

本机运行 `run.py` 时，Flask 调试模式会触发重载器。
如果你是外部 `Start-Process` 拉起，再强杀父进程，可能会留下一个监听 `5000` 的 Python 子进程。

表现通常是：

- 你以为现在访问的是 Docker 后端
- 实际上占用 `5000` 的还是本机残留 Python 进程

排查命令：

```powershell
Get-NetTCPConnection -LocalPort 5000 -State Listen
Get-Process -Id <OwningProcess>
docker port flask_study-backend-1
```

### 5. 优先使用 Python 3.11

当前项目在这台机器上已经验证通过的解释器是：

- `D:\python3.11\python.exe`

不要默认继续使用旧的 `Python 3.9.5`，尤其是在新建虚拟环境时。

## 推荐排错顺序

以后如果另一个 agent 接手这个项目，后端环境问题请按这个顺序排查，不要跳步：

1. 先看 `http://localhost:5000/api/health` 是否可访问
2. 如果不可访问，先看 `docker compose ps`
3. 如果 `backend` 在重启，立刻看 `docker compose logs backend --tail=200`
4. 如果是本机安装依赖失败，先怀疑系统代理，不要先怀疑清华源
5. 如果是本机 Flask 启动失败，先检查是不是还在用 `MYSQL_HOST=mysql`
6. 如果端口状态异常，检查 `5000` 是否被残留 Python 进程占用

## 当前已验证通过的命令

下面这些命令在这个项目里已经实际跑通过：

```powershell
.\scripts\backend-bootstrap.ps1
.\.venv\Scripts\python.exe -m pytest backend\tests -q
docker compose up --build -d mysql backend
.\scripts\backend-run.ps1
```

其中测试结果是：

```text
5 passed
```

## 相关文件

- [AGENTS.md](D:/work/2026/code/life/flask_study/AGENTS.md)
- [scripts/backend-bootstrap.ps1](D:/work/2026/code/life/flask_study/scripts/backend-bootstrap.ps1)
- [scripts/backend-run.ps1](D:/work/2026/code/life/flask_study/scripts/backend-run.ps1)
- [backend/requirements.txt](D:/work/2026/code/life/flask_study/backend/requirements.txt)
- [docker-compose.yml](D:/work/2026/code/life/flask_study/docker-compose.yml)
- [README.md](D:/work/2026/code/life/flask_study/README.md)
