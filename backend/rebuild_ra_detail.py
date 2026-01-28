"""重建 RA DETAIL 表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.tables import Base
from sqlalchemy import text

# 删除并重建 fact_ra_detail 表
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS fact_ra_detail'))
    conn.commit()
    print('已删除 fact_ra_detail 表')

# 重建表
Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables['fact_ra_detail']])
print('已重建 fact_ra_detail 表（不含 claim_date 字段）')
