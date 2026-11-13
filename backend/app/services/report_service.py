import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.land import LandListing

logger = logging.getLogger(__name__)

class ReportService:
    """
    Generates downloadable, print-ready PDF property intelligence reports.
    Uses ReportLab to build structured documents with synthetic disclaimers.
    """

    def generate_land_report(self, land: LandListing) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom styles with BhoomiVaani palette
        primary_color = colors.HexColor("#0F3826")   # Forest Green
        secondary_color = colors.HexColor("#B45309") # Gold/Amber
        danger_color = colors.HexColor("#DC2626")    # Red
        neutral_dark = colors.HexColor("#1F2937")    # Charcoal
        light_bg = colors.HexColor("#F8F9FA")

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=primary_color,
            spaceAfter=4,
            fontName="Helvetica-Bold"
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4B5563")
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=primary_color,
            spaceBefore=12,
            spaceAfter=6,
            fontName="Helvetica-Bold"
        )

        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=neutral_dark
        )

        disclaimer_banner_style = ParagraphStyle(
            "DisclaimerBanner",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#991B1B"),
            alignment=1, # Centered
            fontName="Helvetica-Bold"
        )

        elements = []

        # Top Watermark / Disclaimer Banner
        banner_text = (
            "DEMONSTRATION REPORT - SYNTHETIC DATA - NOT AN OFFICIAL LAND CERTIFICATE<br/>"
            "This report is generated for awareness purposes only. Never execute property transactions without advocate verification."
        )
        banner_table = Table([[Paragraph(banner_text, disclaimer_banner_style)]], colWidths=[540])
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEE2E2")),
            ("BORDER", (0, 0), (-1, -1), 1, danger_color),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 10))

        # Brand Header
        header_table_data = [
            [
                Paragraph("<b>BhoomiVaani</b> | Land Intelligence Dossier", title_style),
                Paragraph(f"Generated: {datetime.now().strftime('%d-%b-%Y')}<br/>Listing ID: {land.id}", subtitle_style)
            ]
        ]
        header_table = Table(header_table_data, colWidths=[380, 160])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=6, spaceAfter=10))

        # Property Overview Card
        elements.append(Paragraph("1. PROPERTY IDENTIFICATION & VALUATION", section_heading))
        prop_data = [
            [Paragraph("<b>Property Title:</b>", body_style), Paragraph(land.title, body_style),
             Paragraph("<b>Survey Number:</b>", body_style), Paragraph(f"<b>{land.survey_number}</b> (Mock)", body_style)],
            [Paragraph("<b>Location / Mandal:</b>", body_style), Paragraph(land.location, body_style),
             Paragraph("<b>District:</b>", body_style), Paragraph(land.district, body_style)],
            [Paragraph("<b>Total Extent:</b>", body_style), Paragraph(f"{land.acres} Acres", body_style),
             Paragraph("<b>Land Category:</b>", body_style), Paragraph(land.land_type, body_style)],
            [Paragraph("<b>Rate per Acre:</b>", body_style), Paragraph(f"₹{land.price_per_acre_lakhs} Lakhs", body_style),
             Paragraph("<b>Total Valuation:</b>", body_style), Paragraph(f"<b>₹{land.total_price_lakhs} Lakhs</b>", body_style)],
            [Paragraph("<b>Legal Title Status:</b>", body_style), Paragraph(f"<b>{land.legal_status}</b>", body_style),
             Paragraph("<b>AI Growth Score:</b>", body_style), Paragraph(f"<b>{land.growth_score} / 100</b>", body_style)]
        ]

        prop_table = Table(prop_data, colWidths=[110, 160, 110, 160])
        prop_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ]))
        elements.append(prop_table)
        elements.append(Spacer(1, 10))

        # Legal Risk Assessment
        elements.append(Paragraph("2. LEGAL RISK & ENCUMBRANCE ANALYSIS", section_heading))
        if land.legal_risks:
            risk_rows = [
                [
                    Paragraph("<b>Risk Classification</b>", body_style),
                    Paragraph("<b>Severity</b>", body_style),
                    Paragraph("<b>Description & Required Buyer Safeguard</b>", body_style)
                ]
            ]
            for r in land.legal_risks:
                risk_rows.append([
                    Paragraph(f"<b>{r.risk_type}</b>", body_style),
                    Paragraph(f"<font color='red'><b>{r.severity}</b></font>", body_style),
                    Paragraph(f"{r.description}<br/><b>Action:</b> {r.recommended_action}", body_style)
                ])

            risk_table = Table(risk_rows, colWidths=[140, 70, 330])
            risk_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEE2E2")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(risk_table)
        else:
            clean_box = [
                [Paragraph("<b>Status: CLEAN TITLE INDICATORS PRESENT</b><br/>"
                           "No registered bank mortgages, court injunctions, or Section 22-A prohibited records found in synthetic records. "
                           "30-year link records reflect clear ancestral title.", body_style)]
            ]
            clean_table = Table(clean_box, colWidths=[540])
            clean_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#10B981")),
                ("PADDING", (0, 0), (-1, -1), 8)
            ]))
            elements.append(clean_table)

        elements.append(Spacer(1, 10))

        # Infrastructure Evidence Status
        elements.append(Paragraph("3. INFRASTRUCTURE CLAIMS & EVIDENCE VERIFICATION", section_heading))
        infra_rows = [
            [
                Paragraph("<b>Claimed Infrastructure</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
                Paragraph("<b>Distance</b>", body_style),
                Paragraph("<b>Official Evidence Source / Remarks</b>", body_style)
            ]
        ]
        for inf in land.infrastructure_evidence:
            status_color = "#10B981" if inf.status in ["Operational", "Officially announced"] else "#F59E0B" if inf.status == "Proposed" else "#EF4444"
            infra_rows.append([
                Paragraph(inf.claim, body_style),
                Paragraph(f"<font color='{status_color}'><b>{inf.status}</b></font>", body_style),
                Paragraph(f"{inf.distance_km} km", body_style),
                Paragraph(inf.evidence_source, body_style)
            ])

        infra_table = Table(infra_rows, colWidths=[160, 110, 60, 210])
        infra_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(infra_table)
        elements.append(Spacer(1, 10))

        # Buyer Precautions Checklist
        elements.append(Paragraph("4. MANDATORY BUYER DUE DILIGENCE CHECKLIST", section_heading))
        precautions = [
            "1. <b>Physical Demarcation:</b> Commission an official survey through the Mandal Revenue Office (F-Line survey) before token advance.",
            "2. <b>Dharani Portal Verification:</b> Verify digital Pattadar Passbook, ROR 1-B, and Pahani records on the government Dharani portal.",
            "3. <b>30-Year Encumbrance Search:</b> Obtain certified Form 15 Encumbrance Certificate from the Sub-Registrar Office.",
            "4. <b>Master Plan Alignment:</b> Verify with HMDA / DTCP that the parcel is not marked under green belt conservation, lake FTL, or road acquisition buffers."
        ]
        for p in precautions:
            elements.append(Paragraph(p, body_style))
            elements.append(Spacer(1, 2))

        elements.append(Spacer(1, 10))
        # Final Footer Note
        footer_text = (
            "<b>DISCLAIMER:</b> BhoomiVaani provides AI-assisted synthetic intelligence for property awareness. "
            "Neither BhoomiVaani nor Gnani AI provides certified legal title opinions. Always consult a licensed property advocate."
        )
        elements.append(Paragraph(footer_text, subtitle_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

report_service = ReportService()
