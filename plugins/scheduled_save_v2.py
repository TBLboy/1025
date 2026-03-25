#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时保存对话脚本 v2

每 30 分钟自动保存：
1. 哥哥和我的私聊消息（从 OpenClaw 会话历史读取）
2. 家庭群聊"秘密花园"的消息（从飞书 API 读取）

运行方式：
python3 scheduled_save_v2.py

或者添加到 crontab：
*/30 * * * * cd /path/to/plugins && python3 scheduled_save_v2.py >> logs/scheduled_save.log 2>&1
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
from feishu_api import feishu_api

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

# 配置：群聊信息（支持多个群聊）
GROUP_CHATS = [
    {
        'chat_id': 'oc_6ca477feac7842bef1e83daa8a649e70',
        'name': '秘密花园',
        'members': ['哥哥', '姐姐', '纳西妲']
    },
    {
        'chat_id': 'oc_c0f815e6f427fef6dd9a4d44311805ce',
        'name': '实验室群聊',
        'members': ['群友们', '纳西妲']
    }
]

# 配置：哥哥的 User ID
BROTHER_USER_ID = 'ou_ce3ee0995da167ac887b8ef308e2a388'


def get_recent_conversations(hours=1, limit=50):
    """
    获取最近 N 小时的私聊对话
    
    从 OpenClaw 会话历史中读取最近的对话。
    """
    conversations = []
    
    sessions_dir = Path.home() / '.openclaw' / 'agents' / 'personal-assistant' / 'sessions'
    
    if not sessions_dir.exists():
        logger.warning(f"会话目录不存在：{sessions_dir}")
        return conversations
    
    try:
        session_files = list(sessions_dir.glob('*.jsonl'))
        session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for session_file in session_files[:10]:
            file_mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
            
            if file_mtime < cutoff_time:
                continue
            
            with open(session_file, 'r', encoding='utf-8') as f:
                user_msg = None
                user_timestamp = None
                
                for line in f:
                    try:
                        entry = json.loads(line)
                        msg_type = entry.get('type', '')
                        message_obj = entry.get('message', {})
                        
                        if msg_type == 'message':
                            role = message_obj.get('role', '')
                            
                            if role == 'user':
                                content_obj = message_obj.get('content', [])
                                user_msg = ''
                                for item in content_obj:
                                    if item.get('type') == 'text':
                                        user_msg += item.get('text', '')
                                user_timestamp = message_obj.get('timestamp', entry.get('timestamp', file_mtime.isoformat()))
                            
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
                                        'session_id': session_file.stem,
                                        'source': 'private_chat'
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
        
        logger.info(f"获取到 {len(conversations)} 条私聊对话")
        
    except Exception as e:
        logger.error(f"读取会话历史失败：{e}")
    
    return conversations


def get_group_messages(hours=1, limit=50):
    """
    获取最近 N 小时的群聊消息（支持多个群聊）
    
    从飞书 API 读取群聊消息。
    """
    all_messages = []
    
    try:
        # 遍历所有配置的群聊
        for group in GROUP_CHATS:
            chat_id = group['chat_id']
            chat_name = group['name']
            
            logger.info(f"正在获取群聊消息：{chat_name} ({chat_id})")
            
            # 获取群聊消息
            chat_messages = feishu_api.get_chat_messages(chat_id, limit=limit)
            
            logger.info(f"从飞书 API 获取到 {len(chat_messages)} 条群聊消息 [{chat_name}]")
            
            for msg in chat_messages:
                msg_id = msg.get('message_id', '')
                msg_type = msg.get('message_type', '')
                create_time = msg.get('create_time', '')
                
                # 跳过非文本消息
                if msg_type != 'text':
                    continue
                
                # 解析消息内容
                content_obj = json.loads(msg.get('content', '{}'))
                text_content = content_obj.get('text', '')
                
                if not text_content.strip():
                    continue
                
                # 获取发送者信息
                sender_id = msg.get('sender_id', '')
                sender_type = msg.get('sender_type', '')
                
                # 判断发送者身份
                if sender_id == BROTHER_USER_ID:
                    sender_name = '哥哥'
                elif sender_type == 'user':
                    sender_name = f'user_{sender_id[:8]}'
                else:
                    sender_name = f'{sender_type}_{sender_id[:8]}'
                
                all_messages.append({
                    'message_id': msg_id,
                    'content': text_content.strip(),
                    'sender': sender_name,
                    'sender_id': sender_id,
                    'timestamp': create_time,
                    'source': 'group_chat',
                    'chat_name': chat_name,
                    'chat_id': chat_id
                })
            
            logger.info(f"过滤后得到 {len([m for m in all_messages if m.get('chat_id') == chat_id])} 条有效群聊消息 [{chat_name}]")
        
        logger.info(f"所有群聊共计 {len(all_messages)} 条有效消息")
        
    except Exception as e:
        logger.error(f"获取群聊消息失败：{e}")
        all_messages = []
    
    return all_messages


