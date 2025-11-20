"""
Indeed Auto-Apply Bot
---------------------
Automates job applications on Indeed using Camoufox.

Usage:
  - Configure your search and Chrome settings in config.yaml
  - Run: python indeed_bot.py

Author: @meteor314
License: MIT
"""

import yaml
import time
import random
import signal
import sys
import json
import re
import os
import math
import urllib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from camoufox.sync_api import Camoufox


from _database import Database
from _indeed import Indeed, REQUESTS_AVAILABLE
from _open_ai import OpenAI_Manager
import _utils


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
camoufox_config = config.get("camoufox", {})
user_data_dir = camoufox_config.get("user_data_dir")

# Get search config with defaults
search_config = config.get("search", {})
country = search_config.get("country", "us")
language = search_config.get("language", "us")  # Use language from search config
openAI_api_key = config.get("openai", {}).get("api_key")

db = Database("indeed_jobs.db")
indeed = Indeed()
openAI_manager = OpenAI_Manager(openAI_api_key)


def collect_job_links(page, language, country):
    """Extract real viewjob links from job cards by extracting job key and constructing proper URLs."""
    job_links = []

    # Wait for job cards to appear on the page
    try:
        # Wait for job title links to appear (the actual job cards are <a> tags)
        page.wait_for_selector('a.jcs-JobTitle, a[jk], a[id^="job_"]', timeout=15000)
    except Exception:
        # If no jobs found, try alternative selectors
        try:
            page.wait_for_selector('a[class*="JobTitle"]', timeout=5000)
        except Exception:
            pass

    # Wait a bit longer for cards to fully load (especially important for subsequent pages)
    time.sleep(2 + random.uniform(0.5, 1))

    # Select job cards - they are <a> tags with specific attributes
    # Each job card is an <a> tag with:
    # - class="jcs-JobTitle ..."
    # - data-jk attribute (job key) - THIS IS WHAT WE NEED
    # - id="job_<job_key>"
    job_cards = []

    # Strategy 1: Select by class jcs-JobTitle (most reliable)
    job_cards = page.query_selector_all("a.jcs-JobTitle")

    # Strategy 2: Select by data-jk attribute
    if not job_cards:
        job_cards = page.query_selector_all("a[jk]")

    # Strategy 3: Select by id pattern (id starts with "job_")
    if not job_cards:
        job_cards = page.query_selector_all('a[id^="job_"]')

    # Get the domain for constructing URLs
    domain = indeed.get_indeed_domain(country)

    print(f"Found {len(job_cards)} job cards (expected ~15 per page)")

    # Extract job keys and construct real viewjob URLs
    for idx, card in enumerate(job_cards):
        try:
            # Extract job key from data-jk attribute (most reliable)
            job_key = None
            try:
                job_key = card.get_attribute("jk")
            except Exception:
                pass

            # Fallback: Extract from id attribute (id="job_<job_key>")
            if not job_key:
                try:
                    card_id = card.get_attribute("id")
                    if card_id and card_id.startswith("job_"):
                        job_key = card_id.replace("job_", "")
                except Exception:
                    pass

            # Fallback: Extract from href if it contains jk=
            if not job_key:
                try:
                    href = card.get_attribute("href")
                    if href and "jk=" in href:
                        match = re.search(r"jk=([a-zA-Z0-9]+)", href)
                        if match:
                            job_key = match.group(1)
                except Exception:
                    pass

            # Construct the real viewjob URL
            if job_key:
                # Real job link format: https://www.indeed.com/viewjob?jk=<job_key>&from=serp&vjs=3
                viewjob_url = f"https://{domain}/viewjob?jk={job_key}&from=serp&vjs=3"
                job_links.append(viewjob_url)
                print(f"  [Card {idx+1}/{len(job_cards)}] Link: {viewjob_url[:80]}...")
            else:
                print(
                    f"  [Card {idx+1}/{len(job_cards)}] Warning: Could not extract job key"
                )
        except Exception as e:
            # Skip cards that cause errors
            print(f"  [Card {idx+1}] Error: {e}")
            continue

    return job_links


