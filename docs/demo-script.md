# Demo Script

Use this short flow to show the local MVP.

## Setup

Start the backend and database:

```bash
docker compose up --build
```

In a second terminal, index the sample documents:

```bash
docker compose run --rm api_service policy-copilot-index-documents --documents-path documents
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Walkthrough

1. Ask: `When do passwords need to be rotated?`
   - Expected: supported answer with an IT Password Policy citation.

2. Ask: `Can I work remotely from another state?`
   - Expected: supported answer with a Remote Work Policy citation.

3. Ask: `What expenses require approval before reimbursement?`
   - Expected: supported answer with an Expense Reimbursement Policy citation.

4. Ask: `What is the cafeteria menu today?`
   - Expected: unsupported response with no citations.

## Points To Show

- Answers come from indexed local documents.
- Supported answers include source snippets and document metadata.
- Unsupported questions are refused instead of answered.
- The browser UI handles loading, empty, unsupported, and API-unavailable states.
