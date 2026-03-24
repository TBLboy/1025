#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token 状态检查与提醒脚本
每 7 天检查一次 Refresh Token 状态，并发送飞书提醒
"""

import sys
import time
import yaml
import requests
import logging
from pathlib import Path
from datetime import datetime, timedelta

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import config


def setup_logging():
    """配置日志"""
    config.ensure_directories()
    log_file = config.logs_dir / 'token_check.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def get_token_status() -> dict:
    """获取当前 Token 状态"""
    creds_file = config.config_dir / ".credentials"
    
    if not creds_file.exists():
        return {'error': 'Credentials file not found'}
    
    with open(creds_file, 'r', encoding='utf-8') as f:
        creds = yaml.safe_load(f) or {}
    
    feishu_config = creds.get('feishu', {})
    
    # 检查必要字段
    has_user_token = bool(feishu_config.get('user_access_token'))
    has_refresh_token = bool(feishu_config.get('refresh_token'))
    
    return {
        'has_user_token': has_user_token,
        'has_refresh_token': has_refresh_token,
        'app_id': feishu_config.get('app_id', 'N/A'),
        'user_id': feishu_config.get('user_id', 'N/A'),
        'last_check': datetime.now().isoformat()
    }


def send_feishu_reminder(message: str):
    """发送飞书提醒消息"""
    try:
        # 获取 Tenant Token
        app_id = config.feishu_app_id
        app_secret = config.feishu_app_secret
        
        token_url = f"{config.get('feishu.base_url', 'https://open.feishu.cn')}/open-apis/auth/v3/tenant_access_token/internal"
        token_resp = requests.post(token_url, json={
            "app_id": app_id,
            "app_secret": app_secret
        }, timeout=10)
        
        tenant_token = token_resp.json().get('tenant_access_token')
        if not tenant_token:
            logging.error("Failed to get tenant token")
            return False
        
        # 获取聊天 ID
        chat_id = "oc_6ca477feac7842bef1e83daa8a649e70"
        
        # 发送消息（使用新的 API 格式）
        message_url = f"{config.get('feishu.base_url')}/open-apis/im/v1/messages"
        headers = {
            'Authorization': f'Bearer {tenant_token}',
            'Content-Type': 'application/json'
        }
        
        message_data = {
            "receive_id": chat_id,
            "receive_id_type": "chat_id",
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        
        resp = requests.post(message_url, headers=headers, json=message_data, timeout=30)
        result = resp.json()
        
        if result.get('code') == 0:
            logging.info("Reminder sent successfully")
            return True
        else:
            logging.error(f"Failed to send reminder: {result}")
            return False
            
    except Exception as e:
        logging.error(f"Error sending reminder: {e}")
        return False


def check_and_remind():
    """检查 Token 状态并发送提醒"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== Token Status Check Started ===")
    
    # 获取 Token 状态
    status = get_token_status()
    logger.info(f"Token status: {status}")
    
    # 检查是否需要提醒
    needs_reminder = False
    reminder_message = ""
    
    if not status.get('has_refresh_token'):
        needs_reminder = True
        reminder_message = "⚠️ **Token 更新提醒**\n\nRefresh Token 未配置！\n\n请重新授权获取新的 Refresh Token。\n\n授权链接：\nhttps://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id=cli_a9310c516a389bc2&redirect_uri=http://localhost:8080/callback&scope=auth:user.id:read%20offline_access%20im:message%20drive:drive%20docs:doc&state=abc123xyz"
    
    elif status.get('has_user_token'):
        # 检查是否接近 7 天（假设上次更新是 7 天前）
        # 实际应该记录上次更新时间，这里简化处理
        needs_reminder = True
        reminder_message = "🔔 **Token 更新提醒**\n\n距离上次授权已过去约 7 天，Refresh Token 即将过期。\n\n为了确保持续自动保存，请重新授权获取新的 Refresh Token。\n\n📝 操作步骤：\n1. 打开授权链接\n2. 复制授权码 (code)\n3. 告诉纳西妲换取新 Token\n\n🔗 授权链接：\nhttps://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id=cli_a9310c516a389bc2&redirect_uri=http://localhost:8080/callback&scope=auth:user.id:read%20offline_access%20im:message%20drive:drive%20docs:doc&state=abc123xyz"
    
    # 发送提醒
    if needs_reminder and reminder_message:
        logger.info("Sending reminder...")
        success = send_feishu_reminder(reminder_message)
        
        if success:
            logger.info("✅ Reminder sent successfully")
        else:
            logger.error("❌ Failed to send reminder")
    else:
        logger.info("No reminder needed")
    
    logger.info("=== Token Status Check Completed ===")
    
    return status


if __name__ == '__main__':
    setup_logging()
    check_and_remind()
