#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理器"""
    
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 配置文件路径（src/ 的上一级目录）
        self.config_dir = Path(__file__).parent.parent
        self.config_file = self.config_dir / "config.yaml"
        self.credentials_file = self.config_dir / ".credentials"
        
        # 加载配置
        self.config: Dict[str, Any] = {}
        self.credentials: Dict[str, Any] = {}
        self._load()
        
        self._initialized = True
    
    def _load(self):
        """加载配置文件"""
        # 加载主配置
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        
        # 加载凭证
        if self.credentials_file.exists():
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                self.credentials = yaml.safe_load(f) or {}
    
    def reload(self):
        """重新加载配置"""
        self._load()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点分隔的路径）"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_credential(self, key: str, default: Any = None) -> Any:
        """获取凭证值"""
        keys = key.split('.')
        value = self.credentials
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def feishu_app_id(self) -> str:
        return self.get_credential('feishu.app_id', '')
    
    @property
    def feishu_app_secret(self) -> str:
        return self.get_credential('feishu.app_secret', '')
    
    @property
    def git_remote_url(self) -> str:
        return self.get_credential('git.remote_url', '')
    
    @property
    def git_token(self) -> str:
        return self.get_credential('git.token', '')
    
    @property
    def chroma_persist_dir(self) -> Path:
        return self.config_dir / self.get('chromadb.persist_directory', './vector_db')
    
    @property
    def archive_dir(self) -> Path:
        return self.config_dir / self.get('storage.archive_directory', './archive')
    
    @property
    def backup_dir(self) -> Path:
        return self.config_dir / self.get('storage.backup_directory', './backup')
    
    @property
    def logs_dir(self) -> Path:
        return self.config_dir / self.get('storage.logs_directory', './logs')
    
    def ensure_directories(self):
        """确保所有目录存在"""
        for directory in [
            self.chroma_persist_dir,
            self.archive_dir,
            self.backup_dir,
            self.logs_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# 全局配置实例
config = Config()
