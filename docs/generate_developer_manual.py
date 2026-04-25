#!/usr/bin/env python3
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
MedPharm ERP — Developer Manual PDF Generator (Volume III)

Volume III is the developer's counterpart to the Technical Reference
(Volume I) and the Service Manual (Volume II). Where Volume I describes
what the software IS and Volume II describes how to OPERATE it in
production, Volume III describes how it was BUILT and how an engineer
should extend, debug, and evolve it.

Audience: software engineers joining the project, maintainers returning
after time away, external auditors reviewing the codebase, and
contributors preparing pull requests. The manual assumes working
knowledge of Python, relational databases, and at least one mobile
platform (Android, iOS, macOS, or Windows).

The generator is deliberately self-contained: it reads no project
files at build time. Code samples are reproduced inline so the manual
compiles cleanly in sterile environments (CI, Docker builds,
documentation-only forks) and does not drift when the underlying
modules are refactored. When source code changes substantially, the
revision of the manual is incremented (1.7.6-A, 1.7.6-B, …) and
re-issued.
"""

from __future__ import annotations

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as canvas_module
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "MedPharm_ERP_Developer_Manual.pdf")

SUPPORT_EMAIL = "Andrew.Stillwell@enlightec.com"
COMPANY_URL = "https://www.enlightec.com"
REPO_URL = "https://github.com/stillwell/MedPharm"
DOCKERHUB_URL = "https://hub.docker.com/u/enlightec"

# ── Colour palette ────────────────────────────────────────────────────────────
#
# Volume III uses a navy / indigo palette — cooler than Volume I's teal
# and Volume II's warmer muted tones. The intent is a scholarly,
# technical feel appropriate to source-code walkthroughs and protocol
# diagrams.

NAVY = colors.HexColor("#0D1B3A")
NAVY_LIGHT = colors.HexColor("#1A237E")
NAVY_PALE = colors.HexColor("#E8EAF6")
INDIGO = colors.HexColor("#3949AB")
INDIGO_PALE = colors.HexColor("#C5CAE9")
STEEL = colors.HexColor("#455A64")
STONE = colors.HexColor("#78909C")
SLATE = colors.HexColor("#37474F")
INK = colors.HexColor("#0B1020")
CLOUD = colors.HexColor("#ECEFF1")
PARCHMENT = colors.HexColor("#FAFAF7")

AMBER = colors.HexColor("#E65100")
AMBER_PALE = colors.HexColor("#FFF8E1")
CRIMSON = colors.HexColor("#B71C1C")
CRIMSON_PALE = colors.HexColor("#FFEBEE")
MOSS = colors.HexColor("#2E7D32")
MOSS_PALE = colors.HexColor("#E8F5E9")
TEAL = colors.HexColor("#00796B")

# Syntax-highlight palette
CODE_BG = colors.HexColor("#0F1530")
CODE_FG = colors.HexColor("#E9EEF7")
CODE_KEYWORD = colors.HexColor("#82AAFF")
CODE_STRING = colors.HexColor("#C3E88D")
CODE_COMMENT = colors.HexColor("#8695B0")
CODE_NUMBER = colors.HexColor("#F78C6C")
CODE_BUILTIN = colors.HexColor("#FFCB6B")
CODE_LINE_NO = colors.HexColor("#5A6782")


# ── Styles ────────────────────────────────────────────────────────────────────

def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "DM_Title", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=38, leading=44,
        textColor=colors.white, alignment=TA_CENTER, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        "DM_Subtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=14, leading=18,
        textColor=INDIGO_PALE, alignment=TA_CENTER, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        "DM_PartTitle", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=28, leading=34,
        textColor=NAVY_LIGHT, alignment=TA_LEFT, spaceBefore=0, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "DM_PartNumber", parent=styles["Normal"],
        fontName="Helvetica", fontSize=11, leading=14,
        textColor=STONE, alignment=TA_LEFT, spaceAfter=24,
    ))
    styles.add(ParagraphStyle(
        "DM_ChapterNumber", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=10, leading=12,
        textColor=INDIGO, alignment=TA_LEFT, spaceAfter=2,
        letterSpacing=2,
    ))
    styles.add(ParagraphStyle(
        "DM_ChapterTitle", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=22, leading=26,
        textColor=NAVY, alignment=TA_LEFT, spaceBefore=0, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        "DM_Section", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=14, leading=18,
        textColor=NAVY_LIGHT, alignment=TA_LEFT, spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "DM_Subsection", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=12, leading=16,
        textColor=INDIGO, alignment=TA_LEFT, spaceBefore=10, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "DM_Body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10.5, leading=15,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "DM_Caption", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=9, leading=12,
        textColor=STEEL, alignment=TA_CENTER, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "DM_Note", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=INK, alignment=TA_LEFT,
        backColor=NAVY_PALE, borderColor=INDIGO, borderWidth=0.5,
        borderPadding=10, spaceBefore=6, spaceAfter=10,
        leftIndent=0, rightIndent=0,
    ))
    styles.add(ParagraphStyle(
        "DM_Caution", parent=styles["DM_Note"],
        backColor=AMBER_PALE, borderColor=AMBER,
    ))
    styles.add(ParagraphStyle(
        "DM_Danger", parent=styles["DM_Note"],
        backColor=CRIMSON_PALE, borderColor=CRIMSON,
    ))
    styles.add(ParagraphStyle(
        "DM_Tip", parent=styles["DM_Note"],
        backColor=MOSS_PALE, borderColor=MOSS,
    ))
    styles.add(ParagraphStyle(
        "DM_Bullet", parent=styles["DM_Body"],
        bulletIndent=10, leftIndent=24, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "DM_Code", parent=styles["Code"],
        fontName="Courier", fontSize=8.5, leading=11.5,
        textColor=CODE_FG, backColor=CODE_BG,
        borderColor=NAVY, borderWidth=0,
        borderPadding=0,
        leftIndent=0, rightIndent=0,
        alignment=TA_LEFT, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        "DM_Inline", parent=styles["Normal"],
        fontName="Courier", fontSize=9.5,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        "DM_TOCPart", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=13, leading=18,
        textColor=NAVY, spaceBefore=12, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "DM_TOCChapter", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10.5, leading=15,
        textColor=INK, leftIndent=14, spaceAfter=2,
    ))
    return styles


# ── Inline helpers ────────────────────────────────────────────────────────────

def b(txt): return f"<b>{txt}</b>"
def i(txt): return f"<i>{txt}</i>"
def c(txt):
    return (f'<font face="Courier" size="9.5" color="#0D1B3A">{txt}</font>')
def link(url, label=None):
    label = label or url
    return f'<link href="{url}" color="#3949AB"><u>{label}</u></link>'
def mail(addr=SUPPORT_EMAIL, label=None):
    return link(f"mailto:{addr}", label or addr)


# ── Spine marker (left-side coloured rule on each chapter opener) ─────────────

class SpineMark(Flowable):
    """A thin coloured rule across the page that marks a chapter opener."""
    def __init__(self, width=7.0 * inch, color=INDIGO):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.height = 2

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


# ── Page frame / document template ────────────────────────────────────────────

class DevManualDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(
            self, filename, pagesize=letter,
            leftMargin=0.9 * inch, rightMargin=0.9 * inch,
            topMargin=1.0 * inch, bottomMargin=0.9 * inch,
            title="MedPharm ERP — Developer Manual",
            author="Robert Andrew Stillwell, Enlightec Ltd.",
            subject="Software Development Reference — Volume III",
            creator="MedPharm Developer Manual Generator",
            **kw,
        )
        self.part_roman = "I"
        self.part_label = "Foundations"
        self.build_date = datetime.now().strftime("%d %B %Y")

        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="normal")

        title_page = PageTemplate("title", [frame], onPage=self._draw_title_page)
        content_page = PageTemplate("content", [frame],
                                    onPage=self._draw_content_page)
        part_page = PageTemplate("partdiv", [frame],
                                 onPage=self._draw_part_page)
        self.addPageTemplates([title_page, content_page, part_page])

    def afterFlowable(self, flowable):
        # Track the current part from part-divider flowables
        if isinstance(flowable, _PartMarker):
            self.part_roman = flowable.roman
            self.part_label = flowable.label

    def _draw_title_page(self, canv, doc):
        w, h = letter
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, 0, w, h, fill=1, stroke=0)
        canv.setFillColor(INDIGO)
        canv.rect(0, h * 0.55, w, 6, fill=1, stroke=0)
        canv.setFillColor(INDIGO_PALE)
        canv.rect(0, h * 0.55 - 8, w, 1, fill=1, stroke=0)
        canv.restoreState()

    def _draw_content_page(self, canv, doc):
        w, h = letter
        canv.saveState()
        # Top header band
        canv.setFillColor(NAVY_PALE)
        canv.rect(0, h - 36, w, 36, fill=1, stroke=0)
        canv.setStrokeColor(INDIGO)
        canv.setLineWidth(0.5)
        canv.line(0, h - 36, w, h - 36)

        canv.setFont("Helvetica-Bold", 9)
        canv.setFillColor(NAVY)
        canv.drawString(0.9 * inch, h - 24,
                        f"MedPharm ERP — Developer Manual")
        canv.setFont("Helvetica", 8)
        canv.setFillColor(STEEL)
        canv.drawRightString(w - 0.9 * inch, h - 24,
                             f"Part {self.part_roman} · {self.part_label}")

        # Bottom footer
        canv.setStrokeColor(INDIGO_PALE)
        canv.setLineWidth(0.4)
        canv.line(0.9 * inch, 0.7 * inch, w - 0.9 * inch, 0.7 * inch)
        canv.setFont("Helvetica", 8)
        canv.setFillColor(STONE)
        canv.drawString(0.9 * inch, 0.52 * inch,
                        f"Issued {self.build_date}  //  Revision 1.7.6-A")
        canv.drawCentredString(w / 2, 0.52 * inch,
                               "Enlightec Ltd. — INTERNAL DEVELOPMENT REFERENCE")
        canv.drawRightString(w - 0.9 * inch, 0.52 * inch, f"Page {doc.page}")
        canv.restoreState()

    def _draw_part_page(self, canv, doc):
        w, h = letter
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, 0, w, h, fill=1, stroke=0)
        # Diagonal accent
        canv.setFillColor(INDIGO)
        p = canv.beginPath()
        p.moveTo(0, h * 0.7)
        p.lineTo(w, h * 0.55)
        p.lineTo(w, h * 0.58)
        p.lineTo(0, h * 0.73)
        p.close()
        canv.drawPath(p, fill=1, stroke=0)
        canv.restoreState()


class _PartMarker(Flowable):
    """Invisible flowable that stamps the active part into the doc template."""
    def __init__(self, roman, label):
        Flowable.__init__(self)
        self.roman = roman
        self.label = label
        self.height = 0
        self.width = 0

    def draw(self):
        pass


class PartBanner(Flowable):
    """Large decorative part heading displayed on the part divider page.

    Paints a full-page navy backdrop directly via the canvas so it does
    not depend on which page template is active. The rect is sized
    generously to cover any letter page; PDF viewers clip to the
    MediaBox, so the over-draw is harmless and avoids needing a
    dedicated page template (whose template-switch dance was producing
    blank pages and bleeding the cover backdrop into body chapters).
    """
    def __init__(self, roman, title):
        Flowable.__init__(self)
        self.roman = roman
        self.title = title
        self.width = 7.0 * inch
        self.height = 3.2 * inch

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(-12 * inch, -12 * inch, 24 * inch, 24 * inch, fill=1, stroke=0)
        c.setFillColor(INDIGO)
        p = c.beginPath()
        p.moveTo(-2 * inch, self.height + 0.5 * inch)
        p.lineTo(10 * inch, self.height - 1.0 * inch)
        p.lineTo(10 * inch, self.height - 0.7 * inch)
        p.lineTo(-2 * inch, self.height + 0.8 * inch)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.restoreState()
        c.setFont("Helvetica", 18)
        c.setFillColor(INDIGO_PALE)
        c.drawString(0, self.height - 30, "PART")
        c.setFont("Helvetica-Bold", 92)
        c.setFillColor(colors.white)
        c.drawString(1.2 * inch, self.height - 120, self.roman)
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(colors.white)
        c.drawString(0, self.height - 180, self.title)
        c.setStrokeColor(INDIGO_PALE)
        c.setLineWidth(0.8)
        c.line(0, self.height - 200, 5.5 * inch, self.height - 200)


# ── Table helper ──────────────────────────────────────────────────────────────

def make_table(headers, rows, col_widths=None, header_color=NAVY_LIGHT,
               header_text_color=colors.white, alt_row_color=NAVY_PALE,
               font_size=9.5):
    data = [headers] + rows
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), header_text_color),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), font_size),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), font_size),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INDIGO),
        ("GRID", (0, 1), (-1, -1), 0.25, INDIGO_PALE),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.add("BACKGROUND", (0, i), (-1, i), alt_row_color)
    table.setStyle(style)
    return table


# ── Code block with simple syntax highlighting ────────────────────────────────

_PY_KEYWORDS = {
    "and", "as", "assert", "async", "await", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "finally", "for", "from",
    "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or",
    "pass", "raise", "return", "try", "while", "with", "yield", "True",
    "False", "None", "self",
}

_SWIFT_KEYWORDS = {
    "import", "struct", "class", "enum", "protocol", "extension", "let",
    "var", "func", "return", "if", "else", "guard", "while", "for", "in",
    "switch", "case", "default", "break", "continue", "throws", "throw",
    "try", "catch", "async", "await", "self", "nil", "true", "false",
    "private", "public", "internal", "fileprivate", "static", "final",
    "override", "mutating", "some", "any", "where",
}

_KOTLIN_KEYWORDS = {
    "package", "import", "class", "object", "interface", "fun", "val",
    "var", "return", "if", "else", "when", "while", "for", "in", "is",
    "as", "private", "public", "protected", "internal", "override",
    "suspend", "data", "open", "sealed", "abstract", "companion",
    "this", "super", "null", "true", "false", "by",
}

_CS_KEYWORDS = {
    "using", "namespace", "class", "struct", "interface", "enum",
    "public", "private", "protected", "internal", "static", "readonly",
    "const", "new", "return", "if", "else", "while", "for", "foreach",
    "in", "switch", "case", "default", "break", "continue", "throw",
    "try", "catch", "finally", "async", "await", "var", "this", "null",
    "true", "false", "override", "virtual", "abstract", "sealed",
    "partial", "get", "set", "record",
}

_SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE",
    "SET", "DELETE", "CREATE", "TABLE", "INDEX", "ALTER", "DROP",
    "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "NOT", "NULL", "UNIQUE",
    "INTEGER", "TEXT", "VARCHAR", "DATETIME", "DATE", "BOOLEAN", "REAL",
    "DEFAULT", "AND", "OR", "IN", "LIKE", "JOIN", "ON", "GROUP", "BY",
    "ORDER", "LIMIT", "DESC", "ASC", "AS", "WITH",
}


def _esc(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def _highlight(line, language):
    """Very lightweight syntax highlighter producing ReportLab-safe markup."""
    if language in ("python", "py"):
        return _highlight_python(line)
    if language == "swift":
        return _highlight_generic(line, _SWIFT_KEYWORDS)
    if language == "kotlin":
        return _highlight_generic(line, _KOTLIN_KEYWORDS)
    if language in ("cs", "csharp"):
        return _highlight_generic(line, _CS_KEYWORDS)
    if language == "sql":
        return _highlight_generic(line, _SQL_KEYWORDS, case_insensitive=True)
    # Default: escape only
    return _esc(line)


def _highlight_python(line):
    # Handle comments first
    out = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        # Comment
        if ch == "#":
            out.append(f'<font color="{CODE_COMMENT.hexval()}">{_esc(line[i:])}</font>')
            return "".join(out)
        # String literal
        if ch in ('"', "'"):
            quote = ch
            j = i + 1
            while j < n and line[j] != quote:
                if line[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                j += 1
            j = min(j + 1, n)
            out.append(f'<font color="{CODE_STRING.hexval()}">{_esc(line[i:j])}</font>')
            i = j
            continue
        # Identifier / keyword
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (line[j].isalnum() or line[j] == "_"):
                j += 1
            word = line[i:j]
            if word in _PY_KEYWORDS:
                out.append(f'<font color="{CODE_KEYWORD.hexval()}"><b>{_esc(word)}</b></font>')
            elif j < n and line[j] == "(":
                out.append(f'<font color="{CODE_BUILTIN.hexval()}">{_esc(word)}</font>')
            else:
                out.append(_esc(word))
            i = j
            continue
        # Number
        if ch.isdigit():
            j = i
            while j < n and (line[j].isdigit() or line[j] == "."):
                j += 1
            out.append(f'<font color="{CODE_NUMBER.hexval()}">{_esc(line[i:j])}</font>')
            i = j
            continue
        out.append(_esc(ch))
        i += 1
    return "".join(out)


def _highlight_generic(line, keywords, case_insensitive=False):
    out = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            out.append(f'<font color="{CODE_COMMENT.hexval()}">{_esc(line[i:])}</font>')
            return "".join(out)
        if ch == "#":
            out.append(f'<font color="{CODE_COMMENT.hexval()}">{_esc(line[i:])}</font>')
            return "".join(out)
        if ch == '"':
            j = i + 1
            while j < n and line[j] != '"':
                if line[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                j += 1
            j = min(j + 1, n)
            out.append(f'<font color="{CODE_STRING.hexval()}">{_esc(line[i:j])}</font>')
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (line[j].isalnum() or line[j] == "_"):
                j += 1
            word = line[i:j]
            check = word.upper() if case_insensitive else word
            if check in keywords:
                out.append(f'<font color="{CODE_KEYWORD.hexval()}"><b>{_esc(word)}</b></font>')
            elif j < n and line[j] == "(":
                out.append(f'<font color="{CODE_BUILTIN.hexval()}">{_esc(word)}</font>')
            else:
                out.append(_esc(word))
            i = j
            continue
        if ch.isdigit():
            j = i
            while j < n and (line[j].isdigit() or line[j] == "."):
                j += 1
            out.append(f'<font color="{CODE_NUMBER.hexval()}">{_esc(line[i:j])}</font>')
            i = j
            continue
        out.append(_esc(ch))
        i += 1
    return "".join(out)


def code_block(src, language="python", caption=None, first_line=1):
    """Render a source listing with line numbers and syntax highlighting."""
    lines = src.rstrip("\n").split("\n")
    rows = []
    for idx, raw in enumerate(lines, start=first_line):
        num_cell = Paragraph(
            f'<font face="Courier" size="7.5" color="{CODE_LINE_NO.hexval()}">{idx:>4}</font>',
            ParagraphStyle("lineno", fontName="Courier", fontSize=7.5,
                           textColor=CODE_LINE_NO, alignment=TA_RIGHT,
                           leading=11, leftIndent=0, rightIndent=0))
        body = _highlight(raw, language)
        if not body:
            body = "&nbsp;"
        body_cell = Paragraph(
            f'<font face="Courier" size="8.5">{body}</font>',
            ParagraphStyle("codeline", fontName="Courier", fontSize=8.5,
                           textColor=CODE_FG, alignment=TA_LEFT,
                           leading=11, leftIndent=0, rightIndent=0,
                           wordWrap="CJK"))
        rows.append([num_cell, body_cell])

    tbl = Table(rows, colWidths=[0.45 * inch, 6.0 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, CODE_LINE_NO),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    flow = [tbl]
    if caption:
        flow.append(Spacer(1, 4))
        flow.append(Paragraph(caption, ParagraphStyle(
            "codecap", fontName="Helvetica-Oblique", fontSize=9, leading=12,
            textColor=STEEL, alignment=TA_CENTER, spaceAfter=12)))
    else:
        flow.append(Spacer(1, 10))
    return flow


# ── Flowchart flowable ────────────────────────────────────────────────────────

class Flowchart(Flowable):
    """Simple box-and-arrow flowchart.

    `nodes` is a list of dicts:
        {"id": "A", "label": "Client", "x": 1.0, "y": 4.0,
         "w": 1.5, "h": 0.6, "shape": "box"|"oval"|"diamond",
         "fill": colors.HexColor("..."), "text_color": colors...}
    `edges` is a list of dicts:
        {"from": "A", "to": "B", "label": "POST /login", "style": "solid"|"dashed"}
    Coordinates are inches, origin at bottom-left of drawing.
    """
    def __init__(self, nodes, edges, width=6.5, height=4.5, caption=None):
        Flowable.__init__(self)
        self.nodes = {n["id"]: n for n in nodes}
        self.node_list = nodes
        self.edges = edges
        self.width = width * inch
        self.height = height * inch
        self.caption = caption

    def wrap(self, *args):
        return self.width, self.height + (0.35 * inch if self.caption else 0)

    def _draw_node(self, c, node):
        x = node["x"] * inch
        y = node["y"] * inch
        w = node.get("w", 1.4) * inch
        h = node.get("h", 0.55) * inch
        shape = node.get("shape", "box")
        fill = node.get("fill", INDIGO_PALE)
        stroke = node.get("stroke", INDIGO)
        text_color = node.get("text_color", NAVY)

        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(0.8)
        if shape == "oval":
            c.ellipse(x - w / 2, y - h / 2, x + w / 2, y + h / 2,
                      fill=1, stroke=1)
        elif shape == "diamond":
            p = c.beginPath()
            p.moveTo(x, y + h / 2)
            p.lineTo(x + w / 2, y)
            p.lineTo(x, y - h / 2)
            p.lineTo(x - w / 2, y)
            p.close()
            c.drawPath(p, fill=1, stroke=1)
        else:  # box
            c.roundRect(x - w / 2, y - h / 2, w, h, 4, fill=1, stroke=1)

        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 9)
        # Wrap label on up to 2 lines
        label = node["label"]
        if len(label) > 22:
            words = label.split()
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            c.drawCentredString(x, y + 2, line1)
            c.drawCentredString(x, y - 9, line2)
        else:
            c.drawCentredString(x, y - 3, label)

    def _edge_points(self, a, b):
        """Compute attachment points between two node boxes."""
        ax = a["x"] * inch
        ay = a["y"] * inch
        aw = a.get("w", 1.4) * inch
        ah = a.get("h", 0.55) * inch
        bx = b["x"] * inch
        by = b["y"] * inch
        bw = b.get("w", 1.4) * inch
        bh = b.get("h", 0.55) * inch

        dx = bx - ax
        dy = by - ay

        if abs(dx) > abs(dy):
            # horizontal-dominated
            if dx > 0:
                start = (ax + aw / 2, ay)
                end = (bx - bw / 2, by)
            else:
                start = (ax - aw / 2, ay)
                end = (bx + bw / 2, by)
        else:
            if dy > 0:
                start = (ax, ay + ah / 2)
                end = (bx, by - bh / 2)
            else:
                start = (ax, ay - ah / 2)
                end = (bx, by + bh / 2)
        return start, end

    def _draw_arrow(self, c, start, end, label=None, dashed=False):
        c.setStrokeColor(SLATE)
        c.setLineWidth(0.8)
        if dashed:
            c.setDash(3, 2)
        else:
            c.setDash()
        c.line(start[0], start[1], end[0], end[1])
        c.setDash()
        # Arrowhead
        import math
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        head_len = 7
        ax = end[0] - head_len * math.cos(angle - math.pi / 7)
        ay = end[1] - head_len * math.sin(angle - math.pi / 7)
        bx = end[0] - head_len * math.cos(angle + math.pi / 7)
        by = end[1] - head_len * math.sin(angle + math.pi / 7)
        c.setFillColor(SLATE)
        p = c.beginPath()
        p.moveTo(end[0], end[1])
        p.lineTo(ax, ay)
        p.lineTo(bx, by)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

        if label:
            c.setFont("Helvetica", 7.5)
            c.setFillColor(STEEL)
            mx = (start[0] + end[0]) / 2
            my = (start[1] + end[1]) / 2 + 3
            c.drawCentredString(mx, my, label)

    def draw(self):
        c = self.canv
        c.saveState()
        # Background
        c.setFillColor(PARCHMENT)
        c.setStrokeColor(INDIGO_PALE)
        c.setLineWidth(0.3)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=1)

        # Edges first so nodes sit on top
        for e in self.edges:
            a = self.nodes[e["from"]]
            b = self.nodes[e["to"]]
            start, end = self._edge_points(a, b)
            self._draw_arrow(c, start, end,
                             label=e.get("label"),
                             dashed=(e.get("style") == "dashed"))
        for n in self.node_list:
            self._draw_node(c, n)
        c.restoreState()

        if self.caption:
            c.saveState()
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(STEEL)
            c.drawCentredString(self.width / 2, -15, self.caption)
            c.restoreState()


# ── Section convenience ───────────────────────────────────────────────────────

def p(text, styles): return Paragraph(text, styles["DM_Body"])
def h2(text, styles): return Paragraph(text, styles["DM_Section"])
def h3(text, styles): return Paragraph(text, styles["DM_Subsection"])
def note(text, styles): return Paragraph(f"<b>Note.</b> {text}", styles["DM_Note"])
def caution(text, styles): return Paragraph(f"<b>Caution.</b> {text}", styles["DM_Caution"])
def danger(text, styles): return Paragraph(f"<b>Danger.</b> {text}", styles["DM_Danger"])
def tip(text, styles): return Paragraph(f"<b>Tip.</b> {text}", styles["DM_Tip"])


def bullets(items, styles):
    return ListFlowable(
        [ListItem(Paragraph(item, styles["DM_Bullet"]), leftIndent=16)
         for item in items],
        bulletType="bullet", bulletFontSize=8,
        leftIndent=10, spaceAfter=8)


def chapter_header(num, title, styles):
    s = [Spacer(1, 0.05 * inch)]
    s.append(Paragraph(f"CHAPTER&nbsp;{num}", styles["DM_ChapterNumber"]))
    s.append(Paragraph(title, styles["DM_ChapterTitle"]))
    s.append(SpineMark())
    s.append(Spacer(1, 0.1 * inch))
    return s


def appendix_header(letter_label, title, styles):
    s = [Spacer(1, 0.05 * inch)]
    s.append(Paragraph(f"APPENDIX&nbsp;{letter_label}", styles["DM_ChapterNumber"]))
    s.append(Paragraph(title, styles["DM_ChapterTitle"]))
    s.append(SpineMark())
    s.append(Spacer(1, 0.1 * inch))
    return s


def part_divider(roman, title, subtitle, styles):
    s = [_PartMarker(roman, title)]
    s.append(Spacer(1, 1.6 * inch))
    s.append(PartBanner(roman, title))
    s.append(Spacer(1, 0.6 * inch))
    s.append(Paragraph(subtitle, ParagraphStyle(
        "PartSub", parent=styles["Normal"], fontName="Helvetica-Oblique",
        fontSize=12, leading=18, textColor=INDIGO_PALE, alignment=TA_LEFT)))
    s.append(PageBreak())
    return s


# Content builders live in subsequent modules of this file, below.
# The sections are assembled by `assemble_story()` at the bottom.


# ═════════════════════════════════════════════════════════════════════════════
# FRONT MATTER
# ═════════════════════════════════════════════════════════════════════════════

def build_cover(styles):
    story = [Spacer(1, 1.0 * inch)]
    story.append(Paragraph("MedPharm ERP", styles["DM_Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("DEVELOPER MANUAL", ParagraphStyle(
        "CovKicker", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=16, leading=20, textColor=INDIGO_PALE,
        alignment=TA_CENTER, spaceAfter=0)))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph(
        "The source-of-truth reference for the engineers who build, "
        "extend, and maintain MedPharm ERP.",
        styles["DM_Subtitle"]))
    story.append(Spacer(1, 0.8 * inch))

    story.append(Paragraph("VOLUME III", ParagraphStyle(
        "CovVol", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=13, textColor=INDIGO_PALE, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph(
        "Revision 1.7.6-A &nbsp;//&nbsp; Issued "
        + datetime.now().strftime("%B %Y"),
        ParagraphStyle("CovRev", parent=styles["Normal"],
                       fontName="Helvetica", fontSize=10,
                       textColor=INDIGO_PALE, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.22 * inch))
    story.append(Paragraph(
        "Enlightec Ltd. &nbsp;&middot;&nbsp; "
        "Medical &amp; Pharmaceutical Enterprise Resource Planning",
        ParagraphStyle("CovAuth", parent=styles["Normal"],
                       fontName="Helvetica-Oblique", fontSize=10,
                       textColor=INDIGO_PALE, alignment=TA_CENTER)))
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())
    return story


def build_colophon(styles):
    story = [Spacer(1, 0.35 * inch)]
    story.append(Paragraph("Document Control", styles["DM_Section"]))
    story.append(make_table(
        ["Field", "Value"],
        [
            ["Title", "MedPharm ERP — Developer Manual"],
            ["Volume / Edition", "Volume III — Engineer Edition"],
            ["Revision", "1.7.6-A"],
            ["Issue Date", datetime.now().strftime("%d %B %Y")],
            ["Author", "Robert Andrew Stillwell"],
            ["Publisher", "Enlightec Ltd., www.enlightec.com"],
            ["Applies To", "MedPharm ERP versions 1.7.x (latest 1.7.6)"],
            ["Classification", "CONFIDENTIAL — Engineering Internal"],
            ["Licence", "GNU General Public License v3.0"],
            ["Companion Volumes",
             "Volume I — Technical Reference (MedPharm_ERP_Documentation.pdf)<br/>"
             "Volume II — Service Manual (MedPharm_ERP_Service_Manual.pdf)"],
            ["Source Repository", REPO_URL],
            ["Container Registry", DOCKERHUB_URL],
            ["Support Contact", SUPPORT_EMAIL],
        ],
        col_widths=[1.7 * inch, 4.6 * inch]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Document Purpose", styles["DM_Section"]))
    story.append(p(
        "This manual is the authoritative description of MedPharm ERP's "
        "software construction. It answers the questions an engineer has "
        "when the code is unfamiliar: "
        + i("why does it look like this, where do I put my change, "
            "how do I test it, and what will I break?") + " "
        "Wherever possible, answers are grounded in code samples pulled "
        "from the current tree; wherever the code cannot answer on its "
        "own, the manual provides the surrounding rationale that would "
        "otherwise live in a senior engineer's head.",
        styles))
    story.append(p(
        "Three readers are kept in mind throughout. The "
        + b("new hire") + " reads cover-to-cover over the first week "
        "and returns to specific chapters thereafter. The "
        + b("returning maintainer") + " skims the table of contents for "
        "the module they need to change and consults only the relevant "
        "chapter. The "
        + b("external auditor") + " reads Parts II through V to evaluate "
        "whether the codebase implements the clinical, financial, and "
        "compliance claims made in the product marketing material. This "
        "document should serve all three without qualification.",
        styles))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Contacting the Authors", styles["DM_Section"]))
    story.append(p(
        f"For correction, clarification, or extension requests, write to "
        f"{mail()}. Responses arrive within two business days in all "
        f"but exceptional weeks; if you have not heard back within "
        f"four business days, please resend with the subject line "
        f"prefixed with {c('[devmanual-followup]')}.",
        styles))
    story.append(p(
        f"Bug reports that are not confidential are welcome as GitHub "
        f"issues at {link(REPO_URL + '/issues')}. Confidential reports — "
        f"including suspected security vulnerabilities — must go by "
        f"email only; see Chapter 30 for the responsible disclosure "
        f"process in full.",
        styles))
    story.append(PageBreak())
    return story


def build_foreword(styles):
    s = chapter_header("", "Foreword", styles)
    s.append(p(
        "A piece of medical software is never finished. It accumulates "
        "improvements, absorbs regulatory changes, and outlasts the "
        "people who first shaped it. The MedPharm ERP codebase has "
        "already lived through more hands than one engineer could keep "
        "in memory; this manual is the artefact that allows the next "
        "hand to pick up where the previous one set the tools down.",
        styles))
    s.append(p(
        "Two manuals already attend to adjacent needs. Volume I "
        "(Technical Reference) describes the system as a finished "
        "artefact: its models, its routes, its contracts. Volume II "
        "(Service Manual) describes the system under an operator's "
        "care: its commissioning, its daily routines, its failure "
        "modes. Volume III is the inside-out companion to those two. "
        "It describes the system as a thing that was " + i("made") + " "
        "and can be " + i("made further") + ". Where the two earlier "
        "volumes assume the code is settled, Volume III assumes — "
        "correctly — that it is not.",
        styles))
    s.append(p(
        "The manual is written in the second person. When it says "
        "\"you\", it is addressing the engineer at the keyboard; when "
        "it says \"we\", it is describing a decision the project has "
        "made, not a royal plural. The tone is plain, the sentences "
        "are intentionally unadorned, and the code samples are real. "
        "Where a diagram helps, a diagram is drawn. Where a line of "
        "SQL is clearer than three paragraphs of prose, the SQL "
        "appears without apology.",
        styles))
    s.append(p(
        "Nothing in the pages that follow is closed to revision. If "
        "you find an inaccuracy, a gap, or an outright lie that the "
        "code has since corrected, please "
        + mail(label="write in") + " and the manual will be updated. A "
        "revision letter (1.7.6-A, 1.7.6-B, …) is appended for each "
        "re-issue, and a visible record appears in Appendix F.",
        styles))
    s.append(Spacer(1, 0.3 * inch))
    s.append(Paragraph(
        "<i>Robert Andrew Stillwell</i><br/>Enlightec Ltd.",
        ParagraphStyle("ForewordSig", parent=styles["Normal"],
                       fontName="Helvetica-Oblique", fontSize=10,
                       textColor=SLATE, alignment=TA_RIGHT)))
    s.append(PageBreak())
    return s


def build_how_to_use(styles):
    s = chapter_header("", "How to Use This Manual", styles)
    s.append(p(
        "The manual is written to support three reading strategies. "
        "A reader who adopts any one of them should find the pages "
        "cooperative.",
        styles))

    s.append(h2("Cover-to-cover as onboarding", styles))
    s.append(p(
        "A newly hired engineer should expect to spend three to five "
        "working days reading the manual end to end, pausing at each "
        "chapter to open the real files on disk and trace the code "
        "against the narrative. The parts are ordered with this path "
        "in mind — foundations first, then data, then backend, then "
        "clients, then cross-cutting concerns, then workflow. By the "
        "end of Part IV the reader has a working mental map of every "
        "user-facing surface; Parts V through VII are the operational "
        "cement that holds the surfaces to the backend.",
        styles))

    s.append(h2("As a reference", styles))
    s.append(p(
        "Once a reader has read the manual once, the table of contents "
        "becomes the primary index. Chapters are self-contained where "
        "possible; where a chapter depends on earlier material, the "
        "dependency is stated in the opening paragraph. The "
        "appendices — in particular the API endpoint catalogue and "
        "the file-by-file code tour — are designed to answer the "
        "\"where does the code live for X?\" question in under a "
        "minute.",
        styles))

    s.append(h2("Under change pressure", styles))
    s.append(p(
        "If you are about to land a substantial change — a new model, "
        "a new endpoint, a new client platform — consult Part VII "
        "(Extending MedPharm) before you start. The recipes there are "
        "written to prevent the specific mistakes that the project "
        "has already been burned by, and following them will save you "
        "from rediscovering those mistakes at code review.",
        styles))

    s.append(h2("A note on completeness", styles))
    s.append(p(
        "This document does not claim that every line of code is "
        "explained. It does claim that every "
        + i("non-obvious decision") + " is explained, and that a "
        "reader who has absorbed the manual can learn the rest by "
        "reading the code. Where you find yourself unable to bridge "
        "the gap between what the manual says and what the code "
        "does, treat that as a bug report and file it.",
        styles))

    s.append(PageBreak())
    return s


def build_conventions(styles):
    s = chapter_header("", "Conventions and Signal Words", styles)
    s.append(p(
        "Consistent typographic and editorial conventions are used "
        "throughout. Scanning a page should give a reliable first "
        "impression of its density and seriousness before a full "
        "read.",
        styles))

    s.append(h2("Typography", styles))
    s.append(p(
        f"Identifiers, filenames, environment variables, and HTTP "
        f"routes appear in a monospaced navy font — for example "
        f"{c('DatabaseManager')}, {c('api/routes.py')}, "
        f"{c('MEDPHARM_JWT_SECRET')}, or "
        f"{c('POST /api/v1/patient/messages')}. Longer listings are "
        f"set in a dark-backgrounded code block with line numbers, "
        f"and source language is indicated in the accompanying "
        f"caption where it is not obvious from context.",
        styles))
    s.append(p(
        f"Cross-references to other volumes appear as "
        f"{b('Vol. I &sect; 4.3')} or "
        f"{b('Vol. II Ch. 19')}. Internal cross-references use the "
        f"same shorthand without the volume prefix — "
        f"{b('Ch. 14')} means Chapter 14 of this manual.",
        styles))
    s.append(p(
        f"Hyperlinks are indigo and underlined — for example "
        f"{link(REPO_URL)} or {mail()}.  Hyperlinks are clickable in "
        f"PDF viewers that support them (Adobe Acrobat Reader, Apple "
        f"Preview, and most modern browsers do).",
        styles))

    s.append(h2("Signal Words", styles))
    s.append(p(
        "Four signal-word boxes appear throughout. Their meanings are "
        "precise; they are never substituted for emphasis.",
        styles))
    s.append(note(
        "A Note conveys useful but non-critical context. Skipping "
        "one will not cause harm; reading one often saves time.",
        styles))
    s.append(tip(
        "A Tip offers a non-obvious technique or shortcut that has "
        "been useful to previous engineers. Tips are optional but "
        "usually worth the thirty seconds they save.",
        styles))
    s.append(caution(
        "A Caution introduces information that, if ignored, will "
        "cause degraded behaviour or avoidable rework. No permanent "
        "damage is expected, but the affected engineer will wish "
        "they had read more carefully.",
        styles))
    s.append(danger(
        "A Danger introduces information that, if ignored, will "
        "cause data loss, security compromise, or other outcomes "
        "from which recovery is costly. Do not proceed past a "
        "Danger without understanding why it applies.",
        styles))

    s.append(h2("Verbs of Requirement", styles))
    s.append(p(
        f"The manual follows the common engineering convention under "
        f"which {b('must')} indicates a firm requirement, "
        f"{b('should')} indicates a strong recommendation whose "
        f"violation must be justified in writing, and {b('may')} "
        f"indicates a permissive option. {b('Must not')} and "
        f"{b('should not')} mirror their positive forms.",
        styles))

    s.append(h2("Time and Date Notation", styles))
    s.append(p(
        "All timestamps in log excerpts and examples use ISO 8601 "
        "with a timezone offset; when no offset is shown, UTC is "
        "assumed. Developers should configure their local machines "
        "to log in UTC — it simplifies correlation across the team "
        "and matches the convention used in production.",
        styles))
    s.append(PageBreak())
    return s


def build_toc(styles):
    s = [Spacer(1, 0.15 * inch)]
    s.append(Paragraph("Table of Contents", ParagraphStyle(
        "TOCTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=26, leading=30, textColor=NAVY, alignment=TA_LEFT,
        spaceAfter=18)))

    toc = [
        ("Front Matter", [
            "Document Control and Colophon",
            "Foreword",
            "How to Use This Manual",
            "Conventions and Signal Words",
        ]),
        ("Part I — Foundations", [
            "1. Project Vision and Problem Space",
            "2. Technology Stack and Its Rationale",
            "3. Architecture Overview",
            "4. Repository Layout and File Inventory",
        ]),
        ("Part II — The Data Model", [
            "5. Database Design Philosophy",
            "6. Core Domain Models",
            "7. Clinical Models",
            "8. Financial and Insurance Models",
            "9. HIPAA Compliance Models",
            "10. Messaging and Private Notes",
        ]),
        ("Part III — The Backend", [
            "11. The DatabaseManager",
            "12. Field-Level Encryption",
            "13. REST API Design",
            "14. JWT Authentication Flow",
            "15. CSRF, Lockout, and MFA",
            "16. The Flask Web Portal",
        ]),
        ("Part IV — The Clients", [
            "17. Qt6 Desktop Application",
            "18. Android (Kotlin / MVVM / Retrofit)",
            "19. iOS (SwiftUI / async-await)",
            "20. macOS (SwiftUI / NavigationSplitView)",
            "21. Windows (.NET 8 / WPF)",
        ]),
        ("Part V — Cross-Cutting Concerns", [
            "22. Audit Logging and PHI Access Trails",
            "23. TLS and Certificate Lifecycle",
            "24. Docker and Containerisation",
            "25. Kubernetes Deployment",
        ]),
        ("Part VI — Development Workflow", [
            "26. Setting Up a Development Environment",
            "27. Running Tests and Smoke Checks",
            "28. Branching, Commits, and Pull Requests",
            "29. Release Engineering",
            "30. Debugging Techniques and Tooling",
        ]),
        ("Part VII — Extending MedPharm", [
            "31. Recipe — Adding a New Model",
            "32. Recipe — Adding a New API Endpoint",
            "33. Recipe — Adding a New Clinical Module",
            "34. Recipe — Adding a New Client Platform",
        ]),
        ("Part VIII — Appendices", [
            "A. File-by-File Code Tour",
            "B. Complete SQL Schema",
            "C. API Endpoint Catalogue",
            "D. HTTP Error Codes and Meanings",
            "E. Glossary of Terms",
            "F. Revision History and Support",
        ]),
    ]

    for part, chapters in toc:
        s.append(Paragraph(part, styles["DM_TOCPart"]))
        for ch in chapters:
            s.append(Paragraph(ch, styles["DM_TOCChapter"]))
    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART I — FOUNDATIONS
# ═════════════════════════════════════════════════════════════════════════════

def chapter_01_vision(styles):
    s = chapter_header("1", "Project Vision and Problem Space", styles)
    s.append(p(
        "MedPharm ERP exists to fold the operational workload of a "
        "small-to-medium medical practice or retail pharmacy into a "
        "single coherent system. The alternative — which most such "
        "organisations live with — is a constellation of three to five "
        "uncoordinated applications: a patient record system that "
        "cannot speak to the billing system, a billing system whose "
        "insurance claims are exported by CSV to a third party, a "
        "pharmacy formulary that lives in a binder, and a scheduling "
        "tool whose access permissions are a spreadsheet in someone's "
        "inbox. Each of these gaps is a place where patient care or "
        "revenue quietly leaks away.",
        styles))
    s.append(p(
        "The product's ambition is therefore not cleverness but "
        "coherence. It does not attempt to out-feature the market "
        "leaders; instead it attempts to do a modest feature set "
        "well, on modest hardware, in a single SQLite database that "
        "an operator can back up with " + c("cp") + ". Every design "
        "decision in this manual should be read against that "
        "backdrop. Where a feature could be implemented in two ways "
        "and one of them requires a second daemon, the project "
        "chooses the one that does not.",
        styles))

    s.append(h2("Who uses MedPharm", styles))
    s.append(p(
        "Three classes of user interact with the running system. "
        "Clinical staff — doctors, psychiatrists, nurses, "
        "pharmacists, office managers, and administrators — use the "
        "PyQt6 desktop application as their primary workstation. "
        "Patients use the Flask web portal on a browser, or one of "
        "the native mobile clients (Android, iOS) or desktop clients "
        "(macOS, Windows) that connect to the cloud REST API. "
        "Operators and system administrators interact with the "
        "system through log files, the " + c("./install.sh") + " "
        "wrapper, Docker compose, and occasional direct SQL.",
        styles))
    s.append(p(
        "The four user-facing surfaces on the patient side share one "
        "backend. The clinical desktop application is unique in "
        "that it may bypass the HTTP API and speak directly to the "
        "SQLite database file — a deliberate choice to keep clinical "
        "latency low when the backend runs on the same machine. "
        "Chapter 3 expands on this topology, and Chapter 17 discusses "
        "its implications for feature development.",
        styles))

    s.append(h2("What MedPharm is not", styles))
    s.append(p(
        "It is useful to state the project's non-goals explicitly so "
        "that an engineer does not waste effort implementing the "
        "wrong thing in the right way. MedPharm is "
        + i("not") + " a hospital information system. It does not "
        "drive bedside monitors, does not negotiate with radiology "
        "PACS, and does not implement HL7 v2 messaging. It is "
        + i("not") + " a multi-tenant SaaS platform — a single "
        "database serves a single practice, and any attempt to run "
        "several databases through one Flask worker is unsupported. "
        "It is " + i("not") + " a research platform — the schema "
        "reflects the needs of clinical operation, not statistical "
        "research, and bulk de-identified exports are out of scope.",
        styles))

    s.append(h2("Where the name comes from", styles))
    s.append(p(
        "\"MedPharm\" is the portmanteau of " + i("medical") + " and "
        + i("pharmaceutical") + ". The project was scoped from the "
        "outset to serve both clinic-side (patient care, scheduling) "
        "and pharmacy-side (dispensing, drug interactions, NDC code "
        "management) workflows within one data model. This is why "
        "the Medication and Prescription models are first-class "
        "citizens rather than appendages — they predate some of the "
        "clinical tables by several design iterations.",
        styles))

    s.append(h2("Regulatory context", styles))
    s.append(p(
        "MedPharm stores protected health information and is "
        "therefore subject to HIPAA's Privacy Rule (45 CFR Part 164, "
        "Subpart E) and Security Rule (Subpart C). The engineering "
        "implications are far-reaching: role-based access control, "
        "audit logging of every PHI touch, encryption at rest for "
        "sensitive fields, transmission security over TLS, breach "
        "notification procedures, and a Security Officer role. The "
        "specific models and code paths that support each of these "
        "requirements are catalogued in Chapter 9; the broader "
        "compliance posture is the subject of the companion "
        + b("HIPAA_COMPLIANCE.md") + " document in "
        + c("docs/") + ".",
        styles))
    s.append(note(
        "HIPAA is the baseline. Deployments outside the United "
        "States may be subject to GDPR (European Union), PIPEDA "
        "(Canada), or comparable local regimes. The code is written "
        "defensively enough that most of these regimes can be "
        "satisfied with configuration rather than code changes, but "
        "the work of mapping the controls is the deploying "
        "organisation's responsibility.",
        styles))

    s.append(h2("A brief history", styles))
    s.append(p(
        "The project began as a PyQt proof-of-concept in 2024, "
        "acquired a Flask web portal a month later, grew a Cloud "
        "REST API when mobile clients were added, and reached "
        "multi-platform parity with the 1.7.x line in early 2026. "
        "The HIPAA-compliance features, TLS-by-default, and secure "
        "messaging were folded in during the 1.6 → 1.7 transition. "
        "The most recent substantial addition is the private "
        "provider-notes feature described in Chapter 10.",
        styles))

    s.append(PageBreak())
    return s


def chapter_02_stack(styles):
    s = chapter_header("2", "Technology Stack and Its Rationale", styles)
    s.append(p(
        "Every technology choice in MedPharm answers to three "
        "constraints: it must be operable by a single System "
        "Operator, it must store PHI safely, and it must be "
        "buildable in a container in under ten minutes. Those three "
        "constraints alone eliminate most of the fashionable options "
        "of the last decade. What survives is a short list of tools "
        "that favour clarity, longevity, and first-party "
        "documentation.",
        styles))

    s.append(h2("The backend", styles))
    s.append(make_table(
        ["Layer", "Tool", "Version", "Rationale"],
        [
            ["Language", "Python", "3.10+",
             "Mature type hints, wide library surface, engineering staff "
             "overlap with data-science backgrounds."],
            ["Web framework", "Flask", "3.0+",
             "Minimal; readable routing table; no baked-in assumptions "
             "that conflict with clinical workflows."],
            ["ORM", "SQLAlchemy", "2.0+",
             "Mapped-dataclass style, clear session lifecycle, supports "
             "the eventual Postgres migration should scaling demand it."],
            ["Database", "SQLite", "3.40+",
             "One file; no separate daemon; no attack surface at the "
             "storage layer; WAL mode gives acceptable concurrency."],
            ["Password hashing", "Werkzeug / PBKDF2-SHA256", "3.0+",
             "Deterministic, FIPS-track, ships with Flask ecosystem."],
            ["Symmetric encryption", "cryptography / Fernet", "46+",
             "AES-128-CBC + HMAC-SHA256, industry-standard authenticated "
             "encryption for PHI fields at rest."],
            ["JWT signing", "stdlib hmac + hashlib", "—",
             "Handwritten to avoid third-party JWT libraries' key "
             "confusion vulnerabilities; payload is a subset of RFC 7519."],
            ["WSGI server", "gunicorn (gevent worker)", "21.2+",
             "Battle-tested, simple configuration, ships in Ubuntu 24.04 "
             "repositories."],
            ["Reverse proxy", "Nginx", "1.24+",
             "TLS termination, HTTP/2, tight request-size limits, wide "
             "operator familiarity."],
        ],
        col_widths=[1.1 * inch, 1.4 * inch, 0.8 * inch, 3.1 * inch]))

    s.append(h2("The clients", styles))
    s.append(make_table(
        ["Platform", "Language", "Frameworks", "Target"],
        [
            ["Clinical desktop", "Python 3.10+", "PyQt6",
             "Any OS with a display server"],
            ["Web portal (patients)", "Python 3.10+", "Flask + Jinja2",
             "Modern browsers; Bootstrap 5 UI"],
            ["Android (patients)", "Kotlin 1.9+",
             "MVVM, Retrofit, OkHttp, Coroutines, EncryptedSharedPreferences",
             "API level 26+ (Android 8.0+)"],
            ["iOS (patients)", "Swift 5.9+",
             "SwiftUI, async/await, Keychain Services",
             "iOS 16+"],
            ["macOS", "Swift 5.9+",
             "SwiftUI, NavigationSplitView",
             "macOS 13+"],
            ["Windows", "C# / .NET 8",
             "WPF, CommunityToolkit.Mvvm, DPAPI",
             "Windows 10 1809+"],
        ],
        col_widths=[1.3 * inch, 1.0 * inch, 2.6 * inch, 1.5 * inch]))

    s.append(h2("Why not newer, more fashionable choices", styles))
    s.append(p(
        "The project deliberately declined several popular options. "
        "Django was considered in place of Flask but rejected for its "
        "size — most of Django is unused here, and its ORM would have "
        "duplicated SQLAlchemy rather than cooperated with it. "
        "PostgreSQL was considered in place of SQLite and remains "
        "the likely migration target if throughput ever demands it, "
        "but at current load SQLite's single-writer limitation is "
        "not the bottleneck — a small clinic sees perhaps two writes "
        "per second at peak — and the operational simplicity of one "
        "file is worth a great deal. Redis for session storage was "
        "considered and rejected because Flask's default signed-"
        "cookie session is sufficient and Redis would be another "
        "daemon to monitor.",
        styles))
    s.append(p(
        "On the client side, Flutter and React Native were both "
        "rejected in favour of native UI toolkits on each platform. "
        "The reasoning is not aesthetic — cross-platform toolkits "
        "can ship acceptable UI — but operational: a native client "
        "in SwiftUI or Jetpack Compose will run correctly on devices "
        "that the cross-platform runtime has already abandoned, and "
        "medical device fleets are notoriously long-lived. The "
        "engineering cost of maintaining four separate codebases is "
        "the price the project pays for that longevity.",
        styles))

    s.append(h2("Operating system targets", styles))
    s.append(p(
        "The backend is supported on Ubuntu Server 24.04 LTS as the "
        "primary target and on Fedora, RHEL, Debian, Arch, and "
        "macOS as best-effort secondary targets. The Docker images "
        "are built on Ubuntu 24.04 LTS. The install script detects "
        "the operating system and adjusts package manager "
        "invocations accordingly; see Chapter 26 for details.",
        styles))

    s.append(PageBreak())
    return s


def chapter_03_architecture(styles):
    s = chapter_header("3", "Architecture Overview", styles)
    s.append(p(
        "MedPharm's architecture is a hub-and-spoke with one "
        "privileged local spoke. The hub is a Flask REST API "
        "("
        + c("/api/v1/*") + ") backed by the SQLAlchemy-managed "
        "SQLite database. Five of the six user-facing surfaces reach "
        "the hub over TLS. The sixth — the PyQt desktop — bypasses "
        "the HTTP layer entirely and speaks to the same database "
        "file through the in-process DatabaseManager. This diagram "
        "is worth memorising.",
        styles))

    # Architecture flowchart
    nodes_arch = [
        {"id": "api", "label": "Flask REST API", "x": 3.2, "y": 2.4,
         "w": 2.2, "h": 0.7, "fill": INDIGO, "text_color": colors.white,
         "stroke": NAVY},
        {"id": "db", "label": "SQLite DB (WAL)", "x": 3.2, "y": 0.8,
         "w": 2.2, "h": 0.7, "fill": NAVY, "text_color": colors.white,
         "stroke": NAVY_LIGHT},
        {"id": "dbm", "label": "DatabaseManager", "x": 0.9, "y": 1.6,
         "w": 1.5, "h": 0.55, "fill": MOSS_PALE, "stroke": MOSS},
        {"id": "qt", "label": "PyQt Desktop", "x": 0.9, "y": 3.6,
         "w": 1.5, "h": 0.55},
        {"id": "web", "label": "Flask Portal", "x": 5.5, "y": 3.6,
         "w": 1.5, "h": 0.55},
        {"id": "android", "label": "Android", "x": 0.9, "y": 4.6,
         "w": 1.2, "h": 0.5},
        {"id": "ios", "label": "iOS", "x": 2.3, "y": 4.6,
         "w": 1.0, "h": 0.5},
        {"id": "mac", "label": "macOS", "x": 3.7, "y": 4.6,
         "w": 1.2, "h": 0.5},
        {"id": "win", "label": "Windows", "x": 5.3, "y": 4.6,
         "w": 1.3, "h": 0.5},
        {"id": "nginx", "label": "Nginx (TLS)", "x": 3.2, "y": 3.6,
         "w": 1.6, "h": 0.55, "fill": AMBER_PALE, "stroke": AMBER},
    ]
    edges_arch = [
        {"from": "qt", "to": "dbm", "label": "direct"},
        {"from": "dbm", "to": "db"},
        {"from": "android", "to": "nginx", "label": "HTTPS"},
        {"from": "ios", "to": "nginx", "label": "HTTPS"},
        {"from": "mac", "to": "nginx", "label": "HTTPS"},
        {"from": "win", "to": "nginx", "label": "HTTPS"},
        {"from": "web", "to": "nginx"},
        {"from": "nginx", "to": "api"},
        {"from": "api", "to": "db"},
    ]
    s.append(Flowchart(nodes_arch, edges_arch, width=7.0, height=5.2,
                       caption=("Fig. 3-1. Deployment topology. Solid arrows are synchronous "
                                "calls; the DatabaseManager is in-process on the clinical desktop.")))
    s.append(Spacer(1, 0.3 * inch))

    s.append(h2("Layers of the backend", styles))
    s.append(p(
        "Inside the Flask process, a request travels through four "
        "discrete layers. Each layer has a clear responsibility and "
        "a single upstream dependency.",
        styles))
    s.append(bullets([
        b("Blueprint routing") + " — "
        + c("api_bp") + " in " + c("api/routes.py") + " maps URL "
        "patterns to handler functions. This layer is thin by design; "
        "it parses request bodies, applies auth decorators, and "
        "returns JSON.",
        b("Authentication") + " — "
        + c("@token_required") + ", "
        + c("@patient_required") + ", "
        + c("@staff_required") + " decorators in " + c("api/auth.py")
        + " verify the bearer token and populate "
        + c("g.current_user_type") + ", "
        + c("g.current_user_id") + ", and related request-scoped "
        "variables.",
        b("Business logic") + " — the body of each route function "
        "calls methods on " + c("g.db_manager") + " (attached to "
        "Flask's request-scoped " + c("g") + " object by the "
        "application factory).",
        b("Persistence") + " — the " + c("DatabaseManager") + " "
        "opens a SQLAlchemy session, performs the reads or writes, "
        "and commits. Sessions never outlive the request.",
    ], styles))

    s.append(h2("Request lifecycle — a worked example", styles))
    s.append(p(
        "Consider a patient opening their prescription list in the "
        "Android app. The following sequence occurs:",
        styles))
    s.append(bullets([
        "The Android " + c("PrescriptionsViewModel") + " calls "
        + c("repository.getPatientPrescriptions(null)") + ", which "
        "invokes the Retrofit interface method "
        + c("api.getPrescriptions(null)") + ".",
        "OkHttp adds the " + c("Authorization: Bearer …") + " header "
        "via " + c("AuthInterceptor") + " and performs an HTTPS "
        "GET to " + c("/api/v1/patient/prescriptions") + ".",
        "Nginx terminates TLS and proxies the request to "
        + c("gunicorn") + " on the loopback interface.",
        "Flask dispatches to " + c("patient_prescriptions()") + " in "
        + c("api/routes.py") + ", whose "
        + c("@patient_required") + " decorator verifies the JWT and "
        "populates " + c("g.current_patient_id") + ".",
        "The route calls "
        + c("g.db_manager.get_prescriptions_by_patient(pid)") + ", "
        "which opens a session, eagerly loads related "
        + c("PrescriptionItem") + " and " + c("Medication") + " "
        "rows, and returns a list of dicts.",
        "The response is serialised with "
        + c("flask.jsonify") + " and returned through the inverse "
        "path.",
    ], styles))

    s.append(h2("The DatabaseManager as seam", styles))
    s.append(p(
        "Two components talk to the DatabaseManager: the REST API "
        "and the PyQt desktop. Neither component cares about SQL or "
        "about how sessions are scoped — they both see an object "
        "with a long list of methods like "
        + c("get_patient_full(patient_id)") + ", "
        + c("create_prescription(...)") + ", and "
        + c("process_insurance_payment(...)") + ". This is the "
        "single most important architectural seam in the project. "
        "Business logic added in the DatabaseManager benefits both "
        "surfaces simultaneously; conversely, business logic added "
        "only in a route function or only in a Qt widget will skew "
        "the two surfaces apart over time. Chapter 11 discusses this "
        "at length, and Chapter 31 formalises the pattern as a "
        "recipe.",
        styles))

    s.append(tip(
        "When in doubt, put the logic in the DatabaseManager. If "
        "it turns out that only one surface needed it, the cost is "
        "one unused method; if both surfaces needed it, the cost "
        "of having put it in only one of them is a subtle "
        "divergence that someone has to untangle later.",
        styles))

    s.append(PageBreak())
    return s


def chapter_04_layout(styles):
    s = chapter_header("4", "Repository Layout and File Inventory", styles)
    s.append(p(
        "A newly checked-out repository has a root directory that "
        "looks busier than it is. Most of the files at the top level "
        "are launchers, installers, or container metadata; the real "
        "code lives in a small number of subdirectories. This "
        "chapter provides the map.",
        styles))

    s.append(h2("Top-level files", styles))
    s.append(make_table(
        ["File", "Purpose"],
        [
            ["run_qt.py", "Clinical desktop application entry point."],
            ["run_web.py", "Flask web portal entry point."],
            ["run_cloud.py", "Flask REST API entry point."],
            ["install.sh", "OS-detection installer. Handles source install, "
                           "virtualenv, Docker-only, or full-stack Docker."],
            ["uninstall.sh", "Reverses everything install.sh creates. "
                             "Never touches tracked source files."],
            ["start_desktop.sh", "Quick-launch wrapper for the Qt app."],
            ["start_web.sh", "Quick-launch wrapper for the Flask portal."],
            ["start_cloud.sh", "Quick-launch wrapper for the API server."],
            ["start_docker_hub.sh", "Interactive Docker Hub launcher — "
                                    "pull, start, stop, choose tag."],
            ["generate_docs.sh", "Regenerates the Volume I PDF. See also "
                                 "docs/generate_service_manual.py and "
                                 "docs/generate_developer_manual.py."],
            ["requirements.txt", "Qt + web portal dependencies."],
            ["requirements-cloud.txt", "Cloud API dependencies."],
            ["Dockerfile", "API-only image (Ubuntu 24.04 base)."],
            ["docker-compose.yml", "Build-from-source Docker Compose file."],
            ["docker-compose.hub.yml", "Pull-from-Docker-Hub Compose file."],
            ["LICENSE", "GNU General Public License v3.0."],
        ],
        col_widths=[2.2 * inch, 4.2 * inch]))

    s.append(h2("Top-level directories", styles))
    s.append(make_table(
        ["Directory", "Contents"],
        [
            ["database/",
             "models.py (all ORM classes and enums), db_manager.py "
             "(the DatabaseManager), seed_data.py, seed_expanded.py."],
            ["api/",
             "app.py (application factory), auth.py (JWT + decorators), "
             "routes.py (all /api/v1/* endpoints), fhir.py (FHIR R4 adapter)."],
            ["qt_app/",
             "main_window.py, styles.py, dialogs/login_dialog.py, and "
             "widgets/ containing one widget per navigation destination."],
            ["web/",
             "app.py, routes.py, static/ (CSS, JS, vendored assets), "
             "templates/ (Jinja2 HTML)."],
            ["security/",
             "encryption.py (Fernet), audit.py, csrf.py, lockout.py, "
             "sessions.py, passwords.py, totp.py, phi.py, emergency.py, "
             "config.py."],
            ["android/",
             "Gradle project. Kotlin sources under "
             "app/src/main/java/com/enlightec/medpharm/."],
            ["ios/, macos/",
             "Xcode projects. Swift sources under "
             "MedPharm/MedPharm/{Models,Services,Views}/."],
            ["windows/",
             ".NET 8 WPF project. Sources under MedPharm/."],
            ["server/",
             "Full-stack Docker package — Dockerfile, supervisord.conf, "
             "nginx/ configs, entrypoint.sh."],
            ["k8s/",
             "Kustomize manifests with cloud-specific overlays (gcp, aws, "
             "generic). medpharm-k8s.sh wrapper."],
            ["docs/",
             "Three PDF generators (generate_pdf.py, "
             "generate_service_manual.py, generate_developer_manual.py) "
             "and Markdown source for HIPAA, installation, API, "
             "Kubernetes, compilation, and client docs."],
            [".github/workflows/",
             "docker-publish.yml — builds and pushes container images on "
             "tagged releases."],
        ],
        col_widths=[1.2 * inch, 5.2 * inch]))

    s.append(h2("Reading order for a new engineer", styles))
    s.append(p(
        "If you are opening the repository for the first time, the "
        "following order will map the territory fastest. Each file "
        "sets up the next.",
        styles))
    s.append(bullets([
        c("database/models.py") + " — all of the data the system "
        "stores.",
        c("database/db_manager.py") + " (skim) — methods grouped by "
        "domain; no need to read every CRUD, just note the grouping.",
        c("api/app.py") + " — the application factory. Shows how "
        "security middleware is wired and where " + c("g.db_manager")
        + " comes from.",
        c("api/auth.py") + " — the JWT implementation and the three "
        "access decorators.",
        c("api/routes.py") + " — skim; note the blueprint structure "
        "and that most routes are one or two lines of logic over a "
        "DatabaseManager call.",
        c("qt_app/main_window.py") + " — the window's navigation "
        "skeleton. Each widget is independently readable.",
        c("web/routes.py") + " — the patient portal. Flask-session "
        "based rather than JWT.",
        c("install.sh") + " — the operator's front door. Reading "
        "this file clarifies how the pieces fit together.",
    ], styles))

    s.append(tip(
        "Every one of those files has been kept readable at human "
        "scale — the largest is under a thousand lines. If a file "
        "starts creeping past 1,500 lines during your work, that is "
        "a signal to break it up, not a reason to keep adding.",
        styles))

    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART II — THE DATA MODEL
# ═════════════════════════════════════════════════════════════════════════════

def chapter_05_db_philosophy(styles):
    s = chapter_header("5", "Database Design Philosophy", styles)
    s.append(p(
        "Before any individual model is examined, it is worth "
        "articulating the design axioms that produced them. An "
        "engineer who understands why the schema is shaped the way "
        "it is will make fewer mistakes when extending it.",
        styles))

    s.append(h2("Axiom 1 — One source of truth", styles))
    s.append(p(
        "Every fact about a patient, prescription, or invoice lives "
        "in exactly one column on exactly one table. When a fact "
        "must be derived (age from date of birth, balance due from "
        "total minus payments), it is computed at read time or "
        "exposed as a Python property on the model. Denormalised "
        "copies exist only for legitimate performance reasons and "
        "are marked as such in code comments.",
        styles))

    s.append(h2("Axiom 2 — Soft delete over hard delete", styles))
    s.append(p(
        "Clinical records must not vanish. Patient rows are "
        "deactivated rather than deleted (" + c("is_active=False") + "); "
        "prescriptions are cancelled rather than removed; invoices "
        "are voided. Hard deletes are reserved for two cases: "
        "transient cache-like rows (failed login attempts, expired "
        "TOTP challenges), and rows that never contained PHI "
        "(session tokens in the Flask session store).",
        styles))

    s.append(h2("Axiom 3 — Enums for finite state", styles))
    s.append(p(
        "Any column whose values are constrained to a small set is "
        "modelled as a Python " + c("enum.Enum") + " subclass and "
        "stored via SQLAlchemy's " + c("Enum") + " type. Eighteen "
        "such enums appear in the schema. Using native strings in "
        "new code is an anti-pattern that has been systematically "
        "removed; do not reintroduce it.",
        styles))
    s.extend(code_block("""class PrescriptionStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(PrescriptionStatus),
                    default=PrescriptionStatus.PENDING,
                    nullable=False)
    # … other fields …""",
        language="python",
        caption="Listing 5-1. Finite-state columns use Python enums, never raw strings."))

    s.append(h2("Axiom 4 — Relationships are explicit", styles))
    s.append(p(
        "Every " + c("ForeignKey") + " is accompanied by an "
        "explicit " + c("relationship()") + " on both sides. Lazy "
        "loading is the default; eager loading is opt-in per query "
        "via " + c("joinedload()") + " or "
        + c("selectinload()") + ". The reason for this explicitness "
        "is defensive: N+1 query problems are easy to introduce and "
        "hard to spot in clinical software, so the project prefers "
        "predictable lazy-by-default with visible eager decisions "
        "to the inverse.",
        styles))

    s.append(h2("Axiom 5 — PHI is named, tracked, and encrypted "
                "when it cannot be keyed", styles))
    s.append(p(
        "Columns that contain protected health information are "
        "catalogued in " + c("security/phi.py") + ". Where a PHI "
        "column must be queryable (patient name, date of birth), "
        "it is stored as plaintext and protected by access control "
        "and audit logging. Where a PHI column is free-form and "
        "unlikely to be queried (provider-note bodies, secure "
        "message contents), it is stored as Fernet ciphertext. "
        "Chapter 12 gives the cryptographic details.",
        styles))

    s.append(h2("Axiom 6 — Timestamps in UTC", styles))
    s.append(p(
        "All timestamp columns default to "
        + c("datetime.utcnow()") + ". Timezone conversion is the "
        "client's concern. This axiom was violated exactly once in "
        "the project's history, discovered during an incident, and "
        "the resulting cleanup took long enough that it will not be "
        "violated again.",
        styles))

    s.append(h2("Axiom 7 — Migrations are schema evolutions, never "
                "data pivots", styles))
    s.append(p(
        "SQLAlchemy's " + c("Base.metadata.create_all()") + " is "
        "used for schema creation. Migrations of existing "
        "deployments are currently performed manually — SQLite's "
        "limitations on " + c("ALTER TABLE") + " make automated "
        "migration fragile. If you are adding a column to an "
        "existing table, produce both a model-level change and a "
        "one-off migration SQL file in " + c("docs/migrations/") + " "
        "with the convention " + c("YYYYMMDD_description.sql") + ".",
        styles))

    s.append(h2("Axiom 8 — The ORM is the contract, the SQL is the "
                "implementation", styles))
    s.append(p(
        "Direct SQL against the database is allowed in exactly two "
        "contexts: the seed scripts (" + c("database/seed_data.py")
        + ") and operator-invoked maintenance from the Service "
        "Manual (Vol. II, Chapter 18). Production code paths read "
        "and write through the ORM so that constraints, enums, and "
        "relationship mappings are honoured.",
        styles))

    s.append(PageBreak())
    return s


