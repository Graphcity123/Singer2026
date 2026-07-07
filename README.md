# Singer2026 — 歌手信息检索系统

清华大学程序设计训练（Python）2026 暑期课程 · 实验一：爬虫与信息检索

基于 Django 的全栈 Web 应用，爬取网易云音乐歌手/歌曲数据，提供浏览、搜索、评论、收藏等社交功能。

## 数据规模

| 数据类型 | 数量 |
|----------|------|
| 歌曲     | 4,718 |
| 歌手     | 1,381 |
| 评论     | 50,717 |
| 图片     | 6,100+ |

## 功能特性

### 浏览与搜索
- 歌曲列表 / 歌手列表（随机排序，分页展示）
- 歌手详情（简介、热门作品、网易云外链）
- 歌曲详情（歌词多栏排版、歌手列表、网易云外链播放器）
- 全站搜索：支持歌手名/简介、歌名/歌手名/歌词匹配，按相关性排序，< 1 秒响应

### 用户系统
- 注册 / 登录 / 登出
- 个人主页：头像上传、个人简介编辑
- 收藏歌曲 / 收藏歌手（主页 tab 切换展示）
- 查看自己的历史评论

### 评论系统
- 在歌曲详情页发布评论
- 登录用户可选择匿名发表
- 点赞 / 取消点赞评论
- 删除自己的评论（管理员可删除任意评论）
- 评论按热度 + 时间排序，分页展示
- 底部固定评论输入栏（毛玻璃效果）

### 管理员功能
- `/manage/users/` 用户活跃统计面板
- 查看任意用户的收藏和评论
- 管理全站评论

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Django 6.0 |
| 数据库 | SQLite3 |
| 前端 | Django Templates + 原生 CSS + SVG 图标 |
| 爬虫 | `requests` + `fake_useragent` + 多线程并发 |
| 部署 | PythonAnywhere（免费账户） |

## 项目结构

```
Singer2026/
├── config/                 # Django 项目配置
│   ├── settings.py         # 数据库、静态文件、中间件等
│   ├── urls.py             # 根路由
│   └── wsgi.py             # WSGI 入口
├── web/                    # Django 应用
│   ├── models.py           # 数据模型（Singer, Song, Comment, ...）
│   ├── views.py            # 视图逻辑
│   ├── urls.py             # 应用路由
│   ├── admin.py            # Django Admin 配置
│   ├── context_processors.py  # 模板上下文（IMAGE_BASE_URL）
│   ├── templates/          # HTML 模板（13 个页面）
│   ├── static/web/         # CSS / 字体 / 图标
│   ├── fixtures/           # JSON 数据备份（loaddata 备用）
│   └── migrations/         # 数据库迁移文件
├── data/                   # 图片 & 爬虫 checkpoint
│   ├── images/             # 歌手/歌曲封面图（6100+）
│   └── crawl_checkpoint.json
├── crawl_hot_songs.py      # 增量爬虫工具
├── consts.py               # 爬虫常量配置
├── list.txt                # 待爬歌手 ID 列表
├── manage.py               # Django CLI 入口
├── requirements.txt        # Python 依赖
└── db.sqlite3              # SQLite 数据库（含全量数据）
```

## 数据模型

| 模型 | 说明 |
|------|------|
| `Singer` | 歌手（name, desc, image_url, source_url, sort_order） |
| `Song` | 歌曲（name, lyrics, image_url, source_url, sort_order），M2M → Singer |
| `Comment` | 评论（user, name, content, song FK, create_time, like_count） |
| `CommentLike` | 点赞记录（user + comment 联合唯一） |
| `FavoriteSong` | 歌曲收藏（user + song 联合唯一） |
| `FavoriteSinger` | 歌手收藏（user + singer 联合唯一） |
| `UserProfile` | 用户扩展资料（avatar, bio），OneToOne → User |

## 快速开始（本地开发）

### 环境要求

- Python 3.12+
- pip

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/Graphcity123/Singer2026.git
cd Singer2026

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt
# 爬虫额外依赖（可选）：
pip install requests fake_useragent

