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
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """通用请求方法"""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})
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
        
        params = {
            'container_id_type': 'chat_id',
            'container_id': chat_id,
            'msg_type': 'all',
            'page_size': limit
        }
        
        if start_time:
            params['start_time'] = int(start_time.timestamp())
        if end_time:
            params['end_time'] = int(end_time.timestamp())
        
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
    
    def get_recent_messages(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近消息（简化版）"""
        return self.get_messages(chat_id, limit=limit)


# 全局 API 实例
feishu_api = FeishuAPI()
