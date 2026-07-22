# MakanReel — AI 短视频内容生成 Portal (Phase 1)

> 对外产品名：**MakanReel**（马来/新马俚语"吃" + Reel 短视频）｜ 内部代号：**NIHAO**
> 为新加坡 180+ 门店餐饮品牌打造的 AI 短视频生成 Web 平台。
> 极简上传 → AI 一键生成爆款视频 → 本地下载与复制文案。

## ✨ 核心能力

- **极简上传**：手机/PC 浏览器扫码即用，1~3 张图片或短视频，原画质传输
- **AI 智能预处理**：谱残差显著性 + 人脸检测做 9:16 智能裁切，CLAHE 画质修复、提饱和、去噪
- **卡点视频合成**：8 套预制模板（Ken Burns / Zoom-In / 快闪 / 滑动等），FFmpeg 卡点拼接 + 花字烧录 + 程序化 BGM
- **本地化文案**：LLM 生成新加坡本地 IG Caption（Shiok! / Refreshing）+ Hashtag 矩阵，无密钥时模板兜底
- **一键导出**：1080×1920 竖屏 MP4 下载 + 文案复制 + 换风格重生

## 🏗 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS（移动端优先） |
| 后端 | Python 3.13 + FastAPI（异步） |
| 视觉 | OpenCV（智能裁切/画质修复）+ YOLOv8（可选增强） |
| 文案 | OpenAI 兼容 LLM（DeepSeek/Gemini/OpenAI）+ 模板兜底 |
| 渲染 | FFmpeg（卡点合成/Ken Burns/花字/BGM） |
| 存储 | 本地文件系统（Phase 2 预留 S3/R2 抽象） |

## 📁 目录结构

```
ai-video-portal/
├── TRD.md                 # 技术需求文档
├── README.md
├── backend/               # FastAPI 后端
│   ├── main.py            # 入口
│   ├── config.py          # 配置
│   ├── models.py          # 数据模型
│   ├── routers/           # 上传/任务/资产/模板路由
│   ├── services/          # 预处理/渲染/文案/任务/BGM 生成
│   ├── templates_data/    # 模板定义 + BGM
│   └── storage/           # 运行时生成（上传/渲染/任务数据）
└── frontend/              # Next.js 前端
    └── src/
        ├── app/           # 页面
        ├── components/    # 上传/进度/结果组件
        └── lib/api.ts     # API 封装
```

## 🚀 快速启动

### 1. 后端

```bash
cd backend
cp .env.example .env          # 按需配置 LLM 密钥（留空则模板兜底）
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
# API 文档: http://localhost:8000/docs
```

### 2. 前端

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# 打开: http://localhost:3000
```

### 3. 使用

1. 手机/PC 打开 `http://localhost:3000`
2. 上传 1~3 张图片，填写产品备注（如「芒果啵啵 买一送一」）
3. 点击「✨ AI 一键生成爆款视频」
4. 预览成品 → 下载 MP4 / 复制 Caption / 换风格重生

## 🔧 配置说明

### LLM 文案（可选）
在 `backend/.env` 配置 OpenAI 兼容接口即可启用真实 AI 文案：
```
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
```
留空 `LLM_API_KEY` 时自动走新加坡本地化模板兜底，系统照常运行。

### YOLO 主体检测（可选）
```
pip install ultralytics
ENABLE_YOLO=true
```
默认用 OpenCV 谱残差显著性做主体定位，无需额外下载。

### BGM 音轨
将卡点音乐 mp3 放入 `backend/templates_data/bgm/`，文件名与模板 `bgm` 字段一致即可。
未提供时自动程序化合成悦耳循环音乐。

## 📡 API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传素材，返回 job_id |
| POST | `/api/jobs/{id}/generate` | 触发生成 |
| GET  | `/api/jobs/{id}` | 查询状态/进度/结果 |
| GET  | `/api/assets/{id}/video` | 下载 MP4 |
| POST | `/api/jobs/{id}/regenerate` | 换风格重生 |
| GET  | `/api/templates` | 模板列表 |

完整文档见 `TRD.md`，交互式 API 文档见 `http://localhost:8000/docs`。

## 🎬 模板库

| ID | 名称 | 时长 | 风格 |
|----|------|------|------|
| summer_cool | 夏日酷炫 | 8s | 活力清凉 |
| zoom_in | 高质感 Zoom-In | 6s | 精致特写 |
| promo_flash | 促销快闪 | 5s | 紧迫高能 |
| ken_burns | 静态微动 | 7s | 电影氛围 |
| fresh_pop | 清新气泡 | 8s | 明亮年轻 |
| night_vibe | 夜间氛围 | 7s | 霓虹暗调 |
| sweet_zoom | 甜蜜聚焦 | 6s | 温暖诱人 |
| energy_burst | 能量爆发 | 8s | 节奏冲击 |

## 🗺 路线图

- **Phase 1（当前）**：极简上传 → AI 生成 → 下载/复制核心闭环 ✅
- **Phase 2**：多模板选择 UI、Instagram Graph API 一键发布、账号体系、云存储 + CDN、Celery 分布式渲染