def chapter_06_core_models(styles):
    s = chapter_header("6", "Core Domain Models", styles)
    s.append(p(
        "The core models are the ones every other table eventually "
        "refers to: " + c("User") + ", " + c("Patient") + ", "
        + c("PatientPortalAccount") + ", and " + c("Insurance") + ". "
        "A reader who understands these four tables has the skeleton "
        "for everything that follows.",
        styles))

    s.append(h2("User — clinical staff", styles))
    s.append(p(
        "The " + c("User") + " table holds every staff account. The "
        "role column is an enum and governs access control "
        "throughout the system.",
        styles))
    s.extend(code_block("""class UserRole(enum.Enum):
    DOCTOR = "doctor"
    PSYCHIATRIST = "psychiatrist"
    PHARMACIST = "pharmacist"
    NURSE = "nurse"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    phone = Column(String(20))
    license_number = Column(String(50))
    specialization = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    vitals_recorded = relationship("Vital", back_populates="recorded_by")
    diagnoses_made = relationship("Diagnosis", back_populates="diagnosed_by")
    medical_records = relationship("MedicalRecord", back_populates="provider")
    prescriptions_written = relationship("Prescription", back_populates="prescriber")
    appointments = relationship("Appointment", back_populates="provider")
    audit_logs = relationship("AuditLog", back_populates="user")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def display_title(self):
        if self.role in (UserRole.DOCTOR, UserRole.PSYCHIATRIST):
            return f"Dr. {self.last_name}"
        return self.full_name""",
        language="python",
        caption="Listing 6-1. database/models.py — User model (extract)."))

    s.append(note(
        "The " + c("display_title") + " property is the canonical "
        "way to format a provider's name in UI. Any view that writes "
        "\"Dr. \" in front of a user's name on its own is a bug — "
        "admins and nurses should not get the title.",
        styles))

    s.append(h2("Patient — the centre of the domain", styles))
    s.append(p(
        "The " + c("Patient") + " table is the hub of nearly every "
        "clinical relationship. Its columns are deliberately flat — "
        "demographics, a small number of medical flags, emergency "
        "contact — with related information pushed out into "
        "dedicated tables (Insurance, Allergy, Vital, Diagnosis, "
        "and so on).",
        styles))
    s.extend(code_block("""class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(Enum(Gender))
    ssn_last4 = Column(String(4))
    email = Column(String(200))
    phone = Column(String(20))
    address = Column(String(300))
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    blood_type = Column(Enum(BloodType))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_patients_name", "last_name", "first_name"),
    )""",
        language="python",
        caption="Listing 6-2. database/models.py — Patient (demographics)."))

    s.append(h2("PatientPortalAccount — separate from Patient", styles))
    s.append(p(
        "A patient's identity (demographic row) and their portal "
        "login credential are deliberately separate rows in separate "
        "tables. Not every patient has a portal account — many are "
        "elderly, paediatric, or simply uninterested — and a single "
        "portal account is tied to a single patient row. This keeps "
        "the demographics table free of authentication concerns and "
        "allows portal credentials to be deactivated without "
        "affecting the clinical chart.",
        styles))
    s.extend(code_block("""class PatientPortalAccount(Base):
    __tablename__ = "patient_portal_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"),
                        unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    patient = relationship("Patient", backref="portal_account")""",
        language="python",
        caption="Listing 6-3. Portal account — one-to-one with Patient."))

    s.append(h2("Insurance — multi-row per patient", styles))
    s.append(p(
        "Patients frequently carry more than one insurance plan "
        "(primary and secondary are common; Medicare plus "
        "supplemental plans add a third). The " + c("Insurance")
        + " table therefore lives in a one-to-many relationship with "
        + c("Patient") + ". Each row describes one policy. When a "
        "claim is filed, the insurance row is referenced directly; "
        "see Chapter 8 for the claim workflow.",
        styles))
    s.extend(code_block("""class CoverageType(enum.Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class Insurance(Base):
    __tablename__ = "insurance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_name = Column(String(200), nullable=False)
    policy_number = Column(String(100), nullable=False)
    group_number = Column(String(100))
    coverage_type = Column(Enum(CoverageType),
                           default=CoverageType.PRIMARY)
    copay_amount = Column(Numeric(10, 2), default=0)
    deductible = Column(Numeric(10, 2), default=0)
    effective_date = Column(Date)
    expiry_date = Column(Date)
    is_active = Column(Boolean, default=True)

    patient = relationship("Patient", back_populates="insurance_records")""",
        language="python",
        caption="Listing 6-4. Insurance records belong to a Patient; a patient may have several."))

    s.append(PageBreak())
    return s


