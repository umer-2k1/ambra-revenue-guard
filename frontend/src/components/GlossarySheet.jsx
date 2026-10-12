import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CARC, CPT, SERVICE, TERM } from '@/lib/glossary'

function Group({ title, entries }) {
  return (
    <div>
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{title}</div>
      <dl className="divide-y overflow-hidden rounded-xl border bg-card">
        {Object.entries(entries).map(([code, meaning]) => (
          <div key={code} className="flex gap-4 px-3 py-2.5">
            <dt className="w-40 shrink-0 font-semibold text-primary">{code}</dt>
            <dd className="text-sm text-foreground/75">{meaning}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export default function GlossarySheet({ open, onOpenChange }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Codes &amp; terms glossary</SheetTitle>
          <SheetDescription>Plain-English meanings for every code used in this demo.</SheetDescription>
        </SheetHeader>
        <ScrollArea className="flex-1">
          <div className="space-y-7 p-6">
            <Group title="Denial reason codes (CARC)" entries={CARC} />
            <Group title="Ambulance billing codes (CPT)" entries={CPT} />
            <Group title="Service levels" entries={SERVICE} />
            <Group title="Terms &amp; acronyms" entries={TERM} />
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
