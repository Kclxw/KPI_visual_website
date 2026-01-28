"""
导入 DETAIL 数据和 ODM 映射数据
"""
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.tables import FactIfirDetail, FactRaDetail, MapOdmToPlant

DATA_DIR = r"D:\WorkDocument\Project\Visual_KPI\VisualTeam\VisualTeam"


def import_odm_mapping():
    """导入 ODM 到 Plant 映射"""
    print("=" * 50)
    print("导入 ODM-Plant 映射")
    
    file_path = os.path.join(DATA_DIR, "ODM_to_PLANT_mapping.xlsx")
    if not os.path.exists(file_path):
        print(f"  文件不存在: {file_path}")
        return
    
    db = SessionLocal()
    try:
        df = pd.read_excel(file_path)
        print(f"  读取行数: {len(df)}")
        print(f"  列名: {list(df.columns)}")
        
        # 检查列名并适配
        rows_inserted = 0
        for _, row in df.iterrows():
            try:
                # 根据实际列名适配
                kpi_type = str(row.get("KPI_TYPE", row.get("kpi_type", "IFIR"))).strip()
                supplier_new = str(row.get("Supplier_NEW", row.get("supplier_new", row.get("ODM", "")))).strip()
                plant = str(row.get("PLANT", row.get("plant", ""))).strip()
                
                if not supplier_new or not plant:
                    continue
                
                record = MapOdmToPlant(
                    kpi_type=kpi_type,
                    supplier_new=supplier_new,
                    plant=plant
                )
                db.merge(record)
                rows_inserted += 1
            except Exception as e:
                print(f"    行错误: {e}")
                continue
        
        db.commit()
        print(f"  导入完成: {rows_inserted} 行")
        
    finally:
        db.close()