def chapter_07_clinical_models(styles):
    s = chapter_header("7", "Clinical Models", styles)
    s.append(p(
        "The clinical models represent the day-to-day output of "
        "medical work: vitals observed, diagnoses made, prescriptions "
        "written, appointments kept, records filed. Each has its own "
        "table; each refers to " + c("Patient") + " (the subject) "
        "and " + c("User") + " (the clinician responsible).",
        styles))

    s.append(h2("Medication — the formulary", styles))
    s.append(p(
        "The " + c("Medication") + " table is the system's "
        "reference formulary. At seed time it holds 75+ drugs with "
        "NDC codes, drug classes, DEA schedules, and pricing. It is "
        "intentionally static — drugs are not patient-specific. "
        "Medication rows are referenced by " + c("PrescriptionItem")
        + " and by the drug-interaction table.",
        styles))
    s.extend(code_block("""class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=False, index=True)
    ndc_code = Column(String(20), unique=True, index=True)
    drug_class = Column(String(100), index=True)
    dea_schedule = Column(Enum(DrugSchedule), default=DrugSchedule.NONE)
    form = Column(Enum(DrugForm))
    route = Column(Enum(DrugRoute))
    strength = Column(String(100))
    manufacturer = Column(String(200))
    unit_price = Column(Numeric(10, 2), default=0)
    description = Column(Text)
    indications = Column(Text)
    contraindications = Column(Text)
    side_effects = Column(Text)
    is_active = Column(Boolean, default=True)""",
        language="python",
        caption="Listing 7-1. Medication — a catalogue row, not a patient-scoped fact."))

    s.append(h2("Prescription and PrescriptionItem — the two-level "
                "structure", styles))
    s.append(p(
        "A prescription is a header (patient, prescriber, status, "
        "date, notes) that carries one or more line items (specific "
        "medications, dosages, quantities, refills). This two-level "
        "structure follows the invoice pattern described in "
        "Chapter 8 and makes it natural to add a second medication "
        "to an existing script.",
        styles))
    s.extend(code_block("""class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rx_number = Column(String(30), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescriber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(PrescriptionStatus),
                    default=PrescriptionStatus.PENDING)
    prescribed_date = Column(Date, default=date.today)
    expiry_date = Column(Date)
    notes = Column(Text)

    patient = relationship("Patient", back_populates="prescriptions")
    prescriber = relationship("User", back_populates="prescriptions_written")
    items = relationship("PrescriptionItem", back_populates="prescription",
                         cascade="all, delete-orphan")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"),
                             nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"),
                           nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    refills_allowed = Column(Integer, default=0)
    refills_used = Column(Integer, default=0)
    instructions = Column(Text)

    prescription = relationship("Prescription", back_populates="items")
    medication = relationship("Medication")""",
        language="python",
        caption="Listing 7-2. Prescription two-level structure."))

    s.append(h2("Drug-drug interaction checking", styles))
    s.append(p(
        "The " + c("MedicationInteraction") + " table is a "
        "many-to-many bridge between two " + c("Medication") + " "
        "rows, annotated with a severity enum and a human-readable "
        "description. When a prescription is saved, the "
        + c("DatabaseManager") + " checks every pair of items "
        "against this table and surfaces any matches to the UI. "
        "The table ships with 24 common pairs from the FDA adverse "
        "event database; adding new pairs is an ordinary data-"
        "maintenance task.",
        styles))

    s.append(h2("Appointment", styles))
    s.append(p(
        "Appointments attach to a provider and a patient with a "
        "scheduled datetime and duration, and progress through a "
        "small state machine: "
        + c("SCHEDULED") + " → "
        + c("CONFIRMED") + " → "
        + c("CHECKED_IN") + " → "
        + c("IN_PROGRESS") + " → "
        + c("COMPLETED") + ". Alternate exits "
        + c("CANCELLED") + " and " + c("NO_SHOW") + " terminate "
        "the state machine early. The Qt Appointments widget and "
        "the patient-side mobile clients render the same underlying "
        "state machine differently but agree on the transitions.",
        styles))

    # Flowchart: appointment state machine
    nodes_appt = [
        {"id": "sch", "label": "SCHEDULED", "x": 0.9, "y": 3.2, "fill": NAVY_PALE},
        {"id": "cfm", "label": "CONFIRMED", "x": 2.8, "y": 3.2, "fill": NAVY_PALE},
        {"id": "ci", "label": "CHECKED_IN", "x": 4.7, "y": 3.2, "fill": NAVY_PALE},
        {"id": "ip", "label": "IN_PROGRESS", "x": 6.2, "y": 3.2, "fill": INDIGO_PALE},
        {"id": "done", "label": "COMPLETED", "x": 6.2, "y": 1.5, "fill": MOSS_PALE, "stroke": MOSS},
        {"id": "cx", "label": "CANCELLED", "x": 2.8, "y": 1.5, "fill": AMBER_PALE, "stroke": AMBER},
        {"id": "ns", "label": "NO_SHOW", "x": 4.7, "y": 1.5, "fill": CRIMSON_PALE, "stroke": CRIMSON},
    ]
    edges_appt = [
        {"from": "sch", "to": "cfm", "label": "confirm"},
        {"from": "cfm", "to": "ci", "label": "arrive"},
        {"from": "ci", "to": "ip", "label": "start"},
        {"from": "ip", "to": "done", "label": "finish"},
        {"from": "sch", "to": "cx", "label": "cancel", "style": "dashed"},
        {"from": "cfm", "to": "cx", "style": "dashed"},
        {"from": "cfm", "to": "ns", "label": "timeout", "style": "dashed"},
        {"from": "ci", "to": "ns", "style": "dashed"},
    ]
    s.append(Flowchart(nodes_appt, edges_appt, width=7.0, height=4.0,
                       caption="Fig. 7-1. Appointment status transitions. Dashed edges are alternate exits."))
    s.append(Spacer(1, 0.3 * inch))

    s.append(h2("MedicalRecord", styles))
    s.append(p(
        "MedicalRecord is a generic container for clinical "
        "documentation — visit notes, lab results, imaging reports, "
        "procedure summaries, referrals. The " + c("record_type")
        + " enum differentiates them, and the content column holds "
        "free text (which may be markdown-formatted). Because this "
        "table can hold PHI that the patient is allowed to see "
        "(records are rendered in the patient portal), the content "
        "is stored as plaintext — encrypting it would make the "
        "portal unable to render it without a decryption key on "
        "the web side, and that is a larger risk surface than the "
        "existing access-control model solves.",
        styles))

    s.append(h2("Allergy, Vital, Diagnosis", styles))
    s.append(p(
        "These three tables all hang off " + c("Patient") + ", are "
        "appended to rather than overwritten, and carry a timestamp "
        "of when the observation was made and a foreign key to the "
        "recording user. They are rendered as history lists in the "
        "Qt desktop's patient detail panel and are available through "
        "the patient-detail REST endpoint.",
        styles))
    s.append(note(
        "Never write over an old Vital row when new vitals are "
        "taken. Insert a new row. The history matters.",
        styles))

    s.append(PageBreak())
    return s


