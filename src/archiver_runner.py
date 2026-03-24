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
        
        # 这里可以添加从 Feishu API 获取新消息的逻辑
        # 目前先作为框架占位
        
        logger.info("Archiver run completed")
        
    except Exception as e:
        logger.error(f"Archiver failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
