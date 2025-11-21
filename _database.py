import re
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List


class Database:

    def __init__(self, db_path: str = "indeed_jobs.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def init_database(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
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
            )"""
        )

        try:
            self.cursor.execute("PRAGMA table_info(jobs)")
            columns = [col[1] for col in self.cursor.fetchall()]

            if "application_status" not in columns:
                self.cursor.execute(
                    'ALTER TABLE jobs ADD COLUMN application_status TEXT DEFAULT "not_applied"'
                )
                print("Database migrated: Added application_status column")

            if "match_score" not in columns:
                self.cursor.execute("ALTER TABLE jobs ADD COLUMN match_score REAL")
                print("Database migrated: Added match_score column")

            if "match_reason" not in columns:
                self.cursor.execute("ALTER TABLE jobs ADD COLUMN match_reason TEXT")
                print("Database migrated: Added match_reason column")

            if "matched_at" not in columns:
                self.cursor.execute("ALTER TABLE jobs ADD COLUMN matched_at TIMESTAMP")
                print("Database migrated: Added matched_at column")

            if "applied_at" not in columns:
                self.cursor.execute("ALTER TABLE jobs ADD COLUMN applied_at TIMESTAMP")
                print("Database migrated: Added applied_at column")

            if "job_summary" not in columns:
                self.cursor.execute("ALTER TABLE jobs ADD COLUMN job_summary TEXT")
                print("Database migrated: Added job_summary column")

            if "job_details" not in columns:
                self.cursor.execute("ALTER TABLE jobs ADD COLUMN job_details TEXT")
                print("Database migrated: Added job_details column")

            if "embedding" not in columns:
                self.cursor.execute("ALTER TABLE jobs ADD COLUMN embedding TEXT")
                print("Database migrated: Added embedding column")

            self.conn.commit()
        except Exception as e:
            print(f"Migration note: {e}")

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_link ON jobs(job_link)
        """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_key ON jobs(job_key)
        """
        )

        try:
            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_application_status ON jobs(application_status)
            """
            )
        except Exception as e:
            pass

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_match_score ON jobs(match_score)
        """
        )

        self.cursor.execute(
            """
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
            )
        """
        )

        try:
            self.cursor.execute("ALTER TABLE jobs ADD COLUMN job_summary TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE jobs ADD COLUMN job_details TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE jobs ADD COLUMN embedding TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE jobs ADD COLUMN match_score REAL")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE jobs ADD COLUMN match_reason TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute(
                'ALTER TABLE jobs ADD COLUMN application_status TEXT DEFAULT "not_applied"'
            )
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE jobs ADD COLUMN matched_at TIMESTAMP")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE jobs ADD COLUMN applied_at TIMESTAMP")
        except sqlite3.OperationalError:
            pass

        self.conn.commit()
        return self.db_path

    def get_jobs_from_db(self, limit: Optional[int] = None):
        query = """
            SELECT id, job_link, job_summary, job_details, embedding
            FROM jobs
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        jobs = self.cursor.fetchall()
        return jobs

    def save_job_link(
        self,
        job_link,
        job_key=None,
        search_query=None,
        location=None,
        country=None,
        language=None,
    ):
        try:
            if not job_key and "jk=" in job_link:
                try:
                    match = re.search(r"jk=([a-zA-Z0-9]+)", job_link)
                    if match:
                        job_key = match.group(1)
                except Exception:
                    pass

            self.cursor.execute(
                """
                INSERT OR IGNORE INTO jobs 
                (job_link, job_key, source, search_query, location, country, language, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    job_link,
                    job_key,
                    "indeed",
                    search_query,
                    location,
                    country,
                    language,
                    datetime.now(),
                ),
            )

            self.conn.commit()
            return (
                self.cursor.rowcount > 0
            )
        except Exception as e:
            self.conn.rollback()
            raise e

    def save_user_profile(self, user_profile: Dict[str, Any]) -> bool:
        try:
            work_experience_json = json.dumps(user_profile.get("work_experience", []))
            education_json = json.dumps(user_profile.get("education", []))
            certifications_json = json.dumps(user_profile.get("certifications", []))
            languages_json = json.dumps(user_profile.get("languages", []))
            job_preferences_json = json.dumps(user_profile.get("job_preferences", {}))

            technical_skills_str = ", ".join(user_profile.get("technical_skills", []))
            soft_skills_str = ", ".join(user_profile.get("soft_skills", []))

            self.cursor.execute("SELECT id FROM user_profile LIMIT 1")
            existing = self.cursor.fetchone()

            if existing:
                self.cursor.execute(
                    """
                    UPDATE user_profile
                    SET name = ?, location = ?, professional_summary = ?,
                        work_experience = ?, education = ?, technical_skills = ?,
                        soft_skills = ?, certifications = ?, languages = ?,
                        job_preferences = ?, experience_level = ?,
                        updated_at = ?
                    WHERE id = ?
                """,
                    (
                        user_profile.get("name"),
                        user_profile.get("location"),
                        user_profile.get("professional_summary"),
                        work_experience_json,
                        education_json,
                        technical_skills_str,
                        soft_skills_str,
                        certifications_json,
                        languages_json,
                        job_preferences_json,
                        user_profile.get("experience_level"),
                        datetime.now(),
                        existing[0],
                    ),
                )
            else:
                self.cursor.execute(
                    """
                    INSERT INTO user_profile
                    (name, location, professional_summary, work_experience, education,
                    technical_skills, soft_skills, certifications, languages,
                    job_preferences, experience_level, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_profile.get("name"),
                        user_profile.get("location"),
                        user_profile.get("professional_summary"),
                        work_experience_json,
                        education_json,
                        technical_skills_str,
                        soft_skills_str,
                        certifications_json,
                        languages_json,
                        job_preferences_json,
                        user_profile.get("experience_level"),
                        datetime.now(),
                        datetime.now(),
                    ),
                )

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error saving user profile: {e}")
            return False

    def get_job_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM jobs")
        count = self.cursor.fetchone()[0]
        return count

    def load_user_profile(self) -> Optional[Dict[str, Any]]:
        try:
            self.cursor.execute(
                "SELECT * FROM user_profile ORDER BY updated_at DESC LIMIT 1"
            )
            row = self.cursor.fetchone()

            if not row:
                return None

            profile = {
                "name": row[1],
                "location": row[2],
                "professional_summary": row[3],
                "work_experience": json.loads(row[4]) if row[4] else [],
                "education": json.loads(row[5]) if row[5] else [],
                "technical_skills": (
                    [s.strip() for s in row[6].split(",")] if row[6] else []
                ),
                "soft_skills": [s.strip() for s in row[7].split(",")] if row[7] else [],
                "certifications": json.loads(row[8]) if row[8] else [],
                "languages": json.loads(row[9]) if row[9] else [],
                "job_preferences": json.loads(row[10]) if row[10] else {},
                "experience_level": row[11],
            }

            return profile
        except Exception as e:
            print(f"Error loading user profile: {e}")
            return None

    def get_matched_jobs(
        self,
        min_score: float = 0.6,
        limit: Optional[int] = None,
        order_by: str = "match_score DESC",
    ) -> List[Dict[str, Any]]:
        query = f"""
                SELECT 
                    id, job_link, job_key, source, search_query, location, country, language,
                    scraped_at, created_at, job_summary, match_score, match_reason,
                    application_status, matched_at, applied_at
                FROM jobs
                WHERE match_score >= ? AND application_status = 'matched'
                ORDER BY {order_by}
            """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query, (min_score,))
        rows = self.cursor.fetchall()

        matched_jobs = []
        for row in rows:
            matched_jobs.append(
                {
                    "id": row[0],
                    "job_link": row[1],
                    "job_key": row[2],
                    "source": row[3],
                    "search_query": row[4],
                    "location": row[5],
                    "country": row[6],
                    "language": row[7],
                    "scraped_at": row[8],
                    "created_at": row[9],
                    "job_summary": row[10],
                    "match_score": row[11],
                    "match_reason": row[12],
                    "application_status": row[13],
                    "matched_at": row[14],
                    "applied_at": row[15],
                }
            )

        self.conn.close()
        return matched_jobs

    def _job_already_matched_in_db(self, normalized_link: str) -> bool:
        self.cursor.execute(
            "SELECT id FROM jobs WHERE job_link = ? AND application_status = 'matched'",
            (normalized_link,),
        )
        already_matched = self.cursor.fetchone() is not None
        return already_matched

    def _save_matched_job_to_db(
        self,
        normalized_link: str,
        job_key: Optional[str],
        search_query: Optional[str],
        location: Optional[str],
        country: Optional[str],
        language: Optional[str],
        job_summary: str,
        job_details: Dict,
        job_embedding_json: Optional[str],
        score: float,
        reason: str,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO jobs 
            (job_link, job_key, source, search_query, location, country, language, 
            scraped_at, job_summary, job_details, embedding, match_score, match_reason, 
            matched_at, application_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_link) DO UPDATE SET
                job_key=excluded.job_key,
                source=excluded.source,
                search_query=excluded.search_query,
                location=excluded.location,
                country=excluded.country,
                language=excluded.language,
                scraped_at=excluded.scraped_at,
                job_summary=excluded.job_summary,
                job_details=excluded.job_details,
                embedding=excluded.embedding,
                match_score=excluded.match_score,
                match_reason=excluded.match_reason,
                matched_at=excluded.matched_at,
                application_status=excluded.application_status
            """,
            (
                normalized_link,
                job_key,
                "indeed",
                search_query,
                location,
                country,
                language,
                datetime.now(),
                job_summary,
                json.dumps(job_details),
                job_embedding_json,
                score,
                reason,
                datetime.now(),
                "matched",
            ),
        )
        self.conn.commit()

    def save_matched_job_to_db(self, job_data: Dict[str, Any]) -> bool:
        try:
            self._save_matched_job_to_db(
                normalized_link=job_data.get("normalized_link", ""),
                job_key=job_data.get("job_key"),
                search_query=job_data.get("search_query"),
                location=job_data.get("location"),
                country=job_data.get("country"),
                language=job_data.get("language"),
                job_summary=job_data.get("job_summary", ""),
                job_details=job_data.get("job_details", {}),
                job_embedding_json=job_data.get("job_embedding_json"),
                score=job_data.get("score", 0.0),
                reason=job_data.get("reason", ""),
            )
            return True
        except Exception as e:
            print(f"Error saving matched job: {e}")
            self.conn.rollback()
            return False

    def fetch_jobs_from_db(
        self,
        limit: Optional[int] = None,
    ) -> List[tuple]:
        query = """
            SELECT id, job_link, job_summary, job_details, embedding
            FROM jobs
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        jobs = self.cursor.fetchall()
        return jobs

    def update_job_in_db(
        self,
        job_id: int,
        job_summary: str,
        job_details: Any,
        job_embedding: Any,
        stored_embedding_json: Any,
        score: float,
        reason: str,
        matched_at_value: Any,
        application_status: str,
    ):
        self.cursor.execute(
            """
            UPDATE jobs
            SET job_summary=?,
                job_details=?,
                embedding=?,
                match_score=?,
                match_reason=?,
                matched_at=?,
                application_status=?
            WHERE id=?
            """,
            (
                job_summary,
                json.dumps(job_details) if job_details else None,
                json.dumps(job_embedding) if job_embedding else stored_embedding_json,
                score,
                reason,
                matched_at_value,
                application_status,
                job_id,
            ),
        )
        self.conn.commit()

    def fetch_dashboard_stats_from_db(self) -> Dict[str, Any]:
        stats = {}

        self.cursor.execute("SELECT COUNT(*) FROM jobs")
        stats["jobs_fetched"] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_summary IS NOT NULL")
        stats["jobs_with_summary"] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 0.6")
        stats["jobs_matched"] = self.cursor.fetchone()[0]

        self.cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE application_status = 'applied'"
        )
        stats["jobs_applied"] = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT application_status, COUNT(*) 
            FROM jobs 
            GROUP BY application_status
        """
        )
        stats["status_breakdown"] = dict(self.cursor.fetchall())

        self.cursor.execute(
            """
            SELECT job_link, match_score, match_reason, application_status
            FROM jobs
            WHERE match_score IS NOT NULL
            ORDER BY match_score DESC
            LIMIT 10
        """
        )
        stats["top_matched_jobs"] = [
            {"job_link": row[0], "score": row[1], "reason": row[2], "status": row[3]}
            for row in self.cursor.fetchall()
        ]

        self.cursor.execute(
            "SELECT AVG(match_score) FROM jobs WHERE match_score IS NOT NULL"
        )
        avg_score = self.cursor.fetchone()[0]
        stats["average_match_score"] = round(avg_score, 3) if avg_score else 0.0

        self.conn.close()
        return stats

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Database connection closed.")