def chapter_08_financial_models(styles):
    s = chapter_header("8", "Financial and Insurance Models", styles)
    s.append(p(
        "Financial state in MedPharm follows the invoice/payment "
        "pattern standard in small-business accounting. Four tables "
        "carry the burden: " + c("Invoice") + ", "
        + c("InvoiceItem") + ", " + c("Payment") + ", and "
        + c("InsuranceClaim") + ". Each invoice belongs to a patient; "
        "payments and claims both accrete against an invoice; an "
        "approved claim produces a payment row automatically.",
        styles))

    s.append(h2("Invoice and InvoiceItem", styles))
    s.append(p(
        "The relationship is the same two-level structure used for "
        "prescriptions. The header holds the patient, dates, status, "
        "and aggregated money fields; the item table holds individual "
        "charges with a unit price and quantity.",
        styles))
    s.extend(code_block("""class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(30), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    invoice_date = Column(Date, default=date.today)
    due_date = Column(Date)
    total_amount = Column(Numeric(10, 2), default=0)
    amount_paid = Column(Numeric(10, 2), default=0)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    notes = Column(Text)

    patient = relationship("Patient", back_populates="invoices")
    prescription = relationship("Prescription")
    items = relationship("InvoiceItem", back_populates="invoice",
                         cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

    @property
    def balance_due(self):
        return float(self.total_amount or 0) - float(self.amount_paid or 0)""",
        language="python",
        caption="Listing 8-1. Invoice header."))

    s.append(h2("Payment", styles))
    s.append(p(
        "A payment row records money received against an invoice — "
        "the method (credit card, debit card, ACH, cash, check), "
        "amount, transaction identifier, and status. When a payment "
        "posts successfully, the DatabaseManager "
        + b("updates the parent invoice's") + " "
        + c("amount_paid") + " "
        + b("and transitions its status") + " if the balance has "
        "reached zero or crossed a threshold. This happens inside "
        "the same session as the payment insert — both succeed "
        "atomically or both roll back.",
        styles))

    s.append(h2("InsuranceClaim — the state machine", styles))
    s.append(p(
        "Claims are a small state machine with real money flowing "
        "at the terminal transitions. The flow is: "
        + c("DRAFT") + " → "
        + c("SUBMITTED") + " → "
        + c("IN_REVIEW") + " → ("
        + c("APPROVED") + " | "
        + c("DENIED") + ") → "
        + c("PAID") + ". Claims that are denied may be resubmitted "
        "by creating a new draft; the original remains in the audit "
        "trail. When a claim transitions to "
        + c("APPROVED") + ", the DatabaseManager inserts a "
        + c("Payment") + " row for the approved amount and updates "
        "the parent invoice in the same transaction.",
        styles))

    # Claim flowchart
    nodes_claim = [
        {"id": "draft", "label": "DRAFT", "x": 0.9, "y": 2.9, "fill": NAVY_PALE},
        {"id": "sub", "label": "SUBMITTED", "x": 2.5, "y": 2.9, "fill": NAVY_PALE},
        {"id": "rev", "label": "IN_REVIEW", "x": 4.1, "y": 2.9, "fill": INDIGO_PALE},
        {"id": "appr", "label": "APPROVED", "x": 5.7, "y": 3.6, "fill": MOSS_PALE, "stroke": MOSS},
        {"id": "den", "label": "DENIED", "x": 5.7, "y": 2.2, "fill": CRIMSON_PALE, "stroke": CRIMSON},
        {"id": "paid", "label": "PAID", "x": 6.8, "y": 3.6, "fill": MOSS, "text_color": colors.white, "stroke": MOSS},
    ]
    edges_claim = [
        {"from": "draft", "to": "sub"},
        {"from": "sub", "to": "rev"},
        {"from": "rev", "to": "appr", "label": "approve"},
        {"from": "rev", "to": "den", "label": "deny"},
        {"from": "appr", "to": "paid", "label": "post"},
    ]
    s.append(Flowchart(nodes_claim, edges_claim, width=7.0, height=4.0,
                       caption="Fig. 8-1. InsuranceClaim lifecycle. Approval triggers a Payment insert."))
    s.append(Spacer(1, 0.3 * inch))

    s.append(h2("Money is stored as Numeric, never as float", styles))
    s.append(p(
        "Every column that holds currency uses SQLAlchemy's "
        + c("Numeric(10, 2)") + " type. Floats are forbidden for "
        "money. The Python side uses " + c("decimal.Decimal") + " "
        "or " + c("float()") + " at the display boundary only. This "
        "prevents the family of rounding bugs that end with an "
        "unexpected cent somewhere.",
        styles))
    s.append(caution(
        "If you see "
        + c("float()") + " applied to a currency value anywhere in "
        "business logic, treat it as a bug. The only legitimate "
        "place for float currency is JSON output (because JSON "
        "numbers are IEEE 754 anyway), and even there the "
        "conversion happens at the last possible moment.",
        styles))

    s.append(PageBreak())
    return s


def chapter_09_hipaa_models(styles):
    s = chapter_header("9", "HIPAA Compliance Models", styles)
    s.append(p(
        "HIPAA's Security Rule requires a documented set of "
        "administrative, physical, and technical safeguards. The "
        "technical safeguards map to code and therefore to tables. "
        "Nine tables exist primarily to satisfy compliance "
        "requirements; they share the property that their rows are "
        "written constantly and read rarely, except during audit.",
        styles))

    s.append(h2("AuditLog — who did what", styles))
    s.append(p(
        "Every action that mutates state — logins, password "
        "changes, patient edits, prescription creation, invoice "
        "adjustments — is logged to " + c("AuditLog") + ". The "
        "table holds the acting user, timestamp, action name, "
        "entity type and id, and a JSON payload of before/after "
        "state where relevant. Audit logs are never deleted.",
        styles))
    s.extend(code_block("""class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details_json = Column(Text)
    ip_address = Column(String(45))

    user = relationship("User", back_populates="audit_logs")""",
        language="python",
        caption="Listing 9-1. AuditLog — one row per state-changing action."))

    s.append(h2("PHIAccessLog — who looked at what", styles))
    s.append(p(
        "Where AuditLog records actions that change data, "
        + c("PHIAccessLog") + " records actions that merely view it. "
        "Opening a patient's chart, fetching a prescription list, "
        "rendering the billing history — each produces a row. The "
        "schema is similar to AuditLog but the action field is "
        "narrower (" + c("VIEW_") + "-prefixed verbs) and the detail "
        "payload is smaller.",
        styles))

    s.append(h2("FailedLogin and PasswordHistory", styles))
    s.append(p(
        c("FailedLogin") + " records every unsuccessful authentication "
        "attempt with the account name, timestamp, IP, user agent, "
        "and a reason code. The " + c("security/lockout.py") + " "
        "module consults this table when deciding whether to "
        "temporarily lock an account. "
        + c("PasswordHistory") + " records the last " + b("N") + " "
        "password hashes for each account so that password reuse "
        "can be prevented at the policy layer.",
        styles))

    s.append(h2("MFASecret — TOTP shared secrets", styles))
    s.append(p(
        "Multi-factor authentication in MedPharm is based on "
        "TOTP (RFC 6238). Each user who has enrolled has a row in "
        + c("MFASecret") + " with a Fernet-encrypted shared secret. "
        "Enrollment, verification, and backup-code handling live in "
        + c("security/totp.py") + ".",
        styles))

    s.append(h2("EmergencyAccessGrantRec — \"break the glass\"", styles))
    s.append(p(
        "In an emergency, a clinician may need to access a "
        "patient's record outside the normal role-based access "
        "controls. The emergency-access mechanism grants a "
        "time-boxed, logged, and later-reviewable exception. Each "
        "grant is a row in " + c("EmergencyAccessGrantRec") + " "
        "with the user, patient, reason, duration, and approval "
        "chain. Every access under the grant produces a PHI access "
        "log row, and grants must be reviewed within the period "
        "specified by the Security Officer.",
        styles))

    s.append(h2("PatientConsent — what the patient agreed to", styles))
    s.append(p(
        "Patients consent to specific uses of their information "
        "(treatment, payment, operations, marketing, research, "
        "portal access, and so on). Each granted consent is a row "
        "in " + c("PatientConsent") + " with a status, grant and "
        "expiry timestamps, a signed signature hash, and a document "
        "reference. The " + c("has_active_consent()") + " method on "
        "the DatabaseManager is the authoritative check used by "
        "feature code.",
        styles))
    s.extend(code_block("""def has_active_consent(self, patient_id: int, consent_type: str) -> bool:
    with self.get_session() as session:
        row = (session.query(PatientConsent)
                      .filter_by(patient_id=patient_id,
                                 consent_type=ConsentType(consent_type),
                                 status=ConsentStatus.GRANTED)
                      .order_by(desc(PatientConsent.granted_at)).first())
        if not row:
            return False
        if row.expires_at and row.expires_at < datetime.utcnow():
            return False
        return True""",
        language="python",
        caption="Listing 9-2. Canonical consent check."))

    s.append(h2("PatientDocument — secure document storage", styles))
    s.append(p(
        "Consent forms, scanned insurance cards, lab reports, and "
        "other file attachments are stored via "
        + c("PatientDocument") + " rows, which carry an encrypted "
        "filename, a storage reference (path or S3 key), content "
        "type, size, an SHA-256 of the ciphertext for integrity, "
        "and an uploader. Files themselves are not stored in the "
        "database; only the metadata lives there. Chapter 12 "
        "describes the encryption of the files on disk.",
        styles))

    s.append(h2("Summary table", styles))
    s.append(make_table(
        ["Table", "Written on", "Retention",
         "Security Rule cite (CFR)"],
        [
            ["audit_logs", "every state change",
             "retained indefinitely",
             "§164.312(b)"],
            ["phi_access_logs", "every PHI read",
             "retained indefinitely",
             "§164.312(b), §164.308(a)(1)(ii)(D)"],
            ["failed_logins", "every bad login",
             "retained at least 6 years",
             "§164.308(a)(5)(ii)(C)"],
            ["password_histories", "every password change",
             "last N per account",
             "§164.308(a)(5)(ii)(D)"],
            ["mfa_secrets", "enrollment",
             "until disabled",
             "§164.312(d)"],
            ["emergency_access_grants", "break-glass",
             "retained indefinitely",
             "§164.312(a)(2)(ii)"],
            ["patient_consents", "consent granted/revoked",
             "retained indefinitely",
             "§164.508"],
            ["patient_documents", "upload",
             "patient-specified",
             "§164.312(c)"],
        ],
        col_widths=[1.6 * inch, 1.7 * inch, 1.4 * inch, 1.8 * inch]))

    s.append(PageBreak())
    return s


def chapter_10_messaging_notes(styles):
    s = chapter_header("10", "Messaging and Private Notes", styles)
    s.append(p(
        "The messaging and private-notes features are the most "
        "recent substantial additions to the schema (version 1.7.5). "
        "Both encrypt their payload at rest; both are simple in "
        "shape but carry specific access-control rules that are "
        "enforced at both the API and DB layers.",
        styles))

    s.append(h2("MessageThread and SecureMessage", styles))
    s.append(p(
        "A thread is the conversational container; it belongs to "
        "exactly one patient and optionally to one provider. "
        "Messages are rows in " + c("SecureMessage") + ", each "
        "tagged with a " + c("sender_type") + " of either "
        + c("patient") + " or " + c("staff") + ". The body is "
        "Fernet-encrypted at rest.",
        styles))
    s.extend(code_block("""class MessageThread(Base):
    __tablename__ = "message_threads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"),
                        nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"),
                         nullable=True, index=True)
    subject = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_closed = Column(Boolean, default=False)

    patient = relationship("Patient")
    provider = relationship("User")
    messages = relationship("SecureMessage", back_populates="thread",
                            cascade="all, delete-orphan",
                            order_by="SecureMessage.sent_at")


class SecureMessage(Base):
    __tablename__ = "secure_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("message_threads.id"),
                       nullable=False)
    sender_type = Column(String(20), nullable=False)   # staff|patient|system
    sender_id = Column(Integer, nullable=False)
    body_encrypted = Column(Text, nullable=False)      # Fernet ciphertext
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    thread = relationship("MessageThread", back_populates="messages")""",
        language="python",
        caption="Listing 10-1. MessageThread and SecureMessage."))

    s.append(h2("ProviderNote — author-private", styles))
    s.append(p(
        "A ProviderNote is a free-text observation written by one "
        "clinician and visible to that clinician alone. It exists "
        "because the existing " + c("MedicalRecord") + " container "
        "is shared across providers and surfaced to the patient in "
        "the portal; those are the wrong semantics for a private "
        "working note. The body is Fernet-encrypted at rest, and "
        "the API and DB layers both enforce "
        + c("author_id") + " equality on every read, update, and "
        "delete operation.",
        styles))
    s.extend(code_block("""class ProviderNote(Base):
    __tablename__ = "provider_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"),
                        nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"),
                       nullable=False, index=True)
    body_encrypted = Column(Text, nullable=False)      # Fernet ciphertext
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    patient = relationship("Patient")
    author = relationship("User")""",
        language="python",
        caption="Listing 10-2. ProviderNote — visible only to the author."))

    s.append(danger(
        "Any future feature that surfaces ProviderNote content must "
        "verify that the viewing user is the author. The REST routes "
        "do this; the Qt desktop does this; no other surface should "
        "be added that queries the table without the author filter. "
        "If you are tempted to build \"share a note with a colleague\" "
        "— don't. Build a new feature (shared_provider_note) rather "
        "than weakening the privacy contract of this one.",
        styles))

    s.append(h2("Message flow and state", styles))
    s.append(p(
        "Messages have no internal status beyond their "
        + c("read_at") + " timestamp; threads have an "
        + c("is_closed") + " flag that prevents further replies. "
        "The " + c("mark_messages_read") + " method sets "
        + c("read_at") + " on unread messages sent by the "
        + i("other side") + " — staff marking a patient's messages "
        "read, or vice versa. It is called automatically when a "
        "thread is opened on either client.",
        styles))

    # Messaging sequence diagram as flowchart
    nodes_msg = [
        {"id": "p", "label": "Patient Client", "x": 0.9, "y": 3.8, "w": 1.6},
        {"id": "api", "label": "REST API", "x": 3.3, "y": 3.8, "w": 1.5, "fill": INDIGO, "text_color": colors.white, "stroke": NAVY},
        {"id": "enc", "label": "Fernet Encrypt", "x": 5.5, "y": 3.8, "w": 1.5, "fill": MOSS_PALE, "stroke": MOSS},
        {"id": "db", "label": "SQLite", "x": 5.5, "y": 2.3, "w": 1.5, "fill": NAVY, "text_color": colors.white, "stroke": NAVY_LIGHT},
        {"id": "dec", "label": "Fernet Decrypt", "x": 3.3, "y": 2.3, "w": 1.5, "fill": MOSS_PALE, "stroke": MOSS},
        {"id": "st", "label": "Staff Client", "x": 0.9, "y": 2.3, "w": 1.6},
    ]
    edges_msg = [
        {"from": "p", "to": "api", "label": "POST reply"},
        {"from": "api", "to": "enc", "label": "plaintext"},
        {"from": "enc", "to": "db", "label": "ciphertext"},
        {"from": "db", "to": "dec", "label": "ciphertext"},
        {"from": "dec", "to": "st", "label": "plaintext"},
    ]
    s.append(Flowchart(nodes_msg, edges_msg, width=7.0, height=4.8,
                       caption="Fig. 10-1. Secure message round-trip. The body is plaintext only inside the Flask process; never on disk."))
    s.append(Spacer(1, 0.3 * inch))

    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART III — THE BACKEND
# ═════════════════════════════════════════════════════════════════════════════

def chapter_11_db_manager(styles):
    s = chapter_header("11", "The DatabaseManager", styles)
    s.append(p(
        "The DatabaseManager is the single most important class in "
        "the codebase. Every state-changing operation, every query, "
        "every business rule that touches more than one row flows "
        "through it. This chapter examines its construction in "
        "depth.",
        styles))

    s.append(h2("Instantiation and lifecycle", styles))
    s.append(p(
        "A DatabaseManager instance is created once per process and "
        "initialised with a path to the SQLite file. Its "
        + c("init_db()") + " method creates the engine, runs "
        + c("Base.metadata.create_all") + ", and stores a session "
        "factory for later use.",
        styles))
    s.extend(code_block("""class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = None
        self._session_factory = None

    def init_db(self):
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()""",
        language="python",
        caption="Listing 11-1. DatabaseManager core — instantiation and session contextmanager."))

    s.append(p(
        "The " + c("get_session()") + " contextmanager is the "
        "canonical way to perform any DB work. It commits on clean "
        "exit and rolls back on exception, so a method body that "
        "consists of "
        + c("with self.get_session() as session: …") + " is safe "
        "even if an SQLAlchemy error occurs inside the "
        + c("with") + " block.",
        styles))
    s.append(caution(
        "Never create a session manually with "
        + c("self._session_factory()") + " outside of "
        + c("get_session()") + ". A forgotten close leaks a SQLite "
        "file handle; a forgotten rollback leaves the connection "
        "in an in-progress transaction.",
        styles))

    s.append(h2("Method grouping conventions", styles))
    s.append(p(
        "The DatabaseManager is a large class (over a thousand "
        "lines) but its methods are grouped by domain with banner "
        "comments that make navigation quick. The groups, in the "
        "order they appear, are:",
        styles))
    s.append(bullets([
        b("Authentication") + " — password hashing, portal account "
        "verification, staff login.",
        b("Users and portal accounts") + " — CRUD, provider listing.",
        b("Patients") + " — demographics, search, full profile "
        "aggregation.",
        b("Medications and interactions") + " — catalogue access, "
        "interaction checks.",
        b("Prescriptions") + " — two-level create, refill, status "
        "transitions.",
        b("Appointments") + " — calendar queries, status updates.",
        b("Medical records, vitals, allergies, diagnoses") + " — "
        "append-only history.",
        b("Invoices and payments") + " — two-level create, payment "
        "posting, balance calculation.",
        b("Insurance and claims") + " — policy management, claim "
        "state machine, automatic payment on approval.",
        b("Symptoms and conditions") + " — reference search with "
        "body-system and category filters.",
        b("Dashboard aggregates") + " — KPI queries for the home "
        "screen of each client.",
        b("Analytics") + " — revenue trends, demographics, top "
        "medications, provider workload.",
        b("Security / HIPAA") + " — audit, PHI access, lockout, "
        "password history, MFA, emergency access, consent.",
        b("Secure messaging") + " — threads, messages, "
        "reader-perspective unread counts.",
        b("Private provider notes") + " — encrypted, author-only.",
        b("Labs and lab results") + " — ordered tests and results.",
        b("Care plans and problems") + " — longitudinal problem lists.",
        b("Immunizations, referrals, documents") + " — the rest of "
        "the clinical surface area.",
    ], styles))

    s.append(h2("A representative method", styles))
    s.append(p(
        "Most DatabaseManager methods share a common shape: open a "
        "session, perform one or more queries, transform to a plain-"
        "dict representation suitable for JSON, return. Here is a "
        "typical example.",
        styles))
    s.extend(code_block("""def get_message_threads(self, *, patient_id: int | None = None,
                        provider_id: int | None = None,
                        reader_type: str | None = None) -> list[dict]:
    with self.get_session() as session:
        q = session.query(MessageThread)
        if patient_id is not None:
            q = q.filter(MessageThread.patient_id == patient_id)
        if provider_id is not None:
            q = q.filter(MessageThread.provider_id == provider_id)
        rows = q.order_by(desc(MessageThread.last_message_at)).all()
        out = []
        for t in rows:
            if reader_type == "staff":
                unread = sum(1 for m in t.messages
                             if m.sender_type == "patient" and m.read_at is None)
            elif reader_type == "patient":
                unread = sum(1 for m in t.messages
                             if m.sender_type == "staff" and m.read_at is None)
            else:
                unread = sum(1 for m in t.messages if m.read_at is None)
            out.append({
                "id": t.id,
                "subject": t.subject,
                "unread_count": unread,
                # … other fields …
            })
        return out""",
        language="python",
        caption="Listing 11-2. A typical DatabaseManager method — filter, order, transform, return."))

    s.append(h2("Eager loading decisions", styles))
    s.append(p(
        "Relationships default to lazy-loaded; eager loading is "
        "opt-in per query. Three patterns are most common:",
        styles))
    s.append(bullets([
        b("No eager loading") + " — when the relationship is not "
        "accessed in the transform loop. Most queries fall here.",
        b("joinedload(rel)") + " — when the relationship is "
        "accessed exactly once per row and produces at most a few "
        "rows on the other side.",
        b("selectinload(rel)") + " — when the relationship is "
        "one-to-many with potentially many rows per parent; "
        "issues a second " + c("IN") + " query instead of a "
        "potentially huge join.",
    ], styles))

    s.append(tip(
        "If you find yourself debugging a \"why is this endpoint "
        "slow?\" on a patient record, add "
        + c("echo=True") + " temporarily to the " + c("create_engine")
        + " call and watch the SQL. Eight out of ten such bugs are "
        "N+1 loads that want " + c("selectinload") + ".",
        styles))

    s.append(h2("Multi-row transactions", styles))
    s.append(p(
        "Some operations touch multiple tables atomically — "
        "creating a prescription also creates an invoice; approving "
        "a claim creates a payment and updates the invoice. These "
        "are written as a single "
        + c("with get_session()") + " block so that they commit "
        "together or not at all. The pattern is worth studying "
        "before you add similar logic elsewhere.",
        styles))
    s.extend(code_block("""def process_insurance_payment(self, claim_id: int,
                              approved: float,
                              copay: float,
                              deductible: float) -> dict:
    with self.get_session() as session:
        claim = session.get(InsuranceClaim, claim_id)
        if not claim:
            return {"error": "Claim not found"}

        claim.approved_amount = Decimal(str(approved))
        claim.copay_amount = Decimal(str(copay))
        claim.deductible_amount = Decimal(str(deductible))
        claim.status = InsuranceClaimStatus.APPROVED
        claim.processed_at = datetime.utcnow()

        invoice = session.get(Invoice, claim.invoice_id)
        if invoice:
            payment = Payment(
                invoice_id=invoice.id,
                amount=Decimal(str(approved)),
                payment_method=PaymentMethod.INSURANCE,
                status=PaymentStatus.COMPLETED,
                reference_number=f"CLM-{claim_id}",
            )
            session.add(payment)
            invoice.amount_paid = (invoice.amount_paid or 0) + Decimal(str(approved))
            if invoice.balance_due <= 0:
                invoice.status = InvoiceStatus.PAID
                claim.status = InsuranceClaimStatus.PAID
            elif invoice.amount_paid > 0:
                invoice.status = InvoiceStatus.PARTIAL
        return {"status": "processed", "approved": approved}""",
        language="python",
        caption="Listing 11-3. Multi-row transaction — claim, payment, invoice state all update together."))

    s.append(PageBreak())
    return s


