-- ============================================================
-- KPI可视化系统 数据库初始化脚本
-- 版本: v1.0
-- 日期: 2026-01-26
-- 
-- 设计来源: plan/数据库/*.md
-- ============================================================

-- 创建数据库（如不存在）
CREATE DATABASE IF NOT EXISTS kpi_visual 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE kpi_visual;

-- ============================================================
-- 1. IFIR ROW 表（IFIR月度聚合事实表）
-- 来源: plan/数据库/fact_IFIR_row.md
-- 粒度: 出货月 × Model × ODM × Plant（无天然业务主键）
-- 策略: 自增id作为物理主键 + content_hash作为业务唯一键
-- ============================================================
DROP TABLE IF EXISTS fact_ifir_row;
CREATE TABLE fact_ifir_row (
  id BIGINT NOT NULL AUTO_INCREMENT,
  content_hash CHAR(32) NOT NULL COMMENT '行内容MD5哈希，用于幂等导入',

  -- 时间维度
  delivery_month DATE NULL COMMENT '出货月（月首日），IFIR的时间主轴',
  
  -- 产品与组织维度（全部14列落库）
  brand VARCHAR(32) NULL COMMENT '品牌',
  geo VARCHAR(16) NULL COMMENT '地区，例如PRC',
  product_line VARCHAR(32) NULL COMMENT '产品线',
  segment VARCHAR(64) NULL COMMENT '业务段',
  series VARCHAR(128) NULL COMMENT '系列',
  model VARCHAR(128) NULL COMMENT '机型',
  plant VARCHAR(64) NULL COMMENT '工厂',
  mach_type VARCHAR(64) NULL COMMENT '平台字段，当前不作为核心分析口径',
  supplier_new VARCHAR(128) NULL COMMENT 'ODM，空值统一转为None',

  -- KPI指标
  box_claim INT NOT NULL COMMENT 'IFIR分子，事件数',
  box_mm INT NOT NULL COMMENT 'IFIR分母，出货量',

  -- 溯源字段（不参与统计）
  year_ignore SMALLINT NULL COMMENT '年份溯源字段，不参与统计',
  month_ignore TINYINT NULL COMMENT '月份溯源字段，不参与统计',

  -- 元数据
  src_file VARCHAR(255) NULL COMMENT '来源文件名',
  etl_batch_id VARCHAR(64) NULL COMMENT 'ETL批次ID',
  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',

  PRIMARY KEY (id),
  UNIQUE KEY uk_content_hash (content_hash),

  -- 索引设计
  KEY idx_month_odm_model (delivery_month, supplier_new, model) COMMENT '支撑ODM层月→ODM→Model趋势',
  KEY idx_month_segment (delivery_month, segment) COMMENT '支撑Segment层趋势',
  KEY idx_odm_plant (supplier_new, plant) COMMENT '支撑ODM下钻时的工厂集合过滤',
  KEY idx_month_plant (delivery_month, plant) COMMENT '支撑按月按工厂去找明细入口'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='IFIR ROW月度聚合事实表';

-- ============================================================
-- 2. IFIR DETAIL 表（IFIR事件级明细表）
-- 来源: plan/数据库/fact_IFIR_detail.md
-- 粒度: 单条索赔事件
-- 策略: claim_nbr作为主键（入库前去重）
-- ============================================================
DROP TABLE IF EXISTS fact_ifir_detail;
CREATE TABLE fact_ifir_detail (
  -- 主键
  claim_nbr VARCHAR(64) NOT NULL COMMENT '索赔单号/事件号（主键）',

  -- A. 时间维度
  claim_month DATE NULL COMMENT '索赔归属月（月首日）',
  claim_date DATE NULL COMMENT '索赔/事件日期',
  delivery_month DATE NULL COMMENT '出货/交付月（月首日），IFIR下钻主时间轴',
  delivery_day TINYINT NULL COMMENT '出货日（1-31）',

  -- B. 区域与组织维度
  geo_2012 VARCHAR(32) NULL COMMENT '地理大区口径',
  financial_region VARCHAR(64) NULL COMMENT '财务口径区域',
  plant VARCHAR(64) NULL COMMENT '工厂/生产基地',

  -- C. 产品归属维度
  brand VARCHAR(64) NULL COMMENT '品牌',
  segment VARCHAR(64) NULL COMMENT '业务段',
  segment2 VARCHAR(64) NULL COMMENT '子业务段',
  style VARCHAR(64) NULL COMMENT '产品大类',
  series VARCHAR(128) NULL COMMENT '系列',
  model VARCHAR(128) NULL COMMENT '型号',
  mtm VARCHAR(64) NULL COMMENT 'MTM机型编码',
  serial_nbr VARCHAR(64) NULL COMMENT '序列号（同一SN可多次claim）',

  -- D. 制造/服务追溯维度
  stationname VARCHAR(255) NULL COMMENT '服务站名称',
  station_id INT NULL COMMENT '服务站ID（数值型）',
  data_source VARCHAR(32) NULL COMMENT '数据来源系统',
  lastsln TEXT NULL COMMENT '最后处理/解决信息（长文本）',

  -- E. 失效与问题描述维度（Issue）
  failure_code VARCHAR(32) NULL COMMENT '标准失效代码',
  fault_category VARCHAR(128) NULL COMMENT '故障大类',
  mach_desc VARCHAR(255) NULL COMMENT '机型描述（更详细）',
  problem_descr VARCHAR(255) NULL COMMENT '问题描述（报修侧）',
  problem_descr_by_tech VARCHAR(255) NULL COMMENT '技术员侧问题描述',

  -- F. 零部件与供应链维度
  commodity VARCHAR(64) NULL COMMENT '物料/系统归类',
  down_part_code VARCHAR(64) NULL COMMENT '下阶/失效部件代码',
  part_nbr VARCHAR(64) NULL COMMENT '部件号',
  part_desc VARCHAR(255) NULL COMMENT '部件描述',
  part_supplier VARCHAR(128) NULL COMMENT '供应商',
  part_barcode VARCHAR(64) NULL COMMENT '部件条码',
  packing_lot_no VARCHAR(64) NULL COMMENT '批次/包装批号',

  -- G. 索赔单与客户维度
  claim_item_nbr VARCHAR(64) NULL COMMENT '索赔行号',
  claim_status VARCHAR(32) NULL COMMENT '索赔状态',
  channel VARCHAR(32) NULL COMMENT '渠道',
  cust_nbr VARCHAR(64) NULL COMMENT '客户编号',

  -- 元数据
  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',

  PRIMARY KEY (claim_nbr),

  -- 索引设计
  KEY idx_delivery_month_plant (delivery_month, plant) COMMENT '下钻入口',
  KEY idx_delivery_month_model (delivery_month, model),
  KEY idx_segment_month (segment, delivery_month),
  KEY idx_issue (fault_category) COMMENT 'Top Issue聚合',
  KEY idx_part (part_nbr) COMMENT 'Top Part聚合'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='IFIR DETAIL事件级明细表';

-- ============================================================
-- 3. RA ROW 表（RA月度聚合事实表）
-- 来源: plan/数据库/fact_RA_row.md
-- 粒度: 索赔月 × Model × ODM × Plant（无天然业务主键）
-- 策略: 自增id + content_hash
-- 注意: RA时间主轴是claim_month，PLANT_OLD入库统一为plant
-- ============================================================
DROP TABLE IF EXISTS fact_ra_row;
CREATE TABLE fact_ra_row (
  id BIGINT NOT NULL AUTO_INCREMENT,
  content_hash CHAR(32) NOT NULL COMMENT '行内容MD5哈希，用于幂等导入',

  -- 时间维度
  claim_month DATE NULL COMMENT '索赔归属月（RA时间主轴）',
  
  -- 产品与组织维度（全部14列落库）
  brand VARCHAR(32) NULL COMMENT '品牌',
  geo VARCHAR(16) NULL COMMENT '地区',
  product_line VARCHAR(32) NULL COMMENT '产品线',
  segment VARCHAR(64) NULL COMMENT '业务段',
  series VARCHAR(128) NULL COMMENT '系列',
  model VARCHAR(128) NULL COMMENT '机型',
  plant VARCHAR(64) NULL COMMENT '工厂（源字段PLANT_OLD，统一为plant）',
  supplier_new VARCHAR(128) NULL COMMENT 'ODM（空值统一转为None）',
  mach_type VARCHAR(64) NULL COMMENT '平台字段（暂不作为分析口径）',

  -- KPI指标
  ra_claim INT NOT NULL COMMENT 'RA分子',
  ra_mm INT NOT NULL COMMENT 'RA分母',

  -- 溯源字段（不参与统计）
  year_ignore SMALLINT NULL COMMENT '年份溯源字段，不参与统计',
  month_ignore TINYINT NULL COMMENT '月份溯源字段，不参与统计',

  -- 元数据
  src_file VARCHAR(255) NULL COMMENT '来源文件名',
  etl_batch_id VARCHAR(64) NULL COMMENT 'ETL批次ID',
  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',

  PRIMARY KEY (id),
  UNIQUE KEY uk_content_hash (content_hash),

  -- 索引设计
  KEY idx_month_odm_model (claim_month, supplier_new, model),
  KEY idx_month_segment (claim_month, segment),
  KEY idx_odm_plant (supplier_new, plant),
  KEY idx_month_plant (claim_month, plant)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='RA ROW月度聚合事实表';

-- ============================================================
-- 4. RA DETAIL 表（RA事件级明细表）
-- 来源: 参考IFIR DETAIL结构，时间主轴为claim_month
-- 粒度: 单条维修事件
-- 策略: claim_nbr作为主键（入库前去重）
-- ============================================================
DROP TABLE IF EXISTS fact_ra_detail;
CREATE TABLE fact_ra_detail (
  -- 主键
  claim_nbr VARCHAR(64) NOT NULL COMMENT '索赔单号/事件号（主键）',

  -- A. 时间维度（RA的下钻主轴是claim_month）
  claim_month DATE NULL COMMENT '索赔归属月（RA下钻主时间轴）',
  claim_date DATE NULL COMMENT '索赔/事件日期',

  -- B. 区域与组织维度
  geo_2012 VARCHAR(32) NULL COMMENT '地理大区口径',
  financial_region VARCHAR(64) NULL COMMENT '财务口径区域',
  plant VARCHAR(64) NULL COMMENT '工厂/生产基地',

  -- C. 产品归属维度
  brand VARCHAR(64) NULL COMMENT '品牌',
  segment VARCHAR(64) NULL COMMENT '业务段',
  segment2 VARCHAR(64) NULL COMMENT '子业务段',
  style VARCHAR(64) NULL COMMENT '产品大类',
  series VARCHAR(128) NULL COMMENT '系列',
  model VARCHAR(128) NULL COMMENT '型号',
  mtm VARCHAR(64) NULL COMMENT 'MTM机型编码',
  serial_nbr VARCHAR(64) NULL COMMENT '序列号',

  -- D. 制造/服务追溯维度
  stationname VARCHAR(255) NULL COMMENT '服务站名称',
  station_id INT NULL COMMENT '服务站ID',
  data_source VARCHAR(32) NULL COMMENT '数据来源系统',
  lastsln TEXT NULL COMMENT '最后处理/解决信息',

  -- E. 失效与问题描述维度
  failure_code VARCHAR(32) NULL COMMENT '标准失效代码',
  fault_category VARCHAR(128) NULL COMMENT '故障大类',
  mach_desc VARCHAR(255) NULL COMMENT '机型描述',
  problem_descr VARCHAR(255) NULL COMMENT '问题描述（报修侧）',
  problem_descr_by_tech VARCHAR(255) NULL COMMENT '技术员侧问题描述',

  -- F. 零部件与供应链维度
  commodity VARCHAR(64) NULL COMMENT '物料/系统归类',
  down_part_code VARCHAR(64) NULL COMMENT '下阶/失效部件代码',
  part_nbr VARCHAR(64) NULL COMMENT '部件号',
  part_desc VARCHAR(255) NULL COMMENT '部件描述',
  part_supplier VARCHAR(128) NULL COMMENT '供应商',
  part_barcode VARCHAR(64) NULL COMMENT '部件条码',
  packing_lot_no VARCHAR(64) NULL COMMENT '批次/包装批号',

  -- G. 索赔单与客户维度
  claim_item_nbr VARCHAR(64) NULL COMMENT '索赔行号',
  claim_status VARCHAR(32) NULL COMMENT '索赔状态',
  channel VARCHAR(32) NULL COMMENT '渠道',
  cust_nbr VARCHAR(64) NULL COMMENT '客户编号',

  -- 元数据
  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',

  PRIMARY KEY (claim_nbr),

  -- 索引设计
  KEY idx_claim_month_plant (claim_month, plant) COMMENT '下钻入口',
  KEY idx_claim_month_model (claim_month, model),
  KEY idx_segment_month (segment, claim_month),
  KEY idx_issue (fault_category),
  KEY idx_part (part_nbr)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='RA DETAIL事件级明细表';

-- ============================================================
-- 5. ODM到PLANT映射表
-- 来源: plan/数据库/map_odm_to_plant.md
-- 本质: 稳定映射表（Bridge Table），不是事实表也不是维表
-- 策略: 复合主键(kpi_type, supplier_new, plant)，不需要自增id
-- 数据来源: 只从ROW表计算，禁止从DETAIL反推
-- ============================================================
DROP TABLE IF EXISTS map_odm_to_plant;
CREATE TABLE map_odm_to_plant (
  kpi_type VARCHAR(16) NOT NULL COMMENT 'KPI类型：IFIR/RA',
  supplier_new VARCHAR(128) NOT NULL COMMENT 'ODM名称（空值统一为None）',
  plant VARCHAR(64) NOT NULL COMMENT '工厂（PLANT/PLANT_OLD）',

  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',

  PRIMARY KEY (kpi_type, supplier_new, plant),

  KEY idx_supplier (supplier_new),
  KEY idx_plant (plant)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='ODM到工厂映射表（从ROW表计算得出）';

-- ============================================================
-- 6. 上传任务表
-- ============================================================
DROP TABLE IF EXISTS upload_task;
CREATE TABLE upload_task (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
  status ENUM('queued', 'processing', 'completed', 'failed') DEFAULT 'queued' COMMENT '任务状态',
  progress INT DEFAULT 0 COMMENT '进度(0-100)',
  
  -- 文件信息
  ifir_detail_file VARCHAR(500) NULL COMMENT 'IFIR Detail文件路径',
  ifir_detail_status VARCHAR(20) NULL COMMENT 'IFIR Detail处理状态',
  ifir_detail_rows INT NULL COMMENT 'IFIR Detail行数',
  
  ifir_row_file VARCHAR(500) NULL COMMENT 'IFIR Row文件路径',
  ifir_row_status VARCHAR(20) NULL COMMENT 'IFIR Row处理状态',
  ifir_row_rows INT NULL COMMENT 'IFIR Row行数',
  
  ra_detail_file VARCHAR(500) NULL COMMENT 'RA Detail文件路径',
  ra_detail_status VARCHAR(20) NULL COMMENT 'RA Detail处理状态',
  ra_detail_rows INT NULL COMMENT 'RA Detail行数',
  
  ra_row_file VARCHAR(500) NULL COMMENT 'RA Row文件路径',
  ra_row_status VARCHAR(20) NULL COMMENT 'RA Row处理状态',
  ra_row_rows INT NULL COMMENT 'RA Row行数',
  
  -- 错误信息
  error_message TEXT NULL COMMENT '错误信息',
  
  -- 时间戳
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at DATETIME NULL COMMENT '开始处理时间',
  completed_at DATETIME NULL COMMENT '完成时间',
  
  UNIQUE KEY uk_task_id (task_id),
  KEY idx_status (status),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='上传任务表';

-- ============================================================
-- 7. 用户表
-- ============================================================
DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id            INT NOT NULL AUTO_INCREMENT,
  username      VARCHAR(50)  NOT NULL COMMENT '登录用户名',
  display_name  VARCHAR(100) NOT NULL COMMENT '显示名称',
  email         VARCHAR(100) NULL     COMMENT '邮箱（可选）',
  hashed_password VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希密码',
  role          ENUM('admin', 'uploader', 'viewer') NOT NULL DEFAULT 'viewer',
  is_active     TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login    DATETIME NULL COMMENT '最后登录时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username),
  UNIQUE KEY uk_email (email),
  KEY idx_role (role),
  KEY idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='系统用户表';

-- ============================================================
-- 完成
-- ============================================================
SELECT 'Database schema initialization completed!' AS message;

