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
    """飞书 API 客户端（支持 Token 自动刷新）"""
    
    def __init__(self):
        self.base_url = config.get('feishu.base_url', 'https://open.feishu.cn')
        self.app_id = config.feishu_app_id
        self.app_secret = config.feishu_app_secret
        
        # 从凭证文件加载 Token
        self._user_access_token = config.get_credential('feishu.user_access_token')
        self._refresh_token = config.get_credential('feishu.refresh_token')
        
        # Token 过期时间
        self._user_token_expire_at: float = 0
        self._tenant_token: Optional[str] = None
        self._tenant_token_expire_at: float = 0
    
    def _get_tenant_token(self) -> str:
        """获取 Tenant Access Token（自动刷新）"""
        if self._tenant_token and time.time() < self._tenant_token_expire_at:
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
        self._tenant_token_expire_at = time.time() + expire_seconds - buffer
        
        logger.info(f"Got new tenant access token, expires in {expire_seconds}s")
        return self._tenant_token
    
    def _refresh_user_token(self) -> str:
        """使用 Refresh Token 刷新 User Access Token"""
        if not self._refresh_token:
            raise Exception("Refresh token not configured. Please re-authorize.")
        
        url = f"{self.base_url}/open-apis/authen/v2/oauth/refresh_token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "refresh_token": self._refresh_token
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('code') != 0:
            # Refresh Token 也过期了，需要重新授权
            if data.get('code') == 20037:  # Refresh Token 过期
                logger.error("Refresh token expired. Please re-authorize.")
                raise Exception("Refresh token expired. Please re-authorize via OAuth flow.")
            raise Exception(f"Failed to refresh user token: {data}")
        
        # 更新 Token
        self._user_access_token = data['access_token']
        self._refresh_token = data['refresh_token']  # Refresh Token 也会更新
        
        # 更新凭证文件
        self._save_credentials()
        
        # 设置过期时间
        expire_seconds = data.get('expires_in', 7200)
        buffer = config.get('feishu.token_expire_buffer', 300)
        self._user_token_expire_at = time.time() + expire_seconds - buffer
        
        logger.info(f"Refreshed user access token, expires in {expire_seconds}s")
        return self._user_access_token
    
    def _get_user_token(self) -> str:
        """获取 User Access Token（自动刷新）"""
        # 检查是否需要刷新
        if not self._user_access_token or time.time() >= self._user_token_expire_at:
            logger.info("User access token expired or missing, attempting to refresh...")
            return self._refresh_user_token()
        
        return self._user_access_token
    
    def _save_credentials(self):
        """保存更新后的凭证到文件"""
        import yaml
        
        creds_file = config.config_dir / ".credentials"
        if creds_file.exists():
            with open(creds_file, 'r', encoding='utf-8') as f:
                creds = yaml.safe_load(f) or {}
            
            # 更新 Token
            if 'feishu' not in creds:
                creds['feishu'] = {}
            creds['feishu']['user_access_token'] = self._user_access_token
            creds['feishu']['refresh_token'] = self._refresh_token
            
            # 保存回文件
            with open(creds_file, 'w', encoding='utf-8') as f:
                yaml.dump(creds, f, allow_unicode=True, default_flow_style=False)
            
            logger.info("Credentials updated successfully")
    
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
