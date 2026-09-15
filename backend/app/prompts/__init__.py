from app.prompts.prompt_v1 import SYSTEM_PROMPT as PROMPT_V1, VERSION_INFO as INFO_V1
from app.prompts.prompt_v2 import SYSTEM_PROMPT as PROMPT_V2, VERSION_INFO as INFO_V2
from app.prompts.prompt_v3 import SYSTEM_PROMPT as PROMPT_V3, VERSION_INFO as INFO_V3
from app.prompts.prompt_v4 import SYSTEM_PROMPT as PROMPT_V4, VERSION_INFO as INFO_V4

PROMPT_REGISTRY = {
    "v1": {
        "info": INFO_V1,
        "prompt": PROMPT_V1
    },
    "v2": {
        "info": INFO_V2,
        "prompt": PROMPT_V2
    },
    "v3": {
        "info": INFO_V3,
        "prompt": PROMPT_V3
    },
    "v4": {
        "info": INFO_V4,
        "prompt": PROMPT_V4
    }
}

def get_prompt_by_version(version: str) -> str:
    v = version.lower().strip()
    if v in PROMPT_REGISTRY:
        return PROMPT_REGISTRY[v]["prompt"]
    return PROMPT_REGISTRY["v4"]["prompt"]
