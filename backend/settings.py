"""Server-only configuration. Never expose credentials through the API."""
import os
from pathlib import Path

def load_local_env():
    path = Path(__file__).resolve().parent.parent / '.env.local'
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                name, value = line.split('=', 1)
                os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

load_local_env()

def setting(name, default):
    return os.environ.get(name, default)

def api_key():
    return os.environ.get('DASHSCOPE_API_KEY', '').strip()

def live_enabled():
    return setting('PAPERMIND_MODE', 'live') != 'fixture' and bool(api_key())

def models():
    return {
        'planner': setting('PAPERMIND_MODEL_PLANNER', 'qwen3.5-plus'),
        'composer': setting('PAPERMIND_MODEL_COMPOSER', 'qwen3.5-plus'),
        'reviewer': setting('PAPERMIND_MODEL_REVIEWER', 'qwen-plus'),
        'copilot': setting('PAPERMIND_MODEL_COPILOT', 'qwen-plus'),
        'vision': setting('PAPERMIND_MODEL_VISION', 'qwen3-vl-plus'),
        'ocr': setting('PAPERMIND_MODEL_OCR', 'qwen3.5-ocr'),
        'search': setting('PAPERMIND_MODEL_SEARCH', 'qwen-plus'),
    }

BASE = setting('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1').rstrip('/')
NATIVE = setting('DASHSCOPE_NATIVE_URL', 'https://dashscope.aliyuncs.com/api/v1').rstrip('/')

def sanitize(message):
    value = str(message)
    return value.replace(api_key(), '[REDACTED]')[:1200] if api_key() else value[:1200]
