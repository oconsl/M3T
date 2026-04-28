import re
import random
from collections.abc import Callable

from m3t.config import MESSAGE_FORMATS, SEND_TRUE


TEMPLATE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VARIABLE_RE = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})")
DYNAMIC_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DYNAMIC_VARIABLE_RE = re.compile(r"(?<!\{)\{dynamic\.([A-Za-z_][A-Za-z0-9_]*)\}(?!\})")


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def extract_variables(*texts: str) -> list[str]:
    variables: set[str] = set()
    for text in texts:
        variables.update(VARIABLE_RE.findall(text or ""))
    return sorted(variables)


def extract_dynamic_variables(*texts: str) -> list[str]:
    variables: set[str] = set()
    for text in texts:
        variables.update(DYNAMIC_VARIABLE_RE.findall(text or ""))
    return sorted(variables)


def render_dynamic_values(
    text: str,
    dynamic_options: dict[str, list[str]],
    choices: dict[str, str] | None = None,
    chooser: Callable[[list[str]], str] = random.choice,
) -> str:
    choices = choices if choices is not None else {}

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in choices:
            return choices[key]
        options = dynamic_options.get(key) or []
        if not options:
            return match.group(0)
        choices[key] = chooser(options)
        return choices[key]

    return DYNAMIC_VARIABLE_RE.sub(replace, text or "")


def format_with_values(text: str, values: dict[str, str]) -> str:
    return VARIABLE_RE.sub(lambda match: str(values.get(match.group(1), match.group(0))), text or "")


def render_template_text(
    text: str,
    values: dict[str, str],
    dynamic_options: dict[str, list[str]] | None = None,
    dynamic_choices: dict[str, str] | None = None,
    chooser: Callable[[list[str]], str] = random.choice,
) -> str:
    dynamic_text = render_dynamic_values(text, dynamic_options or {}, dynamic_choices, chooser)
    return format_with_values(dynamic_text, values)


def normalize_send(value: str) -> str:
    return "yes" if (value or "").strip().lower() in SEND_TRUE else "no"


def normalize_message_format(value: str) -> str:
    value = (value or "").strip().lower()
    return value if value in MESSAGE_FORMATS else "html"


def should_send(row: dict[str, str]) -> bool:
    return (row.get("send", "") or "").strip().lower() in SEND_TRUE
