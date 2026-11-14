import re
import io
import logging
from typing import List, Tuple
from pypdf import PdfReader
from app.models.document import DocumentAnalysisResponse, DetectedIssue

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Analyzes legal property documents (sale deeds, agreements, Dharani passbooks, encumbrance extracts).
    Identifies high-risk warning signs, liens, and title defects.
    """

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """
        Safely extracts raw text from PDF or plain text files.
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                extracted_pages = []
                for idx, page in enumerate(reader.pages[:20]): # limit to 20 pages max
                    page_text = page.extract_text() or ""
                    extracted_pages.append(page_text)
                return "\n".join(extracted_pages)
            except Exception as e:
                logger.error(f"Error parsing PDF file {filename}: {str(e)}")
                raise ValueError(f"Unable to read PDF document: {str(e)}")
        else:
            # Plain text or UTF-8 decode
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="replace")

    def analyze_document(self, text: str, filename: str) -> DocumentAnalysisResponse:
        """
        Scans document text for known risk indicators, survey numbers, and mortgages.
        Guarded against prompt injection by strictly treating content as passive text data.
        """
        # Guard against excessive length
        clean_text = text[:50000]
        text_lower = clean_text.lower()

        detected_issues: List[DetectedIssue] = []
        survey_numbers = list(set(re.findall(r"\b(?:SY|SY\.|SURVEY|S\.NO|RS)\s*[-/:]?\s*(\d+[A-Za-z0-9/\-_]*)", clean_text, re.IGNORECASE)))

        risk_score = 10 # baseline minimal risk

        # 1. Check for Mortgage / Bank Lien / Hypothecation
        mortgage_patterns = [
            r"hypothecat\w+",
            r"bank\s+lien",
            r"collateral\s+security",
            r"outstanding\s+sum",
            r"loan\s+a/c",
            r"unreleased\s+charge",
            r"mortgage\w*"
        ]
        mortgage_found = False
        for pattern in mortgage_patterns:
            if mortgage_found:
                break
            for m in re.finditer(pattern, text_lower):
                # Check surrounding context for negation e.g. "mortgages registered: nil"
                window = text_lower[max(0, m.start() - 30): min(len(text_lower), m.end() + 40)]
                if re.search(r"(?:registered\s*:\s*nil|:\s*nil|:\s*none|no\s+mortgage|nil\s+registered)", window):
                    continue
                mortgage_found = True
                start = max(0, m.start() - 60)
                end = min(len(clean_text), m.end() + 120)
                snippet = clean_text[start:end].strip().replace("\n", " ")

                detected_issues.append(DetectedIssue(
                    issue_title="Undischarged Mortgage / Bank Hypothecation Detected",
                    risk_level="CRITICAL",
                    snippet=f"... {snippet} ...",
                    explanation=(
                        "The uploaded text contains a reference to a bank loan, hypothecation, or mortgage. "
                        "This text scan cannot establish whether the entry is current, registered, or discharged."
                    ),
                    lawyer_questions=[
                        "Has the seller obtained an unconditional No Objection Certificate (NOC) and loan closure certificate from the lender?",
                        "Is there a registered Deed of Release / Reconveyance executed at the Sub-Registrar Office?",
                        "Does the latest Encumbrance Certificate (Form 15) reflect a zero encumbrance status?"
                    ]
                ))
                risk_score += 45
                break

        # 2. Check for Pending Court Litigation / Succession disputes / OS No.
        court_matches = re.finditer(r"(o\.?s\.?\s*(?:no\.?)?\s*\d+/\d+|pending\s+before|sub-court|civil\s+court|injunction|suit\s+pending|co-parcen\w+|unilateral\s+partition|disputing)", text_lower)
        for m in court_matches:
            # Check for negation e.g. "court injunctions: nil"
            window = text_lower[max(0, m.start() - 30): min(len(text_lower), m.end() + 40)]
            if re.search(r"(?:injunctions\s*:\s*nil|:\s*nil|:\s*none|no\s+injunction)", window):
                continue
            start = max(0, m.start() - 60)
            end = min(len(clean_text), m.end() + 120)
            snippet = clean_text[start:end].strip().replace("\n", " ")

            detected_issues.append(DetectedIssue(
                issue_title="Active Civil Litigation / Co-Parcenary Inheritance Dispute",
                risk_level="HIGH",
                snippet=f"... {snippet} ...",
                explanation=(
                    "The uploaded text contains a court-suit, injunction, or succession-dispute reference. "
                    "This scan cannot confirm whether the matter is active; have an advocate check authoritative court records."
                ),
                lawyer_questions=[
                    "What is the current status of the civil suit on the e-Courts portal?",
                    "Have all legal heirs, including daughters and sons, executed a registered family partition or settlement deed?",
                    "Is there an interim stay or status-quo order restraining alienation?"
                ]
            ))
            risk_score += 35
            break

        # 3. Flag text patterns that may refer to missing signatures or attachments.
        if "missing" in text_lower or "unsigned" in text_lower or "not attached" in text_lower or "[missing" in text_lower:
            detected_issues.append(DetectedIssue(
                issue_title="Missing Signatures or Missing Supporting Attachments",
                risk_level="HIGH",
                snippet="Clauses indicate missing co-parcener signatures or unattached bank release receipts.",
                explanation=(
                    "The text scan found terms such as missing, unsigned, or not attached. "
                    "Review the original document and context with a qualified property advocate."
                ),
                lawyer_questions=[
                    "Are all co-owners and lawful title holders signing as Executants before the Sub-Registrar?",
                    "Are all previous 30-year link documents physically available in original form?"
                ]
            ))
            risk_score += 20

        # 4. Flag references to possible survey or acreage differences without asserting one exists.
        variance_match = re.search(
            r"survey variance|demarcation has not|acreage difference|variance|encroach",
            text_lower,
        )
        if variance_match:
            start = max(0, variance_match.start() - 60)
            end = min(len(clean_text), variance_match.end() + 120)
            snippet = clean_text[start:end].strip().replace("\n", " ")
            detected_issues.append(DetectedIssue(
                issue_title="Possible Survey or Acreage Discrepancy Mentioned",
                risk_level="MEDIUM",
                snippet=f"... {snippet} ...",
                explanation=(
                    "The uploaded text mentions a possible variance or encroachment. This scan does not compare official "
                    "revenue records with a physical boundary or establish that a mismatch exists."
                ),
                lawyer_questions=[
                    "Can an official revenue demarcation (F-Line petition) be conducted by the Mandal Surveyor prior to token advance?",
                    "Do physical survey boundary stones match the official village revenue cadastral map?"
                ]
            ))
            risk_score += 15

        # 5. Surface explicit no-encumbrance statements without treating them as verification.
        if not detected_issues:
            no_encumbrance_assertion = re.search(
                r"(?:\b(?:mortgage|encumbrance|lien)\w*\b.{0,40}\b(?:nil|none|not\s+listed|no\s+record)\b"
                r"|\b(?:nil|none|no\s+record)\b.{0,40}\b(?:mortgage|encumbrance|lien)\w*\b)",
                text_lower,
            )
            if no_encumbrance_assertion:
                detected_issues.append(DetectedIssue(
                    issue_title="Text Contains an Assertion of No Recorded Encumbrance",
                    risk_level="LOW",
                    snippet="The uploaded text contains statements such as NIL or NOT LISTED; they have not been independently checked.",
                    explanation=(
                        "These are assertions within the uploaded document, not independently verified findings. "
                        "They do not establish clear title, complete ownership, or a current encumbrance status."
                    ),
                    lawyer_questions=[
                        "Obtain fresh EC (Encumbrance Certificate) from Sub-Registrar covering up to the current registration date.",
                        "Verify physical agricultural possession and verify neighbor boundary declarations."
                    ]
                ))
                risk_score = 15

        risk_score = min(100, risk_score)
        if risk_score >= 70:
            overall_level = "CRITICAL"
        elif risk_score >= 45:
            overall_level = "HIGH"
        elif risk_score >= 25:
            overall_level = "MODERATE"
        else:
            overall_level = "LOW"

        summary_msg = (
            f"A rule-based text scan of '{filename}' found {len(detected_issues)} matching pattern(s). "
            f"Text-pattern indicator: {overall_level} (score {risk_score}/100). This is not a legal-risk or title assessment."
        )

        return DocumentAnalysisResponse(
            filename=filename,
            total_characters=len(clean_text),
            overall_risk_score=risk_score,
            risk_level=overall_level,
            detected_issues=detected_issues,
            summary=summary_msg,
            survey_numbers_found=survey_numbers,
            encumbrance_clauses_found=mortgage_found,
            evidence_type="USER_PROVIDED_DOCUMENT_TEXT",
            ai_mode="RULE_BASED_DOCUMENT_SCAN"
        )

document_service = DocumentService()
