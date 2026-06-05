"""Download and set up FunASR models for development"""
import os, sys, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("download_models")

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models", "funasr")
os.makedirs(MODELS_DIR, exist_ok=True)

REQUIRED = [
    ("VAD", "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"),
    ("Speaker Embedding", "iic/speech_eres2netv2_sv_zh-cn_16k-common"),
    ("ASR + VAD + Punctuation", "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch"),
    ("Punctuation", "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"),
]


def main():
    logger.info("=" * 60)
    logger.info("FunASR Model Downloader")
    logger.info("Models directory: %s", MODELS_DIR)
    logger.info("=" * 60)
    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError:
        logger.error("modelscope not installed. Run: pip install modelscope")
        sys.exit(1)
    for name, model_id in REQUIRED:
        logger.info("Downloading %s: %s ...", name, model_id)
        try:
            snapshot_download(model_id, cache_dir=MODELS_DIR)
            logger.info("  ✅ %s downloaded successfully", name)
        except Exception as e:
            logger.error("  ❌ %s download failed: %s", name, e)
    logger.info("=" * 60)
    logger.info("All models downloaded to: %s", MODELS_DIR)
    logger.info("")
    logger.info('Usage: Set ASR_BACKEND=funasr in environment')
    logger.info('Or run: $env:ASR_BACKEND="funasr" (Windows)')
    logger.info("       export ASR_BACKEND=funasr (Linux/Mac)")
    logger.info("Then start the backend and FunASR will use local models.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
