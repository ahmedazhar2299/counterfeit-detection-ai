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

export type CsvAnalyzeRowError = {
  row: number
  message: string
}

export type CsvAnalyzeResponse = {
  imported: number
  failed: number
  results: AnalysisResponse[]
  errors: CsvAnalyzeRowError[]
}

export type ListingWithAnalysis = {
  listing: ListingInput & { id: number; created_at: string }
  latest_analysis?: AnalysisResponse
}

export type MetricsPayload = {
  model_validation: {
    precision: number
    recall: number
    f1: number
    roc_auc: number
    train_accuracy: number
    test_accuracy: number
    train_error: number
    test_error: number
    confusion_matrix: number[][]
    roc_curve: { fpr: number[]; tpr: number[] }
    calibration_curve: { pred: number[]; true: number[] }
    dataset_profile: {
      row_count: number
      class_balance: {
        legit: number
        counterfeit: number
      }
    }
    feature_importance?: {
      method: string
      items: Array<{
        feature: string
        importance: number
      }>
    }
    model_types: Record<string, string>
  }
  live_marketplace: {
    summary: {
      total_analyses: number
      total_feedback: number
      average_risk_score: number
      latest_risk_score: number | null
    }
    action_counts: Record<string, number>
    score_bands: Record<string, number>
    daily_volume: Array<{ date: string; count: number }>
  }
}
