import { useCallback, useEffect, useState } from 'react'
import { BookOpen } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { TooltipProvider } from '@/components/ui/tooltip'
import { getDenials, getStatus } from '@/api'
import DenialsTable from '@/components/DenialsTable'
import AnalyzeView from '@/components/AnalyzeView'
import KnowledgeBase from '@/components/KnowledgeBase'
import ScoreClaim from '@/components/ScoreClaim'
import DenialDetail from '@/components/DenialDetail'
import GlossarySheet from '@/components/GlossarySheet'

export default function App() {
  const [tab, setTab] = useState('denials')
  const [status, setStatus] = useState(null)
  const [denials, setDenials] = useState(null)
  const [selectedDenial, setSelectedDenial] = useState(null)
  const [glossaryOpen, setGlossaryOpen] = useState(false)

  const refreshStatus = useCallback(async () => {
    try {
      setStatus(await getStatus())
    } catch {
      setStatus(null) // backend not up yet
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    const id = setInterval(refreshStatus, 15000)
    return () => clearInterval(id)
  }, [refreshStatus])

  useEffect(() => {
    getDenials().then(setDenials).catch(() => setDenials([]))
  }, [])

  // Open the case-file drawer from anywhere: pass a denial object OR an id.
  const openDenial = useCallback(
    (idOrCase) => {
      if (idOrCase && typeof idOrCase === 'object') {
        setSelectedDenial(idOrCase)
        return
      }
      const found = (denials || []).find((d) => d.id === idOrCase)
      if (found) setSelectedDenial(found)
    },
    [denials],
  )

  const rulesCount = status?.total_rules ?? 0

  return (
    <TooltipProvider delayDuration={150}>
      <div className="min-h-screen">
        <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
          <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-6">
            <div className="flex items-baseline gap-3">
              <span className="text-lg font-extrabold text-primary">
                <span className="text-accent">✦</span> Ambra
              </span>
              <span className="hidden text-sm text-muted-foreground sm:inline">
                Denial-to-Prevention Feedback Loop
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setGlossaryOpen(true)}>
                <BookOpen className="size-4" /> Glossary
              </Button>
              {status?.vector_store && (
                <span className="hidden text-xs text-muted-foreground lg:inline">
                  {status.llm_provider} · {status.embedding_provider} · {status.vector_store}
                </span>
              )}
              <Badge variant={rulesCount ? 'high' : 'gray'}>
                {rulesCount} {rulesCount === 1 ? 'rule' : 'rules'}
              </Badge>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-[1200px] px-6 py-8">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="denials">Denials</TabsTrigger>
              <TabsTrigger value="analyze">Analyze</TabsTrigger>
              <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
              <TabsTrigger value="score">Score Claim</TabsTrigger>
            </TabsList>

            <TabsContent value="denials">
              <DenialsTable denials={denials} onOpenDenial={openDenial} />
            </TabsContent>
            <TabsContent value="analyze">
              <AnalyzeView
                status={status}
                refreshStatus={refreshStatus}
                onGoToKnowledge={() => setTab('knowledge')}
              />
            </TabsContent>
            <TabsContent value="knowledge">
              <KnowledgeBase status={status} onOpenDenial={openDenial} />
            </TabsContent>
            <TabsContent value="score">
              <ScoreClaim status={status} />
            </TabsContent>
          </Tabs>
        </main>

        <DenialDetail denial={selectedDenial} onClose={() => setSelectedDenial(null)} />
        <GlossarySheet open={glossaryOpen} onOpenChange={setGlossaryOpen} />
      </div>
    </TooltipProvider>
  )
}
