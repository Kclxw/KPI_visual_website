/**
 * IFIR 相关 API
 */
import apiClient from './index'

// 筛选选项
export interface IfirOptions {
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
  ifir: number
  box_claim?: number
  box_mm?: number
}

// Top Model
export interface TopModel {
  rank: number
  model: string
  ifir: number
  box_claim: number
  box_mm: number
  top_issues?: TopIssue[]
}

// Top ODM
export interface TopOdm {
  rank: number
  odm: string
  ifir: number
  box_claim: number
  box_mm: number
}

// Top Issue
export interface TopIssue {
  rank: number
  issue: string
  count: number
  share?: number
}

export type TopSort = 'claim' | 'ifir'

export interface IssueDetailRow {
  model: string
  fault_category: string
  problem_descr_by_tech?: string
  claim_nbr: string
  claim_month: string
  plant?: string
}

export interface IssueDetailResponse {
  total: number
  page: number
  page_size: number
  items: IssueDetailRow[]
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
  ifir: number
  share: number
  box_claim?: number
  box_mm?: number
}

export interface SegmentPieItem {
  segment: string
  ifir: number
  share: number
  box_claim?: number
  box_mm?: number
}

export interface ModelPieItem {
  model: string
  ifir: number
  share: number
  box_claim?: number
  box_mm?: number
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
 * 获取 IFIR 筛选选项（支持任意组合过滤）
 */
export async function getIfirOptions(filters?: {
  segments?: string[]
  odms?: string[]
  models?: string[]
}): Promise<IfirOptions> {
  const params: Record<string, string> = {}
  if (filters?.segments?.length) params.segments = filters.segments.join(',')
  if (filters?.odms?.length) params.odms = filters.odms.join(',')
  if (filters?.models?.length) params.models = filters.models.join(',')
  const response = await apiClient.get('/ifir/options', { 
    params: Object.keys(params).length ? params : undefined 
  })
  return response.data
}

// 兼容旧接口
export const getIfirOdmOptions = (segments?: string[]) => 
  getIfirOptions(segments?.length ? { segments } : undefined)

export const getIfirSegmentOptions = (odms?: string[]) => 
  getIfirOptions(odms?.length ? { odms } : undefined)

export const getIfirModelOptions = (segments?: string[], odms?: string[]) => 
  getIfirOptions({ segments, odms })

/**
 * IFIR ODM 分析
 */
export async function analyzeIfirOdm(params: {
  start_month: string
  end_month: string
  odms: string[]
  segments?: string[]
  models?: string[]
  top_model_sort?: TopSort
}): Promise<OdmAnalyzeResponse> {
  // 转换为后端期望的格式
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
  const response = await apiClient.post('/ifir/odm-analysis/analyze', request)
  return response.data
}

/**
 * IFIR Segment 分析
 */
export async function analyzeIfirSegment(params: {
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
  const response = await apiClient.post('/ifir/segment-analysis/analyze', request)
  return response.data
}

/**
 * IFIR Model 分析
 */
export async function analyzeIfirModel(params: {
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
  const response = await apiClient.post('/ifir/model-analysis/analyze', request)
  return response.data
}

/**
 * IFIR Model Issue 明细
 */
export async function getIfirModelIssueDetails(params: {
  start_month: string
  end_month: string
  model: string
  issue: string
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
      segments: params.segments,
      odms: params.odms
    },
    pagination: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 10
    }
  }
  const response = await apiClient.post('/ifir/model-analysis/issue-details', request)
  return response.data
}
