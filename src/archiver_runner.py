#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆归档主脚本
每分钟执行一次，检查并存储新消息

使用方法：
    python3 src/archiver_runner.py
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from archiver import archiver
from message_fetcher import init_fetcher


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
        
        # 完成
        stats = archiver.get_collection_stats()
        logger.info(f"Updated stats: {stats}")
        logger.info("Archiver run completed")
        
    except Exception as e:
        logger.error(f"Archiver failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
