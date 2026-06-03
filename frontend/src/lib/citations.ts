import type { Citation } from "@/types"

export function sourceLabel(index: number) {
  return `Source ${index + 1}`
}

export function sourceShortLabel(index: number) {
  return `S${String(index + 1).padStart(2, "0")}`
}

export function formatPolicyArea(category: string) {
  return category
    .split("-")
    .filter(Boolean)
    .map((part) => `${part[0]?.toUpperCase() || ""}${part.slice(1)}`)
    .join(" ")
}

export function hasCompleteProvenance(citation: Citation) {
  return Boolean(citation.owner && citation.source_date && citation.document_version)
}

export function missingProvenanceFields(citation: Citation) {
  return [
    citation.owner ? null : "owner",
    citation.source_date ? null : "date",
    citation.document_version ? null : "version",
  ].filter((field): field is string => Boolean(field))
}

export function provenanceStatus(citation: Citation) {
  const missingFields = missingProvenanceFields(citation)

  if (missingFields.length === 0) {
    return "Metadata complete"
  }

  return `Missing ${missingFields.join(", ")}`
}