# def apply_to_job(browser, job_url, language, logger):
#     """Open a new tab, apply to the job, log the result, and close the tab."""
#     page = browser.new_page()
#     try:
#         page.goto(job_url)
#         page.wait_for_load_state("domcontentloaded")
#         time.sleep(3)
#         # Try to find the "Apply now" button using robust, language-agnostic selectors
#         apply_btn = None
#         for _ in range(20):
#             # 1. Try button with "Apply now" text
#             apply_btn = page.query_selector(
#                 'button:visible:has-text("Apply now")')
#             if not apply_btn:
#                 apply_btn = page.query_selector(
#                     'button:visible:has-text("Apply Now")')
#             if not apply_btn:
#                 apply_btn = page.query_selector(
#                     'a:visible:has-text("Apply now")')
#             # 2. Try button with a span with the unique apply class (often css-1ebo7dz)
#             if not apply_btn:
#                 apply_btn = page.query_selector(
#                     'button:has(span[class*="css-1ebo7dz"])')
#             # 3. Fallback: first visible button with a span containing "Postuler" or "Apply"
#             if not apply_btn:
#                 apply_btn = page.query_selector(
#                     'button:visible:has-text("Postuler")')
#             if not apply_btn:
#                 apply_btn = page.query_selector(
#                     'button:visible:has-text("Apply")')
#             # 4. Fallback: first visible button on the page (avoid close/cancel if possible)
#             if not apply_btn:
#                 btns = page.query_selector_all('button:visible')
#                 for btn in btns:
#                     label = (btn.get_attribute("aria-label") or "").lower()
#                     text = (btn.inner_text() or "").lower()
#                     if "close" in label or "cancel" in label or "fermer" in label or "annuler" in label:
#                         continue
#                     if "apply" in text or "postuler" in text or btn.is_visible():
#                         apply_btn = btn
#                         break
#             if apply_btn:
#                 break
#             time.sleep(0.5)
#         if apply_btn:
#             click_and_wait(apply_btn, 5)
#         else:
#             logger.warning(
#                 f"No Apply now button found for {job_url}")
#             page.close()
#             return False

#         # add timeout for the wizard loop
#         start_time = time.time()
#         while True:
#             if time.time() - start_time > 40:
#                 logger.warning(
#                     f"Timeout applying to {job_url}, closing tab and moving to next.")
#                 break
#             current_url = page.url
#             # Resume step: select resume card if present
#             resume_card = page.query_selector(
#                 '[data-testid="FileResumeCardHeader-title"]')
#             if resume_card:
#                 # Click the resume card (or its parent if needed)
#                 try:
#                     resume_card.click()
#                 except Exception:
#                     parent = resume_card.evaluate_handle(
#                         'node => node.parentElement')
#                     if parent:
#                         parent.click()
#                 time.sleep(1)
#                 continuer_btn = None
#                 btns = page.query_selector_all('button:visible')
#                 for btn in btns:
#                     text = (btn.inner_text() or "").lower()
#                     if "continuer" in text or "continue" in text:
#                         continuer_btn = btn
#                         break
#                 if continuer_btn:
#                     click_and_wait(continuer_btn, 3)
#                     continue  # go to next step

#             # try to find a submit button ( dynamic text) idk if it's working
#             submit_btn = None
#             btns = page.query_selector_all('button:visible')
#             for btn in btns:
#                 text = (btn.inner_text() or "").lower()
#                 if (
#                     "déposer ma candidature" in text or
#                     "soumettre" in text or
#                     "submit" in text or
#                     "apply" in text or
#                     "bewerben" in text or  # German
#                     "postular" in text     # Spanish
#                 ):
#                     submit_btn = btn
#                     break
#             # fallback: last visible button (often the submit)
#             if not submit_btn and btns:
#                 submit_btn = btns[-1]
#             if submit_btn:
#                 click_and_wait(submit_btn, 3)
#                 logger.info(f"Applied successfully to {job_url}")
#                 break

#             # fallback: try to find a visible and enabled button to continue (other stesp)
#             btn = page.query_selector(
#                 'button[type="button"]:not([aria-disabled="true"]), button[type="submit"]:not([aria-disabled="true"])')
#             if btn:
#                 click_and_wait(btn, 3)
#                 if "confirmation" in page.url or "submitted" in page.url:
#                     logger.info(f"Applied successfully to {job_url}")
#                     break
#             else:
#                 logger.warning(
#                     f"No continue/submit button found at {current_url}")
#                 break
#         page.close()
#         return True
#     except Exception as e:
#         logger.error(f"Error applying to {job_url}: {e}")
#         page.close()
#         return False


