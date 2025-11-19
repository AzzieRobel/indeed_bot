import re
import time
import random
from typing import Dict, Any, List


def _clean_text_block(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def format_job_details_for_summary(
    details: Dict[str, Any], max_description_chars: int = 4000
) -> str:
    if not details:
        return ""

    parts: List[str] = []
    field_labels = [
        ("title", "Title"),
        ("company", "Company"),
        ("location", "Location"),
        ("job_type", "Job Type"),
        ("salary", "Salary"),
        ("posted_date", "Posted"),
    ]

    for field, label in field_labels:
        value = details.get(field)
        if value:
            parts.append(f"{label}: {value}")

    if details.get("details_list"):
        parts.append("Highlights: " + "; ".join(details["details_list"][:6]))

    description = details.get("description") or details.get("raw_text", "")
    description = description.strip()
    if description:
        clean_desc = re.sub(r"\s+", " ", description)
        if max_description_chars and len(clean_desc) > max_description_chars:
            clean_desc = clean_desc[:max_description_chars].rstrip() + "..."
        parts.append(f"Description: {clean_desc}")

    return "\n".join(parts).strip()

def click_and_wait(element, timeout=5):
    """Click element and wait with randomization."""
    if element:
        element.click()
        # Add randomization to avoid detection
        wait_time = timeout + random.uniform(-1, 1)
        time.sleep(max(0.5, wait_time))