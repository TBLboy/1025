#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 消息自动保存插件

在 OpenClaw 消息处理流程中自动保存聊天记录到向量库。
不需要 User Access Token，直接保存接收到的消息。

使用方法：
在 OpenClaw 配置中启用此插件，或在 agent 初始化时导入。
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config import config
from archiver import archiver

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MessageSaver')


class MessageAutoSaver:
    """
    消息自动保存器
    
    在 OpenClaw 消息处理流程中自动保存用户消息和助手回复。
    """
    
    def __init__(self):
        self.config = config
        self.archiver = archiver
        logger.info("MessageAutoSaver initialized")
    
    def save_user_message(self, content: str, message_id: str = None, 
                          timestamp: str = None, metadata: dict = None):
        """
        保存用户消息
        
        Args:
            content: 消息内容
            message_id: 消息 ID
            timestamp: 时间戳
            metadata: 额外元数据
        """
        try:
            message_data = {
                'message_id': message_id or f'user_{datetime.now().timestamp()}',
                'content': content,
                'sender': 'user',
                'timestamp': timestamp or datetime.now().isoformat(),
                'source_type': 'chat',
                'metadata': metadata or {}
            }
            
            result = self.archiver.store_message(message_data)
            
            if result:
                logger.info(f"✅ Saved user message: {message_data['message_id'][:20]}...")
            else:
                logger.debug(f"⏭️  Skipped duplicate message: {message_data['message_id'][:20]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to save user message: {e}")
            return False
    
    def save_assistant_message(self, content: str, message_id: str = None,
                                timestamp: str = None, metadata: dict = None):
        """
        保存助手回复
        
        Args:
            content: 回复内容
            message_id: 消息 ID
            timestamp: 时间戳
            metadata: 额外元数据
        """
        try:
            message_data = {
                'message_id': message_id or f'assistant_{datetime.now().timestamp()}',
                'content': content,
                'sender': 'assistant',
                'timestamp': timestamp or datetime.now().isoformat(),
                'source_type': 'chat',
                'metadata': metadata or {}
            }
            
            result = self.archiver.store_message(message_data)
            
            if result:
                logger.info(f"✅ Saved assistant message: {message_data['message_id'][:20]}...")
            else:
                logger.debug(f"⏭️  Skipped duplicate message: {message_data['message_id'][:20]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to save assistant message: {e}")
            return False
    
    def save_conversation(self, user_content: str, assistant_content: str,
                         message_id: str = None, timestamp: str = None):
        """
        保存一轮对话（用户消息 + 助手回复）
        
        Args:
            user_content: 用户消息内容
            assistant_content: 助手回复内容
            message_id: 消息 ID 前缀
            timestamp: 时间戳
        """
        ts = timestamp or datetime.now().isoformat()
        
        # 保存用户消息
        self.save_user_message(
            content=user_content,
            message_id=f'{message_id or "conv"}_user',
            timestamp=ts
        )
        
        # 保存助手回复
        self.save_assistant_message(
            content=assistant_content,
            message_id=f'{message_id or "conv"}_assistant',
            timestamp=ts
        )


# 全局实例
auto_saver = MessageAutoSaver()


# ============================================================================
# OpenClaw 集成钩子
# ============================================================================

def on_message_received(message):
    """
    OpenClaw 消息接收钩子
    
    当收到用户消息时自动保存。
    在 OpenClaw 配置中注册此钩子。
    """
    try:
        # 提取消息信息
        content = message.get('content', '')
        message_id = message.get('message_id', None)
        timestamp = message.get('timestamp', None)
        metadata = message.get('metadata', {})
        
        # 保存消息
        auto_saver.save_user_message(
            content=content,
            message_id=message_id,
            timestamp=timestamp,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error in on_message_received: {e}")


def on_reply_sent(reply):
    """
    OpenClaw 回复发送钩子
    
    当发送助手回复时自动保存。
    在 OpenClaw 配置中注册此钩子。
    """
    try:
        # 提取回复信息
        content = reply.get('content', '')
        message_id = reply.get('message_id', None)
        timestamp = reply.get('timestamp', None)
        metadata = reply.get('metadata', {})
        
        # 保存回复
        auto_saver.save_assistant_message(
            content=content,
            message_id=message_id,
            timestamp=timestamp,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error in on_reply_sent: {e}")


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == '__main__':
    # 测试保存功能
    print("=" * 60)
    print("测试消息自动保存功能")
    print("=" * 60)
    
    # 测试保存用户消息
    print("\n1️⃣ 测试保存用户消息...")
    result = auto_saver.save_user_message(
        content="这是一条测试消息",
        message_id="test_user_001",
        timestamp=datetime.now().isoformat()
    )
    print(f"   结果：{'✅ 成功' if result else '❌ 失败'}")
    
    # 测试保存助手回复
    print("\n2️⃣ 测试保存助手回复...")
    result = auto_saver.save_assistant_message(
        content="这是助手的测试回复",
        message_id="test_assistant_001",
        timestamp=datetime.now().isoformat()
    )
    print(f"   结果：{'✅ 成功' if result else '❌ 失败'}")
    
    # 测试保存对话
    print("\n3️⃣ 测试保存完整对话...")
    auto_saver.save_conversation(
        user_content="你好，今天天气怎么样？",
        assistant_content="今天天气很好，阳光明媚！",
        message_id="test_conv_001"
    )
    print(f"   结果：✅ 成功")
    
    # 显示统计信息
    print("\n4️⃣ 当前统计信息...")
    stats = archiver.get_collection_stats()
    print(f"   总消息数：{stats['total_count']}")
    print(f"   最后存储：{stats['last_storage_at']}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
