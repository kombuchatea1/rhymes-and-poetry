#!/usr/bin/env python3
"""
Rhymes & Poetry — Daily SEO Optimizer Agent
============================================
Runs daily (via GitHub Actions cron) on the rhymes-and-poetry Astro repo.
Picks the next unoptimized blog post, calls Claude to suggest targeted SEO
improvements, applies them, commits the changes, and sends an email report
to jakethomasc28@gmail.com.

What it touches (ONLY):
  - title (frontmatter)
  - description (frontmatter)
  - tags (frontmatter)
  - heroImageAlt (frontmatter, if missing)

What it NEVER touches:
  - The poem body / verse content
  - pubDate, slug, category, heroImage path
  - The prose intro/outro voice

Usage (local):
    python seo_optimizer.py                  # optimizes next pending post
    python seo_optimizer.py --dry-run        # preview only, no file changes, no email
    python seo_optimizer.py --slug my-post   # target a specific post by slug
    python seo_optimizer.py --list           # show optimization status of all posts

Environment variables (set in .env or GitHub Secrets):
    ANTHROPIC_API_KEY   — Claude API key
    GMAIL_APP_PASSWORD  — 16-char Google App Password (not your login password)
    GMAIL_FROM          — sender address (can be same as GMAIL_TO)
    GMAIL_TO            — recipient address (jakethomasc28@gmail.com)
    BLOG_DIR            — path to Astro blog content dir (default: src/content/blog)
"""

from __future__ import annotations  # enables modern type hint syntax on Python 3.9

import anthropic
import argparse
import json
import logging
import os
import smtplib
import sys
import yaml  # PyYAML — already installed as a dependency of anthropic
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── Auto-load .env if present ─────────────────────────────────────────────────
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("seo-optimizer")

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
GMAIL_APP_PASSWORD = "".join(os.getenv("GMAIL_APP_PASSWORD", "").split())  # strip all whitespace incl. non-breaking spaces
GMAIL_FROM         = os.getenv("GMAIL_FROM", "jakethomasc28@gmail.com")
GMAIL_TO           = os.getenv("GMAIL_TO", "jakethomasc28@gmail.com")
BLOG_DIR           = os.getenv("BLOG_DIR", "src/content/blog")
SITE_URL           = "https://rhymesandpoetry.org"
CLAUDE_MODEL       = "claude-sonnet-4-6"   # Sonnet is plenty for metadata work; saves cost


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Find the next post to optimize
# ══════════════════════════════════════════════════════════════════════════════

def parse_md_file(path: Path) -> tuple[dict, str]:
    """
    Parse a markdown file with YAML frontmatter.
    Returns (frontmatter_dict, body_string).
    Frontmatter is the block between the opening and closing --- delimiters.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return fm, body


def dump_md_file(path: Path, fm: dict, body: str):
    """Write frontmatter + body back to a markdown file."""
    fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{fm_str}---\n\n{body}"
    path.write_text(content, encoding="utf-8")


def find_blog_posts(blog_dir: Path) -> list[dict]:
    """Read all .md files and return parsed frontmatter + path info."""
    posts = []
    for md_file in sorted(blog_dir.glob("**/*.md")):
        try:
            fm, body = parse_md_file(md_file)
            posts.append({
                "path": md_file,
                "slug": md_file.stem,
                "frontmatter": fm,
                "body": body,
            })
        except Exception as e:
            log.warning(f"Could not parse {md_file}: {e}")
    return posts


def pick_next_post(posts: list[dict], target_slug: str | None = None) -> dict | None:
    """
    Select which post to optimize today.
    Priority order:
      1. Never optimized (seoOptimizedAt missing or None)
      2. Oldest optimized date (so we cycle through the whole catalog)
    If target_slug is given, use that specific post.
    """
    if target_slug:
        matches = [p for p in posts if p["slug"] == target_slug]
        if not matches:
            log.error(f"No post found with slug '{target_slug}'")
            return None
        return matches[0]

    never_optimized = [
        p for p in posts
        if not p["frontmatter"].get("seoOptimizedAt")
    ]

    if never_optimized:
        # Prefer oldest pubDate among never-optimized
        return sorted(
            never_optimized,
            key=lambda p: str(p["frontmatter"].get("pubDate", "1970-01-01"))
        )[0]

    # All posts have been optimized at least once — pick oldest optimized date
    return sorted(
        posts,
        key=lambda p: str(p["frontmatter"].get("seoOptimizedAt", "1970-01-01"))
    )[0]


def build_post_index(posts: list[dict]) -> list[dict]:
    """Build a lightweight index of all posts for internal-link suggestions."""
    index = []
    for p in posts:
        fm = p["frontmatter"]
        index.append({
            "slug": p["slug"],
            "title": fm.get("title", ""),
            "tags": fm.get("tags", []),
            "description": fm.get("description", ""),
        })
    return index


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Call Claude to generate SEO suggestions
# ══════════════════════════════════════════════════════════════════════════════

OPTIMIZATION_PROMPT = """\
You are an SEO specialist reviewing a blog post for rhymesandpoetry.org — a
literary poetry blog with a warm, editorial voice. The site publishes original
poems, haiku, and reflective verse.

