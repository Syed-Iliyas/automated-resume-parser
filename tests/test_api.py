"""End-to-end tests for the upload, listing, search and delete endpoints."""

import io

from docx import Document


def _make_docx(text: str) -> bytes:
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


RESUME = """Jane Doe
jane.doe@example.com | +1 (415) 555-0132
San Francisco, CA

SUMMARY
Machine learning engineer with 5 years of experience.

EDUCATION
M.S. Computer Science, Stanford University, 2019

SKILLS
Python, TensorFlow, Docker, AWS, SQL
"""


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_upload_and_list(client):
    response = client.post(
        "/api/resumes/upload",
        data={"files": (io.BytesIO(_make_docx(RESUME)), "jane.docx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    created = response.get_json()["created"]
    assert len(created) == 1
    assert created[0]["name"] == "Jane Doe"
    assert created[0]["email"] == "jane.doe@example.com"
    assert "Python" in created[0]["skills"]

    listed = client.get("/api/candidates").get_json()
    assert listed["total"] == 1
    assert listed["candidates"][0]["name"] == "Jane Doe"


def test_search_and_delete(client):
    client.post(
        "/api/resumes/upload",
        data={"files": (io.BytesIO(_make_docx(RESUME)), "jane.docx")},
        content_type="multipart/form-data",
    )

    by_skill = client.get("/api/candidates?skill=Docker").get_json()
    assert by_skill["total"] == 1

    by_text = client.get("/api/candidates?q=Stanford").get_json()
    assert by_text["total"] == 1

    skill_list = client.get("/api/skills").get_json()["skills"]
    assert any(s["name"] == "Python" for s in skill_list)

    candidate_id = by_skill["candidates"][0]["id"]
    detail = client.get(f"/api/candidates/{candidate_id}").get_json()
    assert "raw_text" in detail

    assert client.delete(f"/api/candidates/{candidate_id}").status_code == 200
    assert client.get("/api/candidates").get_json()["total"] == 0


def test_upload_rejects_bad_extension(client):
    response = client.post(
        "/api/resumes/upload",
        data={"files": (io.BytesIO(b"hello"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["errors"][0]["error"] == "Unsupported file type"
