<template>
  <div class="page-container">
    <div class="page-header">
      <h1>RA ODM分析</h1>
      <p class="description">按ODM维度分析RA表现与趋势（按索赔月统计）</p>
    </div>
    
    <!-- 筛选区 -->
    <div class="filter-panel">
      <div class="filter-row">
        <div class="filter-item">
          <span class="filter-label">时间范围（索赔月）</span>
          <el-date-picker
            v-model="dateRange"
            type="monthrange"
            range-separator="至"
            start-placeholder="开始月份"
            end-placeholder="结束月份"
            format="YYYY-MM"
            value-format="YYYY-MM"
            :disabled-date="disabledDate"
          />
        </div>
        
        <div class="filter-item">
          <span class="filter-label">ODM <el-tag size="small" type="danger">必选</el-tag></span>
          <el-select
            v-model="selectedOdms"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择ODM"
            style="width: 240px"
            :loading="optionsLoading"
          >
            <el-option
              v-for="item in odmOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </div>
        
        <div class="filter-item">
          <span class="filter-label">Segment</span>
          <el-select
            v-model="selectedSegments"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="全部"
            style="width: 200px"
            :loading="optionsLoading"
          >
            <el-option
              v-for="item in segmentOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </div>
        
        <div class="filter-item">
          <span class="filter-label">TGT目标 (DPPM)</span>
          <el-input-number
            v-model="tgtValue"
            :min="0"
            :max="100000"
            :step="100"
            style="width: 140px"
            controls-position="right"
          />
        </div>
        
        <div class="filter-item" style="margin-left: auto;">
          <span class="filter-label">&nbsp;</span>
          <el-button 
            type="primary" 
            :icon="Search"
            :disabled="selectedOdms.length === 0"
            :loading="analyzing"
            @click="handleAnalyze"
          >
            分析
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div class="result-area" v-if="analyzing">
      <div class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>正在分析数据，请稍候...</p>
      </div>
    </div>
    
    <!-- 结果区 -->
    <div class="result-area" v-else-if="showResult && analyzeResult">
      <!-- Block D: 多ODM汇总对比 -->
      <SummaryBlockD
        v-if="blockDEntities.length > 1"
        entity-label="ODM"
        entity-key="odm"
        :entities="blockDEntities"
        :tgt="tgtValue"
        value-label="RA"
      />
      
      <div class="selector-bar">
        <div 
          v-for="(card, index) in analyzeResult.cards" 
          :key="card.odm"
          class="selector-item"
          :class="{ active: activeIndex === index }"
          @click="activeIndex = index"
        >
          {{ card.odm }}
        </div>
      </div>
      
      <div class="carousel-container">
        <div 
          class="carousel-wrapper"
          :style="{ transform: `translateX(-${activeIndex * 100}%)` }"
        >
          <div 
            v-for="card in analyzeResult.cards" 
            :key="card.odm"
            class="carousel-item"
          >
            <RaOdmCard :odm="card.odm" :data="card" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空态 -->
    <div class="result-area" v-else>
      <div class="empty-state">
        <el-icon><TrendCharts /></el-icon>
        <p class="empty-text">请选择ODM并点击分析按钮</p>
        <p class="empty-hint" v-if="!hasData">
          提示：请先在"数据上传"页面上传数据
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { Search, TrendCharts, Loading } from '@element-plus/icons-vue'
import RaOdmCard from '@/components/kpi/ra/odm/RaOdmCard.vue'
import SummaryBlockD from '@/components/kpi/common/SummaryBlockD.vue'
import { getRaOptions, analyzeRaOdm, type RaOptions, type OdmAnalyzeResponse } from '@/api/ra'
import { ElMessage } from 'element-plus'

// 筛选条件
const dateRange = ref<[string, string] | null>(null)
const selectedOdms = ref<string[]>([])
const selectedSegments = ref<string[]>([])
const tgtValue = ref(1500) // TGT 目标值 (DPPM)

// 选项数据
const optionsLoading = ref(false)
const options = ref<RaOptions | null>(null)