def process_job_for_matching(
    job_link: str,
    openai_client: Any,
    user_profile: Dict[str, Any],
    user_profile_embedding: Optional[List[float]],
    browser_page: Optional[Any] = None,
    search_query: str = None,
    location: str = None,
    country: str = None,
    language: str = None,
    min_score: float = 0.6,
) -> Optional[Dict[str, Any]]:
    if not openai_client or not user_profile:
        return None

    try:
        # Normalize job link
        normalized_link = indeed.normalize_job_link(job_link)

        # Extract job_key
        job_key = None
        if "jk=" in normalized_link:
            try:
                match = re.search(r"jk=([a-zA-Z0-9]+)", normalized_link)
                if match:
                    job_key = match.group(1)
            except Exception:
                pass

        # Scrape job details either from the currently open detail panel or via HTTP
        job_details = None
        if browser_page and job_key:
            job_details = indeed.scrape_job_details_from_dom(
                browser_page, job_key, normalized_link, country or ""
            )

        if not job_details:
            job_details = indeed.scrape_job_details_from_link(normalized_link, REQUESTS_AVAILABLE)
        if not job_details:
            return None

        job_summary = _utils.format_job_details_for_summary(job_details)
        if not job_summary:
            return None

        job_embedding_list = None
        job_embedding_json = None
        if openai_client:
            job_embedding_list = get_embedding(job_summary, openai_client)
            if job_embedding_list:
                job_embedding_json = json.dumps(job_embedding_list)

        # Match the job against the user profile
        score, reason = calculate_match_score(
            job_summary, job_embedding_list, user_profile, user_profile_embedding
        )
        print(f"score: {score}")
        print(f"reason: {reason}")

        if score >= min_score:
            return {
                "normalized_link": normalized_link,
                "job_key": job_key,
                "search_query": search_query,
                "location": location,
                "country": country,
                "language": language,
                "job_summary": job_summary,
                "job_details": job_details,
                "job_embedding_json": job_embedding_json,
                "score": score,
                "reason": reason,
            }
        else:
            return None

    except Exception as e:
        print(f"  ✗ Error processing job: {e}")
        return None


def process_and_save_job_immediately(
    job_link: str,
    openai_client: Any,
    user_profile: Dict[str, Any],
    user_profile_embedding: Optional[List[float]],
    browser_page: Optional[Any] = None,
    search_query: str = None,
    location: str = None,
    country: str = None,
    language: str = None,
    min_score: float = 0.6,
) -> bool:
    job_data = process_job_for_matching(
        job_link,
        openai_client,
        user_profile,
        user_profile_embedding,
        browser_page=browser_page,
        search_query=search_query,
        location=location,
        country=country,
        language=language,
        min_score=min_score,
    )
    if job_data is not None:
        return db.save_matched_job_to_db(job_data)
    return False


def sync_profile_from_config() -> bool:
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            user_profile = config.get("user_profile", {})

        if not user_profile:
            print("No user_profile found in config.yaml")
            return False

        success = db.save_user_profile(user_profile)
        if success:
            print("User profile synced from config.yaml to database")
        return success
    except Exception as e:
        print(f"Error syncing profile from config: {e}")
        return False


# ============================================================================
# OpenAI Integration Functions
# ============================================================================




def get_embedding(
    text: str,
    client: Any,
    model: str = "text-embedding-3-small",
    max_length: int = 8000,
    retries: int = 2,
) -> Optional[List[float]]:
    """Generate an embedding vector for text using OpenAI with safety checks and retries."""

    if not client:
        print("Error: OpenAI client missing in get_embedding()")
        return None

    if not text or not isinstance(text, str):
        print("Error: Invalid or empty text passed to get_embedding()")
        return None

    # 1️⃣ Sanitize text (avoid sending extremely long text)
    clean_text = text.strip()
    if len(clean_text) > max_length:
        clean_text = clean_text[:max_length]

    # 2️⃣ Retry logic
    for attempt in range(retries + 1):
        try:
            response = client.embeddings.create(model=model, input=clean_text)

            # 3️⃣ Validate response
            if not response or not response.data or len(response.data) == 0:
                print("Error: Empty embedding response from OpenAI")
                continue

            # 4️⃣ Return embedding
            return response.data[0].embedding

        except Exception as e:
            print(f"[Attempt {attempt+1}] Error getting embedding: {e}")

    print("Embedding failed after retries.")
    return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


# ============================================================================
# AI Matching Functions
# ============================================================================


