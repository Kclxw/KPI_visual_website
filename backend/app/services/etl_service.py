"""
ETL服务 - 处理Excel文件导入
"""
import hashlib
import logging
import pandas as pd
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.models.tables import (
    UploadTask, FactIfirRow, FactIfirDetail, 
    FactRaRow, FactRaDetail, MapOdmToPlant
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EtlService:
    """ETL数据处理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_upload_task(self, task_id: str, files: dict):
        """处理上传任务"""
        logger.info(f"[ETL] 开始处理任务: {task_id}")
        logger.info(f"[ETL] 文件列表: {list(files.keys())}")
        
        task = self.db.query(UploadTask).filter(UploadTask.task_id == task_id).first()
        if not task:
            logger.error(f"[ETL] 任务不存在: {task_id}")
            return
        
        task.status = "processing"
        task.started_at = datetime.now()
        self.db.commit()
        logger.info(f"[ETL] 任务状态更新为 processing")
        
        total_files = len(files)
        processed = 0
        
        try:
            # 处理各个文件
            if "ifir_row" in files:
                logger.info(f"[ETL] 开始处理 IFIR ROW: {files['ifir_row']}")
                self._process_ifir_row(task, files["ifir_row"])
                processed += 1
                task.progress = int(processed / total_files * 100)
                self.db.commit()
                logger.info(f"[ETL] IFIR ROW 处理完成, 进度: {task.progress}%")
            
            if "ifir_detail" in files:
                logger.info(f"[ETL] 开始处理 IFIR DETAIL: {files['ifir_detail']}")
                self._process_ifir_detail(task, files["ifir_detail"])
                processed += 1
                task.progress = int(processed / total_files * 100)
                self.db.commit()
                logger.info(f"[ETL] IFIR DETAIL 处理完成, 进度: {task.progress}%")
            
            if "ra_row" in files:
                logger.info(f"[ETL] 开始处理 RA ROW: {files['ra_row']}")
                self._process_ra_row(task, files["ra_row"])
                processed += 1
                task.progress = int(processed / total_files * 100)
                self.db.commit()
                logger.info(f"[ETL] RA ROW 处理完成, 进度: {task.progress}%")
            
            if "ra_detail" in files:
                logger.info(f"[ETL] 开始处理 RA DETAIL: {files['ra_detail']}")
                self._process_ra_detail(task, files["ra_detail"])
                processed += 1
                task.progress = int(processed / total_files * 100)
                self.db.commit()
                logger.info(f"[ETL] RA DETAIL 处理完成, 进度: {task.progress}%")
            
            # 更新ODM映射表
            logger.info("[ETL] 开始刷新ODM映射表")
            self._refresh_odm_mapping()
            logger.info("[ETL] ODM映射表刷新完成")
            
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now()
            self.db.commit()
            logger.info(f"[ETL] 任务完成: {task_id}")
            
        except Exception as e:
            logger.error(f"[ETL] 任务失败: {task_id}, 错误: {str(e)}", exc_info=True)
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()
            self.db.commit()
            raise
    
    # ==================== IFIR ROW ====================
    
    def _process_ifir_row(self, task: UploadTask, file_path: str):
        """处理IFIR ROW文件"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"[IFIR ROW] 读取Excel完成, 原始行数: {len(df)}")
            
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
            logger.info(f"[IFIR ROW] 实际列名: {list(df.columns)}")
            
            # 过滤掉非数据行（汇总行、筛选条件等）
            if "delivery_month" in df.columns:
                df["_date_check"] = pd.to_datetime(df["delivery_month"], errors="coerce")
                df = df[df["_date_check"].notna()]
                df = df.drop(columns=["_date_check"])
            
            logger.info(f"[IFIR ROW] 过滤后行数: {len(df)}")
            
            # 数据清洗
            df["supplier_new"] = df["supplier_new"].fillna("None").astype(str).str.strip()
            df["box_claim"] = pd.to_numeric(df["box_claim"], errors="coerce").fillna(0).astype(int)
            df["box_mm"] = pd.to_numeric(df["box_mm"], errors="coerce").fillna(0).astype(int)
            
            # 计算content_hash
            df["content_hash"] = df.apply(self._calc_ifir_row_hash, axis=1)
            df["src_file"] = file_path
            df["etl_batch_id"] = task.task_id
            
            # 批量写入数据库 (使用 INSERT ON DUPLICATE KEY UPDATE)
            total = len(df)
            batch_size = 500
            rows_processed = 0
            
            for start_idx in range(0, total, batch_size):
                end_idx = min(start_idx + batch_size, total)
                batch_df = df.iloc[start_idx:end_idx]
                
                records = []
                for _, row in batch_df.iterrows():
                    records.append({
                        "content_hash": row["content_hash"],
                        "delivery_month": pd.to_datetime(row["delivery_month"]).date() if pd.notna(row["delivery_month"]) else None,
                        "brand": self._safe_str(row, "brand"),
                        "geo": self._safe_str(row, "geo"),
                        "product_line": self._safe_str(row, "product_line"),
                        "segment": self._safe_str(row, "segment"),
                        "series": self._safe_str(row, "series"),
                        "model": self._safe_str(row, "model"),
                        "plant": self._safe_str(row, "plant"),
                        "mach_type": self._safe_str(row, "mach_type"),
                        "supplier_new": self._safe_str(row, "supplier_new"),
                        "box_claim": int(row["box_claim"]),
                        "box_mm": int(row["box_mm"]),
                        "year_ignore": int(row["year_ignore"]) if pd.notna(row.get("year_ignore")) else None,
                        "month_ignore": int(row["month_ignore"]) if pd.notna(row.get("month_ignore")) else None,
                        "src_file": self._safe_str(row, "src_file"),
                        "etl_batch_id": self._safe_str(row, "etl_batch_id")
                    })
                
                if records:
                    stmt = mysql_insert(FactIfirRow).values(records)
                    update_dict = {c.name: stmt.inserted[c.name] for c in FactIfirRow.__table__.columns if c.name not in ['id', 'content_hash', 'load_ts']}
                    stmt = stmt.on_duplicate_key_update(**update_dict)
                    self.db.execute(stmt)
                    self.db.commit()
                
                rows_processed += len(records)
                logger.info(f"[IFIR ROW] 进度: {rows_processed}/{total}")
            
            task.ifir_row_status = "completed"
            task.ifir_row_rows = rows_processed
            logger.info(f"[IFIR ROW] 完成, 插入/更新: {rows_processed} 行")
            
        except Exception as e:
            logger.error(f"[IFIR ROW] 处理失败: {str(e)}", exc_info=True)
            task.ifir_row_status = "failed"
            raise Exception(f"IFIR ROW处理失败: {str(e)}")
    
    def _calc_ifir_row_hash(self, row) -> str:
        """计算IFIR ROW行哈希"""
        parts = [
            self._norm_date(row.get("delivery_month")),
            self._norm_text(row.get("brand")),
            self._norm_text(row.get("geo")),
            self._norm_text(row.get("product_line")),
            self._norm_text(row.get("segment")),
            self._norm_text(row.get("series")),
            self._norm_text(row.get("model")),
            self._norm_text(row.get("plant")),
            self._norm_text(row.get("mach_type")),
            self._norm_text(row.get("supplier_new")),
            self._norm_int(row.get("box_claim")),
            self._norm_int(row.get("box_mm")),
            self._norm_int(row.get("year_ignore")),
            self._norm_int(row.get("month_ignore")),
        ]
        raw = "|".join(parts)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    
    # ==================== IFIR DETAIL ====================
    
    def _process_ifir_detail(self, task: UploadTask, file_path: str):
        """处理IFIR DETAIL文件"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"[IFIR DETAIL] 读取Excel完成, 原始行数: {len(df)}")
            
            # 清理列名：去除前后空格，统一格式
            df.columns = df.columns.str.strip()
            logger.info(f"[IFIR DETAIL] 实际列名: {list(df.columns)}")
            
            # 字段映射
            column_map = {
                "Claim_Nbr": "claim_nbr",
                "Claim_Month": "claim_month",
                "Claim_Date": "claim_date",
                "Delivery_Month": "delivery_month",
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
            
            df = df.rename(columns=column_map)
            
            # 去除claim_nbr为空的行
            if "claim_nbr" not in df.columns:
                raise Exception(f"缺少必需列 claim_nbr, 现有列: {list(df.columns)}")
            
            df = df[df["claim_nbr"].notna()].copy()
            df["claim_nbr"] = df["claim_nbr"].astype(str).str.strip()
            
            # 去重（如果有claim_date则按日期排序，否则直接去重）
            if "claim_date" in df.columns:
                df["claim_date_sort"] = pd.to_datetime(df["claim_date"], errors="coerce")
                df = df.sort_values(["claim_nbr", "claim_date_sort"], ascending=[True, False])
                df = df.drop_duplicates(subset=["claim_nbr"], keep="first")
                df = df.drop(columns=["claim_date_sort"])
            else:
                df = df.drop_duplicates(subset=["claim_nbr"], keep="first")
            
            logger.info(f"[IFIR DETAIL] 去重后行数: {len(df)}")
            
            # 批量写入数据库 (使用 INSERT ON DUPLICATE KEY UPDATE)
            total = len(df)
            batch_size = 500
            rows_processed = 0
            
            for start_idx in range(0, total, batch_size):
                end_idx = min(start_idx + batch_size, total)
                batch_df = df.iloc[start_idx:end_idx]
                
                records = []
                for _, row in batch_df.iterrows():
                    records.append({
                        "claim_nbr": row["claim_nbr"],
                        "claim_month": pd.to_datetime(row.get("claim_month")).date() if pd.notna(row.get("claim_month")) else None,
                        "claim_date": pd.to_datetime(row.get("claim_date")).date() if pd.notna(row.get("claim_date")) else None,
                        "delivery_month": pd.to_datetime(row.get("delivery_month")).date() if pd.notna(row.get("delivery_month")) else None,
                        "delivery_day": int(row["delivery_day"]) if pd.notna(row.get("delivery_day")) else None,
                        "geo_2012": self._safe_str(row, "geo_2012"),
                        "financial_region": self._safe_str(row, "financial_region"),
                        "plant": self._safe_str(row, "plant"),
                        "brand": self._safe_str(row, "brand"),
                        "segment": self._safe_str(row, "segment"),
                        "segment2": self._safe_str(row, "segment2"),
                        "style": self._safe_str(row, "style"),
                        "series": self._safe_str(row, "series"),
                        "model": self._safe_str(row, "model"),
                        "mtm": self._safe_str(row, "mtm"),
                        "serial_nbr": self._safe_str(row, "serial_nbr"),
                        "stationname": self._safe_str(row, "stationname"),
                        "station_id": int(row["station_id"]) if pd.notna(row.get("station_id")) else None,
                        "data_source": self._safe_str(row, "data_source"),
                        "lastsln": self._safe_str(row, "lastsln"),
                        "failure_code": self._safe_str(row, "failure_code"),
                        "fault_category": self._safe_str(row, "fault_category"),
                        "mach_desc": self._safe_str(row, "mach_desc"),
                        "problem_descr": self._safe_str(row, "problem_descr"),
                        "problem_descr_by_tech": self._safe_str(row, "problem_descr_by_tech"),
                        "commodity": self._safe_str(row, "commodity"),
                        "down_part_code": self._safe_str(row, "down_part_code"),
                        "part_nbr": self._safe_str(row, "part_nbr"),
                        "part_desc": self._safe_str(row, "part_desc"),
                        "part_supplier": self._safe_str(row, "part_supplier"),
                        "part_barcode": self._safe_str(row, "part_barcode"),
                        "packing_lot_no": self._safe_str(row, "packing_lot_no"),
                        "claim_item_nbr": self._safe_str(row, "claim_item_nbr"),
                        "claim_status": self._safe_str(row, "claim_status"),
                        "channel": self._safe_str(row, "channel"),
                        "cust_nbr": self._safe_str(row, "cust_nbr")
                    })
                
                if records:
                    stmt = mysql_insert(FactIfirDetail).values(records)
                    update_dict = {c.name: stmt.inserted[c.name] for c in FactIfirDetail.__table__.columns if c.name not in ['claim_nbr', 'load_ts']}
                    stmt = stmt.on_duplicate_key_update(**update_dict)
                    self.db.execute(stmt)
                    self.db.commit()
                
                rows_processed += len(records)
                logger.info(f"[IFIR DETAIL] 进度: {rows_processed}/{total}")
            
            task.ifir_detail_status = "completed"
            task.ifir_detail_rows = rows_processed
            logger.info(f"[IFIR DETAIL] 完成, 插入/更新: {rows_processed} 行")
            
        except Exception as e:
            logger.error(f"[IFIR DETAIL] 处理失败: {str(e)}", exc_info=True)
            task.ifir_detail_status = "failed"
            raise Exception(f"IFIR DETAIL处理失败: {str(e)}")
    
    # ==================== RA ROW ====================
    
    def _process_ra_row(self, task: UploadTask, file_path: str):
        """处理RA ROW文件"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"[RA ROW] 读取Excel完成, 原始行数: {len(df)}")
            
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
            logger.info(f"[RA ROW] 实际列名: {list(df.columns)}")
            
            # 过滤掉非数据行
            if "claim_month" in df.columns:
                df["_date_check"] = pd.to_datetime(df["claim_month"], errors="coerce")
                df = df[df["_date_check"].notna()]
                df = df.drop(columns=["_date_check"])
            
            logger.info(f"[RA ROW] 过滤后行数: {len(df)}")
            
            # 数据清洗
            df["supplier_new"] = df["supplier_new"].fillna("None").astype(str).str.strip()
            df["ra_claim"] = pd.to_numeric(df["ra_claim"], errors="coerce").fillna(0).astype(int)
            df["ra_mm"] = pd.to_numeric(df["ra_mm"], errors="coerce").fillna(0).astype(int)
            
            # 计算content_hash
            df["content_hash"] = df.apply(self._calc_ra_row_hash, axis=1)
            df["src_file"] = file_path
            df["etl_batch_id"] = task.task_id
            
            # 批量写入数据库 (使用 INSERT ON DUPLICATE KEY UPDATE)
            total = len(df)
            batch_size = 500
            rows_processed = 0
            
            for start_idx in range(0, total, batch_size):
                end_idx = min(start_idx + batch_size, total)
                batch_df = df.iloc[start_idx:end_idx]
                
                records = []
                for _, row in batch_df.iterrows():
                    records.append({
                        "content_hash": row["content_hash"],
                        "claim_month": pd.to_datetime(row["claim_month"]).date() if pd.notna(row["claim_month"]) else None,
                        "brand": self._safe_str(row, "brand"),
                        "geo": self._safe_str(row, "geo"),
                        "product_line": self._safe_str(row, "product_line"),
                        "segment": self._safe_str(row, "segment"),
                        "series": self._safe_str(row, "series"),
                        "model": self._safe_str(row, "model"),
                        "plant": self._safe_str(row, "plant"),
                        "supplier_new": self._safe_str(row, "supplier_new"),
                        "mach_type": self._safe_str(row, "mach_type"),
                        "ra_claim": int(row["ra_claim"]),
                        "ra_mm": int(row["ra_mm"]),
                        "year_ignore": int(row["year_ignore"]) if pd.notna(row.get("year_ignore")) else None,
                        "month_ignore": int(row["month_ignore"]) if pd.notna(row.get("month_ignore")) else None,
                        "src_file": self._safe_str(row, "src_file"),
                        "etl_batch_id": self._safe_str(row, "etl_batch_id")
                    })
                
                if records:
                    stmt = mysql_insert(FactRaRow).values(records)
                    update_dict = {c.name: stmt.inserted[c.name] for c in FactRaRow.__table__.columns if c.name not in ['id', 'content_hash', 'load_ts']}
                    stmt = stmt.on_duplicate_key_update(**update_dict)
                    self.db.execute(stmt)
                    self.db.commit()
                
                rows_processed += len(records)
                logger.info(f"[RA ROW] 进度: {rows_processed}/{total}")
            
            task.ra_row_status = "completed"
            task.ra_row_rows = rows_processed
            logger.info(f"[RA ROW] 完成, 插入/更新: {rows_processed} 行")
            
        except Exception as e:
            logger.error(f"[RA ROW] 处理失败: {str(e)}", exc_info=True)
            task.ra_row_status = "failed"
            raise Exception(f"RA ROW处理失败: {str(e)}")
    
    def _calc_ra_row_hash(self, row) -> str:
        """计算RA ROW行哈希"""
        parts = [
            self._norm_date(row.get("claim_month")),
            self._norm_text(row.get("brand")),
            self._norm_text(row.get("geo")),
            self._norm_text(row.get("product_line")),
            self._norm_text(row.get("segment")),
            self._norm_text(row.get("series")),
            self._norm_text(row.get("model")),
            self._norm_text(row.get("plant")),
            self._norm_text(row.get("supplier_new")),
            self._norm_text(row.get("mach_type")),
            self._norm_int(row.get("ra_claim")),
            self._norm_int(row.get("ra_mm")),
            self._norm_int(row.get("year_ignore")),
            self._norm_int(row.get("month_ignore")),
        ]
        raw = "|".join(parts)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    
    # ==================== RA DETAIL ====================
    
    def _process_ra_detail(self, task: UploadTask, file_path: str):
        """处理RA DETAIL文件"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"[RA DETAIL] 读取Excel完成, 原始行数: {len(df)}")
            
            # 清理列名：去除前后空格，统一格式
            df.columns = df.columns.str.strip()
            logger.info(f"[RA DETAIL] 实际列名: {list(df.columns)}")
            
            # 字段映射 (与IFIR DETAIL类似)
            column_map = {
                "Claim_Nbr": "claim_nbr",
                "Claim_Month": "claim_month",
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
            
            df = df.rename(columns=column_map)
            
            # 去除claim_nbr为空的行
            if "claim_nbr" not in df.columns:
                raise Exception(f"缺少必需列 claim_nbr, 现有列: {list(df.columns)}")
            
            df = df[df["claim_nbr"].notna()].copy()
            df["claim_nbr"] = df["claim_nbr"].astype(str).str.strip()
            
            # 去重（按claim_month排序，保留最新的记录）
            if "claim_month" in df.columns:
                df["claim_month_sort"] = pd.to_datetime(df["claim_month"], errors="coerce")
                df = df.sort_values(["claim_nbr", "claim_month_sort"], ascending=[True, False])
                df = df.drop_duplicates(subset=["claim_nbr"], keep="first")
                df = df.drop(columns=["claim_month_sort"])
            else:
                df = df.drop_duplicates(subset=["claim_nbr"], keep="first")
            
            logger.info(f"[RA DETAIL] 去重后行数: {len(df)}")
            
            # 批量写入数据库 (使用 INSERT ON DUPLICATE KEY UPDATE)
            total = len(df)
            batch_size = 500
            rows_processed = 0
            
            for start_idx in range(0, total, batch_size):
                end_idx = min(start_idx + batch_size, total)
                batch_df = df.iloc[start_idx:end_idx]
                
                records = []
                for _, row in batch_df.iterrows():
                    records.append({
                        "claim_nbr": row["claim_nbr"],
                        "claim_month": pd.to_datetime(row.get("claim_month")).date() if pd.notna(row.get("claim_month")) else None,
                        "geo_2012": self._safe_str(row, "geo_2012"),
                        "financial_region": self._safe_str(row, "financial_region"),
                        "plant": self._safe_str(row, "plant"),
                        "brand": self._safe_str(row, "brand"),
                        "segment": self._safe_str(row, "segment"),
                        "segment2": self._safe_str(row, "segment2"),
                        "style": self._safe_str(row, "style"),
                        "series": self._safe_str(row, "series"),
                        "model": self._safe_str(row, "model"),
                        "mtm": self._safe_str(row, "mtm"),
                        "serial_nbr": self._safe_str(row, "serial_nbr"),
                        "stationname": self._safe_str(row, "stationname"),
                        "station_id": int(row["station_id"]) if pd.notna(row.get("station_id")) else None,
                        "data_source": self._safe_str(row, "data_source"),
                        "lastsln": self._safe_str(row, "lastsln"),
                        "failure_code": self._safe_str(row, "failure_code"),
                        "fault_category": self._safe_str(row, "fault_category"),
                        "mach_desc": self._safe_str(row, "mach_desc"),
                        "problem_descr": self._safe_str(row, "problem_descr"),
                        "problem_descr_by_tech": self._safe_str(row, "problem_descr_by_tech"),
                        "commodity": self._safe_str(row, "commodity"),
                        "down_part_code": self._safe_str(row, "down_part_code"),
                        "part_nbr": self._safe_str(row, "part_nbr"),
                        "part_desc": self._safe_str(row, "part_desc"),
                        "part_supplier": self._safe_str(row, "part_supplier"),
                        "part_barcode": self._safe_str(row, "part_barcode"),
                        "packing_lot_no": self._safe_str(row, "packing_lot_no"),
                        "claim_item_nbr": self._safe_str(row, "claim_item_nbr"),
                        "claim_status": self._safe_str(row, "claim_status"),
                        "channel": self._safe_str(row, "channel"),
                        "cust_nbr": self._safe_str(row, "cust_nbr")
                    })
                
                if records:
                    stmt = mysql_insert(FactRaDetail).values(records)
                    update_dict = {c.name: stmt.inserted[c.name] for c in FactRaDetail.__table__.columns if c.name not in ['claim_nbr', 'load_ts']}
                    stmt = stmt.on_duplicate_key_update(**update_dict)
                    self.db.execute(stmt)
                    self.db.commit()
                
                rows_processed += len(records)
                logger.info(f"[RA DETAIL] 进度: {rows_processed}/{total}")
            
            task.ra_detail_status = "completed"
            task.ra_detail_rows = rows_processed
            logger.info(f"[RA DETAIL] 完成, 插入/更新: {rows_processed} 行")
            
        except Exception as e:
            logger.error(f"[RA DETAIL] 处理失败: {str(e)}", exc_info=True)
            task.ra_detail_status = "failed"
            raise Exception(f"RA DETAIL处理失败: {str(e)}")
    
    # ==================== ODM映射表刷新 ====================
    
    def _refresh_odm_mapping(self):
        """从ROW表刷新ODM到Plant映射"""
        # IFIR映射
        ifir_mappings = self.db.query(
            FactIfirRow.supplier_new,
            FactIfirRow.plant
        ).filter(
            FactIfirRow.supplier_new.isnot(None),
            FactIfirRow.plant.isnot(None)
        ).distinct().all()
        
        for odm, plant in ifir_mappings:
            odm = odm.strip() if odm else "None"
            plant = plant.strip() if plant else ""
            if plant:
                mapping = MapOdmToPlant(
                    kpi_type="IFIR",
                    supplier_new=odm,
                    plant=plant
                )
                self.db.merge(mapping)
        
        # RA映射
        ra_mappings = self.db.query(
            FactRaRow.supplier_new,
            FactRaRow.plant
        ).filter(
            FactRaRow.supplier_new.isnot(None),
            FactRaRow.plant.isnot(None)
        ).distinct().all()
        
        for odm, plant in ra_mappings:
            odm = odm.strip() if odm else "None"
            plant = plant.strip() if plant else ""
            if plant:
                mapping = MapOdmToPlant(
                    kpi_type="RA",
                    supplier_new=odm,
                    plant=plant
                )
                self.db.merge(mapping)
        
        self.db.commit()
    
    # ==================== 工具方法 ====================
    
    def _safe_get(self, row, key):
        """安全获取值，将 nan 转换为 None"""
        val = row.get(key)
        if pd.isna(val):
            return None
        return val
    
    def _safe_str(self, row, key):
        """安全获取字符串值"""
        val = row.get(key)
        if pd.isna(val):
            return None
        return str(val).strip() if val else None
    
    def _norm_text(self, x) -> str:
        if pd.isna(x):
            return "None"
        return str(x).strip()
    
    def _norm_int(self, x) -> str:
        if pd.isna(x) or x == "":
            return "None"
        return str(int(float(x)))
    
    def _norm_date(self, x) -> str:
        if pd.isna(x):
            return "None"
        return pd.to_datetime(x).date().isoformat()
