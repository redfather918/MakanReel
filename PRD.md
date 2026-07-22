# 产品需求文档 (PRD) — MakanReel (Phase 1 + Phase 2 规划)

> **对外产品名：MakanReel**（马来/新马俚语"吃" + Reel 短视频）
> **内部代号：NIHAO**
> 版本：v1.1 ｜ 对应 TRD：`TRD.md` ｜ 编写日期：2026-07-23 ｜ 更新：2026-07-23（增补 Phase 2 规划草案）
>
> 本文档基于原始 PRD 原型草案（PDF）整理，补充了**品牌命名**与 **Phase 1 实际交付状态对照**（见第 6 节）。
> 原始草案专为新加坡 180+ 门店规模的餐饮品牌设计，聚焦"极简上传"与"AI 一键生成爆款视频"的核心体验。
> 第 7 节起为 **Phase 2 产品功能演进规划（草案）**，承接 Phase 1 闭环，明确"品质升级 / 社媒直连 / HQ 管控"三条演进主线。

---

## 0. 文档说明

| 项 | 内容 |
| --- | --- |
| 服务对象 | 新加坡 180+ 奶茶/餐饮门店店长、现场员工或 HQ 营销人员 |
| 核心目标 | 零门槛、零剪辑基础，**30 秒内**生产一条符合 Instagram Reels / TikTok 爆款标准的 **5–15 秒**短视频及本土化文案 |
| 形态 | 极简、高频、AI 驱动的移动端 Web 视频与内容生成平台（Web Portal，无需下载 App） |

---

## 1. 产品定位与目标 (Product Vision)

- **核心定位**：极简、高频、AI 驱动的移动端 Web 视频与内容生成平台（Web Portal）。
- **服务对象**：新加坡 180+ 奶茶/餐饮门店店长、现场员工或 Headquarters (HQ) 营销人员。
- **核心目标**：实现"零门槛、零剪辑基础，30 秒内生产一条符合 Instagram Reels / TikTok 爆款标准的 5–15 秒短视频及本土化文案"。

---

## 2. 用户业务流程 (User Workflow)

```
[手机/PC 打开 Web 链接]
        │
        ▼
[步骤 1: 拖拽/点击上传 1~3 张素材照片 或 3s 视频]
        │
        ▼  (可选: 输入简短备注，如 "新品买一送一")
[步骤 2: 点击 【✨ AI 一键生成爆款视频】]
        │
        ▼  (后台静默运行: 画质修复 + 智能裁切 + 卡点合成 + AI 文案)
[步骤 3: 预览成品视频 + 复制配套 IG Caption + 一键下载]
```

---

## 3. 功能模块详细设计 (Detailed Feature Specifications)

### 3.1 模块一：极简素材上传端 (Input & Asset Ingestion)

- **界面形态**：响应式 Mobile-First Web（无需下载 App，浏览器/扫码即用，支持添加到手机桌面）。
- **素材上传能力**：
  - 支持上传 1~3 张图片（JPEG / PNG / HEIC）或 1 段 3~5 秒原始短视频（MP4 / MOV）。
  - 支持手机本地相册直选或调起相机随手拍。
- **原图/原视频传输**：不经过社媒软件压缩，保持最高画质与色彩。
- **轻量输入项（可选）**：
  - 提供一个极简文本框（或语音转文字输入）：备注活动 / 产品名（例：芒果啵啵 买一送一）。

### 3.2 模块二：AI 智能预处理引擎 (AI Silent Pre-processing)

在用户点击生成后，系统后台静默自动执行，无需人工干预：

1. **智能视觉主体识别与 9:16 聚焦 (Smart Cropping)**
   - 技术实现：利用物体检测模型（如 YOLOv8 / Vision API）自动识别照片中的"奶茶杯"、"产品包装"或"人脸"。
   - 功能：自动以识别到的主体为视觉中心，将横屏/4:3 素材安全裁切为 9:16 竖屏（IG Reels / TikTok 标准），确保关键要素永远不会被切掉。
2. **画面质量智能修复 (Image & Video Enhancement)**
   - 功能：自动针对后厨/店面较暗的光线进行色彩调优（提高饮品饱和度、透亮度与对比度），自动去除照片噪点。
3. **背景一键纯化/替换（可选保底）**
   - 功能：若检测到背景过于杂乱（如乱七八糟的设备），系统可自动完成主体抠图，替换为预设的品牌微动色彩或极简冷饮背景。

### 3.3 模块三：卡点视频与内容合成引擎 (Video & Content Generator)

