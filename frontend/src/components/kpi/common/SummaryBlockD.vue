<template>
  <div class="block-d" v-if="showBlockD">
    <div class="block-d-header">
      <h3 class="block-d-title">
        <el-icon><DataAnalysis /></el-icon>
        多{{ entityLabel }}对比汇总
      </h3>
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button value="summary">汇总趋势</el-radio-button>
        <el-radio-button value="monthly">单月饼图</el-radio-button>
      </el-radio-group>
    </div>
    
    <!-- 汇总视图：多线趋势图 + 数据矩阵表 -->
    <div v-if="viewMode === 'summary'" class="summary-view">
      <!-- 多线趋势图 -->
      <div class="trend-chart" ref="trendChartRef"></div>
      
      <!-- 数据矩阵表 -->
      <div class="data-matrix">
        <el-table :data="matrixData" stripe size="small" max-height="300" border>
          <el-table-column :prop="entityKey" :label="entityLabel" width="120" fixed />
          <el-table-column 
            v-for="month in months" 
            :key="month" 
            :label="month"
            width="100"
            align="center"
          >
            <template #default="{ row }">
              <span 
                class="cell-value"
                :class="getCellClass(row[month])"
              >
                {{ formatDppm(row[month]) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    
    <!-- 单月视图：月份选择 + 饼图 -->
    <div v-else class="monthly-view">
      <div class="month-selector">
        <span class="label">选择月份：</span>
        <el-select v-model="selectedMonth" placeholder="选择月份" size="small" style="width: 150px">
          <el-option v-for="m in months" :key="m" :label="m" :value="m" />
        </el-select>
      </div>
      <div class="pie-chart" ref="pieChartRef"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { DataAnalysis } from '@element-plus/icons-vue'

// Props 定义
interface TrendItem {
  month: string
  value: number  // IFIR 或 RA (小数形式)
}

interface EntityTrend {
  name: string  // ODM/Segment/Model 名称
  trend: TrendItem[]
}

interface PieItem {
  name: string
  value: number  // IFIR 或 RA (小数形式)
  share: number
}

const props = withDefaults(defineProps<{
  entityLabel: string  // "ODM" | "Segment" | "Model"
  entityKey: string    // "odm" | "segment" | "model"
  entities: EntityTrend[]  // 各实体的趋势数据
  pieData?: PieItem[]   // 饼图数据（汇总占比）
  tgt?: number          // 目标值 (DPPM)
  valueLabel?: string   // "IFIR" | "RA"
}>(), {
  tgt: 1500,
  valueLabel: 'IFIR'
})

// 视图模式
const viewMode = ref<'summary' | 'monthly'>('summary')
const selectedMonth = ref('')

// 图表引用
const trendChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

// 是否显示 Block D（仅多选时显示）
const showBlockD = computed(() => props.entities.length > 1)

// 所有月份
const months = computed(() => {
  if (props.entities.length === 0) return []
  const allMonths = new Set<string>()
  props.entities.forEach(e => {
    e.trend.forEach(t => {
      if (t.month) allMonths.add(t.month)
    })
  })
  return Array.from(allMonths).sort()
})

// 矩阵数据
const matrixData = computed(() => {
  const data: any[] = []
  props.entities.forEach(entity => {
    const row: any = { [props.entityKey]: entity.name }
    entity.trend.forEach(t => {
      if (!t.month) return
      row[t.month] = t.value
    })
    data.push(row)
  })
  
  // 添加 Total 行（平均值）
  if (data.length > 0) {
    const totalRow: any = { [props.entityKey]: 'Average' }
    months.value.forEach(month => {
      const values = data.map(r => r[month]).filter(v => v !== undefined && v !== null)
      if (values.length > 0) {
        totalRow[month] = values.reduce((a, b) => a + b, 0) / values.length
      }
    })
    data.push(totalRow)
  }
  
  return data
})

// 格式化 DPPM
const formatDppm = (value: number) => {
  if (value === null || value === undefined) return '-'
  return Math.round(value * 1000000).toLocaleString()
}

// 获取单元格样式类
const getCellClass = (value: number) => {
  if (value === null || value === undefined) return ''
  const dppmValue = value * 1000000
  if (dppmValue > props.tgt) return 'over-tgt'
  return 'meet-tgt'
}

// 颜色配置
const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ff9f7f']

// 初始化趋势图
const initTrendChart = () => {
  if (!trendChartRef.value || !showBlockD.value) return
  
  if (trendChart) trendChart.dispose()
  trendChart = echarts.init(trendChartRef.value)
  
  // 构建系列数据
  const series: echarts.SeriesOption[] = props.entities.map((entity, index) => ({
    name: entity.name,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 2, color: colors[index % colors.length] },
    itemStyle: { color: colors[index % colors.length] },
    data: months.value.map(m => {
      const point = entity.trend.find(t => t.month === m)
      return point ? point.value * 1000000 : null
    }),
    connectNulls: true
  }))
  
  // 添加平均线
  const avgData = months.value.map(m => {
    const values = props.entities
      .map(e => e.trend.find(t => t.month === m)?.value)
      .filter(v => v !== undefined && v !== null) as number[]
    if (values.length === 0) return null
    return (values.reduce((a, b) => a + b, 0) / values.length) * 1000000
  })
  
  series.push({
    name: 'Average',
    type: 'line',
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 2, type: 'dashed', color: '#666' },
    data: avgData
  })
  
  // 添加 TGT 目标线
  series.push({
    name: 'TGT',
    type: 'line',
    symbol: 'none',
    lineStyle: { width: 2, color: '#f56c6c' },
    data: months.value.map(() => props.tgt),
    markLine: {
      silent: true,
      symbol: 'none',
      data: [{ yAxis: props.tgt, lineStyle: { color: '#f56c6c', width: 2 } }]
    }
  })
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((p: any) => {
          if (p.value !== null && p.value !== undefined) {
            const color = p.seriesName === 'TGT' ? '#f56c6c' : (p.seriesName === 'Average' ? '#666' : p.color)
            result += `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};margin-right:4px;"></span>`
            result += `${p.seriesName}: ${Math.round(p.value).toLocaleString()} DPPM<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: [...props.entities.map(e => e.name), 'Average', 'TGT'],
      top: 0,
      right: 0,
      textStyle: { fontSize: 12 }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '50px', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months.value,
      axisLine: { lineStyle: { color: '#e4e7ed' } },
      axisLabel: { color: '#606266', rotate: months.value.length > 8 ? 45 : 0 }
    },
    yAxis: {
      type: 'value',
      name: 'DPPM',
      axisLabel: { formatter: (v: number) => v.toLocaleString(), color: '#606266' },
      splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } }
    },
    series
  }
  
  trendChart.setOption(option)
}

// 初始化饼图
const initPieChart = () => {
  if (!pieChartRef.value || !showBlockD.value || !selectedMonth.value) return
  
  if (pieChart) pieChart.dispose()
  pieChart = echarts.init(pieChartRef.value)
  
  // 获取当月数据
  const monthData = props.entities.map((entity, index) => {
    const point = entity.trend.find(t => t.month === selectedMonth.value)
    return {
      name: entity.name,
      value: point ? point.value * 1000000 : 0,
      itemStyle: { color: colors[index % colors.length] }
    }
  }).filter(d => d.value > 0)
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}<br/>${props.valueLabel}: ${Math.round(params.value).toLocaleString()} DPPM<br/>占比: ${params.percent.toFixed(1)}%`
      }
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {d}%'
      },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' }
      },
      data: monthData
    }]
  }
  
  pieChart.setOption(option)
}

