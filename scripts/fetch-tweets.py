#!/usr/bin/env python3
"""
Fetch recent original tweets from a public X profile via Twitter's own
syndication endpoint (the same one the embed widget uses). No API key.

Writes data/tweets.json in the shape the site's render.js expects:
  [{ "text": str, "date": "Mon DD, YYYY", "handle": str, "url": str }]

Usage:
  python3 scripts/fetch-tweets.py [--handle HANDLE] [--limit N]

Default: handle=ai, limit=12, writes to ../data/tweets.json relative to this file.
"""
from __future__ import annotations
import argparse, datetime as dt, gzip, json, pathlib, re, sys, time, urllib.error, urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)
URL = "https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"

# Browser-mimicry headers — Twitter rate-limits naked python-urllib hard from
# datacenter IP ranges. Looking like Safari + having a Referer dramatically
# improves the success rate from GitHub Actions runners.
BROWSER_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://platform.twitter.com/",
    "Cache-Control": "no-cache",
}


def fetch_timeline_html(handle: str, max_retries: int = 3) -> str:
    url = URL.format(handle=handle)
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=BROWSER_HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                return data.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 403) and attempt < max_retries - 1:
                wait = 5 * (3 ** attempt)        # 5s, 15s, 45s
                print(f"  HTTP {e.code} from syndication; retry in {wait}s "
                      f"(attempt {attempt+1}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            raise


def extract_tweets(html: str) -> list[dict]:
    """Pull the __NEXT_DATA__ JSON blob and walk it for tweet objects."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("syndication response missing __NEXT_DATA__ blob")
    data = json.loads(m.group(1))

    out: list[dict] = []
    seen: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            if {"full_text", "created_at", "id_str"}.issubset(node.keys()):
                if node["id_str"] not in seen:
                    seen.add(node["id_str"])
                    out.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return out


def filter_originals(tweets: list[dict], handle: str) -> list[dict]:
    """Keep tweets authored by `handle` that aren't replies. Quote tweets ok."""
    h = handle.lower()
    keep = []
    for t in tweets:
        if (t.get("user") or {}).get("screen_name", "").lower() != h:
            continue                                # retweet / not theirs
        if t.get("in_reply_to_status_id_str"):
            continue                                # reply
        keep.append(t)
    return keep


def strip_trailing_media_url(text: str) -> str:
    """Twitter appends a t.co URL for attached media; strip it for cleaner cards."""
    return re.sub(r"\s+https://t\.co/\S+\s*$", "", text).strip()


def format_date(created_at: str) -> str:
    # e.g. "Fri Sep 26 20:32:26 +0000 2025"
    try:
        d = dt.datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        return d.strftime("%b %-d, %Y")
    except ValueError:
        return created_at


def to_record(t: dict) -> dict:
    handle = (t.get("user") or {}).get("screen_name", "")
    return {
        "text": strip_trailing_media_url(t["full_text"]),
        "date": format_date(t["created_at"]),
        "handle": handle,
        "url": f"https://x.com/{handle}/status/{t['id_str']}",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--handle", default="ai")
    p.add_argument("--limit", type=int, default=12)
    p.add_argument(
        "--out",
        default=str(pathlib.Path(__file__).resolve().parent.parent / "data" / "tweets.json"),
    )
    args = p.parse_args()

    try:
        html = fetch_timeline_html(args.handle)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        # Persistent fetch failure (e.g. Twitter blocking GH runner IP). Don't
        # fail the workflow — last-good tweets.json keeps serving. Cron will
        # try again next hour.
        print(f"fetch failed permanently: {e}; keeping existing tweets.json",
              file=sys.stderr)
        return 0

    raw = extract_tweets(html)
    originals = filter_originals(raw, args.handle)
    # syndication returns newest-first already; preserve that order.
    records = [to_record(t) for t in originals[: args.limit]]

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"wrote {len(records)} tweets to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