def chapter_12_encryption(styles):
    s = chapter_header("12", "Field-Level Encryption", styles)
    s.append(p(
        "Certain columns contain sensitive free-text PHI that is "
        "never queried and should not sit on disk in plaintext. The "
        + c("security/encryption.py") + " module wraps the "
        + c("cryptography") + " library's Fernet primitive into a "
        "pair of pure-function helpers, "
        + c("encrypt_field()") + " and " + c("decrypt_field()") + ", "
        "plus a rotation helper. This chapter walks through the "
        "module and describes the key-management lifecycle.",
        styles))

    s.append(h2("What Fernet is", styles))
    s.append(p(
        "Fernet is an authenticated encryption scheme defined by "
        "the " + c("cryptography") + " library. Internally it "
        "combines AES-128 in CBC mode (for confidentiality) with "
        "HMAC-SHA256 (for authentication and integrity) over a "
        "timestamp-bearing envelope. Tokens are base64-url-safe "
        "encoded. The full specification is at "
        + link("https://github.com/fernet/spec/blob/master/Spec.md")
        + "; the library API is documented at "
        + link("https://cryptography.io/en/latest/fernet/") + ".",
        styles))

    s.append(h2("FieldCipher — the singleton", styles))
    s.append(p(
        "A single " + c("FieldCipher") + " instance is constructed "
        "lazily from the " + c("MEDPHARM_FIELD_KEY") + " environment "
        "variable. The cipher supports a list of legacy keys for "
        "rotation — decryption tries each key in order until one "
        "succeeds.",
        styles))
    s.extend(code_block("""class FieldCipher:
    def __init__(self, primary_key: str, legacy_keys: list[str] = ()):
        self._primary = Fernet(primary_key.encode())
        self._legacy = [Fernet(k.encode()) for k in legacy_keys]

    def encrypt(self, plaintext: str) -> str:
        return self._primary.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        candidates = [self._primary] + self._legacy
        last_exc = None
        for cipher in candidates:
            try:
                return cipher.decrypt(ciphertext.encode("ascii")).decode("utf-8")
            except InvalidToken as exc:
                last_exc = exc
        raise FieldEncryptionError("No valid key decrypted the field") from last_exc


def encrypt_field(plaintext: str | None) -> str | None:
    if plaintext is None: return None
    return _singleton().encrypt(plaintext)


def decrypt_field(ciphertext: str | None) -> str | None:
    if ciphertext is None: return None
    return _singleton().decrypt(ciphertext)""",
        language="python",
        caption="Listing 12-1. FieldCipher — multi-key-aware wrapper over Fernet."))

    s.append(h2("Which columns are encrypted", styles))
    s.append(make_table(
        ["Table", "Column", "Why"],
        [
            ["secure_messages", "body_encrypted",
             "Free-form clinical communication, never queried by "
             "substring."],
            ["provider_notes", "body_encrypted",
             "Author-private working notes; never queried by text."],
            ["mfa_secrets", "secret",
             "TOTP shared secret; leakage would compromise the "
             "second factor."],
            ["patient_documents", "filename_encrypted",
             "Original filenames may contain PHI (\"smith-john-mri-"
             "2024.pdf\")."],
        ],
        col_widths=[1.6 * inch, 1.8 * inch, 3.1 * inch]))

    s.append(h2("The rotation workflow", styles))
    s.append(p(
        "Keys are rotated according to the policy described in the "
        "Service Manual, Chapter 15. The engineering steps are:",
        styles))
    s.append(bullets([
        "Generate a new key with " + c("generate_key()") + " and "
        "set it as " + c("MEDPHARM_FIELD_KEY") + " in the new "
        "environment.",
        "Move the previous key into "
        + c("MEDPHARM_FIELD_KEY_LEGACY") + " (comma-separated for "
        "multiple legacy keys).",
        "Restart the application. New writes are encrypted with "
        "the primary key; existing rows are decrypted under the "
        "legacy key on read.",
        "Over time, a background re-encryption pass may rewrite "
        "existing rows with the new key and retire the legacy key. "
        "This is an operational decision, not an architectural "
        "requirement; dual-key support can be kept indefinitely.",
    ], styles))

    s.append(danger(
        "If all legacy keys are removed before existing ciphertext "
        "has been re-encrypted, the existing rows become "
        + b("permanently unreadable") + ". There is no backdoor. "
        "Always verify by sampling a handful of rows before dropping "
        "a legacy key.",
        styles))

    s.append(h2("Why not column-level transparent encryption?", styles))
    s.append(p(
        "SQLCipher and similar transparent-database-encryption "
        "schemes would be simpler in some respects, but they "
        "encrypt the whole database under a single key. MedPharm's "
        "field-level approach lets us keep queryable columns "
        "(patient name, dates) indexable and searchable while "
        "protecting the fields that do not need to be either. It "
        "also lets the key rotation happen online without re-"
        "opening the database file.",
        styles))

    s.append(PageBreak())
    return s


def chapter_13_rest_api(styles):
    s = chapter_header("13", "REST API Design", styles)
    s.append(p(
        "The REST API is a Flask blueprint registered under "
        + c("/api/v1/") + ". The prefix is deliberately versioned "
        "so that future evolutions of the protocol can cohabit with "
        "older clients. This chapter describes the endpoint "
        "conventions, the request/response shapes, and the common "
        "idioms you will reproduce when adding a new route.",
        styles))

    s.append(h2("URL conventions", styles))
    s.append(bullets([
        "All URLs are lower-case, words separated by hyphens where "
        "necessary.",
        "Collections are plural: " + c("/patients") + ", "
        + c("/prescriptions") + ".",
        "Items within collections are addressed by integer id: "
        + c("/patients/42") + ", "
        + c("/prescriptions/17/items") + ".",
        "Actions that do not fit REST semantics are expressed as "
        "verbs under the owning resource: "
        + c("/staff/messages/17/reply") + ", "
        + c("/staff/messages/17/close") + ".",
        "Patient-facing endpoints live under " + c("/patient/") + ". "
        "Staff-facing endpoints live under " + c("/staff/") + ". "
        "Reference data (medications, symptoms, conditions) lives "
        "at the top level.",
    ], styles))

    s.append(h2("Response conventions", styles))
    s.append(bullets([
        "Success responses always return JSON with a 2xx status.",
        "The top-level object has a single key whose name matches "
        "the resource — e.g. "
        + c('{"threads": [...]}') + " — or a small number of "
        "summary keys for dashboard-style endpoints.",
        "Errors return a 4xx or 5xx status with a body shaped "
        + c('{"error": "<message>"}') + ". Clients should rely on "
        "the status code for programmatic handling and the message "
        "only for user display.",
        "Creation endpoints return the new resource's id and 201, "
        "not the full resource. The client must re-read if it "
        "needs the complete shape.",
    ], styles))

    s.append(h2("A complete route example", styles))
    s.extend(code_block("""@api_bp.route("/patient/messages/<int:thread_id>/reply", methods=["POST"])
@patient_required
def patient_reply_thread(thread_id):
    thread = g.db_manager.get_message_thread(thread_id)
    if not thread or thread["patient_id"] != g.current_patient_id:
        return jsonify({"error": "Thread not found"}), 404
    if thread["is_closed"]:
        return jsonify({"error": "Thread is closed"}), 400
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "Body required"}), 400
    msg_id = g.db_manager.post_secure_message(
        thread_id=thread_id, sender_type="patient",
        sender_id=g.current_user_id, body_plain=body)
    return jsonify({"message_id": msg_id}), 201""",
        language="python",
        caption="Listing 13-1. A canonical route — decorator, validation, DB call, return."))

    s.append(p(
        "Observe the three phases. "
        + b("Validate") + ": the thread exists, it belongs to this "
        "patient, it is not closed, the body is non-empty. "
        + b("Perform") + ": a single DatabaseManager call. "
        + b("Return") + ": the new id plus 201. Routes longer than "
        "about twenty lines are a code smell — the excess usually "
        "wants to move into the DatabaseManager.",
        styles))

    s.append(h2("CORS and versioning", styles))
    s.append(p(
        "CORS is enabled via " + c("flask-cors") + " with origins "
        "configured by the " + c("MEDPHARM_CORS_ORIGINS") + " "
        "environment variable (default " + c("*") + " for "
        "development; specific origins for production). The "
        "single " + c("v1") + " prefix is the only version in "
        "existence at present; when a breaking change is required, "
        "add a " + c("v2") + " blueprint alongside and keep "
        + c("v1") + " working for the lifetime of any client that "
        "depends on it.",
        styles))

    s.append(h2("Endpoint catalogue", styles))
    s.append(p(
        "A complete table of every endpoint — method, path, "
        "required auth, request body, response shape — appears in "
        "Appendix C. When adding a new endpoint, update Appendix C "
        "in the same pull request.",
        styles))

    s.append(PageBreak())
    return s


def chapter_14_jwt(styles):
    s = chapter_header("14", "JWT Authentication Flow", styles)
    s.append(p(
        "MedPharm's JWT implementation is deliberately hand-written "
        "in " + c("api/auth.py") + ". It uses HMAC-SHA256 over a "
        "JSON payload — the " + c("hmac") + " and "
        + c("hashlib") + " standard library modules do the entire "
        "job, and no third-party JWT library is involved. This "
        "chapter explains why, walks through the token lifecycle, "
        "and describes the three access-control decorators.",
        styles))

    s.append(h2("Why not PyJWT or python-jose", styles))
    s.append(p(
        "Third-party JWT libraries have historically shipped a "
        "non-trivial number of verification-bypass vulnerabilities "
        "(algorithm confusion, " + c("alg=none") + " acceptance, "
        "key-type confusion, etc.). The MedPharm token format is "
        "narrow: HMAC-SHA256 is the only supported algorithm, "
        "tokens have a fixed header, and verification uses "
        + c("hmac.compare_digest") + " to avoid timing attacks. "
        "Hand-writing the forty lines of code that suffice closes "
        "the door on those vulnerability classes.",
        styles))

    s.append(h2("Token format", styles))
    s.append(p(
        "A MedPharm token is two base64url-encoded segments "
        "separated by a dot: "
        + c("<payload>.<signature>") + ". The payload is a small "
        "JSON object; the signature is HMAC-SHA256 over the "
        "payload segment using " + c("MEDPHARM_JWT_SECRET") + ". "
        "Payload fields:",
        styles))
    s.append(make_table(
        ["Field", "Type", "Meaning"],
        [
            ["user_type", "str", "\"staff\" or \"patient\""],
            ["user_id", "int", "User or portal account id"],
            ["patient_id", "int", "Associated patient id (patient tokens only)"],
            ["username", "str", "Account username"],
            ["role", "str", "Staff role (doctor, admin, …)"],
            ["name", "str", "Display name"],
            ["iat", "int", "Issued-at (unix seconds)"],
            ["exp", "int", "Expiry (unix seconds)"],
            ["typ", "str", "\"access\" or \"refresh\""],
        ],
        col_widths=[1.2 * inch, 0.8 * inch, 4.3 * inch]))

    s.append(h2("The implementation", styles))
    s.extend(code_block("""def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign(payload_b64: str) -> str:
    signature = hmac.new(
        _SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(signature)


def create_token(user_type, user_id, patient_id=None, username="",
                 role="", name="", is_refresh=False):
    expiry = _REFRESH_EXPIRY_SECONDS if is_refresh else _TOKEN_EXPIRY_SECONDS
    payload = {
        "user_type": user_type, "user_id": user_id,
        "patient_id": patient_id, "username": username,
        "role": role, "name": name,
        "iat": int(time.time()),
        "exp": int(time.time()) + expiry,
        "typ": "refresh" if is_refresh else "access",
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = _b64url_encode(payload_json.encode("utf-8"))
    sig = _sign(payload_b64)
    return f"{payload_b64}.{sig}"


def decode_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = _sign(payload_b64)
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None""",
        language="python",
        caption="Listing 14-1. The whole JWT implementation."))

    s.append(h2("Authentication sequence", styles))
    # Auth flowchart
    nodes_auth = [
        {"id": "c", "label": "Client", "x": 0.9, "y": 3.9, "w": 1.3},
        {"id": "nx", "label": "Nginx (TLS)", "x": 2.7, "y": 3.9, "w": 1.5, "fill": AMBER_PALE, "stroke": AMBER},
        {"id": "app", "label": "Flask", "x": 4.5, "y": 3.9, "w": 1.2},
        {"id": "lockout", "label": "LockoutTracker", "x": 6.2, "y": 3.9, "w": 1.5, "fill": NAVY_PALE},
        {"id": "auth", "label": "authenticate_user()", "x": 6.2, "y": 2.6, "w": 1.8, "fill": INDIGO, "text_color": colors.white, "stroke": NAVY},
        {"id": "tok", "label": "create_token()", "x": 4.5, "y": 2.6, "w": 1.5, "fill": MOSS_PALE, "stroke": MOSS},
        {"id": "resp", "label": "200 + tokens", "x": 2.7, "y": 2.6, "w": 1.5},
    ]
    edges_auth = [
        {"from": "c", "to": "nx", "label": "POST /login"},
        {"from": "nx", "to": "app"},
        {"from": "app", "to": "lockout", "label": "assert_not_locked"},
        {"from": "lockout", "to": "auth"},
        {"from": "auth", "to": "tok", "label": "on success"},
        {"from": "tok", "to": "resp"},
        {"from": "resp", "to": "c"},
    ]
    s.append(Flowchart(nodes_auth, edges_auth, width=7.0, height=4.8,
                       caption="Fig. 14-1. Login sequence. Lockout check happens before password verification."))
    s.append(Spacer(1, 0.3 * inch))

    s.append(h2("The three decorators", styles))
    s.extend(code_block("""def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        if payload.get("typ") != "access":
            return jsonify({"error": "Access token required"}), 401
        g.token_payload = payload
        g.current_user_type = payload["user_type"]
        g.current_user_id = payload["user_id"]
        g.current_patient_id = payload.get("patient_id")
        g.current_role = payload.get("role", "")
        return f(*args, **kwargs)
    return wrapper


def patient_required(f):
    @wraps(f)
    @token_required
    def wrapper(*args, **kwargs):
        if g.current_user_type != "patient":
            return jsonify({"error": "Patient access required"}), 403
        return f(*args, **kwargs)
    return wrapper


def staff_required(f):
    @wraps(f)
    @token_required
    def wrapper(*args, **kwargs):
        if g.current_user_type != "staff":
            return jsonify({"error": "Staff access required"}), 403
        return f(*args, **kwargs)
    return wrapper""",
        language="python",
        caption="Listing 14-2. Access-control decorators."))

    s.append(p(
        "Three rules cover almost all routes. "
        + c("@patient_required") + " — endpoints a patient hits "
        "from their mobile or web client, scoped to their own data. "
        + c("@staff_required") + " — endpoints a clinician or "
        "admin hits, scoped by role only when further restriction "
        "is required inside the handler. "
        + c("@token_required") + " — endpoints that accept either "
        "side, like the medication reference search.",
        styles))

    s.append(PageBreak())
    return s


def chapter_15_csrf_lockout_mfa(styles):
    s = chapter_header("15", "CSRF, Lockout, and MFA", styles)
    s.append(p(
        "Three security modules sit between the application factory "
        "and the routes: " + c("security/csrf.py") + " for Cross-"
        "Site Request Forgery protection on the web portal, "
        + c("security/lockout.py") + " for brute-force-resistant "
        "login, and " + c("security/totp.py") + " for multi-factor "
        "authentication. Each is worth understanding before you "
        "add a feature that touches authentication.",
        styles))

    s.append(h2("CSRF", styles))
    s.append(p(
        "The REST API does not need CSRF protection — it uses "
        "bearer tokens, not cookies, and an attacker's site cannot "
        "induce a browser to attach someone else's Bearer header. "
        "The Flask web portal, however, uses session cookies and "
        "must be protected. The "
        + c("@csrf_required") + " decorator applies to any portal "
        "route that mutates state. The token is generated per "
        "session, included in every form, and verified on POST.",
        styles))
    s.extend(code_block("""def csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            token_form = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            token_session = session.get("csrf_token")
            if not token_form or not token_session or not hmac.compare_digest(token_form, token_session):
                abort(403, description="CSRF verification failed")
        return f(*args, **kwargs)
    return wrapper""",
        language="python",
        caption="Listing 15-1. CSRF decorator — session-stored token compared with constant-time equality."))

    s.append(h2("Lockout", styles))
    s.append(p(
        "The " + c("LockoutTracker") + " in "
        + c("security/lockout.py") + " keeps an in-memory map of "
        + i("key") + " → " + i("(failure count, first-failure-time, "
        "locked-until)") + ". Keys are typically "
        + c("staff:username.lower()") + " or "
        + c("api-patient:username.lower()") + ". A configurable "
        "threshold triggers a lockout for a configurable duration, "
        "after which the counter is reset.",
        styles))
    s.extend(code_block("""class LockoutTracker:
    def __init__(self, threshold=5, window_seconds=300, lockout_seconds=900):
        self.threshold = threshold
        self.window = window_seconds
        self.lockout = lockout_seconds
        self._state: dict[str, tuple[int, float, float]] = {}

    def assert_not_locked(self, key):
        now = time.time()
        state = self._state.get(key)
        if state and state[2] > now:
            raise AccountLockedError(retry_after=int(state[2] - now))

    def record_failure(self, key):
        now = time.time()
        count, first, _ = self._state.get(key, (0, now, 0))
        if now - first > self.window:
            count = 0
            first = now
        count += 1
        locked_until = now + self.lockout if count >= self.threshold else 0
        self._state[key] = (count, first, locked_until)

    def record_success(self, key):
        self._state.pop(key, None)""",
        language="python",
        caption="Listing 15-2. LockoutTracker — simple sliding-window counter with cooldown."))

    s.append(note(
        "The tracker is process-local. Under gunicorn with "
        "multiple workers, an attacker's attempts are spread across "
        "workers; the threshold is therefore effectively multiplied "
        "by the worker count. For deployments with significant "
        "concurrency, consider pinning the tracker to a single "
        "worker or externalising it to Redis. At current scale, "
        "process-local is sufficient.",
        styles))

    s.append(h2("MFA — TOTP", styles))
    s.append(p(
        c("security/totp.py") + " implements TOTP (RFC 6238) with "
        "a 30-second step and SHA-1 HMAC. The shared secret is "
        "generated at enrollment, encoded as a " + c("otpauth://")
        + " URL presentable as a QR code, and stored Fernet-"
        "encrypted in the " + c("MFASecret") + " table. Verification "
        "accepts the current step ±1 (so a one-step clock skew is "
        "tolerated) and produces a single-use backup code set on "
        "initial enrollment.",
        styles))
    s.append(p(
        "The MFA flow is optional at present — a site may run with "
        "MFA disabled — but it is recommended for any deployment "
        "that handles real PHI. See the Service Manual (Vol. II, "
        "Chapter 10) for operator-facing enrollment procedures.",
        styles))

    s.append(PageBreak())
    return s


def chapter_16_web_portal(styles):
    s = chapter_header("16", "The Flask Web Portal", styles)
    s.append(p(
        "The web portal is a classic server-rendered Flask app "
        "living under " + c("web/") + ". It serves patients who "
        "prefer a browser to an app — elderly patients, patients "
        "on a Chromebook, patients on a desktop computer at work. "
        "It uses Flask-session session cookies rather than JWT "
        "because the browser round-trip is naturally cookie-based.",
        styles))

    s.append(h2("Application factory", styles))
    s.extend(code_block("""def create_app(db_manager):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.environ.get("MEDPHARM_SECRET_KEY", _dev_secret())
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (os.environ.get("MEDPHARM_TLS_MODE") != "disable")

    @app.before_request
    def attach_db():
        g.db_manager = db_manager

    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.utcnow().year,
            "user_logged_in": "user_id" in session,
            "patient_name": session.get("patient_name", ""),
            "csrf_token": _ensure_csrf_token(),
        }

    app.register_blueprint(portal_bp)
    return app""",
        language="python",
        caption="Listing 16-1. Web portal application factory."))

    s.append(h2("Routing conventions", styles))
    s.append(bullets([
        "Every mutating route is decorated with "
        + c("@login_required") + " and " + c("@csrf_required") + ".",
        "Routes return rendered Jinja2 templates, not JSON.",
        "On success, mutating routes redirect with "
        + c("redirect(url_for(...))") + " rather than re-rendering "
        "— the POST/Redirect/GET pattern prevents double-submit "
        "on refresh.",
        "Flash messages are used for user-visible confirmations "
        "and errors. The base template renders them in a Bootstrap "
        "alert.",
    ], styles))

    s.append(h2("Templates", styles))
    s.append(p(
        "Templates live in " + c("web/templates/") + " and extend "
        + c("base.html") + ". The base template carries the top "
        "navigation bar, notification bell, logout menu, and "
        "footer. Each functional area (prescriptions, billing, "
        "records, messages, appointments, medications, profile) "
        "has its own template pair — a list view and, where "
        "applicable, a detail view and a form.",
        styles))
    s.append(p(
        "The CSS is a hand-written dark-gradient theme in "
        + c("static/css/style.css") + " with Bootstrap 5 as the "
        "grid and component layer. Font Awesome is vendored under "
        + c("static/vendor/fontawesome/") + ", Bootstrap under "
        + c("static/vendor/bootstrap/") + ", and Google Fonts "
        "cached locally — no CDN is contacted at runtime so that "
        "the portal works in air-gapped deployments.",
        styles))

    s.append(h2("Patient authentication flow", styles))
    s.append(p(
        "The portal's login flow is simpler than the JWT flow. On "
        "POST to " + c("/login") + ", the handler calls "
        + c("db_manager.authenticate_portal(username, password)") + ". "
        "On success, the user_id, patient_id, and display name are "
        "written to the Flask session; on failure, the "
        "LockoutTracker records the attempt. Registration uses "
        "four-factor identity verification (name, DOB, SSN last 4, "
        "insurance id) against an existing Patient row.",
        styles))

    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART IV — THE CLIENTS
# ═════════════════════════════════════════════════════════════════════════════

