# KPI Visual Website 功能汇总

本文基于代码现状整理，覆盖前端、后端、数据模型、ETL与辅助脚本。内容以“功能视角”展开，尽量细化到页面、接口、图表、字段、交互与处理逻辑。

**项目定位**
- 面向 KPI 可视化分析的前后端一体项目，核心指标包含 IFIR 与 RA。
- 主要功能链路：Excel 数据上传 → 后端 ETL 入库 → 前端筛选分析 → 图表与表格呈现。

**技术栈概览**
- 前端：Vue 3 + Vite + TypeScript + Element Plus + ECharts。
- 后端：FastAPI + SQLAlchemy + MySQL + Pandas。

---

**一、前端功能（UI 与交互）**

**1. 全局布局与导航**
- 顶层布局为“侧边栏 + 顶部栏 + 内容区”结构，路径：`frontend/src/components/layout/MainLayout.vue`。
- 顶部栏包含：侧边栏折叠按钮、面包屑导航、应用标题显示，路径：`frontend/src/components/layout/AppHeader.vue`。
- 侧边栏包含：数据上传、IFIR 分析（ODM/Segment/Model）、RA 分析（ODM/Segment/Model）菜单与图标，支持折叠，路径：`frontend/src/components/layout/AppSidebar.vue`。
- 路由结构：`/upload`、`/kpi/ifir/*`、`/kpi/ra/*`，路径：`frontend/src/router/index.ts`。

**2. 全局样式与布局约定**
- 全局样式变量、页面容器、筛选面板、结果区、空态提示、卡片样式、滚动条等统一定义，路径：`frontend/src/styles/index.scss`。
- 统一的页面结构：`page-container`、`page-header`、`filter-panel`、`result-area`、`empty-state` 等。

**3. 前端 API 访问与错误处理**
- Axios 实例统一封装，基地址来自 `VITE_API_BASE_URL`，未配置则回退 `/api`，路径：`frontend/src/api/index.ts`。
- 响应拦截逻辑：要求后端返回 `{ code, message, data }`，`code !== 0` 时直接弹窗报错并 reject。
- 错误提示：统一使用 `Element Plus` 消息提示。

---

**二、前端页面功能（业务页面细化）**

**1. 数据上传页面**
- 页面路径：`/upload`，文件：`frontend/src/pages/upload/UploadPage.vue`。
- 支持上传 4 类 Excel 文件：`IFIR Detail`、`IFIR Row`、`RA Detail`、`RA Row`。
- 上传交互：拖拽或点击选择，每类文件单文件限制，仅需至少上传 1 个文件。
- 上传状态展示：
- 单文件状态（pending / processing / completed / failed）。
- 处理行数显示（rows）。
- 全局进度条显示（task.progress）。
- 成功与失败提示块（Alert）。
- 后端交互：
- 上传接口：`POST /api/upload`。
- 任务状态接口：`GET /api/upload/{taskId}/status`。
- 轮询机制：每 1 秒轮询状态直到完成或失败。

**2. IFIR - ODM 分析页面**
- 页面路径：`/kpi/ifir/odm-analysis`，文件：`frontend/src/pages/ifir/OdmAnalysisPage.vue`。
- 筛选项：
- 时间范围（monthrange，禁用不在后端范围内的月份）。
- ODM（必选，多选）。
- Segment（可选，多选）。
- Model（可选，多选）。
- TGT 目标值（DPPM，数值输入）。
- 联动筛选：选择条件变化时自动刷新其它可选项（级联过滤）。
- 分析执行：点击“分析”按钮请求后端，展示结果或空态。
- 结果展示：
- Block D 汇总对比（多 ODM 时显示）。
- ODM 选择条（横向可切换不同 ODM 卡片）。
- 卡片轮播展示 ODM 详情。

**3. IFIR - Segment 分析页面**
- 页面路径：`/kpi/ifir/segment-analysis`，文件：`frontend/src/pages/ifir/SegmentAnalysisPage.vue`。
- 筛选项：
- 时间范围（monthrange）。
- Segment（必选，多选）。
- ODM（可选，多选）。
- Model（可选，多选）。
- TGT 目标值（DPPM）。
- Top 排序方式：Top ODM Sort / Top Model Sort（按 claim 或 IFIR）。
- 分析执行：切换 Top Sort 会自动重新分析。
- 结果展示：
- Block D 汇总对比（多 Segment 时显示）。
- Segment 选择条与卡片轮播。

