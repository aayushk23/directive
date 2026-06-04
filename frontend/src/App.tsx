import { FormEvent, useRef, useState } from "react"
import {
  AlertCircle,
  FileText,
  Loader2,
  Search,
  Send,
  X,
} from "lucide-react"

import {
  AskHttpError,
  AskMalformedResponseError,
  AskNetworkError,
  askQuestion,
} from "@/api/ask"
import { AskedQuestion } from "@/components/answer/AskedQuestion"
import { EmptyAnswer } from "@/components/answer/EmptyAnswer"
import { ResultBadge } from "@/components/answer/ResultBadge"
import type { AskResponse, Citation } from "@/types"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import {
  formatPolicyArea,
  hasCompleteProvenance,
  missingProvenanceFields,
  provenanceStatus,
  sourceLabel,
  sourceShortLabel,
} from "@/lib/citations"
import { EXAMPLE_QUESTIONS, MAX_QUESTION_LENGTH } from "@/constants"

type RequestState = "idle" | "loading" | "success" | "error"
type CitationItem = {
  citation: Citation
  index: number
}

function supportDecisionText(result: AskResponse, sourceCount: number) {
  if (result.supported && sourceCount > 0) {
    return `This answer is supported by ${sourceCount} cited source${
      sourceCount === 1 ? "" : "s"
    }. Review the source snippets before acting on it.`
  }

  if (result.supported) {
    return "This answer was marked supported, but no citation was returned. Review the indexed documents before acting on it."
  }

  return "Do not use this as an answer. The indexed sources did not meet the support threshold."
}

function citationItems(citations: Citation[]): CitationItem[] {
  return citations.map((citation, index) => ({ citation, index }))
}

function requestErrorMessage(error: unknown) {
  if (error instanceof AskNetworkError) {
    return "The policy API is unavailable. Start the FastAPI backend, then retry."
  }

  if (error instanceof AskMalformedResponseError) {
    return "The policy API returned a response this page could not read."
  }

  if (error instanceof AskHttpError) {
    if (error.status === 400 || error.status === 422) {
      return "The question could not be checked. Edit it and try again."
    }

    if (error.status === 401 || error.status === 403) {
      return "The policy API returned an access error."
    }

    if (error.status === 429) {
      return "The policy API returned a rate limit error. Wait a moment, then try again."
    }

    if (error.status >= 500) {
      return `The policy API returned an error (${error.status}).`
    }

    return `The policy API returned an error (${error.status}).`
  }

  return "The question could not be checked."
}

