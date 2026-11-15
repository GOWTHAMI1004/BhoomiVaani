import json
import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import settings
from app.models.ai import CharacterSpeechItem, ModelStatusItem
from app.models.land import LandListing
from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError
from app.services.language_service import detect_conversation_language

logger = logging.getLogger(__name__)


class ReasoningService:
    """Provider-neutral reasoning boundary with a Gemini generateContent adapter."""

    def __init__(self, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.provider = settings.reasoning_provider.upper()
        self.api_key = settings.reasoning_api_key
        self.api_base_url = settings.reasoning_api_base_url
        self.model = settings.reasoning_model
        self.timeout_seconds = settings.api_timeout_seconds
        self._transport = transport
        self.last_response_time_ms = 0.0

    def _gemini_configuration_error(self) -> Optional[str]:
        if not self.provider:
            return "Reasoning is unavailable: no external LLM provider has been selected."
        if self.provider != "GEMINI":
            return "Reasoning is unavailable: configure REASONING_PROVIDER=GEMINI to use the Gemini adapter."
        missing = [
            name for name, value in (
                ("REASONING_API_KEY", self.api_key),
                ("REASONING_API_BASE_URL", self.api_base_url),
                ("REASONING_MODEL", self.model),
            ) if not value.strip()
        ]
        if missing:
            return "Reasoning is unavailable: missing configuration " + ", ".join(missing) + "."
        return None

    @staticmethod
    def _language_name(language: str) -> str:
        return {
            "en": "English", "te": "Telugu", "hi": "Hindi", "ta": "Tamil",
            "kn": "Kannada", "ml": "Malayalam", "bn": "Bengali", "gu": "Gujarati",
            "pa": "Punjabi", "mr": "Marathi",
        }.get(language.lower().split("-", 1)[0], language)

    async def _generate_gemini_content(
        self, query: str, language: str, conversation_history: Optional[List[Dict[str, str]]],
        context: Dict[str, Any],
    ) -> str:
        configuration_error = self._gemini_configuration_error()
        if configuration_error:
            raise ProviderUnavailableError(configuration_error)

        language_name = self._language_name(language)
        system_instruction = (
            "You are Bhoomi, a careful, conversational land-purchase advisor. "
            f"Respond in {language_name}, the user's language for this turn. Preserve the language of code-mixed input. "
            "Ask at most one concise follow-up question when needed. Use only facts in the supplied context; "
            "never invent listings, prices, official records, facilities, legal findings, or verification. "
            "Clearly label synthetic demonstration records and user-provided claims. Never certify title, promise legal safety, "
            "or present this response as legal advice. If evidence is insufficient, say so plainly."
        )
        contents: List[Dict[str, Any]] = []
        for message in conversation_history or []:
            role = "model" if message.get("role") == "assistant" else "user"
            text = message.get("content")
            if role not in {"model", "user"} or not isinstance(text, str) or not text.strip():
                continue
            contents.append({"role": role, "parts": [{"text": text}]})
        context_text = json.dumps(context, ensure_ascii=False, default=str)
        contents.append({"role": "user", "parts": [{
            "text": f"Investigation context (data may be synthetic; follow its evidence labels):\n{context_text}\n\nUser's current message:\n{query}"
        }]})

        url = f"{self.api_base_url.rstrip('/')}/models/{self.model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1200},
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds, transport=self._transport
            ) as client:
                response = await client.post(
                    url,
                    headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                    json=payload,
                )
            if response.status_code in (401, 403):
                raise ProviderRequestError("Gemini rejected the configured API credentials (HTTP authentication error).")
            if response.status_code == 429:
                raise ProviderRequestError("Gemini rate limit reached. Please retry later.")
            if response.status_code >= 500:
                raise ProviderRequestError(f"Gemini is temporarily unavailable (HTTP {response.status_code}).")
            if response.status_code >= 400:
                raise ProviderRequestError(f"Gemini rejected the request (HTTP {response.status_code}). Check model and request configuration.")
            try:
                result = response.json()
                text = "".join(
                    part.get("text", "")
                    for candidate in result.get("candidates", [])[:1]
                    for part in candidate.get("content", {}).get("parts", [])
                    if isinstance(part.get("text"), str)
                ).strip()
            except (ValueError, AttributeError, TypeError) as exc:
                raise ProviderRequestError("Gemini returned an invalid response format.") from exc
            if not text:
                raise ProviderRequestError("Gemini returned no text for this request.")
            return text
        except ProviderRequestError:
            raise
        except httpx.TimeoutException as exc:
            raise ProviderRequestError("Gemini request timed out. Please retry.") from exc
        except httpx.HTTPError as exc:
            raise ProviderRequestError("Gemini could not be reached. Check network and endpoint configuration.") from exc

    async def get_active_model_info(self) -> Tuple[str, str, bool]:
        if not self.provider:
            return "UNCONFIGURED", "No reasoning provider selected", False
        error = self._gemini_configuration_error()
        if error:
            return self.provider, error, False
        return self.provider, f"Gemini generateContent ({self.model}) configured", False

    async def check_health(self) -> ModelStatusItem:
        configuration_error = self._gemini_configuration_error()
        configured = configuration_error is None
        return ModelStatusItem(
            model_name=self.model or "Unselected external reasoning model",
            provider=self.provider or "UNCONFIGURED",
            role="REASONING",
            connection_status="CONFIGURED" if configured else "NOT_CONFIGURED",
            is_live=False,
            endpoint=(f"{self.api_base_url.rstrip('/')}/models/{self.model}:generateContent" if configured else ""),
            last_ping_status="NOT_PROBED" if configured else ("INCOMPLETE_CONFIGURATION" if self.provider else "NO_PROVIDER_SELECTED"),
            supported_languages=[],
            note=("Gemini generateContent is configured; availability is confirmed only by a successful request." if configured else configuration_error or "Reasoning is unavailable until a provider is configured."),
        )

    async def investigate_collaborative(
        self,
        query: str,
        conversation_language: str = "en",
        available_lands: Optional[List[LandListing]] = None,
        selected_land_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        document_analyses: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        selected = self._select_land(query, available_lands or [], selected_land_id)
        context = {
            # Expose a synthetic parcel to the model only when this investigation
            # explicitly selected or uniquely matched it. Do not seed unrelated
            # locations that could be mistaken for buyer-provided facts.
            "available_properties": [selected.model_dump()] if selected else [],
            "selected_property_id": selected.id if selected else None,
            "document_analyses": document_analyses or [],
        }
        answer = await self._generate_gemini_content(query, conversation_language, conversation_history, context)
        report = self._build_case_report(query, conversation_history, selected, document_analyses)
        speech_item = CharacterSpeechItem(
            character="bhoomi",
            character_name="Bhoomi",
            role="LAND_ADVISOR",
            text=answer,
            voice_id="bhoomi",
            evidence_badge=("DEMO DATA" if selected else "GENERAL GUIDANCE"),
            evidence_type=("SYNTHETIC_DEMONSTRATION_DATA" if selected else "GENERAL_INFORMATION"),
            sentiment="analytical",
            animation_cue="speak",
        )
        return {
            "user_query": query,
            "conversation_language": conversation_language,
            "matched_land_ids": [selected.id] if selected else [],
            "dialogue_sequence": [speech_item.model_dump()],
            "model_used": self.model,
            "provider": "GEMINI",
            "is_live": True,
            "overall_risk_level": "SYNTHETIC_FLAGS_PRESENT" if selected and selected.legal_risks else "NOT_ASSESSED",
            "investigation_report": report,
        }

    def _select_land(
        self, query: str, available_lands: List[LandListing], selected_land_id: Optional[str]
    ) -> Optional[LandListing]:
        explicitly_selected = next(
            (land for land in available_lands if land.id == selected_land_id), None
        ) if selected_land_id else None
        query_lower = query.casefold()
        query_tokens = set(re.findall(r"[\w-]+", query_lower))
        normalized_query = re.sub(r"[^a-z0-9]", "", query_lower)
        area_matches = [
            float(match)
            for match in re.findall(
                r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:-?\s*(?:acres?|ac|ఎకరాలు|ఎకరం|ఎకరాల))",
                query_lower,
            )
        ]
        scores: List[Tuple[LandListing, int, bool]] = []
        for land in available_lands:
            score = 0
            specific_match = False
            if land.id.casefold() in query_lower:
                score += 100
                specific_match = True
            normalized_survey = re.sub(r"[^a-z0-9]", "", land.survey_number.casefold())
            if normalized_survey and normalized_survey in normalized_query:
                score += 80
                specific_match = True
            if any(phrase and phrase.casefold() in query_lower for phrase in (land.title, land.location)):
                score += 40
                specific_match = True
            location_tokens = set(re.findall(r"[\w-]+", land.location.casefold()))
            matched_location_tokens = query_tokens & location_tokens
            score += min(len(matched_location_tokens), 2) * 10
            specific_match = specific_match or bool(matched_location_tokens)
            title_tokens = set(re.findall(r"[\w-]+", land.title.casefold()))
            matched_title_tokens = query_tokens & title_tokens
            if len(matched_title_tokens) >= 2:
                score += 20
                specific_match = True
            if any(abs(area - land.acres) < 0.01 for area in area_matches):
                score += 15
            if score and specific_match:
                scores.append((land, score, specific_match))
        if not scores:
            return explicitly_selected
        best_score = max(score for _, score, _ in scores)
        best_matches = [land for land, score, _ in scores if score == best_score]
        if len(best_matches) == 1:
            return best_matches[0]
        if explicitly_selected and explicitly_selected in best_matches:
            return explicitly_selected
        return None

    def _build_report(self, land: Optional[LandListing]) -> Dict[str, Any]:
        if land is None:
            return {
                "property": {
                    "id": None,
                    "name": "No parcel selected",
                    "location": "Not provided",
                    "district": "Not provided",
                    "survey_reference": "Not provided",
                    "area_acres": None,
                    "asking_price_lakhs": None,
                    "land_type": "Not provided",
                },
                "ownership_and_title": {
                    "status": "NOT_ASSESSED",
                    "detail": "No parcel was uniquely identified. No ownership, title, encumbrance, survey, or location records were checked.",
                },
                "document_analysis": {
                    "status": "NOT_PROVIDED",
                    "detail": "No property documents were supplied for this general-awareness response.",
                },
                "encumbrance_indicators": [],
                "survey_and_boundary": {
                    "status": "NOT_ASSESSED",
                    "detail": "Select a parcel or provide its specific location or survey reference to frame a parcel-specific review.",
                },
                "infrastructure": [],
                "potential_risks": [],
                "missing_documents": [
                    "Exact property location and survey reference",
                    "Registered title deeds and complete chain of title",
                    "Current Encumbrance Certificate from the Sub-Registrar",
                    "Official revenue records and boundary survey",
                ],
                "recommended_next_steps": [
                    "Select a demonstration parcel or provide an exact location and survey reference.",
                    "Have an independent property advocate review original records.",
                    "Verify current certified records directly with the relevant authorities.",
                ],
                "evidence_classification": "NO_PROPERTY_DATA",
                "confidence": "NOT_ASSESSED",
                "disclaimer": "General awareness only. No parcel was identified; this is not property-specific, official verification, or legal advice.",
            }
        risks = [risk.model_dump() for risk in land.legal_risks]
        infrastructure = [item.model_dump() for item in land.infrastructure_evidence]
        return {
            "property": {
                "id": land.id,
                "name": land.title,
                "location": land.location,
                "district": land.district,
                "survey_reference": land.survey_number,
                "area_acres": land.acres,
                "asking_price_lakhs": land.total_price_lakhs,
                "land_type": land.land_type,
            },
            "ownership_and_title": {
                "status": "NOT_VERIFIED",
                "detail": "No owner identity, chain of title, or authoritative revenue record is available in this synthetic demo listing.",
            },
            "document_analysis": {
                "status": "NOT_PROVIDED",
                "detail": "No title deed, patta, encumbrance certificate, or survey record was supplied for this investigation.",
            },
            "encumbrance_indicators": risks or [{
                "risk_type": "No risk entry listed in demo dataset",
                "severity": "UNKNOWN",
                "description": "The absence of a listed risk is not evidence that no encumbrance exists.",
                "recommended_action": "Obtain and independently verify a current Encumbrance Certificate.",
            }],
            "survey_and_boundary": {
                "status": "NOT_VERIFIED",
                "detail": "The survey reference is synthetic; no official map, FMB, or physical demarcation was checked.",
            },
            "infrastructure": infrastructure,
            "potential_risks": risks,
            "missing_documents": [
                "Registered title deeds and complete chain of title",
                "Current Encumbrance Certificate from the Sub-Registrar",
                "Official revenue records and pattadar details",
                "FMB / village map and government boundary demarcation",
                "Court, acquisition, and prohibited-property searches",
            ],
            "recommended_next_steps": [
                "Have an independent property advocate review original documents and the title chain.",
                "Obtain current certified records directly from the relevant authorities.",
                "Commission an official survey and verify boundary stones on site.",
                "Do not pay an advance based only on this demonstration record or broker claims.",
            ],
            "evidence_classification": "SYNTHETIC_DEMONSTRATION_DATA",
            "confidence": "LOW",
            "disclaimer": "Preliminary legal awareness only. This synthetic demonstration is not official verification or legal advice.",
        }

    def _build_case_report(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]],
        land: Optional[LandListing],
        document_analyses: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        report = self._build_report(land)
        documents = document_analyses or []
        buyer = self._build_buyer_context(query, conversation_history, documents)
        user_statements = [
            item["content"]
            for item in (conversation_history or [])
            if item.get("role") == "user" and isinstance(item.get("content"), str)
        ]
        if query.strip() and (not user_statements or user_statements[-1] != query.strip()):
            user_statements.append(query.strip())

        report["buyer_requirements"] = {
            "buying_intent": buyer["buying_intent"],
            "preferred_location": buyer["preferred_location"],
            "land_type": buyer["land_type"],
            "acreage": buyer["acreage"],
            "budget": buyer["budget"],
            "intended_purpose": buyer["intended_purpose"],
            "broker_status": buyer["broker_status"],
            "asking_price_per_acre_as_stated": buyer["asking_price_per_acre"],
            "other_preferences": buyer["buyer_preferences"],
            "conversation_statements": user_statements,
            "evidence_status": "USER_PROVIDED_NOT_VERIFIED",
        }
        report["user_provided_property_details"] = {
            "location": buyer["preferred_location"],
            "survey_reference": buyer["survey_reference"],
            "area": buyer["acreage"],
            "land_type": buyer["land_type"],
            "asking_price_per_acre": buyer["asking_price_per_acre"],
            "source": "Buyer conversation; not independently verified",
        }
        report["broker_workflow"] = {
            "status": buyer["broker_status"],
            "description": {
                "YES": "Broker or seller claims were supplied; each remains unverified.",
                "NO": "The buyer reported no broker; this is an independent-search workflow.",
                "UNKNOWN": "The conversation did not establish whether a broker was approached.",
            }[buyer["broker_status"]],
        }
        incomplete_requirements = [
            label
            for label, key in (
                ("Preferred location", "preferred_location"),
                ("Land type", "land_type"),
                ("Required acreage", "acreage"),
                ("Budget", "budget"),
                ("Intended purpose", "intended_purpose"),
            )
            if not buyer[key]
        ]
        if buyer["broker_status"] == "UNKNOWN":
            incomplete_requirements.append("Broker status")
        if not land and not buyer["survey_reference"]:
            incomplete_requirements.append("Specific property or survey reference")
        if not documents:
            incomplete_requirements.append("Property document analysis")
        if buyer["next_missing_detail"]:
            incomplete_requirements.append(buyer["next_missing_detail"])
        report["report_completeness"] = {
            "status": "INCOMPLETE" if incomplete_requirements else "INPUTS_PRESENT_UNVERIFIED",
            "missing_information": list(dict.fromkeys(incomplete_requirements)),
            "note": "Input completeness does not mean that any property fact or document was independently verified.",
        }
        case_material = json.dumps({
            "query": query,
            "conversation_history": conversation_history or [],
            "selected_land_id": land.id if land else None,
            "documents": documents,
        }, ensure_ascii=False, sort_keys=True, default=str)
        report["case_id"] = f"BV-{hashlib.sha256(case_material.encode('utf-8')).hexdigest()[:10].upper()}"
        report["broker_claims"] = []
        for statement in buyer["broker_statements"]:
            has_identifying_evidence = bool(land) or any(
                document.get("survey_numbers_found") for document in documents
            )
            has_document_scan = bool(documents)
            findings = [
                f"{document.get('filename', 'Uploaded document')}: "
                f"{issue.get('issue_title', 'Text-pattern indicator')}"
                for document in documents
                for issue in document.get("detected_issues", [])
            ]
            report["broker_claims"].append({
                "claim": statement,
                "status": "UNVERIFIED" if has_document_scan and has_identifying_evidence else "MISSING_INFORMATION",
                "evidence": "; ".join(findings) if findings else (
                    "No parcel-specific official evidence was available. Uploaded documents, if any, "
                    "were scanned only for text patterns."
                ),
                "missing_information": (
                    []
                    if has_document_scan and has_identifying_evidence
                    else [
                        item for item, missing in (
                            ("Exact village and survey/subdivision reference", not has_identifying_evidence),
                            ("A relevant document or official record for this claim", not has_document_scan),
                        )
                        if missing
                    ]
                ),
                "required_checks": self._broker_claim_checks(statement),
            })

        report["document_analysis"] = {
            "status": "PATTERN_SCAN_ONLY" if documents else "NOT_PROVIDED",
            "detail": (
                "Uploaded text was scanned for patterns only. The scan does not verify authenticity, "
                "completeness, current status, ownership, or legal effect."
                if documents else
                "No document analysis was supplied in this conversation."
            ),
            "documents": [
                {
                    "filename": document.get("filename", "Uploaded document"),
                    "summary": document.get("summary", "No summary was provided."),
                    "survey_numbers_found": document.get("survey_numbers_found", []),
                    "detected_issues": document.get("detected_issues", []),
                    "disclaimer": document.get("disclaimer", ""),
                    "evidence_type": "USER_PROVIDED_DOCUMENT_TEXT",
                }
                for document in documents
            ],
        }
        report["claim_verification"] = {
            "status": "UNVERIFIED",
            "detail": (
                "No official revenue, registration, court, acquisition, or infrastructure records were queried."
            ),
        }
        report["property_comparison"] = {
            "status": "NO_VERIFIED_LISTING_FEED",
            "properties": [],
            "detail": (
                "No live or independently verified listing feed is configured. Synthetic demonstration "
                "records are not represented as available properties or recommendations."
            ),
        }
        report["potential_advantages"] = [
            "No independently verified property advantages, access, services, or nearby facilities were supplied."
        ]
        report["financial_breakdown"] = {
            "buyer_budget_as_stated": buyer["budget"],
            "broker_asking_price_per_acre_as_stated": buyer["asking_price_per_acre"],
            "property_area_acres": land.acres if land else None,
            "asking_price_per_acre_lakhs": land.price_per_acre_lakhs if land else None,
            "asking_price_total_lakhs": land.total_price_lakhs if land else None,
            "estimate_status": (
                "SYNTHETIC_DEMO_FIGURES" if land else "INSUFFICIENT_PROPERTY_PRICE_INFORMATION"
            ),
            "note": (
                "Figures are copied from a synthetic demonstration record and are not a market valuation."
                if land else
                "No parcel-specific price was supplied or verified; fees, taxes, and transaction costs are excluded."
            ),
        }
        if buyer["broker_status"] == "YES":
            report["recommended_next_steps"] = [
                "Ask the broker or seller for the original documents and exact survey/subdivision reference supporting each claim.",
                "Verify every supplied document and claim with the issuing authority and an independent property advocate.",
                "Do not pay an advance based only on broker statements or text-pattern document scans.",
            ]
        elif buyer["broker_status"] == "NO":
            report["recommended_next_steps"] = [
                "Continue the independent search using the buyer requirements captured in this report.",
                "For any candidate parcel, obtain its exact village and survey/subdivision reference before assessing it.",
                "Have an independent property advocate verify original records before paying an advance.",
            ]
        report["seller_questions"] = [
            "Can you provide the registered original sale deed and the complete chain of title?",
            "Can I obtain a current Encumbrance Certificate directly from the Sub-Registrar?",
            "Do the survey number, subdivision, area, and boundaries match official revenue records and a site survey?",
            "Are there any mortgages, court matters, acquisition notices, restrictions, or unpaid dues?",
            "What official records support the road, water, electricity, zoning, and nearby-project claims?",
        ]
        report["overall_assessment"] = {
            "status": "NOT_DETERMINED",
            "confidence": "LOW",
            "detail": (
                "This report is a preliminary awareness summary. It cannot determine that a property is safe "
                "to buy; independent checks of current original records are required."
            ),
        }
        report["confidence"] = "LOW"
        report["disclaimer"] = (
            "General awareness only. No parcel was identified. User statements, uploaded document text, "
            "and synthetic demo records are not independently verified. This is not a legal opinion, "
            "title certificate, or guarantee that a property is safe to buy."
            if land is None else
            "Preliminary AI awareness only. User statements, uploaded document text, and synthetic demo "
            "records are not independently verified. This is not a legal opinion, title certificate, "
            "or guarantee that a property is safe to buy."
        )
        return report

    @staticmethod
    def _broker_claim_checks(statement: str) -> List[str]:
        claim = statement.casefold()
        checks: List[str] = []
        if any(term in claim for term in ("owner", "ownership", "belongs", "title", "seller")):
            checks.extend([
                "Inspect the registered sale deed and complete chain of title, and confirm the seller's identity and authority to sell.",
                "Obtain a current Encumbrance Certificate directly from the Sub-Registrar and compare it with official revenue and mutation records.",
            ])
        if any(term in claim for term in ("dispute", "court", "case", "litigation", "clear", "legal problem")):
            checks.extend([
                "Search the exact parcel and parties in relevant civil and revenue court records, then review certified orders with an independent advocate.",
                "Check for acquisition, prohibited-property, land-use, and revenue restrictions with the relevant authorities.",
            ])
        if any(term in claim for term in ("highway", "road", "metro", "rail", "airport", "project", "development")):
            checks.extend([
                "Request the project's official government order, approval or tender record, and a published alignment or land-acquisition map from the responsible agency.",
                "Match the official alignment to the parcel's survey number; do not rely on distance or timing stated by a broker.",
            ])
        if any(term in claim for term in ("mortgage", "loan", "encumbrance", "lien", "debt")):
            checks.extend([
                "Obtain a current Encumbrance Certificate from the Sub-Registrar and verify any registered mortgage entry.",
                "For a claimed repayment, inspect the lender's closure confirmation and registered release or reconveyance deed.",
            ])
        if any(term in claim for term in ("water", "borewell", "electricity", "power", "access", "connectivity")):
            checks.extend([
                "Inspect the parcel and confirm all-season legal road access, boundaries, and existing utility connections with the relevant providers.",
                "Verify water source, yield, quality, and any required groundwater permissions independently.",
            ])
        if any(term in claim for term in ("price", " lakhs", "lakh", "crore", "per acre", "cost")):
            checks.append(
                "Compare the asking price with recent registered transactions and the applicable official guideline value; this report does not verify market value."
            )
        if not checks:
            checks.extend([
                "Obtain the exact document or official record supporting the statement.",
                "Verify it with the issuing authority and an independent property advocate.",
            ])
        return list(dict.fromkeys(checks))

    def build_case_report(
        self,
        conversation_history: List[Dict[str, str]],
        land: Optional[LandListing],
        document_analyses: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        user_messages = [
            item.get("content", "")
            for item in conversation_history
            if item.get("role") == "user" and isinstance(item.get("content"), str)
        ]
        latest_query = user_messages[-1] if user_messages else ""
        return self._build_case_report(
            latest_query,
            conversation_history[:-1] if user_messages else conversation_history,
            land,
            document_analyses,
        )

    @staticmethod
    def _build_buyer_context(
        query: str,
        conversation_history: Optional[List[Dict[str, str]]],
        document_analyses: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        user_messages = [
            item["content"]
            for item in (conversation_history or [])
            if item.get("role") == "user" and isinstance(item.get("content"), str)
        ]
        user_messages.append(query)

        def latest_match(pattern: str, group: int = 0) -> Optional[str]:
            for message in reversed(user_messages):
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    return match.group(group).strip(" \t\r\n.,;:") or None
            return None

        location = None
        for message in reversed(user_messages):
            match = re.search(
                r"\b(?:near|around|close to|in|at)\s+([^\W\d_][\w .'-]{0,48})",
                message,
                re.IGNORECASE,
            )
            if match:
                location = re.split(
                    r"\b(?:and|but|for|with|because|where|which)\b",
                    match.group(1),
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip(" \t\r\n.,;:")
                if location:
                    break

        land_type_pattern = (
            r"\b(?:agricultural|agriculture|residential|commercial|industrial|"
            r"farm(?:ing)?|open\s+plot|plots?)\b(?:\s+land)?"
        )
        land_type = latest_match(land_type_pattern)
        acreage = latest_match(
            r"\b\d+(?:\.\d+)?(?:\s*(?:to|-|–)\s*\d+(?:\.\d+)?)?\s*"
            r"(?:acres?|ac|ఎకరాలు|ఎకరం|ఎకరాల)\b"
        )
        amount_pattern = (
            r"(?:₹|INR\s*|Rs\.?\s*)\s*\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh(?:s)?|"
            r"lac(?:s)?|crore(?:s)?|cr|million|thousand))?"
            r"|\b\d[\d,]*(?:\.\d+)?\s*(?:lakh(?:s)?|lac(?:s)?|crore(?:s)?|"
            r"cr|million|thousand)\b"
        )
        budget = None
        for message in reversed(user_messages):
            if not re.search(r"\b(?:budget|afford|spend|maximum|limit)\b", message, re.IGNORECASE):
                continue
            match = re.search(amount_pattern, message, re.IGNORECASE)
            if match and not re.search(
                r"\bper\s+acre\b", message[match.end():match.end() + 24], re.IGNORECASE
            ):
                budget = match.group(0).strip()
                break
        if budget is None:
            for message in reversed(user_messages):
                for match in reversed(list(re.finditer(amount_pattern, message, re.IGNORECASE))):
                    context_start = max(0, match.start() - 24)
                    context_end = min(len(message), match.end() + 24)
                    if not re.search(r"\bper\s+acre\b", message[context_start:context_end], re.IGNORECASE):
                        budget = match.group(0).strip()
                        break
                if budget:
                    break

        asking_price_per_acre = latest_match(
            rf"({amount_pattern})\s*(?:per\s+acre|/\s*acre)", group=1
        )
        broker_mentions = [
            message for message in user_messages
            if re.search(r"\b(?:broker|agent|seller|owner)\b", message, re.IGNORECASE)
        ]
        broker_status = "UNKNOWN"
        for message in reversed(broker_mentions):
            if re.search(
                r"\b(?:no\s+broker|without\s+(?:a\s+)?broker|searching\s+independently|"
                r"(?:haven't|have\s+not|never|didn't|did\s+not)\s+(?:yet\s+)?"
                r"(?:approached|contacted|spoken|talked|met))\b",
                message,
                re.IGNORECASE,
            ):
                broker_status = "NO"
                break
            if re.search(
                r"\b(?:already|yes|have|met|spoke|spoken|contacted|approached)\b.{0,40}"
                r"\b(?:broker|agent)\b|\b(?:broker|agent)\b.{0,24}"
                r"\b(?:showed|told|said|offered|quoted|promised)\b",
                message,
                re.IGNORECASE,
            ):
                broker_status = "YES"
                break

        def direct_broker_answer(answer: str) -> Optional[str]:
            if re.match(
                r"^(?:no|nope|not\s+yet|i\s+haven't|i\s+have\s+not|i\s+didn't|i\s+did\s+not)\b",
                answer.strip(),
                re.IGNORECASE,
            ):
                return "NO"
            if re.match(
                r"^(?:yes|yeah|yep|correct|i\s+have|already)\b",
                answer.strip(),
                re.IGNORECASE,
            ):
                return "YES"
            return None

        history_items = conversation_history or []
        for index, item in enumerate(history_items):
            if item.get("role") != "assistant" or not re.search(
                r"\b(?:broker|agent)\b", item.get("content", ""), re.IGNORECASE
            ):
                continue
            answer = ""
            for candidate in history_items[index + 1:]:
                if candidate.get("role") == "assistant":
                    break
                if candidate.get("role") == "user" and isinstance(candidate.get("content"), str):
                    answer = candidate["content"]
                    break
            status = direct_broker_answer(answer)
            if status:
                broker_status = status

        previous_advisor_question = next(
            (
                item.get("content", "")
                for item in reversed(conversation_history or [])
                if item.get("role") == "assistant" and isinstance(item.get("content"), str)
            ),
            "",
        )
        current_answer = query.strip()
        if broker_status == "UNKNOWN" and re.search(
            r"\b(?:broker|agent)\b", previous_advisor_question, re.IGNORECASE
        ):
            broker_status = direct_broker_answer(current_answer) or broker_status
        def asks_for_broker_claim(text: str) -> bool:
            return bool(re.search(
                r"\b(?:what|which|tell|share|describe|explain)\b.{0,100}"
                r"\b(?:broker|agent|seller)\b"
                r"|\b(?:broker|agent|seller)\b.{0,80}\b(?:said|say|told|claim|offer|show)\b",
                text,
                re.IGNORECASE,
            ))

        broker_statements = [
            message for message in broker_mentions
            if re.search(
                r"\b(?:said|says|told|showed|claimed|claims|promised|offered|quoted|"
                r"price|cost|clear\s+title|no\s+legal\s+problem)\b",
                message,
                re.IGNORECASE,
            )
        ][-5:]
        for index, item in enumerate(history_items):
            if item.get("role") != "assistant" or not asks_for_broker_claim(item.get("content", "")):
                continue
            answer = ""
            for candidate in history_items[index + 1:]:
                if candidate.get("role") == "assistant":
                    break
                if candidate.get("role") == "user" and isinstance(candidate.get("content"), str):
                    answer = candidate["content"].strip()
                    break
            if answer and not re.match(r"^(?:yes|yeah|yep|no|nope|not yet)\b", answer, re.IGNORECASE):
                broker_statements.append(answer)
        if asks_for_broker_claim(previous_advisor_question) and current_answer and not re.match(
            r"^(?:yes|yeah|yep|no|nope|not yet)\b", current_answer, re.IGNORECASE
        ):
            broker_statements.append(current_answer)
        broker_statements = list(dict.fromkeys(broker_statements))[-5:]
        broker_land_type = next(
            (
                match.group(0).strip()
                for statement in reversed(broker_statements)
                if (match := re.search(land_type_pattern, statement, re.IGNORECASE))
            ),
            None,
        )
        documents = [
            message for message in user_messages
            if re.search(
                r"\b(?:documents?|deeds?|patta|papers?|encumbrance)\b|"
                r"\btitle\s+(?:deed|documents?|papers?|records?|chain)\b",
                message,
                re.IGNORECASE,
            )
        ][-3:]
        concerns = [
            message for message in user_messages
            if re.search(
                r"\b(?:concern|worried|worry|risk|dispute|mortgage|loan|fraud|issue)\b",
                message,
                re.IGNORECASE,
            )
        ][-3:]
        buyer_preferences = [
            message for message in user_messages
            if re.search(
                r"\b(?:road|access|water|irrigat|borewell|electricity|power|"
                r"distance|nearby|hospital|school|farming|investment|purpose)\b",
                message,
                re.IGNORECASE,
            )
        ][-5:]
        intended_purpose = latest_match(
            r"\b(?:for|purpose(?:\s+is)?)\s+(farming|agriculture|investment|"
            r"residence|residential|commercial|business|horticulture|a\s+farmhouse)\b"
        )
        buying_intent = any(
            re.search(r"\b(?:buy|buying|purchase|purchasing|acquire)\b", message, re.IGNORECASE)
            for message in user_messages
        )
        survey_reference = latest_match(
            r"\b(?:survey\s*(?:number|no\.?)|s\.?\s*no\.?|sy)\s*[-:#/ ]*"
            r"([A-Z]*\d[A-Z0-9/-]*)\b",
            group=1,
        )
        if survey_reference is None:
            survey_reference = next(
                (
                    reference
                    for document in document_analyses or []
                    for reference in document.get("survey_numbers_found", [])
                    if isinstance(reference, str) and reference.strip()
                ),
                None,
            )
        assistant_questions = [
            item.get("content", "")
            for item in history_items
            if item.get("role") == "assistant" and isinstance(item.get("content"), str)
        ]
        survey_question_asked = bool(assistant_questions and re.search(
            r"\b(?:survey|subdivision)\b", assistant_questions[-1], re.IGNORECASE
        ))
        survey_answered_without_number = survey_question_asked and bool(re.search(
            r"\b(?:don't know|do not know|not sure|no survey|don't have|do not have)\b",
            current_answer,
            re.IGNORECASE,
        ))
        document_question_asked = bool(assistant_questions and re.search(
            r"\b(?:document|deed|patta|paper)\b", assistant_questions[-1], re.IGNORECASE
        ))
        document_answered_without_upload = document_question_asked and bool(re.match(
            r"^(?:yes|yeah|yep|no|nope|not yet|i have|i don't|i do not)\b",
            current_answer,
            re.IGNORECASE,
        ))
        buyer_context_complete = bool(
            budget and documents and concerns and land_type and acreage
        )
        survey_missing = not survey_reference and not survey_answered_without_number
        broker_claims_clear_title = any(
            re.search(r"\b(?:clear\s+title|title\s+is\s+clear)\b", statement, re.IGNORECASE)
            for statement in broker_statements
        )

        if not buying_intent:
            next_missing_detail = None
        elif not location:
            next_missing_detail = "preferred location"
        elif broker_status == "UNKNOWN":
            next_missing_detail = "whether the buyer has already approached a broker"
        elif broker_status == "YES" and not broker_statements:
            next_missing_detail = "what the broker said about the parcel"
        elif broker_status == "YES" and buyer_context_complete:
            next_missing_detail = None
        elif broker_status == "YES" and survey_missing:
            next_missing_detail = (
                "whether the broker supplied documents or a survey number"
                if broker_claims_clear_title and not documents
                else "the village and survey/subdivision number, if known"
            )
        elif broker_status == "YES" and not acreage:
            next_missing_detail = "the parcel area"
        elif broker_status == "YES" and not asking_price_per_acre and not budget:
            next_missing_detail = "the broker's quoted total or per-acre price"
        elif broker_status == "YES" and not broker_land_type:
            next_missing_detail = "land type"
        elif broker_status == "YES" and not document_analyses and not documents and not document_answered_without_upload:
            next_missing_detail = "the documents the broker supplied, if any"
        elif broker_status == "NO" and not land_type:
            next_missing_detail = "land type"
        elif broker_status == "NO" and not acreage:
            next_missing_detail = "required acreage"
        elif broker_status == "NO" and not budget:
            next_missing_detail = "approximate budget"
        elif broker_status == "NO" and not buyer_preferences:
            next_missing_detail = "road, water, electricity, and nearby-facility preferences"
        else:
            next_missing_detail = None

        return {
            "buying_intent": buying_intent,
            "preferred_location": location,
            "land_type": land_type,
            "broker_land_type": broker_land_type,
            "acreage": acreage,
            "budget": budget,
            "asking_price_per_acre": asking_price_per_acre,
            "broker_status": broker_status,
            "broker_statements": broker_statements,
            "documents_discussed": documents,
            "documents_uploaded": bool(document_analyses),
            "survey_reference": survey_reference,
            "concerns": concerns,
            "buyer_preferences": buyer_preferences,
            "intended_purpose": intended_purpose,
            "next_missing_detail": next_missing_detail,
        }

    async def reason(
        self, query: str, language: str = "te", conversation_history=None,
        available_lands=None, selected_land_id=None
    ) -> Dict[str, Any]:
        investigation = await self.investigate_collaborative(
            query, language, available_lands, selected_land_id, conversation_history
        )
        dialogue = investigation["dialogue_sequence"]
        return {
            "transcript": query,
            "response": "\n\n".join(f"**{item['character_name']}**: {item['text']}" for item in dialogue),
            "language": language,
            "matched_land_ids": investigation["matched_land_ids"],
            "legal_warnings": [item["text"] for item in dialogue if item["character"] == "nyaya"],
            "infrastructure_findings": [item["text"] for item in dialogue if item["character"] == "infra"],
            "growth_insights": [item["text"] for item in dialogue if item["character"] == "bhoomi"],
            "ai_mode": f"{investigation['provider']} ({investigation['model_used']})",
        }


reasoning_service = ReasoningService()
