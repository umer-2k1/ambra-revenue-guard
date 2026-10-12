import { useCallback, useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { TooltipProvider } from '@/components/ui/tooltip'
import { getStatus } from '@/api'
import DenialsTable from '@/components/DenialsTable'
import AnalyzeView from '@/components/AnalyzeView'
import KnowledgeBase from '@/components/KnowledgeBase'
import ScoreClaim from '@/components/ScoreClaim'

export default function App() {
  const [tab, setTab] = useState('denials')
  const [status, setStatus] = useState(null)

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
            <div className="flex items-center gap-3">
              {status?.vector_store && (
                <span className="hidden text-xs text-muted-foreground md:inline">
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
              <DenialsTable />
            </TabsContent>
            <TabsContent value="analyze">
              <AnalyzeView
                status={status}
                refreshStatus={refreshStatus}
                onGoToKnowledge={() => setTab('knowledge')}
              />
            </TabsContent>
            <TabsContent value="knowledge">
              <KnowledgeBase status={status} />
            </TabsContent>
            <TabsContent value="score">
              <ScoreClaim status={status} />
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </TooltipProvider>
  )
}
