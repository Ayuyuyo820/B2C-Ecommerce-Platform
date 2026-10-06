# B2C 电商平台

使用 Vue 3、Django REST Framework、MySQL 和 Redis 的前后端分离商城练习项目。

支持用户注册与登录、商品浏览、收货地址、购物车、订单、评价，以及商家商品和订单管理、管理员商品审核与用户管理。支付接口只模拟订单状态变更。

公开源码不包含数据库记录、上传图片或现成账号。数据库迁移文件用于创建空表；接口文档中的账号、联系方式和地址均为演示数据。

## 项目结构

```text
practice/               Django 项目，manage.py 位于此处
  apps/users/           用户、商品、订单等业务模块
  apps/users/migrations/数据库结构迁移
  apps/common/          分页、异常处理和缓存序列化
mall-frontend/          Vue 前端
docs/                   接口文档、问题清单和项目笔记
.env.example            本地配置模板
requirements.txt        后端依赖
```

## 本地运行

准备 Python 3.12、Node.js 20 或更高版本、MySQL 和 Redis。后端核心依赖版本记录在 `requirements.txt`，前端版本由 `package-lock.json` 锁定。复制项目后重新创建虚拟环境，不使用从其他目录复制的 `.venv`。

### 1. 安装后端依赖

在项目根目录执行以下 PowerShell 命令：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

编辑根目录的 `.env`，把生成的新密钥填入 `DJANGO_SECRET_KEY`，并填写自己的数据库账号、密码及 Redis 配置。模板里的占位符必须替换，真实 `.env` 已被 Git 忽略。

Django 会通过 [python-dotenv](https://github.com/theskumar/python-dotenv#readme) 自动读取根目录的 `.env`。操作系统中已经设置的环境变量优先。未配置有效密钥时，后端会给出明确错误。

### 2. 准备 MySQL 和 Redis

在自己的 MySQL 中创建空数据库，例如：

```sql
CREATE DATABASE mall CHARACTER SET utf8mb4;
```

为本地开发账号授予这个数据库的访问权限，并在 `.env` 中填写对应的 `DB_USER` 和 `DB_PASSWORD`。启动本地 Redis；示例配置使用 `127.0.0.1:6379` 的 1 号库。若 Redis 需要密码，填写 `REDIS_PASSWORD`。

如果 MySQL 的认证方式提示缺少 `cryptography`，在虚拟环境中安装 `PyMySQL[rsa]` 后重试。

### 3. 初始化数据库并启动后端

```powershell
Set-Location practice
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

`createsuperuser` 创建本项目的 `superadmin` 角色，用于前端管理页面；本项目没有启用 Django 自带的 `/admin/` 页面。请自行设置账号和密码。

新数据库没有商品和分类。可以在另一个终端进入 `practice` 后，先创建一个演示分类：

```powershell
..\.venv\Scripts\python.exe manage.py shell -c "from apps.users.models import ProductCategories; ProductCategories.objects.get_or_create(name='演示分类')"
```

前端注册商家账号后，可以添加商品；管理员审核后，商品才会出现在用户商品列表中。上传图片会保存到本地 `practice/media/`，这个目录不加入 Git。

### 4. 启动前端

在新的终端进入 `mall-frontend`：

```powershell
npm ci
npm run dev
```

打开终端显示的前端地址，默认是 `http://localhost:3000`。开发代理会把 `/api` 和 `/media` 请求转发到后端 `http://127.0.0.1:8000`。发布前端构建可使用 `npm run build`。
