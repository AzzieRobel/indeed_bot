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
from typing import Dict, Any, Optional, List, Tuple
from camoufox.sync_api import Camoufox
from dotenv import load_dotenv

load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

from _database import Database
from _indeed import Indeed, REQUESTS_AVAILABLE
from _open_ai import OpenAI_Manager
import _utils


camoufox_config = config.get("camoufox", {})
user_data_dir = camoufox_config.get("user_data_dir")
search_config = config.get("search", {})
country = search_config.get("country", "us")
language = search_config.get("language", "us")
openAI_api_key = os.getenv("OPENAI_API_KEY")

db = Database("indeed_jobs.db")
indeed = Indeed()
openAI_manager = OpenAI_Manager(openAI_api_key)


def collect_job_links(page, country):
    job_links = []

    try:
        page.wait_for_selector('a.jcs-JobTitle, a[jk], a[id^="job_"]', timeout=15000)
    except Exception:
        try:
            page.wait_for_selector('a[class*="JobTitle"]', timeout=5000)
        except Exception:
            pass

    time.sleep(2 + random.uniform(0.5, 1))

    job_cards = []

    job_cards = page.query_selector_all("a.jcs-JobTitle")

    if not job_cards:
        job_cards = page.query_selector_all("a[jk]")

    if not job_cards:
        job_cards = page.query_selector_all('a[id^="job_"]')

    domain = indeed.get_indeed_domain(country)

    print(f"Found {len(job_cards)} job cards (expected ~15 per page)")

    for idx, card in enumerate(job_cards):
        try:
            job_key = None
            try:
                job_key = card.get_attribute("jk")
            except Exception:
                pass

            if not job_key:
                try:
                    card_id = card.get_attribute("id")
                    if card_id and card_id.startswith("job_"):
                        job_key = card_id.replace("job_", "")
                except Exception:
                    pass

            if not job_key:
                try:
                    href = card.get_attribute("href")
                    if href and "jk=" in href:
                        match = re.search(r"jk=([a-zA-Z0-9]+)", href)
                        if match:
                            job_key = match.group(1)
                except Exception:
                    pass

            if job_key:
                viewjob_url = f"https://{domain}/viewjob?jk={job_key}&from=serp&vjs=3"
                job_links.append(viewjob_url)
                print(f"  [Card {idx+1}/{len(job_cards)}] Link: {viewjob_url[:80]}...")
            else:
                print(
                    f"  [Card {idx+1}/{len(job_cards)}] Warning: Could not extract job key"
                )
        except Exception as e:
            print(f"  [Card {idx+1}] Error: {e}")
            continue

    return job_links