// 计算选项
const odmOptions = computed(() => options.value?.odms || [])
const segmentOptions = computed(() => options.value?.segments || [])
const hasData = computed(() => odmOptions.value.length > 0)

// 分析状态
const analyzing = ref(false)
const showResult = ref(false)
const activeIndex = ref(0)
const analyzeResult = ref<OdmAnalyzeResponse | null>(null)

// Block D 数据：转换为趋势对比格式
const blockDEntities = computed(() => {
  if (!analyzeResult.value?.cards) return []
  return analyzeResult.value.cards.map(card => ({
    name: card.odm,
    trend: card.trend.map(t => ({
      month: t.month,
      value: t.ra
    }))
  }))
})

// 是否正在进行级联刷新
const isRefreshing = ref(false)

// 禁用日期
const disabledDate = (date: Date) => {
  if (!options.value?.time_range) return false
  const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
  return month < options.value.time_range.min_month || month > options.value.time_range.max_month
}

// 加载筛选选项（支持级联过滤）
const loadOptions = async (setDefaultTime = false) => {
  optionsLoading.value = true
  try {
    const result = await getRaOptions({
      segments: selectedSegments.value.length > 0 ? selectedSegments.value : undefined,
      odms: selectedOdms.value.length > 0 ? selectedOdms.value : undefined,
    })
    options.value = result
    
    // 清除无效的已选项
    if (!isRefreshing.value) {
      isRefreshing.value = true
      selectedOdms.value = selectedOdms.value.filter(v => result.odms.includes(v))
      selectedSegments.value = selectedSegments.value.filter(v => result.segments.includes(v))
      // 等待 watch 触发完成后再重置标志
      await nextTick()
      isRefreshing.value = false
    }
    
    // 设置默认时间范围（仅首次加载）
    if (setDefaultTime && result.time_range && !dateRange.value) {
      const endMonth = result.time_range.max_month
      const endDate = new Date(endMonth + '-01')
      const startDate = new Date(endDate)
      startDate.setMonth(startDate.getMonth() - 5)
      const startMonth = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}`
      const actualStart = startMonth < result.time_range.min_month ? result.time_range.min_month : startMonth
      dateRange.value = [actualStart, endMonth]
    }
  } catch (error) {
    console.error('加载选项失败:', error)
  } finally {
    optionsLoading.value = false
  }
}

// 监听筛选条件变化，刷新其他选项
watch([selectedSegments, selectedOdms], () => {
  if (!isRefreshing.value) {
    loadOptions()
  }
}, { deep: true })

// 分析
const handleAnalyze = async () => {
  if (selectedOdms.value.length === 0) {
    ElMessage.warning('请选择至少一个ODM')
    return
  }
  
  if (!dateRange.value) {
    ElMessage.warning('请选择时间范围')
    return
  }
  
  analyzing.value = true
  showResult.value = false
  
  try {
    const result = await analyzeRaOdm({
      start_month: dateRange.value[0],
      end_month: dateRange.value[1],
      odms: selectedOdms.value,
      segments: selectedSegments.value.length > 0 ? selectedSegments.value : undefined,
    })
    
    analyzeResult.value = result
    showResult.value = true
    activeIndex.value = 0
    
    if (result.cards.length === 0) {
      ElMessage.warning('未查询到符合条件的数据')
    }
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败，请重试')
  } finally {
    analyzing.value = false
  }
}

onMounted(() => {
  loadOptions(true)
})
</script>

<style scoped lang="scss">
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--text-color-secondary);
  
  .el-icon {
    font-size: 48px;
    color: #67c23a;
    margin-bottom: 16px;
  }
  
  p {
    font-size: 14px;
  }
}

.empty-hint {
  font-size: 12px;
  color: var(--text-color-placeholder);
  margin-top: 8px;
}

.carousel-container {
  overflow: hidden;
  margin-top: 20px;
}

.carousel-wrapper {
  display: flex;
  transition: transform 0.3s ease;
}

.carousel-item {
  flex-shrink: 0;
  width: 100%;
}
</style>
