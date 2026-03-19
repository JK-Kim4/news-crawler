from datetime import datetime, timezone
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="ui/templates")


def relative_time(value):
    if not value:
        return "-"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - value.astimezone(timezone.utc)
    seconds = max(int(delta.total_seconds()), 0)
    if seconds < 60:
        return "방금 전"
    if seconds < 3600:
        return f"{seconds // 60}분 전"
    if seconds < 86400:
        return f"{seconds // 3600}시간 전"
    if seconds < 604800:
        return f"{seconds // 86400}일 전"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d")


def score_badge_class(score):
    if score >= 90:
        return "bg-sky-100 text-sky-800 ring-sky-200"
    if score >= 70:
        return "bg-emerald-100 text-emerald-800 ring-emerald-200"
    return "bg-amber-100 text-amber-800 ring-amber-200"


def country_label(country):
    return "한국" if country == "kr" else "해외"


def country_flag(country):
    return "KR" if country == "kr" else "GL"


templates.env.globals.update(
    relative_time=relative_time,
    score_badge_class=score_badge_class,
    country_label=country_label,
    country_flag=country_flag,
)
