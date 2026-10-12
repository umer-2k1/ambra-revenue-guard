import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, ArrowRight, Brain, CheckCircle2, Loader2, RefreshCw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { startAnalysis, resetSystem } from '@/api'
import { cn } from '@/lib/utils'

const sevVariant = (s) => (s === 'high' ? 'high' : s === 'medium' ? 'medium' : 'low')

function FeedLine({ evt }) {
  const icon =
    evt.step === 'stored' || evt.step === 'complete' ? (
      <CheckCircle2 className="size-4 shrink-0 text-[#059669]" />
    ) : evt.step === 'error' ? (
      <AlertTriangle className="size-4 shrink-0 text-destructive" />
    ) : (
      <Loader2 className="size-4 shrink-0 animate-spin text-accent" />
    )
  return (
    <div className="flex items-start gap-2.5 border-b border-border/60 py-2.5 text-sm last:border-0">
      <span className="mt-0.5">{icon}</span>
      <div className="min-w-0 flex-1">
        <div className="text-foreground/80">{evt.message}</div>
        {evt.rule && (
          <div className="mt-2 rounded-xl border border-border border-l-4 border-l-[#dc2626] bg-card p-3">
            <div className="flex items-center gap-2">
              <Badge variant={sevVariant(evt.rule.severity)}>{evt.rule.severity?.toUpperCase()}</Badge>
              <span className="text-xs font-semibold text-primary">{evt.rule.rule_id}</span>
              <span className="text-xs text-muted-foreground">
                confidence {Math.round((evt.rule.confidence ?? 0) * 100)}% · {evt.rule.source_count} denials
              </span>
            </div>
            <div className="mt-1 font-medium text-primary">{evt.rule.rule_title}</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AnalyzeView({ status, refreshStatus, onGoToKnowledge }) {
  const [running, setRunning] = useState(false)
  const [events, setEvents] = useState([])
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [resetting, setResetting] = useState(false)
  const feedRef = useRef(null)

  const rulesCount = status?.total_rules ?? 0
  const complete = rulesCount > 0
  const stats = status

  useEffect(() => {
    const el = feedRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [events])

  async function run() {
    setRunning(true)
    setError(null)
    setEvents([])
    setProgress(0)
    try {
      await startAnalysis((evt) => {
        setEvents((prev) => [...prev, evt])
        if (typeof evt.progress === 'number') setProgress(evt.progress)
      })
      await refreshStatus()
    } catch (e) {
      setError(e.message || 'Analysis failed')
    } finally {
      setRunning(false)
    }
  }

  async function reset() {
    setResetting(true)
    try {
      await resetSystem()
      setEvents([])
      setProgress(0)
      setError(null)
      await refreshStatus()
    } finally {
      setResetting(false)
    }
  }

  const hasRun = running || events.length > 0

  return (
    <div className="space-y-6">
      {!hasRun && !complete && (
        <Card className="p-10 text-center">
          <div className="mx-auto mb-3 flex size-14 items-center justify-center rounded-full bg-secondary">
            <Brain className="size-7 text-primary" />
          </div>
          <h2 className="text-xl">Ready to analyze</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {stats ? `${stats.total_denials} denial cases` : '28 denial cases'} · 5 payers ·{' '}
            {stats ? `$${Math.round(stats.total_denied_amount).toLocaleString()}` : ''} denied
          </p>
          <ol className="mx-auto mt-5 inline-block space-y-1 text-left text-sm text-foreground/70">
            <li>1. Cluster similar denial patterns</li>
            <li>2. Extract prevention rules with AI</li>
            <li>3. Store rules in vector memory</li>
          </ol>
          <div className="mt-7">
            <Button size="lg" onClick={run} disabled={running}>
              Analyze Denials
            </Button>
          </div>
        </Card>
      )}

      {hasRun && (
        <Card className="p-6">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-medium text-primary">
              {running ? 'Analyzing…' : complete ? 'Analysis complete' : 'Stopped'}
            </span>
            <span className="text-xs text-muted-foreground">{Math.round(progress * 100)}%</span>
          </div>
          <Progress value={progress * 100} />

          <div className="mt-5 rounded-2xl border border-border bg-card p-4">
            <div
              ref={feedRef}
              className="max-h-[340px] overflow-y-auto pr-1"
            >
              {events.map((evt, i) => (
                <FeedLine key={i} evt={evt} />
              ))}
              {running && events.length === 0 && (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  <Loader2 className="mx-auto mb-2 size-5 animate-spin text-accent" />
                  Connecting…
                </div>
              )}
            </div>
          </div>

          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertTriangle className="mt-0.5" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {complete && !running && (
            <Alert variant="success" className="mt-4">
              <CheckCircle2 className="mt-0.5" />
              <AlertDescription>
                <span className="font-semibold">
                  Analysis complete — {rulesCount} prevention rules learned.
                </span>{' '}
                Rules and embeddings stored in vector memory.
              </AlertDescription>
            </Alert>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            {complete && !running && (
              <Button onClick={onGoToKnowledge}>
                View Knowledge Base <ArrowRight className="size-4" />
              </Button>
            )}
            <Button variant="outline" onClick={reset} disabled={resetting || running}>
              <RefreshCw className={resetting ? 'size-4 animate-spin' : 'size-4'} />
              Reset &amp; re-analyze
            </Button>
          </div>
        </Card>
      )}

      {complete && !hasRun && (
        <Card className="p-6">
          <Alert variant="success">
            <CheckCircle2 className="mt-0.5" />
            <AlertDescription>
              <span className="font-semibold">
                Analysis complete — {rulesCount} prevention rules in memory.
              </span>{' '}
              Open the Knowledge Base to review them, or reset to run the analysis again.
            </AlertDescription>
          </Alert>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button onClick={onGoToKnowledge}>
              View Knowledge Base <ArrowRight className="size-4" />
            </Button>
            <Button variant="outline" onClick={reset} disabled={resetting}>
              <RefreshCw className={cn('size-4', resetting && 'animate-spin')} />
              Reset &amp; re-analyze
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
