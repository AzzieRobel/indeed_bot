# Database Schemas (Indeed Bot Project)

This document reflects the **current database schema** for the Indeed Bot system, including the `jobs` and `user_profile` tables as implemented in the latest version of the project (`indeed_jobs.db`). These tables are **auto-migrated** as needed by the code. They are the primary sources for all scraping, AI matching, dashboard stats, profile sync, and document generation tasks.

---

## 🗂️ Table: `jobs`

**Purpose:**  
Stores all job postings scraped or processed by the system, as well as AI analysis and application status metadata.

| Column               | Type      | Constraints / Default     | Description                                                  |
| -------------------- | --------- | ------------------------- | ------------------------------------------------------------ |
| `id`                 | INTEGER   | PRIMARY KEY AUTOINCREMENT | Unique job ID                                                |
| `job_link`           | TEXT      | UNIQUE NOT NULL           | Canonical URL for the job posting                            |
| `job_key`            | TEXT      |                           | Indeed job key or source-specific ID                         |
| `source`             | TEXT      | DEFAULT 'indeed'          | Source of this posting (e.g., `indeed`, `other`)             |
| `search_query`       | TEXT      |                           | Search keywords/params that produced this job                |
| `location`           | TEXT      |                           | City/town/region                                             |
| `country`            | TEXT      |                           | Country code (e.g., `us`, `fr`)                              |
| `language`           | TEXT      |                           | Site scraping language                                       |
| `scraped_at`         | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When first scraped                                           |
| `created_at`         | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | DB insertion timestamp                                       |
| `job_summary`        | TEXT      |                           | AI/heuristic short summary (for semantic/keyword matching)   |
| `job_details`        | TEXT      |                           | Raw job JSON, extended attributes, and scraped description   |
| `embedding`          | TEXT      |                           | JSON-encoded embedding vector (AI semantic matching, optional)|
| `match_score`        | REAL      |                           | Relevance/fit score computed by AI matching engine           |
| `match_reason`       | TEXT      |                           | Explanation or keywords for the match score                  |
| `application_status` | TEXT      | DEFAULT 'not_applied'     | One of: `not_applied`, `applied`, `interview`, `rejected`, `skipped` |
| `matched_at`         | TIMESTAMP |                           | When marked as "matched" (by process_jobs)                   |
| `applied_at`         | TIMESTAMP |                           | When user marked as "applied"                                |

### **application_status values**

- `not_applied`: Scraped/saved, not yet applied
- `applied`: User submitted an application (via bot or manually)
- `interview`: User invited to interview
- `rejected`: Marked as rejected by user or via web sync
- `skipped`: Explicitly skipped/hidden (manual workflow)

### **SQL schema as of 2024**

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_link TEXT UNIQUE NOT NULL,
    job_key TEXT,
    source TEXT DEFAULT 'indeed',
    search_query TEXT,
    location TEXT,
    country TEXT,
    language TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_summary TEXT,
    job_details TEXT,
    embedding TEXT,
    match_score REAL,
    match_reason TEXT,
    application_status TEXT DEFAULT 'not_applied',
    matched_at TIMESTAMP,
    applied_at TIMESTAMP
);
```

**Relevant DB Indexes (auto-created):**
```sql
CREATE INDEX IF NOT EXISTS idx_job_link ON jobs(job_link);
CREATE INDEX IF NOT EXISTS idx_job_key ON jobs(job_key);
CREATE INDEX IF NOT EXISTS idx_application_status ON jobs(application_status);
```

---

## 👤 Table: `user_profile`

**Purpose:**  
Stores the single (primary) user profile in use by the bot, mapping to your config and supporting resume & cover letter generation. Sync is from `config.yaml → user_profile` via CLI.

| Column                 | Type      | Constraints / Default     | Description                                  |
| ---------------------- | --------- | ------------------------- | -------------------------------------------- |
| `id`                   | INTEGER   | PRIMARY KEY AUTOINCREMENT | Always 1 (single-profile model)              |
| `name`                 | TEXT      |                           | Full name                                    |
| `location`             | TEXT      |                           | City/region                                  |
| `professional_summary` | TEXT      |                           | Main summary headline or professional bio    |
| `work_experience`      | TEXT      | JSON                      | List of work experience objects (JSON)       |
| `education`            | TEXT      | JSON                      | List of education objects (JSON)             |
| `technical_skills`     | TEXT      |                           | Comma-separated technology/skill strings     |
| `soft_skills`          | TEXT      |                           | Comma-separated soft/personal skills         |
| `certifications`       | TEXT      | JSON                      | List: certifications, awards, licenses (JSON)|
| `languages`            | TEXT      | JSON                      | List of languages + proficiency (JSON)       |
| `job_preferences`      | TEXT      | JSON                      | Preferences: roles, locations, salary, etc   |
| `experience_level`     | TEXT      |                           | e.g., `entry`, `mid`, `senior`               |
| `created_at`           | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When created                                 |
| `updated_at`           | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When last updated (upon profile sync)        |

### **SQL schema as of 2024**
```sql
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    location TEXT,
    professional_summary TEXT,
    work_experience TEXT,
    education TEXT,
    technical_skills TEXT,
    soft_skills TEXT,
    certifications TEXT,
    languages TEXT,
    job_preferences TEXT,
    experience_level TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- All JSON fields are stored as pretty-printed or minified JSON strings per Python `json.dumps`.
- Profile fields directly map to DOCX template placeholders (see `docs/templates.md`). They are updatable via config and the `process_jobs.py --sync-profile` command.

---

**For more schema details, workflow, or troubleshooting, see:**  
- `docs/PROJECT_OVERVIEW.md` (architecture, workflow, and update policy)
- `_database.py` (table migration logic)
- `docs/templates.md` (template/document mapping mechanics)
