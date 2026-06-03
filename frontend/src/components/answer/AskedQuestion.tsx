export function AskedQuestion({ question }: { question: string }) {
  return (
    <div className="rounded-md border bg-background/45 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        Asked
      </p>
      <p className="mt-2 max-w-[72ch] whitespace-pre-wrap text-sm leading-6 text-foreground">
        {question}
      </p>
    </div>
  )
}