- **预制爆款模板库 (Template Base)**：
  - 后台预置 8–10 套 5–15 秒快节奏卡点模板（包含夏日酷炫、高质感 Zoom-In、促销快闪等风格）。
  - 模板内置：专业级转场特效、卡点音乐音轨（Beat detection）、品牌水纹 / Logo 统一放置位置。
- **静态图"动感化"处理 (Ken Burns Effect)**：
  - 若用户仅上传了 1 张静态图片，AI 自动施加微动效果（镜头缓慢拉近、微光闪烁），消除单调感。
- **爆款花字与动态字幕挂载 (Dynamic Overlays)**：
  - 在视频前 1~3 秒（黄金 Hook 视角），AI 根据产品备注自动生成视觉冲击力强的文字挂贴（例：🥭 或 `MUST TRY! MANGO SAGO BUY 1 FREE 1`）。
- **新加坡本土化 Caption 一键生成 (LLM Copywriter)**：
  - 基于 LLM（如 Gemini API），根据输入产品名及图片内容，1 秒生成配套的 Instagram Caption。
  - 文案风格：带有适当的新加坡本地语气与诱人描述（结合 `Shiok!` `Refreshing` 等关键词）。
  - 自动补全本土 Hashtag 矩阵：自动挂载 `#SGFoodie #SGBubbleTea #SingaporeEats #SGDeals #SGDrinks`。

### 3.4 模块四：预览与导出端 (Preview & Output Hub)

- **实时渲染预览 (Video Player)**：
  - 后台渲染完成后，前端直接弹窗播放含音乐、转场、花字的最终 MP4 视频。
- **一键导出工具箱**：
  - 【📥 下载视频文件】：直接保存 1080P 高清 .mp4 至手机相册。
  - 【📋 复制 Caption】：一键将带 Hashtag 的文案复制到剪贴板。
  - 【🔄 换个风格重新生成】：若不满意当前效果，点击此按钮，系统保留原素材，换用另一套卡点音乐与转场模板重新合成。

---

## 4. 技术架构路线推荐 (Technical Architecture)

| 架构层 | 选用技术/服务 | 职责描述 |
| --- | --- | --- |
| 前端 (Frontend) | React / Vue (Next.js / Nuxt) | 极简移动端 Web 界面，拖拽上传与视频预览 |
| 后端 API & 调度 | Node.js / Python FastApi | 负责接收请求、任务排队与存储处理 |
| 存储 (Storage) | Cloudflare R2 / AWS S3 | 高速存储原始素材与生成后的成品 MP4 |
| AI 图像/视觉层 | OpenCV / YOLOv8 / SAM | 负责主体检测、9:16 安全裁切与画质美化 |
| AI 文案层 | Gemini API / OpenAI API | 结合提示词（Prompt）生成新加坡本地化 IG Caption |
| 视频渲染引擎 | Remotion / Shotstack API / FFmpeg | 将图片、视频片段、卡点 BGM、动态花字按模板组装渲染成视频 |

---

## 5. 阶段迭代规划 (Phasing)

- **Phase 1（已完成）**：聚焦"极简上传 ➔ AI 一键生成视频 ➔ 预览/下载/复制文案/换风格"的核心闭环，建立基础模板库与本地化文案引擎。详见第 6 节交付状态对照。
- **Phase 2（规划中，见第 7 节）**：分 2.1 / 2.2 两个小版本演进，三条主线并行：
  - **品质升级**：品牌视觉资产化、真实曲库 + Beat Detection 卡点、智能抠图背景替换、云存储与分布式渲染。
  - **社媒直连**：Instagram / TikTok 一键发布与定时排期、多语言与动态热点文案。
  - **HQ 管控**：总部营销活动与模板统一下发、门店权限隔离与审计、可选审批工作流。
- **核心约束（贯穿 Phase 2）**：见第 7.0 节——**绝不破坏 Phase 1 的"30 秒极简闭环"**，所有新增能力以"可选增强 / 后台配置"方式叠加，不增加门店员工的主路径操作步数。

---

## 6. Phase 1 实际交付状态对照（新增）

> 以下对照表由开发团队在 Phase 1 实现后回填，标注每一项 PRD 要求的落地情况与技术选型差异。