**4. IFIR - Model 分析页面**
- 页面路径：`/kpi/ifir/model-analysis`，文件：`frontend/src/pages/ifir/ModelAnalysisPage.vue`。
- 筛选项：
- 时间范围（monthrange）。
- 趋势窗口（6/12/18/24 个月）。
- Segment（可选，多选）。
- ODM（可选，多选）。
- Model（必选，多选）。
- TGT 目标值（DPPM）。
- 结果展示：
- Block D 汇总对比（多 Model 时显示）。
- Model 选择条与卡片轮播。

**5. RA - ODM 分析页面**
- 页面路径：`/kpi/ra/odm-analysis`，文件：`frontend/src/pages/ra/OdmAnalysisPage.vue`。
- 筛选项：
- 时间范围（Claim 月份）。
- ODM（必选，多选）。
- Segment（可选，多选）。
- TGT 目标值（DPPM）。
- 结果展示：
- Block D 汇总对比（多 ODM 时显示）。
- ODM 选择条与卡片轮播。

**6. RA - Segment 分析页面**
- 页面路径：`/kpi/ra/segment-analysis`，文件：`frontend/src/pages/ra/SegmentAnalysisPage.vue`。
- 筛选项：
- 时间范围（Claim 月份）。
- Segment（必选，多选）。
- ODM（可选，多选）。
- TGT 目标值（DPPM）。
- 结果展示：
- Block D 汇总对比（多 Segment 时显示）。
- Segment 选择条与卡片轮播。

**7. RA - Model 分析页面**
- 页面路径：`/kpi/ra/model-analysis`，文件：`frontend/src/pages/ra/ModelAnalysisPage.vue`。
- 筛选项：
- 时间范围（Claim 月份）。
- 趋势窗口（6/12/18/24 个月）。
- Segment（可选，多选）。
- ODM（可选，多选）。
- Model（必选，多选）。
- TGT 目标值（DPPM）。
- 结果展示：
- Block D 汇总对比（多 Model 时显示）。
- Model 选择条与卡片轮播。

---

**三、前端组件功能（图表与卡片细化）**

**1. SummaryBlockD（通用汇总组件）**
- 文件：`frontend/src/components/kpi/common/SummaryBlockD.vue`。
- 展示条件：实体数量 > 1 才显示（多 ODM/Segment/Model 比较）。
- 支持模式：
- Summary：多实体折线趋势图 + 数据矩阵表格。
- Monthly：单月饼图（按所选月份）。
- 图表细节：
- ECharts 多折线，附加 Average 平均线与 TGT 目标线。
- 纵轴单位为 DPPM（数值 * 1,000,000）。
- 可视化颜色组自动分配。
- 数据矩阵：
- 行为实体（ODM/Segment/Model），列为月份。
- 自动增加 Average 行（各实体平均）。
- 单元格按是否超过 TGT 着色。

**2. IFIR - ODM Card**
- 文件：`frontend/src/components/kpi/ifir/odm/OdmCard.vue`。
- 功能块：
- Block A：趋势图（年度对比 / 全量时间线切换）。
- Block B：Top Model 列表（Summary / Monthly 切换）。
- Block C：AI 总结占位文本。
- 交互细节：
- 点击趋势图点位可弹出月度详情对话框。
- Top Issue 可点击打开 Issue 明细弹窗。
- Issue 明细支持分页与页大小调整。

**3. IFIR - Segment Card**
- 文件：`frontend/src/components/kpi/ifir/segment/SegmentCard.vue`。
- 功能块：
- Block A：趋势图（年度对比 / 时间线）。
- Block B：Top ODM（Summary / Monthly，支持排序切换：CLAIM / IFIR）。
- Block C：Top Model（Summary / Monthly，支持排序切换：CLAIM / IFIR）。
- Block D：AI 总结占位文本。
- 交互细节：
- Top Issue 链接可打开 Issue 明细弹窗（与 IFIR ODM 类似）。
- 父页面控制排序方式，通过 v-model 双向绑定。

**4. IFIR - Model Card**
- 文件：`frontend/src/components/kpi/ifir/model/ModelCard.vue`。
- 功能块：
- Block A：趋势图（年度对比 / 时间线）。
- Block B：Top Issue（Summary / Monthly）。
- Block C：AI 总结占位文本。
- 交互细节：
- 点击 Issue 触发明细弹窗。
- 明细支持分页与页大小切换。

**5. RA - ODM Card**
- 文件：`frontend/src/components/kpi/ra/odm/RaOdmCard.vue`。
- 功能块：
- Block A：RA 趋势图（年度 / 时间线）。
- Block B：Top Model（Summary / Monthly）。
- Block C：AI 总结占位文本。
- 交互细节：趋势图点位弹窗显示 DPPM 明细。

