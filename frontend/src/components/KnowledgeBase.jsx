import { useEffect, useState } from 'react'
import { Brain, ChevronDown } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { getRules } from '@/api'
import { cn } from '@/lib/utils'

const sevVariant = (s) => (s === 'high' ? 'high' : s === 'medium' ? 'medium' : 'low')
const money = (n) => `$${Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function RuleCard({ rule }) {
  const [open, setOpen] = useState(true)
  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start justify-between gap-4 p-6 text-left"
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold text-primary">{rule.rule_id}</span>
            <Badge variant={sevVariant(rule.severity)}>{rule.severity?.toUpperCase()}</Badge>
            <span className="text-xs text-muted-foreground">
              confidence {Math.round((rule.confidence ?? 0) * 100)}%
            </span>
          </div>
          <h3 className="mt-2 text-base">{rule.rule_title}</h3>
        </div>
        <ChevronDown className={cn('mt-1 size-4 shrink-0 text-muted-foreground transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="px-6 pb-6">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">Payer: {rule.payer_pattern}</Badge>
            <Badge variant="outline">CPT: {rule.cpt_pattern}</Badge>
            <Badge variant="outline">CARC: {rule.carc_pattern}</Badge>
            {rule.service_pattern && <Badge variant="outline">{rule.service_pattern}</Badge>}
          </div>
          <p className="mt-3 text-sm text-foreground/70">
            Based on {rule.source_count} denials · avg denied{' '}
            <span className="font-semibold text-accent">{money(rule.avg_denied_amount)}</span>
          </p>
          {rule.risk_description && (
            <p className="mt-3 text-sm text-muted-foreground">{rule.risk_description}</p>
          )}

          <Separator className="my-5" />

          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Required elements
              </div>
              <ul className="ml-4 list-disc space-y-1.5 text-sm text-foreground/75">
                {(rule.required_elements || []).map((el, i) => (
                  <li key={i}>{el}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Recommended phrases
              </div>
              <div className="space-y-2">
                {(rule.recommended_phrases || []).map((ph, i) => (
                  <div key={i} className="rounded-lg border-l-[3px] border-accent bg-background px-3 py-2 text-sm italic text-foreground/70">
                    “{ph}”
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

export default function KnowledgeBase({ status }) {
  const [rules, setRules] = useState(null)

  useEffect(() => {
    if ((status?.total_rules ?? 0) >= 0) {
      getRules().then(setRules).catch(() => setRules([]))
    }
  }, [status?.total_rules])

  if (!rules) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-44 w-full" />
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
      <div className="flex items-baseline gap-3">
        <h2 className="text-lg">Knowledge Base</h2>
        <span className="text-sm text-muted-foreground">
          {rules.length} rules learned from {learnedFrom} denials
        </span>
      </div>
      <div className="space-y-4">
        {rules.map((rule) => (
          <RuleCard key={rule.rule_id} rule={rule} />
        ))}
      </div>
    </div>
  )
}