# 4. 数据库（二选一）
# 方式 A：直接使用预置数据库（推荐，含全量数据）
#    确保 db.sqlite3 在项目根目录，直接运行即可

# 方式 B：从 fixture 导入（数据量较小，适合 PythonAnywhere 免费账户）
python manage.py migrate
python manage.py loaddata web/fixtures/singer_fixture.json
python manage.py loaddata web/fixtures/song_fixture.json
python manage.py loaddata web/fixtures/comment_fixture.json

# 5. 启动开发服务器
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 即可使用。

## 爬虫工具

`crawl_hot_songs.py` — 增量爬取网易云音乐热门歌曲。

### 使用方法

```bash
# 1. 在 list.txt 中填入目标歌手 ID（每行一个）
echo "2116" > list.txt    # 示例：陈奕迅
echo "6452" >> list.txt   # 示例：周杰伦

# 2. （推荐）设置 Cookie 以获得更好的访问体验
export NETEASE_COOKIES="你的网易云Cookie"

# 3. 运行爬虫
python crawl_hot_songs.py
```

### 特性

- **增量爬取**：自动跳过已存在的歌曲和歌手
- **Checkpoint 续跑**：中断后可从断点继续，不重复工作
- **多线程并发**：歌手信息、歌词、图片下载均使用线程池
- **自动去重**：基于网易云 ID 检测重复
- 配置项（`consts.py`）：`LEAST_SONG=2000`、`LEAST_SINGER=200`

## 部署

生产环境部署于 **PythonAnywhere**（免费账户）：

- 域名：https://graphcities.pythonanywhere.com
- 数据库：本地 SQLite3 直传（绕过 loaddata 避免 CPU 超限）
- 图片：通过 `IMAGE_BASE_URL` 环境变量指向 GitHub Raw
- 静态文件：PA Static files 映射 `/static/` → `web/static/`

### 关键环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `IMAGE_BASE_URL` | 图片资源根路径 | `https://raw.githubusercontent.com/.../master/data/images/` |
| `DJANGO_SETTINGS_MODULE` | Django 配置模块 | `config.settings` |
| `NETEASE_COOKIES` | 网易云 Cookie（爬虫用） | 从 `.env` 文件加载 |

### PA WSGI 配置

```python
import os
import sys
path = '/home/graphcities/Singer2026'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['IMAGE_BASE_URL'] = 'https://raw.githubusercontent.com/Graphcity123/Singer2026/master/data/images/'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

> **注意**：免费账户有 100s CPU/天的限制，不宜在服务器端执行大量写入操作。

## URL 路由

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | `index` | 首页，重定向到歌曲列表 |
| `/songlist` | `songlist` | 歌曲列表（分页） |
| `/singerlist` | `singerlist` | 歌手列表（分页） |
| `/song/<id>` | `song` | 歌曲详情 + 评论区 |
| `/singer/<id>` | `singer` | 歌手详情 |
| `/search?q=` | `search_view` | 搜索，tab 切换歌手/歌曲 |
| `/register/` | `register_view` | 注册 |
| `/login/` | `login_view` | 登录 |
| `/logout/` | `logout_view` | 登出 |
| `/profile/` | `profile_view` | 个人主页 |
| `/profile/edit/` | `profile_edit` | 编辑资料 |
| `/manage/users/` | `admin_users` | 管理员用户面板 |
| `/comment/<id>/like` | `like_comment` | 点赞/取消评论 |
| `/comment/<id>/delete` | `delete_comment` | 删除评论 |
| `/song/<id>/favorite` | `favorite_song` | 收藏/取消歌曲 |
| `/singer/<id>/favorite` | `favorite_singer` | 收藏/取消歌手 |

## 管理员

- 管理员账号在部署时通过 `python manage.py createsuperuser` 创建
- 可通过 `/manage/users/` 查看全站用户活动统计
- Django Admin 面板：`/admin/`

## 相关链接

- GitHub：https://github.com/Graphcity123/Singer2026
- 在线演示：https://graphcities.pythonanywhere.com
- 课程：清华大学 2026 暑期 · 程序设计训练（Python）

---

*截止日期：2026 年 7 月 13 日*
