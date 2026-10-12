import { FileText, Globe, Mail, Phone, StickyNote } from 'lucide-react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

const money = (n) =>
  n == null ? '—' : `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

const outcomeVariant = (o = '') => {
  if (o === 'overturned') return 'green'
  if (o === 'denied') return 'red'
  if (o.includes('partial')) return 'amber'
  return 'gray'
}
const pretty = (s = '') => s.replace(/_/g, ' ')

const KIND_STYLE = {
  claim: { dot: 'bg-[#6b5b4b]', badge: 'gray', label: 'Claim' },
  denial: { dot: 'bg-[#dc2626]', badge: 'red', label: 'Denial' },
  appeal: { dot: 'bg-[#f59e0b]', badge: 'amber', label: 'Appeal' },
  resolution: { dot: 'bg-[#10b981]', badge: 'green', label: 'Resolution' },
}

const CHANNEL_ICON = { call: Phone, portal: Globe, remit: Mail, mail: Mail, note: StickyNote }

function Section({ title, children }) {
  return (
    <div>
      <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{title}</div>
      <div className="text-sm leading-relaxed text-foreground/80">{children}</div>
    </div>
  )
}

function Stat({ label, value, accent }) {
  return (
    <div className="rounded-xl border bg-card px-3 py-2">
      <div className={cn('text-base font-bold', accent ? 'text-accent' : 'text-primary')}>{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  )
}

export default function DenialDetail({ denial, onClose }) {
  const open = !!denial
  const d = denial

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent>
        {d && (
          <>
            <SheetHeader>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-bold text-primary">{d.id}</span>
                <Badge variant="payer">{d.payer}</Badge>
                <Badge variant={outcomeVariant(d.appeal_outcome)}>{pretty(d.appeal_outcome)}</Badge>
              </div>
              <SheetTitle>{d.service_type} transport</SheetTitle>
              <SheetDescription>
                {d.cpt_code} · {d.carc_code}
                {d.rarc_code ? ` / ${d.rarc_code}` : ''} · {d.region} · DOS {d.claim_date}
              </SheetDescription>
            </SheetHeader>

            <ScrollArea className="flex-1">
              <div className="space-y-6 p-6">
                <div className="grid grid-cols-4 gap-3">
                  <Stat label="Billed" value={money(d.billed_amount)} />
                  <Stat label="Denied" value={money(d.denied_amount)} accent />
                  <Stat label="Recovered" value={money(d.paid_after_appeal)} />
                  <Stat label="Days to appeal" value={d.days_to_appeal ?? '—'} />
                </div>

                <Section title="What the crew charted">
                  <p className="rounded-xl bg-secondary/60 p-3">{d.pcr_excerpt}</p>
                </Section>

                <Section title="Why the payer denied it">
                  <p>{d.denial_reason}</p>
                </Section>

                <Section title="What was missing">
                  <p className="rounded-xl border-l-[3px] border-accent bg-background p-3">{d.missing_element}</p>
                </Section>

                <Section title="How the appeal team fixed it">{d.appeal_strategy}</Section>

                <Separator />

                <div>
                  <div className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    Case timeline
                  </div>
                  <ol className="relative space-y-4 border-l border-border pl-5">
                    {(d.timeline || []).map((ev, i) => {
                      const style = KIND_STYLE[ev.kind] || KIND_STYLE.claim
                      return (
                        <li key={i} className="relative">
                          <span className={cn('absolute -left-[27px] top-1 size-3 rounded-full ring-4 ring-background', style.dot)} />
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">{ev.date}</span>
                            <Badge variant={style.badge}>{style.label}</Badge>
                          </div>
                          <div className="mt-0.5 font-medium text-primary">{ev.title}</div>
                          <div className="text-sm text-foreground/70">{ev.detail}</div>
                        </li>
                      )
                    })}
                  </ol>
                </div>

                {d.payer_notes?.length > 0 && (
                  <div>
                    <div className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Payer activity &amp; follow-ups
                    </div>
                    <div className="space-y-2">
                      {d.payer_notes.map((n, i) => {
                        const Icon = CHANNEL_ICON[n.channel] || FileText
                        return (
                          <div key={i} className="flex gap-3 rounded-xl border bg-card p-3">
                            <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary">
                              <Icon className="size-3.5 text-primary" />
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground">
                                {n.date} · {pretty(n.channel)}
                              </div>
                              <div className="text-sm text-foreground/80">{n.text}</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {d.appeal_letter && (
                  <div>
                    <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      <FileText className="size-3.5" /> Appeal letter sent
                    </div>
                    <pre className="whitespace-pre-wrap rounded-xl border bg-secondary/40 p-4 font-sans text-sm leading-relaxed text-foreground/80">
                      {d.appeal_letter}
                    </pre>
                  </div>
                )}
              </div>
            </ScrollArea>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
