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
  box_claim: number
  box_mm: number
}

// Top Model
export interface TopModel {
  rank: number
  model: string
  ifir: number
  box_claim: number
  box_mm: number
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
  fault_category: string
  count: number
  percentage: number
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
  trend_window?: number
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
    },
    view: params.trend_window ? { trend_months: params.trend_window } : undefined
  }
  const response = await apiClient.post('/ifir/model-analysis/analyze', request)
  return response.data
}
