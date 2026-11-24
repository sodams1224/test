"""PLLI LIVE experimental metadata-only monitor."""
import argparse, json, re, subprocess, sys, urllib.request
from pathlib import Path

PAGE = "https://weverse.io/plave/live"
TOPIC = "plli-live-lab-76c19f804b3e"
STATE = Path(__file__).with_name("sent.json")
def inspect():
    proc = subprocess.run([sys.executable, "-m", "yt_dlp", "--ignore-config", "--skip-download", "--ignore-no-formats-error", "--no-playlist", "--socket-timeout", "15", "--retries", "0", "--extractor-retries", "0", "--dump-single-json", PAGE], capture_output=True, text=True, timeout=60)
    if proc.returncode:
        if "The channel is not currently live" in proc.stderr and "[WeverseLive]" in proc.stderr:
            return "offline", None, None
        print(proc.stderr[-2000:], file=sys.stderr)
        raise RuntimeError("Unable to verify live status")
    data = json.loads(proc.stdout)
    status = data.get("live_status")
    if status not in {"is_live", "is_upcoming", "was_live", "post_live", "not_live"}:
        raise RuntimeError("Unknown live status")
    match = re.fullmatch(r"[0-9]+-[0-9]+", str(data.get("id", "")))
    if not match:
        raise RuntimeError("Unexpected broadcast ID")
    return status, PAGE + "/" + match.group(), str(data.get("title") or "위버스 라이브")

def notify(url, title, test=False):
    payload = {"topic": TOPIC, "title": "[테스트] 플레이브 라이브 알림" if test else "플레이브 라이브 방송 시작!", "message": "테스트 알림입니다. 실제 방송 아님" if test else "🔴 " + title + " · 지금 위버스에서 만나보세요", "priority": 5, "click": url, "tags": ["rotating_light"]}
    req = urllib.request.Request("https://ntfy.sh/", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.load(resp)
        if not result.get("id"): raise RuntimeError("Push response has no id.")
        print("Push accepted:", result["id"])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["check", "send", "test"], default="check")
    mode = p.parse_args().mode
    if mode == "test":
        notify(PAGE, "", test=True)
        return
    sent = json.loads(STATE.read_text()) if STATE.exists() else []
    status, url, title = inspect()
    print("Weverse live status:", status, url or "")
    if mode == "send" and status == "is_live" and url not in sent:
        notify(url, title)
        sent.append(url)
        STATE.write_text(json.dumps(sent[-200:], indent=2) + "\n")
if __name__ == "__main__":
    main()
