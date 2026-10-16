import os
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
KOL_DATA_PATH = ROOT / "kol_data.json"
OUTPUT_DIR = ROOT / "output"
TEMPLATE_DIR = ROOT / "templates"

# 也支持从 config.yaml 读取
CONFIG_YAML = ROOT / "config.yaml"

# 默认推送方式：一对一（只发给自己），因此这里留空。
# 需要一对多（群组广播）时，任选其一开启：
#   - 改 config.yaml 的 pushplus_topic
#   - 设环境变量 PUSHPLUS_TOPIC
#   - 运行时 `python main.py --topic 你的群组编码`
# （原先默认的一对多群组编码为 `oai.1`，群组名 oai.1；如需恢复一对多，填回该编码即可。）
DEFAULT_PUSHPLUS_TOPIC = ""


def _load_config_yaml() -> dict:
    """读取 config.yaml；文件缺失、pyyaml 未安装或解析失败时返回空字典（不阻断主流程）。"""
    if not CONFIG_YAML.exists():
        return {}
    try:
        import yaml
    except ImportError:
        print(f"[config] 未安装 pyyaml，跳过 {CONFIG_YAML.name}（pip install pyyaml）")
        return {}
    try:
        with open(CONFIG_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"[config] 解析 {CONFIG_YAML.name} 失败：{type(exc).__name__}: {exc}")
        return {}


_YAML_CONFIG = _load_config_yaml()


def get_setting(env_key: str, yaml_key: str = "", default: str = "") -> str:
    """取值优先级：环境变量 > config.yaml > 默认值（空字符串一律视为未配置）。"""
    candidates = [os.getenv(env_key, "")]
    if yaml_key:
        candidates.append(str(_YAML_CONFIG.get(yaml_key, "") or ""))
    for candidate in candidates:
        candidate = candidate.strip()
        if candidate:
            return candidate
    return default


def get_int_setting(env_key: str, yaml_key: str = "", default: int = 0) -> int:
    raw = get_setting(env_key, yaml_key, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"[config] {env_key or yaml_key} = {raw!r} 不是整数，回退默认值 {default}")
        return default


# PushPlus 配置
PUSHPLUS_TOKEN = get_setting("PUSHPLUS_TOKEN", "pushplus_token")
PUSHPLUS_URL = get_setting("PUSHPLUS_URL", default="http://www.pushplus.plus/send")
# 群组编码（一对多）：填了就把战报推给群组内所有订阅者；留空 = 一对一，仅推送给自己
PUSHPLUS_TOPIC = get_setting("PUSHPLUS_TOPIC", "pushplus_topic", DEFAULT_PUSHPLUS_TOPIC)
PUSHPLUS_CHANNEL = get_setting("PUSHPLUS_CHANNEL", "pushplus_channel", "wechat")
PUSHPLUS_TEMPLATE = get_setting("PUSHPLUS_TEMPLATE", "pushplus_template", "html")

# 抓取配置
ACTIVE_THRESHOLD_DAYS = get_int_setting("KOL_ACTIVE_THRESHOLD_DAYS", "active_threshold_days", 90)  # 90天内有更新视为活跃
REQUEST_TIMEOUT = get_int_setting("KOL_REQUEST_TIMEOUT", "request_timeout", 12)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 报告配置
REPORT_TITLE = get_setting("KOL_REPORT_TITLE", "report_title", "全球财经金融 KOL 精选名单 · 多空全景战报")
AUTHOR = get_setting("KOL_AUTHOR", "author", "章鱼 AI·全景分析")
REPORT_DATE_FORMAT = "%Y年%m月%d日"

def load_kols():
    with open(KOL_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