Your task: propose specific, targeted improvements to the SEO metadata of ONE
post. Be surgical — only change what genuinely needs improvement.

ABSOLUTE RULES:
- NEVER suggest changes to the poem body (the verse/stanza content)
- NEVER suggest changes to pubDate, slug, category, or heroImage
- NEVER rewrite the author's prose voice in any field
- Only touch: title, description, tags, heroImageAlt

SEO TARGETS:
- title: 50–60 characters, includes primary keyword naturally
- description: 140–160 characters, keyword-rich, reads like a human wrote it
- tags: 3–6 descriptive tags as lowercase strings (e.g. ["haiku", "grief", "nature"])
- heroImageAlt: if missing or empty, suggest a concise descriptive alt text

POST FRONTMATTER (current values):
{frontmatter_json}

FIRST 400 CHARACTERS OF POST BODY (context only — do not change):
{body_intro}

OTHER POSTS ON SITE (for internal link suggestions):
{post_index_json}

Return ONLY a raw JSON object — no markdown fences, no commentary:
{{
  "changes": [
    {{
      "field": "title | description | tags | heroImageAlt",
      "before": "current value (or null if missing)",
      "after": "proposed new value",
      "rationale": "one sentence explaining the SEO benefit"
    }}
  ],
  "internal_link_suggestions": [
    {{
      "anchor_text": "suggested link text",
      "target_slug": "slug-of-target-post",
      "where_to_place": "brief note on where in the post this link would fit"
    }}
  ],
  "no_changes_needed": false,
  "summary": "One sentence: what changed and why it matters."
}}

