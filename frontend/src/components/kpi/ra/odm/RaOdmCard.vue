<template>
  <div class="ra-odm-card">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="card-title">
        <el-icon><OfficeBuilding /></el-icon>
        <span>{{ odm }}</span>
      </div>
      <div class="card-meta">
        <el-tag size="small">数据截至: {{ latestMonth }}</el-tag>
      </div>
    </div>
    
    <!-- Block A: 趋势图 -->
    <div class="card-section">
      <div class="section-header">
        <h3 class="section-title">
          <el-icon><TrendCharts /></el-icon>
          RA趋势 (DPPM)
        </h3>
        <el-radio-group v-model="chartMode" size="small" @change="initChart">
          <el-radio-button value="yearly">年度对比</el-radio-button>
          <el-radio-button value="timeline">完整趋势</el-radio-button>
        </el-radio-group>
      </div>
      <div class="trend-chart" ref="chartRef"></div>
    </div>
    
    <!-- Block B: Top Model表格 -->
    <div class="card-section">
      <div class="section-header">
        <div class="header-left">
          <h3 class="section-title"><el-icon><Medal /></el-icon>Top Model</h3>
          <div class="sort-group">
            <span class="sort-label">Top Model 排序</span>
            <el-radio-group v-model="topModelSortProxy" size="small">
              <el-radio-button value="claim">CLAIM</el-radio-button>
              <el-radio-button value="ra">RA</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="header-controls">
          <el-radio-group v-model="topModelTab" size="small">
            <el-radio-button value="summary">汇总</el-radio-button>
            <el-radio-button value="monthly">月度</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div v-if="topModelTab === 'summary'">
        <el-table :data="data.top_models" stripe style="width: 100%" size="small" max-height="400">
          <el-table-column prop="rank" label="排名" width="70" align="center">
            <template #default="{ row }"><el-tag :type="row.rank <= 3 ? 'danger' : row.rank <= 6 ? 'warning' : 'info'" size="small">#{{ row.rank }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="model" label="Model" min-width="120" />
          <el-table-column prop="ra" label="RA (DPPM)" width="120" :class-name="topModelSort === 'ra' ? 'sort-active' : ''"><template #default="{ row }">{{ formatDppm(row.ra) }}</template></el-table-column>
          <el-table-column prop="ra_claim" label="RA CLAIM" width="100" align="right" :class-name="topModelSort === 'claim' ? 'sort-active' : ''" />
          <el-table-column prop="ra_mm" label="RA MM" width="100" align="right" />
        </el-table>
      </div>
      <div v-else>
        <div class="month-selector">
          <el-select v-model="selectedMonth" placeholder="选择月份" size="small" style="width: 150px">
            <el-option v-for="item in monthlyTopModelMonths" :key="item" :label="item" :value="item" />
          </el-select>
        </div>
        <el-table :data="currentMonthlyTopModels" stripe style="width: 100%" size="small" max-height="400">
          <el-table-column prop="rank" label="排名" width="70" align="center">
            <template #default="{ row }"><el-tag :type="row.rank <= 3 ? 'danger' : row.rank <= 6 ? 'warning' : 'info'" size="small">#{{ row.rank }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="model" label="Model" min-width="120" />
          <el-table-column prop="ra" label="RA (DPPM)" width="120" :class-name="topModelSort === 'ra' ? 'sort-active' : ''"><template #default="{ row }">{{ formatDppm(row.ra) }}</template></el-table-column>
          <el-table-column prop="ra_claim" label="RA CLAIM" width="100" align="right" :class-name="topModelSort === 'claim' ? 'sort-active' : ''" />
          <el-table-column prop="ra_mm" label="RA MM" width="100" align="right" />
        </el-table>
      </div>
    </div>
    
    <!-- Block C: AI总结 -->
    <div class="card-section">
      <div class="ai-summary">
        <div class="summary-title">
          <el-icon><MagicStick /></el-icon>
          AI 分析总结
        </div>
        <div class="summary-content">
          {{ data.ai_summary || '暂无AI分析（后续版本支持）' }}
        </div>
      </div>
    </div>
    
    <!-- 点击详情弹窗 -->
    <el-dialog v-model="detailVisible" title="数据详情" width="300px" :close-on-click-modal="true">
      <div class="detail-content">
        <p><strong>月份：</strong>{{ detailData.month }}</p>
        <p><strong>DPPM：</strong>{{ formatDppm(detailData.value) }}</p>
        <p><strong>百分比：</strong>{{ formatPercent(detailData.value) }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { OfficeBuilding, TrendCharts, Medal, MagicStick } from '@element-plus/icons-vue'
import type { OdmCard as OdmCardData } from '@/api/ra'

type TopSort = 'claim' | 'ra'

const props = defineProps<{
  odm: string
  data: OdmCardData
  topModelSort: TopSort
}>()

const emit = defineEmits<{
  (e: 'update:topModelSort', value: TopSort): void
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
const chartMode = ref<'yearly' | 'timeline'>('timeline')
const detailVisible = ref(false)
const detailData = ref({ month: '', value: 0 })

// Top Model Tab切换
const topModelTab = ref<'summary' | 'monthly'>('summary')
const topModelSortProxy = computed({
  get: () => props.topModelSort,
  set: (value: TopSort) => emit('update:topModelSort', value)
})
const selectedMonth = ref('')
const monthlyTopModelMonths = computed(() => (props.data.monthly_top_models ?? [])
  .map(m => m.month)
  .filter((month): month is string => !!month))
const currentMonthlyTopModels = computed(() => {
  if (!selectedMonth.value || !props.data.monthly_top_models) return []
  return props.data.monthly_top_models.find(m => m.month === selectedMonth.value)?.items || []
})
watch(monthlyTopModelMonths, (months) => {
  const latest = months[months.length - 1]
  if (latest && !selectedMonth.value) selectedMonth.value = latest
}, { immediate: true })

const yearColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#00d4ff', '#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3']

const latestMonth = computed(() => {
  const last = props.data.trend?.[props.data.trend.length - 1]
  return last?.month ?? '-'
})

const formatDppm = (value: number) => {
  if (value === null || value === undefined) return '-'
  return Math.round(value * 1000000).toLocaleString()
}

const formatPercent = (value: number) => {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(4)}%`
}

const getYearlyData = () => {
  const yearMap: Record<string, { month: string; ra: number }[]> = {}
  props.data.trend?.forEach(item => {
    if (!item.month) return
    const [year, month] = item.month.split('-')
    if (!year || !month) return
    if (!yearMap[year]) yearMap[year] = []
    yearMap[year].push({ month, ra: item.ra })
  })
  return yearMap
}

const getYearlyOption = (): echarts.EChartsOption => {
  const yearlyData = getYearlyData()
  const years = Object.keys(yearlyData).sort()
  const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
  
  const series: echarts.SeriesOption[] = years.map((year, index) => ({
    name: year, type: 'line', smooth: true, symbol: 'circle', symbolSize: 6,
    lineStyle: { width: 2, color: yearColors[index % yearColors.length] },
    itemStyle: { color: yearColors[index % yearColors.length] },
    data: months.map(m => {
      const found = yearlyData[year]?.find(d => d.month === m)
      return found ? found.ra * 1000000 : null
    }),
    connectNulls: true
  }))
  
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((p: any) => {
          if (p.value !== null && p.value !== undefined) {
            result += `${p.marker}${p.seriesName}: ${Math.round(p.value).toLocaleString()} DPPM<br/>`
          }
        })
        return result
      }
    },
    legend: { data: years, top: 0, right: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: months.map(m => `${m}月`), axisLine: { lineStyle: { color: '#e4e7ed' } }, axisLabel: { color: '#606266' } },
    yAxis: { type: 'value', name: 'DPPM', axisLabel: { formatter: (value: number) => value.toLocaleString(), color: '#606266' }, splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } } },
    series
  }
}

const getTimelineOption = (): echarts.EChartsOption => {
  const trendData = props.data.trend || []
  return {
    tooltip: { trigger: 'axis', formatter: (params: any) => `${params[0].name}<br/>RA: ${Math.round(params[0].value).toLocaleString()} DPPM` },
    grid: { left: '3%', right: '4%', bottom: trendData.length > 12 ? '60px' : '3%', top: '10%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: trendData.map(item => item.month), axisLine: { lineStyle: { color: '#e4e7ed' } }, axisLabel: { color: '#606266', rotate: trendData.length > 12 ? 45 : 0 } },
    yAxis: { type: 'value', name: 'DPPM', axisLabel: { formatter: (value: number) => value.toLocaleString(), color: '#606266' }, splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } } },
    dataZoom: trendData.length > 12 ? [
      { type: 'slider', show: true, start: Math.max(0, 100 - (12 / trendData.length) * 100), end: 100, height: 20, bottom: 10 },
      { type: 'inside', start: Math.max(0, 100 - (12 / trendData.length) * 100), end: 100 }
    ] : undefined,
    series: [{
      name: 'RA', type: 'line', smooth: true, symbol: 'circle', symbolSize: 8,
      lineStyle: { width: 3, color: '#409eff' }, itemStyle: { color: '#409eff' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(64, 158, 255, 0.3)' }, { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }]) },
      data: trendData.map(item => item.ra * 1000000)
    }]
  }
}

const initChart = () => {
  if (!chartRef.value || !props.data.trend) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(chartMode.value === 'yearly' ? getYearlyOption() : getTimelineOption())
  
  chartInstance.off('click')
  chartInstance.on('click', (params: any) => {
    if (params.componentType === 'series') {
      const month = chartMode.value === 'yearly' ? `${params.seriesName}-${params.name.replace('月', '')}` : params.name
      detailData.value = { month, value: params.value / 1000000 }
      detailVisible.value = true
    }
  })
}

onMounted(() => initChart())
onActivated(() => chartInstance?.resize())
watch(() => props.data, () => initChart(), { deep: true })
window.addEventListener('resize', () => chartInstance?.resize())
</script>

<style scoped lang="scss">
.ra-odm-card { background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: linear-gradient(135deg, #409eff 0%, #337ecc 100%); color: #fff;
  .card-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 500; }
  .card-meta { :deep(.el-tag) { background: rgba(255, 255, 255, 0.2); border: none; color: #fff; } }
}
.card-section { padding: 20px; border-bottom: 1px solid var(--border-color);
  &:last-child { border-bottom: none; }
  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .header-left { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  .sort-group { display: inline-flex; align-items: center; gap: 8px; }
  .header-controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .sort-label { font-size: 12px; color: var(--text-color-secondary); }
  .section-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 500; color: var(--text-color); margin: 0; .el-icon { color: var(--primary-color); } }
}
.trend-chart { height: 300px; width: 100%; }
.ai-summary {
  .summary-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 500; color: var(--text-color); margin-bottom: 12px; .el-icon { color: #e6a23c; } }
  .summary-content { padding: 16px; background: #ecf5ff; border-radius: 8px; color: #666; line-height: 1.8; font-size: 14px; }
}
.detail-content { p { margin: 12px 0; font-size: 14px; } }
.month-selector { margin-bottom: 12px; }
:deep(th.sort-active) { background: #f3f8ff; }
:deep(td.sort-active) { background: #f9fbff; }
:deep(.sort-active .cell) { font-weight: 600; color: #409eff; }
</style>
