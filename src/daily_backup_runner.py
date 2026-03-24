#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日备份运行脚本
每天凌晨 00:00 执行

使用方法：
    python3 src/daily_backup_runner.py
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from daily_backup import DailyBackup
from sync_git import GitSync


def setup_logging():
    """配置日志"""
    config.ensure_directories()
    log_file = config.logs_dir / 'daily_backup.log'
    
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
    
    logger.info("=== Daily Backup Started ===")
    logger.info(f"Time: {datetime.now().isoformat()}")
    
    try:
        # 执行每日备份
        backup = DailyBackup()
        backup_result = backup.run()
        logger.info(f"Backup completed: {backup_result}")
        
        # 同步到 Git
        sync = GitSync()
        date = datetime.now().strftime('%Y-%m-%d')
        commit_message = f"Daily Backup: {date} - {backup_result['messages_count']} messages"
        
        sync_result = sync.sync(commit_message)
        logger.info(f"Git sync completed: {sync_result}")
        
        logger.info("=== Daily Backup Completed ===")
        
    except Exception as e:
        logger.error(f"Daily backup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
