"""PLLI LIVE experimental metadata-only monitor."""
import argparse, json, re, subprocess, sys, urllib.request
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

PAGE = "https://weverse.io/plave/live"
TOPIC = "plli-live-lab-76c19f804b3e"
STATE = Path(__file__).with_name("sent.json")
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        if tag != "a": return
        href = dict(attrs).get("href")
        if not href: return
        u = urlsplit(urljoin(PAGE, href))
        if u.scheme == "https" and u.netloc == "weverse.io" and re.fullmatch(r"/plave/live/[0-9]+-[0-9]+/?", u.path):
            url = "https://weverse.io" + u.path.rstrip("/")
            if url not in self.urls: self.urls.append(url)

def get_links():
    req = urllib.request.Request(PAGE, headers={"User-Agent": "PLLI-LIVE-metadata-monitor/0.1", "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read(8_000_000).decode("utf-8", "replace")
    parser = Links()
    parser.feed(html)
    if not parser.urls: raise RuntimeError("No public live links found; detection unavailable.")
    return parser.urls[:3]

def inspect(url):
    proc = subprocess.run([sys.executable, "-m", "yt_dlp", "--ignore-config", "--skip-download", "--ignore-no-formats-error", "--no-playlist", "--socket-timeout", "15", "--retries", "0", "--extractor-retries", "0", "--dump-single-json", url], capture_output=True, text=True, timeout=60)
    if proc.returncode: raise RuntimeError("Metadata unavailable: " + url)
    data = json.loads(proc.stdout)
    status = data.get("live_status")
    if status not in {"is_live", "is_upcoming", "was_live", "post_live", "not_live"}:
        raise RuntimeError("Unknown live status: " + url)
    return status, str(data.get("title") or "위버스 라이브")

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
    failed = False
    for url in get_links():
        try:
            status, title = inspect(url)
            print(url, status)
            if mode == "send" and status == "is_live" and url not in sent:
                notify(url, title)
                sent.append(url)
                STATE.write_text(json.dumps(sent[-200:], indent=2) + "\n")
        except Exception as e:
            print(type(e).__name__, str(e), file=sys.stderr)
            failed = True
    if failed: sys.exit(1)
if __name__ == "__main__":
    main()