**6. RA - Segment Card**
- 文件：`frontend/src/components/kpi/ra/segment/RaSegmentCard.vue`。
- 功能块：
- Block A：RA 趋势图（年度 / 时间线）。
- Block B：Top ODM（Summary / Monthly）。
- Block C：Top Model（Summary / Monthly）。
- Block D：AI 总结占位文本。
- 交互细节：趋势图点位弹窗显示 DPPM 明细。

**7. RA - Model Card**
- 文件：`frontend/src/components/kpi/ra/model/RaModelCard.vue`。
- 功能块：
- Block A：RA 趋势图（年度 / 时间线）。
- Block B：Top Issue（Summary / Monthly）。
- Block C：AI 总结占位文本。
- 交互细节：趋势图点位弹窗显示 DPPM 明细。

---

**四、后端功能（API 与计算逻辑）**

**1. 服务入口与基础能力**
- FastAPI 应用入口：`backend/app/main.py`。
- CORS 配置：允许本地前端端口访问（3000/3001/3002/5173 等）。
- 基础接口：
- `GET /` 返回服务基本信息。
- `GET /health` 健康检查。

**2. IFIR 分析 API**
- 路由文件：`backend/app/api/ifir.py`。
- 选项接口：
- `GET /api/ifir/options`：返回可选 Segment/ODM/Model 与时间范围。
- 兼容接口：`/api/ifir/odm-analysis/options`、`/segment-analysis/options`、`/model-analysis/options`。
- 分析接口：
- `POST /api/ifir/odm-analysis/analyze`。
- `POST /api/ifir/segment-analysis/analyze`。
- `POST /api/ifir/model-analysis/analyze`。
- `POST /api/ifir/model-analysis/issue-details`：Issue 明细分页查询。
- 输入校验：odm/segment/model 必选项缺失时返回 `code=400`。

**3. RA 分析 API**
- 路由文件：`backend/app/api/ra.py`。
- 选项接口：
- `GET /api/ra/options`。
- 兼容接口：`/api/ra/odm-analysis/options`、`/segment-analysis/options`、`/model-analysis/options`。
- 分析接口：
- `POST /api/ra/odm-analysis/analyze`。
- `POST /api/ra/segment-analysis/analyze`。
- `POST /api/ra/model-analysis/analyze`。

**4. 上传与 ETL API**
- 路由文件：`backend/app/api/upload.py`。
- 上传接口：`POST /api/upload`，支持多文件同时上传（至少 1 个）。
- 状态接口：`GET /api/upload/{task_id}/status`。
- 任务处理：
- 保存文件到 `backend/uploads`。
- 创建 `upload_task` 记录，初始状态 `queued`。
- 后台线程执行 ETL，状态流转 `processing → completed/failed`。
- 任务失败时记录错误信息。

---

**五、后端业务逻辑（核心计算细化）**

**1. IFIR 计算逻辑**
- 服务文件：`backend/app/services/ifir_service.py`。
- 时间轴：`delivery_month`。
- Options 计算：
- 获取全局最小/最大月份。
- 依据当前筛选条件动态刷新 Segment、ODM、Model 选项。
- ODM 分析：
- Block D：多 ODM 时生成 ODM 饼图汇总（占比按 claim 计算）。
- Block A：ODM 趋势（按月聚合）。
- Block B：Top Model（按 IFIR 排序，附 Top Issue）。
- 月度 Top Model 明细。
- 通过 `map_odm_to_plant` 关联 plant 过滤 Issue。
- Segment 分析：
- Block D：多 Segment 饼图汇总。
- Block A：Segment 趋势。
- Block B：Top ODM 与 Top Model（均支持月度明细）。
- Top Model 携带 Top Issue。
- Model 分析：
- Block D：多 Model 饼图汇总。
- Block A：Model 趋势。
- Block B：Top Issue（按详情表统计）。
- 月度 Top Issue 明细。
- IFIR 值计算：`box_claim / box_mm`，保留 8 位小数。

**2. RA 计算逻辑**
- 服务文件：`backend/app/services/ra_service.py`。
- 时间轴：`claim_month`。
- Options 计算：与 IFIR 相同逻辑。
- ODM 分析：
- Block D：多 ODM 饼图汇总。
- Block A：ODM 趋势。
- Block B：Top Model（Summary / Monthly）。
- Segment 分析：
- Block D：多 Segment 饼图汇总。
- Block A：Segment 趋势。
- Block B：Top ODM 与 Top Model（Summary / Monthly）。
- Model 分析：
- Block D：多 Model 饼图汇总。
- Block A：Model 趋势。
- Block B：Top Issue（详情表统计，支持月度明细）。
- RA 值计算：`ra_claim / ra_mm`，保留 8 位小数。