def chapter_17_qt_desktop(styles):
    s = chapter_header("17", "Qt6 Desktop Application", styles)
    s.append(p(
        "The clinical desktop application is the most feature-rich "
        "client surface. It is a PyQt6 program that embeds the "
        "DatabaseManager in-process and drives a dark-themed "
        "sidebar-navigation window with one widget per functional "
        "area. This chapter walks through the major files and "
        "explains how a new widget is added.",
        styles))

    s.append(h2("Entry point and main window", styles))
    s.append(p(
        c("run_qt.py") + " creates a "
        + c("QApplication") + ", constructs a "
        + c("DatabaseManager") + ", calls "
        + c("init_db()") + ", and passes both to the "
        + c("MainWindow") + " constructor. The main window first "
        "shows a " + c("LoginDialog") + "; on success it sets up "
        "the sidebar, the " + c("QStackedWidget") + ", and the "
        "status bar.",
        styles))
    s.extend(code_block("""class MainWindow(QMainWindow):
    NAV_ITEMS = [
        ("Dashboard", "dashboard"),
        ("Patients", "patients"),
        ("Prescriptions", "prescriptions"),
        ("Medications", "medications"),
        ("Appointments", "appointments"),
        ("Records", "records"),
        ("Billing", "billing"),
        ("Messages", "messages"),
        ("Symptoms", "symptoms"),
        ("Analytics", "analytics"),
    ]

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = None
        self.setWindowTitle("MedPharm ERP")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(STYLESHEET)

        if not self.do_login():
            return

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()
        self.navigate_to(0)""",
        language="python",
        caption="Listing 17-1. MainWindow constructor and nav item list."))

    s.append(h2("Widget responsibilities", styles))
    s.append(p(
        "Each widget lives in its own file under "
        + c("qt_app/widgets/") + " and follows a standard shape: a "
        + c("__init__") + " that calls " + c("setup_ui") + ", a "
        + c("refresh_data") + " method that is invoked on "
        "navigation, and a set of event handlers that call methods "
        "on " + c("self.db_manager") + ". The widget "
        + b("never") + " builds SQL or manipulates ORM objects "
        "directly — it talks only through the DatabaseManager.",
        styles))

    s.append(h2("Dialog idioms", styles))
    s.append(p(
        "Dialogs (" + c("QDialog") + ") are used for modal flows: "
        "new patient, new prescription, payment, insurance claim "
        "submission, provider note editor. The convention is: "
        "build the form, wire Cancel to " + c("dialog.reject()") + ", "
        "wire Save to a method on the parent widget that validates "
        "and calls the DatabaseManager. On success, the parent "
        "widget refreshes its display.",
        styles))

    s.append(h2("Stylesheet", styles))
    s.append(p(
        c("qt_app/styles.py") + " holds a QSS stylesheet applied "
        "globally at startup. The palette is teal-on-dark with a "
        "few semantic accents — pinned notes use amber; critical "
        "allergy warnings use crimson. Object names are set "
        "consistently (" + c('setObjectName("heading")') + ", "
        + c('"primary_button"') + ", "
        + c('"card"') + ", "
        + c('"nav_button"') + ") so the stylesheet selectors can "
        "target them.",
        styles))

    s.append(h2("Threading", styles))
    s.append(p(
        "Long-running database work is rare in clinical widgets — "
        "SQLite on the same machine answers most queries in a "
        "millisecond. The analytics widget, which computes "
        "aggregates for matplotlib charts, is the exception; it "
        "runs its queries synchronously on the main thread today, "
        "and if that becomes painful it will move to a "
        + c("QThread") + ". In general, prefer to keep the event "
        "loop responsive and only introduce threads when profiling "
        "demands it.",
        styles))

    s.append(h2("Adding a new widget", styles))
    s.append(p(
        "Recipe (expanded in Chapter 33): create "
        + c("qt_app/widgets/yourname_widget.py") + " with a class "
        + c("YourNameWidget(QWidget)") + ", import it in "
        + c("main_window.py") + ", add a tuple to "
        + c("NAV_ITEMS") + ", add the instantiation to the stack, "
        "done.",
        styles))

    s.append(PageBreak())
    return s


def chapter_18_android(styles):
    s = chapter_header("18", "Android (Kotlin / MVVM / Retrofit)", styles)
    s.append(p(
        "The Android application is a patient-facing client built "
        "on Jetpack's modern stack. This chapter walks through the "
        "structure, the concurrency model, the secure-storage "
        "strategy, and the conventions you should follow when "
        "adding a new screen.",
        styles))

    s.append(h2("Project layout", styles))
    s.append(bullets([
        c("android/") + " — the Gradle project root; contains "
        + c("build.gradle.kts") + ", "
        + c("settings.gradle.kts") + ", and the "
        + c("app/") + " module.",
        c("app/src/main/java/com/enlightec/medpharm/") + " — "
        "Kotlin sources; see subdirectories below.",
        c("data/api/") + " — " + c("ApiService") + " interface, "
        + c("ApiClient") + " builder, " + c("ServerConfig") + ".",
        c("data/model/") + " — all " + c("data class") + "es that "
        "map to JSON.",
        c("data/repository/") + " — " + c("MedPharmRepository")
        + ", the central facade over Retrofit calls.",
        c("ui/<feature>/") + " — one subdirectory per feature; "
        "each contains Fragment, ViewModel, Adapter, and any "
        "feature-specific Activities.",
        c("util/") + " — " + c("TokenManager") + ", "
        + c("AuthInterceptor") + ", " + c("Resource") + " sealed "
        "result type.",
    ], styles))

    s.append(h2("The Resource sealed class", styles))
    s.extend(code_block("""sealed class Resource<out T> {
    object Loading : Resource<Nothing>()
    data class Success<out T>(val data: T) : Resource<T>()
    data class Error(val message: String, val code: Int = 0) : Resource<Nothing>()
}""",
        language="kotlin",
        caption="Listing 18-1. The Resource wrapper — single return type for any async repository call."))

    s.append(p(
        "Every repository method returns "
        + c("Resource<T>") + ". ViewModels expose "
        + c("LiveData<Resource<T>>") + ". Fragments observe it "
        "and switch on the three cases — Loading, Success, Error. "
        "This uniform shape removes a class of nullability bugs "
        "and makes UI state handling boring in the best sense.",
        styles))

    s.append(h2("Retrofit and ApiService", styles))
    s.append(p(
        "The " + c("ApiService") + " interface enumerates every "
        "endpoint with Retrofit annotations. Adding a new endpoint "
        "is a two-line change here plus one method on the "
        "repository.",
        styles))
    s.extend(code_block("""interface ApiService {
    @POST("api/v1/auth/login/patient")
    suspend fun patientLogin(@Body body: Map<String, String>): Response<LoginResponse>

    @GET("api/v1/patient/messages")
    suspend fun getMessageThreads(): Response<MessageThreadsResponse>

    @POST("api/v1/patient/messages/{threadId}/reply")
    suspend fun replyToThread(
        @Path("threadId") threadId: Int,
        @Body body: ReplyRequest,
    ): Response<MessageResponse>
}""",
        language="kotlin",
        caption="Listing 18-2. ApiService excerpt — declarative endpoint bindings."))

    s.append(h2("Auth interceptor and token storage", styles))
    s.append(p(
        "Tokens are stored in " + c("EncryptedSharedPreferences") + " "
        "through the " + c("TokenManager") + " singleton. The "
        + c("AuthInterceptor") + " runs on every OkHttp request, "
        "adds the " + c("Authorization: Bearer") + " header, and "
        "on 401 triggers a refresh attempt. If refresh fails, the "
        "user is bounced to " + c("LoginActivity") + ".",
        styles))

    s.append(h2("Network security configuration", styles))
    s.append(p(
        c("res/xml/network_security_config.xml") + " pins the "
        "runtime to TLS-only connections to the production "
        "hostname, with a "
        + c("<domain-config>") + " for "
        + c("localhost") + " and "
        + c("10.0.2.2") + " (the Android emulator's alias for the "
        "host machine) that trusts user-installed CAs so developers "
        "can accept the MedPharm self-signed cert.",
        styles))

    s.append(h2("Adding a new screen", styles))
    s.append(p(
        "The pattern is: data class → ApiService method → "
        "repository method → ViewModel → Fragment + layout. The "
        "Messages feature, added in 1.7.5, is a complete example "
        "(" + c("ui/messages/") + ") — use it as a template.",
        styles))

    s.append(PageBreak())
    return s


def chapter_19_ios(styles):
    s = chapter_header("19", "iOS (SwiftUI / async-await)", styles)
    s.append(p(
        "The iOS application is a SwiftUI app targeting iOS 16+. "
        "It uses async/await for all networking, NavigationStack "
        "for hierarchical navigation, and the iOS Keychain for "
        "token storage. The code is deliberately short — SwiftUI "
        "declarative syntax and a small surface area keep the file "
        "count low.",
        styles))

    s.append(h2("Project layout", styles))
    s.append(bullets([
        c("ios/MedPharm/") + " — Xcode project root.",
        c("MedPharm/MedPharmApp.swift") + " — " + c("@main") + " "
        "entry point, conditional root view based on auth state.",
        c("MedPharm/Models/Models.swift") + " — all "
        + c("Codable") + " data types.",
        c("MedPharm/Services/APIClient.swift") + " — actor-based "
        "HTTP client with automatic token refresh.",
        c("MedPharm/Services/AuthManager.swift") + " — login state "
        "management as an " + c("ObservableObject") + ".",
        c("MedPharm/Views/<Feature>/") + " — one directory per "
        "feature area.",
        c("MedPharm/Theme.swift") + " — " + c("MPColor") + " "
        "enum and a reusable gradient background view.",
    ], styles))

    s.append(h2("The APIClient actor", styles))
    s.append(p(
        "Swift's " + c("actor") + " keyword is perfect for a "
        "network client with mutable shared state (tokens). The "
        "APIClient is an actor whose methods can be called "
        "concurrently but whose internal state is serialised "
        "automatically.",
        styles))
    s.extend(code_block("""actor APIClient {
    static let shared = APIClient()
    private var baseURL: String = APIClient.storedBaseURL
    private var accessToken: String? {
        get { KeychainHelper.get(key: "access_token") }
        set { KeychainHelper.set(key: "access_token", value: newValue) }
    }

    func request<T: Decodable>(_ endpoint: String, method: String = "GET",
                                body: Encodable? = nil) async throws -> T {
        guard let url = URL(string: "\\(baseURL)/\\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = accessToken {
            request.setValue("Bearer \\(token)", forHTTPHeaderField: "Authorization")
        }
        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        if httpResponse.statusCode == 401 {
            if let newToken = try? await refreshAccessToken() {
                accessToken = newToken
                // retry once
                request.setValue("Bearer \\(newToken)", forHTTPHeaderField: "Authorization")
                let (retryData, _) = try await URLSession.shared.data(for: request)
                return try JSONDecoder().decode(T.self, from: retryData)
            }
            throw APIError.unauthorized
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        return try JSONDecoder().decode(T.self, from: data)
    }
}""",
        language="swift",
        caption="Listing 19-1. APIClient actor — single generic entry point with automatic token refresh."))

    s.append(h2("View composition", styles))
    s.append(p(
        "Views follow the conventional SwiftUI pattern: a "
        + c("@State") + " property for each user-edited field, an "
        + c("@StateObject") + " or " + c("@EnvironmentObject") + " "
        "for any shared service (primarily " + c("AuthManager") + "), "
        "and "
        + c(".task") + " modifiers to perform initial loads. The "
        + c("MessagesView") + ", added in 1.7.5, is a good compact "
        "example of the full pattern — list → detail → compose.",
        styles))

    s.append(h2("Keychain storage", styles))
    s.append(p(
        "Tokens live in the iOS Keychain via the "
        + c("KeychainHelper") + " utility. The Keychain persists "
        "across app uninstalls by default; the app explicitly "
        "clears entries on logout. The server-URL override lives "
        "in " + c("UserDefaults") + " — it is operational "
        "configuration, not a secret, and is more conveniently "
        "inspected in UserDefaults for support purposes.",
        styles))

    s.append(PageBreak())
    return s


def chapter_20_macos(styles):
    s = chapter_header("20", "macOS (SwiftUI / NavigationSplitView)", styles)
    s.append(p(
        "The macOS client shares most of its code with the iOS "
        "client. The Models, APIClient, and AuthManager are "
        "essentially identical; the Views differ where macOS "
        "idioms (NavigationSplitView, contextual menus, table "
        "columns) warrant different layout.",
        styles))

    s.append(h2("What is different from iOS", styles))
    s.append(bullets([
        "The root view is a " + c("NavigationSplitView") + " with "
        "a permanent sidebar of destinations, replacing iOS's "
        "tab bar.",
        "Lists use " + c("List") + " with selection binding "
        "rather than " + c("NavigationLink") + " rows — this gives "
        "the canonical Mac master-detail feel.",
        "Dialogs are " + c("sheet") + "s with explicit frame sizes, "
        "because Mac modals expect a reasonable minimum size.",
        "The Messages view uses an inner " + c("HSplitView") + " "
        "so that the thread list and the conversation pane are "
        "independently resizable.",
        "There is no " + c("navigationBarTitleDisplayMode") + "; "
        "toolbar items go in " + c(".primaryAction") + " or "
        + c(".automatic") + " placements instead of iOS's "
        "topBarLeading/topBarTrailing.",
    ], styles))

    s.append(h2("Shared codebase", styles))
    s.append(p(
        "Where the Models, Services, or Views are materially "
        "similar, the macOS files are near-copies of the iOS "
        "files with the comment header adjusted. This is a "
        "deliberate trade-off: a shared Swift package would reduce "
        "duplication but complicate the Xcode project graph. With "
        "two targets only, the maintenance cost is small — a new "
        "Model added on iOS is a copy-paste to macOS.",
        styles))

    s.append(note(
        "If you are adding a model field, update "
        + i("both") + " " + c("ios/.../Models.swift") + " and "
        + c("macos/.../Models.swift") + " in the same commit. A "
        "drift between them is a class of subtle bug that has "
        "happened before.",
        styles))

    s.append(h2("Building and packaging", styles))
    s.append(p(
        "Open " + c("macos/MedPharm/MedPharm.xcodeproj") + " in "
        "Xcode and build. For TestFlight/App Store distribution, "
        "the usual signing and provisioning steps apply; for "
        "internal distribution of unsigned builds, the Service "
        "Manual (Vol. II, Ch. 24) documents the deployment path.",
        styles))

    s.append(PageBreak())
    return s


def chapter_21_windows(styles):
    s = chapter_header("21", "Windows (.NET 8 / WPF)", styles)
    s.append(p(
        "The Windows client is a WPF application on .NET 8 using "
        "the MVVM pattern via the CommunityToolkit.Mvvm package. "
        "It exists because many medical practices run Windows at "
        "the front desk and benefit from a native desktop client "
        "rather than a browser.",
        styles))

    s.append(h2("Project layout", styles))
    s.append(bullets([
        c("windows/MedPharm/") + " — solution root.",
        c("MedPharm.csproj") + " — project file (" + c("<UseWPF>true</UseWPF>")
        + ", " + c("<TargetFramework>net8.0-windows</TargetFramework>") + ").",
        c("App.xaml") + " / " + c("App.xaml.cs") + " — application "
        "startup, theme loading, global " + c("ApiClient") + " and "
        + c("TokenStore") + " singletons.",
        c("Models/ApiModels.cs") + " — POCOs matching the JSON "
        "shapes.",
        c("Services/ApiClient.cs") + " — " + c("HttpClient") + "-"
        "based API client with " + c("Newtonsoft.Json") + " "
        "serialisation.",
        c("Services/TokenStore.cs") + " — DPAPI-encrypted token "
        "storage (" + c("ProtectedData") + " with "
        + c("DataProtectionScope.CurrentUser") + ").",
        c("Views/") + " — " + c("MainWindow.xaml") + " plus "
        + c("Pages/") + " (UserControls) for each navigation "
        "destination.",
        c("Themes/MedPharmTheme.xaml") + " — color brushes, "
        "gradient backgrounds, nav-button styles, card style.",
    ], styles))

    s.append(h2("Why DPAPI for token storage", styles))
    s.append(p(
        "Windows Data Protection API (DPAPI) encrypts data with a "
        "key derived from the user's credentials. Tokens encrypted "
        "with DPAPI cannot be decrypted by another user on the "
        "same machine and cannot be decrypted at all outside the "
        "local machine. This is a better fit than the Windows "
        "credential manager for ephemeral secrets; credentials go "
        "to the credential manager, access tokens to DPAPI.",
        styles))

    s.append(h2("Conversational view construction", styles))
    s.append(p(
        "The MessagesPage, added in 1.7.5, is a good example of "
        "WPF data binding plus code-behind for dynamic content. "
        "The XAML declares a two-column " + c("Grid") + " with a "
        + c("ListBox") + " on the left (threads) and a conversation "
        "pane on the right. Because each message bubble must be "
        "coloured differently depending on sender, the bubbles are "
        "built in code-behind (" + c("BuildBubble") + ") rather "
        "than via a XAML " + c("DataTemplate") + " with converters "
        "— this avoids having to ship four value converters for a "
        "decorative layout.",
        styles))

    s.append(h2("Building the Windows client", styles))
    s.append(p(
        "Open " + c("windows/MedPharm/MedPharm.sln") + " in Visual "
        "Studio 2022 or later and build, or use "
        + c("dotnet build") + " on the command line on Windows. "
        "Cross-building from Linux uses "
        + c("<EnableWindowsTargeting>true</EnableWindowsTargeting>")
        + " in the project file, but the resulting binaries will "
        "still need to be signed and tested on Windows.",
        styles))

    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART V — CROSS-CUTTING CONCERNS
# ═════════════════════════════════════════════════════════════════════════════

def chapter_22_audit(styles):
    s = chapter_header("22", "Audit Logging and PHI Access Trails", styles)
    s.append(p(
        "Audit is not a feature bolted on — it is an invariant "
        "maintained by every code path that changes state or views "
        "PHI. This chapter describes the two logging streams, the "
        "helper methods that emit to them, and the rules you must "
        "follow when adding new routes.",
        styles))

    s.append(h2("Two streams", styles))
    s.append(p(
        "MedPharm emits audit events to two separate tables: "
        + c("audit_logs") + " for state changes, and "
        + c("phi_access_logs") + " for read-only PHI access. The "
        "separation matters because retention, review, and "
        "export rules differ. An auditor asking \"who modified "
        "anything last Thursday?\" wants audit_logs; one asking "
        "\"who looked at this patient's chart?\" wants "
        "phi_access_logs.",
        styles))

    s.append(h2("The log_action helper", styles))
    s.extend(code_block("""def log_action(self, user_id: int, action: str, entity_type: str = "",
               entity_id: int = None, details: dict = None, ip: str = ""):
    with self.get_session() as session:
        row = AuditLog(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=json.dumps(details or {}, default=str),
            ip_address=ip,
        )
        session.add(row)""",
        language="python",
        caption="Listing 22-1. Canonical audit emission."))

    s.append(h2("Idioms for action names", styles))
    s.append(p(
        "Action names follow a verb-noun convention in snake_case: "
        + c("create_patient") + ", " + c("update_prescription") + ", "
        + c("delete_note") + ", " + c("submit_claim") + ", "
        + c("process_payment") + ". PHI-read actions use the "
        + c("view_") + " prefix: " + c("view_patient_chart") + ", "
        + c("view_prescription") + ". Consistency matters — "
        "auditors grep for these strings.",
        styles))

    s.append(h2("What to include in details_json", styles))
    s.append(bullets([
        "For create: the new record's id and a small summary "
        "(patient name, rx number, etc.). Do not include the full "
        "object.",
        "For update: only the changed fields, in "
        + c("{\"before\": {...}, \"after\": {...}}") + " form.",
        "For delete: the id of the deleted row and a reason if the "
        "caller supplied one.",
        "Never include raw passwords, token strings, Fernet keys, "
        "or MFA secrets. These are all audit-log poison.",
    ], styles))

    s.append(caution(
        "A common mistake is to log the full form data posted by "
        "the user. Form data can contain fields that were edited "
        "and immediately corrected — the audit trail should "
        "reflect the change the database actually stored, not the "
        "transient values typed along the way.",
        styles))

    s.append(h2("PHI access logging", styles))
    s.append(p(
        "Routes that read PHI should call "
        + c("self.log_phi_access(...)") + " on the DatabaseManager "
        "with the viewing user, the patient_id, the record type, "
        "and a short reason. The pattern is not yet uniformly "
        "applied across every endpoint — a pull request that adds "
        "missing calls is always welcome — but new endpoints are "
        "expected to honour it.",
        styles))

    s.append(PageBreak())
    return s


def chapter_23_tls(styles):
    s = chapter_header("23", "TLS and Certificate Lifecycle", styles)
    s.append(p(
        "Every installation path terminates TLS by default: "
        "Docker, source Python, Kubernetes, and the full-stack "
        "image all ship TLS-capable. The Service Manual documents "
        "the operator-facing workflow in detail; this chapter "
        "covers the developer's view — where the code that runs "
        "the TLS logic lives, and how to make changes safely.",
        styles))

    s.append(h2("The three modes", styles))
    s.append(p(
        c("MEDPHARM_TLS_MODE") + " takes three values:",
        styles))
    s.append(bullets([
        b("auto") + " — default. If a cert is present in "
        + c("MEDPHARM_TLS_DIR") + ", use it; otherwise generate a "
        "self-signed one on first boot.",
        b("require") + " — fail to start unless a cert is "
        "present. Use this in production to guarantee no "
        "plaintext fallback.",
        b("disable") + " — serve plaintext. Local development "
        "only; never in production.",
    ], styles))

    s.append(h2("Generation script", styles))
    s.append(p(
        c("server/nginx/generate-cert.sh") + " is the single "
        "source of truth for self-signed cert generation. It "
        "produces an RSA-4096 cert valid for "
        + c("MEDPHARM_TLS_DAYS") + " days (default 825) with the "
        "common name set from "
        + c("MEDPHARM_TLS_HOSTNAME") + ". The same script is "
        "invoked from the Docker entrypoint, from "
        + c("./start_cloud.sh") + ", and from the Kubernetes "
        "wrapper.",
        styles))

    s.append(h2("Bringing your own cert", styles))
    s.append(p(
        "To use a CA-issued cert, drop "
        + c("fullchain.pem") + " and " + c("privkey.pem") + " into "
        "the " + c("medpharm-tls") + " Docker volume or the "
        + c("medpharm-tls") + " Kubernetes Secret, set "
        + c("MEDPHARM_TLS_MODE=require") + ", and restart. The "
        "gunicorn and Nginx configs both honour the two filenames.",
        styles))

    s.append(h2("Developer convenience", styles))
    s.append(p(
        "For local dev, the easiest path is "
        + c("MEDPHARM_TLS_MODE=disable ./start_cloud.sh") + ", "
        "which serves plaintext HTTP on port 8080. Mobile clients "
        "in the emulator/simulator work either way — the Android "
        "network security config trusts user-installed CAs on "
        "localhost, and the iOS simulator accepts a self-signed "
        "cert once added to the trust store.",
        styles))

    s.append(PageBreak())
    return s


def chapter_24_docker(styles):
    s = chapter_header("24", "Docker and Containerisation", styles)
    s.append(p(
        "Two images are published to Docker Hub under the "
        + link(DOCKERHUB_URL, "enlightec") + " namespace:",
        styles))
    s.append(bullets([
        c("enlightec/medpharm-api") + " — API-only. Built from the "
        "root " + c("Dockerfile") + ". Exposes port 8080.",
        c("enlightec/medpharm-server") + " — full stack (Nginx + "
        "API + web portal under supervisord). Built from "
        + c("server/Dockerfile") + ". Exposes 80, 443, 8080, 5000.",
    ], styles))

    s.append(h2("Dockerfile structure", styles))
    s.append(p(
        "Both Dockerfiles are multi-stage, pinned to Ubuntu "
        "24.04 LTS, and follow the same shape:",
        styles))
    s.append(bullets([
        "Install system dependencies (Python, Nginx, build tools "
        "required for " + c("cryptography") + ").",
        "Create an unprivileged " + c("medpharm") + " user.",
        "Copy the source tree.",
        "Install Python requirements into a virtualenv under "
        + c("/opt/medpharm/venv") + ".",
        "Set sane ENV defaults (ports, TLS mode, worker counts).",
        "Declare exposed ports, volumes, health check, and "
        "entrypoint.",
    ], styles))

    s.append(h2("Supervisord for the full-stack image", styles))
    s.append(p(
        c("server/supervisord.conf") + " manages three processes: "
        "Nginx, gunicorn-for-API, and gunicorn-for-web-portal. Each "
        "has its own log destination. When the container exits, "
        "supervisord stops all three gracefully. Log rotation is "
        "delegated to the host or orchestrator; within the "
        "container, logs stream to mounted volumes.",
        styles))

    s.append(h2("Building locally", styles))
    s.extend(code_block("""# API only
docker build -f Dockerfile \\
  -t enlightec/medpharm-api:1.7.6 \\
  -t enlightec/medpharm-api:latest .

# Full stack
docker build -f server/Dockerfile \\
  -t enlightec/medpharm-server:1.7.6 \\
  -t enlightec/medpharm-server:latest .

# Test locally
docker compose -f docker-compose.hub.yml up -d
curl -k https://localhost:8080/api/v1/health""",
        language="kotlin",
        caption="Listing 24-1. Local build and quick-launch."))

    s.append(h2("CI/CD", styles))
    s.append(p(
        c(".github/workflows/docker-publish.yml") + " builds and "
        "pushes both images on every " + c("v*.*.*") + " tag push. "
        "The workflow validates Python syntax, exercises the "
        "database initialisation code path, verifies the API "
        "health endpoint, and only then runs the Docker build. "
        "Credentials come from repository secrets "
        + c("DOCKERHUB_USERNAME") + " and "
        + c("DOCKERHUB_TOKEN") + ".",
        styles))

    s.append(tip(
        "If CI is blocked (billing, runner outage) the manual "
        "fallback is to build and push from a developer machine — "
        "it is the same two " + c("docker build") + " commands "
        "followed by four " + c("docker push") + "es. Only run "
        "this with explicit release-manager authorisation; "
        "tagged images on Docker Hub are a contract.",
        styles))

    s.append(PageBreak())
    return s


