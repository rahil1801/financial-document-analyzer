import re
from pathlib import Path
from typing import Any, Dict, Optional

import fitz


def read_pdf_text(path: str) -> str:
    """Read all text from a PDF file."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    pages: list[str] = []
    with fitz.open(str(pdf_path)) as doc:
        for page in doc:
            pages.append((page.get_text() or "").strip())

    full_text = "\n".join(pages).strip()

    if not full_text:
        raise ValueError("No extractable text found in the provided PDF")

    return full_text


def _extract_money_metric(text: str, label: str) -> Optional[float]:
    """Extract monetary value based on label."""
    pattern = rf"{label}[^\d]{{0,25}}([\$€£]?\s?[\d,]+(?:\.\d+)?)"
    match = re.search(pattern, text, flags=re.IGNORECASE)

    if not match:
        return None

    cleaned = re.sub(r"[^\d.]", "", match.group(1))

    try:
        return float(cleaned)
    except ValueError:
        return None


class FinancialDocumentTool:
    """
    Responsible ONLY for reading financial document content.
    """

    @staticmethod
    def read_data_tool(path: str = "data/sample.pdf") -> str:
        """Reads and returns raw text from PDF."""
        return read_pdf_text(path)

class InvestmentTool:
    """
    Responsible for investment decision logic.
    Extracts financial metrics and produces recommendation.
    """

    @staticmethod
    def analyze_investment_tool(text: str, query: str) -> Dict[str, Any]:
        """
        Deterministic investment analysis.
        """

        if not text:
            raise ValueError("Document text is required for investment analysis.")

        normalized_text = re.sub(r"\s+", " ", text)

        revenue = _extract_money_metric(normalized_text, "revenue")
        net_income = _extract_money_metric(normalized_text, "net income")
        cash = _extract_money_metric(normalized_text, "cash")
        debt = _extract_money_metric(normalized_text, "debt")

        recommendation = "HOLD"
        rationale = "Insufficient financial metrics for strong conviction."

        if revenue is not None and net_income is not None:

            if net_income > 0:
                if debt is None:
                    recommendation = "BUY"
                    rationale = "Company is profitable with no detected debt."
                elif net_income > (debt * 0.05):
                    recommendation = "BUY"
                    rationale = "Positive profitability and manageable leverage."
                else:
                    recommendation = "HOLD"
                    rationale = "Profitable but debt level requires monitoring."

            elif net_income < 0:
                recommendation = "CAUTIOUS"
                rationale = "Negative net income increases downside risk."

        return {
            "query": query,
            "metrics": {
                "revenue": revenue,
                "net_income": net_income,
                "cash": cash,
                "debt": debt,
            },
            "recommendation": recommendation,
            "recommendation_rationale": rationale,
        }


class RiskTool:
    """
    Responsible for risk assessment logic.
    """

    @staticmethod
    def create_risk_assessment_tool(text: str) -> Dict[str, Any]:
        """
        Performs deterministic keyword-based risk detection.
        """

        if not text:
            raise ValueError("Document text is required for risk assessment.")

        lowered = text.lower()

        risk_keywords = {
            "supply chain": "Supply-chain exposure mentioned.",
            "regulatory": "Regulatory risk discussed.",
            "litigation": "Legal/litigation risk detected.",
            "volatility": "Market volatility highlighted.",
            "inflation": "Inflationary pressure referenced.",
            "recession": "Recession-related concern detected.",
        }

        detected_risks = []

        for keyword, message in risk_keywords.items():
            if keyword in lowered:
                detected_risks.append(message)

        risk_level = "LOW"

        if len(detected_risks) >= 4:
            risk_level = "HIGH"
        elif len(detected_risks) >= 2:
            risk_level = "MEDIUM"

        return {
            "detected_risks": detected_risks,
            "risk_count": len(detected_risks),
            "overall_risk_level": risk_level,
        }