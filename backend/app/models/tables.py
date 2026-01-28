"""
数据库表模型
基于 scripts/db/init.sql 和 plan/数据库/*.md 设计
"""
from sqlalchemy import Column, BigInteger, Integer, SmallInteger, String, Text, Date, DateTime, Enum, func
from app.core.database import Base


class FactIfirRow(Base):
    """
    IFIR ROW 月度聚合事实表
    时间主轴: delivery_month
    """
    __tablename__ = "fact_ifir_row"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    content_hash = Column(String(32), unique=True, nullable=False, comment="行内容MD5哈希")
    
    # 时间维度
    delivery_month = Column(Date, nullable=True, comment="出货月(IFIR时间主轴)")
    
    # 产品与组织维度
    brand = Column(String(32), nullable=True)
    geo = Column(String(16), nullable=True)
    product_line = Column(String(32), nullable=True)
    segment = Column(String(64), nullable=True)
    series = Column(String(128), nullable=True)
    model = Column(String(128), nullable=True)
    plant = Column(String(64), nullable=True)
    mach_type = Column(String(64), nullable=True)
    supplier_new = Column(String(128), nullable=True, comment="ODM")
    
    # KPI指标
    box_claim = Column(Integer, nullable=False, comment="IFIR分子")
    box_mm = Column(Integer, nullable=False, comment="IFIR分母")
    
    # 溯源字段
    year_ignore = Column(SmallInteger, nullable=True)
    month_ignore = Column(SmallInteger, nullable=True)
    
    # 元数据
    src_file = Column(String(255), nullable=True)
    etl_batch_id = Column(String(64), nullable=True)
    load_ts = Column(DateTime, server_default=func.now())


class FactIfirDetail(Base):
    """
    IFIR DETAIL 事件级明细表
    主键: claim_nbr
    """
    __tablename__ = "fact_ifir_detail"
    
    claim_nbr = Column(String(64), primary_key=True, comment="索赔单号")
    
    # 时间维度
    claim_month = Column(Date, nullable=True)
    claim_date = Column(Date, nullable=True)
    delivery_month = Column(Date, nullable=True, comment="IFIR下钻主时间轴")
    delivery_day = Column(SmallInteger, nullable=True)
    
    # 区域维度
    geo_2012 = Column(String(32), nullable=True)
    financial_region = Column(String(64), nullable=True)
    plant = Column(String(64), nullable=True)
    
    # 产品维度
    brand = Column(String(64), nullable=True)
    segment = Column(String(64), nullable=True)
    segment2 = Column(String(64), nullable=True)
    style = Column(String(64), nullable=True)
    series = Column(String(128), nullable=True)
    model = Column(String(128), nullable=True)
    mtm = Column(String(64), nullable=True)
    serial_nbr = Column(String(64), nullable=True)
    
    # 服务追溯
    stationname = Column(String(255), nullable=True)
    station_id = Column(Integer, nullable=True)
    data_source = Column(String(32), nullable=True)
    lastsln = Column(Text, nullable=True)
    
    # 故障维度
    failure_code = Column(String(32), nullable=True)
    fault_category = Column(String(128), nullable=True, comment="故障大类-Top Issue")
    mach_desc = Column(String(255), nullable=True)
    problem_descr = Column(String(255), nullable=True)
    problem_descr_by_tech = Column(String(255), nullable=True)
    
    # 零部件维度
    commodity = Column(String(64), nullable=True)
    down_part_code = Column(String(64), nullable=True)
    part_nbr = Column(String(64), nullable=True)
    part_desc = Column(String(255), nullable=True)
    part_supplier = Column(String(128), nullable=True)
    part_barcode = Column(String(64), nullable=True)
    packing_lot_no = Column(String(64), nullable=True)
    
    # 索赔维度
    claim_item_nbr = Column(String(64), nullable=True)
    claim_status = Column(String(32), nullable=True)
    channel = Column(String(32), nullable=True)
    cust_nbr = Column(String(64), nullable=True)
    
    load_ts = Column(DateTime, server_default=func.now())


