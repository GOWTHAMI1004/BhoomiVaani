import io
import logging
from html import escape
from datetime import datetime
from typing import List
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
            [Paragraph("<b>Demo Title Note:</b>", body_style), Paragraph(f"<b>{land.legal_status}</b>", body_style),
             Paragraph("<b>Synthetic Demo Index:</b>", body_style), Paragraph(f"<b>{land.growth_score} / 100</b>", body_style)]
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
        elements.append(Paragraph("2. SYNTHETIC DEMO RISK ENTRIES — NOT A TITLE ASSESSMENT", section_heading))
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
            no_risks_box = [[Paragraph(
                "<b>No risk entries are listed in this synthetic demo record.</b><br/>"
                "No title search or encumbrance check was performed. The absence of a listed risk does not establish clear title.",
                body_style,
            )]]
            no_risks_table = Table(no_risks_box, colWidths=[540])
            no_risks_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
                ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
                ("PADDING", (0, 0), (-1, -1), 8)
            ]))
            elements.append(no_risks_table)

        elements.append(Spacer(1, 10))

        # Infrastructure Evidence Status
        elements.append(Paragraph("3. SYNTHETIC INFRASTRUCTURE ENTRIES — NOT INDEPENDENTLY VERIFIED", section_heading))
        infra_rows = [
            [
                Paragraph("<b>Demo Entry</b>", body_style),
                Paragraph("<b>Demo Label</b>", body_style),
                Paragraph("<b>Illustrative Distance</b>", body_style),
                Paragraph("<b>Synthetic Source / Remarks</b>", body_style)
            ]
        ]
        for inf in land.infrastructure_evidence:
            infra_rows.append([
                Paragraph(inf.claim, body_style),
                Paragraph(f"<font color='#B45309'><b>{inf.status}</b></font>", body_style),
                Paragraph(f"{inf.distance_km} km", body_style),
                Paragraph(inf.evidence_source, body_style)
            ])
        if not land.infrastructure_evidence:
            infra_rows.append([
                Paragraph("No infrastructure entries are listed in this synthetic record.", body_style),
                Paragraph("Not assessed", body_style),
                Paragraph("N/A", body_style),
                Paragraph("No independent infrastructure lookup was performed.", body_style),
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
            "<b>DISCLAIMER:</b> BhoomiVaani provides synthetic demonstration information for property awareness. "
            "Neither BhoomiVaani nor Gnani AI provides certified legal title opinions. Always consult a licensed property advocate."
        )
        elements.append(Paragraph(footer_text, subtitle_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_case_report(self, report: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=42,
            leftMargin=42,
            topMargin=42,
            bottomMargin=42,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CaseReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#193b2a"),
            spaceAfter=8,
        )
        heading_style = ParagraphStyle(
            "CaseReportHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#244b36"),
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "CaseReportBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            spaceAfter=4,
            wordWrap="CJK",
        )
        elements = [
            Paragraph("PRELIMINARY AWARENESS REPORT — NOT INDEPENDENTLY VERIFIED", ParagraphStyle(
                "CaseReportBanner",
                parent=body_style,
                textColor=colors.HexColor("#991B1B"),
                alignment=1,
                fontName="Helvetica-Bold",
                backColor=colors.HexColor("#FEE2E2"),
                borderColor=colors.HexColor("#DC2626"),
                borderWidth=1,
                borderPadding=7,
            )),
            Spacer(1, 10),
            Paragraph("BhoomiVaani Land-Buying Report", title_style),
            Paragraph(f"Generated: {datetime.now().strftime('%d-%b-%Y')}", body_style),
        ]

        def display(value: object) -> str:
            if value is None or value == "":
                return "Not provided"
            if isinstance(value, bool):
                return "Yes" if value else "No"
            text = str(value)
            unsupported_scripts = (
                (0x0900, 0x0DFF),
            )
            if any(
                start <= ord(character) <= end
                for character in text
                for start, end in unsupported_scripts
            ):
                return "[Original-language text is not supported by this PDF font; see the conversation in BhoomiVaani.]"
            return text

        def add_section(title: str, lines: List[str]) -> None:
            elements.append(Paragraph(escape(title), heading_style))
            if not lines:
                lines = ["No information was provided."]
            for line in lines:
                safe_line = escape(line).replace("\n", "<br/>")
                elements.append(Paragraph(safe_line, body_style))

        buyer = report.get("buyer_requirements", {})
        add_section("1. Buyer requirements and preferences", [
            f"Buying intent: {display(buyer.get('buying_intent'))}",
            f"Preferred location: {display(buyer.get('preferred_location'))}",
            f"Land type: {display(buyer.get('land_type'))}",
            f"Required acreage: {display(buyer.get('acreage'))}",
            f"Budget: {display(buyer.get('budget'))}",
            f"Intended purpose: {display(buyer.get('intended_purpose'))}",
            f"Broker approached: {display(buyer.get('broker_status'))}",
            f"Evidence status: {display(buyer.get('evidence_status'))}",
            *[f"Preference or concern shared: {display(item)}" for item in buyer.get("other_preferences", [])],
        ])

        property_info = report.get("property", {})
        add_section("2. Property details", [
            f"Property: {display(property_info.get('name'))}",
            f"Location: {display(property_info.get('location'))}",
            f"District: {display(property_info.get('district'))}",
            f"Survey reference: {display(property_info.get('survey_reference'))}",
            f"Area: {display(property_info.get('area_acres'))} acres",
            f"Land type: {display(property_info.get('land_type'))}",
            f"Recorded asking price: {display(property_info.get('asking_price_lakhs'))} lakhs",
            f"Listing data classification: {display(report.get('evidence_classification'))}",
        ])

        add_section("3. Conversation notes supplied by the buyer", [
            f"Buyer: {display(item)}" for item in buyer.get("conversation_statements", [])
        ])

        claims = report.get("broker_claims", [])
        claim_lines = []
        for claim in claims:
            claim_lines.append(
                f"Claim: {display(claim.get('claim'))} | Status: {display(claim.get('status'))} | "
                f"Evidence: {display(claim.get('evidence'))}"
            )
            claim_lines.extend(
                f"Required check: {display(item)}" for item in claim.get("required_checks", [])
            )
        add_section("4. Broker or seller claims and evidence status", claim_lines or [
            "No broker or seller claim was identified in the conversation."
        ])

        document_analysis = report.get("document_analysis", {})
        document_lines = [
            f"Overall status: {display(document_analysis.get('status'))}",
            display(document_analysis.get("detail")),
        ]
        for item in document_analysis.get("documents", []):
            document_lines.append(f"Document: {display(item.get('filename'))}")
            document_lines.append(f"Text-scan summary: {display(item.get('summary'))}")
            document_lines.append(
                f"Survey numbers found in text: {display(', '.join(item.get('survey_numbers_found', [])))}"
            )
            for issue in item.get("detected_issues", []):
                document_lines.append(
                    f"Pattern flag ({display(issue.get('risk_level'))}): "
                    f"{display(issue.get('issue_title'))} — {display(issue.get('explanation'))}"
                )
            document_lines.append(display(item.get("disclaimer")))
        add_section("5. Uploaded document analysis", document_lines)

        ownership = report.get("ownership_and_title", {})
        doc_status = document_analysis.get("detail", "")
        encumbrances = report.get("encumbrance_indicators", [])
        checks = [
            f"Ownership and title: {display(ownership.get('status'))}. {display(ownership.get('detail'))}",
            f"Document review: {display(doc_status)}",
            f"Claim verification: {display(report.get('claim_verification', {}).get('detail'))}",
        ]
        for item in encumbrances:
            checks.append(
                f"Record indicator ({display(item.get('severity'))}): "
                f"{display(item.get('risk_type'))} — {display(item.get('description'))}"
            )
        add_section("6. Ownership, registration, encumbrance, and litigation checks", checks)

        infrastructure = report.get("infrastructure", [])
        infra_lines = [
            f"{display(item.get('claim'))}: {display(item.get('status'))}; "
            f"{display(item.get('distance_km'))} km; source: {display(item.get('evidence_source'))}. "
            "This entry is not independently verified."
            for item in infrastructure
        ]
        add_section("7. Infrastructure, connectivity, water, and electricity", infra_lines or [
            "No parcel-specific infrastructure, road access, water, or electricity information was verified."
        ])

        add_section("Potential advantages", [
            f"- {display(item)}" for item in report.get("potential_advantages", [])
        ])
        add_section("8. Identified risks and missing information", [
            f"Risk: {display(item.get('risk_type'))} ({display(item.get('severity'))}) — "
            f"{display(item.get('description'))} Next step: {display(item.get('recommended_action'))}"
            for item in report.get("potential_risks", [])
        ] + [
            f"Missing: {display(item)}" for item in report.get("missing_documents", [])
        ])

        financial = report.get("financial_breakdown", {})
        add_section("9. Financial breakdown (figures are not valuations)", [
            f"Budget stated: {display(financial.get('buyer_budget_as_stated'))}",
            f"Broker price per acre as stated: {display(financial.get('broker_asking_price_per_acre_as_stated'))}",
            f"Area: {display(financial.get('property_area_acres'))} acres",
            f"Asking price per acre: {display(financial.get('asking_price_per_acre_lakhs'))} lakhs",
            f"Total asking price: {display(financial.get('asking_price_total_lakhs'))} lakhs",
            f"Estimate status: {display(financial.get('estimate_status'))}",
            display(financial.get("note")),
        ])

        comparison = report.get("property_comparison", {})
        add_section("10. Property comparison and recommendations", [
            f"Status: {display(comparison.get('status'))}",
            display(comparison.get("detail")),
            *[
                f"Comparison record: {display(item)}"
                for item in comparison.get("properties", [])
            ],
        ])

        add_section("11. Questions to ask the seller or broker", [
            f"- {display(item)}" for item in report.get("seller_questions", [])
        ])
        add_section("12. Recommended next steps", [
            f"- {display(item)}" for item in report.get("recommended_next_steps", [])
        ])

        assessment = report.get("overall_assessment", {})
        add_section("13. Overall assessment and confidence", [
            f"Assessment: {display(assessment.get('status'))}",
            f"Confidence: {display(assessment.get('confidence'))}",
            display(assessment.get("detail")),
            f"Report confidence: {display(report.get('confidence'))}",
        ])
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            escape(display(report.get("disclaimer"))),
            ParagraphStyle(
                "CaseReportDisclaimer",
                parent=body_style,
                textColor=colors.HexColor("#7F1D1D"),
                fontName="Helvetica-Bold",
            ),
        ))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

report_service = ReportService()
