import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { getMetrics } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

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

  const m = query.data?.metrics
  if (!m) return null

  const rocData = m.roc_curve.fpr.map((fpr, i) => ({ fpr, tpr: m.roc_curve.tpr[i] }))
  const calibration = m.calibration_curve.pred.map((pred, i) => ({ pred, true: m.calibration_curve.true[i] }))
  const [tn, fp] = m.confusion_matrix[0]
  const [fn, tp] = m.confusion_matrix[1]
  const confusionData = [
    { metric: 'TP', value: tp },
    { metric: 'FP', value: fp },
    { metric: 'TN', value: tn },
    { metric: 'FN', value: fn }
  ]
  const summary = [
    { name: 'Precision', value: m.precision },
    { name: 'Recall', value: m.recall },
    { name: 'F1', value: m.f1 },
    { name: 'ROC-AUC', value: m.roc_auc }
  ]

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <Card>
          <CardHeader><CardTitle>ROC Curve</CardTitle></CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rocData}>
                <CartesianGrid strokeDasharray="3 3" />
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
          <CardHeader><CardTitle>Calibration Curve</CardTitle></CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={calibration}>
                <CartesianGrid strokeDasharray="3 3" />
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
          <CardHeader><CardTitle>Confusion Matrix</CardTitle></CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confusionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="metric" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#38bdf8" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <Card>
          <CardHeader><CardTitle>Model Metrics</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {summary.map((item) => (
              <div key={item.name} className="rounded-xl border border-border/50 p-3">
                <p className="text-xs text-muted-foreground">{item.name}</p>
                <p className="text-2xl font-semibold">{(item.value * 100).toFixed(2)}%</p>
              </div>
            ))}
            <div className="rounded-xl border border-border/50 p-3 text-sm text-muted-foreground">
              Structured: {m.model_types.structured} | Text: {m.model_types.text}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
