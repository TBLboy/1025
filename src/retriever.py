#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆检索模块
负责从 ChromaDB 中检索相关记忆
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from config import config


logger = logging.getLogger(__name__)


class MemoryRetriever:
    """记忆检索器"""
    
    def __init__(self):
        # 初始化 ChromaDB
        self.chroma_dir = config.chroma_persist_dir
        self.collection_name = config.get('chromadb.collection_name', 'memory_collection')
        
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_collection(self.collection_name)
        
        # 检索配置
        self.default_top_k = config.get('retrieval.default_top_k', 10)
        self.time_filter_enabled = config.get('retrieval.time_filter_enabled', True)
    
    def search(self, query: str, top_k: Optional[int] = None,
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        语义搜索记忆
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filters: 过滤条件（如日期、发送者等）
        
        Returns:
            匹配的记忆列表
        """
        if top_k is None:
            top_k = self.default_top_k
        
        # 构建 where 条件
        where = None
        if filters:
            where = self._build_where(filters)
        
        # 执行搜索
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 格式化结果
            memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    memory = {
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_time(self, date: str, query: Optional[str] = None,
                       top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        按日期搜索记忆
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)
            query: 可选的语义搜索词
            top_k: 返回结果数量
        
        Returns:
            匹配的记忆列表
        """
        filters = {'date': date}
        
        if query:
            # 语义搜索 + 时间过滤
            return self.search(query, top_k=top_k, filters=filters)
        else:
            # 仅时间过滤（需要获取所有该日期的记忆）
            return self.get_by_date(date, limit=top_k)
    
    def get_by_date(self, date: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取指定日期的所有记忆"""
        try:
            # ChromaDB 的 where 条件支持有限，这里用简单过滤
            results = self.collection.get(
                where={'date': date},
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            memories = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    memory = {
                        'content': doc,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {},
                        'id': results['ids'][i] if results['ids'] else None
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Get by date failed: {e}")
            return []
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的记忆"""
        try:
            results = self.collection.get(
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            memories = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    memory = {
                        'content': doc,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {},
                        'id': results['ids'][i] if results['ids'] else None
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Get recent failed: {e}")
            return []
    
    def _build_where(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """构建 ChromaDB where 条件"""
        # 简单实现，只支持等值过滤
        where = {}
        for key, value in filters.items():
            if key == 'date':
                # 日期过滤需要特殊处理 timestamp 字段
                where['timestamp'] = {'$gte': f"{value}T00:00:00"}
            else:
                where[key] = value
        return where


# 全局检索器实例
retriever = MemoryRetriever()


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    # 测试搜索
    results = retriever.search("测试", top_k=5)
    print(f"Found {len(results)} memories")
    for mem in results:
        print(f"  - {mem['content'][:50]}...")