If no changes are needed, set "no_changes_needed": true and "changes": [].
Internal link suggestions are always optional — include 1–2 only if clearly relevant.
"""


def generate_suggestions(post: dict, post_index: list[dict]) -> dict:
    """Call Claude and return parsed suggestions dict."""
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. "
            "See README.md for setup instructions."
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    fm = dict(post["frontmatter"])
    # Don't pass internal tracking fields to the prompt — keep it focused
    fm.pop("seoOptimizedAt", None)

    prompt = OPTIMIZATION_PROMPT.format(
        frontmatter_json=json.dumps(fm, indent=2, default=str),
        body_intro=post["body"][:400].strip(),
        post_index_json=json.dumps(post_index[:30], indent=2),  # cap at 30 posts
    )

    log.info(f"Calling Claude ({CLAUDE_MODEL}) for: {post['slug']}")
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if Claude wrapped anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse Claude output as JSON: {e}")
        log.error(f"Raw:\n{raw}")
        raise

    changes = result.get("changes", [])
    log.info(f"Suggestions: {len(changes)} change(s) proposed.")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Apply changes to the file
# ══════════════════════════════════════════════════════════════════════════════

PROTECTED_FIELDS = {"pubDate", "slug", "category", "heroImage", "seoOptimizedAt"}


def apply_changes(post: dict, suggestions: dict) -> bool:
    """
    Apply suggested frontmatter changes to the markdown file.
    Returns True if any changes were made.
    """
    if suggestions.get("no_changes_needed"):
        log.info("No changes needed — skipping file write.")
        return False

    changes = suggestions.get("changes", [])
    if not changes:
        log.info("No changes in suggestions — skipping file write.")
        return False

    # Re-parse the file fresh before writing
    fm, body = parse_md_file(post["path"])
    changed = False

    for change in changes:
        field = change.get("field", "")
        after = change.get("after")

        if field in PROTECTED_FIELDS:
            log.warning(f"Claude tried to change protected field '{field}' — skipping.")
            continue

        if after is None:
            continue

        fm[field] = after
        changed = True
        log.info(f"  {field}: updated")

    if changed:
        # Stamp the optimization date
        fm["seoOptimizedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dump_md_file(post["path"], fm, body)
        log.info(f"File updated: {post['path']}")

    return changed


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Send email report
# ══════════════════════════════════════════════════════════════════════════════

def build_email_html(post: dict, suggestions: dict, changes_applied: bool) -> tuple[str, str]:
    """Return (subject, html_body) for the daily report email."""
    fm = post["frontmatter"]
    slug = post["slug"]
    title = fm.get("title", slug)
    today = datetime.now().strftime("%B %d, %Y")
    post_url = f"{SITE_URL}/blog/{slug}"

    changes = suggestions.get("changes", [])
    links   = suggestions.get("internal_link_suggestions", [])
    summary = suggestions.get("summary", "")
    no_changes = suggestions.get("no_changes_needed", False)

    subject = f"SEO Daily Report — \"{title}\" [{datetime.now().strftime('%Y-%m-%d')}]"

    # ── Build HTML ──
    status_badge = (
        '<span style="background:#d4edda;color:#155724;padding:3px 10px;border-radius:12px;font-size:13px;">✓ Changes applied</span>'
        if changes_applied else
        '<span style="background:#fff3cd;color:#856404;padding:3px 10px;border-radius:12px;font-size:13px;">✓ No changes needed</span>'
    )

    changes_html = ""
    if changes:
        rows = ""
        for i, c in enumerate(changes, 1):
            field = c.get("field", "")
            before = c.get("before") or "<em>(empty)</em>"
            after = c.get("after", "")
            rationale = c.get("rationale", "")
            rows += f"""
            <tr>
              <td style="padding:12px 8px;border-bottom:1px solid #eee;font-weight:600;color:#4a6741;vertical-align:top;white-space:nowrap">{i}. {field}</td>
              <td style="padding:12px 8px;border-bottom:1px solid #eee;vertical-align:top">
                <div style="color:#999;font-size:13px;margin-bottom:4px">Before: <code style="background:#f5f5f5;padding:2px 5px;border-radius:3px">{before}</code></div>
                <div style="color:#222;margin-bottom:6px">After: <strong>{after}</strong></div>
                <div style="color:#666;font-size:13px;font-style:italic">{rationale}</div>
              </td>
            </tr>"""
        changes_html = f"""
        <h3 style="color:#333;margin-top:28px;margin-bottom:12px;">Changes Made</h3>
        <table style="width:100%;border-collapse:collapse;font-size:14px">{rows}</table>"""
    else:
        changes_html = """
        <h3 style="color:#333;margin-top:28px;margin-bottom:12px;">Changes Made</h3>
        <p style="color:#666;font-style:italic">This post's SEO metadata is already well-optimized. No changes were needed.</p>"""

    links_html = ""
    if links:
        link_items = ""
        for lnk in links:
            anchor = lnk.get("anchor_text", "")
            target = lnk.get("target_slug", "")
            where  = lnk.get("where_to_place", "")
            link_items += f"""
            <li style="margin-bottom:10px">
              <strong>"{anchor}"</strong> → <a href="{SITE_URL}/blog/{target}" style="color:#4a6741">/blog/{target}</a>
              <div style="color:#666;font-size:13px;margin-top:3px">{where}</div>
            </li>"""
        links_html = f"""
        <h3 style="color:#333;margin-top:28px;margin-bottom:12px;">Internal Link Opportunities</h3>
        <p style="color:#666;font-size:13px;margin-bottom:10px">These are suggestions only — add them manually if they feel natural.</p>
        <ul style="padding-left:20px;color:#333;font-size:14px">{link_items}</ul>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f7f6f3;font-family:'Georgia',serif">
  <div style="max-width:620px;margin:32px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08)">

    <!-- Header -->
    <div style="background:#4a6741;padding:24px 32px">
      <p style="color:rgba(255,255,255,0.7);margin:0;font-size:12px;letter-spacing:1px;text-transform:uppercase">Rhymes & Poetry · Daily SEO Report</p>
      <h1 style="color:#fff;margin:8px 0 0;font-size:22px;font-weight:normal">{title}</h1>
      <p style="color:rgba(255,255,255,0.6);margin:6px 0 0;font-size:13px">{today}</p>
    </div>

    <!-- Body -->
    <div style="padding:28px 32px">

      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        {status_badge}
        <a href="{post_url}" style="color:#4a6741;font-size:13px">{post_url}</a>
      </div>

      {f'<p style="color:#555;font-size:15px;border-left:3px solid #4a6741;padding-left:14px;margin:0 0 20px">{summary}</p>' if summary else ''}

      {changes_html}
      {links_html}

      <!-- Footer note -->
      <div style="margin-top:36px;padding-top:20px;border-top:1px solid #eee;color:#999;font-size:12px">
        <p style="margin:0">Changes were committed to <code>main</code> and will go live on next Cloudflare Pages deploy.</p>
        <p style="margin:6px 0 0">Tomorrow's post will be selected automatically from the unoptimized backlog.</p>
      </div>

    </div>
  </div>
</body>
</html>"""

    return subject, html