def chapter_25_kubernetes(styles):
    s = chapter_header("25", "Kubernetes Deployment", styles)
    s.append(p(
        "Kubernetes manifests live under " + c("k8s/") + " as a "
        "Kustomize base with three overlays: "
        + c("overlays/gcp/") + ", "
        + c("overlays/aws/") + ", and "
        + c("overlays/generic/") + ". The wrapper script "
        + c("k8s/medpharm-k8s.sh") + " abstracts the common "
        "workflows — install, status, deploy, backup, rotate-tls.",
        styles))

    s.append(h2("Base manifests", styles))
    s.append(bullets([
        c("deployment.yaml") + " — single-pod deployment of the "
        + c("enlightec/medpharm-server") + " image.",
        c("service.yaml") + " — ClusterIP service exposing 80 and "
        "443.",
        c("ingress.yaml") + " — ingress rules; overlays supply the "
        "cloud-specific ingress class (GCE, ALB, nginx).",
        c("secret.yaml") + " — placeholder Secret for "
        "MEDPHARM_JWT_SECRET, MEDPHARM_SECRET_KEY, and "
        "MEDPHARM_FIELD_KEY. Operators fill in real values via "
        + c("kubectl create secret generic") + ".",
        c("pvc.yaml") + " — PersistentVolumeClaim for "
        + c("/data") + " and "
        + c("/etc/ssl/medpharm") + ".",
        c("kustomization.yaml") + " — lists the above and sets the "
        "container image tag.",
    ], styles))

    s.append(h2("Scaling story", styles))
    s.append(p(
        "The single-pod deployment is intentional: SQLite's "
        "single-writer constraint means multiple pods would "
        "contend on the same database file. If write throughput "
        "demands it, the migration path is to PostgreSQL plus a "
        "horizontal pod autoscaler — not multiple SQLite pods. "
        "For read-heavy scaling, an additional API-only "
        "deployment can front read-only endpoints, but that is a "
        "deployment choice, not a code change.",
        styles))

    s.append(h2("Hot backup", styles))
    s.append(p(
        c("k8s/medpharm-k8s.sh backup <file>") + " runs SQLite's "
        "online backup API against the running pod and streams the "
        "result to the local file. The database remains "
        "available throughout; there is no lock held longer than "
        "a few milliseconds.",
        styles))

    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART VI — DEVELOPMENT WORKFLOW
# ═════════════════════════════════════════════════════════════════════════════

def chapter_26_dev_env(styles):
    s = chapter_header("26", "Setting Up a Development Environment", styles)
    s.append(p(
        "A fresh checkout to a working clinical desktop should take "
        "under ten minutes on Ubuntu or macOS and under fifteen on "
        "Windows (via WSL2). This chapter walks through the exact "
        "sequence.",
        styles))

    s.append(h2("Prerequisites", styles))
    s.append(make_table(
        ["Tool", "Minimum version", "Needed for"],
        [
            ["Python", "3.10", "Everything server-side"],
            ["Git", "2.30", "Source control"],
            ["Docker", "24+", "Container builds (optional)"],
            ["Xcode", "15", "iOS/macOS builds"],
            ["Android Studio", "Iguana (2023.3)", "Android builds"],
            [".NET SDK", "8.0", "Windows builds"],
            ["Qt6", "(via pip)", "Desktop UI"],
        ],
        col_widths=[1.4 * inch, 1.6 * inch, 3.3 * inch]))

    s.append(h2("The canonical install", styles))
    s.extend(code_block("""git clone https://github.com/stillwell/MedPharm.git
cd MedPharm
chmod +x install.sh
./install.sh""",
        language="kotlin",
        caption="Listing 26-1. The happy path."))

    s.append(p(
        "The install script detects the OS, installs system "
        "dependencies, creates a virtualenv under "
        + c("venv/") + ", installs Python requirements, "
        "initialises the SQLite database, and runs the seed "
        "scripts. On completion, three launchers are ready: "
        + c("./start_cloud.sh") + ", "
        + c("./start_web.sh") + ", and "
        + c("./start_desktop.sh") + ".",
        styles))

    s.append(h2("Manual install (if the script fails)", styles))
    s.extend(code_block("""python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-cloud.txt
pip install reportlab pygame  # optional extras
python3 -c "
from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_expanded import seed_expanded_data
db = DatabaseManager('medpharm_erp.db')
db.init_db()
seed_database(db)
seed_expanded_data(db)
print('DB ready')
" """,
        language="kotlin",
        caption="Listing 26-2. Manual install path."))

    s.append(h2("Environment variables worth setting", styles))
    s.append(make_table(
        ["Variable", "Dev default", "Purpose"],
        [
            ["MEDPHARM_TLS_MODE", "disable",
             "Plaintext HTTP during local dev"],
            ["MEDPHARM_DEBUG", "true",
             "Flask debug mode; autoreload and verbose errors"],
            ["MEDPHARM_JWT_SECRET", "(dev-default)",
             "Override to test refresh logic explicitly"],
            ["MEDPHARM_FIELD_KEY", "(auto-generated)",
             "For testing encryption rotation"],
            ["MEDPHARM_DB_PATH", "medpharm_erp.db",
             "Point at a throwaway DB during tests"],
        ],
        col_widths=[1.7 * inch, 1.3 * inch, 3.3 * inch]))

    s.append(h2("Editor configuration", styles))
    s.append(p(
        "The project does not ship an editor configuration, but "
        "all Python files are PEP 8 formatted with two small "
        "tolerances: lines may exceed 79 columns up to 100, and "
        "double-quoted strings are the norm. The Swift code is "
        "Swift-Format-defaulted. Kotlin uses the Android Studio "
        "defaults. C# uses the Visual Studio / Rider defaults. "
        "Reformat anything you touch if it deviates.",
        styles))

    s.append(PageBreak())
    return s


def chapter_27_testing(styles):
    s = chapter_header("27", "Running Tests and Smoke Checks", styles)
    s.append(p(
        "MedPharm does not currently maintain an exhaustive unit "
        "test suite — an honest statement that should be understood "
        "as \"there is room to help.\" What does exist is a "
        "deliberate set of smoke checks that exercise the "
        "application's critical paths end-to-end. Passing them is "
        "the bar a pull request must clear.",
        styles))

    s.append(h2("The CI smoke suite", styles))
    s.append(p(
        "The GitHub Actions workflow "
        + c(".github/workflows/docker-publish.yml") + " runs the "
        "following in sequence on every tag push:",
        styles))
    s.append(bullets([
        c("python -m py_compile") + " against every module under "
        + c("api/") + ", " + c("database/") + ", and "
        + c("web/") + ". Catches syntax errors.",
        "Database initialisation — creates a throwaway SQLite "
        "file, runs both seed scripts. Catches ORM misconfiguration.",
        "API app creation — constructs the Flask application and "
        "queries " + c("/api/v1/health") + ". Catches blueprint "
        "registration bugs.",
        "Web portal app creation — renders "
        + c("/login") + ". Catches template errors.",
        "Docker image build — end-to-end container bring-up. "
        "Catches Dockerfile mistakes.",
    ], styles))

    s.append(h2("Running smoke checks locally", styles))
    s.extend(code_block("""source venv/bin/activate
python3 -m py_compile api/app.py api/auth.py api/routes.py \\
    database/models.py database/db_manager.py \\
    web/app.py web/routes.py

python3 -c "
import sys, os; sys.path.insert(0, os.getcwd())
from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from api.app import create_cloud_app
import tempfile
tmp = tempfile.mktemp(suffix='.db')
db = DatabaseManager(tmp); db.init_db(); seed_database(db)
app = create_cloud_app(db); client = app.test_client()
r = client.get('/api/v1/health'); assert r.status_code == 200
os.unlink(tmp); print('API OK')
" """,
        language="kotlin",
        caption="Listing 27-1. The minimum pre-commit smoke sequence."))

    s.append(h2("End-to-end tests for new features", styles))
    s.append(p(
        "When adding a feature that crosses the wire, write a "
        "short end-to-end test script that logs in, exercises the "
        "happy path, and verifies the expected DB state. The "
        "messaging feature (1.7.5) was validated this way before "
        "merge — see the commit message for that release for a "
        "concrete example.",
        styles))

    s.append(h2("Client-side testing", styles))
    s.append(p(
        "Each native client has standard platform tooling: "
        "XCTest on iOS/macOS, JUnit/Espresso on Android, xUnit on "
        ".NET. None is currently integrated into the CI pipeline; "
        "contributing a scaffold for any of them is an open "
        "invitation. In the meantime, clients are validated by "
        "manual testing against a running backend.",
        styles))

    s.append(PageBreak())
    return s


def chapter_28_branching(styles):
    s = chapter_header("28", "Branching, Commits, and Pull Requests", styles)
    s.append(p(
        "The project uses a plain single-main-branch workflow. "
        "Feature branches merge to " + c("master") + " via pull "
        "request; releases are cut by tagging "
        + c("master") + " with " + c("v1.7.x") + ".",
        styles))

    s.append(h2("Commit message conventions", styles))
    s.append(bullets([
        "Subject line ≤ 70 characters, imperative mood.",
        "Prefix with a subsystem or area name when helpful: "
        + c("Qt:") + ", " + c("api:") + ", "
        + c("android:") + ", etc.",
        "Body paragraphs explain " + i("why") + ", not "
        + i("what") + " — the diff shows what.",
        "End with a " + c("Co-Authored-By:") + " trailer for "
        "pair-programmed or AI-assisted work.",
    ], styles))

    s.append(h2("Pull request checklist", styles))
    s.append(bullets([
        "Smoke checks (Chapter 27) pass locally.",
        "New or changed routes are documented in Appendix C "
        "(endpoint catalogue).",
        "New models include a migration SQL file in "
        + c("docs/migrations/") + " if they add columns to "
        "existing tables.",
        "PHI-touching code paths emit audit and PHI access logs.",
        "Secrets are not committed. "
        + c(".env") + " and " + c("*.key") + " files are "
        ".gitignored; verify before pushing.",
        "The PR description includes a test plan.",
    ], styles))

    s.append(PageBreak())
    return s


def chapter_29_release(styles):
    s = chapter_header("29", "Release Engineering", styles)
    s.append(p(
        "Releases bump the version, rebuild the PDFs, push to "
        "Docker Hub, and push the tag to GitHub. The mechanics are "
        "mechanical; the judgement is in picking the right version "
        "increment.",
        styles))

    s.append(h2("Version policy", styles))
    s.append(bullets([
        "Major (x.0.0) — incompatible API changes. Has not "
        "happened yet; when it does, " + c("v2") + " blueprint "
        "coexists with " + c("v1") + ".",
        "Minor (1.x.0) — new feature areas, additive API changes, "
        "new clients.",
        "Patch (1.7.x) — bug fixes and small additive changes that "
        "do not break older clients.",
    ], styles))

    s.append(h2("The release sequence", styles))
    s.append(bullets([
        "Bump version strings — "
        + c("__init__.py") + ", "
        + c("run_qt.py") + ", "
        + c("api/{app,routes,fhir}.py") + ", "
        + c("install.sh") + " banner, "
        + c("Dockerfile") + "s, "
        + c("SECURITY.md") + ", HIPAA doc header, "
        + c("android/app/build.gradle.kts") + ", iOS/macOS version "
        "strings, Windows " + c(".csproj") + ", k8s defaults, the "
        "three PDF generators.",
        "Do not bump — kotlinx-coroutines library version "
        "(it happens to equal 1.7.x), historical references in "
        "the service manual.",
        "Add the new tag to the supported-tags list in "
        + c("README.md") + " without removing older tags.",
        "Regenerate all three PDFs.",
        "Commit everything with a "
        + c("Release X.Y.Z: <one-line summary>") + " subject.",
        "Tag with " + c("git tag -a vX.Y.Z -m '...'") + ".",
        "Push " + c("master") + " and the tag.",
        "Verify CI built the Docker images. If CI is blocked, "
        "build and push manually (see the Docker chapter).",
    ], styles))

    s.append(PageBreak())
    return s


def chapter_30_debugging(styles):
    s = chapter_header("30", "Debugging Techniques and Tooling", styles)
    s.append(p(
        "Debugging is the skill the manual cannot teach but can "
        "scaffold. This chapter lists the techniques that have "
        "proven most useful on MedPharm, arranged by the "
        "subsystem they apply to.",
        styles))

    s.append(h2("The SQL dump", styles))
    s.append(p(
        "When an ORM query produces surprising results, the first "
        "thing to do is see the SQL. Set "
        + c("echo=True") + " on the engine temporarily in "
        + c("DatabaseManager.init_db") + " and re-run. SQLAlchemy "
        "will print every statement, and the cause of an N+1 or a "
        "missing filter is usually obvious after fifteen seconds "
        "of log scanning.",
        styles))

    s.append(h2("The HTTP replay", styles))
    s.append(p(
        "When a client bug appears to be server-side, capture the "
        "actual request with " + c("curl -v") + " against the "
        "running backend — the Android app's "
        + c("OkHttp") + " logging interceptor and the iOS "
        + c("URLSession") + " console output both give the URL, "
        "headers, and body. A reproducible "
        + c("curl") + " makes subsequent debugging mechanical.",
        styles))

    s.append(h2("The debugger", styles))
    s.append(p(
        "The Python debugger (" + c("import pdb; pdb.set_trace()")
        + " or, on 3.7+, " + c("breakpoint()") + ") works fine in "
        "development. In Qt, it does not play well with the event "
        "loop; for Qt debugging, prefer structured logging or a "
        "remote debugger from an IDE. For mobile clients, use the "
        "platform debugger — Xcode's or Android Studio's.",
        styles))

    s.append(h2("Responsible disclosure of security issues", styles))
    s.append(p(
        f"If you discover a security vulnerability, do not open a "
        f"public GitHub issue. Write to {mail()} with subject "
        f"prefix {c('[security]')} and a private description of "
        f"the issue. Expect an acknowledgement within one business "
        f"day; a fix timeline will be coordinated privately. "
        f"Disclosure to third parties is appropriate only after a "
        f"fix has shipped and affected operators have been "
        f"notified.",
        styles))

    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART VII — EXTENDING MEDPHARM
# ═════════════════════════════════════════════════════════════════════════════

def chapter_31_add_model(styles):
    s = chapter_header("31", "Recipe — Adding a New Model", styles)
    s.append(p(
        "When to reach for this recipe: a new table is needed to "
        "store a concept that does not fit an existing table. Not "
        "when an existing table needs a new column — that is a "
        "column-add and a migration, not a model addition.",
        styles))

    s.append(h2("Step 1 — Design the columns", styles))
    s.append(p(
        "Before writing any code, list the columns. For each, ask: "
        "is this PHI? Is it queryable? Is it a finite set (→ "
        "enum)? Does it reference another table (→ ForeignKey + "
        "relationship)? The Service Manual's Part II has a "
        "useful checklist.",
        styles))

    s.append(h2("Step 2 — Add the model class", styles))
    s.append(p(
        "Place the class in the topically appropriate group in "
        + c("database/models.py") + ". If you are adding a new "
        "group entirely, add a banner comment. Remember to add a "
        + c("relationship()") + " on both sides of any "
        + c("ForeignKey") + ".",
        styles))

    s.append(h2("Step 3 — Extend the import list in db_manager", styles))
    s.append(p(
        "The top of " + c("database/db_manager.py") + " imports "
        "every model explicitly. Add your new class there so that "
        "queries can refer to it.",
        styles))

    s.append(h2("Step 4 — Add DatabaseManager methods", styles))
    s.append(p(
        "Typical new methods: "
        + c("create_<thing>") + ", "
        + c("get_<thing>") + ", "
        + c("list_<thing>s") + ", "
        + c("update_<thing>") + ", "
        + c("delete_<thing>") + ". Each opens a "
        + c("get_session()") + " contextmanager and returns "
        "plain-dict data where possible.",
        styles))

    s.append(h2("Step 5 — Migration SQL (if live deployments exist)", styles))
    s.append(p(
        "Produce "
        + c("docs/migrations/YYYYMMDD_add_<thing>.sql") + " with "
        "the " + c("CREATE TABLE") + " and any supporting "
        "indices. Operators apply migrations manually on "
        "existing deployments.",
        styles))

    s.append(h2("Step 6 — Wire it to the API", styles))
    s.append(p(
        "See Chapter 32.",
        styles))

    s.append(h2("Step 7 — Wire it to the clients", styles))
    s.append(p(
        "If the new thing is patient-visible, add it to the web "
        "portal and the four native clients. Chapter 34 covers "
        "the client-side recipe.",
        styles))

    s.append(PageBreak())
    return s


def chapter_32_add_endpoint(styles):
    s = chapter_header("32", "Recipe — Adding a New API Endpoint", styles)
    s.append(p(
        "You have a DatabaseManager method and want to expose it "
        "over HTTP. This is the shortest recipe in the manual.",
        styles))

    s.append(h2("Step 1 — Pick a URL", styles))
    s.append(bullets([
        "Under " + c("/patient/") + " if a patient is the caller.",
        "Under " + c("/staff/") + " if a staff member is the "
        "caller.",
        "Plural collection, singular detail. Verbs as actions at "
        "the leaf.",
    ], styles))

    s.append(h2("Step 2 — Write the route", styles))
    s.extend(code_block("""@api_bp.route("/staff/widgets", methods=["GET"])
@staff_required
def staff_list_widgets():
    widgets = g.db_manager.list_widgets()
    return jsonify({"widgets": widgets})


@api_bp.route("/staff/widgets", methods=["POST"])
@staff_required
def staff_create_widget():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    widget_id = g.db_manager.create_widget(
        name=name, created_by=g.current_user_id)
    return jsonify({"widget_id": widget_id}), 201""",
        language="python",
        caption="Listing 32-1. A complete pair of CRUD endpoints."))

    s.append(h2("Step 3 — Document in Appendix C", styles))
    s.append(p(
        "Every new endpoint must land in the API endpoint "
        "catalogue (Appendix C) in the same pull request. An "
        "endpoint that is not documented is an endpoint the "
        "clients cannot find.",
        styles))

    s.append(h2("Step 4 — Smoke-test", styles))
    s.append(p(
        "Add a one-liner to the smoke check (Chapter 27) that "
        "exercises the new endpoint against a throwaway database. "
        "Takes a minute; prevents the new endpoint from silently "
        "breaking in a future refactor.",
        styles))

    s.append(PageBreak())
    return s


def chapter_33_add_module(styles):
    s = chapter_header("33", "Recipe — Adding a New Clinical Module", styles)
    s.append(p(
        "A clinical module is a larger piece of functionality — a "
        "new navigation destination in the Qt app, a corresponding "
        "page in the web portal, API endpoints, and client "
        "support on the native platforms. The messaging feature "
        "(1.7.5) is the canonical recent example and a good "
        "template.",
        styles))

    s.append(h2("Step 1 — Model and DB methods", styles))
    s.append(p(
        "Follow Chapter 31 to add whatever tables and "
        "DatabaseManager methods the module needs.",
        styles))

    s.append(h2("Step 2 — API routes", styles))
    s.append(p(
        "Follow Chapter 32 for each endpoint. Group related routes "
        "under a banner comment in "
        + c("api/routes.py") + ".",
        styles))

    s.append(h2("Step 3 — Qt widget", styles))
    s.append(bullets([
        "Create " + c("qt_app/widgets/<name>_widget.py") + ".",
        "Import it in " + c("qt_app/main_window.py") + ".",
        "Add a tuple to " + c("NAV_ITEMS") + ".",
        "Add a " + c("self.stack.addWidget(...)") + " line in the "
        "same order.",
    ], styles))

    s.append(h2("Step 4 — Web portal page", styles))
    s.append(bullets([
        "Add a route function to " + c("web/routes.py") + ".",
        "Add a template under "
        + c("web/templates/") + ". Extend "
        + c("base.html") + ".",
        "Add a nav link to " + c("base.html") + ".",
    ], styles))

    s.append(h2("Step 5 — Native clients", styles))
    s.append(p(
        "See Chapter 34 for the client-side recipe. Add the "
        "feature to Android, iOS, macOS, and Windows in the same "
        "pull request or a follow-up labelled with the same "
        "feature name.",
        styles))

    s.append(tip(
        "If the feature is large, land it in phases: backend + "
        "Qt first (one PR), web portal next, each mobile/desktop "
        "client in its own PR. This reduces review surface and "
        "reduces rollback risk.",
        styles))

    s.append(PageBreak())
    return s


def chapter_34_add_client(styles):
    s = chapter_header("34", "Recipe — Adding a New Client Platform", styles)
    s.append(p(
        "Adding a whole new client platform — say, a tvOS patient "
        "check-in kiosk, or a Rust command-line client for "
        "operators — is a larger undertaking than adding a "
        "feature to an existing client. This recipe sketches the "
        "work.",
        styles))

    s.append(h2("Step 1 — Minimum viable client", styles))
    s.append(bullets([
        "HTTP client library with TLS.",
        "Secure storage for the access and refresh tokens "
        "(platform-appropriate: Keychain, KeyStore, DPAPI, etc.).",
        "Model types matching the API JSON shapes.",
        "At minimum: login, one happy-path screen, logout.",
    ], styles))

    s.append(h2("Step 2 — Server-URL override", styles))
    s.append(p(
        "Every existing client exposes a " + c("Server URL") + " "
        "field on the login screen with a \"Reset to default\" "
        "button. Honour this convention — operators rely on it "
        "for pointing demo builds at staging backends.",
        styles))

    s.append(h2("Step 3 — Network security", styles))
    s.append(bullets([
        "Require TLS by default.",
        "Provide a documented path for accepting a self-signed "
        "cert during development (e.g. user-installed CA on "
        "Android, trust store modification on iOS).",
        "Never ship with certificate verification disabled; when "
        "tempted, add a developer-only flag behind a build "
        "configuration rather than hardcoding.",
    ], styles))

    s.append(h2("Step 4 — Build and packaging", styles))
    s.append(p(
        "Document the build steps in "
        + c("docs/COMPILATION.md") + " alongside the existing "
        "platforms. Include platform-specific signing "
        "requirements.",
        styles))

    s.append(h2("Step 5 — Feature parity", styles))
    s.append(p(
        "Once the client is booted, working backwards through the "
        "feature list from the nearest existing client — Android "
        "if the new platform is mobile, Windows if it is desktop "
        "— is the fastest way to approach parity. The existing "
        "clients already provide the reference UX flows; your job "
        "is to translate them into idiomatic code for the new "
        "platform.",
        styles))

    s.append(h2("Step 6 — Update the manual", styles))
    s.append(p(
        "Add a chapter to Part IV of this manual describing the "
        "new client's layout, idioms, and quirks. A new client "
        "without a corresponding manual chapter is an undocumented "
        "liability.",
        styles))

    s.append(PageBreak())
    return s


# ═════════════════════════════════════════════════════════════════════════════
# PART VIII — APPENDICES
# ═════════════════════════════════════════════════════════════════════════════

