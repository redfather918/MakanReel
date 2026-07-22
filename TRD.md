# 技术需求文档 (TRD)

# MakanReel (Phase 1)

> 对外产品名：**MakanReel** ｜ 内部代号：**NIHAO**
> 版本：v1.0 ｜ 对应 PRD：AI 短视频内容生成 Portal (Phase 1)
> 编写日期：2026-07-23

---

## 0. 文档目的

本 TRD 将《产品需求文档 (PRD) 原型：AI 短视频内容生成 Portal (Phase 1)》转化为可落地的技术方案，明确架构选型、模块边界、接口契约、数据模型与部署方式，作为开发团队的实施依据。

**Phase 1 范围（与 PRD 一致）**：极简上传 → AI 一键生成视频 → 本地下载与复制文案的核心闭环，建立基础模板库。不含 IG Graph API 发布、多账号体系。

---

## 1. 技术选型与决策

### 1.1 选型总表

| 架构层 | 选用技术 | 决策理由 |
|--------|----------|----------|
| 前端 | **Next.js 14 (App Router) + TypeScript + Tailwind CSS** | 移动端优先、SSR 首屏快、生态成熟；拖拽上传与视频预览组件齐全 |
| 后端 API & 调度 | **Python 3.13 + FastAPI** | 异步高性能；与 AI/视觉生态 (OpenCV/ultralytics) 同语言，免去跨语言胶水 |
| 对象存储 | **本地文件系统 (Phase 1)** + S3/R2 抽象接口 | 开发期零成本；接口预留，Phase 2 可平滑切到 Cloudflare R2 |
| AI 视觉层 | **OpenCV**（智能裁切 + 画质修复）+ **ultralytics YOLOv8**（主体检测，可选增强） | OpenCV 零模型依赖、稳定可靠；YOLOv8 提升主体识别精度，按需启用 |
| AI 文案层 | **OpenAI 兼容 API**（DeepSeek / Gemini / OpenAI 均可配置）+ 模板兜底 | 统一接口，密钥可配置；无密钥时模板生成，保证可运行 |
| 视频渲染引擎 | **FFmpeg** | 已具备；卡点合成、转场、Ken Burns、字幕烧录一条龙；无第三方付费依赖 |
| 任务队列 | **内存异步 (asyncio + 后台任务)** (Phase 1) | 单机够用；Phase 2 升级 Celery + Redis |
| 字体 | Noto Sans SC / 系统字体 | 花字与字幕渲染，支持中英文 |

### 1.2 关键决策说明

- **为何选 FFmpeg 而非 Remotion/Shotstack**：Remotion 需 React 渲染管线、Shotstack 为付费 API；FFmpeg 本地零成本、对卡点/转场/字幕烧录支持完备，足以覆盖 Phase 1 的 8–10 套模板需求。
- **为何视觉层默认 OpenCV 主导**：YOLOv8 需下载权重文件（~6MB），网络受限环境不可用。Phase 1 默认使用 OpenCV 的显著性检测 (saliency) + 人脸 Haar 级联做主体定位，YOLOv8 作为可选增强开关 (`ENABLE_YOLO=true`)。
- **为何 LLM 层做兜底**：保证无 API 密钥时系统仍可跑通核心流程，便于本地开发与演示。

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户 (手机/PC 浏览器)                    │
│                   扫码/打开 Web Portal 链接                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│              Frontend  (Next.js 14 · 移动端优先)              │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌───────────┐  │
│  │ 上传组件 │→ │ 生成触发   │→ │ 预览播放 │→ │ 下载/复制 │  │
│  └──────────┘  └────────────┘  └──────────┘  └───────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API (JSON + multipart)
┌──────────────────────────▼──────────────────────────────────┐
│              Backend  (FastAPI · 异步)                        │
│  ┌────────────┐ ┌──────────────┐ ┌───────────────────────┐  │
│  │ 上传路由   │ │ 生成/任务路由│ │ 资产/下载路由         │  │
│  └─────┬──────┘ └──────┬───────┘ └───────────┬───────────┘  │
│        │               │                     │              │
│  ┌─────▼───────────────▼─────────────────────▼───────────┐  │
│  │                   服务层 (Services)                    │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐  │  │
│  │  │ 预处理引擎  │ │ 视频合成引擎 │ │ 文案生成引擎   │  │  │
│  │  │ (OpenCV)    │ │ (FFmpeg)     │ │ (LLM + 模板)   │  │  │
│  │  └─────────────┘ └──────────────┘ └────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            任务管理器 (asyncio 后台任务)               │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ 文件 I/O
┌──────────────────────────▼──────────────────────────────────┐
│        本地存储 (uploads/ · renders/)  ←→  S3/R2 抽象层      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心业务流（对应 PRD 用户流程）

