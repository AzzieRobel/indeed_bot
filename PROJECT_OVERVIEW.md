# Indeed Bot Project - How It Works & How to Control It

## 🏗️ Project Architecture

This project is an **AI-powered job scraping and matching system** for Indeed.com with three main components:

### 1. **Job Scraping** (`indeed_bot.py`)
   - Scrapes job links from Indeed search results
   - Uses Camoufox browser automation (bypasses Cloudflare/CAPTCHA)
   - Saves all job links to SQLite database (`indeed_jobs.db`)

### 2. **AI Processing** (`process_jobs.py`)
   - Extracts job summaries using OpenAI
   - Generates embeddings for semantic matching
   - Matches jobs against your resume/profile
   - Generates dashboard reports

### 3. **Database** (`indeed_jobs.db`)
   - Stores job links, summaries, embeddings, match scores
   - Stores your resume/profile data
   - Tracks application status

---

## 🔄 How It Works (Step-by-Step Flow)

### Phase 1: Job Scraping
```
1. User configures search in config.yaml (job, location, country)
2. Run: python indeed_bot.py
3. Bot opens Camoufox browser (stealth mode)
4. Logs into Indeed (first time: manual login required)
5. Navigates through search result pages
6. Extracts job links from each page
7. Filters out ad links (/viewjob), keeps real jobs (/rc/clk?jk=...)
8. Saves all links to database (indeed_jobs.db)
9. Continues until no more pages found
```

### Phase 2: AI Processing (Optional)
```
1. Run: python process_jobs.py --extract-summaries
2. For each job link:
   - Opens job page (or uses OpenAI to fetch)
   - Extracts structured summary (title, company, skills, etc.)
   - Generates embedding vector
   - Saves to database
3. Run: python process_jobs.py --match
4. For each job with summary:
   - Calculates match score (embeddings + keyword scoring)
   - Updates database with match_score, match_reason
   - Marks as 'matched' if score ≥ 0.6
```

### Phase 3: Dashboard & Reports
```
1. Run: python process_jobs.py --dashboard
2. Shows statistics:
   - Jobs fetched
   - Jobs with summaries
   - Jobs matched
   - Jobs applied
   - Top matched jobs
3. Saves JSON report
```

---

## 🎮 How to Control the Project

### **Configuration File: `config.yaml`**

This is your **main control panel**. Edit it to customize everything:

#### 1. Search Parameters
```yaml
search:
  job: "full stack developer"      # What jobs to search for
  location: "remote"                # Where (city, state, or "remote")
  country: "us"                     # Country code
  language: "us"                    # Language code
```

#### 2. Browser Settings
```yaml
camoufox:
  user_data_dir: "user_data_dir"   # Where to store browser session
```

#### 3. OpenAI (for AI matching)
```yaml
openai:
  api_key: "your-key-here"          # Get from platform.openai.com
```

#### 4. Your Resume/Profile
```yaml
user_profile:
  name: "Your Name"
  professional_summary: "..."
  work_experience: [...]
  technical_skills: ["Python", "JavaScript", ...]
  job_preferences:
    desired_role: "Full Stack Developer"
    preferred_locations: ["remote", "San Francisco"]
    preferred_job_types: ["full-time"]
  experience_level: "mid"
```

---

## 🚀 Control Commands

### **Basic Job Scraping**
```bash
# Scrape job links from Indeed
python indeed_bot.py
```
**What it does:**
- Opens browser, logs in (if needed)
- Scrapes all job links from search results
- Saves to `indeed_jobs.db`
- Shows progress: `[Page 1] Saved 15 new links...`

**Control:**
- Press `Ctrl+C` to stop anytime
- Check `indeed_apply.log` for errors
- Results in database: `indeed_jobs.db`

---

### **AI Processing Commands**

#### Extract Job Summaries
```bash
# Extract summaries for all jobs
python process_jobs.py --extract-summaries

# Test with 10 jobs first
python process_jobs.py --extract-summaries --limit 10

# Use browser for more accurate scraping (slower)
python process_jobs.py --extract-summaries --use-browser
```

#### Run AI Matching
```bash
# Match all jobs against your profile
python process_jobs.py --match

# Match only first 50 jobs
python process_jobs.py --match --limit 50
```

#### Sync Your Profile
```bash
# Save your resume from config.yaml to database
python process_jobs.py --sync-profile
```

#### View Dashboard
```bash
# Show statistics and top matches
python process_jobs.py --dashboard
```

#### Combined Operations
```bash
# Full pipeline: extract → match → dashboard
python process_jobs.py --extract-summaries --match --dashboard

# Test run with 10 jobs
python process_jobs.py --extract-summaries --match --dashboard --limit 10
```

