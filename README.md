# lead-finder

A small, **read-only** Python (PRAW) script that alerts me to Reddit posts where people ask to hire a writer.

**Commercial use:** I am a freelance SEO content writer, and I use this tool to find paying clients for my own business.

## What it does
- Every 90 seconds, makes one read-only request for the 25 newest posts across: r/forhire, r/HireaWriter, r/SEO, r/smallbusiness, r/blogging, r/content_marketing.
- Matches title and body against a hiring-intent keyword pattern (e.g. "looking for a blog writer").
- Ignores posts older than 6 hours and posts where the author is advertising their own services.
- Prints an alert (optionally a private Telegram message) with the post link and a draft reply.

## What it never does
- Never posts, comments, votes, sends messages, or modifies anything on Reddit.
- Stores only a local list of already-seen post IDs (no usernames, no content).
- Does not resell or share data, train AI models, profile users, or infer anything about them.

## Human involvement
I read each flagged post and reply manually from my own account (u/sherpa-hillery-101), following each subreddit's rules.

## Compliance
Uses a descriptive user-agent, backs off on errors and rate limits, and is used under Reddit's Responsible Builder Policy and Data API Terms (access requested via Reddit's approval process).

## Run
```bash
pip install -r requirements.txt
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."
# optional private alerts:
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python lead_bot.py
```
Never commit your credentials. They are read from environment variables only.