| 模块 | PRD 要求 | 实现状态 | 差异 / 备注 |
| --- | --- | --- | --- |
| 3.1 上传端 | 1~3 图 (JPEG/PNG/HEIC) 或 1 段 3~5s 视频 | ✅ 已实现（图片） | 图片上传 + HEIC 解码完整；视频文件可接收，但 Phase 1 主要验证图片链路 |
| 3.1 上传端 | 移动端优先 Web / 扫码即用 | ✅ 已实现 | Next.js 14 移动端优先响应式 |
| 3.1 上传端 | 原画质传输 | ✅ 已实现 | 直传后端，不经压缩 |
| 3.1 上传端 | 备注文本框 | ✅ 已实现 | 极简备注输入 |
| 3.2 智能裁切 | YOLOv8/Vision API 主体识别 + 9:16 裁切 | ✅ 功能达成 | 以 OpenCV 谱残差显著性 + 人脸检测降级实现主体聚焦（未引入 YOLO/SAM，但达成"关键要素不被切掉"目标） |
| 3.2 画质修复 | 提饱和/透亮/对比度 + 去噪 | ✅ 已实现 | CLAHE + 非局部去噪 + 色彩增强 |
| 3.2 背景替换 | 抠图换品牌背景（可选保底） | ✅ 已实现（Phase 2.1） | 用 RMBG-1.4 ONNX 轻量 matting 替代 SAM；支持 summer_cool / neon_night / minimal_brand 三套品牌背景；模板可指定 background；默认开启且不增加门店操作步数 |
| 3.3 模板库 | 8–10 套 5–15s 卡点模板 | ✅ 已实现 | 8 套模板（summer_cool / night_vibe / ken_burns / zoom_in / flash / slide 等），时长 3.5–8s |
| 3.3 转场/BGM | 转场 + Beat detection 卡点音乐 | ⚠️ 部分实现 | 转场 + 程序化合成 BGM（numpy→WAV）；**未做**节拍检测，音轨为程序生成而非曲库 |
| 3.3 品牌 Logo | 水纹/Logo 统一位置 | ✅ 已实现（Phase 2.1） | 角标自动挂载已完成（top-right/bottom-right，90% 透明）；Endcard 动画为增强项 |
| 3.3 Ken Burns | 单图微动（拉近/闪烁） | ✅ 已实现 | zoompan 实现，消除单图单调感 |
| 3.3 花字 Hook | 前 1~3s 动态文字挂贴 | ✅ 已实现 | FFmpeg drawtext 烧录 Hook 文案 |
| 3.3 本土化文案 | LLM 生成 SG Caption + Hashtag 矩阵 | ✅ 已实现 | OpenAI 兼容接口（DeepSeek/Gemini/OpenAI）；无密钥时本地化模板兜底，含 `Shiok!` `Refreshing` + 5 个 SG Hashtag |
| 3.4 预览 | 渲染后直接播放 MP4 | ✅ 已实现 | 前端 `<video>` 预览 |
| 3.4 导出 | 下载 1080P .mp4 | ✅ 已实现 | 1080×1920 H.264 + AAC |
| 3.4 导出 | 复制 Caption（带 Hashtag） | ✅ 已实现 | 剪贴板一键复制 |
| 3.4 导出 | 换风格重新生成 | ✅ 已实现 | 保留素材，切换模板重合成 |
| 架构-前端 | Next.js | ✅ 采用 | Next.js 14 + TypeScript + Tailwind |
| 架构-后端 | Python FastAPI | ✅ 采用 | FastAPI + asyncio 任务编排 + JSON 持久化 |
| 架构-存储 | Cloudflare R2 / AWS S3 | ⚠️ 简化 | Phase 1 用本地文件系统（`backend/storage/`）；S3/R2 为 Phase 2 目标 |
| 架构-视觉 | OpenCV/YOLOv8/SAM | ⚠️ 部分 | 仅用 OpenCV（Python 5.0 兼容实现），未引入 YOLO/SAM |
| 架构-文案 | Gemini / OpenAI API | ✅ 采用 | OpenAI 兼容，可接 Gemini/DeepSeek |
| 架构-渲染 | Remotion/Shotstack/FFmpeg | ✅ 采用 | FFmpeg 本地渲染（未用 Remotion/Shotstack 云服务） |

**图例**：✅ 已实现 ｜ ⚠️ 部分实现（功能达标但有简化/差异） ｜ ❌ 未实现（列入后续规划）

**Phase 1 小结**：核心闭环（极简上传 ➔ AI 一键生成 ➔ 预览/下载/复制文案/换风格）已完整跑通；与原始草案的主要差异为——视觉层以 OpenCV 替代 YOLO/SAM、存储用本地文件系统替代 S3、BGM 程序化合成替代曲库 Beat detection、背景替换与品牌 Logo 挂载已在 Phase 2.1 落地。这些均属 Phase 1 合理简化，不影响核心体验，已在 TRD 风险对策中说明。

