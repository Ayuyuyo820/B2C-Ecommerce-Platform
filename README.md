# B2C 电商平台

一个使用 **Vue 3 + Django REST Framework + MySQL + Redis** 构建的前后端分离商城项目，覆盖商品浏览、购物车、订单、评价，以及商家和管理员的运营流程。

适合用于学习商城业务、阅读前后端源码和本地运行体验。当前支付功能为模拟支付，仅变更订单状态。

## 项目功能

| 角色 | 主要功能 |
| --- | --- |
| 普通用户 | 注册与登录、浏览和搜索商品、管理个人资料与收货地址、购物车、下单与模拟支付、确认收货、商品评价 |
| 商家 | 发布和管理商品、查看订单与发货、查看和回复评价 |
| 管理员 | 用户启用与禁用、商品审核、查看订单和销售统计 |
| 超级管理员 | 管理员功能，以及分配用户角色 |

注册页面支持普通用户和商家两种身份。超级管理员通过后端命令创建，普通管理员可由超级管理员分配。

项目使用 JWT 进行身份认证，使用 Redis 缓存商品分类；下单时结合数据库事务、购物车行锁和条件扣减库存处理并发请求。

## 技术栈

| 部分 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Vue Router、Pinia、Axios、Element Plus |
| 后端 | Django、Django REST Framework、Simple JWT |
| 数据存储 | MySQL、Redis |
| 其他 | PyMySQL、django-redis、python-dotenv |

后端依赖见 [requirements.txt](requirements.txt)，前端依赖见 [package.json](mall-frontend/package.json)，安装时使用仓库中的 `package-lock.json` 锁定版本。

## 项目结构

```text
B2C-Ecommerce-Platform/
├── mall-frontend/               Vue 前端
│   ├── src/api/                 API 请求封装
│   ├── src/router/              路由与页面访问控制
│   ├── src/store/               用户状态
│   ├── src/views/               商城、商家和管理员页面
│   └── vite.config.js           开发服务与接口代理
├── practice/                    Django 后端
│   ├── apps/common/             分页、异常处理和缓存序列化
│   ├── apps/users/              用户、商品、订单等业务模块
│   │   └── migrations/          数据库结构迁移
│   ├── practice/settings.py     项目配置
│   ├── practice/urls.py         路由入口
│   └── manage.py                Django 管理命令
├── requirements.txt             后端依赖
└── README.md
```

## 本地运行

准备 Python 3.12、Node.js 20 或更高版本，以及可连接的 MySQL 和 Redis 服务。下面的命令以 **Windows PowerShell** 为例；Linux / macOS 可使用 `python3.12` 创建虚拟环境，并将后续 Python 路径替换为 `.venv/bin/python`。

### 1. 下载项目并安装后端依赖

```powershell
git clone https://github.com/Ayuyuyo820/B2C-Ecommerce-Platform.git
Set-Location B2C-Ecommerce-Platform

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 准备数据库和缓存

在 MySQL 客户端中创建数据库：

```sql
CREATE DATABASE mall CHARACTER SET utf8mb4;
```

准备一个有权访问该数据库、创建和修改表结构的本地开发账号。稍后在 `.env` 中填写这个账号的用户名和密码。

启动 Redis，默认连接地址为 `127.0.0.1:6379`，使用 1 号库。也可以在下面的配置中填写自己的服务地址。

### 3. 创建本地配置

在**项目根目录**新建 `.env` 文件，与 `README.md` 放在同一级目录。将以下内容复制到文件中：

```dotenv
# 替换为下一条命令生成的新密钥
DJANGO_SECRET_KEY=replace-with-a-new-random-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# 填写自己的 MySQL 连接信息
DB_NAME=mall
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Redis 配置；本地服务没有密码时，REDIS_PASSWORD 留空
REDIS_URL=redis://127.0.0.1:6379/1
REDIS_PASSWORD=
REDIS_KEY_PREFIX=mall
```

在项目根目录执行以下命令生成密钥，将输出填入 `DJANGO_SECRET_KEY`：

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

同时替换 `DB_USER`、`DB_PASSWORD`，并按需要调整 MySQL 和 Redis 的连接信息。以上配置用于本地开发。

后端会自动加载根目录的 `.env`；已经设置的操作系统环境变量优先。`.env` 已被 Git 忽略，请将真实密钥和密码保存在本地。

### 4. 初始化数据库和管理员账号

```powershell
Set-Location practice

..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser
```

按提示输入用户名、手机号、邮箱和密码。这个账号的角色为 `superadmin`，可登录前端管理员页面。

新数据库中没有商品和分类。首次体验时，可先创建一个分类：

```powershell
..\.venv\Scripts\python.exe manage.py shell -c "from apps.users.models import ProductCategories; ProductCategories.objects.get_or_create(name='演示分类')"
```

### 5. 启动后端

在 `practice` 目录执行，并保持此终端运行：

```powershell
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

后端 API 的基础地址为 `http://127.0.0.1:8000/api/v1/`。

### 6. 启动前端

打开新的终端，从项目根目录进入 `mall-frontend`：

```powershell
Set-Location mall-frontend
npm ci
npm run dev
```

打开终端显示的地址，默认是 **http://localhost:3000**。前端开发服务会将 `/api` 和 `/media` 请求转发到 `http://127.0.0.1:8000`。

生成前端构建产物：

```powershell
npm run build
```

构建文件输出到 `mall-frontend/dist/`。

## 首次体验流程

仓库不包含现成账号、商品数据或上传图片。完成迁移、创建管理员和分类后，可按以下顺序体验：

1. 打开注册页面，选择“商家（卖家）”并注册账号。
2. 登录商家账号，进入“商品管理”，添加商品、图片、价格和库存。
3. 退出商家账号，使用之前创建的超级管理员账号登录，进入“商品审核”并通过审核。
4. 注册并登录普通用户账号，浏览商品、填写收货地址、加入购物车并下单。
5. 使用模拟支付，切换商家账号发货，再由买家确认收货并评价。
6. 切换商家账号查看并回复评价，或使用管理员账号查看用户和销售统计。

上传文件会保存到本地 `practice/media/`，运行时由 Django 在开发模式下提供访问。

## 常见问题

**启动时提示需要配置 `DJANGO_SECRET_KEY`**

确认 `.env` 位于项目根目录，而不是 `practice` 目录，并已将密钥占位符替换为生成的值。在 Windows 下检查文件名是否误写成 `.env.txt`。

**数据库连接失败或提示没有权限**

检查 MySQL 是否运行、数据库是否存在，以及 `DB_HOST`、`DB_PORT`、账号、密码和授权是否一致。如果提示认证需要 `cryptography`，在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pip install "PyMySQL[rsa]==1.2.0"
```

**分类加载失败，提示无法连接 Redis**

确认 Redis 服务已启动，检查 `REDIS_URL` 和 `REDIS_PASSWORD`。分类接口依赖 Redis 缓存。

**商品列表为空**

新数据库没有预置商品。需要先创建分类，再由商家添加商品，并由管理员审核上架。

**访问后端 `/admin/` 时返回 404**

管理员通过前端运营页面管理商城，例如 `http://localhost:3000/admin/users`。项目未启用 Django 自带的后台页面。

**商品图片无法显示**

确认后端已启动、本地上传文件存在，以及开发配置中的 `DJANGO_DEBUG=True`；前端通过 `/media` 代理访问上传图片。
