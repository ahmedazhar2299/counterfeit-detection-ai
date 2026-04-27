import { useMemo, useRef, useState } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { FileUp, ShieldCheck, Sparkles, TriangleAlert } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { analyzeListing, analyzeListingsCsv } from '@/lib/api'
import type { ListingInput } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

const LEGIT_PRESET: ListingInput = {
  title: 'Apple iPhone 15 Pro Max 256GB - Original',
  description: 'Purchased from official Apple Store. Invoice, box, and serial details included. 30-day returns.',
  brand: 'Apple',
  category: 'Electronics',
  price: 1049,
  currency: 'USD',
  seller_age_days: 980,
  seller_rating: 4.9,
  seller_sales_count: 2200,
  review_count: 860,
  shipping_country: 'US',
  return_policy_days: 30
}

const SUSPICIOUS_PRESET: ListingInput = {
  title: 'Rolex watch 1:1 mirror quality no box',
  description: 'Factory surplus copy version, inspired luxury style. DM for wholesale lot and discounted luxury offers.',
  brand: 'Rolex',
  category: 'Watches',
  price: 389,
  currency: 'USD',
  seller_age_days: 8,
  seller_rating: 2.2,
  seller_sales_count: 3,
  review_count: 0,
  shipping_country: 'CN',
  return_policy_days: 1
}

const initial: ListingInput = {
  title: '',
  description: '',
  brand: '',
  category: '',
  price: 0,
  currency: 'USD'
}

const loadingMessages = [
  'Scanning lexical risk signals...',
  'Computing seller trust and price outlier features...',
  'Fusing structured and text model outputs...',
  'Building explainability payload...'
]

