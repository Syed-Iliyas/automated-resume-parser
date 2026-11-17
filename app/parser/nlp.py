"""NLP + regex based extraction of structured fields from resume text."""

import re
from functools import lru_cache

from .skills_data import SKILLS

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?)?\d{3,4}[\s.\-]?\d{4}")
# Phone regex is intentionally permissive; we filter by digit count below.

DEGREE_RE = re.compile(
    r"\b("
    r"Bachelor(?:'s)?|B\.?S\.?c?\.?|B\.?A\.?|B\.?Tech|B\.?E\.?"
    r"|Master(?:'s)?|M\.?S\.?c?\.?|M\.?A\.?|M\.?Tech|M\.?B\.?A\.?|MBA"
    r"|Ph\.?D\.?|Doctorate|Associate(?:'s)?| Diploma| HND"
    r")\b",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
EXPERIENCE_RE = re.compile(
    r"(\d{1,2}(?:\.\d)?)\+?\s*(?:\-|to)?\s*\d{0,2}\s*years?\s+(?:of\s+)?(?:professional\s+)?(?:work\s+)?experience",
    re.IGNORECASE,
)

LOC_KEYWORDS = {
    "united states", "usa", "canada", "united kingdom", "uk", "india", "australia",
    "germany", "france", "netherlands", "singapore", "uae", "pakistan", "bangladesh",
    "new york", "london", "san francisco", "toronto", "sydney", "dubai", "remote",
}


@lru_cache(maxsize=1)
def load_nlp():
    """Load the spaCy model lazily; return None if it is not installed."""
    try:
        import spacy

        return spacy.load("en_core_web_sm")
    except (ImportError, OSError):
        # Regex-based fallbacks still produce useful results without the model.
        return None


def clean_text(text: str) -> str:
    """Normalise whitespace while preserving line breaks."""
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_email(text: str) -> str | None:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    for match in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 7 <= len(digits) <= 15:
            return match.group(0).strip()
    return None


def extract_name(text: str, nlp=None) -> str:
    """Prefer the first PERSON entity near the top; fall back to first line."""
    nlp = nlp or load_nlp()
    if nlp is not None:
        head = "\n".join(text.splitlines()[:8])
        doc = nlp(head)
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 5:
                return ent.text.strip()

    for line in text.splitlines():
        line = line.strip(" :-•|")
        if not line:
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and all(re.match(r"^[A-Z][A-Za-z.'\-]*$", w) for w in words):
            return line
    return "Unknown"


def extract_skills(text: str) -> list[str]:
    """Match the curated skill catalogue against the text with word boundaries."""
    lowered = f" {text.lower()} "
    found: set[str] = set()

    for canonical, aliases in SKILLS.items():
        for alias in aliases:
            pattern = r"(?<![a-z0-9])" + re.escape(alias.strip()) + r"(?![a-z0-9])"
            if re.search(pattern, lowered):
                found.add(canonical)
                break

    return sorted(found)


def extract_education(text: str) -> list[dict]:
    """Find degree mentions and pair them with nearby institutions and years."""
    results: list[dict] = []
    seen: set[tuple] = set()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for index, line in enumerate(lines):
        if not DEGREE_RE.search(line):
            continue

        degree_match = DEGREE_RE.search(line)
        window = lines[max(0, index - 1): index + 3]
        institution = None
        field = None

        for neighbour in window:
            if neighbour == line:
                continue
            if institution is None and re.search(
                r"university|college|institute|school|academy|polytechnic",
                neighbour,
                re.IGNORECASE,
            ):
                institution = neighbour.strip(" ,|•-")

        # Field of study often appears after "in" on the same line.
        field_match = re.search(
            r"\bin\s+([A-Za-z][A-Za-z\s&]{2,60})",
            line,
            re.IGNORECASE,
        )
        if field_match:
            field = field_match.group(1).strip().rstrip(",")

        year_match = YEAR_RE.search(line) or YEAR_RE.search(" ".join(window))
        key = (degree_match.group(0).lower(), institution, year_match.group(0) if year_match else None)
        if key in seen:
            continue
        seen.add(key)

        results.append(
            {
                "degree": degree_match.group(0).strip(),
                "institution": institution,
                "field_of_study": field,
                "year": year_match.group(0) if year_match else None,
            }
        )

    return results


def extract_years_experience(text: str) -> float | None:
    match = EXPERIENCE_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def extract_location(text: str, nlp=None) -> str | None:
    """Look for a known city/country keyword, then fall back to spaCy GPE."""
    lowered = text.lower()
    for keyword in sorted(LOC_KEYWORDS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            return keyword.title()

    nlp = nlp or load_nlp()
    if nlp is not None:
        for ent in nlp("\n".join(text.splitlines()[:8])).ents:
            if ent.label_ in {"GPE", "LOC"}:
                return ent.text.strip()
    return None


def extract_summary(text: str) -> str | None:
    """Return the text under a SUMMARY/OBJECTIVE/PROFILE heading if present."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"\b(summary|objective|profile|about me)\b", line, re.IGNORECASE) and len(line) < 40:
            chunk: list[str] = []
            for following in lines[i + 1: i + 8]:
                if re.match(r"^[A-Z][A-Z /&]{3,}$", following.strip()) or not following.strip():
                    break
                chunk.append(following.strip())
            if chunk:
                return " ".join(chunk)[:600]
    return None


def parse_resume(text: str, filename: str | None = None) -> dict:
    """Parse raw resume text into the structured payload used by the API."""
    text = clean_text(text)
    nlp = load_nlp()

    return {
        "name": extract_name(text, nlp),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "location": extract_location(text, nlp),
        "summary": extract_summary(text),
        "years_experience": extract_years_experience(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "filename": filename,
        "raw_text": text,
    }
