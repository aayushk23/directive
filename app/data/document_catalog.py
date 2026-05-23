from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    category: str
    answer: str
    citation_snippet: str
    keywords: tuple[str, ...]


DOCUMENT_CATALOG: tuple[Document, ...] = (
    Document(
        document_id="it-password-policy",
        title="IT Password Policy",
        category="information-security",
        answer=(
            "Employees must rotate passwords every 90 days and immediately report "
            "suspected account compromise to IT Security."
        ),
        citation_snippet=(
            "Employees must rotate passwords every 90 days. Employees who suspect "
            "account compromise must immediately contact IT Security."
        ),
        keywords=(
            "password",
            "passwords",
            "rotation",
            "rotate",
            "90 days",
            "credentials",
            "account compromise",
            "suspected account compromise",
            "suspect account compromise",
            "compromise",
            "compromised",
            "it security",
        ),
    ),
    Document(
        document_id="remote-work-policy",
        title="Remote Work Policy",
        category="workplace",
        answer="Recurring remote work requires manager approval before the arrangement begins.",
        citation_snippet=(
            "Recurring remote work arrangements require manager approval before the arrangement begins."
        ),
        keywords=(
            "remote",
            "work from home",
            "manager approval",
            "hybrid",
            "recurring",
        ),
    ),
    Document(
        document_id="expense-reimbursement-policy",
        title="Expense Reimbursement Policy",
        category="finance",
        answer="Employees must provide receipts for reimbursable expenses over $25.",
        citation_snippet="Receipts are required for reimbursable expenses over $25.",
        keywords=(
            "expense",
            "expenses",
            "reimbursement",
            "receipt",
            "receipts",
            "$25",
            "25",
        ),
    ),
)
