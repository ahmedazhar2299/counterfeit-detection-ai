import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Activity, BrainCircuit, Database, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'

import { getMetrics } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const snapshotPalette = ['#38bdf8', '#14b8a6', '#22c55e', '#f59e0b', '#8b5cf6', '#fb7185']
const volumeGradientId = 'daily-volume-gradient'

export function MetricsPage() {
  const query = useQuery({ queryKey: ['metrics'], queryFn: getMetrics })

  if (query.isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-72" />
        <Skeleton className="h-72" />
      </div>
    )
  }

  const validation = query.data?.model_validation
  const live = query.data?.live_marketplace
  if (!validation || !live) return null

  const rocData = validation.roc_curve.fpr.map((fpr, i) => ({ fpr, tpr: validation.roc_curve.tpr[i] }))
  const calibration = validation.calibration_curve.pred.map((pred, i) => ({ pred, true: validation.calibration_curve.true[i] }))
  const [tn, fp] = validation.confusion_matrix[0]
  const [fn, tp] = validation.confusion_matrix[1]
  const confusionData = [
    { metric: 'TP', value: tp },
    { metric: 'FP', value: fp },
    { metric: 'TN', value: tn },
    { metric: 'FN', value: fn }
  ]
  const actionData = Object.entries(live.action_counts).map(([name, value]) => ({ name, value }))
  const scoreBandData = Object.entries(live.score_bands).map(([name, value]) => ({ name, value }))
  const classBalanceData = [
    { name: 'Legit', value: validation.dataset_profile.class_balance.legit },
    { name: 'Counterfeit', value: validation.dataset_profile.class_balance.counterfeit }
  ]
  const shapData =
    validation.feature_importance?.items.map((item) => ({
      ...item,
      shortLabel: item.feature.length > 24 ? `${item.feature.slice(0, 24)}...` : item.feature
    })) ?? []

  const totalVolume = live.daily_volume.reduce((sum, row) => sum + row.count, 0)
  const peakDay = live.daily_volume.reduce<{ date: string; count: number } | null>(
    (peak, row) => (!peak || row.count > peak.count ? row : peak),
    null
  )

  const summary = [
    { name: 'Precision', value: validation.precision, icon: ShieldCheck, tone: 'from-sky-500/25 to-cyan-500/10' },
    { name: 'Recall', value: validation.recall, icon: Activity, tone: 'from-emerald-500/25 to-teal-500/10' },
    { name: 'F1 Score', value: validation.f1, icon: Sparkles, tone: 'from-violet-500/20 to-fuchsia-500/10' },
    { name: 'ROC-AUC', value: validation.roc_auc, icon: TrendingUp, tone: 'from-amber-500/25 to-orange-500/10' },
    { name: 'Train Accuracy', value: validation.train_accuracy, icon: BrainCircuit, tone: 'from-blue-500/25 to-sky-500/10' },
    { name: 'Test Accuracy', value: validation.test_accuracy, icon: Database, tone: 'from-teal-500/25 to-cyan-500/10' }
  ]

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader>
            <CardDescription>Total analyses</CardDescription>
            <CardTitle>{live.summary.total_analyses}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Average live risk</CardDescription>
            <CardTitle>{live.summary.average_risk_score.toFixed(1)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Latest risk score</CardDescription>
            <CardTitle>{live.summary.latest_risk_score?.toFixed(1) ?? '-'}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Feedback received</CardDescription>
            <CardTitle>{live.summary.total_feedback}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="overflow-hidden border-white/10 bg-white/5 backdrop-blur-xl">
            <CardHeader className="relative">
              <div className="absolute inset-x-6 top-0 h-24 rounded-full bg-cyan-500/10 blur-3xl" />
              <CardTitle>Daily Volume</CardTitle>
              <CardDescription>Live throughput of listing analyses in your current database.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Analyses logged</p>
                  <p className="mt-2 text-3xl font-semibold">{totalVolume}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Peak day</p>
                  <p className="mt-2 text-2xl font-semibold">{peakDay?.count ?? 0}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{peakDay?.date ?? 'No activity yet'}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-500/18 to-sky-500/8 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-cyan-100/80">Current signal</p>
                  <p className="mt-2 text-2xl font-semibold">{live.summary.latest_risk_score?.toFixed(1) ?? '-'}</p>
                  <p className="mt-1 text-xs text-cyan-50/70">Latest analyzed listing risk</p>
                </div>
              </div>

              <div className="h-80 rounded-3xl border border-white/10 bg-slate-950/35 p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={live.daily_volume}>
                    <defs>
                      <linearGradient id={volumeGradientId} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.95} />
                        <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.15} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" />
                    <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(2, 6, 23, 0.92)',
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: 16
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="count"
                      stroke={`url(#${volumeGradientId})`}
                      strokeWidth={4}
                      dot={{ r: 0 }}
                      activeDot={{ r: 6, fill: '#67e8f9', stroke: '#0f172a', strokeWidth: 2 }}
                      name="Analyses"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card className="overflow-hidden border-white/10 bg-white/5 backdrop-blur-xl">
            <CardHeader>
              <CardTitle>Validation Snapshot</CardTitle>
              <CardDescription>Offline holdout metrics for the deployed fusion pipeline. These only change when you retrain.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                {summary.map((item, index) => {
                  const Icon = item.icon
                  return (
                    <div
                      key={item.name}
                      className={`relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br ${item.tone} p-4`}
                    >
                      <div className="absolute inset-x-3 top-0 h-16 rounded-full bg-white/10 blur-2xl" />
                      <div className="relative flex items-start justify-between">
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-slate-300">{item.name}</p>
                          <p className="mt-3 text-3xl font-semibold text-white">{(item.value * 100).toFixed(2)}%</p>
                        </div>
                        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-2">
                          <Icon className="h-4 w-4 text-white" />
                        </div>
                      </div>
                      <div className="relative mt-4 h-1.5 overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          className="h-full rounded-full bg-white"
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.max(4, item.value * 100)}%` }}
                          transition={{ duration: 0.7, delay: 0.04 * index }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Training rows</p>
                  <p className="mt-2 text-2xl font-semibold">{validation.dataset_profile.row_count.toLocaleString()}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Model stack</p>
                  <p className="mt-2 text-sm text-slate-200">
                    {validation.model_types.structured} + {validation.model_types.text}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">{validation.model_types.fusion}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader>
              <CardTitle>Live Action Distribution</CardTitle>
              <CardDescription>Changes as you analyze real listings in this database.</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={actionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                  <XAxis dataKey="name" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#14b8a6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardHeader>
              <CardTitle>Live Risk Bands</CardTitle>
              <CardDescription>How your analyzed listings currently spread across approval thresholds.</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={scoreBandData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                  <XAxis dataKey="name" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#38bdf8" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader>
              <CardTitle>Dataset Balance</CardTitle>
              <CardDescription>Class distribution used for offline training and evaluation.</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={classBalanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                  <XAxis dataKey="name" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#22c55e" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardHeader>
              <CardTitle>SHAP Plot</CardTitle>
              <CardDescription>
                Global feature impact for the structured model. Uses SHAP when available, otherwise a stable importance fallback.
              </CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              {shapData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[...shapData].reverse()} layout="vertical" margin={{ left: 12, right: 12 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="shortLabel" width={136} tick={{ fontSize: 11 }} />
                    <Tooltip
                      formatter={(value: number) => value.toFixed(4)}
                      labelFormatter={(_, payload) => payload?.[0]?.payload?.feature ?? ''}
                    />
                    <Bar dataKey="importance" radius={[0, 10, 10, 0]}>
                      {shapData
                        .slice()
                        .reverse()
                        .map((item, index) => (
                          <Cell key={`${item.feature}-${index}`} fill={snapshotPalette[index % snapshotPalette.length]} />
                        ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-white/10 bg-slate-950/30 text-sm text-muted-foreground">
                  Retrain the model to generate feature importance for this view.
                </div>
              )}
            </CardContent>
            {validation.feature_importance?.method && (
              <div className="px-6 pb-6 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                Method: {validation.feature_importance.method}
              </div>
            )}
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader>
              <CardTitle>ROC Curve</CardTitle>
              <CardDescription>Offline classifier separation quality on the test split.</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={rocData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                  <XAxis dataKey="fpr" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="tpr" stroke="#0ea5e9" strokeWidth={3} dot={false} name="TPR" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardHeader>
              <CardTitle>Calibration Curve</CardTitle>
              <CardDescription>Offline probability calibration on the validation split.</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={calibration}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                  <XAxis dataKey="pred" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="true" stroke="#14b8a6" strokeWidth={3} dot={false} name="Observed" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardHeader>
              <CardTitle>Confusion Matrix</CardTitle>
              <CardDescription>Offline test-split counts, not live analyst outcomes.</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={confusionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                  <XAxis dataKey="metric" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#38bdf8" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