def save_private_conversations(conversations):
    """保存私聊对话到向量库"""
    saved_count = 0
    
    for conv in conversations:
        try:
            timestamp = conv.get('timestamp', datetime.now().isoformat())
            session_id = conv.get('session_id', 'unknown')
            
            # 保存用户消息
            archiver.store_message({
                'message_id': f'session_{session_id}_user_{timestamp}',
                'content': conv['user_message'],
                'sender': '哥哥',
                'timestamp': timestamp,
                'source_type': 'private_chat',
                'metadata': {
                    'session_id': session_id,
                    'saved_by': 'scheduled_save_v2',
                    'chat_type': 'private'
                }
            })
            
            # 保存助手回复
            archiver.store_message({
                'message_id': f'session_{session_id}_assistant_{timestamp}',
                'content': conv['assistant_reply'],
                'sender': '纳西妲',
                'timestamp': timestamp,
                'source_type': 'private_chat',
                'metadata': {
                    'session_id': session_id,
                    'saved_by': 'scheduled_save_v2',
                    'chat_type': 'private'
                }
            })
            
            saved_count += 1
            
        except Exception as e:
            logger.error(f"保存私聊对话失败：{e}")
    
    logger.info(f"保存了 {saved_count} 条私聊对话")
    return saved_count


def save_group_messages(messages):
    """保存群聊消息到向量库"""
    saved_count = 0
    
    for msg in messages:
        try:
            archiver.store_message({
                'message_id': f"group_{msg['message_id']}",
                'content': msg['content'],
                'sender': msg['sender'],
                'timestamp': msg['timestamp'],
                'source_type': 'group_chat',
                'metadata': {
                    'chat_id': msg.get('chat_id', 'unknown'),
                    'chat_name': msg.get('chat_name', 'unknown'),
                    'sender_id': msg['sender_id'],
                    'saved_by': 'scheduled_save_v2',
                    'chat_type': 'group'
                }
            })
            
            saved_count += 1
            
        except Exception as e:
            logger.error(f"保存群聊消息失败：{e}")
    
    logger.info(f"保存了 {saved_count} 条群聊消息")
    return saved_count


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("定时保存任务 v2 启动")
    logger.info(f"配置群聊数：{len(GROUP_CHATS)}")
    for group in GROUP_CHATS:
        logger.info(f"  - {group['name']} ({group['chat_id']})")
    logger.info("=" * 60)
    
    total_saved = 0
    
    # 1. 保存私聊对话
    logger.info("正在获取私聊对话...")
    private_conversations = get_recent_conversations(hours=1, limit=50)
    if private_conversations:
        total_saved += save_private_conversations(private_conversations)
    else:
        logger.info("没有新的私聊对话需要保存")
    
    # 2. 保存群聊消息
    logger.info("正在获取群聊消息...")
    group_messages = get_group_messages(hours=1, limit=50)
    if group_messages:
        total_saved += save_group_messages(group_messages)
    else:
        logger.info("没有新的群聊消息需要保存")
    
    # 显示统计信息
    stats = archiver.get_collection_stats()
    logger.info(f"当前向量库统计:")
    logger.info(f"  总消息数：{stats['total_count']}")
    logger.info(f"  最后存储：{stats['last_storage_at']}")
    
    logger.info("=" * 60)
    logger.info(f"✅ 完成！共保存了 {total_saved} 条消息")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
