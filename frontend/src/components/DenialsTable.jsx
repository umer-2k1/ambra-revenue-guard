import { useEffect, useState } from 'react'
import { AlertTriangle, ChevronRight } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { getDenials, getDenialStats } from '@/api'
import DenialDetail from '@/components/DenialDetail'

const outcomeVariant = (o = '') => {
  if (o === 'overturned') return 'green'
  if (o === 'denied') return 'red'
  if (o.includes('partial')) return 'amber'
  return 'gray'
}
const pretty = (s = '') => s.replace(/_/g, ' ')
const money = (n) =>
  n == null ? '—' : `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function Stat({ value, label }) {
  return (
    <Card className="p-4">
      <div className="text-2xl font-bold leading-none text-accent">{value}</div>
      <div className="mt-2 text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </Card>
  )
}

export default function DenialsTable() {
  const [denials, setDenials] = useState(null)
  const [stats, setStats] = useState(null)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    getDenials().then(setDenials).catch(() => setDenials([]))
    getDenialStats().then(setStats).catch(() => setStats(null))
  }, [])

  const recoveredPct = stats
    ? Math.round((((stats.by_outcome?.overturned ?? 0) / stats.total_cases) * 100) || 0)
    : '—'

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat value={stats ? stats.total_cases : '—'} label="Denial cases" />
        <Stat value={stats ? money(stats.total_denied_amount) : '—'} label="Total denied" />
        <Stat value={stats ? Object.keys(stats.by_payer).length : '—'} label="Payers" />
        <Stat value={`${recoveredPct}%`} label="Recovered on appeal" />
      </div>

      <Card className="overflow-hidden">
        <div className="px-6 pb-2 pt-6">
          <h2 className="text-base">Denial cases</h2>
          <p className="text-sm text-muted-foreground">
            Resolved denials across {stats ? Object.keys(stats.by_payer).length : 5} payers — click any row to open the full case file.
          </p>
        </div>

        {!denials ? (
          <div className="space-y-2 p-6 pt-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>ID</TableHead>
                <TableHead>Payer</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>CPT</TableHead>
                <TableHead>CARC</TableHead>
                <TableHead className="text-right">Denied</TableHead>
                <TableHead>Outcome</TableHead>
                <TableHead className="w-8" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {denials.map((d) => (
                <TableRow
                  key={d.id}
                  onClick={() => setSelected(d)}
                  className="cursor-pointer even:bg-secondary/25"
                >
                  <TableCell className="font-semibold text-primary">{d.id}</TableCell>
                  <TableCell>
                    <Badge variant="payer">{d.payer}</Badge>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-muted-foreground">{d.service_type}</TableCell>
                  <TableCell>{d.cpt_code}</TableCell>
                  <TableCell>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="cursor-help font-medium">{d.carc_code}</span>
                      </TooltipTrigger>
                      <TooltipContent>{d.denial_reason}</TooltipContent>
                    </Tooltip>
                  </TableCell>
                  <TableCell className="text-right font-medium">{money(d.denied_amount)}</TableCell>
                  <TableCell>
                    <Badge variant={outcomeVariant(d.appeal_outcome)}>{pretty(d.appeal_outcome)}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    <ChevronRight className="size-4" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Alert variant="warm">
        <AlertTriangle className="mt-0.5 text-accent" />
        <AlertDescription>
          <span className="font-semibold text-primary">This knowledge is trapped in resolved cases.</span>{' '}
          When an appeal is won, the lesson never flows back — charting and denial management run as
          separate pipelines.
        </AlertDescription>
      </Alert>

      <DenialDetail denial={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
