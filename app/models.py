"""Database models for parsed candidates, skills and education."""

from datetime import datetime, timezone

from .extensions import db

# Many-to-many link between candidates and skills.
candidate_skills = db.Table(
    "candidate_skills",
    db.Column(
        "candidate_id",
        db.Integer,
        db.ForeignKey("candidate.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "skill_id",
        db.Integer,
        db.ForeignKey("skill.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Candidate(db.Model):
    __tablename__ = "candidate"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(200), index=True)
    phone = db.Column(db.String(50))
    location = db.Column(db.String(200))
    summary = db.Column(db.Text)
    years_experience = db.Column(db.Float)
    filename = db.Column(db.String(300))
    raw_text = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    skills = db.relationship(
        "Skill",
        secondary=candidate_skills,
        back_populates="candidates",
        lazy="selectin",
    )
    education = db.relationship(
        "Education",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self, include_raw: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "summary": self.summary,
            "years_experience": self.years_experience,
            "filename": self.filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "skills": [skill.name for skill in self.skills],
            "education": [edu.to_dict() for edu in self.education],
        }
        if include_raw:
            data["raw_text"] = self.raw_text
        return data


class Skill(db.Model):
    __tablename__ = "skill"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)

    candidates = db.relationship(
        "Candidate",
        secondary=candidate_skills,
        back_populates="skills",
    )

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


class Education(db.Model):
    __tablename__ = "education"

    id = db.Column(db.Integer, primary_key=True)
    degree = db.Column(db.String(200))
    institution = db.Column(db.String(200))
    field_of_study = db.Column(db.String(200))
    year = db.Column(db.String(20))
    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=False,
    )

    candidate = db.relationship("Candidate", back_populates="education")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "degree": self.degree,
            "institution": self.institution,
            "field_of_study": self.field_of_study,
            "year": self.year,
        }
