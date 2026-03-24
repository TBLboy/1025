#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆归档核心模块
负责将消息存储到 ChromaDB 向量数据库
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import config


logger = logging.getLogger(__name__)


class MemoryArchiver:
    """记忆归档器"""
    
    def __init__(self):
        # 初始化 ChromaDB
        self.chroma_dir = config.chroma_persist_dir
        self.collection_name = config.get('chromadb.collection_name', 'memory_collection')
        
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Memory collection for chat messages"}
        )
        
        # 初始化嵌入模型（懒加载）
        self._embedding_model: Optional[SentenceTransformer] = None
        
        # 状态文件
        self.state_file = config.config_dir / "state.json"
        self.state = self._load_state()
    
    @property
    def embedding_model(self) -> SentenceTransformer:
        """懒加载嵌入模型"""
        if self._embedding_model is None:
            model_name = config.get('embedding.model_name', 'BAAI/bge-m3')
            logger.info(f"Loading embedding model: {model_name}")
            # 设置 HuggingFace 镜像源
            import os
            os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
            self._embedding_model = SentenceTransformer(model_name)
        return self._embedding_model
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态文件"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'last_storage_at': None,
            'last_message_id': None,
            'total_messages_stored': 0,
            'stored_message_ids': []
        }
    
    def _save_state(self):
        """保存状态文件"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def _compute_embedding(self, text: str) -> List[float]:
        """计算文本向量"""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _generate_id(self, message: Dict[str, Any]) -> str:
        """生成消息 ID（用于 ChromaDB）"""
        # 优先使用 message_id
        if 'message_id' in message:
            return message['message_id']
        
        # 否则生成哈希 ID
        content = json.dumps(message, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_already_stored(self, message_id: str) -> bool:
        """检查消息是否已存储"""
        return message_id in self.state.get('stored_message_ids', [])
    
    def store_message(self, message: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        存储单条消息到向量数据库
        
        Args:
            message: 消息内容，包含 content, sender, timestamp 等
            metadata: 额外元数据
        
        Returns:
            bool: 是否成功存储
        """
        message_id = self._generate_id(message)
        
        # 检查是否已存储
        if self._is_already_stored(message_id):
            logger.debug(f"Message {message_id} already stored, skipping")
            return False
        
        # 准备数据
        content = message.get('content', '')
        if not content:
            logger.warning(f"Empty content for message {message_id}")
            return False
        
        # 计算向量
        try:
            embedding = self._compute_embedding(content)
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            return False
        
        # 构建元数据
        full_metadata = {
            'message_id': message_id,
            'sender': message.get('sender', 'unknown'),
            'timestamp': message.get('timestamp', datetime.now().isoformat()),
            'stored_at': datetime.now().isoformat(),
            'source_type': message.get('source_type', 'chat'),
            **message.get('metadata', {}),
            **(metadata or {})
        }
        
        # 存储到 ChromaDB
        try:
            self.collection.add(
                ids=[message_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[full_metadata]
            )
            
            # 更新状态
            if 'stored_message_ids' not in self.state:
                self.state['stored_message_ids'] = []
            self.state['stored_message_ids'].append(message_id)
            self.state['last_storage_at'] = datetime.now().isoformat()
            self.state['last_message_id'] = message_id
            self.state['total_messages_stored'] = self.state.get('total_messages_stored', 0) + 1
            self._save_state()
            
            logger.info(f"Stored message {message_id} from {full_metadata['sender']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            return False
    
    def store_messages_batch(self, messages: List[Dict[str, Any]]) -> int:
        """批量存储消息"""
        count = 0
        for message in messages:
            if self.store_message(message):
                count += 1
        return count
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        return {
            'total_count': self.collection.count(),
            'last_storage_at': self.state.get('last_storage_at'),
            'total_messages_stored': self.state.get('total_messages_stored', 0)
        }


# 全局归档器实例
archiver = MemoryArchiver()


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    # 测试存储
    test_message = {
        'message_id': 'test_001',
        'content': '这是一条测试消息',
        'sender': 'user',
        'timestamp': datetime.now().isoformat()
    }
    
    result = archiver.store_message(test_message)
    print(f"Store result: {result}")
    print(f"Stats: {archiver.get_collection_stats()}")
