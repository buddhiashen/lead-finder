"""
lead_bot.py - read-only Reddit lead finder (PRAW)

Purpose: find posts where people ask to hire a writer, so the owner can
reply MANUALLY from his own account. COMMERCIAL USE: finding clients for a
freelance writing business.

This script NEVER posts, comments, votes, sends messages, or modifies
anything on Reddit. It makes one read-only request every POLL_SECONDS.
It stores only a local list of already-seen post IDs (no usernames, no content).
"""

import json
import logging
import os
import re
import time
from pathlib import Path

import praw
import requests
from prawcore.exceptions import (
    RequestException,
    ResponseException,
    ServerError,
    TooManyRequests,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# ---------------- settings ----------------
SUBREDDITS = "forhire+HireaWriter+SEO+smallbusiness+blogging+content_marketing"
POLL_SECONDS = 90            # one request per poll (~40 requests/hour)
POST_LIMIT = 25              # newest posts fetched per request
MAX_POST_AGE = 6 * 3600      # ignore posts older than 6 hours
MAX_BACKOFF = 900            # max wait after errors (15 minutes)
SEEN_FILE = Path("seen.json")
USER_AGENT = "lead-finder:v1.0 (by u/sherpa-hillery-101)"

# hiring intent + writing terms
KEYWORDS = re.compile(
    r"(need|looking for|hiring|want|seeking).{0,40}"
    r"(blog|article|seo|content|copy)\s*(writer|writing|posts?)",
    re.I,
)
# ignore people advertising their own services
SKIP = re.compile(r"\[for hire\]|\bfor hire\b|\bi offer\b|\bmy services\b", re.I)

# optional private Telegram alerts (leave unset to just print to the console)
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

# ---------------- reddit (read-only) ----------------
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent=USER_AGENT,
)
reddit.read_only = True  # no username/password; cannot take any action


def load_seen():
    try:
        return set(json.loads(SEEN_FILE.read_text()))
    except Exception:
        return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(list(seen)[-2000:]))


def alert(message):
    print("\n" + message + "\n")
    if TG_TOKEN and TG_CHAT:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={
                    "chat_id": TG_CHAT,
                    "text": message,
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
        except requests.RequestException as exc:
            logging.warning("Telegram alert failed: %s", exc)


def draft_reply(post):
    # A starting point only: I edit it and post it by hand.
    return (
        f'Hi! I saw your post about "{post.title[:60]}". I write SEO-focused '
        "articles and can send relevant samples. What's your niche and target "
        "keyword? (Edit before sending.)"
    )


def check(seen):
    for post in reddit.subreddit(SUBREDDITS).new(limit=POST_LIMIT):
        if post.id in seen:
            continue
        seen.add(post.id)
        if time.time() - post.created_utc > MAX_POST_AGE:
            continue
        text = f"{post.title} {post.selftext}"
        if SKIP.search(text) or not KEYWORDS.search(text):
            continue
        alert(
            f"LEAD in r/{post.subreddit}\n{post.title}\n"
            f"https://reddit.com{post.permalink}\n\n"
            f"Draft reply (edit, then post manually):\n{draft_reply(post)}"
        )


def main():
    seen = load_seen()
    delay = POLL_SECONDS
    while True:
        try:
            check(seen)
            save_seen(seen)
            delay = POLL_SECONDS
        except TooManyRequests as exc:
            retry_after = getattr(exc.response, "headers", {}).get("Retry-After", 120)
            delay = max(int(retry_after), 120)
            logging.warning("Rate limited, sleeping %ss", delay)
        except (RequestException, ServerError, ResponseException) as exc:
            delay = min(delay * 2, MAX_BACKOFF)  # exponential backoff
            logging.warning("Reddit error (%s), retrying in %ss", exc, delay)
        time.sleep(delay)


if __name__ == "__main__":
    main()
