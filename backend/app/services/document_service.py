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
                        "The document references an outstanding bank loan, hypothecation, or mortgage registered against the property. "
                        "If the seller defaults, the lending institution retains first charge and can auction the land under the SARFAESI Act."
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
                    "Reference to an active court suit (OS number), court injunction, or succession dispute was detected. "
                    "Purchasing property under active litigation (Doctrine of Lis Pendens, Section 52 Transfer of Property Act) "
                    "binds the buyer to the court decree."
                ),
                lawyer_questions=[
                    "What is the current status of the civil suit on the e-Courts portal?",
                    "Have all legal heirs, including daughters and sons, executed a registered family partition or settlement deed?",
                    "Is there an interim stay or status-quo order restraining alienation?"
                ]
            ))
            risk_score += 35
            break

        # 3. Check for Missing Signatures / Unsigned Co-parceners
        if "missing" in text_lower or "unsigned" in text_lower or "not attached" in text_lower or "[missing" in text_lower:
            detected_issues.append(DetectedIssue(
                issue_title="Missing Signatures or Missing Supporting Attachments",
                risk_level="HIGH",
                snippet="Clauses indicate missing co-parcener signatures or unattached bank release receipts.",
                explanation=(
                    "Key signatories or vital title annexures appear unexecuted or omitted from the deed schedule. "
                    "Unsigned joint owners can later file to void the conveyance."
                ),
                lawyer_questions=[
                    "Are all co-owners and lawful title holders signing as Executants before the Sub-Registrar?",
                    "Are all previous 30-year link documents physically available in original form?"
                ]
            ))
            risk_score += 20

        # 4. Check for Survey Number Discrepancy / Acreage Variance
        if any(w in text_lower for w in ["survey variance", "demarcation has not", "acreage difference", "variance", "encroach"]):
            detected_issues.append(DetectedIssue(
                issue_title="Cadastral Survey Number or Acreage Discrepancy",
                risk_level="MEDIUM",
                snippet="Variance detected between recorded revenue extent and physical site boundary claims.",
                explanation=(
                    "A mismatch exists between the land area recorded in government village revenue records (1-B/Dharani) "
                    "and the physical field boundary claimed by the seller."
                ),
                lawyer_questions=[
                    "Can an official revenue demarcation (F-Line petition) be conducted by the Mandal Surveyor prior to token advance?",
                    "Do physical survey boundary stones match the official village revenue cadastral map?"
                ]
            ))
            risk_score += 15

        # 5. Clean Title Check
        if not detected_issues:
            if "nil" in text_lower and ("mortgage" in text_lower or "encumbrance" in text_lower) and "clean" in text_lower or "pattadar" in text_lower:
                detected_issues.append(DetectedIssue(
                    issue_title="Clean Title Record Indicators Present",
                    risk_level="CLEAR",
                    snippet="30-year encumbrance search reflects NIL registered charges. Prohibited list check: NOT LISTED.",
                    explanation=(
                        "The document exhibits standard positive markers: zero registered mortgages, clear ancestral devolution, "
                        "and absence from Government Section 22-A prohibited property lists."
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
            f"Analysis of '{filename}' identified {len(detected_issues)} key legal title items. "
            f"Overall legal risk status is assessed as {overall_level} (Score {risk_score}/100)."
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
            ai_mode="MOCK AI"
        )

document_service = DocumentService()
