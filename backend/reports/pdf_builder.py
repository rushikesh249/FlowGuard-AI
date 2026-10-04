"""
reports/pdf_builder.py
──────────────────────
Professional PDF report generation using fpdf2.

Design: Minimal, fintech-grade layout — Inter/Helvetica, clean tables,
structured sections, muted color palette.
"""
from __future__ import annotations

import io
from typing import Any

from fpdf import FPDF


# ── Style constants ───────────────────────────────────────────────────────────

_FONT = "Helvetica"
_COLOR_PRIMARY  = (15, 23, 42)     # slate-900
_COLOR_SECONDARY = (100, 116, 139) # slate-500
_COLOR_ACCENT   = (30, 41, 59)     # slate-800
_COLOR_BORDER   = (226, 232, 240)  # slate-200
_COLOR_BG_LIGHT = (248, 250, 252)  # slate-50
_COLOR_RED      = (220, 38, 38)    # red-600
_COLOR_GREEN    = (5, 150, 105)    # emerald-600

# fpdf2 core fonts only support latin-1.  Transliterate common Unicode
# punctuation and drop anything else that cannot be encoded.
_UNICODE_SUBS = {
    "\u2014": "-",   # em dash
    "\u2013": "-",   # en dash
    "\u2022": "-",   # bullet
    "\u2019": "'",   # right single quote
    "\u2018": "'",   # left single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u00a0": " ",   # non-breaking space
    "\u2026": "...", # ellipsis
}


def _safe(text: Any) -> str:
    """Coerce *text* to a latin-1-encodable string for core PDF fonts."""
    s = str(text)
    for src, dst in _UNICODE_SUBS.items():
        s = s.replace(src, dst)
    return s.encode("latin-1", "replace").decode("latin-1")


# ── Base PDF class ────────────────────────────────────────────────────────────

class FlowGuardPDF(FPDF):
    """Custom PDF with consistent branding."""

    def header(self):
        self.set_font(_FONT, "B", 9)
        self.set_text_color(*_COLOR_SECONDARY)
        self.cell(0, 8, "FlowGuard AI", align="L")
        self.cell(0, 8, "Confidential", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*_COLOR_BORDER)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font(_FONT, "", 8)
        self.set_text_color(*_COLOR_SECONDARY)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.set_font(_FONT, "B", 12)
        self.set_text_color(*_COLOR_PRIMARY)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def metric_row(self, label: str, value: str, color=None):
        self.set_font(_FONT, "", 10)
        self.set_text_color(*_COLOR_SECONDARY)
        self.cell(80, 7, _safe(label))
        self.set_font(_FONT, "B", 10)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(*_COLOR_PRIMARY)
        self.cell(0, 7, _safe(value), new_x="LMARGIN", new_y="NEXT")

    def table_header(self, columns: list[tuple[str, int]]):
        """columns: list of (label, width)"""
        self.set_font(_FONT, "B", 8)
        self.set_text_color(*_COLOR_SECONDARY)
        self.set_fill_color(*_COLOR_BG_LIGHT)
        for label, w in columns:
            self.cell(w, 7, label.upper(), border=1, fill=True, align="C")
        self.ln()

    def table_row(self, values: list[str], widths: list[int], bold_first=False):
        self.set_font(_FONT, "", 8)
        self.set_text_color(*_COLOR_PRIMARY)
        for i, (val, w) in enumerate(zip(values, widths)):
            if bold_first and i == 0:
                self.set_font(_FONT, "B", 8)
            else:
                self.set_font(_FONT, "", 8)
            self.cell(w, 6, _safe(val)[:40], border="B", align="L")
        self.ln()


# ── Executive Summary PDF ────────────────────────────────────────────────────

