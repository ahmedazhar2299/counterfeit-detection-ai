import { createBrowserRouter } from 'react-router-dom'

import { AppLayout } from '@/components/layout/app-layout'
import { AnalyzePage } from '@/components/pages/analyze-page'
import { HistoryPage } from '@/components/pages/history-page'
import { MetricsPage } from '@/components/pages/metrics-page'
import { ResultsPage } from '@/components/pages/results-page'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <AnalyzePage /> },
      { path: 'results/:listingId', element: <ResultsPage /> },
      { path: 'history', element: <HistoryPage /> },
      { path: 'metrics', element: <MetricsPage /> }
    ]
  }
])
