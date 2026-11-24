"""Prototype: filter already-authorized Weverse notification card text.
No login credentials, account data, or notification bodies are stored or logged.
"""
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256

KST = timezone(timedelta(hours=9))
MEMBERS = {"YEJUN": "예준", "NOAH": "노아", "BAMBY": "밤비", "EUNHO": "은호", "HAMIN": "하민", "PLAVE": "플레이브"}
START = re.compile(r"(?:^|[🔴\s])(" + "|".join(MEMBERS) + r")\s*님이\s*LIVE를\s*시작했습니다(?=\s|:|[.!]|$)", re.I)
STAMP = re.compile(r"\bPLAVE\s*[·・]\s*(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2})\b", re.I)

def parse_card(text):
    text = " ".join(text.split())
    m, t = START.search(text), STAMP.search(text)
    if not m or not t:
        return None
    try:
        when = datetime.strptime(t.group(1), "%Y.%m.%d %H:%M").replace(tzinfo=KST)
    except ValueError:
        return None
    member = m.group(1).upper()
    key = sha256(f"{member}|{when.isoformat()}".encode()).hexdigest()
    return {"id": key, "member": MEMBERS[member], "when": when}

def select_new(cards, seen, now, initialized):
    events = {}
    for card in cards:
        event = parse_card(card)
        if event:
            events[event["id"]] = event
    # On first run, establish a baseline; never replay historical alerts.
    if not initialized:
        return [], seen | set(events)
    result = [e for key, e in events.items() if key not in seen and timedelta(0) <= now - e["when"] <= timedelta(minutes=15)]
    return sorted(result, key=lambda e: e["when"]), seen | set(events)

if __name__ == "__main__":
    sample = "🔴 BAMBY님이 LIVE를 시작했습니다 : 📞 PLAVE · 2026.11.23 22:23"
    chat = "EUNHO님이 BAMBY님의 LIVE에 채팅을 작성했습니다 PLAVE · 2026.11.23 22:27"
    assert parse_card(sample)["member"] == "밤비"
    assert parse_card(chat) is None
    assert parse_card("NOTICE: PLAVE · 2026.11.23 14:00") is None
    assert parse_card(sample.replace("PLAVE ·", "OTHER ·")) is None
    now = datetime(2026,11,23,22,28,tzinfo=KST)
    alerts, seen = select_new([sample], set(), now, False)
    assert not alerts and len(seen)==1
    alerts, _ = select_new([sample], seen, now, True)
    assert not alerts
    alerts, _ = select_new([sample, sample], set(), now, True)
    assert len(alerts)==1
    alerts, _ = select_new([sample], set(), now+timedelta(hours=2), True)
    assert not alerts
    print("All notification filtering checks passed; no network or push performed.")