export function AnalyzePage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<ListingInput>(initial)
  const [showErrors, setShowErrors] = useState(false)
  const [importSummary, setImportSummary] = useState<{ imported: number; failed: number } | null>(null)
  const csvInputRef = useRef<HTMLInputElement | null>(null)

  const validation = useMemo(() => ({
    title: form.title.trim().length >= 4,
    description: form.description.trim().length >= 8,
    brand: form.brand.trim().length >= 2,
    category: form.category.trim().length >= 2,
    price: Number(form.price) > 0
  }), [form])

  const isValid = Object.values(validation).every(Boolean)

  const mutation = useMutation({
    mutationFn: analyzeListing,
    onSuccess: (res) => {
      toast.success('Analysis complete')
      sessionStorage.setItem('latest-analysis', JSON.stringify(res))
      navigate(`/results/${res.listing_id}`)
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        if (Array.isArray(detail) && detail.length) {
          toast.error(`${detail[0].loc?.[1] ?? 'field'}: ${detail[0].msg}`)
          return
        }
      }
      toast.error('Analysis failed. Check backend is running.')
    }
  })

  const csvMutation = useMutation({
    mutationFn: analyzeListingsCsv,
    onSuccess: (res) => {
      setImportSummary({ imported: res.imported, failed: res.failed })
      toast.success(`Imported ${res.imported} listing(s), ${res.failed} failed`)
      if (res.results.length > 0) {
        sessionStorage.setItem('latest-analysis', JSON.stringify(res.results[res.results.length - 1]))
      }
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        toast.error(typeof detail === 'string' ? detail : 'CSV import failed')
        return
      }
      toast.error('CSV import failed. Check backend is running.')
    }
  })

  const update = (key: keyof ListingInput, value: string | number | undefined) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const onSubmit = () => {
    setShowErrors(true)
    if (!isValid) return

    const safeNum = (v: unknown) => {
      const n = Number(v)
      return Number.isFinite(n) ? n : undefined
    }

    const rating = safeNum(form.seller_rating)
    mutation.mutate({
      ...form,
      price: Number(form.price),
      seller_age_days: safeNum(form.seller_age_days),
      seller_rating: rating !== undefined && rating >= 1 && rating <= 5 ? rating : undefined,
      seller_sales_count: safeNum(form.seller_sales_count),
      review_count: safeNum(form.review_count),
      return_policy_days: safeNum(form.return_policy_days),
      shipping_country: form.shipping_country?.trim() || undefined
    })
  }

  const onCsvButtonClick = () => csvInputRef.current?.click()

  const onCsvPicked = (file: File | null) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.csv')) {
      toast.error('Please choose a .csv file')
      return
    }
    setImportSummary(null)
    csvMutation.mutate(file)
  }

  const loadingText = loadingMessages[Math.floor(Date.now() / 700) % loadingMessages.length]

  return (
    <div className="space-y-6">
      <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
        <p className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
          <Sparkles className="mr-2 h-3.5 w-3.5" /> AI-Powered Listing Guardrail
        </p>
        <h1 className="text-3xl font-semibold md:text-4xl">AI-Driven Counterfeit Risk Assessment Framework</h1>
        <p className="max-w-2xl text-muted-foreground">Hybrid ML combines seller metadata and listing text patterns with explainable decisions.</p>
      </motion.section>

      <Card>
        <CardHeader>
          <CardTitle>Analyze Listing</CardTitle>
          <CardDescription>Use a preset or enter product details manually.</CardDescription>
          <div className="flex flex-wrap gap-2 pt-2">
            <Button variant="secondary" onClick={() => setForm(LEGIT_PRESET)}>
              <ShieldCheck className="mr-2 h-4 w-4" /> Legit Example
            </Button>
            <Button variant="secondary" onClick={() => setForm(SUSPICIOUS_PRESET)}>
              <TriangleAlert className="mr-2 h-4 w-4" /> Suspicious Example
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1">
              <Input placeholder="Title" value={form.title} onChange={(e) => update('title', e.target.value)} />
              {showErrors && !validation.title && <p className="text-xs text-red-500">Title must be at least 4 characters.</p>}
            </div>
            <div className="space-y-1">
              <Input placeholder="Brand" value={form.brand} onChange={(e) => update('brand', e.target.value)} />
              {showErrors && !validation.brand && <p className="text-xs text-red-500">Brand is required.</p>}
            </div>
            <div className="space-y-1">
              <Input placeholder="Category" value={form.category} onChange={(e) => update('category', e.target.value)} />
              {showErrors && !validation.category && <p className="text-xs text-red-500">Category is required.</p>}
            </div>
            <div className="space-y-1">
              <Input type="number" step="0.01" placeholder="Price" value={form.price || ''} onChange={(e) => update('price', Number(e.target.value))} />
              {showErrors && !validation.price && <p className="text-xs text-red-500">Price must be {'>'} 0.</p>}
            </div>
            <Select value={form.currency} onChange={(e) => update('currency', e.target.value)}>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
            </Select>
            <Input placeholder="Shipping Country (optional)" value={form.shipping_country || ''} onChange={(e) => update('shipping_country', e.target.value)} />
            <Input type="number" placeholder="Seller Age Days" value={form.seller_age_days ?? ''} onChange={(e) => update('seller_age_days', e.target.value === '' ? undefined : Number(e.target.value))} />
            <Input type="number" step="0.1" placeholder="Seller Rating (1-5)" value={form.seller_rating ?? ''} onChange={(e) => update('seller_rating', e.target.value === '' ? undefined : Number(e.target.value))} />
            <Input type="number" placeholder="Seller Sales Count" value={form.seller_sales_count ?? ''} onChange={(e) => update('seller_sales_count', e.target.value === '' ? undefined : Number(e.target.value))} />
            <Input type="number" placeholder="Review Count" value={form.review_count ?? ''} onChange={(e) => update('review_count', e.target.value === '' ? undefined : Number(e.target.value))} />
            <Input type="number" placeholder="Return Policy Days" value={form.return_policy_days ?? ''} onChange={(e) => update('return_policy_days', e.target.value === '' ? undefined : Number(e.target.value))} />
          </div>

          <div className="mt-4 space-y-1">
            <Textarea placeholder="Description" value={form.description} onChange={(e) => update('description', e.target.value)} />
            {showErrors && !validation.description && <p className="text-xs text-red-500">Description must be at least 8 characters.</p>}
          </div>

          <div className="mt-6 flex items-center gap-3">
            <motion.div whileTap={{ scale: 0.98 }} whileHover={{ y: -2 }}>
              <Button size="lg" onClick={onSubmit} disabled={mutation.isPending}>
                {mutation.isPending ? 'Analyzing...' : 'Analyze Risk'}
              </Button>
            </motion.div>
            <input
              ref={csvInputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => onCsvPicked(e.target.files?.[0] ?? null)}
            />
            <motion.div whileTap={{ scale: 0.98 }} whileHover={{ y: -2 }}>
              <Button variant="secondary" size="lg" onClick={onCsvButtonClick} disabled={csvMutation.isPending}>
                <FileUp className="mr-2 h-4 w-4" />
                {csvMutation.isPending ? 'Importing CSV...' : 'Import Bulk CSV'}
              </Button>
            </motion.div>
            {mutation.isPending && <p className="animate-pulse text-sm text-muted-foreground">{loadingText}</p>}
          </div>

          {csvMutation.isPending && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-3 rounded-xl border border-primary/25 bg-primary/10 p-3 text-sm text-primary"
            >
              <span className="inline-flex animate-pulse items-center">Analyzing CSV rows and creating listings...</span>
            </motion.div>
          )}

          {importSummary && !csvMutation.isPending && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25 }}
              className="mt-3 rounded-xl border border-emerald-300/40 bg-emerald-500/10 p-3 text-sm text-emerald-700 dark:text-emerald-300"
            >
              CSV import complete. Imported <span className="font-semibold">{importSummary.imported}</span> row(s),
              failed <span className="font-semibold">{importSummary.failed}</span>.
            </motion.div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
