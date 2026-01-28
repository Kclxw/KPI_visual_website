"""
文件上传相关Schema
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class FileInfo(BaseModel):
    """文件信息"""
    filename: str
    status: str = "pending"
    rows: Optional[int] = None
    error: Optional[str] = None


class UploadTaskCreate(BaseModel):
    """创建上传任务"""
    ifir_detail_file: Optional[str] = None
    ifir_row_file: Optional[str] = None
    ra_detail_file: Optional[str] = None
    ra_row_file: Optional[str] = None


class UploadTaskStatus(BaseModel):
    """上传任务状态"""
    task_id: str
    status: str
    progress: int
    
    ifir_detail: Optional[FileInfo] = None
    ifir_row: Optional[FileInfo] = None
    ra_detail: Optional[FileInfo] = None
    ra_row: Optional[FileInfo] = None
    
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class UploadResponse(BaseModel):
    """上传响应"""
    code: int = 0
    message: str = "success"
    data: Optional[UploadTaskStatus] = None