def appendix_a_file_tour(styles):
    s = appendix_header("A", "File-by-File Code Tour", styles)
    s.append(p(
        "This appendix is the reference you reach for when someone "
        "asks \"where does the code for X live?\". Files are grouped "
        "by area; for each, the one-line purpose and the most "
        "important classes or functions are listed.",
        styles))

    s.append(h2("Database layer", styles))
    s.append(make_table(
        ["Path", "Purpose / key symbols"],
        [
            ["database/models.py",
             "All 50+ SQLAlchemy ORM classes and 20+ enums. "
             "Base class, relationships, table args."],
            ["database/db_manager.py",
             "DatabaseManager. Session lifecycle, every CRUD, "
             "business logic that spans rows."],
            ["database/seed_data.py",
             "Seeds baseline fixtures — users, patients, "
             "medications, interactions. Idempotent."],
            ["database/seed_expanded.py",
             "Seeds reference data — symptoms (30+), conditions "
             "(25+), additional medications."],
        ],
        col_widths=[2.1 * inch, 4.3 * inch]))

    s.append(h2("API layer", styles))
    s.append(make_table(
        ["Path", "Purpose / key symbols"],
        [
            ["api/app.py",
             "create_cloud_app factory. CORS, security middleware, "
             "blueprint registration."],
            ["api/auth.py",
             "JWT create/decode, @token_required, @patient_required, "
             "@staff_required, @admin_required."],
            ["api/routes.py",
             "api_bp blueprint. All /api/v1/* endpoints."],
            ["api/fhir.py",
             "FHIR R4 CapabilityStatement and resource adapters."],
        ],
        col_widths=[2.1 * inch, 4.3 * inch]))

    s.append(h2("Security layer", styles))
    s.append(make_table(
        ["Path", "Purpose / key symbols"],
        [
            ["security/encryption.py",
             "FieldCipher. encrypt_field / decrypt_field. Key rotation."],
            ["security/audit.py",
             "Helpers to emit AuditLog and PHIAccessLog rows from "
             "middleware."],
            ["security/csrf.py",
             "csrf_required decorator for web portal."],
            ["security/lockout.py",
             "LockoutTracker. AccountLockedError."],
            ["security/passwords.py",
             "PasswordPolicy. validate_password. Password reuse check."],
            ["security/sessions.py",
             "Flask-session lifecycle; session regeneration on auth."],
            ["security/totp.py",
             "TOTP generate/verify; enrollment URL; backup codes."],
            ["security/emergency.py",
             "Break-glass grant, verify, expire, review."],
            ["security/phi.py",
             "Catalogue of PHI columns. Used by audit helpers."],
            ["security/config.py",
             "SecurityConfig dataclass; env-driven tunables."],
        ],
        col_widths=[2.1 * inch, 4.3 * inch]))

    s.append(h2("Qt desktop", styles))
    s.append(make_table(
        ["Path", "Purpose"],
        [
            ["qt_app/main_window.py",
             "MainWindow, NAV_ITEMS, navigation stack."],
            ["qt_app/styles.py", "Global QSS stylesheet."],
            ["qt_app/dialogs/login_dialog.py", "Staff login modal."],
            ["qt_app/widgets/dashboard_widget.py", "KPIs, today's activity."],
            ["qt_app/widgets/patient_widget.py",
             "Master-detail patient panel + Notes tab."],
            ["qt_app/widgets/prescription_widget.py",
             "Prescription list + creation dialog with DDI check."],
            ["qt_app/widgets/medication_widget.py",
             "Formulary browser."],
            ["qt_app/widgets/appointment_widget.py",
             "Calendar scheduling."],
            ["qt_app/widgets/records_widget.py",
             "Medical records list + new-record dialog."],
            ["qt_app/widgets/billing_widget.py",
             "Invoices, payments, insurance claims, processing."],
            ["qt_app/widgets/messages_widget.py",
             "Secure messaging (staff side)."],
            ["qt_app/widgets/symptoms_widget.py",
             "Symptoms + conditions reference browser."],
            ["qt_app/widgets/analytics_widget.py",
             "matplotlib-powered charts."],
        ],
        col_widths=[2.5 * inch, 3.9 * inch]))

    s.append(h2("Web portal", styles))
    s.append(make_table(
        ["Path", "Purpose"],
        [
            ["web/app.py", "create_app factory."],
            ["web/routes.py",
             "portal_bp. Login, register, dashboard, prescriptions, "
             "billing, records, appointments, medications, profile, "
             "messages."],
            ["web/templates/*.html", "Jinja2 templates; extend base.html."],
            ["web/static/css/style.css", "Dark-gradient theme."],
            ["web/static/vendor/*", "Bootstrap, Font Awesome, Google Fonts."],
        ],
        col_widths=[2.5 * inch, 3.9 * inch]))

    s.append(h2("Native clients", styles))
    s.append(make_table(
        ["Path root", "Language / purpose"],
        [
            ["android/", "Kotlin; Jetpack / Retrofit MVVM."],
            ["ios/MedPharm/", "Swift; SwiftUI / async-await."],
            ["macos/MedPharm/", "Swift; SwiftUI / NavigationSplitView."],
            ["windows/MedPharm/", ".NET 8; WPF MVVM."],
        ],
        col_widths=[2.0 * inch, 4.4 * inch]))

    s.append(h2("Ops / deployment", styles))
    s.append(make_table(
        ["Path", "Purpose"],
        [
            ["Dockerfile", "API-only image (Ubuntu 24.04 LTS)."],
            ["server/Dockerfile",
             "Full stack (Nginx + API + portal + supervisord)."],
            ["server/supervisord.conf",
             "Process manager for the full-stack image."],
            ["server/nginx/", "Nginx configs and TLS generation."],
            ["docker-compose.yml",
             "Local build-from-source compose."],
            ["docker-compose.hub.yml",
             "Pull-from-Docker-Hub compose (API)."],
            ["server/docker-compose.hub.yml",
             "Pull-from-Docker-Hub compose (full stack)."],
            ["install.sh", "OS-detection installer."],
            ["uninstall.sh", "Reverse installer."],
            ["start_*.sh", "Quick-launch wrappers."],
            ["generate_docs.sh", "Regenerates Volume I PDF."],
            ["k8s/", "Kubernetes Kustomize base + cloud overlays."],
            [".github/workflows/docker-publish.yml",
             "CI/CD — build, test, push."],
        ],
        col_widths=[2.5 * inch, 3.9 * inch]))

    s.append(h2("Documentation", styles))
    s.append(make_table(
        ["Path", "Purpose"],
        [
            ["docs/generate_pdf.py",
             "Volume I (Technical Reference) generator."],
            ["docs/generate_service_manual.py",
             "Volume II (Service Manual) generator."],
            ["docs/generate_developer_manual.py",
             "Volume III (this manual) generator."],
            ["docs/API.md", "REST API Markdown reference."],
            ["docs/CLIENTS.md", "Multi-platform client notes."],
            ["docs/INSTALLATION.md", "Install paths and troubleshooting."],
            ["docs/KUBERNETES.md", "Kubernetes walkthrough."],
            ["docs/COMPILATION.md", "Compilation instructions."],
            ["docs/SERVER.md", "Full-stack server notes."],
            ["docs/HIPAA_COMPLIANCE.md", "Compliance mapping."],
            ["docs/BAA_TEMPLATE.md", "Business Associate Agreement template."],
            ["docs/BREACH_NOTIFICATION.md", "Breach notification procedure."],
        ],
        col_widths=[2.7 * inch, 3.7 * inch]))

    s.append(PageBreak())
    return s


def appendix_b_schema(styles):
    s = appendix_header("B", "Complete SQL Schema (Excerpted)", styles)
    s.append(p(
        "This appendix excerpts the "
        + c("CREATE TABLE") + " statements that SQLAlchemy emits "
        "from " + c("database/models.py") + ". Column types are "
        "shown in their SQLite equivalents; ORM-level types like "
        + c("Enum") + " are rendered as " + c("VARCHAR(32)") + " "
        "after SQLAlchemy maps them. Constraints and indices are "
        "preserved.",
        styles))

    s.append(h2("Core tables", styles))
    s.extend(code_block("""CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(32) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    license_number VARCHAR(50),
    specialization VARCHAR(200),
    created_at DATETIME,
    is_active BOOLEAN DEFAULT 1,
    UNIQUE (username),
    UNIQUE (email)
);
CREATE INDEX ix_users_username ON users (username);

CREATE TABLE patients (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(32),
    ssn_last4 VARCHAR(4),
    email VARCHAR(200),
    phone VARCHAR(20),
    address VARCHAR(300),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    blood_type VARCHAR(32),
    created_at DATETIME,
    is_active BOOLEAN DEFAULT 1
);
CREATE INDEX ix_patients_name ON patients (last_name, first_name);""",
        language="sql",
        caption="Listing B-1. users and patients tables."))

    s.append(h2("Clinical tables", styles))
    s.extend(code_block("""CREATE TABLE prescriptions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    rx_number VARCHAR(30) NOT NULL UNIQUE,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    prescriber_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(32) DEFAULT 'pending',
    prescribed_date DATE,
    expiry_date DATE,
    notes TEXT
);

CREATE TABLE prescription_items (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id),
    medication_id INTEGER NOT NULL REFERENCES medications(id),
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    quantity INTEGER DEFAULT 0,
    refills_allowed INTEGER DEFAULT 0,
    refills_used INTEGER DEFAULT 0,
    instructions TEXT
);

CREATE TABLE appointments (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    provider_id INTEGER NOT NULL REFERENCES users(id),
    scheduled_datetime DATETIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    appointment_type VARCHAR(32),
    status VARCHAR(32) DEFAULT 'scheduled',
    reason TEXT,
    notes TEXT
);
CREATE INDEX ix_appointments_datetime ON appointments (scheduled_datetime);""",
        language="sql",
        caption="Listing B-2. prescriptions, prescription_items, appointments."))

    s.append(h2("Messaging and notes (1.7.5)", styles))
    s.extend(code_block("""CREATE TABLE message_threads (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    provider_id INTEGER REFERENCES users(id),
    subject VARCHAR(200) NOT NULL,
    created_at DATETIME,
    last_message_at DATETIME,
    is_closed BOOLEAN DEFAULT 0
);
CREATE INDEX ix_message_threads_patient_id ON message_threads(patient_id);
CREATE INDEX ix_message_threads_provider_id ON message_threads(provider_id);
CREATE INDEX ix_message_threads_last_message_at ON message_threads(last_message_at);

CREATE TABLE secure_messages (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL REFERENCES message_threads(id),
    sender_type VARCHAR(20) NOT NULL,
    sender_id INTEGER NOT NULL,
    body_encrypted TEXT NOT NULL,
    sent_at DATETIME,
    read_at DATETIME
);

CREATE TABLE provider_notes (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    author_id INTEGER NOT NULL REFERENCES users(id),
    body_encrypted TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);
CREATE INDEX ix_provider_notes_patient_id ON provider_notes(patient_id);
CREATE INDEX ix_provider_notes_author_id ON provider_notes(author_id);
CREATE INDEX ix_provider_notes_created_at ON provider_notes(created_at);""",
        language="sql",
        caption="Listing B-3. Messaging and private-notes tables (added in 1.7.5)."))

    s.append(PageBreak())
    return s


def appendix_c_endpoints(styles):
    s = appendix_header("C", "API Endpoint Catalogue", styles)
    s.append(p(
        "Every /api/v1 endpoint is listed here with method, path, "
        "required role, and a one-line description. When you add "
        "or remove an endpoint, update this appendix in the same "
        "commit.",
        styles))

    s.append(h2("Authentication", styles))
    s.append(make_table(
        ["Method", "Path", "Auth", "Description"],
        [
            ["POST", "/auth/login/patient", "public", "Patient login."],
            ["POST", "/auth/login/staff", "public", "Staff login."],
            ["POST", "/auth/register", "public", "Patient self-registration (4-factor)."],
            ["POST", "/auth/refresh", "public", "Exchange refresh for access token."],
        ],
        col_widths=[0.6 * inch, 2.0 * inch, 0.7 * inch, 3.0 * inch]))

    s.append(h2("Health and reference", styles))
    s.append(make_table(
        ["Method", "Path", "Auth", "Description"],
        [
            ["GET", "/health", "public", "Liveness probe."],
            ["GET", "/medications/search", "token", "Search formulary."],
            ["GET", "/medications/<id>", "token", "Medication detail."],
            ["GET", "/reference/symptoms", "token", "Symptom search."],
            ["GET", "/reference/symptoms/body-systems", "token", "List of body systems."],
            ["GET", "/reference/conditions", "token", "Condition search."],
            ["GET", "/reference/conditions/categories", "token", "List of condition categories."],
        ],
        col_widths=[0.6 * inch, 2.6 * inch, 0.7 * inch, 2.4 * inch]))

    s.append(h2("Patient endpoints", styles))
    s.append(make_table(
        ["Method", "Path", "Description"],
        [
            ["GET", "/patient/dashboard", "Dashboard KPIs and recent activity."],
            ["GET", "/patient/profile", "Patient demographics + insurance + allergies."],
            ["PUT", "/patient/profile", "Update phone/email/address."],
            ["GET", "/patient/prescriptions", "List prescriptions (optional ?status=)."],
            ["POST", "/patient/prescriptions/<id>/refill", "Request a refill."],
            ["GET", "/patient/billing", "Invoices, payments, balance."],
            ["POST", "/patient/billing/<id>/pay", "Submit payment."],
            ["GET", "/patient/records", "Medical records (optional ?type=)."],
            ["GET", "/patient/appointments", "Upcoming and past appointments."],
            ["GET", "/patient/medications", "Current medication list."],
            ["GET", "/patient/notifications", "Aggregated notifications (upcoming, overdue)."],
            ["GET", "/patient/insurance", "Patient's insurance records."],
            ["GET", "/patient/insurance/claims", "Claim history."],
            ["POST", "/patient/insurance/claims", "Submit a claim."],
            ["GET", "/patient/messages", "List message threads."],
            ["POST", "/patient/messages", "Start a new thread."],
            ["GET", "/patient/messages/<id>", "Read a thread (and mark read)."],
            ["POST", "/patient/messages/<id>/reply", "Reply to a thread."],
            ["GET", "/patient/messages/providers", "List providers for compose dropdown."],
        ],
        col_widths=[0.6 * inch, 2.8 * inch, 3.0 * inch]))

    s.append(h2("Staff endpoints", styles))
    s.append(make_table(
        ["Method", "Path", "Description"],
        [
            ["GET", "/staff/dashboard", "Staff dashboard stats and recent activity."],
            ["GET", "/staff/patients", "List/search patients."],
            ["GET", "/staff/patients/<id>", "Full patient record."],
            ["GET", "/staff/appointments", "Appointments by date or provider."],
            ["GET", "/staff/prescriptions", "Prescriptions (optional ?patient_id=)."],
            ["GET", "/staff/analytics/revenue", "Revenue by month."],
            ["GET", "/staff/analytics/top-medications", "Top prescribed medications."],
            ["GET", "/staff/analytics/demographics", "Patient demographics."],
            ["GET", "/staff/insurance/claims", "All claims (filterable)."],
            ["POST", "/staff/insurance/claims/<id>/process", "Approve/deny/pay a claim."],
            ["GET", "/staff/messages", "All threads; filter by patient_id."],
            ["GET", "/staff/messages/<id>", "Read a thread (and mark read)."],
            ["POST", "/staff/messages/<id>/reply", "Reply to a thread."],
            ["POST", "/staff/messages/<id>/close", "Close a thread."],
            ["GET", "/staff/patients/<pid>/notes", "List the current user's notes for this patient."],
            ["POST", "/staff/patients/<pid>/notes", "Create a private note."],
            ["GET", "/staff/notes/<id>", "Read a private note (if author)."],
            ["PUT", "/staff/notes/<id>", "Update a private note (if author)."],
            ["DELETE", "/staff/notes/<id>", "Delete a private note (if author)."],
        ],
        col_widths=[0.7 * inch, 2.8 * inch, 2.9 * inch]))

    s.append(PageBreak())
    return s


def appendix_d_errors(styles):
    s = appendix_header("D", "HTTP Error Codes and Meanings", styles)
    s.append(p(
        "Clients should rely on the HTTP status code for "
        "programmatic behaviour and the JSON "
        + c("error") + " message only for display. The table below "
        "summarises how each status is used across the API.",
        styles))

    s.append(make_table(
        ["Status", "Meaning in this API"],
        [
            ["200 OK", "GET succeeded."],
            ["201 Created", "POST that created a resource. Body includes the new id."],
            ["204 No Content", "Rare; used for acknowledgements without a body."],
            ["400 Bad Request", "Malformed or missing parameters."],
            ["401 Unauthorized", "Missing, invalid, or expired bearer token. Client should refresh or re-login."],
            ["403 Forbidden", "Authenticated but not permitted. CSRF failure on portal."],
            ["404 Not Found", "Resource does not exist or is not visible to the caller."],
            ["409 Conflict", "State collision (duplicate unique value, closed thread)."],
            ["429 Too Many Requests", "Lockout active. Body includes retry_after_seconds."],
            ["500 Internal Server Error", "Unhandled exception; check the server log."],
            ["502/503/504", "Upstream/proxy issue; not emitted by Flask itself."],
        ],
        col_widths=[1.3 * inch, 5.1 * inch]))

    s.append(PageBreak())
    return s


def appendix_e_glossary(styles):
    s = appendix_header("E", "Glossary of Terms", styles)
    s.append(make_table(
        ["Term", "Meaning"],
        [
            ["BAA", "Business Associate Agreement. Required under HIPAA "
                    "between a covered entity and any vendor that handles PHI."],
            ["Break-the-glass", "Time-boxed, logged override of normal access "
                                "control. See EmergencyAccessGrantRec."],
            ["Covered Entity",
             "Under HIPAA, a health plan, healthcare clearinghouse, or "
             "healthcare provider that electronically transmits health "
             "information."],
            ["DDI", "Drug-Drug Interaction. Checked via "
                    "MedicationInteraction pairs when a prescription is created."],
            ["DEA Schedule",
             "US Drug Enforcement Administration classification (I–V) of a "
             "controlled substance. Stored on Medication."],
            ["DPAPI",
             "Windows Data Protection API. Used to encrypt tokens in the "
             "Windows client."],
            ["Fernet",
             "Symmetric encryption scheme combining AES-128-CBC with "
             "HMAC-SHA256. Used for field-level encryption."],
            ["FHIR R4",
             "Fast Healthcare Interoperability Resources, Release 4. An "
             "HL7 standard; MedPharm exposes a small FHIR R4 surface via "
             "api/fhir.py."],
            ["JWT",
             "JSON Web Token. MedPharm implements a narrow, handwritten "
             "HMAC-SHA256 variant."],
            ["LOINC",
             "Logical Observation Identifiers Names and Codes. Used on "
             "LabOrder and LabResult."],
            ["NDC",
             "National Drug Code. Ten- or eleven-digit identifier for a "
             "specific drug product."],
            ["PHI",
             "Protected Health Information. Anything that can identify a "
             "patient plus a health fact."],
            ["POCO",
             "Plain Old C# Object. Used to describe simple data carriers "
             "in the Windows client."],
            ["PRG",
             "POST / Redirect / GET. Web pattern that prevents form "
             "resubmission on refresh."],
            ["TOTP",
             "Time-based One-Time Password. RFC 6238. Basis of MFA."],
            ["WAL",
             "SQLite Write-Ahead Logging mode. Preferred over the default "
             "rollback-journal for concurrent reads."],
        ],
        col_widths=[1.5 * inch, 4.9 * inch]))

    s.append(PageBreak())
    return s


def appendix_f_support(styles):
    s = appendix_header("F", "Revision History and Support", styles)
    s.append(p(
        "This volume is a living document. Each substantive "
        "revision is numbered against the MedPharm release with "
        "which it shipped, followed by a letter marking revisions "
        "of the manual itself within that release.",
        styles))

    s.append(h2("Revision history", styles))
    s.append(make_table(
        ["Revision", "Date", "Author", "Summary"],
        [
            ["1.7.6-A", datetime.now().strftime("%d %b %Y"),
             "R. Stillwell",
             "Reissued for the 1.7.6 product line. Notes the PDF "
             "rendering fixes applied to this volume (cover-page navy "
             "backdrop no longer bleeds onto body pages; spurious "
             "blank pages before part dividers removed; output now "
             "linearised as PDF 1.5 for browser viewers) and the "
             "ngrok-tunnel onboarding flow available to operators "
             "exposing the API across firewalls or NAT."],
            ["1.7.5-A", "20 Apr 2026",
             "R. Stillwell",
             "Initial issue of the developer manual."],
        ],
        col_widths=[1.0 * inch, 1.2 * inch, 1.3 * inch, 2.9 * inch]))

    s.append(h2("Support contacts", styles))
    s.append(make_table(
        ["Channel", "Address", "Use for"],
        [
            ["Email (general)", SUPPORT_EMAIL,
             "Questions, clarifications, corrections"],
            ["Email (security)", SUPPORT_EMAIL + " (prefix [security])",
             "Suspected security vulnerabilities"],
            ["Email (manual updates)", SUPPORT_EMAIL + " (prefix [devmanual])",
             "Manual errata and expansion requests"],
            ["GitHub Issues", REPO_URL + "/issues",
             "Non-confidential bug reports, feature requests"],
            ["Docker Hub", DOCKERHUB_URL,
             "Official container images"],
            ["Company", COMPANY_URL,
             "Enlightec Ltd. (publisher)"],
        ],
        col_widths=[1.7 * inch, 2.5 * inch, 2.2 * inch]))

    s.append(h2("How to contribute to this manual", styles))
    s.append(p(
        f"The manual is generated by "
        f"{c('docs/generate_developer_manual.py')}. To propose a "
        f"change, edit that file, run it to regenerate the PDF, "
        f"verify the output opens cleanly in Adobe Acrobat Reader "
        f"(or any modern PDF viewer), and submit a pull request. "
        f"For substantive structural changes, discuss by email "
        f"({mail()}) before investing significant time — the "
        f"editorial decisions about part ordering, signal-word "
        f"usage, and level of detail are coordinated across all "
        f"three volumes.",
        styles))

    s.append(h2("Document integrity", styles))
    s.append(p(
        "Each authoritative revision is hashed and the hash "
        "published alongside the PDF on the MedPharm release "
        "page. Engineers downloading the manual may verify that "
        "their copy matches the authoritative version. "
        + "The hash algorithm is SHA-256 over the raw PDF bytes.",
        styles))

    s.append(Spacer(1, 0.4 * inch))
    s.append(Paragraph(
        "<i>End of the MedPharm ERP Developer Manual, "
        "Volume III, Revision 1.7.6-A.</i>",
        ParagraphStyle("EndSig", parent=styles["DM_Body"],
                       alignment=TA_CENTER, textColor=SLATE,
                       fontName="Helvetica-Oblique")))
    return s


# ═════════════════════════════════════════════════════════════════════════════
# ASSEMBLE AND BUILD
# ═════════════════════════════════════════════════════════════════════════════

def assemble_story(styles):
    story = []

    # Title page (uses "title" template). build_cover() switches to the
    # plain "content" template before its trailing PageBreak so the navy
    # backdrop does not bleed past the cover.
    story.append(Paragraph("<!--title-->", ParagraphStyle("tx", parent=styles["Normal"])))  # placeholder
    story += build_cover(styles)

    # Front matter
    story += build_colophon(styles)
    story += build_foreword(styles)
    story += build_how_to_use(styles)
    story += build_conventions(styles)
    story += build_toc(styles)

    # Part I
    story += part_divider("I", "Foundations",
        "A new engineer's orientation — what MedPharm is, why it "
        "was built the way it is, and how its pieces fit together.",
        styles)
    story += chapter_01_vision(styles)
    story += chapter_02_stack(styles)
    story += chapter_03_architecture(styles)
    story += chapter_04_layout(styles)

    # Part II
    story += part_divider("II", "The Data Model",
        "Every table the system stores, why it looks the way it "
        "does, and how the models relate to each other in code and "
        "in the runtime graph.",
        styles)
    story += chapter_05_db_philosophy(styles)
    story += chapter_06_core_models(styles)
    story += chapter_07_clinical_models(styles)
    story += chapter_08_financial_models(styles)
    story += chapter_09_hipaa_models(styles)
    story += chapter_10_messaging_notes(styles)

    # Part III
    story += part_divider("III", "The Backend",
        "From the Flask application factory to the DatabaseManager "
        "to the JWT handler — the server-side code paths an engineer "
        "touches on a typical day.",
        styles)
    story += chapter_11_db_manager(styles)
    story += chapter_12_encryption(styles)
    story += chapter_13_rest_api(styles)
    story += chapter_14_jwt(styles)
    story += chapter_15_csrf_lockout_mfa(styles)
    story += chapter_16_web_portal(styles)

    # Part IV
    story += part_divider("IV", "The Clients",
        "Five client surfaces share one backend. Each chapter "
        "describes the idioms, the code layout, and the conventions "
        "to follow when extending that client.",
        styles)
    story += chapter_17_qt_desktop(styles)
    story += chapter_18_android(styles)
    story += chapter_19_ios(styles)
    story += chapter_20_macos(styles)
    story += chapter_21_windows(styles)

    # Part V
    story += part_divider("V", "Cross-Cutting Concerns",
        "Audit, encryption at rest, TLS, Docker, Kubernetes — the "
        "systems that span every layer and determine how the whole "
        "product behaves in production.",
        styles)
    story += chapter_22_audit(styles)
    story += chapter_23_tls(styles)
    story += chapter_24_docker(styles)
    story += chapter_25_kubernetes(styles)

    # Part VI
    story += part_divider("VI", "Development Workflow",
        "How to get a working build, what tests to run, how to "
        "land a change, how releases are cut, and what to do when "
        "something breaks.",
        styles)
    story += chapter_26_dev_env(styles)
    story += chapter_27_testing(styles)
    story += chapter_28_branching(styles)
    story += chapter_29_release(styles)
    story += chapter_30_debugging(styles)

    # Part VII
    story += part_divider("VII", "Extending MedPharm",
        "Recipes for the four most common expansion tasks: a new "
        "model, a new endpoint, a new clinical module, and a new "
        "client platform.",
        styles)
    story += chapter_31_add_model(styles)
    story += chapter_32_add_endpoint(styles)
    story += chapter_33_add_module(styles)
    story += chapter_34_add_client(styles)

    # Part VIII
    story += part_divider("VIII", "Appendices",
        "The reference tables. File tours, schema listings, "
        "endpoint catalogues, error codes, glossary, and contact "
        "information.",
        styles)
    story += appendix_a_file_tour(styles)
    story += appendix_b_schema(styles)
    story += appendix_c_endpoints(styles)
    story += appendix_d_errors(styles)
    story += appendix_e_glossary(styles)
    story += appendix_f_support(styles)

    return story


def _optimize_pdf_for_web(path):
    """Linearize the PDF and rewrite as v1.5 via Ghostscript. Linearized
    ("Fast Web View") files render reliably in pdf.js — the viewer
    GitHub embeds for in-browser preview — and stream the first page
    before the full file has loaded. No-op if Ghostscript isn't on PATH.
    """
    import shutil, subprocess, tempfile
    gs = shutil.which("gs")
    if not gs:
        return False
    fd, tmp_path = tempfile.mkstemp(suffix=".pdf",
                                   dir=os.path.dirname(path) or None)
    os.close(fd)
    try:
        result = subprocess.run([
            gs, "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            "-dPDFSETTINGS=/default",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dFastWebView=true",
            f"-sOutputFile={tmp_path}",
            path,
        ], check=False, capture_output=True)
        if result.returncode == 0 and os.path.getsize(tmp_path) > 1024:
            os.replace(tmp_path, path)
            return True
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return False


def build():
    styles = build_styles()
    doc = DevManualDoc(OUTPUT_PATH)
    story = assemble_story(styles)

    # The 'title' template drives only the cover; the body uses
    # 'content' (a NextPageTemplate at the end of build_cover handles the
    # transition). Part divider pages paint their own navy backdrop from
    # within the PartBanner flowable, so the per-template approach is
    # not used for them.
    doc.build(story)
    web_opt = _optimize_pdf_for_web(OUTPUT_PATH)
    size = os.path.getsize(OUTPUT_PATH)
    suffix = " (linearized)" if web_opt else ""
    print(f"Wrote {OUTPUT_PATH} ({size:,} bytes){suffix}")


if __name__ == "__main__":
    build()
