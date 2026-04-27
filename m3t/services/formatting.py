import re

from m3t.config import MESSAGE_FORMATS, SEND_TRUE


TEMPLATE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VARIABLE_RE = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})")


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def extract_variables(*texts: str) -> list[str]:
    variables: set[str] = set()
    for text in texts:
        variables.update(VARIABLE_RE.findall(text or ""))
    return sorted(variables)


def format_with_values(text: str, values: dict[str, str]) -> str:
    return VARIABLE_RE.sub(lambda match: str(values.get(match.group(1), match.group(0))), text or "")


def normalize_send(value: str) -> str:
    return "yes" if (value or "").strip().lower() in SEND_TRUE else "no"


def normalize_message_format(value: str) -> str:
    value = (value or "").strip().lower()
    return value if value in MESSAGE_FORMATS else "html"


def should_send(row: dict[str, str]) -> bool:
    return (row.get("send", "") or "").strip().lower() in SEND_TRUE
