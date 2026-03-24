#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时保存对话脚本

每 30 分钟自动保存最近的对话到向量库。
不需要 User Access Token，直接读取 OpenClaw 会话历史。

运行方式：
python3 scheduled_save.py

或者添加到 crontab：
*/30 * * * * cd /path/to/plugins && python3 scheduled_save.py >> logs/scheduled_save.log 2>&1
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config import config
from archiver import archiver

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'scheduled_save.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ScheduledSave')


def get_recent_conversations(hours=1, limit=50):
    """
    获取最近 N 小时的对话
    
    从 OpenClaw 会话历史中读取最近的对话。
    
    Args:
        hours: 获取最近多少小时的对话
        limit: 最多获取多少条对话
    
    Returns:
        list: 对话列表，每个对话包含 user_message 和 assistant_reply
    """
    conversations = []
    
    # 读取 OpenClaw 会话索引
    sessions_index_file = Path.home() / '.openclaw' / 'agents' / 'personal-assistant' / 'sessions' / 'sessions.json'
    sessions_dir = Path.home() / '.openclaw' / 'agents' / 'personal-assistant' / 'sessions'
    
    if not sessions_dir.exists():
        logger.warning(f"会话目录不存在：{sessions_dir}")
        return conversations
    
    try:
        # 读取会话索引
        session_files = list(sessions_dir.glob('*.jsonl'))
        
        # 按修改时间排序，获取最新的会话文件
        session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for session_file in session_files[:10]:  # 最多检查 10 个文件
            # 检查文件修改时间
            file_mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
            
            if file_mtime < cutoff_time:
                continue
            
            # 读取会话文件
            with open(session_file, 'r', encoding='utf-8') as f:
                user_msg = None
                user_timestamp = None
                
                for line in f:
                    try:
                        entry = json.loads(line)
                        msg_type = entry.get('type', '')
                        message_obj = entry.get('message', {})
                        
                        # 检查是否是消息
                        if msg_type == 'message':
                            role = message_obj.get('role', '')
                            
                            # 用户消息
                            if role == 'user':
                                content_obj = message_obj.get('content', [])
                                user_msg = ''
                                for item in content_obj:
                                    if item.get('type') == 'text':
                                        user_msg += item.get('text', '')
                                user_timestamp = message_obj.get('timestamp', entry.get('timestamp', file_mtime.isoformat()))
                            
                            # 助手回复
                            elif role == 'assistant' and user_msg:
                                content_obj = message_obj.get('content', [])
                                assistant_reply = ''
                                for item in content_obj:
                                    if item.get('type') == 'text':
                                        assistant_reply += item.get('text', '')
                                
                                if assistant_reply.strip():
                                    conversations.append({
                                        'user_message': user_msg.strip(),
                                        'assistant_reply': assistant_reply.strip(),
                                        'timestamp': user_timestamp,
                                        'session_id': session_file.stem
                                    })
                                    user_msg = None
                                    user_timestamp = None
                                    
                                    if len(conversations) >= limit:
                                        break
                    except Exception as e:
                        logger.debug(f"解析行失败：{e}")
                        continue
            
            if len(conversations) >= limit:
                break
        
        logger.info(f"获取到 {len(conversations)} 条最近对话")
        
    except Exception as e:
        logger.error(f"读取会话历史失败：{e}")
    
    return conversations


def save_conversations(conversations):
    """
    保存对话到向量库
    
    Args:
        conversations: 对话列表
    """
    saved_count = 0
    
    for conv in conversations:
        try:
            timestamp = conv.get('timestamp', datetime.now().isoformat())
            session_id = conv.get('session_id', 'unknown')
            
            # 保存用户消息
            archiver.store_message({
                'message_id': f'session_{session_id}_user_{timestamp}',
                'content': conv['user_message'],
                'sender': 'user',
                'timestamp': timestamp,
                'source_type': 'chat',
                'metadata': {
                    'session_id': session_id,
                    'saved_by': 'scheduled_save'
                }
            })
            
            # 保存助手回复
            archiver.store_message({
                'message_id': f'session_{session_id}_assistant_{timestamp}',
                'content': conv['assistant_reply'],
                'sender': 'assistant',
                'timestamp': timestamp,
                'source_type': 'chat',
                'metadata': {
                    'session_id': session_id,
                    'saved_by': 'scheduled_save'
                }
            })
            
            saved_count += 1
            
        except Exception as e:
            logger.error(f"保存对话失败：{e}")
    
    logger.info(f"保存了 {saved_count} 条对话")
    return saved_count


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("定时保存任务启动")
    logger.info("=" * 60)
    
    # 获取最近 1 小时的对话（最多 50 条）
    conversations = get_recent_conversations(hours=1, limit=50)
    
    if not conversations:
        logger.info("没有新的对话需要保存")
        return
    
    # 保存对话
    saved_count = save_conversations(conversations)
    
    # 显示统计信息
    stats = archiver.get_collection_stats()
    logger.info(f"当前向量库统计:")
    logger.info(f"  总消息数：{stats['total_count']}")
    logger.info(f"  最后存储：{stats['last_storage_at']}")
    
    logger.info("=" * 60)
    logger.info(f"✅ 完成！保存了 {saved_count} 条对话")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
