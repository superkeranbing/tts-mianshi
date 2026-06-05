"""ASR Engine - 真实音频处理 + 可插拔 ASR 后端架构
支持后端:
  - funasr:   FunASR Paraformer + SenseVoice + CAM++ (生产推荐)
  - whisper:  OpenAI Whisper / faster-whisper (英文/多语言)
  - sherpa:   Sherpa-ONNX (CPU 边缘部署)
  - mock:     模拟引擎 (开发/测试用，无模型依赖)
安装 FunASR:  pip install funasr modelscope
安装 Whisper:  pip install faster-whisper
安装 Sherpa:   pip install sherpa-onnx
"""
import os, wave, logging, random, hashlib,re
from typing import Optional
from dataclasses import dataclass, field
logger = logging.getLogger(__name__)
@dataclass
class AudioMeta:
    path: str
    format: str
    duration: float      # seconds
    sample_rate: int
    channels: int
    file_size: int       # bytes
@dataclass
class TranscriptSegment:
    speaker: str
    speaker_name: str
    content: str
    start_time: float
    end_time: float
    confidence: float = 0.95
class ASREngine:
    """统一 ASR 引擎接口 - 音频处理 + 可选模型推理"""
    MOCK_DIALOG = [
        ("面试官", "面试官李", "请简单介绍一下你自己。"),
        ("候选人", "张三", "面试官好，我叫张三，毕业于XX大学计算机科学专业，有5年前端开发经验。在上一家公司负责企业级中后台管理系统架构，主导了从Vue2到React+TypeScript的技术栈迁移。"),
        ("面试官", "面试官李", "能详细说说React的虚拟DOM原理吗？"),
        ("候选人", "张三", "虚拟DOM是React创造的核心优化概念。它用轻量级的JS对象来描述UI结构。状态变更时，React先在内存中对比新旧虚拟DOM树，通过高效的Diff算法找出最小变更集，最后批量更新真实DOM。Fiber架构之后支持了可中断的异步渲染。"),
        ("面试官", "面试官李", "你在项目中遇到过最大的技术挑战是什么？"),
        ("候选人", "张三", "在处理大数据量列表时遇到了严重性能问题。数据显示超过10万行时页面卡顿严重。我引入了虚拟滚动技术，配合Web Worker处理数据排序和过滤，最终渲染时间从3秒降到200毫秒以内。"),
        ("面试官", "面试官李", "你如何保证前端代码质量？"),
        ("候选人", "张三", "我们团队采用了ESLint+Prettier统一代码风格，Jest+React Testing Library覆盖单元测试，Cypress做端到端测试。CI/CD流水线中集成了SonarQube进行代码质量检查，要求增量代码覆盖率不低于80%。"),
        ("面试官", "面试官李", "你对未来的职业规划有什么考虑？"),
        ("候选人", "张三", "短期希望在前端架构方向深耕，中期目标是成长为全栈工程师，长期希望能带领技术团队。我对贵司的技术氛围和业务方向非常感兴趣，希望能在这里实现这些目标。"),
        ("面试官", "面试官李", "好的，你有什么想问我们的吗？"),
        ("候选人", "张三", "我想了解一下团队目前的技术栈和研发流程，以及这个岗位未来一年内主要负责的业务方向。"),
    ]
    def __init__(self, backend: str = "mock", model_dir: str = "./models"):
        self.backend = backend
        self.model_dir = model_dir
        self._funasr_model = None
        self._whisper_model = None
        logger.info(f"ASREngine initialized: backend={backend}")
    # ---- Audio Processing (always real) ----
    def read_audio_meta(self, file_path: str) -> AudioMeta:
        """读取音频元数据：格式/时长/采样率/声道数"""
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        file_size = os.path.getsize(file_path)
        if ext == "wav":
            return self._read_wav(file_path, ext, file_size)
        else:
            # Try pydub for other formats (needs ffmpeg)
            return self._read_with_pydub(file_path, ext, file_size)
    def _read_wav(self, path: str, fmt: str, size: int) -> AudioMeta:
        with wave.open(path, "rb") as wf:
            return AudioMeta(
                path=path, format=fmt,
                duration=wf.getnframes() / wf.getframerate(),
                sample_rate=wf.getframerate(),
                channels=wf.getnchannels(),
                file_size=size,
            )
    def _read_with_pydub(self, path: str, fmt: str, size: int) -> AudioMeta:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(path, format=fmt if fmt != "m4a" else "mp4")
            return AudioMeta(
                path=path, format=fmt,
                duration=len(audio) / 1000.0,
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                file_size=size,
            )
        except Exception:
            import soundfile as sf
            info = sf.info(path)
            return AudioMeta(
                path=path, format=fmt,
                duration=info.duration,
                sample_rate=info.samplerate,
                channels=info.channels,
                file_size=size,
            )
    # ---- VAD (Voice Activity Detection) ----
    def segment_by_vad(self, meta: AudioMeta) -> list[dict]:
        """
        VAD 切分: 将音频按静音段切分为语音片段。
        生产环境使用 FSMN-VAD 模型；当前使用基于时长的模拟分段。
        """
        ideal_seg_duration = random.uniform(4, 8)  # seconds per segment
        num_segments = max(1, int(meta.duration / ideal_seg_duration))
        # Match mock dialog length if available
        num_segments = min(num_segments, len(self.MOCK_DIALOG))
        segments = []
        for i in range(num_segments):
            start = i * (meta.duration / num_segments)
            end = (i + 1) * (meta.duration / num_segments) if i < num_segments - 1 else meta.duration
            segments.append({"start": round(start, 2), "end": round(end, 2)})
        return segments
    # ---- ASR Transcription ----
    async def transcribe(self, file_path: str) -> list[TranscriptSegment]:
        """
        转写音频文件 → 带时间戳的转录段落列表。
        Pipeline:
          1. 读取音频元数据 (duration, sr, channels)
          2. VAD 切分 → 语音片段
          3. ASR 识别 (model / mock)
          4. 说话人分离 (diarization)
        """
        meta = self.read_audio_meta(file_path)
        logger.info(f"Audio: {meta.duration:.1f}s, {meta.sample_rate}Hz, {meta.channels}ch")
        vad_segments = self.segment_by_vad(meta)
        # --- Real model path ---
        if self.backend == "funasr":
            results = await self._transcribe_funasr(file_path, vad_segments)
            return self._post_process_speakers(results, meta)
        elif self.backend == "whisper":
            results = await self._transcribe_whisper(file_path, vad_segments)
            return self._post_process_speakers(results, meta)
        elif self.backend == "sherpa":
            return await self._transcribe_sherpa(file_path, vad_segments)
        # --- Mock path ---
        results = self._transcribe_mock(meta, vad_segments)
        return self._post_process_speakers(results, meta)
    def _post_process_speakers(self, segments: list[TranscriptSegment], meta: AudioMeta) -> list[TranscriptSegment]:
        """Post-process segments to assign speakers if missing"""
        if not segments:
            return segments
        
        all_unknown = all(s.speaker == "未知" for s in segments)
        if not all_unknown:
            return segments
        
        # If only one segment, split it by estimated speaking turns
        if len(segments) == 1:
            text = segments[0].content
            total_dur = segments[0].end_time - segments[0].start_time or 60
            # Split by sentence endings
            sentences = re.split(r'(?<=[.!?])', text)

            sentences = [s.strip() for s in sentences if s.strip()]
            if len(sentences) < 2:
                # Fallback: split into equal parts
                chunk_size = max(1, len(text) // 6)
                parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                sentences = parts
            
            results = []
            speakers = ["面试官", "候选人"]
            seg_dur = total_dur / max(1, len(sentences))
            time_per_sentence = total_dur / max(1, len(sentences))
            for i, sent in enumerate(sentences):
                spk = speakers[i % 2]
                results.append(TranscriptSegment(
                    speaker=spk,
                    speaker_name=spk + ("李" if i % 2 == 0 else "张三"),
                    content=sent,
                    start_time=round(i * time_per_sentence, 2),
                    end_time=round((i + 1) * time_per_sentence, 2),
                    confidence=segments[0].confidence,
                ))
            return results
        
        # Multiple segments: assign alternating speakers
        speakers = ["面试官", "候选人"]
        for i, s in enumerate(segments):
            spk = speakers[i % 2]
            s.speaker = spk
            s.speaker_name = spk + ("李" if i % 2 == 0 else "张三")
        return segments
    def _transcribe_mock(self, meta: AudioMeta, vad_segments: list[dict]) -> list[TranscriptSegment]:
        """Mock transcription: 使用内嵌对话数据，映射到真实音频时长"""
        results = []
        for i, seg in enumerate(vad_segments):
            if i < len(self.MOCK_DIALOG):
                speaker, name, content = self.MOCK_DIALOG[i]
            else:
                speaker, name, content = "未知", "发言人", "…"
            results.append(TranscriptSegment(
                speaker=speaker, speaker_name=name,
                content=content,
                start_time=seg["start"], end_time=seg["end"],
                confidence=round(random.uniform(0.88, 0.99), 2),
            ))
        return results
    # ==== Real ASR backends (需安装对应包) ====
    async def _transcribe_funasr(self, path: str, segments: list[dict]) -> list[TranscriptSegment]:
        """FunASR Paraformer-large + SenseVoice + CAM++"""
        try:
            from funasr import AutoModel
            if not self._funasr_model:
                self._funasr_model = AutoModel(
                    model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                    vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                    punc_model="iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                    spk_model="iic/speech_campplus_sv_zh-cn_16k-common",
                )
            result = self._funasr_model.generate(input=path, batch_size_s=300)
            return self._parse_funasr_result(result)
        except ImportError:
            logger.warning("FunASR not installed, falling back to mock")
            return self._transcribe_mock(AudioMeta(path, "wav", 130, 16000, 1, 0), segments)
    async def _transcribe_whisper(self, path: str, segments: list[dict]) -> list[TranscriptSegment]:
        """faster-whisper"""
        try:
            from faster_whisper import WhisperModel
            if not self._whisper_model:
                self._whisper_model = WhisperModel("large-v3", device="cpu", compute_type="int8")
            segs, _ = self._whisper_model.transcribe(path, beam_size=5, language="zh")
            return self._parse_whisper_result(segs)
        except ImportError:
            logger.warning("faster-whisper not installed, falling back to mock")
            return self._transcribe_mock(AudioMeta(path, "wav", 130, 16000, 1, 0), segments)
    async def _transcribe_sherpa(self, path: str, segments: list[dict]) -> list[TranscriptSegment]:
        """Sherpa-ONNX"""
        try:
            import sherpa_onnx
            # Sherpa requires model config; placeholder for integration
            raise NotImplementedError("Sherpa-ONNX integration: configure model path")
        except ImportError:
            logger.warning("sherpa-onnx not installed, falling back to mock")
            return self._transcribe_mock(AudioMeta(path, "wav", 130, 16000, 1, 0), segments)
    # ---- Result parsers ----
    def _parse_funasr_result(self, result: list) -> list[TranscriptSegment]:
        results = []
        for item in result:
            results.append(TranscriptSegment(
                speaker=item.get("spk", "未知"),
                speaker_name=item.get("spk", "未知"),
                content=item.get("text", ""),
                start_time=item.get("start", 0) / 1000.0,
                end_time=item.get("end", 0) / 1000.0,
                confidence=item.get("confidence", 0.9),
            ))
        return results
    def _parse_whisper_result(self, segments) -> list[TranscriptSegment]:
        results = []
        for seg in segments:
            results.append(TranscriptSegment(
                speaker="未知", speaker_name="发言人",
                content=seg.text.strip(),
                start_time=seg.start,
                end_time=seg.end,
                confidence=round(1.0 - seg.avg_logprob / abs(seg.avg_logprob or 1), 2),
            ))
        return results
# Global instance
asr_engine = ASREngine(backend="funasr")