def keyword_score(job_summary: str, user_profile: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate keyword-based scores for different criteria.
    Returns a dictionary with scores for: relevance, location, role_type, experience
    """
    if not job_summary:
        return {"relevance": 0.0, "location": 0.0, "role_type": 0.0, "experience": 0.0}

    summary_lower = job_summary.lower()
    scores = {"relevance": 0.0, "location": 0.0, "role_type": 0.0, "experience": 0.0}

    # Relevance scoring: match desired skills/technologies
    # Combine technical and soft skills
    technical_skills = user_profile.get("technical_skills", [])
    soft_skills = user_profile.get("soft_skills", [])
    desired_skills = technical_skills + soft_skills

    # Also check work experience titles and descriptions
    work_experience = user_profile.get("work_experience", [])
    for exp in work_experience:
        if exp.get("title"):
            # Extract skills from job titles (e.g., "Python Developer" -> "Python")
            title_words = exp["title"].split()
            desired_skills.extend([w for w in title_words if len(w) > 3])

    if desired_skills:
        matched_skills = sum(
            1 for skill in desired_skills if skill.lower() in summary_lower
        )
        scores["relevance"] = min(1.0, matched_skills / max(len(desired_skills), 1))

    # Location scoring
    job_prefs = user_profile.get("job_preferences", {})
    preferred_locations = job_prefs.get("preferred_locations", [])
    if preferred_locations:
        location_match = any(
            loc.lower() in summary_lower for loc in preferred_locations
        )
        if location_match:
            scores["location"] = 1.0
        elif "remote" in summary_lower or "work from home" in summary_lower:
            if job_prefs.get("accept_remote", True):
                scores["location"] = 0.8
        else:
            scores["location"] = 0.3  # Partial score for other locations

    # Role type scoring
    preferred_types = job_prefs.get("preferred_job_types", ["full-time"])
    job_type_match = any(jt.lower() in summary_lower for jt in preferred_types)
    if job_type_match:
        scores["role_type"] = 1.0
    else:
        scores["role_type"] = 0.5  # Partial score

    # Experience level scoring
    user_experience = user_profile.get("experience_level", "mid")
    experience_keywords = {
        "entry": ["entry", "junior", "intern", "0-2 years", "0-1 years"],
        "mid": ["mid", "intermediate", "2-5 years", "3-5 years"],
        "senior": ["senior", "lead", "principal", "5+ years", "7+ years"],
    }

    summary_experience = experience_keywords.get(user_experience, [])
    if summary_experience:
        experience_match = any(exp in summary_lower for exp in summary_experience)
        if experience_match:
            scores["experience"] = 1.0
        else:
            # Check for adjacent levels
            if user_experience == "mid":
                if any(exp in summary_lower for exp in experience_keywords["entry"]):
                    scores["experience"] = 0.7
                elif any(exp in summary_lower for exp in experience_keywords["senior"]):
                    scores["experience"] = 0.6
            else:
                scores["experience"] = 0.4

    return scores


def calculate_match_score(
    job_summary: str,
    job_embedding: Optional[List[float]],
    user_profile: Dict[str, Any],
    user_profile_embedding: Optional[List[float]],
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, str]:
    """
    Calculate overall match score combining embeddings and keyword scoring.
    Returns (score, reason) tuple.
    """
    print(f"user profile : ", user_profile)
    print(f"job summary : ", job_summary)
    if weights is None:
        weights = {
            "embedding": 0.4,  # 40% weight on semantic similarity
            "relevance": 0.3,  # 30% weight on skill relevance
            "location": 0.15,  # 15% weight on location
            "role_type": 0.1,  # 10% weight on job type
            "experience": 0.05,  # 5% weight on experience level
        }

    # Embedding similarity score
    embedding_score = 0.0
    if job_embedding and user_profile_embedding:
        embedding_score = cosine_similarity(job_embedding, user_profile_embedding)

    # Keyword scores
    keyword_scores = keyword_score(job_summary, user_profile)

    # Weighted combination
    final_score = (
        embedding_score * weights["embedding"]
        + keyword_scores["relevance"] * weights["relevance"]
        + keyword_scores["location"] * weights["location"]
        + keyword_scores["role_type"] * weights["role_type"]
        + keyword_scores["experience"] * weights["experience"]
    )

    # Generate reason
    reasons = []
    if embedding_score > 0.7:
        reasons.append("high semantic similarity")
    if keyword_scores["relevance"] > 0.7:
        reasons.append("strong skill match")
    if keyword_scores["location"] > 0.7:
        reasons.append("preferred location")
    if keyword_scores["role_type"] > 0.7:
        reasons.append("preferred job type")
    if keyword_scores["experience"] > 0.7:
        reasons.append("matching experience level")

    reason = ", ".join(reasons) if reasons else "general match"

    return (final_score, reason)


def profile_to_text(profile: Dict[str, Any]) -> str:
    lines = []
    if profile.get("professional_summary"):
        lines.append(profile["professional_summary"].strip())
    for a in profile.get("key_achievements", []):
        if a:
            lines.append(f"Achievement: {a}")
    prefs = profile.get("job_preferences", {})
    if prefs.get("desired_role"):
        lines.append(f"Desired role: {prefs['desired_role']}")
    for exp in profile.get("work_experience", []):
        t = exp.get("title", "")
        c = exp.get("company", "")
        l = exp.get("location", "")
        d = exp.get("duration", "")
        desc = exp.get("description", "")
        s = " ".join(
            filter(
                None,
                [
                    t,
                    f"at {c}" if c else "",
                    f"({l})" if l else "",
                    f"[{d}]" if d else "",
                ],
            )
        )
        desc = desc.strip().replace("\n", " ").replace("  ", " ") if desc else ""
        lines.append(f"{s}: {desc}" if s and desc else s or desc)
    tech = profile.get("technical_skills", [])
    if tech:
        lines.append("Technical skills: " + ", ".join(tech))
    soft = profile.get("soft_skills", [])
    if soft:
        lines.append("Soft skills: " + ", ".join(soft))
    for ed in profile.get("education", []):
        e = ed.get("degree", "")
        i = ed.get("institution", "")
        d = ed.get("duration", "")
        x = e
        if i:
            x += f" from {i}"
        if d:
            x += f" ({d})"
        if x:
            lines.append(x)
    certs = profile.get("certifications", [])
    for cert in certs:
        if isinstance(cert, dict):
            name = cert.get("name", "")
            issuer = cert.get("issuer", "")
            n = name
            if issuer:
                n += f" from {issuer}"
            if n:
                lines.append(n)
        elif isinstance(cert, str) and cert.strip():
            lines.append(cert.strip())
    for lng in profile.get("languages", []):
        if isinstance(lng, dict):
            lang = lng.get("language", "")
            prof = lng.get("proficiency", "")
            msg = f"Language: {lang}" + (f" ({prof})" if prof else "")
            if lang or prof:
                lines.append(msg)
        elif isinstance(lng, str) and lng.strip():
            lines.append(f"Language: {lng.strip()}")
    return " ".join(filter(None, lines))


def match_jobs(
    user_profile: Dict[str, Any],
    openai_client: Optional[Any] = None,
    min_score: float = 0.6,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Workflow:
        1. Ensure each stored job has scraped job details + summary text.
        2. Match the scraped content with the provided user profile.
        3. Save updated data to the database and return matches above min_score.
    """
    jobs = db.get_jobs_from_db(limit)
    matched_jobs: List[Dict[str, Any]] = []

    profile_text = profile_to_text(user_profile)
    user_profile_embedding = None
    if openai_client and profile_text:
        user_profile_embedding = get_embedding(profile_text, openai_client)

    for (
        job_id,
        job_link,
        stored_summary,
        stored_details_json,
        stored_embedding_json,
    ) in jobs:
        job_details = None
        if stored_details_json:
            try:
                job_details = json.loads(stored_details_json)
            except Exception:
                job_details = None

        job_summary = stored_summary or ""
        if not job_details or not job_summary:
            scraped = indeed.scrape_job_details_from_link(job_link, REQUESTS_AVAILABLE)
            if scraped:
                job_details = scraped
                job_summary = _utils.format_job_details_for_summary(scraped)

        if not job_summary:
            job_summary = f"Job posting could not be scraped for {job_link}"

        job_embedding = None
        if stored_embedding_json:
            try:
                job_embedding = json.loads(stored_embedding_json)
            except Exception:
                job_embedding = None

        if not job_embedding and openai_client and job_summary:
            job_embedding = get_embedding(job_summary, openai_client)

        score, reason = calculate_match_score(
            job_summary, job_embedding, user_profile, user_profile_embedding
        )

        matched = score >= min_score
        matched_at_value = datetime.now() if matched else None
        application_status = "matched" if matched else "not_matched"

        db.update_job_in_db(
            job_id,
            job_summary,
            job_details,
            job_embedding,
            score,
            reason,
            matched_at_value,
            application_status,
            stored_embedding_json
        )

        if matched:
            matched_jobs.append(
                {
                    "id": job_id,
                    "job_link": job_link,
                    "job_summary": job_summary,
                    "score": score,
                    "reason": reason,
                }
            )
    return matched_jobs


# ============================================================================
# Dashboard/Report Functions
# ============================================================================


def print_dashboard():
    """Print formatted dashboard to console."""
    stats = db.fetch_dashboard_stats_from_db()

    print("\n" + "=" * 60)
    print("JOB MATCHING DASHBOARD")
    print("=" * 60)
    print(f"\n📊 Overview:")
    print(f"   Jobs Fetched:        {stats['jobs_fetched']}")
    print(f"   Jobs with Summary:   {stats['jobs_with_summary']}")
    print(f"   Jobs Matched:        {stats['jobs_matched']}")
    print(f"   Jobs Applied:        {stats['jobs_applied']}")
    print(f"   Avg Match Score:     {stats['average_match_score']}")

    print(f"\n📈 Status Breakdown:")
    for status, count in stats["status_breakdown"].items():
        print(f"   {status}: {count}")

    if stats["top_matched_jobs"]:
        print(f"\n🏆 Top Matched Jobs:")
        for i, job in enumerate(stats["top_matched_jobs"][:5], 1):
            print(f"   {i}. Score: {job['score']:.2f} | Status: {job['status']}")
            print(f"      Reason: {job['reason']}")
            print(f"      Link: {job['job_link'][:80]}...")

    print("\n" + "=" * 60 + "\n")


def save_dashboard_json(
    output_file: Optional[str] = None
):
    """Save dashboard as JSON file."""
    if not output_file:
        output_file = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    stats = db.fetch_dashboard_stats_from_db()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"Dashboard saved to: {output_file}")
    return output_file