def import_ifir_detail():
    """导入 IFIR DETAIL 数据"""
    print("=" * 50)
    print("导入 IFIR DETAIL")
    
    file_path = os.path.join(DATA_DIR, "IFIR DETAIL.xlsx")
    if not os.path.exists(file_path):
        print(f"  文件不存在: {file_path}")
        return
    
    db = SessionLocal()
    try:
        df = pd.read_excel(file_path)
        print(f"  读取行数: {len(df)}")
        print(f"  列名: {list(df.columns)[:10]}...")
        
        # 过滤无效行 - 检查 claim_nbr 列
        claim_col = None
        for col in ["Claim_Nbr", "Claim_nbr", "CLAIM_NBR", "claim_nbr"]:
            if col in df.columns:
                claim_col = col
                break
        
        if not claim_col:
            print("  错误: 找不到 claim_nbr 列")
            print(f"  可用列: {list(df.columns)[:10]}")
            return
        
        # 过滤空值和汇总行
        df = df[df[claim_col].notna()]
        df = df[~df[claim_col].astype(str).str.lower().str.contains("total|grand|sum", na=False)]
        print(f"  有效数据行: {len(df)}")
        
        # 字段映射 (根据实际Excel列名)
        column_map = {
            "Claim_Nbr": "claim_nbr",
            "Delivery_Month": "delivery_month",
            "Delivery_Date": "delivery_date",
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
            "Cust_Nbr": "cust_nbr",
            "Claim_Date": "claim_date"
        }
        
        # 重命名列
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        
        # 批量插入
        rows_inserted = 0
        batch_size = 500
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
                try:
                    claim_nbr = str(row.get("claim_nbr", "")).strip()
                    if not claim_nbr:
                        continue
                    
                    record = FactIfirDetail(
                        claim_nbr=claim_nbr,
                        delivery_month=pd.to_datetime(row.get("delivery_month"), errors="coerce"),
                        delivery_date=pd.to_datetime(row.get("delivery_date"), errors="coerce"),
                        delivery_year=int(row["delivery_year"]) if pd.notna(row.get("delivery_year")) else None,
                        delivery_day=int(row["delivery_day"]) if pd.notna(row.get("delivery_day")) else None,
                        geo_2012=str(row.get("geo_2012", ""))[:32] if pd.notna(row.get("geo_2012")) else None,
                        financial_region=str(row.get("financial_region", ""))[:64] if pd.notna(row.get("financial_region")) else None,
                        plant=str(row.get("plant", ""))[:64] if pd.notna(row.get("plant")) else None,
                        brand=str(row.get("brand", ""))[:64] if pd.notna(row.get("brand")) else None,
                        segment=str(row.get("segment", ""))[:64] if pd.notna(row.get("segment")) else None,
                        segment2=str(row.get("segment2", ""))[:64] if pd.notna(row.get("segment2")) else None,
                        style=str(row.get("style", ""))[:64] if pd.notna(row.get("style")) else None,
                        series=str(row.get("series", ""))[:128] if pd.notna(row.get("series")) else None,
                        model=str(row.get("model", ""))[:128] if pd.notna(row.get("model")) else None,
                        mtm=str(row.get("mtm", ""))[:64] if pd.notna(row.get("mtm")) else None,
                        serial_nbr=str(row.get("serial_nbr", ""))[:64] if pd.notna(row.get("serial_nbr")) else None,
                        stationname=str(row.get("stationname", ""))[:255] if pd.notna(row.get("stationname")) else None,
                        station_id=int(row["station_id"]) if pd.notna(row.get("station_id")) else None,
                        data_source=str(row.get("data_source", ""))[:32] if pd.notna(row.get("data_source")) else None,
                        lastsln=str(row.get("lastsln", "")) if pd.notna(row.get("lastsln")) else None,
                        failure_code=str(row.get("failure_code", ""))[:32] if pd.notna(row.get("failure_code")) else None,
                        fault_category=str(row.get("fault_category", ""))[:128] if pd.notna(row.get("fault_category")) else None,
                        mach_desc=str(row.get("mach_desc", ""))[:255] if pd.notna(row.get("mach_desc")) else None,
                        problem_descr=str(row.get("problem_descr", ""))[:255] if pd.notna(row.get("problem_descr")) else None,
                        problem_descr_by_tech=str(row.get("problem_descr_by_tech", ""))[:255] if pd.notna(row.get("problem_descr_by_tech")) else None,
                        commodity=str(row.get("commodity", ""))[:64] if pd.notna(row.get("commodity")) else None,
                        down_part_code=str(row.get("down_part_code", ""))[:64] if pd.notna(row.get("down_part_code")) else None,
                        part_nbr=str(row.get("part_nbr", ""))[:64] if pd.notna(row.get("part_nbr")) else None,
                        part_desc=str(row.get("part_desc", ""))[:255] if pd.notna(row.get("part_desc")) else None,
                        part_supplier=str(row.get("part_supplier", ""))[:128] if pd.notna(row.get("part_supplier")) else None,
                        part_barcode=str(row.get("part_barcode", ""))[:64] if pd.notna(row.get("part_barcode")) else None,
                        packing_lot_no=str(row.get("packing_lot_no", ""))[:64] if pd.notna(row.get("packing_lot_no")) else None,
                        claim_item_nbr=str(row.get("claim_item_nbr", ""))[:64] if pd.notna(row.get("claim_item_nbr")) else None,
                        claim_status=str(row.get("claim_status", ""))[:32] if pd.notna(row.get("claim_status")) else None,
                        channel=str(row.get("channel", ""))[:32] if pd.notna(row.get("channel")) else None,
                        cust_nbr=str(row.get("cust_nbr", ""))[:64] if pd.notna(row.get("cust_nbr")) else None,
                    )
                    db.merge(record)
                    rows_inserted += 1
                except Exception as e:
                    if "Duplicate" not in str(e):
                        print(f"    行错误: {e}")
                    continue
            
            db.commit()
            print(f"  已处理: {min(i+batch_size, len(df))}/{len(df)}")
        
        print(f"  导入完成: {rows_inserted} 行")
        
    finally:
        db.close()