def build_executive_pdf(data: dict) -> bytes:
    pdf = FlowGuardPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title
    pdf.set_font(_FONT, "B", 20)
    pdf.set_text_color(*_COLOR_PRIMARY)
    pdf.cell(0, 14, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(_FONT, "", 9)
    pdf.set_text_color(*_COLOR_SECONDARY)
    pdf.cell(0, 6, f"Generated: {_safe(data.get('generated_at', 'N/A'))}  |  Period: {_safe(data.get('date_range', 'N/A'))}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # KPI metrics
    pdf.section_title("Key Metrics")
    pdf.metric_row("Total Cases", f"{data['total_cases']:,}")
    pdf.metric_row("Total Events", f"{data['total_events']:,}")
    pdf.metric_row("Unique Activities", str(data["unique_activities"]))
    pdf.metric_row("Anomalies Detected", str(data["n_anomalies"]),
                   color=_COLOR_RED if data["n_anomalies"] > 0 else None)
    pdf.metric_row("Anomaly Rate", f"{data['anomaly_rate']}%")
    pdf.metric_row("Process Health Score", f"{data['health_score']}/100",
                   color=_COLOR_GREEN if data["health_score"] >= 90 else _COLOR_RED)
    pdf.ln(6)

    # Top anomalies
    top = data.get("top_anomalies", [])
    if top:
        pdf.section_title("Top Anomalies")
        cols = [("Case ID", 60), ("Score", 25), ("Events", 25), ("Activities", 25)]
        pdf.table_header(cols)
        widths = [60, 25, 25, 25]
        for a in top[:10]:
            pdf.table_row([
                a.get("case_id", ""),
                f"{a.get('anomaly_score', 0) * 100:.0f}%",
                str(a.get("n_events", 0)),
                str(a.get("n_unique_activities", 0)),
            ], widths)

    return pdf.output()


# ── Department Report PDF ────────────────────────────────────────────────────

def build_department_pdf(data: dict) -> bytes:
    pdf = FlowGuardPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font(_FONT, "B", 20)
    pdf.set_text_color(*_COLOR_PRIMARY)
    pdf.cell(0, 14, "Department Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(_FONT, "", 9)
    pdf.set_text_color(*_COLOR_SECONDARY)
    pdf.cell(0, 6, f"Generated: {data.get('generated_at', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    depts = data.get("departments", [])
    if not depts:
        pdf.set_font(_FONT, "", 10)
        pdf.cell(0, 10, "No department data available.")
        return pdf.output()

    cols = [
        ("Department", 50), ("Cases", 22), ("Events", 22),
        ("Avg Hrs", 22), ("Anomalies", 22), ("Rate", 22),
    ]
    pdf.table_header(cols)
    widths = [50, 22, 22, 22, 22, 22]

    for d in depts:
        rate_str = f"{d.get('anomaly_rate', 0):.1f}%"
        pdf.table_row([
            d["department"][:25],
            str(d["n_cases"]),
            str(d["n_events"]),
            f"{d.get('avg_duration_hours', 0):.1f}",
            str(d.get("n_anomalies", 0)),
            rate_str,
        ], widths, bold_first=True)

    return pdf.output()


# ── Anomaly Report PDF ───────────────────────────────────────────────────────

def build_anomaly_pdf(data: dict) -> bytes:
    pdf = FlowGuardPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font(_FONT, "B", 20)
    pdf.set_text_color(*_COLOR_PRIMARY)
    pdf.cell(0, 14, "Anomaly Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(_FONT, "", 9)
    pdf.set_text_color(*_COLOR_SECONDARY)
    pdf.cell(0, 6, f"Generated: {data.get('generated_at', 'N/A')}  |  "
             f"Total: {data.get('total_cases', 0)} cases  |  "
             f"Flagged: {data.get('total_anomalies', 0)} ({data.get('anomaly_rate', 0)}%)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    anomalies = data.get("anomalies", [])
    for i, a in enumerate(anomalies[:50]):  # Cap at 50 for PDF size
        # Case header
        pdf.set_font(_FONT, "B", 10)
        pdf.set_text_color(*_COLOR_PRIMARY)
        pdf.cell(0, 7, _safe(f"{a['case_id']}  -  Score: {a['anomaly_score'] * 100:.0f}%"),
                 new_x="LMARGIN", new_y="NEXT")

        pdf.set_font(_FONT, "", 8)
        pdf.set_text_color(*_COLOR_SECONDARY)
        pdf.cell(0, 5, f"Events: {a['n_events']}  |  Activities: {a['n_unique_activities']}  |  "
                 f"Severity: {a.get('severity_score', 0)}/10",
                 new_x="LMARGIN", new_y="NEXT")

        # Summary
        if a.get("summary"):
            pdf.set_font(_FONT, "", 8)
            pdf.set_text_color(*_COLOR_PRIMARY)
            pdf.multi_cell(0, 4, _safe(a["summary"]), new_x="LMARGIN", new_y="NEXT")

        # Explanations
        for exp in a.get("explanations", [])[:3]:
            severity = exp.get("severity", "")
            color = _COLOR_RED if severity == "high" else _COLOR_SECONDARY
            pdf.set_font(_FONT, "", 7)
            pdf.set_text_color(*color)
            desc = _safe(exp.get("description", ""))[:120]
            pdf.set_x(pdf.l_margin + 5)  # indent
            pdf.multi_cell(0, 4, f"- [{severity.upper()}] {desc}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(3)

        # Page break every 5 items
        if (i + 1) % 5 == 0 and pdf.get_y() > 240:
            pdf.add_page()

    return pdf.output()


# ── Monthly Report PDF ───────────────────────────────────────────────────────

def build_monthly_pdf(data: dict) -> bytes:
    pdf = FlowGuardPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font(_FONT, "B", 20)
    pdf.set_text_color(*_COLOR_PRIMARY)
    pdf.cell(0, 14, "Monthly Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(_FONT, "", 9)
    pdf.set_text_color(*_COLOR_SECONDARY)
    pdf.cell(0, 6, f"Generated: {data.get('generated_at', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    months = data.get("months", [])
    if not months:
        pdf.set_font(_FONT, "", 10)
        pdf.cell(0, 10, "No monthly data available.")
        return pdf.output()

    cols = [("Month", 45), ("Events", 30), ("Cases", 30), ("Anomalies", 30)]
    pdf.table_header(cols)
    widths = [45, 30, 30, 30]

    for m in months:
        pdf.table_row([
            m["month"],
            f"{m['n_events']:,}",
            f"{m['n_cases']:,}",
            str(m.get("n_anomalies", 0)),
        ], widths)

    # Totals
    pdf.ln(3)
    pdf.set_font(_FONT, "B", 9)
    pdf.set_text_color(*_COLOR_PRIMARY)
    total_events = sum(m["n_events"] for m in months)
    total_cases = sum(m["n_cases"] for m in months)
    total_anom = sum(m.get("n_anomalies", 0) for m in months)
    pdf.cell(45, 7, "TOTAL")
    pdf.cell(30, 7, f"{total_events:,}")
    pdf.cell(30, 7, f"{total_cases:,}")
    pdf.cell(30, 7, str(total_anom))

    return pdf.output()