def check_login_status(page):
    """Check if user is logged in by checking for PPID cookie."""
    try:
        cookies = page.context.cookies()
        ppid_cookie = next(
            (cookie for cookie in cookies if cookie["name"] == "PPID"), None
        )
        return ppid_cookie is not None
    except Exception as e:
        print(f"Error checking login status: {e}")
        return False


def wait_for_manual_login(page, language, max_wait=300):
    """Wait for user to manually log in, checking periodically."""
    print("Token not found, please log in to Indeed first.")
    print("Redirecting to login page...")
    print("You need to restart the bot after logging in.")
    print("Press Ctrl+C to exit after logging in.")

    try:
        page.goto(f"https://secure.indeed.com/auth?hl={language}")
        page.wait_for_load_state("domcontentloaded")

        # Check every 5 seconds if user has logged in
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if check_login_status(page):
                print("Login detected! Please restart the bot.")
                return True
            time.sleep(5)
            print(".", end="", flush=True)

        print(
            f"\nTimeout after {max_wait} seconds. Please restart the bot after logging in."
        )
        return False
    except KeyboardInterrupt:
        print("\nInterrupted. Please restart the bot after logging in.")
        return False
    except Exception as e:
        print(f"\nError during login wait: {e}")
        return False


# Global browser reference for cleanup
browser_instance = None
shutdown_flag = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_flag
    shutdown_flag = True
    print("\n\nShutting down gracefully...")
    sys.exit(0)