```
上传素材 (1~3 图 / 3~5s 视频) + 可选备注
        │
        ▼
点击【✨ AI 一键生成爆款视频】  → 创建生成任务 (status=pending)
        │
        ▼  (后台静默执行)
┌───────────────────────────────────────────────┐
│ 1. 预处理: 智能裁切 9:16 + 画质修复 (+背景纯化)│
│ 2. 合成:   选模板 → 卡点拼接/Ken Burns → 烧录花字│
│ 3. 文案:   LLM 生成新加坡本地化 IG Caption      │
└───────────────────────────────────────────────┘
        │
        ▼
任务完成 (status=done) → 前端轮询拿到 video_url + caption
        │
        ▼
预览播放 + 下载 1080P MP4 + 复制 Caption / 换风格重生
```

---

## 3. 模块详细设计

### 3.1 模块一：极简素材上传 (Input & Asset Ingestion)

**职责**：接收 1~3 张图片或 1 段短视频，保持原画质存储，返回资产 ID。

- 支持格式：图片 JPEG/PNG/HEIC；视频 MP4/MOV
- 限制：单图 ≤ 20MB，视频 ≤ 50MB，视频时长 ≤ 10s（超出由后端截取前 5s）
- 存储：`uploads/{job_id}/orig/{filename}`，保留原文件不压缩
- 轻量输入：可选 `note`（产品名/活动备注，如 "芒果啵啵 买一送一"）
- HEIC 统一在预处理阶段转为 JPEG 供后续使用

### 3.2 模块二：AI 智能预处理引擎 (AI Silent Pre-processing)

**职责**：用户无感，后台自动执行三步。

| 步骤 | 实现 | 产出 |
|------|------|------|
| ① 智能裁切 9:16 | OpenCV 显著性检测定位主体中心 + 人脸 Haar 级联；YOLOv8 可选增强（识别"杯/瓶/人"） | 每张图产出 1080×1920 竖屏图 |
| ② 画质修复 | CLAHE 对比度增强 + 饱和度提升 + 去噪（fastNlMeansDenoising） | 提亮、增透、降噪 |
| ③ 背景纯化（保底） | 显著性低分时触发：GrabCut 抠主体 → 替换品牌渐变背景 | 干净背景图 |

产出目录：`uploads/{job_id}/processed/{N}.jpg`

### 3.3 模块三：卡点视频与内容合成引擎 (Video & Content Generator)

**职责**：将预处理后的素材按模板合成为 5–15s 竖屏视频，并生成花字与文案。

- **模板库**：8 套预制模板（JSON 定义），每套含：时长、BGM 路径、每帧片段的转场类型、片段时长、花字文本模板、Logo 位置
  - 模板示例：`summer_cool`（夏日酷炫）、`zoom_in`（高质感 Zoom-In）、`promo_flash`（促销快闪）、`ken_burns`（静态微动）等
- **静态图动感化**：单图时施加 Ken Burns（缓慢拉近 + 微缩放），FFmpeg `zoompan` 滤镜实现
- **卡点合成**：多图按 BGM 节拍点切换，`xfade` 转场
- **花字烧录**：前 1–3s 黄金 Hook，`drawtext` 烧录大字（如 "🥭 MUST TRY!" / "BUY 1 FREE 1"）
- **字幕**：可选底部动态字幕
- **输出**：`renders/{job_id}/final.mp4`，1080×1920，H.264 + AAC

**文案生成 (LLM Copywriter)**：
- 输入：产品备注 + 模板风格
- 输出：新加坡本地化 IG Caption（含 Shiok! / Refreshing 等本地语气）+ Hashtag 矩阵 (`#SGFoodie #SGBubbleTea #SingaporeEats #SGDeals #SGDrinks`)
- 无 API 密钥时走模板兜底，保证可用

### 3.4 模块四：预览与导出端 (Preview & Output Hub)

