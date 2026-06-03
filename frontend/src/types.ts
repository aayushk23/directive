export type Citation = {
  document_id: string
  chunk_id: string
  title: string
  category: string
  owner: string | null
  source_date: string | null
  document_version: string | null
  snippet: string
}

export type AskResponse = {
  answer: string
  supported: boolean
  citations: Citation[]
  refusal_reason: string | null
}
