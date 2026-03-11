import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { getListings } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/table'

export function HistoryPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [brand, setBrand] = useState('all')
  const [category, setCategory] = useState('all')
  const [action, setAction] = useState('all')
  const [sort, setSort] = useState('risk_desc')

  const query = useQuery({ queryKey: ['history'], queryFn: () => getListings(100) })

  const { brands, categories, rows } = useMemo(() => {
    const list = query.data ?? []
    const brands = [...new Set(list.map((x) => x.listing.brand))]
    const categories = [...new Set(list.map((x) => x.listing.category))]
    const rows = list
      .filter((x) => x.listing.title.toLowerCase().includes(search.toLowerCase()))
      .filter((x) => (brand === 'all' ? true : x.listing.brand === brand))
      .filter((x) => (category === 'all' ? true : x.listing.category === category))
      .filter((x) => (action === 'all' ? true : x.latest_analysis?.action === action))
      .sort((a, b) => {
        if (sort === 'risk_desc') return (b.latest_analysis?.risk_score || 0) - (a.latest_analysis?.risk_score || 0)
        if (sort === 'risk_asc') return (a.latest_analysis?.risk_score || 0) - (b.latest_analysis?.risk_score || 0)
        return +new Date(b.listing.created_at) - +new Date(a.listing.created_at)
      })
    return { brands, categories, rows }
  }, [query.data, search, brand, category, action, sort])

  if (query.isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-16" />
        <Skeleton className="h-72" />
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Listing History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 grid gap-3 md:grid-cols-5">
          <Input placeholder="Search title" value={search} onChange={(e) => setSearch(e.target.value)} />
          <Select value={brand} onChange={(e) => setBrand(e.target.value)}>
            <option value="all">All Brands</option>
            {brands.map((b) => <option key={b}>{b}</option>)}
          </Select>
          <Select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="all">All Categories</option>
            {categories.map((c) => <option key={c}>{c}</option>)}
          </Select>
          <Select value={action} onChange={(e) => setAction(e.target.value)}>
            <option value="all">All Actions</option>
            <option value="APPROVE">APPROVE</option>
            <option value="REVIEW">REVIEW</option>
            <option value="BLOCK">BLOCK</option>
          </Select>
          <Select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="risk_desc">Risk high-low</option>
            <option value="risk_asc">Risk low-high</option>
            <option value="date_desc">Newest</option>
          </Select>
        </div>

        <div className="overflow-auto rounded-xl border border-border/50">
          <Table>
            <THead>
              <TR>
                <TH>Title</TH>
                <TH>Brand</TH>
                <TH>Category</TH>
                <TH>Risk</TH>
                <TH>Action</TH>
                <TH>Date</TH>
              </TR>
            </THead>
            <TBody>
              {rows.map((row) => (
                <motion.tr key={row.listing.id} whileHover={{ y: -1 }} className="cursor-pointer" onClick={() => navigate(`/results/${row.listing.id}`)}>
                  <TD>{row.listing.title}</TD>
                  <TD>{row.listing.brand}</TD>
                  <TD>{row.listing.category}</TD>
                  <TD>{row.latest_analysis?.risk_score?.toFixed(1) ?? '-'}</TD>
                  <TD>{row.latest_analysis?.action ?? '-'}</TD>
                  <TD>{new Date(row.listing.created_at).toLocaleString()}</TD>
                </motion.tr>
              ))}
            </TBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
