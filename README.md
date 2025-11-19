# Indeed Auto-Apply Bot

**WARNING:**  
This guide explains how to use this bot. Use at your own risk. Indeed may change their website or introduce new protections (such as captchas or anti-bot measures) at any time, which could break this tool or result in your account being restricted. This is for educational purposes only.

---

## Features

- **Automated Job Scraping**: Finds and collects job links from Indeed search results
- **Direct Job Detail Scraping**: Visits job links and extracts full job details (title, company, description, salary, etc.)
- **AI-Powered Job Matching**: Uses OpenAI embeddings and keyword scoring to match jobs based on your profile
- **Browser Automation**: Uses Camoufox for stealth browsing (bypasses Cloudflare, CAPTCHA)
- **Database Storage**: SQLite database stores all job data, summaries, embeddings, and match scores
- **Dashboard & Reports**: Track jobs fetched, matched, and applications submitted

---

## Project Structure

The project is organized into modular components:

```
indeed_bot-master/
├── __init__.py          # Main entry point and module initialization
├── _indeed.py           # Indeed scraping and job detail extraction
├── database.py           # Database operations (Database class)
├── utils.py             # Utility functions
├── config.yaml          # Configuration file (YOUR CONTROL PANEL)
├── indeed_jobs.db       # SQLite database (all job data)
├── user_data_dir/       # Browser session (cookies, login)
├── db_schema.md         # Database schema documentation
└── PROJECT_OVERVIEW.md  # Detailed project architecture
```

---

## Prerequisites

