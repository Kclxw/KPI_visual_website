"""
直接数据导入脚本 - 用于测试和调试
"""
import os
import sys
import pandas as pd
import hashlib
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.tables import FactIfirRow, FactRaRow

def norm_text(x):
    if pd.isna(x):
        return "None"
    return str(x).strip()

def norm_int(x):
    if pd.isna(x) or x == "":
        return "None"
    return str(int(float(x)))

def norm_date(x):
    if pd.isna(x):
        return "None"
    return pd.to_datetime(x).date().isoformat()

def calc_ifir_row_hash(row):
    parts = [
        norm_date(row.get("delivery_month")),
        norm_text(row.get("brand")),
        norm_text(row.get("geo")),
        norm_text(row.get("product_line")),
        norm_text(row.get("segment")),
        norm_text(row.get("series")),
        norm_text(row.get("model")),
        norm_text(row.get("plant")),
        norm_text(row.get("mach_type")),
        norm_text(row.get("supplier_new")),
        norm_int(row.get("box_claim")),
        norm_int(row.get("box_mm")),
        norm_int(row.get("year_ignore")),
        norm_int(row.get("month_ignore")),
    ]
    raw = "|".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def import_ifir_row(file_path):
    print(f"导入 IFIR ROW: {file_path}")
    
    db = SessionLocal()
    try:
        df = pd.read_excel(file_path)
        print(f"  读取行数: {len(df)}")
        
        # 字段映射
        column_map = {
            "Delivery_month": "delivery_month",
            "BRAND": "brand",
            "GEO": "geo",
            "Product_line": "product_line",
            "Segment": "segment",
            "SERIES": "series",
            "Model": "model",
            "PLANT": "plant",
            "Mach_type": "mach_type",
            "Supplier_NEW": "supplier_new",
            "BOX CLAIM": "box_claim",
            "BOX MM": "box_mm",
            "YEAR": "year_ignore",
            "MONTH": "month_ignore"
        }
        df = df.rename(columns=column_map)
        
        # 过滤无效行
        if "delivery_month" in df.columns:
            df["_date_check"] = pd.to_datetime(df["delivery_month"], errors="coerce")
            valid_count = df["_date_check"].notna().sum()
            df = df[df["_date_check"].notna()].copy()
            df = df.drop(columns=["_date_check"])
            print(f"  有效数据行: {valid_count}")
        
        # 数据清洗
        df["supplier_new"] = df["supplier_new"].fillna("None").astype(str).str.strip()
        df["box_claim"] = pd.to_numeric(df["box_claim"], errors="coerce").fillna(0).astype(int)
        df["box_mm"] = pd.to_numeric(df["box_mm"], errors="coerce").fillna(0).astype(int)
        
        # 批量插入
        rows_inserted = 0
        batch_size = 500
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
                try:
                    content_hash = calc_ifir_row_hash(row)
                    record = FactIfirRow(
                        content_hash=content_hash,
                        delivery_month=pd.to_datetime(row["delivery_month"]).date(),
                        brand=row.get("brand") if pd.notna(row.get("brand")) else None,
                        geo=row.get("geo") if pd.notna(row.get("geo")) else None,
                        product_line=row.get("product_line") if pd.notna(row.get("product_line")) else None,
                        segment=row.get("segment") if pd.notna(row.get("segment")) else None,
                        series=row.get("series") if pd.notna(row.get("series")) else None,
                        model=row.get("model") if pd.notna(row.get("model")) else None,
                        plant=row.get("plant") if pd.notna(row.get("plant")) else None,
                        mach_type=row.get("mach_type") if pd.notna(row.get("mach_type")) else None,
                        supplier_new=row["supplier_new"],
                        box_claim=row["box_claim"],
                        box_mm=row["box_mm"],
                        year_ignore=int(row["year_ignore"]) if pd.notna(row.get("year_ignore")) else None,
                        month_ignore=int(row["month_ignore"]) if pd.notna(row.get("month_ignore")) else None,
                    )
                    db.merge(record)
                    rows_inserted += 1
                except Exception as e:
                    print(f"    行错误: {e}")
                    continue
            
            db.commit()
            print(f"  已处理: {min(i+batch_size, len(df))}/{len(df)}")
        
        print(f"  导入完成: {rows_inserted} 行")
        return rows_inserted
        
    finally:
        db.close()

