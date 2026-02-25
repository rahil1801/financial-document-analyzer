import os
from dotenv import load_dotenv
from crewai.agents import Agent
from crewai import LLM

from tools import (
    FinancialDocumentTool,
    InvestmentTool,
    RiskTool,
)

load_dotenv()


def _build_llm() -> LLM:
    model = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required")

    return LLM(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Finance Document Analyzer"
        },
        temperature=0.1
    )


llm = _build_llm()


financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal=(
        "Provide accurate, evidence-based analysis of uploaded financial documents. "
        "You must use tools to extract document data before answering the query: {query}."
    ),
    verbose=True,
    memory=False,
    backstory=(
        "You are a disciplined financial analyst focused strictly on factual interpretation "
        "of documented numbers, trends, and risks. "
        "You never fabricate financial data. "
        "You always use available tools before drawing conclusions."
    ),

    tools=[
        FinancialDocumentTool.read_data_tool,
        InvestmentTool.analyze_investment_tool,
        RiskTool.create_risk_assessment_tool,
    ],

    llm=llm,
    max_iter=5,        # Allow multiple tool calls
    max_rpm=20,
    allow_delegation=False,
)

verifier = Agent(
    role="Financial Document Verifier",
    goal=(
        "Use the document reading tool to verify whether the uploaded file "
        "contains structured financial data such as revenue, income, balance sheet terms, "
        "or financial reporting language."
    ),
    backstory=(
        "You are a financial compliance auditor. "
        "You validate documents strictly based on financial terminology and structure."
    ),
    tools=[FinancialDocumentTool.read_data_tool],
    llm=llm,
    verbose=True,
    memory=False,
    max_iter=2,
    allow_delegation=False
)

risk_assessor = Agent(
    role="Financial Risk Assessment Specialist",
    goal=(
        "Use the risk assessment tool to evaluate financial risk factors "
        "and provide structured LOW, MEDIUM, or HIGH risk classification."
    ),
    backstory=(
        "You are a professional financial risk analyst. "
        "You rely on detected risk indicators and never exaggerate."
    ),
    tools=[RiskTool.create_risk_assessment_tool],
    llm=llm,
    verbose=True,
    memory=False,
    max_iter=2,
    allow_delegation=False
)

investment_advisor = Agent(
    role="Professional Investment Advisor",
    goal=(
        "Use the investment analysis tool to generate evidence-based "
        "investment insights strictly from financial metrics."
    ),
    backstory=(
        "You are a certified investment advisor focused on data-driven decisions. "
        "You never fabricate financial recommendations."
    ),
    tools=[InvestmentTool.analyze_investment_tool],
    llm=llm,
    verbose=True,
    memory=False,
    max_iter=2,
    allow_delegation=False
)