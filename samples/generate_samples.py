"""Generate realistic sample resumes as DOCX and PDF for testing the parser.

Run: python samples/generate_samples.py
"""

from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT_DIR = Path(r"C:\Users\Ilyas\Desktop\sample_resumes")

RESUMES = [
    {
        "filename": "jane_doe_ml_engineer",
        "lines": [
            "Jane Doe",
            "jane.doe@example.com | +1 (415) 555-0132",
            "San Francisco, CA, United States",
            "",
            "SUMMARY",
            "Machine learning engineer with 5 years of experience building and deploying "
            "production models. Strong background in Python, deep learning and cloud infrastructure.",
            "",
            "EDUCATION",
            "M.S. Computer Science, Stanford University, 2019",
            "Bachelor of Science in Electrical Engineering, MIT, 2015",
            "",
            "SKILLS",
            "Python, TensorFlow, PyTorch, Machine Learning, NLP, Docker, Kubernetes, AWS, SQL, Spark",
            "",
            "EXPERIENCE",
            "Machine Learning Engineer, TechCorp (2019 - Present)",
            "Built recommendation systems and MLOps pipelines serving millions of users.",
            "Data Scientist, DataWorks (2015 - 2019)",
            " Developed predictive models using scikit-learn and pandas.",
        ],
    },
    {
        "filename": "john_smith_fullstack",
        "lines": [
            "John Smith",
            "john.smith@email.com | +44 20 7946 0958",
            "London, United Kingdom",
            "",
            "SUMMARY",
            "Full stack developer with 3 years of experience delivering web applications "
            "using React, Node.js and PostgreSQL. Agile and CI/CD practitioner.",
            "",
            "EDUCATION",
            "Bachelor of Science in Computer Science, University of Manchester, 2020",
            "",
            "SKILLS",
            "JavaScript, TypeScript, React, Node.js, HTML, CSS, PostgreSQL, REST APIs, "
            "Docker, Git, CI/CD, Agile",
            "",
            "EXPERIENCE",
            "Frontend Developer, Webify Ltd (2021 - Present)",
            "Built responsive interfaces with React and TypeScript.",
            "Junior Developer, CodeHub (2020 - 2021)",
            " Developed REST APIs with Node.js and PostgreSQL.",
        ],
    },
    {
        "filename": "aisha_khan_data_analyst",
        "lines": [
            "Aisha Khan",
            "aisha.khan@example.com | +1 (416) 555-0177",
            "Toronto, Canada",
            "",
            "SUMMARY",
            "Data analyst with 7 years of experience turning raw data into business insights. "
            "Expert in SQL, Python, data visualization and Excel.",
            "",
            "EDUCATION",
            "Master of Science in Statistics, University of Toronto, 2016",
            "Bachelor of Arts in Economics, York University, 2013",
            "",
            "SKILLS",
            "Python, SQL, Pandas, NumPy, Data Analysis, Data Visualization, Tableau, "
            "Power BI, Excel, ETL, AWS",
            "",
            "EXPERIENCE",
            "Senior Data Analyst, Insights Inc (2018 - Present)",
            "Led reporting and dashboard projects for retail clients.",
            "Data Analyst, Analytics Co (2016 - 2018)",
            " Automated ETL pipelines and built Tableau dashboards.",
        ],
    },
    {
        "filename": "michael_chen_cloud_devops",
        "lines": [
            "Michael Chen",
            "michael.chen@example.com | +1 (206) 555-0143",
            "Seattle, United States",
            "",
            "SUMMARY",
            "DevOps engineer with 6 years of experience in cloud infrastructure, Kubernetes "
            "and automation. Passionate about Linux, Docker and CI/CD pipelines.",
            "",
            "EDUCATION",
            "Bachelor of Technology in Information Technology, University of Washington, 2017",
            "",
            "SKILLS",
            "AWS, Azure, Docker, Kubernetes, Linux, Bash, Python, Terraform, Jenkins, "
            "CI/CD, Git, Microservices, Cybersecurity",
            "",
            "EXPERIENCE",
            "Cloud Engineer, CloudScale (2019 - Present)",
            "Managed Kubernetes clusters and Terraform-based infrastructure.",
            "Systems Administrator, NetOps (2017 - 2019)",
            " Automated deployments with Jenkins and shell scripting.",
        ],
    },
]


def make_docx(resume: dict, path: Path) -> None:
    doc = Document()
    for index, line in enumerate(resume["lines"]):
        paragraph = doc.add_paragraph()
        run = paragraph.add_run(line)
        if index == 0:
            run.bold = True
            run.font.size = Pt(18)
        elif line.isupper() and 0 < len(line) < 40:
            run.bold = True
            run.font.size = Pt(12)
    doc.save(path)


def make_pdf(resume: dict, path: Path) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )
    story = []
    for index, line in enumerate(resume["lines"]):
        if not line:
            story.append(Spacer(1, 8))
            continue
        if index == 0:
            style = ParagraphStyle("name", fontSize=18, leading=22, spaceAfter=10)
            text = f"<b>{escape(line)}</b>"
        elif line.isupper() and len(line) < 40:
            style = ParagraphStyle(
                "heading", fontSize=12, leading=16, spaceBefore=10, spaceAfter=4
            )
            text = f"<b>{escape(line)}</b>"
        else:
            style = ParagraphStyle("body", fontSize=10, leading=14, spaceAfter=2)
            text = escape(line)
        story.append(Paragraph(text, style))
    doc.build(story)


if __name__ == "__main__":
    for resume in RESUMES:
        make_docx(resume, OUT_DIR / f"{resume['filename']}.docx")
        make_pdf(resume, OUT_DIR / f"{resume['filename']}.pdf")
    print(f"Generated {len(RESUMES) * 2} sample resumes in {OUT_DIR}")