class FactRaRow(Base):
    """
    RA ROW 月度聚合事实表
    时间主轴: claim_month
    """
    __tablename__ = "fact_ra_row"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    content_hash = Column(String(32), unique=True, nullable=False)
    
    # 时间维度
    claim_month = Column(Date, nullable=True, comment="索赔归属月(RA时间主轴)")
    
    # 产品与组织维度
    brand = Column(String(32), nullable=True)
    geo = Column(String(16), nullable=True)
    product_line = Column(String(32), nullable=True)
    segment = Column(String(64), nullable=True)
    series = Column(String(128), nullable=True)
    model = Column(String(128), nullable=True)
    plant = Column(String(64), nullable=True, comment="源字段PLANT_OLD")
    supplier_new = Column(String(128), nullable=True, comment="ODM")
    mach_type = Column(String(64), nullable=True)
    
    # KPI指标
    ra_claim = Column(Integer, nullable=False, comment="RA分子")
    ra_mm = Column(Integer, nullable=False, comment="RA分母")
    
    # 溯源字段
    year_ignore = Column(SmallInteger, nullable=True)
    month_ignore = Column(SmallInteger, nullable=True)
    
    # 元数据
    src_file = Column(String(255), nullable=True)
    etl_batch_id = Column(String(64), nullable=True)
    load_ts = Column(DateTime, server_default=func.now())


class FactRaDetail(Base):
    """
    RA DETAIL 事件级明细表
    主键: claim_nbr
    """
    __tablename__ = "fact_ra_detail"
    
    claim_nbr = Column(String(64), primary_key=True)
    
    # 时间维度
    claim_month = Column(Date, nullable=True, comment="RA下钻主时间轴")
    
    # 区域维度
    geo_2012 = Column(String(32), nullable=True)
    financial_region = Column(String(64), nullable=True)
    plant = Column(String(64), nullable=True)
    
    # 产品维度
    brand = Column(String(64), nullable=True)
    segment = Column(String(64), nullable=True)
    segment2 = Column(String(64), nullable=True)
    style = Column(String(64), nullable=True)
    series = Column(String(128), nullable=True)
    model = Column(String(128), nullable=True)
    mtm = Column(String(64), nullable=True)
    serial_nbr = Column(String(64), nullable=True)
    
    # 服务追溯
    stationname = Column(String(255), nullable=True)
    station_id = Column(Integer, nullable=True)
    data_source = Column(String(32), nullable=True)
    lastsln = Column(Text, nullable=True)
    
    # 故障维度
    failure_code = Column(String(32), nullable=True)
    fault_category = Column(String(128), nullable=True)
    mach_desc = Column(String(255), nullable=True)
    problem_descr = Column(String(255), nullable=True)
    problem_descr_by_tech = Column(String(255), nullable=True)
    
    # 零部件维度
    commodity = Column(String(64), nullable=True)
    down_part_code = Column(String(64), nullable=True)
    part_nbr = Column(String(64), nullable=True)
    part_desc = Column(String(255), nullable=True)
    part_supplier = Column(String(128), nullable=True)
    part_barcode = Column(String(64), nullable=True)
    packing_lot_no = Column(String(64), nullable=True)
    
    # 索赔维度
    claim_item_nbr = Column(String(64), nullable=True)
    claim_status = Column(String(32), nullable=True)
    channel = Column(String(32), nullable=True)
    cust_nbr = Column(String(64), nullable=True)
    
    load_ts = Column(DateTime, server_default=func.now())


class MapOdmToPlant(Base):
    """
    ODM到工厂映射表
    复合主键: (kpi_type, supplier_new, plant)
    """
    __tablename__ = "map_odm_to_plant"
    
    kpi_type = Column(String(16), primary_key=True, comment="IFIR/RA")
    supplier_new = Column(String(128), primary_key=True, comment="ODM")
    plant = Column(String(64), primary_key=True, comment="工厂")
    load_ts = Column(DateTime, server_default=func.now())


class UploadTask(Base):
    """上传任务表"""
    __tablename__ = "upload_task"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(100), unique=True, nullable=False)
    status = Column(Enum("queued", "processing", "completed", "failed"), default="queued")
    progress = Column(Integer, default=0)
    
    # 文件信息
    ifir_detail_file = Column(String(500), nullable=True)
    ifir_detail_status = Column(String(20), nullable=True)
    ifir_detail_rows = Column(Integer, nullable=True)
    
    ifir_row_file = Column(String(500), nullable=True)
    ifir_row_status = Column(String(20), nullable=True)
    ifir_row_rows = Column(Integer, nullable=True)
    
    ra_detail_file = Column(String(500), nullable=True)
    ra_detail_status = Column(String(20), nullable=True)
    ra_detail_rows = Column(Integer, nullable=True)
    
    ra_row_file = Column(String(500), nullable=True)
    ra_row_status = Column(String(20), nullable=True)
    ra_row_rows = Column(Integer, nullable=True)
    
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