def import_ra_row(file_path):
    print(f"导入 RA ROW: {file_path}")
    
    db = SessionLocal()
    try:
        df = pd.read_excel(file_path)
        print(f"  读取行数: {len(df)}")
        
        # 字段映射
        column_map = {
            "Claim_month": "claim_month",
            "BRAND": "brand",
            "GEO": "geo",
            "Product_line": "product_line",
            "Segment": "segment",
            "SERIES": "series",
            "Model": "model",
            "PLANT_OLD": "plant",
            "Supplier_NEW": "supplier_new",
            "Mach_type": "mach_type",
            "RA CLAIM": "ra_claim",
            "RA MM": "ra_mm",
            "Year": "year_ignore",
            "Month": "month_ignore"
        }
        df = df.rename(columns=column_map)
        
        # 过滤无效行
        if "claim_month" in df.columns:
            df["_date_check"] = pd.to_datetime(df["claim_month"], errors="coerce")
            valid_count = df["_date_check"].notna().sum()
            df = df[df["_date_check"].notna()].copy()
            df = df.drop(columns=["_date_check"])
            print(f"  有效数据行: {valid_count}")
        
        # 数据清洗
        df["supplier_new"] = df["supplier_new"].fillna("None").astype(str).str.strip()
        df["ra_claim"] = pd.to_numeric(df["ra_claim"], errors="coerce").fillna(0).astype(int)
        df["ra_mm"] = pd.to_numeric(df["ra_mm"], errors="coerce").fillna(0).astype(int)
        
        # 批量插入
        rows_inserted = 0
        batch_size = 500
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
                try:
                    parts = [
                        norm_date(row.get("claim_month")),
                        norm_text(row.get("brand")),
                        norm_text(row.get("geo")),
                        norm_text(row.get("product_line")),
                        norm_text(row.get("segment")),
                        norm_text(row.get("series")),
                        norm_text(row.get("model")),
                        norm_text(row.get("plant")),
                        norm_text(row.get("supplier_new")),
                        norm_text(row.get("mach_type")),
                        norm_int(row.get("ra_claim")),
                        norm_int(row.get("ra_mm")),
                        norm_int(row.get("year_ignore")),
                        norm_int(row.get("month_ignore")),
                    ]
                    content_hash = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
                    
                    record = FactRaRow(
                        content_hash=content_hash,
                        claim_month=pd.to_datetime(row["claim_month"]).date(),
                        brand=row.get("brand") if pd.notna(row.get("brand")) else None,
                        geo=row.get("geo") if pd.notna(row.get("geo")) else None,
                        product_line=row.get("product_line") if pd.notna(row.get("product_line")) else None,
                        segment=row.get("segment") if pd.notna(row.get("segment")) else None,
                        series=row.get("series") if pd.notna(row.get("series")) else None,
                        model=row.get("model") if pd.notna(row.get("model")) else None,
                        plant=row.get("plant") if pd.notna(row.get("plant")) else None,
                        supplier_new=row["supplier_new"],
                        mach_type=row.get("mach_type") if pd.notna(row.get("mach_type")) else None,
                        ra_claim=row["ra_claim"],
                        ra_mm=row["ra_mm"],
                        year_ignore=int(row["year_ignore"]) if pd.notna(row.get("year_ignore")) else None,
                        month_ignore=int(row["month_ignore"]) if pd.notna(row.get("month_ignore")) else None,
                    )
                    db.merge(record)
                    rows_inserted += 1
                except Exception as e:
                    print(f"    行错误: {e}")
                    continue
            
            db.commit()
            print(f"  已处理: {min(i+batch_size, len(df))}/{len(df)}")
        
        print(f"  导入完成: {rows_inserted} 行")
        return rows_inserted
        
    finally:
        db.close()

if __name__ == "__main__":
    test_data_dir = "../test_data"
    
    print("=" * 50)
    print("直接数据导入")
    print("=" * 50)
    
    # 导入 IFIR ROW
    ifir_row_path = os.path.join(test_data_dir, "IFIR ROW.xlsx")
    if os.path.exists(ifir_row_path):
        import_ifir_row(ifir_row_path)
    
    # 导入 RA ROW
    ra_row_path = os.path.join(test_data_dir, "RA row.xlsx")
    if os.path.exists(ra_row_path):
        import_ra_row(ra_row_path)
    
    print("=" * 50)
    print("导入完成")
    print("=" * 50)
