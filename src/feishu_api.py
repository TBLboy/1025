#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书 API 封装模块
"""

import time
import requests
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from config import config


logger = logging.getLogger(__name__)


class FeishuAPI:
    """飞书 API 客户端"""
    
    def __init__(self):
        self.base_url = config.get('feishu.base_url', 'https://open.feishu.cn')
        self.app_id = config.feishu_app_id
        self.app_secret = config.feishu_app_secret
        self.user_access_token = config.get_credential('feishu.user_access_token')
        
        self._tenant_token: Optional[str] = None
        self._token_expire_at: float = 0
    
    def _get_tenant_token(self) -> str:
        """获取 Tenant Access Token（自动刷新）"""
        if self._tenant_token and time.time() < self._token_expire_at:
            return self._tenant_token
        
        # 获取新 token
        url = f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('code') != 0:
            raise Exception(f"Failed to get tenant token: {data}")
        
        self._tenant_token = data['tenant_access_token']
        expire_seconds = data.get('expire', 7200)
        buffer = config.get('feishu.token_expire_buffer', 300)
        self._token_expire_at = time.time() + expire_seconds - buffer
        
        logger.info(f"Got new tenant access token, expires in {expire_seconds}s")
        return self._tenant_token
    
    def _get_user_token(self) -> str:
        """获取 User Access Token"""
        if self.user_access_token:
            return self.user_access_token
        raise Exception("User access token not configured")
    
    def _request(self, method: str, endpoint: str, use_user_token: bool = False, **kwargs) -> Dict[str, Any]:
        """通用请求方法"""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})
        
        # 选择 Token 类型
        if use_user_token:
            headers['Authorization'] = f"Bearer {self._get_user_token()}"
        else:
            headers['Authorization'] = f"Bearer {self._get_tenant_token()}"
        
        headers['Content-Type'] = 'application/json'
        
        response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            result = self._request('GET', f'/open-apis/contact/v3/users/{user_id}')
            return result.get('data')
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    def get_chat_list(self, user_id: Optional[str] = None, page_size: int = 50) -> List[Dict[str, Any]]:
        """获取会话列表"""
        chats = []
        page_token = None
        
        while True:
            params = {'page_size': page_size}
            if page_token:
                params['page_token'] = page_token
            
            result = self._request('GET', '/open-apis/im/v1/chats', params=params)
            
            if result.get('code') != 0:
                logger.error(f"Failed to get chat list: {result}")
                break
            
            items = result.get('data', {}).get('items', [])
            chats.extend(items)
            
            page_token = result.get('data', {}).get('page_token')
            if not page_token:
                break
        
        return chats
    
    def get_messages(self, chat_id: str, start_time: Optional[datetime] = None, 
                     end_time: Optional[datetime] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取消息列表"""
        messages = []
        page_token = None
        
        # Feishu API v1 获取消息的正确参数
        params = {
            'container_id_type': 'chat_id',
            'container_id': chat_id,
            'page_size': min(limit, 50)  # 最大 50
        }
        
        if start_time:
            params['start_time'] = int(start_time.timestamp() * 1000)  # 毫秒
        if end_time:
            params['end_time'] = int(end_time.timestamp() * 1000)
        
        while True:
            if page_token:
                params['page_token'] = page_token
            
            result = self._request('GET', '/open-apis/im/v1/messages', params=params)
            
            if result.get('code') != 0:
                logger.error(f"Failed to get messages: {result}")
                break
            
            items = result.get('data', {}).get('items', [])
            messages.extend(items)
            
            page_token = result.get('data', {}).get('page_token')
            if not page_token or len(items) < limit:
                break
        
        return messages
    
    def get_chat_messages(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取聊天消息（简化版本）"""
        messages = []
        page_token = None
        
        params = {
            'container_id_type': 'chat',
            'container_id': chat_id,
            'page_size': min(limit, 50)
        }
        
        try:
            while True:
                if page_token:
                    params['page_token'] = page_token
                
                # 使用 User Access Token 获取消息
                result = self._request('GET', '/open-apis/im/v1/messages', use_user_token=True, params=params)
                
                if result.get('code') != 0:
                    logger.error(f"Failed to get messages: {result}")
                    break
                
                items = result.get('data', {}).get('items', [])
                messages.extend(items)
                
                page_token = result.get('data', {}).get('page_token')
                if not page_token or len(items) < 50:
                    break
            
            return messages[-limit:] if len(messages) > limit else messages
            
        except Exception as e:
            logger.error(f"Get chat messages error: {e}")
            return []
    
    def get_recent_messages(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近消息（简化版）"""
        return self.get_messages(chat_id, limit=limit)


# 全局 API 实例
feishu_api = FeishuAPI()
