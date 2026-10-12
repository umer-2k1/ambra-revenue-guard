import { useEffect, useState } from 'react'
import { AlertTriangle, Loader2, ShieldCheck, Sparkles } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { getDemoClaim, scoreClaim } from '@/api'
import { cn } from '@/lib/utils'

const SERVICE_TYPES = [
  'ALS-1 Emergency',
  'ALS-1 Non-Emergency',
  'ALS-2',
  'BLS Emergency',
  'BLS Non-Emergency',
  'SCT',
]
const CPT_CODES = ['A0425', 'A0427', 'A0428', 'A0429', 'A0433', 'A0434']
const PAYERS = ['UnitedHealthcare', 'Aetna', 'Anthem BCBS', 'Medicare (Novitas MAC)', 'Cigna']

const riskStyle = {
  HIGH: { badge: 'high', ring: 'border-[#dc2626] bg-[#fee2e2] text-[#dc2626]' },
  MEDIUM: { badge: 'medium', ring: 'border-[#f59e0b] bg-[#fef3c7] text-[#b45309]' },
  LOW: { badge: 'low', ring: 'border-[#10b981] bg-[#d1fae5] text-[#059669]' },
}
const flagVariant = (r) => (r === 'high' ? 'high' : r === 'medium' ? 'medium' : 'low')
const money = (n) => `$${Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function Result({ result, onReset }) {
  const style = riskStyle[result.overall_risk] || riskStyle.LOW
  return (
    <Card className="p-6">
      <div className="flex items-center gap-5">
        <div className={cn('flex size-24 flex-col items-center justify-center rounded-full border-2', style.ring)}>
          <span className="text-lg font-extrabold">{result.overall_risk}</span>
          <span className="text-[10px] font-semibold tracking-widest">RISK</span>
        </div>
        <div>
          <div className="text-3xl font-bold text-primary">
            {result.risk_score}
            <span className="text-base font-medium text-muted-foreground">/100</span>
          </div>
          <div className="text-sm text-muted-foreground">
            {result.flags.length} {result.flags.length === 1 ? 'issue' : 'issues'} found · {result.rules_checked} rules checked
          </div>
        </div>
      </div>

      {result.top_recommendation && (
        <Alert variant="warm" className="mt-5">
          <Sparkles className="mt-0.5 text-accent" />
          <AlertDescription>
            <span className="font-semibold text-primary">Top recommendation: </span>
            {result.top_recommendation}
          </AlertDescription>
        </Alert>
      )}

      <div className="mt-5 space-y-3">
        {result.flags.map((f, i) => (
          <div
            key={i}
            className={cn(
              'rounded-2xl border border-border border-l-4 bg-card p-4',
              f.risk_level === 'high' ? 'border-l-[#dc2626]' : f.risk_level === 'medium' ? 'border-l-[#f59e0b]' : 'border-l-[#10b981]',
            )}
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={flagVariant(f.risk_level)}>{f.risk_level?.toUpperCase()}</Badge>
              <span className="font-semibold text-primary">{f.rule_title}</span>
            </div>
            <div className="mt-1.5 text-xs text-muted-foreground">
              Rule {f.rule_id} · based on {f.similar_denial_count} similar denials · est. risk{' '}
              <span className="font-semibold text-accent">{money(f.estimated_denial_risk)}</span>
            </div>
            <p className="mt-2 text-sm text-foreground/75">
              <span className="font-medium text-foreground">Missing:</span> {f.missing_element}
            </p>
            <div className="mt-2.5 rounded-lg bg-background px-3 py-2 text-sm text-foreground/75">
              <span className="font-semibold text-primary">Fix: </span>
              {f.suggestion}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 text-center">
        <Button variant="outline" onClick={onReset}>
          Score another claim
        </Button>
      </div>
    </Card>
  )
}

export default function ScoreClaim({ status }) {
  const [form, setForm] = useState({ service_type: 'ALS-1 Emergency', cpt_code: 'A0427', payer: 'UnitedHealthcare', narrative: '' })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const rulesCount = status?.total_rules ?? 0

  useEffect(() => {
    getDemoClaim()
      .then((c) => setForm({ service_type: c.service_type, cpt_code: c.cpt_code, payer: c.payer, narrative: c.narrative }))
      .catch(() => {})
  }, [])

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }))

  async function submit() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await scoreClaim(form))
    } catch (e) {
      setError(e.message || 'Scoring failed')
    } finally {
      setLoading(false)
    }
  }

  if (rulesCount === 0) {
    return (
      <Alert variant="warm">
        <ShieldCheck className="mt-0.5 text-accent" />
        <AlertDescription>
          Run the analysis first to build the knowledge base — then this tab scores new claims against it.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="p-6">
        <h2 className="text-base">Score a claim before submission</h2>
        <p className="mb-5 text-sm text-muted-foreground">
          Pre-filled with the demo claim. Edit anything, then score it.
        </p>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Service type">
            <Select value={form.service_type} onValueChange={set('service_type')}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {SERVICE_TYPES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </Field>
          <Field label="Payer">
            <Select value={form.payer} onValueChange={set('payer')}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {PAYERS.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
          </Field>
          <Field label="CPT code">
            <Select value={form.cpt_code} onValueChange={set('cpt_code')}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {CPT_CODES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </Field>
        </div>

        <div className="mt-4">
          <Field label="PCR narrative">
            <Textarea
              value={form.narrative}
              onChange={(e) => set('narrative')(e.target.value)}
              rows={9}
            />
          </Field>
        </div>

        <div className="mt-5 text-center">
          <Button size="lg" onClick={submit} disabled={loading || !form.narrative}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <ShieldCheck className="size-4" />}
            {loading ? 'Scoring…' : 'Score Claim'}
          </Button>
        </div>

        {error && (
          <Alert variant="destructive" className="mt-4">
            <AlertTriangle className="mt-0.5" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </Card>

      <div>
        {loading && <ResultSkeleton />}
        {!loading && result && <Result result={result} onReset={() => setResult(null)} />}
        {!loading && !result && (
          <Card className="flex h-full min-h-64 flex-col items-center justify-center p-10 text-center">
            <div className="mb-3 flex size-14 items-center justify-center rounded-full bg-secondary">
              <ShieldCheck className="size-7 text-primary" />
            </div>
            <p className="text-sm text-muted-foreground">
              The risk assessment will appear here — score, flags, and exactly what to fix.
            </p>
          </Card>
        )}
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </label>
      {children}
    </div>
  )
}

function ResultSkeleton() {
  return (
    <Card className="space-y-4 p-6">
      <Skeleton className="h-24 w-24 rounded-full" />
      <Separator />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-24 w-full" />
    </Card>
  )
}
