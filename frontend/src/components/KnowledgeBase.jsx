import { useEffect, useState } from 'react'
import { Brain, ChevronDown, Trash2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { getRules, resetSystem } from '@/api'
import { cn } from '@/lib/utils'
import { carcMeaning, cptMeaning, serviceMeaning } from '@/lib/glossary'

const sevVariant = (s) => (s === 'high' ? 'high' : s === 'medium' ? 'medium' : 'low')
const money = (n) => `$${Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function Term({ children, meaning }) {
  const badge = (
    <Badge variant="outline" className={cn(meaning && 'cursor-help border-dashed')}>
      {children}
    </Badge>
  )
  if (!meaning) return badge
  return (
    <Tooltip>
      <TooltipTrigger asChild>{badge}</TooltipTrigger>
      <TooltipContent>{meaning}</TooltipContent>
    </Tooltip>
  )
}

function RuleCard({ rule, onOpenDenial }) {
  const [open, setOpen] = useState(false)
  const title = rule.plain_title || rule.rule_title

  return (
    <Card className="overflow-hidden">
      <div className="p-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-primary">{rule.rule_id}</span>
          <Badge variant={sevVariant(rule.severity)}>{rule.severity?.toUpperCase()}</Badge>
          <span className="text-xs text-muted-foreground">confidence {Math.round((rule.confidence ?? 0) * 100)}%</span>
        </div>

        <h3 className="mt-2 text-lg leading-snug">{title}</h3>
        {rule.plain_summary && <p className="mt-1.5 text-sm leading-relaxed text-foreground/70">{rule.plain_summary}</p>}

        {rule.required_elements?.length > 0 && (
          <div className="mt-4">
            <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              What to add to the chart
            </div>
            <ul className="ml-4 list-disc space-y-1 text-sm text-foreground/80">
              {rule.required_elements.map((el, i) => (
                <li key={i}>{el}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Term meaning={carcMeaning(rule.carc_pattern)}>{rule.carc_pattern}</Term>
          <Term meaning={cptMeaning(rule.cpt_pattern)}>{rule.cpt_pattern}</Term>
          <Term meaning={serviceMeaning(rule.service_pattern)}>{rule.service_pattern}</Term>
          <Term>{rule.payer_pattern}</Term>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2">
          <span className="text-sm text-muted-foreground">
            Learned from {rule.source_count} denials · average{' '}
            <span className="font-semibold text-accent">{money(rule.avg_denied_amount)}</span>
          </span>
          {rule.source_denials?.length > 0 && (
            <span className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-muted-foreground">taught by</span>
              {rule.source_denials.map((id) => (
                <button
                  key={id}
                  onClick={() => onOpenDenial(id)}
                  className="rounded-full border bg-card px-2 py-0.5 text-xs font-semibold text-primary transition-colors hover:bg-secondary"
                >
                  {id}
                </button>
              ))}
            </span>
          )}
        </div>
      </div>

      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-4 border-t px-6 py-3 text-left text-sm text-muted-foreground transition-colors hover:bg-secondary/40"
      >
        <span>Details for billing teams — exact wording, codes, and why this rule exists</span>
        <ChevronDown className={cn('size-4 shrink-0 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="space-y-4 border-t px-6 py-5">
          <div>
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Technical rule
            </div>
            <p className="text-sm text-foreground/80">{rule.rule_title}</p>
          </div>
          {rule.risk_description && (
            <div>
              <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Why this causes denials
              </div>
              <p className="text-sm leading-relaxed text-foreground/70">{rule.risk_description}</p>
            </div>
          )}
          {rule.recommended_phrases?.length > 0 && (
            <div>
              <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Example wording a medic can use
              </div>
              <div className="space-y-2">
                {rule.recommended_phrases.map((ph, i) => (
                  <div key={i} className="rounded-lg border-l-[3px] border-accent bg-background px-3 py-2 text-sm italic text-foreground/70">
                    “{ph}”
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

export default function KnowledgeBase({ status, onOpenDenial, refreshStatus }) {
  const [rules, setRules] = useState(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if ((status?.total_rules ?? 0) >= 0) {
      getRules().then(setRules).catch(() => setRules([]))
    }
  }, [status?.total_rules])

  async function deleteAll() {
    if (!window.confirm('Delete all learned rules and embeddings? This clears the knowledge base.')) return
    setDeleting(true)
    try {
      await resetSystem()
      setRules([])
      if (refreshStatus) await refreshStatus()
    } finally {
      setDeleting(false)
    }
  }

  if (!rules) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-52 w-full" />
        ))}
      </div>
    )
  }

  if (rules.length === 0) {
    return (
      <Alert variant="warm">
        <Brain className="mt-0.5 text-accent" />
        <AlertDescription>
          No rules learned yet. Run the analysis on the <span className="font-semibold">Analyze</span> tab
          to build the knowledge base.
        </AlertDescription>
      </Alert>
    )
  }

  const learnedFrom = rules.reduce((sum, r) => sum + (r.source_count || 0), 0)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h2 className="text-lg">Knowledge Base</h2>
          <span className="text-sm text-muted-foreground">
            {rules.length} rules learned from {learnedFrom} denials
          </span>
          <span className="text-sm text-muted-foreground">· hover any dashed tag to see what the code means</span>
        </div>
        <Button variant="outline" size="sm" onClick={deleteAll} disabled={deleting}>
          <Trash2 className="size-4" /> Delete all
        </Button>
      </div>
      <div className="space-y-4">
        {rules.map((rule) => (
          <RuleCard key={rule.rule_id} rule={rule} onOpenDenial={onOpenDenial} />
        ))}
      </div>
    </div>
  )
}
