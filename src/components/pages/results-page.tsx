import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import CountUp from 'react-countup'
import { motion } from 'framer-motion'
import { Bot, Check, Copy, MessageSquareText, ShieldCheck, Sparkles, TriangleAlert } from 'lucide-react'
import { useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { getListing, sendFeedback } from '@/lib/api'
import type { AnalysisResponse } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'

function statusStyles(action: string) {
  if (action === 'APPROVE') return 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-300'
  if (action === 'REVIEW') return 'bg-amber-500/20 text-amber-600 dark:text-amber-300'
  return 'bg-red-500/20 text-red-600 dark:text-red-300'
}

function escapeHtml(text: string) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function getSignalTone(action: AnalysisResponse['action']) {
  if (action === 'APPROVE') {
    return {
      title: 'What looked healthy',
      description: 'The strongest signals that supported automatic approval.',
      eyebrow: 'Approval confidence signals',
      icon: ShieldCheck,
      iconClass: 'bg-white/70 text-emerald-600 dark:bg-slate-900/60 dark:text-emerald-300',
      panelClass: 'border-emerald-300/30 bg-gradient-to-br from-emerald-500/10 via-teal-400/10 to-sky-400/10',
      barClass: 'bg-gradient-to-r from-emerald-400 to-sky-400',
      eyebrowClass: 'text-emerald-700 dark:text-emerald-300'
    }
  }

  return {
    title: 'What raised concern',
    description: 'The strongest signals that pushed this listing toward review risk.',
    eyebrow: 'Risk-driving signals',
    icon: TriangleAlert,
    iconClass: 'bg-white/70 text-amber-600 dark:bg-slate-900/60 dark:text-amber-300',
    panelClass: 'border-amber-300/30 bg-gradient-to-br from-amber-500/10 via-orange-400/10 to-rose-400/10',
    barClass: 'bg-gradient-to-r from-amber-400 to-rose-400',
    eyebrowClass: 'text-amber-700 dark:text-amber-300'
  }
}

export function ResultsPage() {
  const { listingId } = useParams()
  const [showHighlights, setShowHighlights] = useState(true)
  const [label, setLabel] = useState('unsure')
  const [notes, setNotes] = useState('')
  const [copied, setCopied] = useState(false)

  const query = useQuery({
    queryKey: ['listing', listingId],
    queryFn: () => getListing(Number(listingId)),
    enabled: !!listingId
  })

  const sessionAnalysis = useMemo(() => {
    const raw = sessionStorage.getItem('latest-analysis')
    return raw ? (JSON.parse(raw) as AnalysisResponse) : null
  }, [])

  const analysis = query.data?.latest_analysis && query.data.latest_analysis.listing_id === Number(listingId)
    ? query.data.latest_analysis
    : sessionAnalysis

  const feedbackMutation = useMutation({
    mutationFn: sendFeedback,
    onSuccess: () => toast.success('Feedback saved'),
    onError: () => toast.error('Feedback failed')
  })

  const highlightedDescription = useMemo(() => {
    const currentAnalysis = analysis
    const description = query.data?.listing.description || ''
    if (!currentAnalysis) return escapeHtml(description)
    if (!showHighlights || !currentAnalysis.highlights.length) return escapeHtml(description)
    const ranges = [...currentAnalysis.highlights]
      .filter((h) => h.start >= 0 && h.end <= description.length && h.start < h.end)
      .sort((a, b) => a.start - b.start)
    if (!ranges.length) return escapeHtml(description)

    let cursor = 0
    let out = ''
    ranges.forEach((r) => {
      if (r.start < cursor) return
      out += escapeHtml(description.slice(cursor, r.start))
      out += `<mark class="rounded bg-red-400/30 px-0.5 text-inherit">${escapeHtml(description.slice(r.start, r.end))}</mark>`
      cursor = r.end
    })
    out += escapeHtml(description.slice(cursor))
    return out
  }, [showHighlights, analysis, query.data?.listing.description])

  if (query.isLoading || !analysis) {
    return (
      <div className="grid gap-4">
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
      </div>
    )
  }

  const score = analysis.risk_score
  const radius = 96
  const circumference = 2 * Math.PI * radius
  const progress = circumference - (score / 100) * circumference
  const signalTone = getSignalTone(analysis.action)
  const SignalIcon = signalTone.icon
  const primarySignals = analysis.explanations.slice(0, 3)

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Risk Result</CardTitle>
          <CardDescription>Unified model decision with explainability.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <div className="flex items-center justify-center">
            <div className="relative h-60 w-60">
              <svg className="h-full w-full -rotate-90" viewBox="0 0 240 240">
                <circle cx="120" cy="120" r={radius} stroke="currentColor" className="text-muted/40" strokeWidth="18" fill="none" />
                <motion.circle
                  cx="120"
                  cy="120"
                  r={radius}
                  stroke="currentColor"
                  className="text-primary"
                  strokeWidth="18"
                  fill="none"
                  strokeLinecap="round"
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: progress }}
                  transition={{ duration: 1.2, ease: 'easeOut' }}
                  strokeDasharray={circumference}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Risk Score</p>
                <p className="text-4xl font-semibold">
                  <CountUp end={score} duration={1.1} decimals={0} />
                </p>
                <motion.div animate={{ scale: [1, 1.04, 1] }} transition={{ duration: 2, repeat: Infinity }}>
                  <Badge className={statusStyles(analysis.action)}>{analysis.action}</Badge>
                </motion.div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {[
              { label: 'Structured', value: analysis.structured_prob },
              { label: 'Text', value: analysis.text_prob },
              { label: 'Fused', value: analysis.fused_prob }
            ].map((item) => (
              <motion.div key={item.label} whileHover={{ y: -3 }} className="rounded-2xl border border-border/50 bg-white/40 p-4 dark:bg-slate-900/40">
                <div className="flex justify-between text-sm">
                  <span>{item.label}</span>
                  <span>{(item.value * 100).toFixed(1)}%</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-muted">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${item.value * 100}%` }} transition={{ duration: 0.9 }} className="h-2 rounded-full bg-primary" />
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="overflow-hidden lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>AI summary</CardTitle>
                <CardDescription>Plain-English explanation generated from the model output.</CardDescription>
              </div>
              <Badge className={analysis.llm_provider === 'gemini' ? 'bg-sky-500/15 text-sky-600 dark:text-sky-300' : 'bg-slate-500/15 text-slate-600 dark:text-slate-300'}>
                <Bot className="mr-1 h-3.5 w-3.5" />
                {analysis.llm_provider === 'gemini' ? 'Gemini Assist' : 'Local Summary'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative overflow-hidden rounded-[24px] border border-sky-300/30 bg-gradient-to-br from-sky-500/10 via-cyan-400/10 to-emerald-400/10 p-5"
            >
              <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-sky-400/20 blur-2xl" />
              <div className="absolute bottom-0 left-6 h-20 w-20 rounded-full bg-emerald-400/15 blur-2xl" />
              <div className="relative flex items-start gap-3">
                <div className="rounded-2xl bg-white/70 p-3 text-sky-600 shadow-sm dark:bg-slate-900/60 dark:text-sky-300">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium tracking-wide text-sky-700 dark:text-sky-300">
                    {analysis.action === 'APPROVE' ? 'Why the system felt comfortable approving this' : 'Why the system wants extra attention here'}
                  </p>
                  <motion.p
                    key={analysis.llm_summary}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5 }}
                    className="max-w-4xl text-[15px] leading-7 text-slate-700 dark:text-slate-100"
                  >
                    {analysis.llm_summary || 'No AI summary available.'}
                  </motion.p>
                </div>
              </div>
            </motion.div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{signalTone.title}</CardTitle>
            <CardDescription>{signalTone.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`relative overflow-hidden rounded-[24px] border p-5 ${signalTone.panelClass}`}
            >
              <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-white/20 blur-2xl dark:bg-white/5" />
              <div className="relative flex items-start gap-3">
                <div className={`rounded-2xl p-3 shadow-sm ${signalTone.iconClass}`}>
                  <SignalIcon className="h-5 w-5" />
                </div>
                <div className="w-full space-y-3">
                  <p className={`text-sm font-medium tracking-wide ${signalTone.eyebrowClass}`}>{signalTone.eyebrow}</p>
                  <div className="grid gap-3">
                    {primarySignals.map((item, index) => (
                      <motion.div
                        key={`${item.feature}-${index}`}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.06 }}
                        className="rounded-2xl border border-white/40 bg-white/50 p-4 backdrop-blur-sm dark:border-white/10 dark:bg-slate-950/30"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold capitalize text-slate-800 dark:text-slate-100">{item.feature.replaceAll('_', ' ')}</p>
                          <Badge>{item.source}</Badge>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.detail}</p>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>

            <div className="rounded-2xl border border-border/50 bg-white/35 p-4 dark:bg-slate-900/30">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium">
                  {analysis.action === 'APPROVE' ? 'Supporting signal mix' : 'Risk signal mix'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {analysis.action === 'APPROVE' ? 'Shown for transparency' : 'Shown for analyst review'}
                </p>
              </div>
              <div className="mt-3 space-y-3">
                {analysis.explanations.slice(0, 6).map((item) => {
                  const normalized = Math.min(100, Math.max(8, Math.abs(item.contribution) * 100))
                  return (
                    <div key={`${item.source}-${item.feature}`} className="space-y-1.5">
                      <div className="flex items-center justify-between gap-3 text-xs">
                        <span className="capitalize text-slate-700 dark:text-slate-300">{item.feature.replaceAll('_', ' ')}</span>
                        <span className="text-muted-foreground">{item.source}</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-muted/80">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${normalized}%` }}
                          transition={{ duration: 0.8 }}
                          className={`h-full rounded-full ${signalTone.barClass}`}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Description highlights</CardTitle>
            <CardDescription>
              {analysis.highlights.length
                ? 'Text segments that contributed to model concern.'
                : 'No suspicious phrasing was detected in the listing text.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-3 flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowHighlights((v) => !v)}>
                {showHighlights ? 'Hide highlights' : 'Show highlights'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  await navigator.clipboard.writeText(JSON.stringify(analysis, null, 2))
                  setCopied(true)
                  toast.success('Copied JSON')
                  setTimeout(() => setCopied(false), 1000)
                }}
              >
                {copied ? <Check className="mr-1 h-4 w-4" /> : <Copy className="mr-1 h-4 w-4" />} Copy JSON
              </Button>
            </div>
            <p className="rounded-xl border border-border/60 p-4 text-sm leading-7" dangerouslySetInnerHTML={{ __html: highlightedDescription }} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model comparison + feedback</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 md:grid-cols-2">
          <div className="grid gap-3">
            <div className="rounded-xl border border-border/60 p-4">
              <p className="text-sm font-medium">Structured Model</p>
              <p className="text-xs text-muted-foreground">Metadata + seller trust + price band features.</p>
            </div>
            <div className="rounded-xl border border-border/60 p-4">
              <p className="text-sm font-medium">Text Model</p>
              <p className="text-xs text-muted-foreground">TF-IDF lexical patterns + suspicious phrase features.</p>
            </div>
            <div className="rounded-xl border border-border/60 p-4">
              <p className="text-sm font-medium">Fusion</p>
              <p className="text-xs text-muted-foreground">Weighted blend with optional calibrator.</p>
            </div>
          </div>

          <div className="space-y-3 rounded-2xl border border-border/60 p-4">
            <p className="inline-flex items-center text-sm font-medium"><MessageSquareText className="mr-2 h-4 w-4" /> Analyst feedback</p>
            <Select value={label} onChange={(e) => setLabel(e.target.value)}>
              <option value="unsure">Unsure</option>
              <option value="counterfeit">Counterfeit</option>
              <option value="legit">Legit</option>
            </Select>
            <Textarea placeholder="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
            <Button onClick={() => feedbackMutation.mutate({ analysis_id: analysis.analysis_id, label, notes })} disabled={feedbackMutation.isPending}>
              Submit feedback
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
