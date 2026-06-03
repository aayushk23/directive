import { ListChecks, Search } from "lucide-react"

export function EmptyAnswer() {
  return (
    <div className="rounded-md border border-dashed bg-background/30 px-5 py-6 sm:px-6 sm:py-7">
      <div className="flex max-w-2xl items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md border bg-muted/30">
          <Search aria-hidden="true" className="h-4 w-4 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-semibold">Ready for a policy question</p>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Results appear here with a support decision, answer text, and source
            snippets in the same workspace.
          </p>
          <div className="mt-4 grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
            {["Ask", "Check support", "Review snippets"].map((item) => (
              <div
                className="flex items-center gap-2 rounded-md border bg-muted/15 px-3 py-2"
                key={item}
              >
                <ListChecks aria-hidden="true" className="h-3.5 w-3.5" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
