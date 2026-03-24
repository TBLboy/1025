#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆归档主脚本（集成文件下载功能）
每分钟执行一次，检查并存储新消息，自动下载聊天中的文件

使用方法：
    python3 src/archiver_runner.py
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from archiver import archiver
from message_fetcher import init_fetcher

# 导入文件下载功能
import requests


def setup_logging():
    """配置日志"""
    config.ensure_directories()
    log_file = config.logs_dir / 'archiver.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== Memory Archiver Started ===")
    logger.info(f"Time: {datetime.now().isoformat()}")
    
    try:
        # 获取统计信息
        stats = archiver.get_collection_stats()
        logger.info(f"Current stats: {stats}")
        
        # 从 Feishu API 获取新消息
        user_id = config.get('feishu.user_id', 'ou_ce3ee0995da167ac887b8ef308e2a388')
        logger.info(f"Fetching messages for user: {user_id}")
        
        fetcher = init_fetcher(user_id)
        
        # 获取 chat_id（尝试从配置读取或使用默认值）
        chat_id = config.get('feishu.chat_id', None)
        
        if not chat_id:
            # 尝试获取 chat_id
            chat_id = fetcher.get_chat_id()
            if chat_id:
                logger.info(f"Found chat_id: {chat_id}")
            else:
                logger.warning("Could not find chat_id, skipping message fetch")
                chat_id = None
        
        # 获取并存储消息
        if chat_id:
            messages = fetcher.fetch_messages(chat_id, limit=50)
            logger.info(f"Fetched {len(messages)} new messages")
            
            if messages:
                # 存储消息
                count = archiver.store_messages_batch(messages)
                logger.info(f"Stored {count} messages")
                
                # 下载文件消息
                file_count = download_files_from_messages(messages, chat_id, logger)
                if file_count > 0:
                    logger.info(f"Downloaded {file_count} files")
        
        # 完成
        stats = archiver.get_collection_stats()
        logger.info(f"Updated stats: {stats}")
        logger.info("Archiver run completed")
        
    except Exception as e:
        logger.error(f"Archiver failed: {e}", exc_info=True)
        sys.exit(1)


def download_files_from_messages(messages, chat_id, logger):
    """
    从消息中下载文件
    
    Args:
        messages: 消息列表
        chat_id: 聊天 ID
        logger: 日志对象
    
    Returns:
        下载的文件数量
    """
    # 获取 Tenant Token
    config_obj = config
    app_id = config_obj.feishu_app_id
    app_secret = config_obj.feishu_app_secret
    
    token_url = f"{config_obj.get('feishu.base_url', 'https://open.feishu.cn')}/open-apis/auth/v3/tenant_access_token/internal"
    token_resp = requests.post(token_url, json={
        "app_id": app_id,
        "app_secret": app_secret
    }, timeout=10)
    
    tenant_token = token_resp.json().get('tenant_access_token')
    if not tenant_token:
        logger.error("Failed to get tenant token")
        return 0
    
    # 文件保存目录
    archive_dir = config_obj.config_dir / "archive" / "files"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 下载文件
    file_count = 0
    base_url = config_obj.get('feishu.base_url', 'https://open.feishu.cn')
    
    for msg in messages:
        if msg.get('msg_type') == 'file':
            try:
                msg_id = msg.get('message_id')
                file_info = msg.get('body', {}).get('content', '{}')
                
                if isinstance(file_info, str):
                    file_info = json.loads(file_info)
                
                file_key = file_info.get('file_key')
                file_name = file_info.get('file_name')
                
                if not file_key or not file_name:
                    continue
                
                # 正确的 API 路径和参数
                download_url = f"{base_url}/open-apis/im/v1/messages/{msg_id}/resources/{file_key}"
                params = {"type": "file"}
                headers = {
                    'Authorization': f'Bearer {tenant_token}'
                }
                
                # 下载文件
                resp = requests.get(download_url, headers=headers, params=params, stream=True, timeout=30)
                
                if resp.status_code == 200:
                    # 保存文件
                    save_path = archive_dir / file_name
                    with open(save_path, 'wb') as f:
                        f.write(resp.content)
                    
                    logger.info(f"✅ Downloaded file: {file_name} ({len(resp.content)} bytes)")
                    file_count += 1
                else:
                    logger.warning(f"❌ Failed to download {file_name}: {resp.status_code} - {resp.text[:100]}")
                    
            except Exception as e:
                logger.error(f"Error downloading file: {e}")
    
    return file_count


if __name__ == '__main__':
    main()
