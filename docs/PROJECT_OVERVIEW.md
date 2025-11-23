# Indeed Bot Project - Project Overview and Controls

## 🏗️ Project Architecture

This project is an **AI-powered automation suite** for job search and application on Indeed.com. It supports job search, advanced filtering and matching, resume and cover letter generation, and workflow dashboards. The core components are:

### 1. **Job Scraping** (`indeed_bot.py`)
   - Scrapes job postings and links from Indeed search results using Stealth browser automation (with Camoufox)
   - Bypasses most CAPTCHAs and Cloudflare
   - Saves all results to a SQLite database (`indeed_jobs.db`)

### 2. **AI Processing & Matching** (`process_jobs.py`, `_resume_generator.py`, AI providers)
   - Extracts job summaries and attributes using Gemini (or optionally OpenAI)
   - Calculates semantic similarity (embeddings) and keyword-based scores to your profile
   - Generates resume and cover letters tailored to specific jobs (requires setup, see milestone docs)
   - Generates workflows, reports, and dashboards

### 3. **Database** (`indeed_jobs.db`)
   - Stores all job data (links, summaries, embeddings, scores, status)
   - Stores your user profile (resume info)
   - Tracks match/application progress

### 4. **Resume/Cover Letter Generation** (`_resume_generator.py`, `docs/MILESTONE_2_README.md`)
   - Generate professional resumes and cover letters per job using provided Microsoft Word templates
   - Output as DOCX (and optionally PDF if configured)

---

## 🔄 How It Works: Step-by-Step

### Phase 1: Job Scraping
```
1. Edit `config.yaml` to define search parameters (job, location, country, etc)
2. Run: python indeed_bot.py
3. Automated browser opens in stealth mode (manual login first run)
4. Bot navigates results and collects job links, skipping ads and dups
5. All valid links saved in `indeed_jobs.db`
```

### Phase 2: AI Processing & Matching
```
1. Run: python process_jobs.py --extract-summaries
   - For each job, fetches job description (via browser or API)
   - Uses Gemini or OpenAI (configurable) to extract structured summary
   - Saves summary and embedding vector to DB

2. Run: python process_jobs.py --match
   - Compares each job with your user profile (resume)
   - Scores for skills, experience, match type, and embeddings (semantic fit)
   - Updates DB with score, reason, and match status ('matched' if above threshold)
```

### Phase 3: Reporting and Document Generation
```
1. Run: python process_jobs.py --dashboard
   - Summary statistics: total jobs, matched, applied, summaries extracted, etc.
   - Shows/exports top matched jobs
   - Creates dashboard_*.json report

2. (Optional) Generate custom resume/cover letters:
   - Use: _resume_generator.py + your user_profile and job description
   - CLI and example usage in docs/MILESTONE_2_README.md
```

---

## 🎮 Project Control & Customization

### **Main Control Panel: `config.yaml`**

Edit this YAML file to control all key settings:

#### Search Parameters
```yaml
search:
  job: "full stack developer"
  location: "remote"
  country: "us"
  language: "us"
```

#### Browser / Session Settings
```yaml
camoufox:
  user_data_dir: "user_data_dir"   # Browser session directory
```

#### AI Provider (Gemini recommended, OpenAI also supported)
```yaml
openai:
  api_key: "YOUR_OPENAI_KEY"
gemini:
  api_key: "YOUR_GEMINI_API_KEY"
```

#### User Profile / Resume Data
```yaml
user_profile:
  name: "Your Name"
  professional_summary: "..."
  work_experience: [...]
  technical_skills: ["Python", "JavaScript"]
  job_preferences:
    desired_role: "Full Stack Developer"
    preferred_locations: ["remote", "San Francisco"]
    preferred_job_types: ["full-time"]
  experience_level: "mid"
```

---

## 🚀 Workflow & Usage Commands

### Scrape Job Postings
```bash
python indeed_bot.py
```
*Starts browser, saves links to `indeed_jobs.db`.*

### AI Processing & Enrichment
```bash
python process_jobs.py --extract-summaries                 # Extract job summaries + embeddings
python process_jobs.py --extract-summaries --limit 10      # Just 10 jobs, for testing
python process_jobs.py --extract-summaries --use-browser   # (Slower/accurate parsing)
```

### Semantic Matching
```bash
python process_jobs.py --match
python process_jobs.py --match --limit 50
```

### Profile Sync (update DB with your latest resume)
```bash
python process_jobs.py --sync-profile
```

### Results Dashboard
```bash
python process_jobs.py --dashboard
```

### Full Pipeline (all steps at once)
```bash
python process_jobs.py --extract-summaries --match --dashboard
python process_jobs.py --extract-summaries --match --dashboard --limit 10
```

### Resume & Cover Letter Generation (see: docs/MILESTONE_2_README.md)
```bash
python _resume_test.py                     # Example: generates resume/cover for DB jobs using Gemini
```
*Edit `_resume_test.py` or call `ResumeCoverLetterGenerator` yourself for custom output!*