def process_job_for_matching(
    job_link: str,
    openai_client: Any,
    user_profile: Dict[str, Any],
    user_profile_embedding: Optional[List[float]],
    browser_page: Optional[Any] = None,
    search_query: str = None,
    min_score: float = 0.6,
) -> Optional[Dict[str, Any]]:
    if not openai_client or not user_profile:
        return None

    try:
        normalized_link = indeed.normalize_job_link(job_link)

        job_key = None
        if "jk=" in normalized_link:
            try:
                match = re.search(r"jk=([a-zA-Z0-9]+)", normalized_link)
                if match:
                    job_key = match.group(1)
            except Exception:
                pass

        job_details = None
        if browser_page and job_key:
            job_details = indeed.scrape_job_details_from_dom(
                browser_page, job_key, normalized_link, country or ""
            )

        if not job_details:
            job_details = indeed.scrape_job_details_from_link(
                normalized_link, REQUESTS_AVAILABLE
            )
        if not job_details:
            return None

        job_summary = openAI_manager.extract_job_summary_with_openai(job_details, openai_client)
        if not job_summary:
            return None

        job_embedding_list = None
        job_embedding_json = None
        if openai_client:
            job_embedding_list = openAI_manager.get_embedding(
                job_summary, openai_client
            )
            if job_embedding_list:
                job_embedding_json = json.dumps(job_embedding_list)

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
    min_score: float = 0.6,
) -> bool:
    job_data = process_job_for_matching(
        job_link,
        openai_client,
        user_profile,
        user_profile_embedding,
        browser_page=browser_page,
        search_query=search_query,
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
# AI Matching Functions
# ============================================================================


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def keyword_score(job_summary: str, user_profile: Dict[str, Any]) -> Dict[str, float]:
    if not job_summary:
        return {"relevance": 0.0, "location": 0.0, "role_type": 0.0, "experience": 0.0}

    summary_lower = job_summary.lower()
    scores = {"relevance": 0.0, "location": 0.0, "role_type": 0.0, "experience": 0.0}

    technical_skills = user_profile.get("technical_skills", [])
    soft_skills = user_profile.get("soft_skills", [])
    desired_skills = technical_skills + soft_skills

    work_experience = user_profile.get("work_experience", [])
    for exp in work_experience:
        if exp.get("title"):
            title_words = exp["title"].split()
            desired_skills.extend([w for w in title_words if len(w) > 3])

    if desired_skills:
        matched_skills = sum(
            1 for skill in desired_skills if skill.lower() in summary_lower
        )
        scores["relevance"] = min(1.0, matched_skills / max(len(desired_skills), 1))

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
            scores["location"] = 0.3

    preferred_types = job_prefs.get("preferred_job_types", ["full-time"])
    job_type_match = any(jt.lower() in summary_lower for jt in preferred_types)
    if job_type_match:
        scores["role_type"] = 1.0
    else:
        scores["role_type"] = 0.5

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
    print(f"user profile : ", user_profile)
    print(f"job summary : ", job_summary)
    if weights is None:
        weights = {
            "embedding": 0.4,
            "relevance": 0.3,
            "location": 0.15,
            "role_type": 0.1,
            "experience": 0.05,
        }

    embedding_score = 0.0
    if job_embedding and user_profile_embedding:
        embedding_score = cosine_similarity(job_embedding, user_profile_embedding)

    keyword_scores = keyword_score(job_summary, user_profile)

    final_score = (
        embedding_score * weights["embedding"]
        + keyword_scores["relevance"] * weights["relevance"]
        + keyword_scores["location"] * weights["location"]
        + keyword_scores["role_type"] * weights["role_type"]
        + keyword_scores["experience"] * weights["experience"]
    )

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


def check_login_status(page):
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
    print("Token not found, please log in to Indeed first.")
    print("Redirecting to login page...")
    print("You need to restart the bot after logging in.")
    print("Press Ctrl+C to exit after logging in.")

    try:
        page.goto(f"https://secure.indeed.com/auth?hl={language}")
        page.wait_for_load_state("domcontentloaded")

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


shutdown_flag = False


def signal_handler(sig, frame):
    global shutdown_flag
    shutdown_flag = True
    print("\n\nShutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

try:
    with Camoufox(
        user_data_dir=user_data_dir,
        persistent_context=True,
        proxy={
            "server": "http://ca.proxy-jet.io:1010",
            "username": "251113n8NQc-resi_region-US_Newyork_Newyork",
            "password": "Vqo54K6NsgV3cKY",
        },
    ) as browser:
        page = browser.new_page()

        try:
            indeed_domain = indeed.get_indeed_domain(country)
            page.goto(f"https://{indeed_domain}")
            page.wait_for_load_state("domcontentloaded")

            if not check_login_status(page):
                wait_for_manual_login(page, language, country)
                page.close()
                sys.exit(0)

            print("Token found, proceeding with job search...")

            db_path = db.init_database()
            print(f"Database initialized: {db_path}")

            openai_client = openAI_manager.get_openai_client()
            if not openai_client:
                print(
                    "Warning: OpenAI client not available. Jobs will be saved but not processed immediately."
                )
                print(
                    "You can process them later using: python process_jobs.py --extract-summaries --match"
                )
                user_profile = None
                user_profile_embedding = None
            else:
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

                user_profile_embedding = None
                if user_profile and openai_client:
                    profile_parts = []
                    if user_profile.get("professional_summary"):
                        profile_parts.append(user_profile["professional_summary"])
                    job_prefs = user_profile.get("job_preferences", {})
                    if job_prefs.get("desired_role"):
                        profile_parts.append(
                            f"Desired role: {job_prefs['desired_role']}"
                        )
                    work_experience = user_profile.get("work_experience", [])
                    for exp in work_experience:
                        exp_text = f"{exp.get('title', '')} at {exp.get('company', '')}: {exp.get('description', '')}"
                        profile_parts.append(exp_text)
                    technical_skills = user_profile.get("technical_skills", [])
                    soft_skills = user_profile.get("soft_skills", [])
                    if technical_skills:
                        profile_parts.append(
                            f"Technical skills: {', '.join(technical_skills)}"
                        )
                    if soft_skills:
                        profile_parts.append(f"Soft skills: {', '.join(soft_skills)}")
                    education = user_profile.get("education", [])
                    for edu in education:
                        edu_text = (
                            f"{edu.get('degree', '')} from {edu.get('institution', '')}"
                        )
                        profile_parts.append(edu_text)
                    profile_text = " ".join(profile_parts)
                    if profile_text:
                        print("Generating user profile embedding...")
                        user_profile_embedding = openAI_manager.get_embedding(
                            profile_text, openai_client
                        )
                        print("User profile embedding ready.")

                if user_profile:
                    print(
                        f"User profile loaded. Processing jobs immediately with AI matching..."
                    )
                else:
                    print(
                        "Warning: No user profile found. Jobs will be saved but not matched."
                    )

            job = search_config.get("job", "")
            location = search_config.get("location", "")

            if not job:
                print("Error: 'job' field is required in config.yaml")
                sys.exit(1)

            base_domain = indeed.get_indeed_domain(country)

            params = {"q": job}

            if location:
                params["l"] = location

            query_string = urllib.parse.urlencode(params)
            base_url = f"https://{base_domain}/jobs?{query_string}"

            print(f"Search Configuration:")
            print(f"  Job: {job}")
            print(f"  Location: {location if location else 'Any location'}")
            print(f"  Country: {country}")
            print(f"  Language: {language}")
            print(f"  Base URL: {base_url}")
            print()

            start_index = 0
            empty_pages_count = 0
            max_empty_pages = 2
            max_pages = 1000

            print("Starting to process jobs with AI...")
            print(
                "Each job will be: normalized → extract summary → match → save if matched"
            )
            print("(Pages are paginated by increments of 10: start=0, 10, 20, 30, ...)")
            print()

            while start_index < max_pages * 10:
                if shutdown_flag:
                    break

                if start_index == 0:
                    url = base_url
                else:
                    separator = "&" if "?" in base_url else "?"
                    url = f"{base_url}{separator}start={start_index}"
                page_num = (start_index // 10) + 1

                try:
                    print(f"[Page {page_num}] Visiting URL: {url}")
                    page.goto(url, wait_until="load", timeout=60000)

                    print("Waiting for page to fully load...")
                    try:
                        page.wait_for_selector(
                            "a.jcs-JobTitle, a[data-jk], div#jobsearch",
                            timeout=30000,
                            state="visible",
                        )
                    except Exception:
                        print(
                            "Cloudflare protection detected, waiting for manual interaction if needed..."
                        )
                        time.sleep(5)

                    wait_time = 6 + random.uniform(2, 4)
                    time.sleep(wait_time)

                    try:
                        page.wait_for_selector(
                            'a.jcs-JobTitle, a[data-jk], a[id^="job_"]', timeout=15000
                        )
                        print("Job cards detected on page")
                    except Exception:
                        print(
                            "Warning: Job listings may not have loaded yet, trying anyway..."
                        )
                        time.sleep(3)

                    try:
                        current_url = page.url
                        print(
                            f"[Page {page_num}] Current page URL: {current_url[:100]}..."
                        )

                        job_links = collect_job_links(page, country)

                        if job_links:
                            empty_pages_count = 0

                            matched_count = 0
                            skipped_count = 0
                            error_count = 0

                            for i, link in enumerate(job_links, 1):
                                print(
                                    f"  [{i}/{len(job_links)}] Processing: {link[:60]}..."
                                )

                                if openai_client and user_profile:
                                    matched = process_and_save_job_immediately(
                                        link,
                                        openai_client,
                                        user_profile,
                                        user_profile_embedding,
                                        page,
                                        job,
                                    )
                                    if matched:
                                        matched_count += 1
                                        print(f"    ✓ Matched and saved")
                                    else:
                                        skipped_count += 1
                                        print(f"    ✗ Not matched (score < 0.6)")
                                else:
                                    try:
                                        job_key = None
                                        if "jk=" in link:
                                            match = re.search(
                                                r"jk=([a-zA-Z0-9]+)", link
                                            )
                                            if match:
                                                job_key = match.group(1)
                                        saved = db.save_job_link(
                                            link,
                                            job_key,
                                            job,
                                            location,
                                            country,
                                            language,
                                        )
                                        if saved:
                                            matched_count += 1
                                        else:
                                            skipped_count += 1
                                    except Exception as e:
                                        error_count += 1
                                        print(f"    ✗ Error: {e}")

                                if openai_client:
                                    time.sleep(1)

                            total_matched = db.get_job_count()
                            print(
                                f"[Page {page_num}] Matched: {matched_count}, Skipped: {skipped_count}, Errors: {error_count} (Total matched in DB: {total_matched})"
                            )
                        else:
                            empty_pages_count += 1
                            print(f"[Page {page_num}] No job links found on this page.")

                            try:
                                job_cards_count_1 = len(
                                    page.query_selector_all("a.jcs-JobTitle")
                                )
                                job_cards_count_2 = len(
                                    page.query_selector_all("a[data-jk]")
                                )
                                job_cards_count_3 = len(
                                    page.query_selector_all('a[id^="job_"]')
                                )
                                total_cards = max(
                                    job_cards_count_1,
                                    job_cards_count_2,
                                    job_cards_count_3,
                                )

                                print(
                                    f"  Debug: Found {job_cards_count_1} cards with jcs-JobTitle, {job_cards_count_2} with data-jk, {job_cards_count_3} with id^='job_'"
                                )

                                if total_cards == 0:
                                    print(
                                        f"[Page {page_num}] No job cards found - likely reached the end of results."
                                    )
                                    empty_pages_count = max_empty_pages
                                else:
                                    print(
                                        f"[Page {page_num}] Found {total_cards} job cards but couldn't extract links - may need more wait time"
                                    )
                            except Exception as e:
                                print(f"  Debug error checking cards: {e}")

                            if empty_pages_count >= max_empty_pages:
                                print(
                                    f"\nReached end of results: {max_empty_pages} consecutive pages with no jobs found."
                                )
                                print("Stopping scrape.")
                                break

                    except Exception as e:
                        print(f"[Page {page_num}] Error extracting jobs: {e}")
                        empty_pages_count += 1
                        if empty_pages_count >= max_empty_pages:
                            print("Too many errors, stopping scrape.")
                            break

                    start_index += 10

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
                    start_index += 10
                    continue

            if not shutdown_flag:
                total_in_db = db.get_job_count()
                print(f"\nTotal matched jobs in database: {total_in_db}")
                print(
                    f"Processing complete - only matched jobs (score >= 0.6) are saved"
                )
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