---

## 7. Phase 2 产品功能演进规划 (Feature Roadmap — 草案)

> 本章基于已交付的 **MakanReel Phase 1 (NIHAO)** 闭环，梳理 Phase 2 演进方向。
> 所有规划均以第 6 节「Phase 1 实际交付状态对照」中标记为 ⚠️ 部分实现 / ❌ 未实现 的条目为起点，优先补齐短板，再向高级自动化与多渠道矩阵演进。

### 7.0 演进核心原则（Two Guardrails）

贯穿 Phase 2 全程的两条不可妥协原则：

1. **不破坏 Phase 1 的"30 秒极简闭环"**
   - 门店员工主路径（上传 ➔ 点生成 ➔ 看片/导出）操作步骤数**不得超过 Phase 1 的 3 步**。
   - 任何新增能力（品牌挂载、卡点、发布、排期）默认以「可选增强 / 后台配置」叠加，不强制门店在前台做额外决策。
2. **补齐 Phase 1 合理简化的短板 + 向高级自动化 / 多渠道矩阵演进**
   - 优先消除第 6 节中的 ❌/⚠️ 项：品牌视觉、真实曲库与卡点、云存储、智能抠图。
   - 在第二阶段引入社媒直连、HQ 管控、多账号矩阵，把"生成工具"升级为"内容运营平台"。

**设计守则**：门店前台 = 极简生成（保持轻）；HQ / 高级功能 = 独立后台（不打扰门店）；所有"重能力"可灰度开关。

---

### 7.1 一、基础能力补齐与强化 (Core Enhancements)

Phase 1 为快速验证闭环，在视觉与音频上做了轻量化（程序化 BGM、OpenCV 替代高级抠图）。Phase 2 首要目标是提升视频的**品牌感**与**爆款质感**。

#### 7.1.1 品牌视觉资产化 (Brand Identity & Overlays)

| 能力 | 说明 | 对应 Phase 1 短板 | 状态 |
| --- | --- | --- | --- |
| 品牌 Logo 角标自动挂载 | 模板按 `logo_position` 在右上角/右下角叠加半透明品牌 Logo（默认 90% 透明、15% 宽、4% 边距）；Logo 图与策略后台可配（`GET/POST /api/brand`） | ❌ 3.3 品牌 Logo | ✅ **Phase 2.1 已落地**（2026-07-23）：`backend/assets/logo.png` 内置 MakanReel 字标，渲染器 `_overlay_logo` 接入 |
| 品牌 Endcard 动画（结尾 1s） | 视频结尾 1 秒弹出品牌 Endcard 动画 | — | ⏳ 规划中（角标已覆盖主诉求，Endcard 为增强项） |
| 品牌 VI 风格约束 | 后台配置指定字体（Fonts）、品牌色盘（Brand Colors）、贴纸（Stickers），确保 180+ 门店视觉高度统一 | ❌ 未做 VI 约束 | ⏳ 规划中 |
| 智能抠图与背景替换 (Matting & BG Replacement) | 引入 Segment Anything (SAM) 或 lightweight matting 模型；店长后厨/前台随手拍时，一键提取奶茶主体，替换为清凉夏日 / 霓虹夜店 / 极简品牌背景 | ❌ 3.2 背景替换 | ✅ **Phase 2.1 已落地**（2026-07-23）：RMBG-1.4 ONNX 轻量 matting + 3 套品牌背景（summer_cool / neon_night / minimal_brand），预处理流水线接入；模型缺失时降级 OpenCV 显著性软抠图 |

#### 7.1.2 音频与节拍引擎升级 (Audio & Beat Matching)

| 能力 | 说明 | 对应 Phase 1 短板 |
| --- | --- | --- |
| 商业爆款音频库集成 | 替代程序化音效，引入无版权风险的流行短视频 BGM 曲库 | ⚠️ 3.3 BGM 为程序化合成 |
| 节拍检测卡点 (Beat Detection) | 音频分析识别 BGM 重音点（Beats），使转场/切页完全配合节奏，大幅提升动感 | ⚠️ 3.3 未做 Beat detection |

#### 7.1.3 存储与高并发架构云化 (Cloud Infrastructure)

| 能力 | 说明 | 对应 Phase 1 短板 |
| --- | --- | --- |
| 云存储迁移 | 本地文件存储 (`backend/storage/`) 全面升级为 **Cloudflare R2 / AWS S3**，解决 180+ 门店高并发上传存储压力 | ⚠️ 架构-存储 用本地文件系统 |
| 分布式渲染队列 | 引入 **Celery / Redis** 消息队列，节假日营销高峰期平滑排队渲染任务 | ⚠️ 本地 asyncio 编排，无横向扩展 |