function CitationList({
  items,
  emptyMessage = "No reviewed source snippets returned.",
}: {
  items: CitationItem[]
  emptyMessage?: string
}) {
  if (items.length === 0) {
    return (
      <div className="rounded-md border border-dashed bg-background/55 px-4 py-5 text-sm leading-6 text-muted-foreground">
        {emptyMessage}
      </div>
    )
  }

  return (
    <ol className="space-y-3">
      {items.map(({ citation, index }) => {
        const missingFields = missingProvenanceFields(citation)

        return (
          <li
            className="rounded-md border bg-background/55 p-4 shadow-[0_10px_34px_hsl(220_18%_3%_/_0.18)]"
            key={`${citation.document_id}:${citation.chunk_id}`}
          >
            <div className="flex items-start gap-3 sm:gap-4">
              <span className="flex h-8 w-10 shrink-0 items-center justify-center rounded-md border bg-muted/45 font-mono text-[11px] font-semibold text-muted-foreground tabular-nums">
                {sourceShortLabel(index)}
              </span>
              <div className="min-w-0 flex-1">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      {sourceLabel(index)}
                    </p>
                    <span className="rounded-sm border bg-muted/20 px-1.5 py-0.5 text-[11px] leading-4 text-muted-foreground">
                      {provenanceStatus(citation)}
                    </span>
                  </div>
                  <span className="mt-2 block break-words text-sm font-semibold leading-5 text-foreground">
                    {citation.title}
                  </span>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs leading-5 text-muted-foreground">
                    <span>{formatPolicyArea(citation.category)}</span>
                  </div>
                </div>
                <dl className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2 xl:grid-cols-4">
                  <div>
                    <dt className="font-semibold uppercase tracking-[0.16em]">
                      Policy owner
                    </dt>
                    <dd className="mt-1 break-words text-foreground">
                      {citation.owner || "Not provided"}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold uppercase tracking-[0.16em]">
                      Source date
                    </dt>
                    <dd className="mt-1 text-foreground">
                      {citation.source_date || "Not provided"}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold uppercase tracking-[0.16em]">
                      Version
                    </dt>
                    <dd className="mt-1 text-foreground">
                      {citation.document_version || "Not provided"}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold uppercase tracking-[0.16em]">
                      Reference ID
                    </dt>
                    <dd className="mt-1 break-all font-mono text-[11px] leading-5 text-foreground">
                      {citation.chunk_id}
                    </dd>
                  </div>
                </dl>
                {missingFields.length > 0 ? (
                  <p className="mt-3 rounded-md border bg-muted/20 px-3 py-2 text-xs leading-5 text-muted-foreground">
                    Metadata incomplete: missing {missingFields.join(", ")}.
                  </p>
                ) : null}
                <div className="mt-3 rounded-md border bg-card/45 p-3">
                  <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    <FileText aria-hidden="true" className="h-3.5 w-3.5" />
                    Source snippet
                  </p>
                  <p className="text-sm leading-6 text-muted-foreground">
                    {citation.snippet}
                  </p>
                </div>
              </div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function VerificationSummary({
  result,
}: {
  result: AskResponse
}) {
  const sourceCount = result.citations.length
  const sourceAreas = Array.from(
    new Set(result.citations.map((citation) => formatPolicyArea(citation.category))),
  )
  const incompleteProvenanceCount = result.citations.filter(
    (citation) => !hasCompleteProvenance(citation),
  ).length

  return (
    <div className="rounded-md border bg-background/45 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Support decision
          </p>
          <p className="mt-2 max-w-[72ch] text-sm leading-6 text-foreground">
            {supportDecisionText(result, sourceCount)}
          </p>
          {incompleteProvenanceCount > 0 ? (
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Check metadata before relying on this result: {incompleteProvenanceCount} source
              {incompleteProvenanceCount === 1 ? "" : "s"} lack owner, date, or
              version details.
            </p>
          ) : null}
        </div>
        <ResultBadge result={result} />
      </div>
      <p className="mt-4 text-sm leading-6 text-muted-foreground">
        Policy area:{" "}
        <span className="text-foreground">
          {sourceAreas.length ? sourceAreas.join(", ") : "None cited"}
        </span>
        {sourceCount > 0 ? (
          <>
            {" "}
            Metadata:{" "}
            <span className="text-foreground">
              {incompleteProvenanceCount === 0
                ? "complete"
                : "needs review"}
            </span>
            .
          </>
        ) : (
          "."
        )}
      </p>
    </div>
  )
}

function UnsupportedRecovery({
  onClear,
  onRevise,
}: {
  onClear: () => void
  onRevise: () => void
}) {
  return (
    <div className="rounded-md border bg-background/45 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        Next steps
      </p>
      <p className="mt-2 max-w-[72ch] text-sm leading-6 text-muted-foreground">
        Revise the question or check whether the indexed documents include this policy.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button className="min-h-9 px-3 text-xs" onClick={onRevise} type="button">
          <Search aria-hidden="true" className="h-3.5 w-3.5" />
          Revise question
        </Button>
        <Button
          className="min-h-9 px-3 text-xs"
          onClick={onClear}
          type="button"
          variant="ghost"
        >
          <X aria-hidden="true" className="h-3.5 w-3.5" />
          Clear and ask new
        </Button>
      </div>
    </div>
  )
}

export default function App() {
  const [question, setQuestion] = useState("")
  const [submittedQuestion, setSubmittedQuestion] = useState("")
  const [result, setResult] = useState<AskResponse | null>(null)
  const [requestState, setRequestState] = useState<RequestState>("idle")
  const [errorMessage, setErrorMessage] = useState("")
  const [validationMessage, setValidationMessage] = useState("")
  const questionFieldRef = useRef<HTMLTextAreaElement | null>(null)

  const isLoading = requestState === "loading"
  const trimmedQuestion = question.trim()
  const hasDraftQuestion = trimmedQuestion.length > 0
  const isOverLimit = trimmedQuestion.length > MAX_QUESTION_LENGTH
  const questionCharactersRemaining = Math.max(
    0,
    MAX_QUESTION_LENGTH - trimmedQuestion.length,
  )
  const isFollowUpDraft = Boolean(
    result && submittedQuestion && trimmedQuestion !== submittedQuestion,
  )
  const allCitationItems = citationItems(result?.citations || [])

  async function askCurrentQuestion(questionText: string) {
    const nextSubmittedQuestion = questionText.trim()

    if (!nextSubmittedQuestion) {
      setValidationMessage("Enter a question before submitting.")
      return
    }

    if (nextSubmittedQuestion.length > MAX_QUESTION_LENGTH) {
      setValidationMessage(
        `Keep the question under ${MAX_QUESTION_LENGTH} characters.`,
      )
      return
    }

    setValidationMessage("")
    setErrorMessage("")
    setSubmittedQuestion(nextSubmittedQuestion)
    setResult(null)
    setRequestState("loading")

    try {
      const response = await askQuestion(nextSubmittedQuestion)
      setResult(response)
      setRequestState("success")
    } catch (error) {
      setErrorMessage(requestErrorMessage(error))
      setRequestState("error")
    }
  }

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await askCurrentQuestion(question)
  }

  function clearWorkspace() {
    setQuestion("")
    setSubmittedQuestion("")
    setResult(null)
    setRequestState("idle")
    setErrorMessage("")
    setValidationMessage("")
  }

  function reviseQuestion() {
    questionFieldRef.current?.focus()
    questionFieldRef.current?.select()
  }

  return (
    <main className="min-h-screen px-4 py-4 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto grid w-full max-w-7xl gap-4">
        <header className="border-b border-border/80 pb-4 pt-1">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="max-w-3xl text-2xl font-semibold leading-tight tracking-normal text-foreground sm:text-3xl">
                Enterprise Policy Copilot
              </h1>
            </div>
          </div>
        </header>

        <div className="grid gap-5 lg:grid-cols-[minmax(320px,390px)_minmax(0,1fr)] lg:items-start">
          <Card className="overflow-hidden border-border/90 bg-card/86 lg:sticky lg:top-5">
            <CardHeader className="border-b bg-muted/20 pb-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <CardTitle className="text-xl">Question</CardTitle>
                  <CardDescription className="mt-2">
                    Ask about the indexed policy documents.
                  </CardDescription>
                </div>
                {isLoading ? (
                  <Loader2
                    aria-hidden="true"
                    className="mt-1 h-4 w-4 animate-spin text-muted-foreground"
                  />
                ) : null}
                {isLoading ? (
                  <span className="sr-only" role="status">
                    Checking sources for an answer.
                  </span>
                ) : null}
              </div>
            </CardHeader>
            <CardContent className="p-5 sm:p-6">
              <form className="grid gap-4" onSubmit={submitQuestion}>
                <div className="grid gap-2">
                  <div className="flex items-center justify-between gap-3">
                    <label className="text-sm font-medium" htmlFor="question">
                      Ask policy question
                    </label>
                    {hasDraftQuestion ? (
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {trimmedQuestion.length} chars
                      </span>
                    ) : null}
                  </div>
                  <Textarea
                    aria-describedby="question-help"
                    aria-invalid={Boolean(validationMessage) || isOverLimit}
                    disabled={isLoading}
                    id="question"
                    maxLength={MAX_QUESTION_LENGTH + 1}
                    minLength={1}
                    name="question"
                    onKeyDown={(event) => {
                      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                        event.currentTarget.form?.requestSubmit()
                      }
                    }}
                    onChange={(event) => {
                      setQuestion(event.target.value)
                      if (validationMessage) {
                        setValidationMessage("")
                      }
                    }}
                    placeholder="What is the password rotation policy?"
                    ref={questionFieldRef}
                    required
                    rows={5}
                    value={question}
                  />
                  <div
                    className="flex flex-col gap-1 text-xs leading-5 text-muted-foreground sm:flex-row sm:items-center sm:justify-between"
                    id="question-help"
                  >
                    <span>Use Cmd/Ctrl+Enter to ask.</span>
                    <span
                      className={
                        isOverLimit ? "font-semibold text-destructive" : undefined
                      }
                    >
                      {questionCharactersRemaining} characters remaining
                    </span>
                  </div>
                </div>

                {validationMessage ? (
                  <p className="text-sm text-destructive" role="alert">
                    {validationMessage}
                  </p>
                ) : null}
                {isOverLimit && !validationMessage ? (
                  <p className="text-sm text-destructive" role="alert">
                    Shorten the question before submitting.
                  </p>
                ) : null}

                <Button
                  className="min-h-11 w-full px-5"
                  disabled={isLoading || isOverLimit}
                  type="submit"
                >
                  {isLoading ? (
                    <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send aria-hidden="true" className="h-4 w-4" />
                  )}
                  {isLoading
                    ? "Checking sources"
                    : isFollowUpDraft
                      ? "Ask follow-up"
                      : result
                        ? "Ask again"
                        : "Ask"}
                </Button>
                {!hasDraftQuestion ? (
                  <div className="grid gap-2">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      Examples
                    </p>
                    {EXAMPLE_QUESTIONS.map((example) => (
                      <Button
                        className="h-auto min-h-9 justify-start whitespace-normal px-3 py-2 text-left text-xs text-muted-foreground"
                        disabled={isLoading}
                        key={example}
                        onClick={() => {
                          setQuestion(example)
                          setValidationMessage("")
                        }}
                        type="button"
                        variant="outline"
                      >
                        <FileText aria-hidden="true" className="h-3.5 w-3.5" />
                        {example}
                      </Button>
                    ))}
                  </div>
                ) : null}
              </form>

              {question || result ? (
                <div className="mt-5 border-t pt-5">
                  <Button
                    className="h-9 w-full"
                    disabled={isLoading}
                    onClick={clearWorkspace}
                    type="button"
                    variant="outline"
                  >
                    <X aria-hidden="true" className="h-3.5 w-3.5" />
                    Clear question and result
                  </Button>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card
            aria-live="polite"
            className="overflow-hidden border-border/90 bg-card/86"
          >
            <CardHeader className="border-b bg-muted/20 pb-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <CardTitle className="text-xl">Answer and sources</CardTitle>
                  <CardDescription className="mt-2">
                    Check the answer against its cited source.
                  </CardDescription>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {result ? <ResultBadge result={result} /> : null}
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-5 sm:p-6">
              {!isLoading && result ? (
                <p className="sr-only" role="status">
                  Request completed. {result.supported ? "Supported" : "Unsupported"} answer
                  with {result.citations.length} citation
                  {result.citations.length === 1 ? "" : "s"}.
                </p>
              ) : null}

              {isLoading ? (
                <div className="space-y-5">
                  {submittedQuestion ? (
                    <AskedQuestion question={submittedQuestion} />
                  ) : null}
                  <div className="flex items-center gap-2 rounded-md border bg-background/45 p-4 text-sm text-muted-foreground">
                    <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
                    Checking indexed sources.
                  </div>
                </div>
              ) : null}

              {!isLoading && requestState === "error" ? (
                <div className="space-y-5">
                  {submittedQuestion ? (
                    <AskedQuestion question={submittedQuestion} />
                  ) : null}
                  <Alert
                    className="border-destructive/45 bg-destructive/10 text-destructive"
                    variant="destructive"
                  >
                    <AlertCircle aria-hidden="true" className="h-4 w-4" />
                    <AlertTitle>Question failed</AlertTitle>
                    <AlertDescription className="text-destructive/90">
                      {errorMessage}
                    </AlertDescription>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button
                        className="h-9 px-3"
                        onClick={clearWorkspace}
                        type="button"
                        variant="ghost"
                      >
                        <X aria-hidden="true" className="h-3.5 w-3.5" />
                        Clear
                      </Button>
                    </div>
                  </Alert>
                </div>
              ) : null}

              {!isLoading && requestState !== "error" && !result ? (
                <EmptyAnswer />
              ) : null}

              {!isLoading && result?.supported ? (
                <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px] lg:items-start">
                  <section
                    className="min-w-0 space-y-4"
                    aria-labelledby="answer-title"
                  >
                    {submittedQuestion ? (
                      <AskedQuestion question={submittedQuestion} />
                    ) : null}
                    <VerificationSummary result={result} />

                    <div className="flex items-center justify-between gap-3">
                      <h2
                        id="answer-title"
                        className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground"
                      >
                        Answer
                      </h2>
                    </div>

                    <div className="rounded-md border bg-background/45 p-5 shadow-[inset_0_1px_0_hsl(210_18%_92%_/_0.04)]">
                      {result.citations.length > 0 ? (
                        <p className="mb-4 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                          Cited support:{" "}
                          {result.citations
                            .map((_, index) => sourceLabel(index))
                            .join(", ")}
                        </p>
                      ) : null}
                      <p className="max-w-[72ch] whitespace-pre-wrap text-base leading-7 text-foreground">
                        {result.answer}
                      </p>
                    </div>
                  </section>

                  <div className="border-t lg:hidden" />

                  <section
                    id="cited-sources"
                    className="min-w-0 space-y-3"
                    aria-labelledby="citations-title"
                  >
                    <div className="flex items-end justify-between gap-3">
                      <div>
                        <h2
                          id="citations-title"
                          className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground"
                        >
                          Cited source
                        </h2>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {result.citations.length} citation
                          {result.citations.length === 1 ? "" : "s"}
                        </p>
                      </div>
                    </div>
                    <CitationList
                      items={allCitationItems}
                      emptyMessage="No cited source returned."
                    />
                  </section>
                </div>
              ) : null}

              {!isLoading && result && !result.supported ? (
                <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px] lg:items-start">
                  <section
                    className="min-w-0 space-y-4"
                    aria-labelledby="unsupported-title"
                  >
                    {submittedQuestion ? (
                      <AskedQuestion question={submittedQuestion} />
                    ) : null}
                    <VerificationSummary result={result} />

                    <div className="rounded-md border border-[hsl(var(--warning-border))] bg-[hsl(var(--warning-background))] p-5 text-[hsl(var(--warning))]">
                      <div className="flex items-start gap-3">
                        <AlertCircle
                          aria-hidden="true"
                          className="mt-0.5 h-4 w-4 shrink-0"
                        />
                        <div className="min-w-0">
                          <h2
                            className="text-base font-semibold text-foreground"
                            id="unsupported-title"
                          >
                            No supported answer found
                          </h2>
                          <p className="mt-2 max-w-[72ch] text-sm leading-6 text-[hsl(var(--warning))]">
                            {result.refusal_reason ||
                              "The available sources did not provide enough support to answer this question reliably."}
                          </p>
                          <p className="mt-4 max-w-[72ch] text-sm leading-6 text-muted-foreground">
                            Revise the question or check the cited context before taking action.
                          </p>
                        </div>
                      </div>
                    </div>
                    <UnsupportedRecovery
                      onClear={clearWorkspace}
                      onRevise={reviseQuestion}
                    />
                  </section>

                  {result.citations.length > 0 ? (
                    <section
                      id="source-context"
                      className="min-w-0 space-y-3"
                      aria-labelledby="source-context-title"
                    >
                      <div>
                        <h2
                          id="source-context-title"
                          className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground"
                        >
                          Source
                        </h2>
                        <p className="mt-1 text-sm text-muted-foreground">
                          These snippets were close, but not enough to support an answer.
                        </p>
                      </div>
                      <CitationList
                        items={allCitationItems}
                        emptyMessage="No source returned."
                      />
                    </section>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  )
}
