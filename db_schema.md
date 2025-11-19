# Database Schemas

This document provides a clean, structured, and stylistically improved version of your database schema documentation for both the **`jobs`** and **`user_profile`** tables.

---

## 🗂️ Jobs Table Schema

Stores all data related to job postings scraped or processed by the system.

### **Table: `jobs`**

| Column               | Type      | Constraints / Default     | Description                                        |
| -------------------- | --------- | ------------------------- | -------------------------------------------------- |
| `id`                 | INTEGER   | PRIMARY KEY AUTOINCREMENT | Unique identifier for each job entry               |
| `job_link`           | TEXT      | UNIQUE NOT NULL           | Canonical URL of the job posting                   |
| `job_key`            | TEXT      |                           | Indeed-specific job key                            |
| `source`             | TEXT      | DEFAULT 'indeed'          | Source of posting (e.g., `indeed`, `aggregator`)   |
| `search_query`       | TEXT      |                           | Keywords used when searching for this job          |
| `location`           | TEXT      |                           | City or region of the job posting                  |
| `country`            | TEXT      |                           | Country code (e.g., `us`, `fr`)                    |
| `language`           | TEXT      |                           | Language used during scraping                      |
| `scraped_at`         | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the job was first scraped           |
| `created_at`         | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when record was inserted                 |
| `job_summary`        | TEXT      |                           | Plaintext summary (used for embeddings + matching) |
| `job_details`        | TEXT      |                           | Raw or expanded JSON job data                      |
| `embedding`          | TEXT      |                           | JSON-encoded embedding vector                      |
| `match_score`        | REAL      |                           | AI/algorithmic relevance score                     |
| `match_reason`       | TEXT      |                           | Explanation for the match score                    |
| `application_status` | TEXT      | DEFAULT 'not_applied'     | Application stage/status                           |
| `matched_at`         | TIMESTAMP |                           | Timestamp when job was AI-matched                  |
| `applied_at`         | TIMESTAMP |                           | Timestamp when user applied                        |

### **Status Values for `application_status`**

| Status        | Description                        |
| ------------- | ---------------------------------- |
| `not_applied` | Job saved but user has not applied |
| `applied`     | User submitted an application      |
| `interview`   | User advanced to interview stage   |
| `rejected`    | User was rejected                  |
| `skipped`     | User intentionally skipped the job |

### **Example Match Metadata**

* `match_score`: `0.85`
* `match_reason`: `Skills matched; preferred location; strong relevance`

### **SQL — Table Creation**

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

### **SQL — Indexes**

```sql
CREATE INDEX IF NOT EXISTS idx_job_link ON jobs(job_link);
CREATE INDEX IF NOT EXISTS idx_job_key ON jobs(job_key);
CREATE INDEX IF NOT EXISTS idx_application_status ON jobs(application_status);
```

---

## 👤 User Profile Table Schema

Stores user professional and preference information used for job matching.

### **Table: `user_profile`**

| Column                 | Type      | Constraints / Default     | Description                        |
| ---------------------- | --------- | ------------------------- | ---------------------------------- |
| `id`                   | INTEGER   | PRIMARY KEY AUTOINCREMENT | Unique identifier                  |
| `name`                 | TEXT      |                           | User's full name                   |
| `location`             | TEXT      |                           | User's city or region              |
| `professional_summary` | TEXT      |                           | Short professional bio             |
| `work_experience`      | TEXT      | JSON                      | List of experience objects         |
| `education`            | TEXT      | JSON                      | List of education objects          |
| `technical_skills`     | TEXT      |                           | Comma-separated technical skills   |
| `soft_skills`          | TEXT      |                           | Comma-separated soft skills        |
| `certifications`       | TEXT      | JSON                      | List of certifications             |
| `languages`            | TEXT      | JSON                      | List of languages + proficiency    |
| `job_preferences`      | TEXT      | JSON                      | Job preference metadata            |
| `experience_level`     | TEXT      |                           | e.g., `entry`, `mid`, `senior`     |
| `created_at`           | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when record created      |
| `updated_at`           | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when record last updated |

### **SQL — Table Creation**

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

---