"""
快速批量导入 DETAIL 数据（使用 bulk insert）
"""
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
DATA_DIR = r"D:\WorkDocument\Project\Visual_KPI\VisualTeam\VisualTeam"

def fast_import_ifir_detail():
    """快速导入 IFIR DETAIL"""
    print("=" * 50)
    print("快速导入 IFIR DETAIL")
    
    file_path = os.path.join(DATA_DIR, "IFIR DETAIL.xlsx")
    if not os.path.exists(file_path):
        print(f"  文件不存在: {file_path}")
        return
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        df = pd.read_excel(file_path)
        print(f"  读取行数: {len(df)}")
        
        # 字段映射
        column_map = {
            "Claim_Nbr": "claim_nbr",
            "Delivery_Month": "delivery_month",
            "Claim_Date": "claim_date",
            "Delivery_Year": "delivery_year",
            "Delivery_Day": "delivery_day",
            "Geo_2012": "geo_2012",
            "Financial Region": "financial_region",
            "PLANT": "plant",
            "Brand": "brand",
            "Segment": "segment",
            "Segment2": "segment2",
            "Style": "style",
            "Series": "series",
            "Model": "model",
            "MTM": "mtm",
            "Serial_Nbr": "serial_nbr",
            "StationName": "stationname",
            "Station_ID": "station_id",
            "Data_Source": "data_source",
            "LastSln": "lastsln",
            "Failure_Code": "failure_code",
            "Fault_Category": "fault_category",
            "Mach_Desc": "mach_desc",
            "Problem_Descr": "problem_descr",
            "Problem_Descr_by_Tech": "problem_descr_by_tech",
            "Commodity": "commodity",
            "Down_Part_Code": "down_part_code",
            "Part_Nbr": "part_nbr",
            "Part_desc": "part_desc",
            "Part_Supplier": "part_supplier",
            "Part_Barcode": "part_barcode",
            "Packing_Lot_No": "packing_lot_no",
            "Claim_Item_Nbr": "claim_item_nbr",
            "Claim_Status": "claim_status",
            "Channel": "channel",
            "Cust_Nbr": "cust_nbr"
        }
        
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        
        # 过滤无效行
        if "claim_nbr" in df.columns:
            df = df[df["claim_nbr"].notna()]
            df = df[~df["claim_nbr"].astype(str).str.lower().str.contains("total|grand|sum", na=False)]
            print(f"  有效数据行: {len(df)}")
        
        # 只保留数据库表中存在的列
        db_columns = [
            "claim_nbr", "delivery_month", "claim_date", "delivery_year", "delivery_day",
            "geo_2012", "financial_region", "plant", "brand", "segment", "segment2",
            "style", "series", "model", "mtm", "serial_nbr", "stationname", "station_id",
            "data_source", "lastsln", "failure_code", "fault_category", "mach_desc",
            "problem_descr", "problem_descr_by_tech", "commodity", "down_part_code",
            "part_nbr", "part_desc", "part_supplier", "part_barcode", "packing_lot_no",
            "claim_item_nbr", "claim_status", "channel", "cust_nbr"
        ]
        
        df_insert = df[[col for col in db_columns if col in df.columns]]
        
        # 日期转换
        for date_col in ["delivery_month", "claim_date"]:
            if date_col in df_insert.columns:
                df_insert[date_col] = pd.to_datetime(df_insert[date_col], errors="coerce")
        
        # 字符串长度截断
        string_limits = {
            "claim_nbr": 64, "geo_2012": 32, "financial_region": 64, "plant": 64,
            "brand": 64, "segment": 64, "segment2": 64, "style": 64, "series": 128,
            "model": 128, "mtm": 64, "serial_nbr": 64, "stationname": 255,
            "data_source": 32, "failure_code": 32, "fault_category": 128,
            "mach_desc": 255, "problem_descr": 255, "problem_descr_by_tech": 255,
            "commodity": 64, "down_part_code": 64, "part_nbr": 64, "part_desc": 255,
            "part_supplier": 128, "part_barcode": 64, "packing_lot_no": 64,
            "claim_item_nbr": 64, "claim_status": 32, "channel": 32, "cust_nbr": 64
        }
        
        for col, limit in string_limits.items():
            if col in df_insert.columns:
                df_insert[col] = df_insert[col].astype(str).str[:limit]
                df_insert[col] = df_insert[col].replace('nan', None)
        
        # 使用 pandas to_sql 批量插入 (ON DUPLICATE KEY IGNORE)
        print("  开始批量插入...")
        with engine.connect() as conn:
            # 先删除已存在的数据（可选）
            # conn.execute(text("TRUNCATE TABLE fact_ifir_detail"))
            # conn.commit()
            
            # 批量插入，使用 replace 处理重复键
            df_insert.to_sql(
                name="fact_ifir_detail",
                con=conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000
            )
            conn.commit()
        
        print(f"  导入完成: {len(df_insert)} 行")
        
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