# Register signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# No, this function does not need to get job links unless its role is to scrape and process jobs.
# If the purpose is just to initialize the browser and environment, the section gathering job links and processing them could be refactored out.
# Here is a version of the selection that does NOT collect job links or process them, but simply prepares the environment and shows what you'd do if you simply wanted to "set up":

try:
    with Camoufox(user_data_dir=user_data_dir, persistent_context=True) as browser:
        browser_instance = browser
        page = browser.new_page()
        
        try:
            # Get correct Indeed domain based on country
            indeed_domain = indeed.get_indeed_domain(country)
            page.goto(f"https://{indeed_domain}")
            page.wait_for_load_state("domcontentloaded")
            
            # Check if logged in
            if not check_login_status(page):
                wait_for_manual_login(page, language, country)
                page.close()
                sys.exit(0)
            
            print("Token found, proceeding with job search...")
            
            # Initialize database
            db_path = db.init_database()
            print(f"Database initialized: {db_path}")
            
            # Initialize OpenAI client and user profile for immediate processing
            openai_client = openAI_manager.get_openai_client()
            if not openai_client:
                print("Warning: OpenAI client not available. Jobs will be saved but not processed immediately.")
                print("You can process them later using: python process_jobs.py --extract-summaries --match")
                user_profile = None
                user_profile_embedding = None
            else:
                # Load user profile
                user_profile = db.load_user_profile()
                if not user_profile:
                    try:
                        with open("config.yaml", "r") as f:
                            config_data = yaml.safe_load(f)
                            user_profile = config_data.get("user_profile", {})
                        if user_profile:
                            sync_profile_from_config()
                    except Exception as e:
                        print(f"Warning: Could not load user profile: {e}")
                        user_profile = None
                
                # Generate user profile embedding once
                user_profile_embedding = None
                if user_profile and openai_client:
                    profile_parts = []
                    if user_profile.get("professional_summary"):
                        profile_parts.append(user_profile["professional_summary"])
                    job_prefs = user_profile.get("job_preferences", {})
                    if job_prefs.get("desired_role"):
                        profile_parts.append(f"Desired role: {job_prefs['desired_role']}")
                    work_experience = user_profile.get("work_experience", [])
                    for exp in work_experience:
                        exp_text = f"{exp.get('title', '')} at {exp.get('company', '')}: {exp.get('description', '')}"
                        profile_parts.append(exp_text)
                    technical_skills = user_profile.get("technical_skills", [])
                    soft_skills = user_profile.get("soft_skills", [])
                    if technical_skills:
                        profile_parts.append(f"Technical skills: {', '.join(technical_skills)}")
                    if soft_skills:
                        profile_parts.append(f"Soft skills: {', '.join(soft_skills)}")
                    education = user_profile.get("education", [])
                    for edu in education:
                        edu_text = f"{edu.get('degree', '')} from {edu.get('institution', '')}"
                        profile_parts.append(edu_text)
                    profile_text = " ".join(profile_parts)
                    if profile_text:
                        print("Generating user profile embedding...")
                        user_profile_embedding = get_embedding(profile_text, openai_client)
                        print("User profile embedding ready.")
                
                if user_profile:
                    print(f"User profile loaded. Processing jobs immediately with AI matching...")
                else:
                    print("Warning: No user profile found. Jobs will be saved but not matched.")
            
            # Get search parameters - only job and location are used
            job = search_config.get("job", "")
            location = search_config.get("location", "")
            
            # Validate required fields
            if not job:
                print("Error: 'job' field is required in config.yaml")
                sys.exit(1)
            
            # Build Indeed search URL
            # Use helper function to get correct domain
            base_domain = indeed.get_indeed_domain(country)
            
            # Build query parameters - only job and location
            params = {
                "q": job
            }
            
            # Add location if specified (including "remote")
            if location:
                params["l"] = location
            
            # Encode parameters
            query_string = urllib.parse.urlencode(params)
            base_url = f"https://{base_domain}/jobs?{query_string}"
            
            print(f"Search Configuration:")
            print(f"  Job: {job}")
            print(f"  Location: {location if location else 'Any location'}")
            print(f"  Country: {country}")
            print(f"  Language: {language}")
            print(f"  Base URL: {base_url}")
            print()

            # Collect all job links - scrape all pages until no more jobs found
            start_index = 0  # Start at page 0
            empty_pages_count = 0  # Track consecutive empty pages
            max_empty_pages = 2  # Stop after 2 consecutive empty pages
            max_pages = 1000  # Safety limit (1000 pages = 10,000 jobs max)
            
            print("Starting to process jobs with AI...")
            print("Each job will be: normalized → extract summary → match → save if matched")
            print("(Pages are paginated by increments of 10: start=0, 10, 20, 30, ...)")
            print()
            
            while start_index < max_pages * 10:
                if shutdown_flag:
                    break
                
                # Build URL with start parameter (skip start=0 for first page)
                if start_index == 0:
                    url = base_url  # First page has no start parameter
                else:
                    separator = "&" if "?" in base_url else "?"
                    url = f"{base_url}{separator}start={start_index}"
                page_num = (start_index // 10) + 1
                
                try:
                    print(f"[Page {page_num}] Visiting URL: {url}")
                    # Use load state instead of networkidle for better reliability
                    page.goto(url, wait_until="load", timeout=60000)
                    
                    # Wait for Cloudflare to pass (if present)
                    print("Waiting for page to fully load...")
                    try:
                        # Wait for Cloudflare challenge to complete or job cards to appear
                        page.wait_for_selector('a.jcs-JobTitle, a[data-jk], div#jobsearch', timeout=30000, state="visible")
                    except Exception:
                        # If Cloudflare is present, wait a bit longer
                        print("Cloudflare protection detected, waiting for manual interaction if needed...")
                        time.sleep(5)
                    
                    # Additional wait for dynamic content (especially important for page 2+)
                    wait_time = 6 + random.uniform(2, 4)
                    time.sleep(wait_time)
                    
                    # Wait for job listings to appear (job cards are <a> tags)
                    # This is critical for subsequent pages
                    try:
                        page.wait_for_selector('a.jcs-JobTitle, a[data-jk], a[id^="job_"]', timeout=15000)
                        print("Job cards detected on page")
                    except Exception:
                        print("Warning: Job listings may not have loaded yet, trying anyway...")
                        # Wait a bit more and try again
                        time.sleep(3)

                    try:
                        # Debug: Check current page URL
                        current_url = page.url
                        print(f"[Page {page_num}] Current page URL: {current_url[:100]}...")
                        
                        job_links = collect_job_links(page, language, country)
                        
                        if job_links:
                            # Found jobs on this page
                            empty_pages_count = 0  # Reset empty pages counter
                            
                            # Process each job immediately: extract summary, match, and save if matched
                            matched_count = 0
                            skipped_count = 0
                            error_count = 0
                            
                            for i, link in enumerate(job_links, 1):
                                # _utils.click_and_wait()
                                print(f"  [{i}/{len(job_links)}] Processing: {link[:60]}...")

                                print(openai_client, user_profile)
                                if openai_client and user_profile:
                                    # Process immediately: extract summary, match, save if matched
                                    matched = process_and_save_job_immediately(
                                        link, openai_client, user_profile,
                                        user_profile_embedding, page, job, location, country, language
                                    )
                                    if matched:
                                        matched_count += 1
                                        print(f"    ✓ Matched and saved")
                                    else:
                                        skipped_count += 1
                                        print(f"    ✗ Not matched (score < 0.6)")
                                else:
                                    # Fallback: just save link (no AI processing)
                                    try:
                                        job_key = None
                                        if 'jk=' in link:
                                            match = re.search(r'jk=([a-zA-Z0-9]+)', link)
                                            if match:
                                                job_key = match.group(1)
                                        saved = db.save_job_link(link, job_key, job, location, country, language)
                                        if saved:
                                            matched_count += 1
                                        else:
                                            skipped_count += 1
                                    except Exception as e:
                                        error_count += 1
                                        print(f"    ✗ Error: {e}")
                                
                                # Rate limiting for OpenAI API
                                if openai_client:
                                    time.sleep(1)
                            
                            total_matched = db.get_job_count()
                            print(f"[Page {page_num}] Matched: {matched_count}, Skipped: {skipped_count}, Errors: {error_count} (Total matched in DB: {total_matched})")
                        else:
                            # No jobs found on this page - debug why
                            empty_pages_count += 1
                            print(f"[Page {page_num}] No job links found on this page.")
                            
                            # Check if there are any job cards at all
                            try:
                                # Try multiple selectors to see what's on the page
                                job_cards_count_1 = len(page.query_selector_all('a.jcs-JobTitle'))
                                job_cards_count_2 = len(page.query_selector_all('a[data-jk]'))
                                job_cards_count_3 = len(page.query_selector_all('a[id^="job_"]'))
                                total_cards = max(job_cards_count_1, job_cards_count_2, job_cards_count_3)
                                
                                print(f"  Debug: Found {job_cards_count_1} cards with jcs-JobTitle, {job_cards_count_2} with data-jk, {job_cards_count_3} with id^='job_'")
                                
                                if total_cards == 0:
                                    print(f"[Page {page_num}] No job cards found - likely reached the end of results.")
                                    empty_pages_count = max_empty_pages  # Force stop
                                else:
                                    print(f"[Page {page_num}] Found {total_cards} job cards but couldn't extract links - may need more wait time")
                            except Exception as e:
                                print(f"  Debug error checking cards: {e}")
                            
                            # Stop if we've hit too many consecutive empty pages
                            if empty_pages_count >= max_empty_pages:
                                print(f"\nReached end of results: {max_empty_pages} consecutive pages with no jobs found.")
                                print("Stopping scrape.")
                                break
                                
                    except Exception as e:
                        print(f"[Page {page_num}] Error extracting jobs: {e}")
                        empty_pages_count += 1
                        if empty_pages_count >= max_empty_pages:
                            print("Too many errors, stopping scrape.")
                            break
                    
                    # Increment to next page (start parameter increases by 10)
                    start_index += 10
                    
                    # Randomized delay between pages
                    delay = 4 + random.uniform(1, 3)
                    time.sleep(delay)
                    
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user. Shutting down...")
                    shutdown_flag = True
                    break
                except Exception as e:
                    print(f"[Page {page_num}] Error visiting {url}: {e}")
                    empty_pages_count += 1
                    if empty_pages_count >= max_empty_pages:
                        print("Too many errors, stopping scrape.")
                        break
                    start_index += 10  # Continue to next page even on error
                    continue

            if not shutdown_flag:
                total_in_db = db.get_job_count()
                print(f"\nTotal matched jobs in database: {total_in_db}")
                print(f"Processing complete - only matched jobs (score >= 0.6) are saved")
                print(f"Database location: {os.path.abspath(db_path)}")
                print("\n\nJob processing completed!")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Shutting down...")
        except Exception as e:
            print(f"Fatal error: {e}")
        finally:
            try:
                page.close()
            except Exception:
                pass

except KeyboardInterrupt:
    print("\n\nInterrupted during browser initialization. Exiting...")
except Exception as e:
    print(f"Error initializing browser: {e}")
    sys.exit(1)