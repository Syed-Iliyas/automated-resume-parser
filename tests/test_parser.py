"""Fast unit tests for the regex-based extraction (no spaCy model required)."""

from app.parser.nlp import (
    extract_education,
    extract_email,
    extract_phone,
    extract_skills,
    extract_years_experience,
    parse_resume,
)

SAMPLE = """Jane Doe
jane.doe@example.com | +1 (415) 555-0132
San Francisco, CA

SUMMARY
Machine learning engineer with 5 years of experience.

EDUCATION
M.S. Computer Science, Stanford University, 2019
Bachelor of Science in Electrical Engineering, MIT, 2015

SKILLS
Python, TensorFlow, Docker, AWS, SQL
"""


def test_email():
    assert extract_email(SAMPLE) == "jane.doe@example.com"


def test_phone():
    assert extract_phone(SAMPLE) is not None


def test_skills():
    skills = extract_skills(SAMPLE)
    assert {"Python", "Machine Learning", "Deep Learning", "Docker", "AWS", "SQL"} <= set(skills)


def test_education():
    edu = extract_education(SAMPLE)
    assert len(edu) >= 2
    assert any("Stanford" in (e["institution"] or "") for e in edu)


def test_years_experience():
    assert extract_years_experience(SAMPLE) == 5.0


def test_parse_resume_full():
    data = parse_resume(SAMPLE, "jane.pdf")
    assert data["filename"] == "jane.pdf"
    assert data["email"] == "jane.doe@example.com"
    assert data["skills"]
    assert data["education"]
