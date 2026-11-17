"""REST API and UI routes."""

import os
from uuid import uuid4

from flask import Blueprint, abort, current_app, jsonify, render_template, request
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Candidate, Education, Skill
from ..parser import extract_text, parse_resume

api = Blueprint("api", __name__)


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def _get_or_create_skill(name: str) -> Skill:
    skill = Skill.query.filter_by(name=name).first()
    if skill is None:
        skill = Skill(name=name)
        db.session.add(skill)
        db.session.flush()
    return skill


def _save_candidate(data: dict) -> Candidate:
    candidate = Candidate(
        name=data["name"] or "Unknown",
        email=data.get("email"),
        phone=data.get("phone"),
        location=data.get("location"),
        summary=data.get("summary"),
        years_experience=data.get("years_experience"),
        filename=data.get("filename"),
        raw_text=data.get("raw_text"),
    )

    candidate.skills = [_get_or_create_skill(name) for name in data.get("skills", [])]

    for edu in data.get("education", []):
        candidate.education.append(
            Education(
                degree=edu.get("degree"),
                institution=edu.get("institution"),
                field_of_study=edu.get("field_of_study"),
                year=edu.get("year"),
            )
        )

    db.session.add(candidate)
    db.session.commit()
    return candidate


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/")
def index():
    return render_template("index.html")


@api.post("/api/resumes/upload")
def upload_resume():
    """Upload one or more resumes, parse them and store the results."""
    files = request.files.getlist("files") or request.files.getlist("file")
    files = [f for f in files if f and f.filename]

    if not files:
        return jsonify({"error": "No files provided. Send multipart field 'files'."}), 400

    created = []
    errors = []

    for file_storage in files:
        if not _allowed_file(file_storage.filename):
            errors.append({"file": file_storage.filename, "error": "Unsupported file type"})
            continue

        original_name = secure_filename(file_storage.filename)
        saved_path = None
        try:
            # Persist a copy for traceability (parsing itself uses the stream).
            upload_dir = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_dir, exist_ok=True)
            saved_path = os.path.join(upload_dir, f"{uuid4().hex}_{original_name}")
            file_storage.save(saved_path)
            file_storage.stream.seek(0)

            text = extract_text(file_storage)
            data = parse_resume(text, original_name)
            candidate = _save_candidate(data)
            created.append(candidate.to_dict())
        except Exception as exc:  # noqa: BLE001 - report per-file failures
            if saved_path and os.path.exists(saved_path):
                os.remove(saved_path)
            db.session.rollback()
            errors.append({"file": file_storage.filename, "error": str(exc)})

    status = 201 if created else 400
    return jsonify({"created": created, "errors": errors}), status


@api.get("/api/candidates")
def list_candidates():
    """List candidates with optional search, skill filter and pagination."""
    query = request.args.get("q", "").strip()
    skill_filter = request.args.get("skill", "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)

    stmt = Candidate.query

    if query:
        like = f"%{query}%"
        stmt = stmt.outerjoin(Candidate.education).outerjoin(Candidate.skills).filter(
            or_(
                Candidate.name.ilike(like),
                Candidate.email.ilike(like),
                Candidate.location.ilike(like),
                Candidate.raw_text.ilike(like),
                Skill.name.ilike(like),
                Education.institution.ilike(like),
                Education.degree.ilike(like),
            )
        ).distinct()

    if skill_filter:
        stmt = stmt.filter(Candidate.skills.any(Skill.name.ilike(skill_filter)))

    pagination = stmt.order_by(Candidate.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        {
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "candidates": [c.to_dict() for c in pagination.items],
        }
    )


@api.get("/api/candidates/<int:candidate_id>")
def get_candidate(candidate_id: int):
    candidate = db.session.get(Candidate, candidate_id) or abort(404)
    return jsonify(candidate.to_dict(include_raw=True))


@api.delete("/api/candidates/<int:candidate_id>")
def delete_candidate(candidate_id: int):
    candidate = db.session.get(Candidate, candidate_id) or abort(404)
    db.session.delete(candidate)
    db.session.commit()
    return jsonify({"deleted": candidate_id})


@api.get("/api/skills")
def list_skills():
    skills = Skill.query.order_by(Skill.name).all()
    return jsonify({"skills": [s.to_dict() for s in skills]})
