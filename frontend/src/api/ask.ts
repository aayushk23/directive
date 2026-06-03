import type { AskResponse } from "@/types"

export const DEFAULT_API_BASE_URL = ""

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL

export class AskHttpError extends Error {
  status: number

  constructor(status: number) {
    super(`Request failed with status ${status}`)
    this.name = "AskHttpError"
    this.status = status
  }
}

export class AskNetworkError extends Error {
  constructor() {
    super("Network request failed")
    this.name = "AskNetworkError"
  }
}

export class AskMalformedResponseError extends Error {
  constructor() {
    super("Malformed ask response")
    this.name = "AskMalformedResponseError"
  }
}

function apiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`

  if (API_BASE_URL.startsWith("/")) {
    return `${API_BASE_URL.replace(/\/$/, "")}${normalizedPath}`
  }

  if (!API_BASE_URL) {
    return normalizedPath
  }

  return new URL(normalizedPath, API_BASE_URL).toString()
}

function isStringOrNull(value: unknown): value is string | null {
  return typeof value === "string" || value === null
}

function isCitation(value: unknown) {
  if (!value || typeof value !== "object") {
    return false
  }

  const citation = value as Record<string, unknown>

  return (
    typeof citation.document_id === "string" &&
    typeof citation.chunk_id === "string" &&
    typeof citation.title === "string" &&
    typeof citation.category === "string" &&
    isStringOrNull(citation.owner) &&
    isStringOrNull(citation.source_date) &&
    isStringOrNull(citation.document_version) &&
    typeof citation.snippet === "string"
  )
}

function isAskResponse(value: unknown): value is AskResponse {
  if (!value || typeof value !== "object") {
    return false
  }

  const response = value as Record<string, unknown>

  return (
    typeof response.answer === "string" &&
    typeof response.supported === "boolean" &&
    Array.isArray(response.citations) &&
    response.citations.every(isCitation) &&
    isStringOrNull(response.refusal_reason)
  )
}

export async function askQuestion(question: string): Promise<AskResponse> {
  let response: Response

  try {
    response = await fetch(apiUrl("/ask"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    })
  } catch {
    throw new AskNetworkError()
  }

  if (!response.ok) {
    throw new AskHttpError(response.status)
  }

  let payload: unknown

  try {
    payload = await response.json()
  } catch {
    throw new AskMalformedResponseError()
  }

  if (!isAskResponse(payload)) {
    throw new AskMalformedResponseError()
  }

  return payload
}