---

### 7.2 二、社交网络闭环与排期发布 (Publishing & Analytics)

Phase 1 止步于"下载 MP4 + 复制 Caption"。Phase 2 打通社交平台 API，实现真正的**一键发布**。

#### 7.2.1 Instagram & TikTok 直连发布 (Social Media Integration)

- **Instagram Graph API 集成**
  - 门店在 Portal 内授权连接品牌官方 Instagram 账号。
  - 结果页增加 **【🚀 一键发布至 Instagram Reels】** 按钮，无需下载保存再打开 IG。
- **定时排期系统 (Post Scheduler)**
  - 极简日历 / 时间选择器（如："今天 18:00 新加坡晚高峰发布"）。
  - 后台 CronJob 自动调用 API 定时发布。

#### 7.2.2 文本与营销策略智能升级 (Advanced Content & Multilingual)

- **多语言与本地化扩充**：除英文 / Singlish 外，增加中文（照顾华语店长）及马来语 / 印尼语 Caption 自动切换。
- **动态热点营销提示 (Trending Prompting)**
  - 系统抓取新加坡本地天气（暴雨 / 高温）或节日（国庆日 / 中秋节）。
  - 自动建议提示语：*检测到新加坡当前高温 33°C，AI 已自动为您匹配"冰爽解暑"主题模板与 Caption！*

---

### 7.3 三、HQ 集中管控与多门店权限矩阵 (HQ Management & Multi-Store)

新加坡 180+ 门店规模要求 Headquarters (HQ) 具备统一管理、监控与下发能力。

#### 7.3.1 模板与营销活动下发 (Campaign & Template Hub)

- **HQ 控制台**
  - HQ 营销团队上架"限时新品模板"（如全网统一的"芒芒甘露新品上市"专题模板），并限制有效期（例：7/23–8/1）。
  - 门店店长登录 Portal 后，顶部**优先推荐** HQ 当前推送的营销活动模板。

#### 7.3.2 门店管理与审计 (Store Matrix & Audit Trail)

- **门店权限隔离**：每个门店拥有独立 **Store ID**，便于追踪哪家门店产出最活跃。
- **审批工作流（可选预留）**
  - **模式 A（自由模式）**：店长生成后直接发布。
  - **模式 B（HQ 审核模式）**：店长生成后提交，HQ 营销人员在后台一键 Approve 后才自动发布到 IG。

---

### 7.4 四、Phase 2 优先级建议与 Roadmap

为避免功能膨胀，将 Phase 2 拆分为两个小版本迭代：

```
[Phase 1 已完成]
      │
      ▼
[Phase 2.1: 爆款视觉与音频升级]  ──重点：好看、动感、有品牌──
      │
      ▼
[Phase 2.2: 社媒直连与 HQ 控制台] ──重点：省事、管控、发布──
```

#### 🎯 Phase 2.1：品质与体验升级

| # | 功能 | 说明 |
| - | --- | --- |
| 1 | 品牌 Logo 挂载 | Top-Right / Bottom-Right 角标 + Endcard 动画 |
| 2 | 真实短视频曲库 + Beat Detection | 替代程序化 BGM，节拍自动卡点剪辑 |
| 3 | 云存储迁移 | Cloudflare R2 / AWS S3 |
| 4 | 背景智能抠图替换 | SAM / Matting 保底，杂乱背景一键换品牌背景 |

#### 🎯 Phase 2.2：链路闭环与商业管理

| # | 功能 | 说明 |
| - | --- | --- |
| 1 | Instagram Graph API 对接 | 一键定时 / 实时发布 Reels |
| 2 | HQ 营销活动与模板统一下发后台 | 限时模板 + 有效期 + 门店优先推荐 |
| 3 | 动态热点文案推荐 | 结合新加坡天气 / 节日趋势自动匹配主题 |

#### 📌 待客户确认（优先级取舍）

三条演进主线 —— **品质升级（7.1）** vs **社媒直连发布（7.2）** vs **HQ 集中管控（7.3）** —— 客户当前最迫切希望优先落地哪一个？确认后将针对性深挖技术方案与验收标准，并回填至对应 TRD 章节。

---

*（Phase 2 为规划草案，尚未实现；具体技术选型、接口契约与数据模型将在对应小版本启动前于 `TRD.md` 中细化。）*