def import_ra_detail():
    """导入 RA DETAIL 数据"""
    print("=" * 50)
    print("导入 RA DETAIL")
    
    file_path = os.path.join(DATA_DIR, "RA DETAIL.xlsx")
    if not os.path.exists(file_path):
        print(f"  文件不存在: {file_path}")
        return
    
    db = SessionLocal()
    try:
        df = pd.read_excel(file_path)
        print(f"  读取行数: {len(df)}")
        print(f"  列名: {list(df.columns)[:10]}...")
        
        # 找 claim_nbr 列
        claim_col = None
        for col in ["Claim_Nbr", "Claim_nbr", "CLAIM_NBR", "claim_nbr"]:
            if col in df.columns:
                claim_col = col
                break
        
        if not claim_col:
            print("  错误: 找不到 claim_nbr 列")
            print(f"  可用列: {list(df.columns)[:10]}")
            return
        
        # 过滤无效行
        df = df[df[claim_col].notna()]
        df = df[~df[claim_col].astype(str).str.lower().str.contains("total|grand|sum", na=False)]
        print(f"  有效数据行: {len(df)}")
        
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
        
        # 批量插入
        rows_inserted = 0
        batch_size = 500
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
                try:
                    claim_nbr = str(row.get("claim_nbr", "")).strip()
                    if not claim_nbr:
                        continue
                    
                    record = FactRaDetail(
                        claim_nbr=claim_nbr,
                        claim_month=pd.to_datetime(row.get("claim_month"), errors="coerce"),
                        claim_date=pd.to_datetime(row.get("claim_date"), errors="coerce"),
                        geo_2012=str(row.get("geo_2012", ""))[:32] if pd.notna(row.get("geo_2012")) else None,
                        financial_region=str(row.get("financial_region", ""))[:64] if pd.notna(row.get("financial_region")) else None,
                        plant=str(row.get("plant", ""))[:64] if pd.notna(row.get("plant")) else None,
                        brand=str(row.get("brand", ""))[:64] if pd.notna(row.get("brand")) else None,
                        segment=str(row.get("segment", ""))[:64] if pd.notna(row.get("segment")) else None,
                        segment2=str(row.get("segment2", ""))[:64] if pd.notna(row.get("segment2")) else None,
                        style=str(row.get("style", ""))[:64] if pd.notna(row.get("style")) else None,
                        series=str(row.get("series", ""))[:128] if pd.notna(row.get("series")) else None,
                        model=str(row.get("model", ""))[:128] if pd.notna(row.get("model")) else None,
                        mtm=str(row.get("mtm", ""))[:64] if pd.notna(row.get("mtm")) else None,
                        serial_nbr=str(row.get("serial_nbr", ""))[:64] if pd.notna(row.get("serial_nbr")) else None,
                        stationname=str(row.get("stationname", ""))[:255] if pd.notna(row.get("stationname")) else None,
                        station_id=int(row["station_id"]) if pd.notna(row.get("station_id")) else None,
                        data_source=str(row.get("data_source", ""))[:32] if pd.notna(row.get("data_source")) else None,
                        lastsln=str(row.get("lastsln", "")) if pd.notna(row.get("lastsln")) else None,
                        failure_code=str(row.get("failure_code", ""))[:32] if pd.notna(row.get("failure_code")) else None,
                        fault_category=str(row.get("fault_category", ""))[:128] if pd.notna(row.get("fault_category")) else None,
                        mach_desc=str(row.get("mach_desc", ""))[:255] if pd.notna(row.get("mach_desc")) else None,
                        problem_descr=str(row.get("problem_descr", ""))[:255] if pd.notna(row.get("problem_descr")) else None,
                        problem_descr_by_tech=str(row.get("problem_descr_by_tech", ""))[:255] if pd.notna(row.get("problem_descr_by_tech")) else None,
                        commodity=str(row.get("commodity", ""))[:64] if pd.notna(row.get("commodity")) else None,
                        down_part_code=str(row.get("down_part_code", ""))[:64] if pd.notna(row.get("down_part_code")) else None,
                        part_nbr=str(row.get("part_nbr", ""))[:64] if pd.notna(row.get("part_nbr")) else None,
                        part_desc=str(row.get("part_desc", ""))[:255] if pd.notna(row.get("part_desc")) else None,
                        part_supplier=str(row.get("part_supplier", ""))[:128] if pd.notna(row.get("part_supplier")) else None,
                        part_barcode=str(row.get("part_barcode", ""))[:64] if pd.notna(row.get("part_barcode")) else None,
                        packing_lot_no=str(row.get("packing_lot_no", ""))[:64] if pd.notna(row.get("packing_lot_no")) else None,
                        claim_item_nbr=str(row.get("claim_item_nbr", ""))[:64] if pd.notna(row.get("claim_item_nbr")) else None,
                        claim_status=str(row.get("claim_status", ""))[:32] if pd.notna(row.get("claim_status")) else None,
                        channel=str(row.get("channel", ""))[:32] if pd.notna(row.get("channel")) else None,
                        cust_nbr=str(row.get("cust_nbr", ""))[:64] if pd.notna(row.get("cust_nbr")) else None,
                    )
                    db.merge(record)
                    rows_inserted += 1
                except Exception as e:
                    if "Duplicate" not in str(e):
                        print(f"    行错误: {e}")
                    continue
            
            db.commit()
            print(f"  已处理: {min(i+batch_size, len(df))}/{len(df)}")
        
        print(f"  导入完成: {rows_inserted} 行")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("DETAIL 和 ODM 映射数据导入")
    print("=" * 50)
    
    # 1. 导入 ODM 映射
    import_odm_mapping()
    
    # 2. 导入 IFIR DETAIL
    import_ifir_detail()
    
    # 3. 导入 RA DETAIL
    import_ra_detail()
    
    print("\n" + "=" * 50)
    print("全部导入完成")
    print("=" * 50)
