"""Generate assignment PDFs with a fixed simple layout."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


class DocPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"Boreas take-home - page {self.page_no()}", align="C")


def write_lines(pdf: DocPDF, lines: list[str]) -> None:
    for line in lines:
        pdf.set_x(pdf.l_margin)
        w = pdf.epw
        if line.startswith("H1:"):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(w, 8, line[3:].strip())
            pdf.ln(2)
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("H2:"):
            pdf.ln(3)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(w, 7, line[3:].strip())
            pdf.ln(1)
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("B:"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(w, 6, line[2:].strip())
            pdf.set_font("Helvetica", size=11)
        elif not line.strip():
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(w, 6, line)


def arch_pdf() -> None:
    pdf = DocPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    write_lines(
        pdf,
        [
            "H1:Boreas - Architecture, Design and Tradeoffs",
            "H2:Product",
            "Boreas is a day-ahead GB national wind desk for January 2026.",
            "It shows the WINDFOR run a trader could use before the EPEX gate,",
            "pairs it to FUELHH WIND actuals, and reports MAE/RMSE/MAPE/bias plus a P90 residual band.",
            "H2:Architecture",
            "React SPA (Vite) -> FastAPI Boreas API -> Elexon Insights stream (FUELHH, WINDFOR).",
            "Local: docker compose (web:8080 proxies /api to api:8000).",
            "Deploy target: Vercel static frontend + Python serverless (Mangum).",
            "Cache: data/cache/jan2026_bundle.json baked for cold starts.",
            "",
            "ASCII diagram:",
            "[ React SPA ] --/api/*--> [ FastAPI ] --HTTPS--> [ Elexon Insights ]",
            "      |                      |",
            "   nginx (docker)     JSON cache volume",
            "H2:Decision-window rule",
            "For delivery day D (00:00-24:00 Europe/London):",
            "1. Gate close = 09:20 CET on D-1 (EPEX SPOT GB day-ahead).",
            "2. Eligible forecasts: WINDFOR publishTime <= gate.",
            "3. Take the latest eligible publishTime.",
            "4. Keep points with startTime on day D.",
            "5. Pair to FUELHH fuelType=WIND on matching startTime.",
            "Note: WINDFOR is hourly; FUELHH is half-hourly -> 744 paired intervals in Jan 2026.",
            "H2:Tradeoffs",
            "B:Stream dataset APIs vs opinionated forecast endpoints",
            "Chosen streams for publish-time history required by the brief.",
            "B:Baked cache vs live-only",
            "Deterministic demos and Vercel cold starts; refresh via POST /api/refresh.",
            "B:P90 abs error as residual band",
            "Non-parametric and procurement-actionable.",
            "B:Vercel-only (no Heroku)",
            "Per delivery constraint; Docker is the guaranteed local path.",
            "H2:Security and ops",
            "Elexon Insights is public (no key). Optional ELEXON_API_KEY for future gateways.",
            "No PII; national aggregates only.",
        ],
    )
    out = DOCS / "architecture-and-tradeoffs.pdf"
    pdf.output(str(out))
    print("Wrote", out)


def brief_pdf() -> None:
    pdf = DocPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    write_lines(
        pdf,
        [
            "H1:Boreas - Assignment Brief and Deliverables",
            "H2:What was asked",
            "UK utility day-ahead buyer needs:",
            "1. Decision-relevant national wind forecasts for purchase decisions.",
            "2. Quantitative accuracy to size thermal/residual procurement.",
            "Scope: Elexon FUELHH WIND + WINDFOR only; January 2026 delivery.",
            "Stack: React, Python, Docker; deploy sample; docs; public GitHub; demo materials.",
            "H2:What we delivered",
            "[x] React + FastAPI app (Boreas)",
            "[x] Elexon integration with decision-window filter",
            "[x] Metrics: MAE, RMSE, MAPE, bias, lead-time error, P90 band",
            "[x] Docker Compose",
            "[x] README with methodology and AI disclosure",
            "[x] Architecture PDF + assignment brief PDF",
            "[x] Public GitHub repo mqxvn-k7wp",
            "[x] Silent demo MP4 + SPEAKER_SCRIPT.md",
            "[x] SUBMISSION.md paste sheet (no Google form auto-submit)",
            "[ ] Live Vercel URL (morning login if token missing)",
            "[ ] Narrated unlisted YouTube (human morning upload)",
            "H2:Explicit non-goals",
            "No Google form submission, no Heroku, no overnight YouTube publish,",
            "no non-Elexon sources, no months beyond Jan 2026 delivery scope.",
        ],
    )
    out = DOCS / "assignment-brief-and-deliverables.pdf"
    pdf.output(str(out))
    print("Wrote", out)


if __name__ == "__main__":
    arch_pdf()
    brief_pdf()
