/**
 * RA 相关 API
 */
import apiClient from './index'

export type TopSort = 'claim' | 'ra'

// 筛选选项
export interface RaOptions {
  time_range: {
    min_month: string
    max_month: string
  }
  odms: string[]
  segments: string[]
  models: string[]
}

// 趋势数据点
export interface TrendPoint {
  month: string
  ra: number
  ra_claim?: number
  ra_mm?: number
}

// Top Model
export interface TopModel {
  rank: number
  model: string
  ra: number
  ra_claim: number
  ra_mm: number
  top_issues?: TopIssue[]
}

// Top ODM
export interface TopOdm {
  rank: number
  odm: string
  ra: number
  ra_claim: number
  ra_mm: number
}

// Top Issue
export interface TopIssue {
  rank: number
  issue: string
  count: number
  share?: number
}

// 月度明细
export interface MonthlyTopModels {
  month: string
  items: TopModel[]
}

export interface MonthlyTopOdms {
  month: string
  items: TopOdm[]
}

export interface MonthlyTopIssues {
  month: string
  items: TopIssue[]
}

// 饼图数据
export interface OdmPieItem {
  odm: string
  ra: number
  share: number
  ra_claim?: number
  ra_mm?: number
}

export interface SegmentPieItem {
  segment: string
  ra: number
  share: number
  ra_claim?: number
  ra_mm?: number
}

export interface ModelPieItem {
  model: string
  ra: number
  share: number
  ra_claim?: number
  ra_mm?: number
}

// ODM 分析卡片
export interface OdmCard {
  odm: string
  trend: TrendPoint[]
  top_models: TopModel[]
  monthly_top_models?: MonthlyTopModels[]
  ai_summary: string
}

// Segment 分析卡片
export interface SegmentCard {
  segment: string
  trend: TrendPoint[]
  top_odms: TopOdm[]
  top_models: TopModel[]
  monthly_top_odms?: MonthlyTopOdms[]
  monthly_top_models?: MonthlyTopModels[]
  ai_summary: string
}

// Model 分析卡片
export interface ModelCard {
  model: string
  trend: TrendPoint[]
  top_issues: TopIssue[]
  monthly_top_issues?: MonthlyTopIssues[]
  ai_summary: string
}

// Summary 数据 (Block D)
export interface OdmSummary {
  odm_pie: OdmPieItem[]
}

export interface SegmentSummary {
  segment_pie: SegmentPieItem[]
}

export interface ModelSummary {
  model_pie: ModelPieItem[]
}

// 分析元数据
export interface AnalyzeMeta {
  data_as_of: string
  time_range: {
    start_month: string
    end_month: string
  }
}

// ODM 分析响应
export interface OdmAnalyzeResponse {
  meta: AnalyzeMeta
  cards: OdmCard[]
  summary?: OdmSummary
}

// Segment 分析响应
export interface SegmentAnalyzeResponse {
  meta: AnalyzeMeta
  cards: SegmentCard[]
  summary?: SegmentSummary
}

// Model 分析响应
export interface ModelAnalyzeResponse {
  meta: AnalyzeMeta
  cards: ModelCard[]
  summary?: ModelSummary
}

/**
 * 获取 RA 筛选选项（支持任意组合过滤）
 */
export async function getRaOptions(filters?: {
  segments?: string[]
  odms?: string[]
  models?: string[]
}): Promise<RaOptions> {
  const params: Record<string, string> = {}
  if (filters?.segments?.length) params.segments = filters.segments.join(',')
  if (filters?.odms?.length) params.odms = filters.odms.join(',')
  if (filters?.models?.length) params.models = filters.models.join(',')
  const response = await apiClient.get('/ra/options', { 
    params: Object.keys(params).length ? params : undefined 
  })
  return response.data
}

// 兼容旧接口
export const getRaOdmOptions = (segments?: string[]) => 
  getRaOptions(segments?.length ? { segments } : undefined)

export const getRaSegmentOptions = (odms?: string[]) => 
  getRaOptions(odms?.length ? { odms } : undefined)

export const getRaModelOptions = (segments?: string[], odms?: string[]) => 
  getRaOptions({ segments, odms })

/**
 * RA ODM 分析
 */
export async function analyzeRaOdm(params: {
  start_month: string
  end_month: string
  odms: string[]
  segments?: string[]
  models?: string[]
  top_model_sort?: TopSort
}): Promise<OdmAnalyzeResponse> {
  const request = {
    time_range: {
      start_month: params.start_month,
      end_month: params.end_month
    },
    filters: {
      odms: params.odms,
      segments: params.segments,
      models: params.models
    },
    view: {
      top_model_sort: params.top_model_sort
    }
  }
  const response = await apiClient.post('/ra/odm-analysis/analyze', request)
  return response.data
}

