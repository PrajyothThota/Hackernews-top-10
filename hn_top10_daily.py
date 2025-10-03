#!/usr/bin/env python3
"""
hn_top10_daily.py
Fetch the top 10 "new" Hacker News stories from the past 24 hours (Asia/Kolkata),
ranked by score. Outputs to terminal by default; optional CSV and Markdown outputs.

Usage:
  python hn_top10_daily.py
  python hn_top10_daily.py --csv top10.csv
  python hn_top10_daily.py --md top10.md
  python hn_top10_daily.py --limit 400 --window-hours 24

Scheduling (cron example, runs daily at 8:00 IST):
  0 8 * * * /usr/bin/python3 /path/to/hn_top10_daily.py --csv ~/hn_top10.csv

Requirements: Python 3.9+ (uses zoneinfo). No external dependencies.
"""

import argparse
import concurrent.futures as cf
import csv
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    print("This script requires Python 3.9+ for zoneinfo.", file=sys.stderr)
    sys.exit(1)

API_BASE = "https://hacker-news.firebaseio.com/v0"
NEW_STORIES_ENDPOINT = f"{API_BASE}/newstories.json"
ITEM_ENDPOINT = f"{API_BASE}/item/{{id}}.json"
HN_ITEM_URL = "https://news.ycombinator.com/item?id={id}"

HEADERS = {
    "User-Agent": "HNTop10Daily/1.0 (+https://news.ycombinator.com/)"
}

@dataclass
class Story:
    id: int
    title: str
    url: Optional[str]
    score: int
    by: str
    time: int
    descendants: int

    @property
    def hn_link(self) -> str:
        return HN_ITEM_URL.format(id=self.id)

    @property
    def created_at_ist(self) -> str:
        dt = datetime.fromtimestamp(self.time, tz=timezone.utc).astimezone(ZoneInfo("Asia/Kolkata"))
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def fetch_json(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as e:
        return None

def get_new_story_ids() -> List[int]:
    data = fetch_json(NEW_STORIES_ENDPOINT)
    if not isinstance(data, list):
        return []
    return data  # newest first

def get_item(story_id: int) -> Optional[Story]:
    data = fetch_json(ITEM_ENDPOINT.format(id=story_id))
    if not data or data.get("type") != "story":
        return None
    return Story(
        id=data.get("id"),
        title=data.get("title") or "(no title)",
        url=data.get("url"),
        score=int(data.get("score") or 0),
        by=data.get("by") or "unknown",
        time=int(data.get("time") or 0),
        descendants=int(data.get("descendants") or 0),
    )

def human_trunc(s: str, max_len: int = 100) -> str:
    s = s or ""
    return s if len(s) <= max_len else s[:max_len - 1] + "…"

def collect_top_new(limit: int, window_hours: int) -> List[Story]:
    ids = get_new_story_ids()[:limit]
    if not ids:
        return []

    # Parallel fetch for speed
    stories: List[Story] = []
    with cf.ThreadPoolExecutor(max_workers=24) as ex:
        for story in ex.map(get_item, ids):
            if story:
                stories.append(story)

    # Filter to last window
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    cutoff_utc = (now_ist - timedelta(hours=window_hours)).astimezone(timezone.utc)
    cutoff_ts = int(cutoff_utc.timestamp())
    recent = [s for s in stories if s.time >= cutoff_ts]

    # Rank by score desc, then comments, then recency
    recent.sort(key=lambda s: (s.score, s.descendants, s.time), reverse=True)
    return recent[:10]

def print_table(stories: List[Story]) -> None:
    if not stories:
        print("No stories found in the specified window.")
        return

    # Simple fixed-width table
    headers = ["#", "Title", "Score", "Comments", "By", "Created (IST)", "HN Link", "URL"]
    rows = []
    for i, s in enumerate(stories, 1):
        rows.append([
            i,
            human_trunc(s.title, 80),
            s.score,
            s.descendants,
            s.by,
            s.created_at_ist,
            s.hn_link,
            human_trunc(s.url or s.hn_link, 80),
        ])

    col_widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    def fmt_row(row):
        return " | ".join(str(v).ljust(w) for v, w in zip(row, col_widths))

    print(fmt_row(headers))
    print("-+-".join("-" * w for w in col_widths))
    for r in rows:
        print(fmt_row(r))

def write_csv(stories: List[Story], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "id", "title", "score", "comments", "by", "created_ist", "hn_link", "url"])
        for i, s in enumerate(stories, 1):
            w.writerow([i, s.id, s.title, s.score, s.descendants, s.by, s.created_at_ist, s.hn_link, s.url or ""])

def write_md(stories: List[Story], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Top 10 New Hacker News (last 24h, IST)\n\n")
        for i, s in enumerate(stories, 1):
            url = s.url or s.hn_link
            f.write(f"{i}. [{s.title}]({url}) — **{s.score} points**, {s.descendants} comments — {s.created_at_ist} — [HN]({s.hn_link})\n")

def main():
    parser = argparse.ArgumentParser(description="Top 10 'new' Hacker News stories from the past 24h (IST), ranked by score.")
    parser.add_argument("--limit", type=int, default=400, help="Number of newest stories to inspect (default: 400).")
    parser.add_argument("--window-hours", type=int, default=24, help="Lookback window in hours (default: 24).")
    parser.add_argument("--csv", type=str, default=None, help="Optional path to write CSV output.")
    parser.add_argument("--md", type=str, default=None, help="Optional path to write Markdown output.")
    args = parser.parse_args()

    stories = collect_top_new(limit=args.limit, window_hours=args.window_hours)

    print_table(stories)

    if args.csv:
        write_csv(stories, args.csv)
        print(f"\nSaved CSV to {args.csv}")
    if args.md:
        write_md(stories, args.md)
        print(f"Saved Markdown to {args.md}")

if __name__ == "__main__":
    main()
