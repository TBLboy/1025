#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日备份脚本
每天凌晨执行，生成每日摘要并归档
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from config import config
from archiver import archiver
from retriever import retriever


logger = logging.getLogger(__name__)


class DailyBackup:
    """每日备份管理器"""
    
    def __init__(self):
        self.archive_dir = config.archive_dir
        self.backup_dir = config.backup_dir
        self.logs_dir = config.logs_dir
    
    def get_today_messages(self) -> List[Dict[str, Any]]:
        """获取今天的消息"""
        today = datetime.now().strftime('%Y-%m-%d')
        return retriever.get_by_date(today)
    
    def generate_daily_summary(self, messages: List[Dict[str, Any]]) -> str:
        """生成每日摘要"""
        if not messages:
            return "# 每日记忆摘要\n\n今日没有新记忆。\n"
        
        date = datetime.now().strftime('%Y-%m-%d')
        
        # 按发送者分组
        user_messages = [m for m in messages if m['metadata'].get('sender') == 'user']
        assistant_messages = [m for m in messages if m['metadata'].get('sender') == 'assistant']
        
        summary = f"# 每日记忆摘要 - {date}\n\n"
        summary += f"## 统计\n\n"
        summary += f"- 总消息数：{len(messages)}\n"
        summary += f"- 用户消息：{len(user_messages)}\n"
        summary += f"- 助手回复：{len(assistant_messages)}\n\n"
        
        summary += f"## 今日话题\n\n"
        
        # 提取关键话题（简单实现：取前 10 条）
        for i, msg in enumerate(messages[:10], 1):
            content = msg['content'][:100] + '...' if len(msg['content']) > 100 else msg['content']
            sender = msg['metadata'].get('sender', 'unknown')
            summary += f"{i}. [{sender}] {content}\n"
        
        summary += f"\n---\n_生成时间：{datetime.now().isoformat()}_\n"
        
        return summary
    
    def backup_to_json(self, messages: List[Dict[str, Any]]) -> Path:
        """备份到 JSON 文件"""
        today = datetime.now().strftime('%Y-%m-%d')
        date_path = self.archive_dir / datetime.now().strftime('%Y') / datetime.now().strftime('%m')
        date_path.mkdir(parents=True, exist_ok=True)
        
        backup_file = date_path / f"{today}.json"
        
        backup_data = {
            'date': today,
            'total_messages': len(messages),
            'backup_at': datetime.now().isoformat(),
            'messages': messages
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Backed up {len(messages)} messages to {backup_file}")
        return backup_file
    
    def save_summary(self, summary: str) -> Path:
        """保存每日摘要"""
        today = datetime.now().strftime('%Y-%m-%d')
        summary_dir = self.backup_dir / 'daily_summary'
        summary_dir.mkdir(parents=True, exist_ok=True)
        
        summary_file = summary_dir / f"{today}.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"Saved daily summary to {summary_file}")
        return summary_file
    
    def update_manifest(self, backup_file: Path, summary_file: Path):
        """更新备份清单"""
        manifest_file = self.backup_dir / 'manifest.json'
        
        if manifest_file.exists():
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        else:
            manifest = {
                'backup_version': '1.0',
                'created_at': datetime.now().isoformat(),
                'last_backup': None,
                'total_backups': 0,
                'backup_files': []
            }
        
        manifest['last_backup'] = datetime.now().isoformat()
        manifest['total_backups'] += 1
        manifest['backup_files'].append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'json_file': str(backup_file),
            'summary_file': str(summary_file),
            'backup_at': datetime.now().isoformat()
        })
        
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    def run(self):
        """执行每日备份"""
        logger.info("Starting daily backup...")
        
        # 获取今日消息
        messages = self.get_today_messages()
        logger.info(f"Found {len(messages)} messages today")
        
        # 生成摘要
        summary = self.generate_daily_summary(messages)
        
        # 备份到 JSON
        backup_file = self.backup_to_json(messages)
        
        # 保存摘要
        summary_file = self.save_summary(summary)
        
        # 更新清单
        self.update_manifest(backup_file, summary_file)
        
        logger.info("Daily backup completed!")
        return {
            'messages_count': len(messages),
            'backup_file': str(backup_file),
            'summary_file': str(summary_file)
        }


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    backup = DailyBackup()
    result = backup.run()
    print(f"Backup result: {result}")