---

## 📊 Database Structure

### `jobs` Table
- `id` - Unique ID
- `job_link` - The job URL
- `job_key` - Extracted from link (jk=...)
- `job_summary` - AI-generated summary
- `embedding` - Vector for semantic matching
- `match_score` - 0.0 to 1.0 (higher = better match)
- `match_reason` - Why it matched
- `application_status` - 'not_applied', 'matched', 'applied'
- `scraped_at`, `matched_at`, `applied_at` - Timestamps

### `user_profile` Table
- Stores your resume data from config.yaml
- Used for matching calculations

---

## 🎯 Matching Algorithm

Jobs are scored using a **hybrid approach**:

1. **Embeddings (40%)** - Semantic similarity
   - Compares job description with your resume
   - Uses OpenAI embeddings

2. **Keyword Scoring (60%)**:
   - **Relevance (30%)** - Skills match
   - **Location (15%)** - Preferred locations
   - **Role Type (10%)** - Full-time, contract, etc.
   - **Experience (5%)** - Entry, mid, senior

**Threshold:** Jobs with score ≥ 0.6 are marked as "matched"

---

## 🔧 Advanced Control

### Query Database Directly
```python
import sqlite3

conn = sqlite3.connect('indeed_jobs.db')
cursor = conn.cursor()

# Get all matched jobs
cursor.execute("""
    SELECT job_link, match_score, match_reason 
    FROM jobs 
    WHERE match_score >= 0.6 
    ORDER BY match_score DESC
""")

for row in cursor.fetchall():
    print(f"Score: {row[1]:.2f} - {row[0]}")
```

### Use Python API
```python
from indeed_bot import (
    print_dashboard,
    generate_dashboard,
    match_jobs,
    load_user_profile
)

# View dashboard
print_dashboard()

# Get dashboard data
stats = generate_dashboard()
print(f"Matched: {stats['jobs_matched']}")

# Load your profile
profile = load_user_profile()
print(profile['technical_skills'])
```

---

## 📁 File Structure

```
indeed_bot-master/
├── indeed_bot.py          # Main scraping bot
├── process_jobs.py         # AI processing script
├── config.yaml            # Configuration (YOUR CONTROL PANEL)
├── indeed_jobs.db         # SQLite database (all data)
├── indeed_apply.log       # Log file (errors, progress)
├── user_data_dir/         # Browser session (cookies, login)
└── dashboard_*.json       # Generated reports
```

---

## 🎛️ Control Points Summary

| What to Control | Where | How |
|----------------|-------|-----|
| **Search terms** | `config.yaml` → `search` | Edit job, location, country |
| **Your resume** | `config.yaml` → `user_profile` | Fill in skills, experience, etc. |
| **OpenAI API** | `config.yaml` → `openai.api_key` | Add your API key |
| **Scraping** | Command line | `python indeed_bot.py` |
| **AI Processing** | Command line | `python process_jobs.py --extract-summaries --match` |
| **Matching threshold** | Code | Default: 0.6 (in `match_jobs()` function) |
| **Stop scraping** | Runtime | Press `Ctrl+C` |

---

## ⚠️ Important Notes

1. **First Run:** You must manually log in to Indeed the first time
2. **Costs:** OpenAI API usage costs money - monitor at platform.openai.com/usage
3. **Rate Limits:** Built-in delays prevent API rate limiting
4. **Database:** All data persists in `indeed_jobs.db` - safe to re-run
5. **Browser Session:** Saved in `user_data_dir` - don't delete if you want to stay logged in

---

## 🐛 Troubleshooting

**Bot not scraping?**
- Check `indeed_apply.log`
- Verify login status (check cookies)
- Try manual login again

**No matches?**
- Check your `user_profile` in config.yaml
- Lower matching threshold (edit code)
- Verify OpenAI API key is set

**Database issues?**
- Database auto-migrates on first run
- Old data is preserved
- Can delete `indeed_jobs.db` to start fresh

---

## 📈 Typical Workflow

```bash
# 1. Configure your search and profile
# Edit config.yaml

# 2. Scrape jobs
python indeed_bot.py

# 3. Sync your profile to database
python process_jobs.py --sync-profile

# 4. Extract summaries (test with 10 first)
python process_jobs.py --extract-summaries --limit 10

# 5. If good, process all
python process_jobs.py --extract-summaries

# 6. Match jobs
python process_jobs.py --match

# 7. View results
python process_jobs.py --dashboard
```

---

**That's it!** You now have full control over the job scraping and matching system. 🎉

