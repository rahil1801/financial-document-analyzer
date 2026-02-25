from crewai import Task

from agents import (
    financial_analyst,
    verifier,
    investment_advisor,
    risk_assessor,
)

from tools import (
    FinancialDocumentTool,
    InvestmentTool,
    RiskTool,
)


verification = Task(
    description=(
        "Use the document reading tool to extract the uploaded file text. "
        "Determine whether it contains legitimate financial content such as "
        "revenue, income, balance sheet terminology, or structured financial reporting. "
        "Base your conclusion strictly on extracted evidence."
    ),

    expected_output=(
        "Provide:\n"
        "- Whether the document appears to be financial (Yes/No)\n"
        "- Evidence found (financial keywords or monetary figures)\n"
        "- A brief justification based only on document content\n"
        "Do not fabricate financial terminology."
    ),

    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)


analyze_financial_document = Task(
    description=(
        "First call the document reading tool to extract the PDF text. "
        "Then use the investment analysis tool to evaluate the financial metrics. "
        "Answer the user query: {query}. "
        "Use only data extracted from the document."
    ),

    expected_output=(
        "Provide a structured response including:\n"
        "- Extracted key financial metrics (revenue, net income, cash, debt)\n"
        "- Investment recommendation (BUY / HOLD / CAUTIOUS)\n"
        "- Clear rationale based strictly on metrics\n"
        "Do not assume or fabricate any financial values."
    ),

    agent=financial_analyst,
    tools=[
        FinancialDocumentTool.read_data_tool,
        InvestmentTool.analyze_investment_tool,
    ],
    async_execution=False,
)

investment_analysis = Task(
    description=(
        "Use the investment analysis tool to generate a professional investment opinion "
        "based on the extracted financial metrics. "
        "Address the user query: {query}. "
        "Do not recommend speculative assets unless supported by document data."
    ),

    expected_output=(
        "Provide:\n"
        "- Summary of financial strength\n"
        "- Risk-adjusted investment view\n"
        "- Clear investment stance\n"
        "- Any limitations due to missing data\n"
        "Avoid exaggerated claims or unrelated assets."
    ),

    agent=investment_advisor,
    tools=[InvestmentTool.analyze_investment_tool],
    async_execution=False,
)

risk_assessment = Task(
    description=(
        "Use the risk assessment tool to analyze risk indicators present in the document. "
        "Classify overall risk as LOW, MEDIUM, or HIGH based strictly on detected signals. "
        "Answer in context of user query: {query}."
    ),

    expected_output=(
        "Provide:\n"
        "- List of detected risk factors\n"
        "- Total number of risks identified\n"
        "- Overall risk classification (LOW / MEDIUM / HIGH)\n"
        "- Brief explanation based only on document content\n"
        "Do not exaggerate or minimize risk without evidence."
    ),

    agent=risk_assessor,
    tools=[RiskTool.create_risk_assessment_tool],
    async_execution=False,
)