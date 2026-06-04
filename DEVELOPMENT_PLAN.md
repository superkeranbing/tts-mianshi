# 听记面试 (TTS-Mianshi) — 开发文档

> **版本**: v1.0 | **日期**: 2026-06-04 | **状态**: 设计阶段

---

## 目录

1. [项目概述](#1-项目概述)
2. [WPS 听记功能对标分析](#2-wps-听记功能对标分析)
3. [新增功能：面试提升](#3-新增功能面试提升)
4. [技术选型](#4-技术选型)
5. [整体技术架构](#5-整体技术架构)
6. [模块详细设计](#6-模块详细设计)
7. [数据库设计](#7-数据库设计)
8. [API 接口设计](#8-api-接口设计)
9. [开发路线图](#9-开发路线图)
10. [部署方案](#10-部署方案)
11. [风险与应对](#11-风险与应对)

---

## 1. 项目概述

### 1.1 项目背景

本项目旨在基于开源技术方案，完整复现 WPS 听记的全部核心功能，并在此基础上新增 **"面试提升"** 特色模块：支持上传简历文档（PDF/DOC），结合面试录音的语音识别结果，利用大语言模型（LLM）进行深度分析，输出面试问题的最佳答案、被面试者的应答评估、相关知识点设计以及整体提升建议。

### 1.2 项目定位

- **目标用户**: 求职者、HR、面试培训师、职场人士
- **使用场景**: 模拟面试复盘、真实面试录音分析、面试能力自评
- **产品形态**: Web 应用 + 桌面客户端（Tauri），可渐进部署

### 1.3 核心价值

| 维度 | 价值 |
|------|------|
| 语音转文字 | 开源方案替代付费服务，数据本地化，隐私可控 |
| 面试分析 | 结合简历+面试录音，AI 深度分析面试表现 |
| 知识沉淀 | 自动提取面试知识点，构建个人知识库 |
| 提升闭环 | 从"发现问题"到"给出方案"的完整链路 |

---

## 2. WPS 听记功能对标分析

WPS 听记是金山办公旗下的智能语音转写产品，以下是其核心功能及开源对标方案：

### 2.1 功能对标表

| 序号 | WPS 听记功能 | 功能说明 | 开源对标方案 | 优先级 |
|------|-------------|---------|-------------|--------|
| 1 | **实时录音转写** | 边录边转，实时显示文字 | FunASR Paraformer 实时流式解码 | P0 |
| 2 | **导入音频转写** | 上传已有音频文件转文字 | FunASR / Whisper 离线批处理 | P0 |
| 3 | **多语言识别** | 中英文混合识别 | SenseVoice + Whisper large-v3 | P0 |
| 4 | **区分说话人** | 自动识别不同说话人并标注 | CAM++ 说话人日志 (FunASR 内置) | P0 |
| 5 | **音频文本同步** | 点击文字跳转到对应音频位置 | 词级时间戳对齐 (VAD + 强制对齐) | P1 |
| 6 | **智能分段** | 根据语义自动分段/分句 | VAD 切分 + 标点恢复 (CT-Transformer) | P1 |
| 7 | **智能纪要** | AI 自动生成录音摘要 | LLM (Qwen / DeepSeek / GPT) 摘要生成 | P1 |
| 8 | **关键词/重点标记** | 手动标记高亮重点内容 | 前端富文本标注组件 | P2 |
| 9 | **全文搜索定位** | 在转写文本中搜索关键词 | 前端全文搜索 + 后端 Elasticsearch | P2 |
| 10 | **导出多格式** | 导出 TXT/Word/PDF/SRT 字幕 | python-docx / WeasyPrint / ReportLab | P1 |
| 11 | **历史记录管理** | 录音和转写历史列表 | PostgreSQL + 文件存储 | P1 |
| 12 | **云同步** | 多端同步录音和转写 | MinIO (S3兼容) + PostgreSQL | P3 |
| 13 | **录音标记** | 录音中打点标记重要时刻 | 前端录音控件 + 时间戳标记 | P2 |

### 2.2 核心技术对标

```
WPS 听记 ASR 引擎  →  FunASR (Paraformer-large + SenseVoice + CAM++)
WPS 听记前端      →  React + TypeScript + TailwindCSS + WaveSurfer.js
WPS 听记后端      →  Python FastAPI + Celery + Redis + PostgreSQL
WPS 智能纪要      →  LLM API (Qwen-Max / DeepSeek-V3 / GPT-4o)
```

---

## 3. 新增功能：面试提升

### 3.1 功能概述

面试提升模块是本项目的差异化核心功能，基于 **简历文档解析** + **面试语音转写** + **LLM 深度分析**，构建面试能力评估与提升闭环。

### 3.2 功能流程

```
+-------------+     +-------------+     +-------------+
|  上传简历    |     |  导入面试录音 |     |  LLM 分析    |
|  PDF/DOC    | --> |  语音转文字   | --> |  生成报告    |
+-------------+     +-------------+     +-------------+
       |                                       |
       +--------------- 联合分析 ---------------+
                               |
                    +----------+----------+
                    v          v          v
              +---------+ +--------+ +--------+
              |最佳答案  | |知识点   | |提升总结 |
              |生成     | |设计     | |        |
              +---------+ +--------+ +--------+
```

### 3.3 详细功能

#### 3.3.1 简历上传解析

- **支持格式**: PDF（扫描件 + 电子版）、DOC / DOCX
- **解析引擎**:
  - PDF 电子版：PyMuPDF (fitz) 提取文本
  - PDF 扫描件：PaddleOCR / Tesseract OCR 文字识别
  - DOC/DOCX：python-docx
- **提取字段**: 基本信息、教育经历、工作经历、项目经验、技能标签

#### 3.3.2 面试语音分析

- **输入**: 面试录音（mp3/wav/m4a）→ ASR 转写文本 + 说话人标注
- **处理流程**:
  1. ASR 转写（FunASR / Whisper）
  2. 说话人分离（CAM++）
  3. 区分「面试官」与「被面试者」
  4. LLM 提取对话中的问答对

#### 3.3.3 问题提取与分类

LLM 自动从转写文本中提取面试问题并分类：

| 问题类别 | 示例 |
|---------|------|
| 自我介绍类 | "请简单介绍一下你自己" |
| 技术问题 | "React 的虚拟 DOM 原理是什么？" |
| 项目经验 | "你在这个项目中遇到的最大挑战是什么？" |
| 行为面试 | "请举例说明你如何处理团队冲突" |
| 职业规划 | "你未来3年的职业规划是什么？" |
| 薪资期望 | "你对薪资有什么期望？" |

#### 3.3.4 最佳答案生成

- **结合简历上下文**，针对每个面试问题生成最佳答案
- **答案模板**: STAR 法则（行为/项目问题），结构化技术回答（技术问题）
- **个性化**: 根据简历中的项目经验、技能标签定制答案

#### 3.3.5 被面试者回答评估

- **评分维度**: 准确性、完整性、表达清晰度、STAR 规范度
- **对比分析**: 实际回答 vs 最佳答案的差距
- **改进建议**: 具体的话术优化建议

#### 3.3.6 知识点设计

LLM 根据面试中涉及的技术话题，自动设计结构化知识点卡片，包含：核心概念、关键词、推荐资料、面试要点。

#### 3.3.7 提升总结

综合分析后输出结构化提升报告：整体评分、优势分析、待提升项、重点提升方向、建议练习计划。

---

## 4. 技术选型

### 4.1 技术栈总览

| 层次 | 技术 | 版本要求 | 说明 |
|------|------|---------|------|
| **前端框架** | React 18 + TypeScript | >= 18.2 | 主流前端框架，生态丰富 |
| **构建工具** | Vite | >= 5.0 | 快速开发构建 |
| **UI 框架** | TailwindCSS + shadcn/ui | >= 3.4 | 原子化 CSS + 高质量组件 |
| **音频波形** | WaveSurfer.js | latest | 音频波形可视化 |
| **桌面壳** | Tauri 2.x | latest | 比 Electron 更轻量，Rust 内核 |
| **后端框架** | FastAPI (Python) | >= 0.110 | 异步高性能，自动生成 OpenAPI 文档 |
| **任务队列** | Celery + Redis | >= 5.3 | 异步处理 ASR 和 LLM 任务 |
| **数据库** | PostgreSQL 16 + pgvector | >= 16 + 0.7 | 主数据库 + 向量搜索 |
| **文件存储** | MinIO (S3 兼容) | latest | 音频文件、导出文件存储 |
| **缓存** | Redis | >= 7.0 | 任务队列 + 缓存 |
| **搜索** | Elasticsearch | >= 8.x | 转写全文搜索（P2 阶段） |
| **ASR 引擎** | FunASR (阿里达摩院) | latest | 核心语音识别引擎 |
| **LLM 接口** | OpenAI 兼容 API | - | 支持 Qwen / DeepSeek / GPT |

### 4.2 ASR 引擎选型深度对比

| 指标 | FunASR (Paraformer) | Whisper (large-v3) | SenseVoice | Sherpa-ONNX |
|------|---------------------|-------------------|------------|-------------|
| **中文识别率** | ★★★★★ (最优) | ★★★★ | ★★★★ | ★★★ |
| **实时流式** | ✅ Paraformer 流式 | ❌ 仅离线 | ✅ 支持 | ✅ 支持 |
| **说话人分离** | ✅ CAM++ 内置 | ❌ 需额外方案 | ❌ | ❌ |
| **标点恢复** | ✅ CT-Transformer | ✅ 内置 | ✅ 内置 | ❌ |
| **模型大小** | ~220MB (large) | ~3.1GB (large-v3) | ~80MB (small) | ~50MB |
| **推理速度** | 快 (ONNX 优化) | 慢 | 极快 | 极快 |
| **GPU 要求** | 推荐 GPU | 推荐 GPU | CPU 可跑 | CPU 优先 |
| **许可证** | Apache 2.0 | MIT | Apache 2.0 | Apache 2.0 |
| **热词定制** | ✅ | ❌ | ✅ | ✅ |
| **开源地址** | [FunASR](https://github.com/modelscope/FunASR) | [Whisper](https://github.com/openai/whisper) | 集成在 FunASR | [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) |

**选型结论**:
- **主引擎**: FunASR (Paraformer-large + SenseVoice-Small)，中文识别最优，内置说话人分离
- **辅助引擎**: Whisper large-v3，用于英文访谈或多语言混合场景
- **边缘部署**: Sherpa-ONNX，用于纯离线 CPU 场景

### 4.3 LLM 选型

| 模型 | 优势 | 劣势 | 推荐场景 |
|------|------|------|---------|
| **Qwen-Max / Qwen3** | 中文理解最佳，阿里生态 | API 费用 | 面试分析（主力） |
| **DeepSeek-V3** | 性价比极高，中文优秀 | 推理稍慢 | 批量分析 |
| **GPT-4o** | 综合能力最强 | 价格高，网络限制 | 高质量需求 |
| **本地 Qwen2.5** | 数据隐私，零费用 | 需 GPU 资源 | 隐私敏感场景 |

**推荐**: 优先接入 OpenAI 兼容 API，支持灵活切换。默认推荐 **DeepSeek-V3**（性价比最优），高质量场景使用 **Qwen-Max**。

---

## 5. 整体技术架构

### 5.1 架构图

```
+-----------------------------------------------------------------+
|                         客户端层                                  |
|  +--------------+  +--------------+  +----------------------+   |
|  |  Web 浏览器   |  |  Tauri 桌面  |  |  移动端 (PWA)        |   |
|  +------+-------+  +------+-------+  +----------+-----------+   |
|         |                 |                      |               |
|         +-----------------+----------------------+               |
|                           | HTTP/WebSocket                       |
+---------------------------+--------------------------------------+
                            |
+---------------------------+--------------------------------------+
|                     Nginx 反向代理                                |
|  (HTTPS 终止 / 静态资源 / WebSocket 代理 / 负载均衡)             |
+---------------------------+--------------------------------------+
                            |
+---------------------------+--------------------------------------+
|                     应用服务层 (FastAPI)                          |
|                                                                  |
|  +-------------+ +-------------+ +-------------+ +-----------+  |
|  | 用户管理     | | 录音管理     | | 面试分析     | | 导出服务   |  |
|  | 模块        | | 模块        | | 模块        | | 模块      |  |
|  +-------------+ +-------------+ +-------------+ +-----------+  |
|                                                                  |
|  +-------------------------------------------------------------+ |
|  |                    REST API / WebSocket                      | |
|  |   POST /api/asr/upload    ->  文件上传与转写                  | |
|  |   WS   /api/asr/stream    ->  实时流式转写                    | |
|  |   POST /api/interview/analyze -> 面试分析                     | |
|  |   GET  /api/report/{id}   ->  获取分析报告                    | |
|  +-------------------------------------------------------------+ |
+---------------------------+--------------------------------------+
                            |
         +------------------+------------------+
         |                  |                  |
         v                  v                  v
+-----------------+ +--------------+ +------------------+
|  Celery Worker  | |  Celery      | |  Celery Worker   |
|  ASR 引擎        | |  Beat        | |  LLM 引擎         |
|  - FunASR       | |  定时任务     | |  - 问题提取       |
|  - Whisper      | |  - 清理临时   | |  - 答案生成       |
|  - SenseVoice   | |    文件       | |  - 知识点设计     |
|  - CAM++        | |              | |  - 提升总结       |
+--------+--------+ +--------------+ +--------+---------+
         |                                    |
         |           +------------------------+
         |           |
         v           v
+----------------------------------------------------------------+
|                        数据存储层                                |
|  +--------------+ +------------+ +------------+ +------------+  |
|  | PostgreSQL   | | MinIO      | | Redis      | | Elastic-   |  |
|  | (主数据库)    | | (文件存储)  | | (缓存/队列) | | search     |  |
|  | + pgvector   | |            | |            | | (P2)       |  |
|  +--------------+ +------------+ +------------+ +------------+  |
+----------------------------------------------------------------+
```

### 5.2 ASR 数据流

```
                    用户上传音频
                         |
                         v
                    音频预处理
                  (降噪/重采样/格式转换)
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       VAD 切分       说话人分离      语言检测
    (FSMN-VAD)       (CAM++)
          +--------------+--------------+
                         |
                         v
                    ASR 语音识别
              (Paraformer / Whisper)
                         |
                         v
                      后处理
           (标点恢复 / 逆文本正则化 / 时间戳对齐)
                         |
                         v
                 转写结果 + 说话人标签
                         |
          +--------------+--------------+
          v              v              v
      智能纪要        面试分析        多格式导出
       (LLM)         (LLM)
```

---

## 6. 模块详细设计

### 6.1 项目目录结构

```
tts-mianshi/
├── frontend/                    # 前端项目 (React + TypeScript)
│   ├── src/
│   │   ├── components/          # 通用组件
│   │   │   ├── ui/              # shadcn/ui 基础组件
│   │   │   ├── AudioRecorder/   # 录音控件
│   │   │   ├── AudioPlayer/     # 音频播放器（波形+时间轴）
│   │   │   ├── TranscriptView/  # 转写文本展示（分说话人）
│   │   │   ├── InterviewReport/ # 面试报告组件
│   │   │   ├── ResumeUploader/  # 简历上传组件
│   │   │   └── KnowledgeCard/   # 知识点卡片
│   │   ├── pages/               # 页面
│   │   │   ├── HomePage.tsx     # 首页（录音/导入入口）
│   │   │   ├── RecordingPage.tsx# 录音转写页面
│   │   │   ├── TranscriptPage.tsx# 转写详情/编辑页面
│   │   │   ├── InterviewPage.tsx# 面试分析页面
│   │   │   ├── ReportPage.tsx   # 分析报告页面
│   │   │   └── HistoryPage.tsx  # 历史记录页面
│   │   ├── hooks/               # 自定义 Hooks
│   │   │   ├── useAudioRecorder.ts
│   │   │   ├── useWebSocket.ts  # WebSocket 实时转写
│   │   │   └── useInterviewAnalysis.ts
│   │   ├── services/            # API 服务层
│   │   │   ├── api.ts
│   │   │   ├── asrService.ts
│   │   │   ├── interviewService.ts
│   │   │   └── exportService.ts
│   │   ├── stores/              # 状态管理 (Zustand)
│   │   │   ├── recordingStore.ts
│   │   │   └── interviewStore.ts
│   │   ├── types/               # TypeScript 类型定义
│   │   │   ├── asr.ts
│   │   │   └── interview.ts
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                     # 后端项目 (Python FastAPI)
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── api/                 # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # 用户认证
│   │   │   ├── asr.py           # ASR 转写接口
│   │   │   ├── recording.py     # 录音管理
│   │   │   ├── interview.py     # 面试分析
│   │   │   ├── export.py        # 导出
│   │   │   └── websocket.py     # WebSocket 实时转写
│   │   ├── models/              # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── recording.py
│   │   │   ├── transcript.py
│   │   │   ├── interview.py
│   │   │   └── resume.py
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── asr.py
│   │   │   └── interview.py
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── asr_service.py   # ASR 引擎封装
│   │   │   ├── diarization.py   # 说话人分离
│   │   │   ├── llm_service.py   # LLM 调用封装
│   │   │   ├── interview_service.py  # 面试分析业务
│   │   │   ├── resume_parser.py # 简历解析
│   │   │   ├── export_service.py# 导出服务
│   │   │   └── summary_service.py # 智能纪要
│   │   ├── tasks/               # Celery 异步任务
│   │   │   ├── __init__.py
│   │   │   ├── asr_tasks.py     # ASR 转写任务
│   │   │   └── interview_tasks.py # 面试分析任务
│   │   ├── core/                # 核心基础设施
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── celery_app.py
│   │   │   ├── storage.py       # MinIO 存储
│   │   │   └── security.py      # 安全/JWT
│   │   └── utils/
│   │       ├── audio_utils.py   # 音频处理
│   │       └── text_utils.py    # 文本处理
│   ├── alembic/                 # 数据库迁移
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docker/                      # Docker 编排
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── nginx/nginx.conf
│   └── minio/init.sh
│
├── docs/                        # 文档
│   ├── api-spec.md
│   └── deployment.md
│
└── README.md
```

### 6.2 ASR 模块详细设计

#### ASR 引擎封装 (services/asr_service.py)

```python
class ASREngine:
    """统一 ASR 引擎接口，支持多后端切换"""

    def __init__(self, backend: Literal["funasr", "whisper", "sensevoice"]):
        self.backend = backend
        self.model = self._load_model()

    async def transcribe_file(self, audio_path: str) -> TranscriptResult:
        """离线文件转写"""
        ...

    async def transcribe_stream(self, audio_chunk: bytes) -> StreamResult:
        """实时流式转写"""
        ...

    def get_timestamps(self, audio_path: str, text: str) -> list[WordTimestamp]:
        """词级时间戳对齐"""
        ...

class DiarizationEngine:
    """说话人分离引擎 (CAM++)"""

    async def separate_speakers(
        self, audio_path: str
    ) -> list[SpeakerSegment]:
        """返回: [{speaker_id: "SPK_0", start: 0.0, end: 5.2}, ...]"""
        ...
```

#### 音频处理管线

```
原始音频 → 降噪(noisereduce) → 重采样(16kHz mono)
    → VAD 切分 → ASR 识别 → 标点恢复 → ITN → 时间戳对齐
                        │
                   说话人分离(CAM++)
                        │
                   ─────┴─────
                  融合结果(说话人+文本+时间)
```

### 6.3 简历解析器设计 (services/resume_parser.py)

```python
class ResumeParser:
    """简历解析器"""

    async def parse(self, file_path: str, file_type: str) -> ResumeData:
        """
        解析流程:
        1. PDF -> PyMuPDF 提取文本 (电子版) + PaddleOCR (扫描件)
        2. DOC -> python-docx 提取文本
        3. LLM 结构化提取: 基本信息/教育/工作/项目/技能
        """
        raw_text = self._extract_text(file_path, file_type)
        structured = await self._llm_extract_structured(raw_text)
        return structured
```

### 6.4 面试分析引擎设计 (services/interview_service.py)

```python
class InterviewAnalyzer:
    """面试分析核心引擎"""

    async def analyze(
        self,
        transcript: TranscriptData,   # ASR 转写结果
        resume: ResumeData,           # 简历结构化数据
        job_description: str = None,  # 可选岗位JD
    ) -> InterviewReport:
        """
        分析流程:
        1. 提取问答对 (Q&A Pairs)
        2. 问题分类 (技术/行为/项目/规划)
        3. 对每个问题:
           a. 结合简历生成最佳答案
           b. 评估被面试者实际回答
           c. 生成对比得分和改进建议
        4. 设计知识点卡片
        5. 生成整体提升总结
        """
        ...
```

### 6.5 LLM Prompt 设计要点

| Prompt 类型 | 核心要求 |
|------------|---------|
| 问题提取 | 从对话转写中提取面试官问题，区分说话人，按类别归类 |
| 最佳答案生成 | 结合简历经历 + STAR 法则 + 技术框架，生成个性化答案 |
| 回答评估 | 多维度评分（准确性/完整性/清晰度/STAR规范度） |
| 知识点设计 | 提取技术关键词 → 组织相关知识 → 结构化卡片输出 |
| 提升总结 | 聚合所有问答对评估 → 输出优势、待提升、练习计划 |

### 6.6 前端关键页面布局

**录音转写页面:**

```
+----------------------------------------------------------+
|  <- 返回         录音转写                    历史记录      |
|----------------------------------------------------------|
|                                                          |
|          +-------------------------+                     |
|          |     🎤 正在录音...       |                     |
|          |     00:12:34             |                     |
|          |     ==============      |  <- 波形可视化       |
|          |  [⏸ 暂停] [🏷 标记] [⏹ 结束]                  |
|          +-------------------------+                     |
|                                                          |
|  +----------------------------------------------------+  |
|  | 实时转写文字区域                                     |  |
|  | 🟢 面试官: 请简单介绍一下你自己                        |  |
|  | 🔵 候选人: 我叫张三，毕业于...                         |  |
|  +----------------------------------------------------+  |
|                                                          |
|  [📝 编辑模式]  [🔍 搜索]  [📥 导出]                     |
+----------------------------------------------------------+
```

**面试分析报告页面:**

```
+--------------------------------------------------------------+
|  面试提升报告                          2024-01-15 面试记录    |
|--------------------------------------------------------------|
|  +--------------------------+  +--------------------------+ |
|  | 📊 综合评分: 78/100       |  | 📋 张三 | 3年前端开发    | |
|  +--------------------------+  +--------------------------+ |
|                                                              |
|  =============== 问题分析 (共8个问题) ===============       |
|                                                              |
|  +--------------------------------------------------------+  |
|  | Q1: React 的虚拟 DOM 原理是什么？            [技术类]    |  |
|  |                                                         |  |
|  | 🎯 你的回答 (评分: 75/100)                               |  |
|  | "虚拟DOM就是用JS对象来模拟真实DOM..."                      |  |
|  |                                                         |  |
|  | ✅ 最佳答案                                             |  |
|  | "虚拟DOM是React的核心优化机制..."                          |  |
|  |                                                         |  |
|  | 💡 改进建议: 可从Reconciliation算法角度补充...            |  |
|  |                                                         |  |
|  | 📚 知识点: Virtual DOM | Reconciliation | Fiber          |  |
|  +--------------------------------------------------------+  |
|                                                              |
|  =============== 提升总结 ===============                   |
|  ✅ 优势: 基础扎实，项目经验丰富                              |
|  ⚠️ 待提升: 系统设计能力不足，缺少量化成果                    |
|  🎯 重点方向: 分布式系统、微服务架构、表达技巧                |
|  📅 练习计划: 第1周系统设计 / 第2周行为面试 / 第3周技术深度  |
|                                                              |
|  [📥 导出报告 PDF]  [📋 复制到剪贴板]                        |
+--------------------------------------------------------------+
```

---

## 7. 数据库设计

### 7.1 数据库表关系

```
users (1)-----(N) recordings (1)-----(N) transcripts
  |                |
  |                |
  |           interview_reports (1)-----(N) qa_pairs
  |                |
  |           knowledge_points
  |
resumes
```

### 7.2 核心表 SQL (PostgreSQL)

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 录音记录表
CREATE TABLE recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    audio_path VARCHAR(500) NOT NULL,        -- MinIO 路径
    audio_duration FLOAT,                    -- 音频时长(秒)
    audio_format VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    language VARCHAR(10) DEFAULT 'zh',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_recordings_user_id ON recordings(user_id);

-- 转写内容表（按说话人分段）
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recording_id UUID NOT NULL REFERENCES recordings(id) ON DELETE CASCADE,
    speaker VARCHAR(50) NOT NULL,            -- "面试官" / "候选人"
    speaker_name VARCHAR(100),
    content TEXT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_transcripts_recording_id ON transcripts(recording_id);

-- 简历表
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,          -- pdf/doc/docx
    parsed_data JSONB DEFAULT '{}',          -- LLM 解析后结构化数据
    raw_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 面试分析报告表
CREATE TABLE interview_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recording_id UUID NOT NULL REFERENCES recordings(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    overall_score FLOAT,                     -- 综合评分 (0-100)
    strengths JSONB DEFAULT '[]',
    weaknesses JSONB DEFAULT '[]',
    improvement_plan JSONB DEFAULT '[]',
    summary TEXT,
    report_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 问答对表
CREATE TABLE qa_pairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES interview_reports(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    question_category VARCHAR(50),           -- technical/behavioral/project/planning
    your_answer TEXT,
    best_answer TEXT,
    answer_score FLOAT,
    improvement_suggestions TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 知识点卡片表
CREATE TABLE knowledge_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES interview_reports(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    key_concepts JSONB DEFAULT '[]',
    content TEXT NOT NULL,
    resources JSONB DEFAULT '[]',
    interview_tips JSONB DEFAULT '[]',
    embedding vector(1536),                  -- pgvector 向量 (语义搜索)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_kp_embedding ON knowledge_points
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 8. API 接口设计

### 8.1 API 总览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 用户 | POST | `/api/auth/register` | 注册 |
| 用户 | POST | `/api/auth/login` | 登录 |
| 录音 | POST | `/api/recordings/upload` | 上传音频文件 |
| 录音 | GET | `/api/recordings` | 录音列表 |
| 录音 | GET | `/api/recordings/{id}` | 录音详情（含转写） |
| 录音 | DELETE | `/api/recordings/{id}` | 删除录音 |
| 转写 | WS | `/ws/asr/stream` | 实时流式转写 |
| 转写 | POST | `/api/recordings/{id}/transcribe` | 触发离线转写 |
| 简历 | POST | `/api/resumes/upload` | 上传简历 |
| 简历 | GET | `/api/resumes` | 简历列表 |
| 简历 | GET | `/api/resumes/{id}` | 简历详情 |
| 分析 | POST | `/api/interview/analyze` | 创建面试分析 |
| 分析 | GET | `/api/interview/reports` | 分析报告列表 |
| 分析 | GET | `/api/interview/reports/{id}` | 报告详情 |
| 分析 | GET | `/api/interview/reports/{id}/pdf` | 导出 PDF |
| 导出 | GET | `/api/export/{recording_id}/{format}` | 导出转写文本 (txt/docx/pdf/srt) |
| 知识点 | GET | `/api/knowledge-points/search` | 语义搜索知识点 |

### 8.2 核心 API 详细设计

#### 上传音频并触发转写

```
POST /api/recordings/upload
Content-Type: multipart/form-data

Request:
  file: audio.mp3 (binary)
  title: "前端面试-腾讯-20240115"
  language: "zh"

Response 201:
{
  "id": "uuid",
  "title": "前端面试-腾讯-20240115",
  "audio_duration": 1834.5,
  "status": "pending",
  "created_at": "2026-01-15T10:30:00Z"
}
```

#### 实时流式转写 (WebSocket)

```
WS /ws/asr/stream

Client -> Server (binary):
  音频块 (PCM 16kHz 16bit mono, 每块 3200 bytes ≈ 100ms)

Server -> Client (JSON):
{
  "type": "partial_result",      // 中间结果（实时）
  "text": "请简单介绍一",
  "is_final": false,
  "timestamp": 12.5
}

{
  "type": "final_result",        // 最终确认结果
  "text": "请简单介绍一下你自己",
  "speaker": "面试官",
  "is_final": true,
  "start_time": 12.5,
  "end_time": 15.2
}

{
  "type": "error",
  "message": "识别服务异常",
  "code": "ASR_ERROR"
}
```

#### 面试分析

```
POST /api/interview/analyze
Content-Type: application/json

Request:
{
  "recording_id": "uuid",
  "resume_id": "uuid",           // 可选
  "job_description": "JD文本",    // 可选
  "language": "zh"
}

Response 202:
{
  "task_id": "celery-task-uuid",
  "status": "processing",
  "estimated_time": 60           // 预估完成时间(秒)
}
```

#### 获取分析报告

```
GET /api/interview/reports/{id}

Response 200:
{
  "id": "uuid",
  "overall_score": 78,
  "strengths": [
    "项目经验描述清晰，STAR 法则运用较好",
    "基础技术问题回答准确"
  ],
  "weaknesses": [
    "系统设计类问题回答不够结构化",
    "行为面试中缺少量化成果"
  ],
  "qa_pairs": [
    {
      "id": "uuid",
      "question": "React 的虚拟 DOM 原理是什么？",
      "category": "technical",
      "your_answer": "虚拟DOM就是用JS对象来模拟真实DOM...",
      "best_answer": "虚拟DOM是React的核心优化机制。它的核心思想是...",
      "answer_score": 75,
      "improvement_suggestions": "可以从Reconciliation算法角度补充..."
    }
  ],
  "knowledge_points": [
    {
      "id": "uuid",
      "title": "React 虚拟 DOM",
      "category": "前端技术",
      "key_concepts": ["Virtual DOM", "Reconciliation", "Fiber"],
      "content": "虚拟DOM是一种用JS对象模拟DOM结构的编程概念...",
      "resources": [
        {"title": "React 官方文档", "url": "https://react.dev/..."}
      ],
      "interview_tips": [
        "为什么需要虚拟 DOM？",
        "Diff 算法三原则",
        "Fiber 架构解决了什么问题？"
      ]
    }
  ],
  "improvement_plan": [
    {"week": 1, "focus": "系统设计每日一题"},
    {"week": 2, "focus": "行为面试模拟练习"},
    {"week": 3, "focus": "技术深度专题复习"}
  ],
  "summary": "整体表现良好，基础扎实但需加强系统设计能力...",
  "created_at": "2026-01-15T12:00:00Z"
}
```

---

## 9. 开发路线图

### 9.1 总体时间线

```
Phase 1 [第1-2周]   基础架构搭建          -> 项目骨架可运行
Phase 2 [第3-4周]   核心 ASR 功能          -> 音频->文字链路打通
Phase 3 [第5-6周]   WPS 听记全功能对标     -> 功能完整度 > 80%
Phase 4 [第7-8周]   面试提升模块开发        -> 核心差异功能上线
Phase 5 [第9-10周]  优化与客户端打包        -> 产品可用，开始内测
Phase 6 [第11-12周] Beta 测试与修复        -> 正式发布 v1.0
```

### 9.2 分阶段详细任务

#### Phase 1: 基础架构 (第1-2周)

- [ ] 项目脚手架搭建（前后端 monorepo）
- [ ] Docker 开发环境配置（PostgreSQL + Redis + MinIO）
- [ ] FastAPI 基础框架 + OpenAPI 文档自动生成
- [ ] React + Vite + TailwindCSS + shadcn/ui 基础 UI
- [ ] 用户注册/登录/Token 认证
- [ ] 数据库模型 + Alembic 迁移
- [ ] Celery 异步任务框架搭建

#### Phase 2: 核心 ASR (第3-4周)

- [ ] FunASR 模型下载与本地部署
- [ ] 离线音频文件转写 API
- [ ] 说话人分离 (CAM++) 集成
- [ ] 音频上传与转写结果展示 UI
- [ ] 转写文字与音频时间同步播放
- [ ] VAD 分段 + 标点恢复后处理

#### Phase 3: WPS 听记功能对标 (第5-6周)

- [ ] 实时录音 Stream 转写 (WebSocket)
- [ ] 录音波形可视化组件
- [ ] 转写文本编辑与手动修正
- [ ] 全文搜索定位
- [ ] 智能纪要 (LLM 摘要)
- [ ] 多格式导出 (TXT/DOCX/PDF/SRT)
- [ ] 历史记录列表与管理
- [ ] 录音打点标记功能

#### Phase 4: 面试提升模块 (第7-8周)

- [ ] 简历上传与解析 (PDF/DOC)
- [ ] 简历结构化提取 (LLM)
- [ ] 面试问答对自动提取
- [ ] 问题分类与最佳答案生成
- [ ] 回答评分与改进建议
- [ ] 知识点卡片生成与展示
- [ ] 面试提升报告生成
- [ ] 报告导出 PDF

#### Phase 5: 优化与客户端 (第9-10周)

- [ ] Tauri 桌面客户端打包 (Windows/macOS)
- [ ] PWA 支持
- [ ] 性能优化 (ASR 模型量化、前端懒加载)
- [ ] 音频预处理优化（降噪增强）
- [ ] UI/UX 打磨
- [ ] 错误处理与边界情况完善

#### Phase 6: Beta 与发布 (第11-12周)

- [ ] 内测用户招募与反馈收集
- [ ] Bug 修复
- [ ] 文档完善 (用户手册 + 开发文档)
- [ ] 部署文档与一键部署脚本
- [ ] v1.0 正式发布

---

## 10. 部署方案

### 10.1 开发环境 (Docker Compose)

```yaml
# docker-compose.dev.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: tts_mianshi
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports: ["9000:9000", "9001:9001"]
    volumes: [miniodata:/data]

volumes:
  pgdata:
  miniodata:
```

### 10.2 生产环境架构

```
                         Nginx (反向代理 + HTTPS)
                                  |
                  +---------------+---------------+
                  |               |               |
                  v               v               v
           API 服务器 x2    ASR Worker (GPU)   Celery Worker
           (FastAPI)        (Paraformer)       (LLM 分析)
                  |               |               |
                  +-------+-------+-------+
                          |
            +-------------+-------------+
            v             v             v
      PostgreSQL     Redis        MinIO
      (主从复制)    (Cluster)   (对象存储)
```

**GPU 需求**:
- ASR (Paraformer-large): 推荐 NVIDIA T4 / A10，显存 ≥ 8GB
- LLM 本地部署 (Qwen2.5-7B): 推荐 NVIDIA A10 / A100，显存 ≥ 16GB
- 若使用云端 LLM API，则 ASR Worker 可降为 CPU 实例

### 10.3 推荐生产配置

| 组件 | 规格 | 数量 | 说明 |
|------|------|------|------|
| API 服务器 | 4C8G | 2 | 负载均衡 |
| ASR Worker (GPU) | T4 16GB / A10 24GB | 1-2 | FunASR 推理 |
| LLM Worker | 8C16G (调用 API) 或 A10 (本地) | 1-2 | 面试分析 |
| PostgreSQL | 4C16G + 500GB SSD | 1 主 + 1 从 | 主数据库 |
| Redis | 4C16G | 1 或 3 (Cluster) | 缓存 + 队列 |
| MinIO | 4C8G + 1TB | 1 | 文件存储 |

---

## 11. 风险与应对

| 风险 | 影响 | 概率 | 应对方案 |
|------|------|------|---------|
| FunASR 中英混合识别不准 | 转写质量下降 | 中 | 引入 Whisper 作为英文 fallback |
| 说话人分离准确率不足 | 面试官/候选人混淆 | 中 | 多通道录音 + 手动修正 UI |
| 实时转写延迟 > 2s | 用户体验差 | 低 | SenseVoice-Small 做实时引擎 + WS 优化 |
| LLM API 费用过高 | 运营成本失控 | 中 | DeepSeek 性价比方案 + 本地部署 Qwen2.5 |
| 扫描件简历 OCR 识别率低 | 简历解析失败 | 中 | PaddleOCR 优化 + 手动修正入口 |
| 面试分析质量不稳定 | 用户信任度下降 | 中 | 多轮 Prompt 迭代 + 用户反馈循环 |

---

## 附录

### A. 核心开源项目清单

| 项目 | 用途 | 许可证 | GitHub |
|------|------|--------|--------|
| FunASR | ASR 引擎（主力） | Apache 2.0 | modelscope/FunASR |
| OpenAI Whisper | ASR 引擎（辅助） | MIT | openai/whisper |
| Sherpa-ONNX | 边缘部署 ASR | Apache 2.0 | k2-fsa/sherpa-onnx |
| PyMuPDF | PDF 解析 | AGPL | pymupdf/PyMuPDF |
| python-docx | DOCX 解析 | MIT | python-openxml/python-docx |
| PaddleOCR | OCR 识别 | Apache 2.0 | PaddlePaddle/PaddleOCR |
| FastAPI | 后端框架 | MIT | fastapi/fastapi |
| Celery | 任务队列 | BSD | celery/celery |
| WaveSurfer.js | 音频波形 | BSD | katspaugh/wavesurfer.js |
| shadcn/ui | 前端组件 | MIT | shadcn-ui/ui |
| Tauri | 桌面壳 | MIT/Apache 2.0 | tauri-apps/tauri |

### B. 环境变量配置模板

```env
# === 数据库 ===
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tts_mianshi

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === MinIO ===
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=tts-mianshi

# === ASR ===
ASR_BACKEND=funasr                    # funasr | whisper | sensevoice
ASR_MODEL_DIR=/models/funasr
WHISPER_MODEL=large-v3                # tiny | base | small | medium | large-v3

# === LLM ===
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
LLM_MAX_TOKENS=4096

# === JWT ===
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# === 应用 ===
DEBUG=false
CORS_ORIGINS=http://localhost:5173,http://localhost:1420
```

---

> **下一步**: 按照 Phase 1 计划开始基础架构搭建。  
> **维护者**: 项目团队  
> **最后更新**: 2026-06-04