**3. Issue 明细查询**
- IFIR：`/api/ifir/model-analysis/issue-details`。
- 输入包含：时间范围、model、issue、分页信息、可选 segment/odm。
- 输出包含：明细列表（fault_category、problem_descr_by_tech、claim_nbr、claim_month、plant 等）。

---

**六、数据模型（数据库功能）**

**1. fact_ifir_row（IFIR ROW）**
- 粒度：月度聚合，时间轴 `delivery_month`。
- 关键字段：`segment`、`model`、`supplier_new(ODM)`、`plant`、`box_claim`、`box_mm`。
- 唯一性：`content_hash` 用于去重。

**2. fact_ifir_detail（IFIR DETAIL）**
- 粒度：单条索赔事件，主键 `claim_nbr`。
- 关键字段：`delivery_month`、`segment`、`model`、`fault_category`、`problem_descr_by_tech`。

**3. fact_ra_row（RA ROW）**
- 粒度：月度聚合，时间轴 `claim_month`。
- 关键字段：`segment`、`model`、`supplier_new(ODM)`、`plant`、`ra_claim`、`ra_mm`。
- 唯一性：`content_hash` 用于去重。

**4. fact_ra_detail（RA DETAIL）**
- 粒度：单条索赔事件，主键 `claim_nbr`。
- 关键字段：`claim_month`、`segment`、`model`、`fault_category`。

**5. map_odm_to_plant（ODM → Plant）**
- 复合主键：`(kpi_type, supplier_new, plant)`。
- 来源：从 ROW 表刷新生成（或导入种子数据）。

**6. upload_task（上传任务）**
- 记录上传任务状态、进度、文件路径、行数、错误信息、开始/完成时间。

---

**七、ETL 与数据导入功能**

**1. 在线上传 ETL**
- 入口：`backend/app/services/etl_service.py`。
- 支持文件类型：IFIR ROW、IFIR DETAIL、RA ROW、RA DETAIL。
- 处理流程：
- Excel → DataFrame → 列映射 → 数据清洗 → 批量 upsert。
- IFIR/RA ROW 使用 content_hash 防重。
- DETAIL 使用 claim_nbr 主键防重。
- 自动刷新 `map_odm_to_plant`。

**2. 数据库初始化脚本**
- `scripts/db/init.sql`：建库建表、索引、注释。
- `scripts/db/seed_odm_mapping.sql`：预置 ODM-Plant 映射数据。

**3. 离线数据导入工具（backend 目录）**
- `backend/direct_import.py`：直接导入 IFIR/RA ROW（适合调试）。
- `backend/fast_import_detail.py`：批量导入 DETAIL（pandas to_sql）。
- `backend/import_detail_odm.py`：导入 DETAIL + ODM 映射。
- `backend/check_columns.py`：检查 Excel 列名并输出到 `column_check.txt`。
- `backend/rebuild_ra_detail.py`：重建 `fact_ra_detail` 表。

---

**八、测试与辅助脚本**

**1. API 测试**
- `Test/test_api.py`：
- 健康检查。
- 上传测试。
- 轮询任务状态。
- IFIR/RA Options 与分析 API 测试。

**2. 分析接口测试**
- `Test/test_analyze.py`：
- IFIR/RA ODM 分析请求示例与输出检查。

**3. 数据库与连通性测试**
- `Test/test_connection.py`：
- 数据库连接检查。
- API 基础连通检查。

---

**九、配置与运行相关能力**

- 后端配置：`backend/.env` 与 `env.example`。
- 数据库配置：`DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`。
- 前端配置：`VITE_API_BASE_URL`（已修正为 `/api`）。
- 本地启动指引：`docs/runbook/startup.md`、`docs/runbook/local-dev.md`。

---

**十、功能地图（端到端链路）**

- 上传链路：前端上传页面 → `POST /api/upload` → 后端保存文件与任务 → 线程 ETL → 更新任务状态 → 前端轮询展示结果。
- 分析链路：前端筛选 → `GET /api/*/options` 拉取动态选项 → `POST /api/*/analyze` 获取分析结果 → 卡片、图表、表格渲染。
- 明细链路：前端点击 Issue → `POST /api/ifir/model-analysis/issue-details` → 弹窗分页表格展示明细。