- **预览**：返回 `video_url`，前端 `<video>` 直接播放
- **下载**：`/api/assets/{job_id}/video` 返回 MP4 文件流，1080P
- **复制 Caption**：`/api/jobs/{job_id}` 返回 `caption` 字段，前端一键复制
- **换风格重生**：`/api/jobs/{job_id}/regenerate`，保留原素材，换模板重新合成

---

## 4. API 接口设计

Base URL: `http://localhost:8000/api`

### 4.1 上传素材

```
POST /upload
Content-Type: multipart/form-data

Body:
  files[]   : File[]   (1~3 张图片 或 1 段视频)
  note      : string   (可选，产品名/活动备注)

Response 201:
{
  "job_id": "j_20260723_a1b2c3",
  "assets": [
    {"id": "a_0", "name": "photo1.jpg", "type": "image", "size": 2345678}
  ],
  "note": "芒果啵啵 买一送一",
  "status": "uploaded"
}
```

### 4.2 触发生成

```
POST /jobs/{job_id}/generate
Body (可选):
{
  "template": "summer_cool"   // 不传则自动选择
}

Response 202:
{
  "job_id": "j_20260723_a1b2c3",
  "status": "processing",
  "template": "summer_cool"
}
```

### 4.3 查询任务状态（轮询）

```
GET /jobs/{job_id}

Response 200:
{
  "job_id": "...",
  "status": "processing" | "done" | "failed",
  "progress": 65,            // 0-100
  "stage": "rendering",      // preprocessing | composing | caption | done
  "video_url": "/api/assets/.../video",
  "thumbnail_url": "/api/assets/.../thumb.jpg",
  "caption": "...",          // done 时返回
  "hashtags": ["#SGFoodie", ...],
  "template": "summer_cool",
  "error": null
}
```

### 4.4 下载视频

```
GET /assets/{job_id}/video
Response: video/mp4 文件流 (attachment)
```

### 4.5 换风格重生

```
POST /jobs/{job_id}/regenerate
Body: { "template": "promo_flash" }
Response 202: { "job_id": "...", "status": "processing" }
```

### 4.6 模板列表

```
GET /templates
Response: [{ "id": "summer_cool", "name": "夏日酷炫", "duration": 8, "tags": ["cool","summer"] }, ...]
```

---

## 5. 数据模型

### 5.1 Job（生成任务）

```python
Job {
  job_id: str           # 主键，j_{date}_{rand}
  status: str           # uploaded | processing | done | failed
  stage: str            # preprocessing | composing | caption | done
  progress: int         # 0-100
  note: str             # 用户备注
  assets: [Asset]       # 原始素材
  processed: [str]      # 预处理后图片路径
  template: str         # 使用的模板 id
  video_path: str       # 成品 mp4 路径
  thumbnail_path: str
  caption: str          # IG 文案
  hashtags: [str]
  created_at: datetime
  updated_at: datetime
  error: str | None
}
```

### 5.2 Asset（素材）

```python
Asset {
  id: str
  name: str
  type: str             # image | video
  orig_path: str        # 原始文件
  size: int
}
```

### 5.3 Template（模板定义，JSON）

```python
Template {
  id: str               # summer_cool
  name: str             # 夏日酷炫
  duration: float       # 秒
  bgm: str              # 音轨文件名
  segments: [Segment]   # 片段定义
  hook_text: str        # 花字模板，如 "🥭 MUST TRY!"
  hook_duration: float  # 花字显示时长
  transition: str       # xfade 类型
  logo_position: str    # top-right 等
  style_prompt: str     # 喂给 LLM 的风格描述
}
Segment {
  duration: float
  effect: str           # ken_burns | zoom_in | flash | slide
  overlay_text: str | None
}
```

**存储**：Phase 1 使用内存字典 + JSON 文件持久化 (`backend/data/jobs/{job_id}.json`)，无需数据库。Phase 2 引入 PostgreSQL。

---

## 6. 目录结构

