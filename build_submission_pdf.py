from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT_PATH = Path(__file__).resolve().parent / "BrandLens_Round2_Submission.pdf"
INK = colors.HexColor("#1A3032")
TEAL = colors.HexColor("#27604F")
MINT = colors.HexColor("#BCE2CF")
BODY = colors.HexColor("#465559")
MUTED = colors.HexColor("#77868A")
LINE = colors.HexColor("#E3EAE8")
PALE = colors.HexColor("#F3F7F4")
GOLD = colors.HexColor("#BD8B48")


class CoverBanner(Flowable):
    def __init__(self, width: float, height: float = 60 * mm) -> None:
        super().__init__()
        self.width = width
        self.height = height

    def draw(self) -> None:
        canvas = self.canv
        canvas.setFillColor(INK)
        canvas.roundRect(0, 0, self.width, self.height, 4 * mm, fill=1, stroke=0)
        canvas.setFillColor(MINT)
        canvas.roundRect(12 * mm, self.height - 23 * mm, 11 * mm, 11 * mm, 2.5 * mm, fill=1, stroke=0)
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(1.7)
        x = 17.5 * mm
        y = self.height - 17.5 * mm
        canvas.line(x - 2.3 * mm, y, x - 0.5 * mm, y - 2 * mm)
        canvas.line(x - 0.5 * mm, y - 2 * mm, x + 3 * mm, y + 2.3 * mm)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(27 * mm, self.height - 17 * mm, "BRANDLENS")
        canvas.setFillColor(MINT)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(self.width - 12 * mm, self.height - 17 * mm, "CODESTAR 30  /  ROUND 2")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 25)
        canvas.drawString(12 * mm, self.height - 39 * mm, "Evidence-first brand review.")
        canvas.setFillColor(MINT)
        canvas.setFont("Helvetica", 15)
        canvas.drawString(12 * mm, self.height - 48 * mm, "Human-led decisions, from draft to sign-off.")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13.5,
            textColor=BODY,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "SmallCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "heading": ParagraphStyle(
            "HeadingCustom",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=INK,
            spaceAfter=5,
        ),
        "subheading": ParagraphStyle(
            "SubheadingCustom",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=INK,
            spaceAfter=3,
        ),
        "label": ParagraphStyle(
            "LabelCustom",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=TEAL,
            spaceAfter=4,
        ),
        "cell": ParagraphStyle(
            "CellCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=BODY,
        ),
        "cell_bold": ParagraphStyle(
            "CellBoldCustom",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=INK,
        ),
        "callout": ParagraphStyle(
            "CalloutCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=12,
            textColor=BODY,
            leftIndent=1,
        ),
    }


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _section_heading(number: str, title: str, styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    return [
        _paragraph(f'<font color="#27604F">{number}  /  </font>{title}', styles["heading"]),
        Spacer(1, 2 * mm),
    ]


def _table(rows: list[list[Flowable]], widths: list[float], header: bool = False) -> Table:
    table = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.45, LINE),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ]
        )
    else:
        commands.extend(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LINEBEFORE", (1, 0), (1, -1), 0.45, LINE),
            ]
        )
    table.setStyle(TableStyle(commands))
    return table