def send_email_report(subject: str, html_body: str):
    """Send the HTML report via Gmail SMTP."""
    if not GMAIL_APP_PASSWORD:
        log.warning("GMAIL_APP_PASSWORD not set — skipping email send.")
        log.info("(Set GMAIL_APP_PASSWORD in .env or GitHub Secrets to enable email reports.)")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_FROM
    msg["To"]      = GMAIL_TO

    # Plain text fallback
    plain = (
        f"Rhymes & Poetry — Daily SEO Report\n"
        f"{subject}\n\n"
        f"View this email in an HTML-capable client for the full formatted report."
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(GMAIL_FROM, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_FROM, GMAIL_TO, msg.as_string())
        log.info(f"Email report sent → {GMAIL_TO}")
    except Exception as e:
        log.error(f"Failed to send email: {e}")
        raise


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — List mode (audit all posts)
# ══════════════════════════════════════════════════════════════════════════════

def print_status_list(posts: list[dict]):
    """Print a table showing optimization status of all posts."""
    never   = [p for p in posts if not p["frontmatter"].get("seoOptimizedAt")]
    done    = sorted(
        [p for p in posts if p["frontmatter"].get("seoOptimizedAt")],
        key=lambda p: str(p["frontmatter"].get("seoOptimizedAt", ""))
    )

    print(f"\n{'─'*70}")
    print(f"  Rhymes & Poetry — SEO Optimization Status ({len(posts)} posts total)")
    print(f"{'─'*70}")
    print(f"  Never optimized: {len(never)}   Already optimized: {len(done)}")
    print(f"{'─'*70}")

    print("\n  NEVER OPTIMIZED (will be picked first):")
    for p in never:
        title = p["frontmatter"].get("title", p["slug"])
        print(f"    ○  {p['slug']:<45}  {title[:35]}")

    if done:
        print("\n  ALREADY OPTIMIZED (oldest first = next in cycle):")
        for p in done:
            date  = p["frontmatter"].get("seoOptimizedAt", "")
            title = p["frontmatter"].get("title", p["slug"])
            print(f"    ✓  {p['slug']:<45}  {str(date):<12}  {title[:25]}")

    print(f"\n{'─'*70}\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Rhymes & Poetry Daily SEO Optimizer")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Preview only — no file changes, no email sent")
    parser.add_argument("--slug",     type=str, default=None,
                        help="Optimize a specific post by slug instead of auto-selecting")
    parser.add_argument("--list",     action="store_true",
                        help="Show optimization status of all posts and exit")
    parser.add_argument("--blog-dir", type=str, default=BLOG_DIR,
                        help=f"Path to Astro blog content dir (default: {BLOG_DIR})")
    args = parser.parse_args()

    # Resolve blog dir relative to CWD (the repo root when run via GitHub Actions)
    blog_dir = Path(args.blog_dir)
    if not blog_dir.exists():
        log.error(
            f"Blog dir not found: {blog_dir.resolve()}\n"
            f"Run this script from the repo root, or set --blog-dir."
        )
        sys.exit(1)

    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("Rhymes & Poetry — Daily SEO Optimizer")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    posts = find_blog_posts(blog_dir)
    log.info(f"Found {len(posts)} blog posts.")

    if args.list:
        print_status_list(posts)
        return

    post = pick_next_post(posts, target_slug=args.slug)
    if not post:
        log.warning("No post selected — nothing to do.")
        sys.exit(0)

    log.info(f"Selected post: {post['slug']}")
    log.info(f"  Title: {post['frontmatter'].get('title', '(no title)')}")
    log.info(f"  Last optimized: {post['frontmatter'].get('seoOptimizedAt', 'never')}")

    post_index = build_post_index(posts)
    suggestions = generate_suggestions(post, post_index)

    if args.dry_run:
        log.info("Dry run — proposed changes:")
        print(json.dumps(suggestions, indent=2))
        return

    changes_applied = apply_changes(post, suggestions)
    subject, html_body = build_email_html(post, suggestions, changes_applied)

    log.info(f"Email subject: {subject}")
    send_email_report(subject, html_body)

    log.info("Done. ✓")


if __name__ == "__main__":
    main()