```
ai-video-portal/
├── TRD.md                      # 本文档
├── README.md                   # 启动说明
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── main.py                 # FastAPI 入口 + 路由挂载
│   ├── config.py               # 配置（环境变量）
│   ├── models.py               # Pydantic 数据模型
│   ├── routers/
│   │   ├── upload.py
│   │   ├── jobs.py
│   │   ├── assets.py
│   │   └── templates.py
│   ├── services/
│   │   ├── preprocessor.py     # OpenCV 智能裁切+画质修复
│   │   ├── video_renderer.py   # FFmpeg 合成
│   │   ├── caption_writer.py   # LLM 文案
│   │   └── task_manager.py     # 异步任务调度
│   ├── templates_data/
│   │   ├── templates.json      # 8 套模板定义
│   │   └── bgm/                # 卡点音轨 (mp3)
│   ├── assets/                 # 字体、logo 水印
│   │   ├── font.ttf
│   │   └── logo.png
│   ├── storage/                # 运行时生成（gitignore）
│   │   ├── uploads/
│   │   ├── renders/
│   │   └── data/jobs/
│   └── tests/
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── .env.local.example
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx        # 主页：上传+生成
        │   ├── result/page.tsx # 结果：预览+下载
        │   └── globals.css
        ├── components/
        │   ├── Uploader.tsx    # 拖拽/点击上传
        │   ├── GenerateButton.tsx
        │   ├── VideoPreview.tsx
        │   ├── CaptionCard.tsx
        │   └── ProgressBar.tsx
        └── lib/
            └── api.ts          # 后端 API 封装
```

---

## 7. 前端设计要点

- **移动端优先**：Tailwind 响应式，`max-w-md mx-auto` 容器，触控友好大按钮
- **上传组件**：支持点击/拖拽，多图预览缩略图，相机调用 (`capture` 属性)
- **生成流程**：点击后进入进度页，轮询 `/jobs/{id}` 展示 stage + progress
- **结果页**：`<video>` 自动播放预览 + 下载按钮 + Caption 复制按钮 + 换风格按钮
- **PWA 友好**：可添加到手机桌面（manifest）

---

## 8. 环境配置

### 8.1 后端 `.env.example`

```
# LLM 配置（OpenAI 兼容）
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=              # 留空则走模板兜底
LLM_MODEL=deepseek-chat

# YOLO 增强（可选）
ENABLE_YOLO=false

# 存储
STORAGE_DIR=./storage

# 服务
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000
```

### 8.2 前端 `.env.local.example`

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

---

## 9. 部署方案

### 9.1 开发期（Phase 1）

- 后端：`uvicorn main:app --reload --port 8000`
- 前端：`npm run dev`（端口 3000）
- 存储：本地 `backend/storage/`

### 9.2 生产期（Phase 2 预留）

- 容器化：`docker-compose.yml`（backend + frontend + nginx 反代）
- 存储：切换 `STORAGE_DRIVER=s3`，接入 Cloudflare R2
- 队列：Celery + Redis，Worker 独立扩缩
- CDN：前端走 Vercel/Cloudflare Pages，视频走 R2 + CDN

---

## 10. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| FFmpeg 滤镜参数在不同平台表现不一 | 渲染异常 | 统一 H.264 编码 + 像素格式；模板参数做平台测试 |
| YOLOv8 权重下载失败 | 主体识别降级 | 默认 OpenCV 显著性兜底，YOLO 仅增强 |
| LLM API 不可用/超时 | 无文案 | 模板兜底 + 超时 8s 自动降级 |
| HEIC 解码 | 上传失败 | pillow-heif 支持转码；不支持则提示用户转 JPEG |
| 视频渲染耗时长 | 用户等待 | 异步任务 + 进度轮询；限制素材数量与时长 |
| 大文件上传超时 | 上传失败 | 前端分片校验大小；后端流式接收 |

---

## 11. Phase 1 验收标准

- [ ] 移动端浏览器可上传 1~3 张图片，含可选备注
- [ ] 点击生成后，30s 内（单图）/ 60s 内（多图）产出 5–15s 竖屏 MP4
- [ ] 成品为 1080×1920，含 BGM、转场、花字
- [ ] 返回新加坡本地化 IG Caption + Hashtag
- [ ] 可预览播放、下载 MP4、复制 Caption、换风格重生
- [ ] 无 API 密钥时系统仍可跑通（模板兜底）

---

## 12. 后续演进（Phase 2 预告）

- 多模板自主选择 UI
- Instagram Graph API 一键排期/定时发布
- 用户账号与多门店隔离
- 云存储 + CDN + Celery 分布式渲染
- 视频模板可视化编辑器