/**
 * RA Segment 分析
 */
export async function analyzeRaSegment(params: {
  start_month: string
  end_month: string
  segments: string[]
  odms?: string[]
  models?: string[]
  top_odm_sort?: TopSort
  top_model_sort?: TopSort
}): Promise<SegmentAnalyzeResponse> {
  const request = {
    time_range: {
      start_month: params.start_month,
      end_month: params.end_month
    },
    filters: {
      segments: params.segments,
      odms: params.odms,
      models: params.models
    },
    view: {
      top_odm_sort: params.top_odm_sort,
      top_model_sort: params.top_model_sort
    }
  }
  const response = await apiClient.post('/ra/segment-analysis/analyze', request)
  return response.data
}

/**
 * RA Model 分析
 */
export async function analyzeRaModel(params: {
  start_month: string
  end_month: string
  models: string[]
  segments?: string[]
  odms?: string[]
}): Promise<ModelAnalyzeResponse> {
  const request = {
    time_range: {
      start_month: params.start_month,
      end_month: params.end_month
    },
    filters: {
      models: params.models,
      segments: params.segments,
      odms: params.odms
    }
  }
  const response = await apiClient.post('/ra/model-analysis/analyze', request)
  return response.data
}

// ==================== Report Download ====================

export interface ReportDownloadResult {
  blob: Blob
  filename?: string
}

function _getFilename(headers: Record<string, string>): string | undefined {
  const cd = headers['content-disposition']
  if (!cd) return undefined
  const m = cd.match(/filename\*=UTF-8''([^;]+)/i)
  if (m?.[1]) return decodeURIComponent(m[1])
  const m2 = cd.match(/filename="?([^";]+)"?/i)
  return m2?.[1]
}

export async function downloadRaModelReport(params: {
  start_month: string
  end_month: string
  models: string[]
  segments?: string[]
  odms?: string[]
  tgt?: number
}): Promise<ReportDownloadResult> {
  const request = {
    time_range: { start_month: params.start_month, end_month: params.end_month },
    filters: { models: params.models, segments: params.segments, odms: params.odms },
    tgt: params.tgt,
  }
  const response = await apiClient.post('/ra/report/model', request, {
    responseType: 'blob', timeout: 120000,
  })
  return { blob: response.data, filename: _getFilename(response.headers as any) }
}

export async function downloadRaOdmReport(params: {
  start_month: string
  end_month: string
  odms: string[]
  segments?: string[]
  models?: string[]
  top_model_sort?: TopSort
  tgt?: number
}): Promise<ReportDownloadResult> {
  const request = {
    time_range: { start_month: params.start_month, end_month: params.end_month },
    filters: { odms: params.odms, segments: params.segments, models: params.models },
    view: { top_model_sort: params.top_model_sort },
    tgt: params.tgt,
  }
  const response = await apiClient.post('/ra/report/odm', request, {
    responseType: 'blob', timeout: 120000,
  })
  return { blob: response.data, filename: _getFilename(response.headers as any) }
}

export async function downloadRaSegmentReport(params: {
  start_month: string
  end_month: string
  segments: string[]
  odms?: string[]
  models?: string[]
  top_odm_sort?: TopSort
  top_model_sort?: TopSort
  tgt?: number
}): Promise<ReportDownloadResult> {
  const request = {
    time_range: { start_month: params.start_month, end_month: params.end_month },
    filters: { segments: params.segments, odms: params.odms, models: params.models },
    view: { top_odm_sort: params.top_odm_sort, top_model_sort: params.top_model_sort },
    tgt: params.tgt,
  }
  const response = await apiClient.post('/ra/report/segment', request, {
    responseType: 'blob', timeout: 120000,
  })
  return { blob: response.data, filename: _getFilename(response.headers as any) }
}


// Issue 明细行
export interface IssueDetailRow {
  model: string
  fault_category: string
  problem_descr_by_tech?: string
  claim_nbr: string
  claim_month: string
  plant?: string
}

// Issue 明细响应
export interface IssueDetailResponse {
  total: number
  page: number
  page_size: number
  items: IssueDetailRow[]
}

/**
 * RA Model Issue 明细
 */
export async function getRaModelIssueDetails(params: {
  start_month: string
  end_month: string
  model: string
  issue: string
  month?: string
  segments?: string[]
  odms?: string[]
  page?: number
  page_size?: number
}): Promise<IssueDetailResponse> {
  const request = {
    time_range: {
      start_month: params.start_month,
      end_month: params.end_month
    },
    filters: {
      model: params.model,
      issue: params.issue,
      month: params.month,
      segments: params.segments,
      odms: params.odms
    },
    pagination: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10
    }
  }
  const response = await apiClient.post('/ra/model-analysis/issue-details', request)
  return response.data
}