def fast_import_ra_detail():
    """快速导入 RA DETAIL"""
    print("=" * 50)
    print("快速导入 RA DETAIL")
    
    file_path = os.path.join(DATA_DIR, "RA DETAIL.xlsx")
    if not os.path.exists(file_path):
        print(f"  文件不存在: {file_path}")
        return
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        df = pd.read_excel(file_path)
        print(f"  读取行数: {len(df)}")
        
        # 字段映射
        column_map = {
            "Claim_Nbr": "claim_nbr",
            "Claim_Month": "claim_month",
            "Claim_Date": "claim_date",
            "Geo_2012": "geo_2012",
            "Financial Region": "financial_region",
            "PLANT": "plant",
            "Brand": "brand",
            "Segment": "segment",
            "Segment2": "segment2",
            "Style": "style",
            "Series": "series",
            "Model": "model",
            "MTM": "mtm",
            "Serial_Nbr": "serial_nbr",
            "StationName": "stationname",
            "Station_ID": "station_id",
            "Data_Source": "data_source",
            "LastSln": "lastsln",
            "Failure_Code": "failure_code",
            "Fault_Category": "fault_category",
            "Mach_Desc": "mach_desc",
            "Problem_Descr": "problem_descr",
            "Problem_Descr_by_Tech": "problem_descr_by_tech",
            "Commodity": "commodity",
            "Down_Part_Code": "down_part_code",
            "Part_Nbr": "part_nbr",
            "Part_desc": "part_desc",
            "Part_Supplier": "part_supplier",
            "Part_Barcode": "part_barcode",
            "Packing_Lot_No": "packing_lot_no",
            "Claim_Item_Nbr": "claim_item_nbr",
            "Claim_Status": "claim_status",
            "Channel": "channel",
            "Cust_Nbr": "cust_nbr"
        }
        
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        
        # 过滤无效行
        if "claim_nbr" in df.columns:
            df = df[df["claim_nbr"].notna()]
            df = df[~df["claim_nbr"].astype(str).str.lower().str.contains("total|grand|sum", na=False)]
            print(f"  有效数据行: {len(df)}")
        
        # 只保留数据库表中存在的列
        db_columns = [
            "claim_nbr", "claim_month", "claim_date", "geo_2012", "financial_region",
            "plant", "brand", "segment", "segment2", "style", "series", "model",
            "mtm", "serial_nbr", "stationname", "station_id", "data_source", "lastsln",
            "failure_code", "fault_category", "mach_desc", "problem_descr",
            "problem_descr_by_tech", "commodity", "down_part_code", "part_nbr",
            "part_desc", "part_supplier", "part_barcode", "packing_lot_no",
            "claim_item_nbr", "claim_status", "channel", "cust_nbr"
        ]
        
        df_insert = df[[col for col in db_columns if col in df.columns]]
        
        # 日期转换
        for date_col in ["claim_month", "claim_date"]:
            if date_col in df_insert.columns:
                df_insert[date_col] = pd.to_datetime(df_insert[date_col], errors="coerce")
        
        # 字符串长度截断
        string_limits = {
            "claim_nbr": 64, "geo_2012": 32, "financial_region": 64, "plant": 64,
            "brand": 64, "segment": 64, "segment2": 64, "style": 64, "series": 128,
            "model": 128, "mtm": 64, "serial_nbr": 64, "stationname": 255,
            "data_source": 32, "failure_code": 32, "fault_category": 128,
            "mach_desc": 255, "problem_descr": 255, "problem_descr_by_tech": 255,
            "commodity": 64, "down_part_code": 64, "part_nbr": 64, "part_desc": 255,
            "part_supplier": 128, "part_barcode": 64, "packing_lot_no": 64,
            "claim_item_nbr": 64, "claim_status": 32, "channel": 32, "cust_nbr": 64
        }
        
        for col, limit in string_limits.items():
            if col in df_insert.columns:
                df_insert[col] = df_insert[col].astype(str).str[:limit]
                df_insert[col] = df_insert[col].replace('nan', None)
        
        # 批量插入
        print("  开始批量插入...")
        with engine.connect() as conn:
            df_insert.to_sql(
                name="fact_ra_detail",
                con=conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000
            )
            conn.commit()
        
        print(f"  导入完成: {len(df_insert)} 行")
        
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("快速批量导入 DETAIL 数据")
    print("=" * 50)
    
    fast_import_ifir_detail()
    fast_import_ra_detail()
    
    print("\n" + "=" * 50)
    print("导入完成")
    print("=" * 50)
