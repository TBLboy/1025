#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书消息获取模块
负责从 Feishu API 获取聊天记录
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from feishu_api import feishu_api


logger = logging.getLogger(__name__)


class MessageFetcher:
    """消息获取器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.api = feishu_api
        
        # 状态文件路径
        self.state_file = None  # 由外部设置
        
        # 加载状态
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态文件"""
        try:
            from pathlib import Path
            from config import config
            
            state_file = config.config_dir / "fetcher_state.json"
            if state_file.exists():
                import json
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            'last_fetch_time': None,
            'last_message_id': None,
            'total_messages_fetched': 0
        }
    
    def _save_state(self):
        """保存状态文件"""
        try:
            from pathlib import Path
            from config import config
            import json
            
            state_file = config.config_dir / "fetcher_state.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_chat_id(self) -> Optional[str]:
        """获取与指定用户的聊天 ID"""
        try:
            # 获取会话列表
            chats = self.api.get_chat_list(page_size=100)
            
            # 查找包含目标用户的会话
            for chat in chats:
                chat_id = chat.get('chat_id', '')
                # 单聊会话通常包含用户 ID
                if self.user_id in chat_id or chat.get('owner_id') == self.user_id:
                    logger.info(f"Found chat: {chat_id}")
                    return chat_id
            
            # 如果没有找到，尝试使用 user_id 作为 chat_id
            # Feishu 的单聊 chat_id 格式通常是特殊的
            logger.warning(f"Chat not found, trying to use user_id as chat_id")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chat_id: {e}")
            return None
    
    def fetch_messages(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取消息
        
        Args:
            chat_id: 会话 ID
            limit: 每次获取的消息数量
        
        Returns:
            消息列表
        """
        try:
            messages = self.api.get_chat_messages(chat_id, limit=limit)
            
            logger.info(f"Fetched {len(messages)} messages from chat {chat_id}")
            
            # 转换为统一格式
            formatted_messages = []
            for msg in messages:
                # 跳过已存储的消息
                msg_id = msg.get('message_id', '')
                if msg_id == self.state.get('last_message_id'):
                    continue
                
                # 提取消息内容
                content = self._extract_content(msg)
                if not content:
                    continue
                
                # 确定发送者
                sender_id = msg.get('sender_id', '')
                sender = 'user' if sender_id == self.user_id else 'assistant'
                
                # 格式化消息
                formatted = {
                    'message_id': msg_id,
                    'content': content,
                    'sender': sender,
                    'sender_id': sender_id,
                    'timestamp': self._format_timestamp(msg.get('create_time', 0)),
                    'chat_id': chat_id,
                    'source_type': 'feishu_chat'
                }
                formatted_messages.append(formatted)
            
            # 更新状态
            if formatted_messages:
                self.state['last_message_id'] = formatted_messages[-1]['message_id']
                self.state['last_fetch_time'] = datetime.now().isoformat()
                self.state['total_messages_fetched'] = self.state.get('total_messages_fetched', 0) + len(formatted_messages)
                self._save_state()
            
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Failed to fetch messages: {e}")
            return []
    
    def _extract_content(self, msg: Dict[str, Any]) -> str:
        """提取消息内容"""
        msg_type = msg.get('msg_type', 'text')
        
        if msg_type == 'text':
            content_obj = msg.get('content', {})
            if isinstance(content_obj, str):
                import json
                try:
                    content_obj = json.loads(content_obj)
                except:
                    pass
            
            if isinstance(content_obj, dict):
                return content_obj.get('text', '')
            return str(content_obj) if content_obj else ''
        
        elif msg_type == 'post':
            # 富文本消息
            content_obj = msg.get('content', {})
            if isinstance(content_obj, str):
                import json
                try:
                    content_obj = json.loads(content_obj)
                except:
                    return ''
            
            # 提取 post 内容
            content = ''
            if isinstance(content_obj, dict):
                post = content_obj.get('post', {})
                zh_cn = post.get('zh_cn', {})
                for item in zh_cn.get('content', []):
                    if item.get('tag') == 'text':
                        content += item.get('text', '')
            return content
        
        elif msg_type == 'image':
            return '[图片]'
        
        elif msg_type == 'file':
            return '[文件]'
        
        else:
            return f'[{msg_type} 消息]'
    
    def _format_timestamp(self, timestamp: int) -> str:
        """格式化时间戳"""
        if not timestamp:
            return datetime.now().isoformat()
        
        # Feishu 时间戳是毫秒
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()


# 全局消息获取器实例（需要初始化）
fetcher: Optional[MessageFetcher] = None


def init_fetcher(user_id: str) -> MessageFetcher:
    """初始化消息获取器"""
    global fetcher
    fetcher = MessageFetcher(user_id)
    return fetcher


def get_fetcher() -> Optional[MessageFetcher]:
    """获取消息获取器实例"""
    return fetcher