---

## 📊 Database Structure (Key Tables)

**`jobs` Table**
- `id`, `job_link`, `job_summary`, `embedding`, `match_score`, `match_reason`
- `application_status` = 'not_applied', 'matched', 'applied'
- Timestamps: `scraped_at`, `matched_at`, `applied_at`

**`user_profile` Table**
- Your resume/profile (from config)
- Used for all comparisons and document generation

---

## 🎯 Matching Algorithm (Overview)

Hybrid scoring is used to match jobs to your resume/profile:

- **Embeddings (40%)**: Semantic similarity (Gemini or OpenAI)
- **Keyword scoring (60%)**: 
   - Skills/tech (30%)
   - Location (15%)
   - Role type (10%)
   - Experience (5%)

- **Threshold**: Jobs with score ≥ 0.6 are 'matched' (customize in code)

---

## 🔧 Advanced Control

### Query Database Directly
```python
import sqlite3

conn = sqlite3.connect('indeed_jobs.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT job_link, match_score, match_reason 
    FROM jobs 
    WHERE match_score >= 0.6 
    ORDER BY match_score DESC
""")
for row in cursor.fetchall():
    print(f"Score: {row[1]:.2f} - {row[0]}")
```

### Use Python API Directly
```python
from indeed_bot import (
    print_dashboard,
    generate_dashboard,
    match_jobs,
    load_user_profile
)
print_dashboard()
stats = generate_dashboard()
print(f"Matched: {stats['jobs_matched']}")
profile = load_user_profile()
print(profile['technical_skills'])
```

---

## 📁 Project File Structure

```
indeed_bot-master/
├── indeed_bot.py              # Main: job scraping
├── process_jobs.py            # AI processing, matching, dashboard
├── _resume_generator.py       # Resume/Cover Letter AI generator
├── _resume_test.py            # Example/test: generate docs from jobs
├── _gemini_ai.py              # Gemini API integrations
├── _database.py               # DB logic
├── config.yaml                # Your control panel!
├── indeed_jobs.db             # SQLite main DB
├── indeed_apply.log           # Log file
├── user_data_dir/             # Browser session/cookies
└── dashboard_*.json           # Dashboard reports
```

---

## 🎛️ Key Control Points

| Control                 | Where                  | How                                       |
|-------------------------|------------------------|--------------------------------------------|
| **Search terms**        | config.yaml → search   | Edit job, location, country                |
| **Your profile/resume** | config.yaml → user_profile | Fill in skills, experience, etc.      |
| **AI Provider Key**     | config.yaml → gemini.api_key or openai.api_key | Add your API key  |
| **Job scraping**        | Command line           | `python indeed_bot.py`                     |
| **AI Processing**       | Command line           | `python process_jobs.py ...`               |
| **Matching threshold**  | Code                   | Default 0.6 (in process_jobs.py/match_jobs)|
| **Doc Generation**      | _resume_generator.py,  | See docs/MILESTONE_2_README.md             |
| **Stop scraping**       | Runtime                | Press `Ctrl+C` in terminal                 |

---

## ⚠️ Important Tips & Notes

- **First Use:** Manual login to Indeed in browser is required ONCE; future sessions are automatic.
- **API Costs:** Gemini and OpenAI usage may incur costs—monitor your usage.
- **Persistence:** All progress is in `indeed_jobs.db` (safe to re-run, no data loss)
- **Rate Limits:** System is tuned to avoid provider rate-limiting.
- **Session/Cookies:** Browser session is kept in `user_data_dir/` (don’t delete unless you want to reset login)
- **Resumes/Cover letters:** See milestone 2 and `_resume_generator.py` for automation details.

---

## 🐛 Troubleshooting

- **Bot not scraping?**
   - Check `indeed_apply.log`
   - Verify login (user_data_dir/ cookies exist)
   - Try manual login again

- **No matches found?**
   - Check your profile in config.yaml (skills, experience)
   - Lower threshold if too strict (edit code)
   - Ensure your Gemini/OpenAI API key is set

- **DB problems?**
   - DB auto-migrates if schema changes
   - Old data is preserved; delete `indeed_jobs.db` for a fresh start

---

## 📈 Typical Workflow Example

```bash
# 1. Configure search and profile in config.yaml
# 2. Scrape jobs
python indeed_bot.py

# 3. Sync your profile to the DB
python process_jobs.py --sync-profile

# 4. Extract summaries (try with 10 first)
python process_jobs.py --extract-summaries --limit 10

# 5. If working, process all jobs
python process_jobs.py --extract-summaries

# 6. AI Match jobs to your profile
python process_jobs.py --match

# 7. View dashboard/results
python process_jobs.py --dashboard

# 8. (Optional) Auto-generate resumes / cover letters for top jobs
python _resume_test.py
```

---

**You now have full control over automated scraping, advanced AI matching, and fast resume/cover letter generation for your Indeed job hunt! See individual milestone docs for in-depth HOWTOs. 🎉**
