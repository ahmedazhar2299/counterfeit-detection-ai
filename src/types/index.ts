export type ListingInput = {
  title: string
  description: string
  brand: string
  category: string
  price: number
  currency: string
  seller_age_days?: number
  seller_rating?: number
  seller_sales_count?: number
  review_count?: number
  shipping_country?: string
  return_policy_days?: number
}

export type ExplanationItem = {
  source: 'structured' | 'text' | 'fusion'
  feature: string
  contribution: number
  detail: string
}

export type Highlight = {
  phrase: string
  start: number
  end: number
}

export type AnalysisResponse = {
  analysis_id: number
  listing_id: number
  risk_score: number
  action: 'APPROVE' | 'REVIEW' | 'BLOCK'
  structured_prob: number
  text_prob: number
  fused_prob: number
  llm_summary?: string | null
  llm_provider?: string | null
  explanations: ExplanationItem[]
  highlights: Highlight[]
  model: {
    version: string
    training_timestamp: string
  }
}

export type ListingWithAnalysis = {
  listing: ListingInput & { id: number; created_at: string }
  latest_analysis?: AnalysisResponse
}

export type MetricsPayload = {
  metrics: {
    precision: number
    recall: number
    f1: number
    roc_auc: number
    confusion_matrix: number[][]
    roc_curve: { fpr: number[]; tpr: number[] }
    calibration_curve: { pred: number[]; true: number[] }
    model_types: Record<string, string>
  }
}
