# Rhymes & Poetry — Daily SEO Optimizer

An agentic workflow that runs once per day, picks the next unoptimized blog post,
calls Claude to improve its SEO metadata, commits the changes, and emails you a
report explaining every change and why it was made.

---

## What it touches

| Field | What it does |
|-------|-------------|
| `title` | Brings to 50–60 chars with a natural primary keyword |
| `description` | Brings to 140–160 chars, keyword-rich and human-readable |
| `tags` | Trims or expands to 3–6 descriptive lowercase tags |
| `heroImageAlt` | Adds descriptive alt text if missing |
| `seoOptimizedAt` | Stamps today's date (internal tracking) |

**What it never touches:** poem bodies, `pubDate`, `slug`, `category`, `heroImage` path, or your prose voice.

---

## How it works

```
GitHub Actions cron (daily)
  → picks next post (never-optimized first, then oldest-optimized)
  → calls Claude Sonnet with frontmatter + first 400 chars of body
  → Claude returns: proposed changes + rationale, as JSON
  → applies changes to the .md file
  → commits to main → Cloudflare Pages auto-redeploys
  → sends HTML email report to jakethomasc28@gmail.com
```

---

## Setup (one-time, ~15 minutes)

### 1. Get an Anthropic API key
- Go to [console.anthropic.com](https://console.anthropic.com)
- Sign in → **API Keys** → **Create Key**
- Copy the key (starts with `sk-ant-...`)

### 2. Create a Gmail App Password
Your regular Gmail password won't work here — Google requires an App Password for
scripts. Here's how:

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Make sure **2-Step Verification** is ON (required)
3. Search for **"App Passwords"** in the search bar (or go to Security → App Passwords)
4. Click **Create** → name it `R&P SEO Optimizer`
5. Google gives you a 16-character password like `abcd efgh ijkl mnop`
6. Copy it immediately — you can't see it again

### 3. Add secrets to GitHub

In your `rhymes-and-poetry` GitHub repo:
- **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these two secrets:

| Secret name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic key from step 1 |
| `GMAIL_APP_PASSWORD` | The 16-char App Password from step 2 |

### 4. Copy the workflow file
Copy `github-workflow.yml` from this folder into your repo at:
```
rhymes-and-poetry/.github/workflows/daily-seo-optimizer.yml
```
Create the `.github/workflows/` directory if it doesn't exist.

### 5. Copy the optimizer script
Copy the entire `seo-optimizer/` folder into the root of your `rhymes-and-poetry` repo:
```
rhymes-and-poetry/seo-optimizer/
  seo_optimizer.py
  requirements.txt
  .env.example
```

### 6. Commit and push
```bash
cd ~/rhymes-and-poetry
git add .github/workflows/daily-seo-optimizer.yml seo-optimizer/
git commit -m "feat: add daily SEO optimizer agent"
git push
```

The workflow will now run daily at 9:00 AM UTC. Check the **Actions** tab in GitHub to confirm.

---

## Running locally (for testing)

```bash
cd ~/rhymes-and-poetry
cp seo-optimizer/.env.example seo-optimizer/.env
# Edit .env and fill in your keys

pip install -r seo-optimizer/requirements.txt

# Preview what Claude would change (no file writes, no email):
python seo-optimizer/seo_optimizer.py --dry-run

# Optimize the next pending post for real:
python seo-optimizer/seo_optimizer.py

# Target a specific post:
python seo-optimizer/seo_optimizer.py --slug the-rains-grammar

# Check optimization status of all posts:
python seo-optimizer/seo_optimizer.py --list
```

---

## Understanding the email report

You'll receive a formatted HTML email that looks like this:

```
Subject: SEO Daily Report — "The Rain's Grammar" [2026-05-21]

✓ Changes applied        https://rhymesandpoetry.org/blog/the-rains-grammar

Changes Made:
1. title
   Before: "Rain"
   After:  "The Rain's Grammar: A Poem About Language and Silence"
   Why:    Short titles underperform; added searchable keywords naturally.

2. description
   Before: (empty)
   After:  "A reflective haiku sequence exploring how rainfall teaches us
            to listen to what's left unsaid. 97 characters."
   Why:    Missing meta description means Google picks random excerpt.

Internal Link Opportunities (suggestions — add manually if they feel right):
  → "language and silence" → /blog/the-space-between-words
    (Where: mention in the reflection section intro)

Changes were committed to main and will go live on next Cloudflare Pages deploy.
```

---

## Adjusting the schedule

The cron in `github-workflow.yml` is set to `0 9 * * *` (9:00 AM UTC = 11:00 PM HST previous night).

To change the time, edit the `cron:` line using [crontab.guru](https://crontab.guru):
- 8:00 AM HST = `0 18 * * *`
- Noon HST = `0 22 * * *`

---

## Cost

Each daily run uses Claude Sonnet with ~1,500 tokens of input and ~500 tokens of output.
Approximately **$0.01–0.03 per run** — roughly **$0.30–0.90/month**.