// 监听数据变化
watch(() => props.entities, () => {
  nextTick(() => {
    if (viewMode.value === 'summary') {
      initTrendChart()
    } else {
      initPieChart()
    }
  })
}, { deep: true })

// 监听视图模式变化
watch(viewMode, (mode) => {
  nextTick(() => {
    if (mode === 'summary') {
      initTrendChart()
    } else {
      const latest = months.value[months.value.length - 1]
      if (latest && !selectedMonth.value) {
        selectedMonth.value = latest
      }
      initPieChart()
    }
  })
})

// 监听月份选择变化
watch(selectedMonth, () => {
  if (viewMode.value === 'monthly') {
    nextTick(() => initPieChart())
  }
})

// 监听 TGT 变化
watch(() => props.tgt, () => {
  if (viewMode.value === 'summary') {
    nextTick(() => initTrendChart())
  }
})

// 初始化
onMounted(() => {
  if (showBlockD.value) {
    const latest = months.value[months.value.length - 1]
    if (latest) {
      selectedMonth.value = latest
    }
    nextTick(() => initTrendChart())
  }
})

// 窗口大小调整
window.addEventListener('resize', () => {
  trendChart?.resize()
  pieChart?.resize()
})
</script>

<style scoped lang="scss">
.block-d {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.block-d-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.block-d-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color);
  margin: 0;
  
  .el-icon {
    color: var(--primary-color);
  }
}

.summary-view {
  .trend-chart {
    height: 350px;
    width: 100%;
    margin-bottom: 20px;
  }
  
  .data-matrix {
    :deep(.cell-value) {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 13px;
      font-weight: 500;
      
      &.over-tgt {
        background: #fef0f0;
        color: #f56c6c;
      }
      
      &.meet-tgt {
        background: #f0f9eb;
        color: #67c23a;
      }
    }
  }
}

.monthly-view {
  .month-selector {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    
    .label {
      font-size: 14px;
      color: var(--text-color-secondary);
    }
  }
  
  .pie-chart {
    height: 350px;
    width: 100%;
  }
}
</style>