- Python 3.8+
- [Camoufox](https://github.com/meteor314/camoufox) installed and configured
- An Indeed account with:
  - Your CV already uploaded
  - Your name, address, and phone number filled in your Indeed profile
- (Optional) OpenAI API key for AI matching features (get from https://platform.openai.com/api-keys)
- (Optional) `requests` and `beautifulsoup4` for HTTP-based scraping

---

## Installation

1. **Clone this repository** and install dependencies:
    ```bash
    pip install -r requirements.txt
    pip install openai  # For AI matching features (optional)
    pip install requests beautifulsoup4  # For HTTP-based scraping (optional)
    ```

2. **Edit `config.yaml`:**

    Configure your search parameters and user profile:
    ```yaml
    search:
      job: "full stack developer"
      location: "remote"
      country: "us"
      language: "us"

    camoufox:
      user_data_dir: "user_data_dir"

    # OpenAI Configuration (optional, for AI matching)
    openai:
      api_key: "your-openai-api-key-here"

    # User Profile for AI Matching
    user_profile:
      name: "Your Name"
      location: "Your Location"
      professional_summary: "Your professional summary..."
      work_experience:
        - title: "Software Engineer"
          company: "Tech Corp"
          location: "San Francisco"
          duration: "2020-2023"
          description: "Developed web applications..."
      education:
        - degree: "BS Computer Science"
          institution: "University Name"
          duration: "2016-2020"
      technical_skills:
        - "Python"
        - "JavaScript"
        - "React"
        - "Node.js"
      soft_skills:
        - "Communication"
        - "Teamwork"
      job_preferences:
        desired_role: "Full Stack Developer"
        preferred_locations:
          - "remote"
          - "San Francisco"
        preferred_job_types:
          - "full-time"
        accept_remote: true
      experience_level: "mid"  # "entry", "mid", or "senior"
    ```

---

## Usage

### Basic Workflow

The project uses a modular, class-based architecture. You can use it as a Python module or extend it with custom scripts.

#### 1. **Using as a Python Module**

```python
import yaml
from camoufox.sync_api import Camoufox
import database
import _indeed

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize database
db = database.Database("indeed_jobs.db")
db.init_database()

# Initialize Indeed scraper
indeed = _indeed.Indeed()

# Use with browser automation
with Camoufox(user_data_dir=config["camoufox"]["user_data_dir"]) as browser:
    page = browser.new_page()
    # Your scraping logic here
```

#### 2. **Job Scraping**

The main entry point (`__init__.py`) sets up the environment. For actual job scraping, you'll need to implement or use the scraping functions:

- **Collect job links**: Extract job links from search result pages
- **Scrape job details**: Visit each job link and extract full details
- **Save to database**: Store all data in SQLite database

#### 3. **AI Matching (Optional)**

If you have OpenAI API configured:

```python
from openai import OpenAI
import database

# Initialize
db = database.Database("indeed_jobs.db")
client = OpenAI(api_key="your-api-key")

# Load user profile
profile = db.load_user_profile()

# Match jobs (if matching functions are available)
# This would use the matching algorithms to score jobs
```

---

## How It Works

### Workflow Overview

1. **Job Link Collection**
   - Bot navigates through Indeed search result pages
   - Extracts job links from job cards
   - Normalizes links to `viewjob` format
   - Saves links to database

2. **Job Detail Scraping**
   - Visits each saved job link
   - Scrapes job details (title, company, description, salary, etc.)
   - Can use HTTP requests (fast) or browser automation (more accurate)
   - Saves structured job data to database

3. **AI Matching** (Optional)
   - Extracts job summaries from scraped details
   - Generates embeddings using OpenAI
   - Matches jobs against user profile using:
     - **Embeddings (40%)**: Semantic similarity
     - **Keyword Scoring (60%)**: Skills, location, job type, experience
   - Jobs with score ≥ 0.6 are marked as "matched"

4. **Database Storage**
   - All data persists in `indeed_jobs.db`
   - Jobs table stores: links, summaries, embeddings, match scores
   - User profile table stores: resume data for matching

---

## Database Schema

See `db_schema.md` for detailed schema documentation.

### Key Tables

**`jobs` Table:**
- `job_link` - Canonical job URL
- `job_summary` - Text summary for matching
- `job_details` - Full JSON job data
- `embedding` - Vector for semantic matching
- `match_score` - 0.0 to 1.0 (higher = better match)
- `match_reason` - Explanation for match
- `application_status` - 'not_applied', 'matched', 'applied'

**`user_profile` Table:**
- Stores your resume/profile data
- Used for matching calculations

---

## Configuration

### Search Parameters

Edit `config.yaml` to customize your search:

```yaml
search:
  job: "full stack developer"  # Job title/keywords
  location: "remote"            # City, state, or "remote"
  country: "us"                 # Country code (us, jp, fr, etc.)
  language: "us"                # Language code
```

### Browser Settings

```yaml
camoufox:
  user_data_dir: "user_data_dir"  # Where to store browser session
```

### OpenAI (for AI matching)

```yaml
openai:
  api_key: "your-openai-api-key-here"
```

### User Profile

Fill in your complete profile in `config.yaml` under `user_profile` section. This is used for AI matching.

---

## AI Matching Details

The AI matching system uses a hybrid approach:

1. **Embeddings (40% weight)**: Semantic similarity using OpenAI embeddings
2. **Keyword Scoring (60% weight)**:
   - **Relevance (30%)**: Matches your skills/technologies
   - **Location (15%)**: Matches preferred locations
   - **Role Type (10%)**: Matches preferred job types
   - **Experience (5%)**: Matches experience level

Jobs with a match score ≥ 0.6 are marked as "matched" in the database.

---

## First Run

1. **Login to Indeed manually:**
   - Run the initialization script (or your custom scraping script)
   - If not logged in, the bot will open Indeed and prompt you to log in manually
   - After logging in, close the bot and restart it

2. **Your session will be saved:**
   - All session data (cookies, login info) will be preserved in the `user_data_dir` specified in `config.yaml`
   - You won't need to log in again on subsequent runs

---

## Advanced Usage

### Direct Database Access

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

### Using Database Class

```python
import database

db = database.Database("indeed_jobs.db")
db.init_database()

# Save job link
db.save_job_link("https://www.indeed.com/viewjob?jk=...", 
                 job_key="abc123", 
                 search_query="python developer",
                 location="remote")

# Load user profile
profile = db.load_user_profile()

# Save user profile
db.save_user_profile(profile_data)
```

### Using Indeed Scraper

```python
import _indeed

indeed = _indeed.Indeed()

# Normalize job link
normalized = indeed.normalize_job_link("https://jp.indeed.com/rc/clk?jk=...")

# Scrape job details (HTTP-based)
details = indeed.scrape_job_details_from_link(
    normalized, 
    REQUESTS_AVAILABLE=True,
    browser_page=None
)
```

---

## Notes & Limitations

- This bot works by scraping job postings directly from Indeed
- Job details are extracted by visiting each job link (HTTP or browser-based)
- If you encounter captchas or anti-bot protections, Camoufox should handle them automatically, but you may need to solve them manually
- Indeed may change their website at any time, which could break this bot
- Use responsibly and do not spam applications
- OpenAI API usage will incur costs. Monitor your usage at https://platform.openai.com/usage
- This program is a guide on how to automate job applications, you need to make some modifications to the code to make it work for your needs

---

## Troubleshooting

- **Module import errors**: Make sure all dependencies are installed (`pip install -r requirements.txt`)
- **Database errors**: Database auto-migrates on first run. Old data is preserved
- **Scraping fails**: Check `indeed_apply.log` for errors. Verify login status
- **No matches**: Check your `user_profile` in config.yaml. Verify OpenAI API key is set
- **Browser issues**: Ensure Camoufox is properly installed and configured

---

## Project Documentation

- **`PROJECT_OVERVIEW.md`**: Detailed architecture and workflow documentation
- **`db_schema.md`**: Complete database schema reference

---

## Disclaimer

This project is not affiliated with Indeed. Use at your own risk.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
