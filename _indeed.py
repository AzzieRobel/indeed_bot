from datetime import datetime
import time
import random
import urllib.parse
from typing import Dict, Any, Optional, List

import _utils

try:
    from bs4 import BeautifulSoup
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print(
        "Warning: requests/BeautifulSoup not installed. Install with: pip install requests beautifulsoup4"
    )


class Indeed:
    
    def __init__(self) -> None:
        self.REQUEST_USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ]


    def _default_request_headers(self):
        return {
            "User-Agent": random.choice(self.REQUEST_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://www.indeed.com/",
        }

    @staticmethod
    def get_indeed_domain(country_code):
        if country_code == "us":
            return "www.indeed.com"
        else:
            return f"{country_code}.indeed.com"


    def normalize_job_link(self, job_link: str) -> str:
        if not job_link or "jk=" not in job_link:
            return job_link

        try:
            parsed = urllib.parse.urlparse(job_link)

            domain = parsed.netloc

            query_params = urllib.parse.parse_qs(parsed.query)
            jk_value = query_params.get("jk", [None])[0]

            if not jk_value:
                return job_link

            if (
                "/viewjob" in job_link
                and "from=serp" in job_link
                and "vjs=3" in job_link
            ):
                return job_link

            normalized_link = f"https://{domain}/viewjob?jk={jk_value}&from=serp&vjs=3"

            return normalized_link
        except Exception as e:
            print(f"Warning: Could not normalize job link: {e}")
            return job_link

    def scrape_job_details_from_link(
        self, job_link: str, REQUESTS_AVAILABLE, browser_page: Any = None, max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        if not job_link:
            return None

        html_content = None
        errors: List[str] = []

        if REQUESTS_AVAILABLE:
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        job_link, headers=self._default_request_headers(), timeout=20
                    )
                    if response.status_code == 200 and len(response.text) > 500:
                        html_content = response.text
                        break
                    errors.append(f"HTTP {response.status_code}")
                except Exception as exc:
                    errors.append(str(exc))
                    time.sleep(1 + attempt)

        if not html_content and browser_page is not None:
            try:
                browser_page.goto(job_link, wait_until="load", timeout=45000)
                time.sleep(2)
                html_content = browser_page.content()
            except Exception as exc:
                errors.append(str(exc))

        if not html_content:
            reason = errors[0] if errors else "no response"
            print(f"  ✗ Unable to fetch job page: {job_link[:90]}... ({reason})")
            return None

        if not REQUESTS_AVAILABLE:
            print("  ✗ requests/BeautifulSoup not available; cannot parse job page.")
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "aside"]):
            tag.decompose()

        def pick_text(selectors: List[str]) -> str:
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(" ", strip=True)
                    if text:
                        return _utils.clean_text_block(text)
            return ""

        title = pick_text(
            [
                "h1.jobsearch-JobInfoHeader-title",
                'h1[data-testid="job-title"]',
                "div.jobsearch-JobInfoHeader-title-container h1",
                "h1 span",
                "h1",
            ]
        )

        company = pick_text(
            [
                'div[data-testid="inlineCompanyName"]',
                'a[data-testid="company-name"]',
                'div[data-company-name="true"]',
                "span.companyName",
                "div.jobsearch-InlineCompanyRating div:first-child",
            ]
        )

        location_text = pick_text(
            [
                'div[data-testid="inlineCompanyLocation"]',
                'div[data-testid="job-location"]',
                'div[data-testid="inlineCompanyHeading"] span',
                "div.companyLocation",
                "div.jobsearch-CompanyInfoWithoutHeaderImage div",
            ]
        )

        description_element = None
        for selector in [
            'div[id="jobDescriptionText"]',
            'div[data-testid="jobDescriptionText"]',
            "div.jobsearch-jobDescriptionText",
            'div[data-tn-component="jobDescription"]',
        ]:
            description_element = soup.select_one(selector)
            if description_element:
                break
        description_text = ""
        if description_element:
            description_text = "\n".join(
                [line.strip() for line in description_element.stripped_strings]
            )
        else:
            body = soup.body
            if body:
                description_text = body.get_text(" ", strip=True)

        description_text = description_text[:10000] if description_text else ""
        description_text = _utils.clean_text_block(description_text)

        detail_list = [
            item.get_text(" ", strip=True)
            for item in soup.select('div[data-testid="jobDetailsSection"] li')
        ]
        detail_list = [_utils.clean_text_block(item) for item in detail_list if item]

        salary = ""
        job_type = ""
        for detail in detail_list:
            lower_detail = detail.lower()
            if any(currency in detail for currency in ["$", "€", "£"]) and not salary:
                salary = detail
            if (
                any(
                    key in lower_detail
                    for key in [
                        "full-time",
                        "part-time",
                        "contract",
                        "internship",
                        "remote",
                        "temporary",
                    ]
                )
                and not job_type
            ):
                job_type = detail

        posted_date = pick_text(
            [
                'div[data-testid="myJobsStateDate"]',
                'span[data-testid="myJobsStateDate"]',
                "span.jobsearch-HiringInsights-entry--text",
                "div.jobsearch-JobMetadataFooter",
            ]
        )

        raw_text = soup.get_text(" ", strip=True)
        raw_text = raw_text[:12000] if raw_text else ""

        job_details = {
            "job_link": job_link,
            "title": title,
            "company": company,
            "location": location_text,
            "salary": salary,
            "job_type": job_type,
            "posted_date": posted_date,
            "description": description_text,
            "details_list": detail_list,
            "raw_text": self.clean_text_block(raw_text),
            "scraped_at": datetime.now().isoformat(),
        }

        return job_details


    def scrape_job_details_from_dom(
        self,
        page: Any,
        job_key: Optional[str],
        job_link: str,
        country: str,
        wait_timeout: int = 8000,
    ) -> Optional[Dict[str, Any]]:
        if not page or not job_key:
            return None

        selectors = [
            f'a[data-jk="{job_key}"]',
            f'a[id="job_{job_key}"]',
            f'a[href*="jk={job_key}"]',
            f'li[data-jk="{job_key}"] a',
        ]

        card = None
        for selector in selectors:
            try:
                card = page.query_selector(selector)
                if card:
                    break
            except Exception:
                continue

        if not card:
            return None

        try:
            card.scroll_into_view_if_needed()
        except Exception:
            pass

        try:
            card.click()
        except Exception:
            return None

        try:
            page.wait_for_selector(
                "div.fastviewjob.jobsearch-ViewJobLayout--embedded, div.fastviewjob, div#jobDescriptionText",
                timeout=wait_timeout,
            )
        except Exception:
            time.sleep(2)

        details = self.extract_job_details(page, card, job_link, country)
        if details and (
            details.get("description") or details.get("title") or details.get("company")
        ):
            return details

        return None


    def extract_job_details(self, page, card, job_url, country):
        job_details = {
            "url": job_url,
            "title": "",
            "company": "",
            "location": "",
            "salary": "",
            "job_type": "",
            "description": "",
            "posted_date": "",
            "has_apply_now": False,
            "links": {
                "job_url": job_url,
                "company_website": "",
                "apply_link": "",
                "company_profile": "",
                "all_links": [],
            },
            "scraped_at": datetime.now().isoformat(),
        }

        try:
            detail_container = None
            detail_selectors = [
                "div.fastviewjob.jobsearch-ViewJobLayout--embedded",
                "div.fastviewjob",
                "div.jobsearch-ViewJobLayout--embedded",
                'div[class*="jobsearch-ViewJobLayout"]',
                'div[data-testid="jobsearch-ViewJobHeader"]',
            ]
            for selector in detail_selectors:
                detail_container = page.query_selector(selector)
                if detail_container:
                    break

            query_target = detail_container if detail_container else page

            time.sleep(0.5 + random.uniform(0, 0.3))

            try:
                title_elem = query_target.query_selector(
                    'h1.jobsearch-JobInfoHeader-title, h1[data-testid="job-title"], h2.jobTitle, h2[class*="jobTitle"], h2[data-testid="job-title"]'
                )
                if not title_elem:
                    title_elem = query_target.query_selector("h2, h1")
                if title_elem:
                    job_details["title"] = title_elem.inner_text().strip()
            except Exception:
                pass

            try:
                company_elem = query_target.query_selector(
                    '[data-testid="company-name"], div[data-testid="inlineCompanyName"], span.companyName, a[data-testid="company-name"]'
                )
                if not company_elem:
                    company_elem = query_target.query_selector(
                        'span[class*="company"], a[class*="company"]'
                    )
                if company_elem:
                    job_details["company"] = company_elem.inner_text().strip()
            except Exception:
                pass

            try:
                location_elem = query_target.query_selector(
                    '[data-testid="job-location"], div[data-testid="inlineCompanyLocation"], span[class*="location"], div[class*="companyLocation"]'
                )
                if location_elem:
                    job_details["location"] = location_elem.inner_text().strip()
            except Exception:
                pass

            try:
                salary_elem = query_target.query_selector(
                    '[data-testid="attribute_snippet_testid"], span[class*="salary"], div[class*="salary"]'
                )
                if not salary_elem:
                    salary_elem = query_target.query_selector(
                        'span:has-text("$"), div:has-text("$")'
                    )
                if salary_elem:
                    salary_text = salary_elem.inner_text().strip()
                    if "$" in salary_text or "€" in salary_text or "£" in salary_text:
                        job_details["salary"] = salary_text
            except Exception:
                pass

            try:
                job_type_elems = query_target.query_selector_all(
                    '[data-testid="attribute_snippet_testid"], span[class*="jobType"]'
                )
                for elem in job_type_elems:
                    text = elem.inner_text().lower()
                    if any(
                        t in text
                        for t in [
                            "full-time",
                            "part-time",
                            "contract",
                            "temporary",
                            "permanent",
                            "remote",
                        ]
                    ):
                        job_details["job_type"] = elem.inner_text().strip()
                        break
            except Exception:
                pass

            try:
                desc_elem = query_target.query_selector(
                    '[data-testid="job-description"], div[class*="jobDescription"], div[id*="jobDescriptionText"], div#jobDescriptionText'
                )
                if not desc_elem:
                    desc_elem = query_target.query_selector(
                        'div[class*="description"], div[id*="description"]'
                    )
                if desc_elem:
                    job_details["description"] = desc_elem.inner_text().strip()[
                        :1000
                    ]
            except Exception:
                pass

            try:
                date_elem = query_target.query_selector(
                    '[data-testid="myJobsStateDate"], span[class*="date"], span[class*="posted"], div.jobsearch-JobMetadataFooter'
                )
                if not date_elem:
                    date_elem = query_target.query_selector(
                        'span:has-text("ago"), span:has-text("days")'
                    )
                if date_elem:
                    job_details["posted_date"] = date_elem.inner_text().strip()
            except Exception:
                pass

            try:
                apply_now = query_target.query_selector(
                    'button:visible:has-text("Apply now"), button:visible:has-text("Apply Now"), [data-testid="indeedApply"]'
                )
                if apply_now:
                    job_details["has_apply_now"] = True
                    try:
                        apply_href = apply_now.get_attribute("href")
                        if apply_href:
                            if not apply_href.startswith("http"):
                                domain = self.get_indeed_domain(country)
                                apply_href = f"https://{domain}{apply_href}"
                            job_details["links"]["apply_link"] = apply_href
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                all_links = query_target.query_selector_all("a[href]")
                extracted_links = []

                for link_elem in all_links:
                    try:
                        href = link_elem.get_attribute("href")
                        link_text = link_elem.inner_text().strip()

                        if href:
                            if href.startswith("/"):
                                domain = self.get_indeed_domain(country)
                                href = f"https://{domain}{href}"
                            elif not href.startswith("http"):
                                domain = self.get_indeed_domain(country)
                                href = f"https://{domain}{href}"

                            link_info = {
                                "url": href,
                                "text": (
                                    link_text[:100] if link_text else ""
                                ),
                                "type": "unknown",
                            }

                            href_lower = href.lower()
                            text_lower = (link_text or "").lower()

                            if (
                                "company" in text_lower
                                or "website" in text_lower
                                or "company" in href_lower
                            ):
                                link_info["type"] = "company_website"
                                if not job_details["links"]["company_website"]:
                                    job_details["links"]["company_website"] = href
                            elif (
                                "apply" in text_lower
                                or "apply" in href_lower
                                or "indeed.com/apply" in href_lower
                            ):
                                link_info["type"] = "apply"
                                if not job_details["links"]["apply_link"]:
                                    job_details["links"]["apply_link"] = href
                            elif (
                                "viewjob" in href_lower or "/jobs/viewjob" in href_lower
                            ):
                                link_info["type"] = "job_posting"
                            elif (
                                "company" in href_lower and "reviews" not in href_lower
                            ):
                                link_info["type"] = "company_profile"
                                if not job_details["links"]["company_profile"]:
                                    job_details["links"]["company_profile"] = href
                            elif "indeed.com" not in href_lower:
                                link_info["type"] = "external"

                            extracted_links.append(link_info)
                    except Exception:
                        continue

                job_details["links"]["all_links"] = extracted_links

            except Exception:
                pass

        except Exception as e:
            pass

        return job_details