def _callout(text: str, width: float, styles: dict[str, ParagraphStyle], color=PALE) -> Table:
    box = Table([[_paragraph(text, styles["callout"])]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEBEFORE", (0, 0), (0, 0), 2.4, TEAL if color == PALE else GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return box


def _page_chrome(canvas, doc) -> None:
    canvas.saveState()
    page_width, page_height = A4
    canvas.setFillColor(TEAL)
    canvas.rect(0, page_height - 3 * mm, page_width, 3 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, 15 * mm, page_width - doc.rightMargin, 15 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(doc.leftMargin, 10 * mm, "BRANDLENS  |  CODESTAR 30  |  ROUND 2 BUILD")
    canvas.drawRightString(page_width - doc.rightMargin, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def build_pdf() -> None:
    page_width, _ = A4
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=18 * mm,
        bottomMargin=21 * mm,
        title="BrandLens | CodeStar 30 Round 2 Submission",
        author="Yuvraj Sonkar",
        subject="Updated project submission: features, implementation, plan changes and Round 3 improvements",
    )
    styles = _styles()
    usable = page_width - doc.leftMargin - doc.rightMargin
    story: list[Flowable] = []

    story.extend(
        [
            CoverBanner(usable),
            Spacer(1, 8 * mm),
            _paragraph("UPDATED PROJECT SUBMISSION  |  26 OCTOBER 2026", styles["label"]),
            _paragraph("A pre-publication checkpoint for every brand.", styles["heading"]),
            _paragraph(
                "BrandLens helps a team check marketing copy against an editable brand policy, "
                "see exactly why a phrase needs attention, and record a human review decision. "
                "Automated checks never approve or publish a draft.",
                styles["body"],
            ),
            Spacer(1, 3 * mm),
        ]
    )

    info = [
        [
            _paragraph("<b>TEAM</b><br/>BrandLens", styles["cell"]),
            _paragraph("<b>TEAM LEADER</b><br/>Yuvraj Sonkar (solo participant)", styles["cell"]),
            _paragraph("<b>PRODUCT STAGE</b><br/>Round 2 working build", styles["cell"]),
        ]
    ]
    story.append(_table(info, [usable * 0.27, usable * 0.38, usable * 0.35]))
    story.extend([Spacer(1, 5 * mm), _callout(
        '<b>Submission links:</b> The app and source must be published to public URLs before this PDF is filed. '
        'This local build includes a Render deployment blueprint; no public URL is claimed until deployment '
        'and repository publication are completed.',
        usable,
        styles,
        colors.HexColor("#FFF8EA"),
    ), Spacer(1, 5 * mm)])
    story.extend(_section_heading("01", "The judge's core workflow", styles))

    workflow = [
        [_paragraph("<b>01  Set policy</b>", styles["cell_bold"]), _paragraph("Add banned phrases and approved facts in Brand policy.", styles["cell"])],
        [_paragraph("<b>02  Submit a draft</b>", styles["cell_bold"]), _paragraph("Paste a campaign title and marketing copy; a sample is ready on first open.", styles["cell"])],
        [_paragraph("<b>03  Inspect the evidence</b>", styles["cell_bold"]), _paragraph("Review exact quoted text, rule/fact source IDs, severity, reason, and next step.", styles["cell"])],
        [_paragraph("<b>04  Make the call</b>", styles["cell_bold"]), _paragraph("Approve or request changes, add a note, and revisit the saved audit/history.", styles["cell"])],
    ]
    story.append(_table(workflow, [usable * 0.31, usable * 0.69]))
    story.extend(
        [
            Spacer(1, 5 * mm),
            _paragraph(
                "<b>Judge tip:</b> Run the pre-filled sample first. It intentionally triggers banned-term "
                "and unsupported-claim findings so the explanation and decision path are visible immediately.",
                styles["small"],
            ),
            PageBreak(),
        ]
    )

    story.extend(_section_heading("02", "Completed Round 2 features", styles))
    story.append(
        _paragraph(
            "The implementation prioritises a complete, testable text-review loop over unbuilt screens or "
            "claims of AI-powered compliance.",
            styles["body"],
        )
    )
    feature_rows = [
        [_paragraph("FEATURE", styles["cell_bold"]), _paragraph("IMPLEMENTATION", styles["cell_bold"]), _paragraph("USER VALUE", styles["cell_bold"])],
        [_paragraph("<b>Editable brand policy</b>", styles["cell"]), _paragraph("Add and persist banned phrases and approved facts in SQLite.", styles["cell"]), _paragraph("Reviews use the team's current reference list.", styles["cell"])],
        [_paragraph("<b>Explainable draft checks</b>", styles["cell"]), _paragraph("Case-insensitive exact-term checks plus numeric/absolute-claim heuristics.", styles["cell"]), _paragraph("Reviewers can inspect a quoted trigger and cited source ID.", styles["cell"])],
        [_paragraph("<b>Review findings</b>", styles["cell"]), _paragraph("Show severity, confidence label, reason, source text, and suggested next step.", styles["cell"]), _paragraph("Feedback is tied to draft evidence, not an unexplained score.", styles["cell"])],
        [_paragraph("<b>Human decision</b>", styles["cell"]), _paragraph("Approve or request changes with an optional reviewer note.", styles["cell"]), _paragraph("The system does not change or approve a draft automatically.", styles["cell"])],
        [_paragraph("<b>Review history &amp; audit</b>", styles["cell"]), _paragraph("Persist drafts, findings, status changes, notes, and dated audit events.", styles["cell"]), _paragraph("Reopen reviews and see who made a decision in this demo workspace.", styles["cell"])],
        [_paragraph("<b>Demo-ready interface</b>", styles["cell"]), _paragraph("Sample draft, policy/history pages, mobile layout, error and empty states.", styles["cell"]), _paragraph("A first-time judge can try the main flow without a walkthrough.", styles["cell"])],
    ]
    story.append(_table(feature_rows, [usable * 0.24, usable * 0.46, usable * 0.30], header=True))
    story.extend(
        [
            Spacer(1, 5 * mm),
            _paragraph("WHAT IS NOT IN THIS BUILD", styles["label"]),
            _callout(
                "No external LLM, retrieval/vector index, document/PDF upload, image review, role-based login, "
                "tracked edits, publishing integration, or analytics dashboard. The rules are deterministic "
                "heuristics and do not provide legal advice or prove that content is compliant.",
                usable,
                styles,
            ),
            Spacer(1, 5 * mm),
            _paragraph("Round 2 validation evidence", styles["label"]),
            _paragraph(
                "Four backend workflow tests pass, covering configurable policy, quoted findings, fact matching, "
                "human decisions, saved audit events, and blank input. Frontend lint and production build pass. "
                "The running browser/API workflow was manually checked against the sample draft.",
                styles["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(_section_heading("03", "Technology & implementation", styles))
    stack_rows = [
        [_paragraph("LAYER", styles["cell_bold"]), _paragraph("TECHNOLOGY", styles["cell_bold"]), _paragraph("ROLE IN THE BUILD", styles["cell_bold"])],
        [_paragraph("<b>Frontend</b>", styles["cell"]), _paragraph("React 19, Vite, JavaScript, CSS", styles["cell"]), _paragraph("Draft editor, policy controls, findings, decisions, and history views.", styles["cell"])],
        [_paragraph("<b>Backend API</b>", styles["cell"]), _paragraph("Python 3.11, FastAPI, Pydantic", styles["cell"]), _paragraph("Validated endpoints, deterministic checks, and review workflow.", styles["cell"])],
        [_paragraph("<b>Storage</b>", styles["cell"]), _paragraph("SQLite", styles["cell"]), _paragraph("Policy, draft, result, decision, and audit event records.", styles["cell"])],
        [_paragraph("<b>Deployment</b>", styles["cell"]), _paragraph("Docker multi-stage image; Render Blueprint", styles["cell"]), _paragraph("One web service builds the React assets and serves the API and app.", styles["cell"])],
        [_paragraph("<b>Quality checks</b>", styles["cell"]), _paragraph("unittest, Oxlint, Vite build", styles["cell"]), _paragraph("Repeatable backend workflow checks and production frontend verification.", styles["cell"])],
    ]
    story.append(_table(stack_rows, [usable * 0.19, usable * 0.32, usable * 0.49], header=True))
    story.extend(
        [
            Spacer(1, 6 * mm),
            _paragraph("Evidence-first review pipeline", styles["label"]),
            _callout(
                "<b>Draft text</b>  &gt;  <b>active policy</b>  &gt;  <b>deterministic match</b>  &gt;  "
                "<b>finding with exact quote + source ID</b>  &gt;  <b>human decision + audit event</b><br/><br/>"
                "A banned phrase is flagged only when it is found in the submitted text. Numeric/absolute claims "
                "are surfaced for reviewer verification unless an approved fact contains an exact matching claim. "
                "These safeguards are rule-based, not generative AI or a legal guarantee.",
                usable,
                styles,
            ),
            Spacer(1, 6 * mm),
            _paragraph("Responsible demo use", styles["label"]),
            _paragraph(
                "The public-demo configuration has no authentication and permits anonymous visitors. On the "
                "included free Render setup, SQLite is stored under /tmp and can reset when the instance restarts "
                "or redeploys. Do not enter confidential or personal material. Use persistent storage and add "
                "authentication before handling real organisation data.",
                styles["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(_section_heading("04", "Plan changes & Round 3 improvements", styles))
    story.append(_paragraph("Changes from the Round 1 proposal", styles["label"]))
    changes = [
        [_paragraph("<b>Kept</b>", styles["cell_bold"]), _paragraph("React frontend, Python FastAPI backend, SQLite for the demo, explainable checks, human approval, and audit/history.", styles["cell"])],
        [_paragraph("<b>Focused for Round 2</b>", styles["cell_bold"]), _paragraph("Completed the end-to-end text-review loop first: starter policy, configurable rules/facts, findings, reviewer note, human decision, and saved history.", styles["cell"])],
        [_paragraph("<b>Deferred openly</b>", styles["cell_bold"]), _paragraph("Document upload, image checks/OCR, multi-user roles, external AI and semantic retrieval, tracked-change editing, and insight analytics.", styles["cell"])],
    ]
    story.append(_table(changes, [usable * 0.25, usable * 0.75]))
    story.extend([Spacer(1, 6 * mm), _paragraph("Three substantive additions planned for Round 3", styles["label"])])

    improvements = [
        (
            "01",
            "Image brand review",
            "Accept image assets, check brand palette and logo presence, capture required alt text, and run OCR so image text can enter the same explainable text checks.",
        ),
        (
            "02",
            "Guideline-health insights",
            "Aggregate review findings and reviewer overrides to surface recurring problem areas and rules that may be unclear; let brand owners inspect the source before revising it.",
        ),
        (
            "03",
            "Verifier reliability upgrade",
            "Create a seeded-error evaluation set, reject quotes absent from the submitted draft and IDs absent from policy, test false positives/regressions, and tune when uncertain claims require human verification.",
        ),
    ]
    for number, title, detail in improvements:
        card = [
            _paragraph(f'<font color="#27604F"><b>{number}</b></font>', styles["cell_bold"]),
            _paragraph(f"<b>{title}</b><br/>{detail}", styles["cell"]),
        ]
        story.append(_table([card], [usable * 0.11, usable * 0.89]))
    story.extend(
        [
            Spacer(1, 6 * mm),
            _callout(
                "<b>Before filing:</b> publish the source as a public repository, deploy the Docker service, "
                "open the live app link in a private window, verify that a first-time visitor can run the sample, "
                "then replace the pending links in this PDF with the final public URLs.",
                usable,
                styles,
                colors.HexColor("#FFF8EA"),
            ),
            Spacer(1, 4 * mm),
            _paragraph("Project files: README.md  |  Dockerfile  |  render.yaml  |  backend/  |  frontend/", styles["small"]),
        ]
    )

    doc.build(story, onFirstPage=_page_chrome, onLaterPages=_page_chrome)
    print(f"Created {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
