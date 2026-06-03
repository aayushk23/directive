import { AlertCircle, CheckCircle2 } from "lucide-react"

import type { AskResponse } from "@/types"
import { Badge } from "@/components/ui/badge"

export function ResultBadge({ result }: { result: AskResponse }) {
  return (
    <Badge
      className="w-fit gap-1.5"
      variant={result.supported ? "success" : "warning"}
    >
      {result.supported ? (
        <CheckCircle2 aria-hidden="true" className="h-3.5 w-3.5" />
      ) : (
        <AlertCircle aria-hidden="true" className="h-3.5 w-3.5" />
      )}
      {result.supported ? "Supported" : "Unsupported"}
    </Badge>
  )
}
