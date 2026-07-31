# 线上部署说明

本地助手已支持 gunicorn / Docker。数据仍来自 [ARAM Mayhem](https://arammayhem.com/zh-cn/)，上线请保留来源说明，并控制请求频率（已有本地缓存）。

## 方案一：Render（推荐，免费试用最简单）

1. 把本项目推到 GitHub（只要 `aram-mayhem-helper` 目录，或整仓指定根目录）
2. 打开 [https://render.com](https://render.com) 注册 → **New → Web Service**
3. 连接仓库，设置：
   - **Root Directory**: `aram-mayhem-helper`（若在仓库子目录）
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -b 0.0.0.0:$PORT -w 2 --timeout 60 app:app`
4. 创建后得到类似 `https://xxx.onrender.com` 的地址

免费实例会休眠，冷启动可能要等几十秒。

## 方案二：自己的 Linux 服务器 / 宝塔

```bash
cd /opt
git clone <你的仓库> aram-helper
cd aram-helper/aram-mayhem-helper   # 按实际路径
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
gunicorn -b 127.0.0.1:8765 -w 2 --timeout 60 app:app
```

宝塔里用 **Nginx 反向代理** 到 `127.0.0.1:8765`，并配置 SSL。

或用 Docker：

```bash
docker build -t aram-helper .
docker run -d --name aram-helper -p 8765:8765 --restart unless-stopped aram-helper
```

## 方案三：Railway / Fly.io

同样连接 GitHub，Start Command 用：

```text
gunicorn -b 0.0.0.0:$PORT -w 2 --timeout 60 app:app
```

## 上线后

- 手机/电脑浏览器打开你的域名即可搜外号
- 桌面快捷方式可改成线上地址，不必再开本地黑窗口
- 首次查询某个英雄会稍慢（拉官网并缓存），之后会快很多

## 注意

- 这是非官方工具，依赖第三方站点结构；对方改版可能导致解析失败
- 不要对目标站高频爬取；当前缓存默认约 6 小时
- 若只是自己用，其实本地助手已经够用；上线主要是为了手机随时查、或分享给朋友
