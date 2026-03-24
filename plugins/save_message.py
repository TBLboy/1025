#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 消息自动保存 - 简单集成脚本

在每次对话中调用此脚本保存消息。
用法：python3 save_message.py "用户消息" "助手回复"
"""

import sys
import os
from pathlib import Path

# 添加插件路径
plugin_path = Path(__file__).parent
sys.path.insert(0, str(plugin_path))

from message_auto_saver import auto_saver


def save_conversation(user_content: str, assistant_content: str, conversation_id: str = None):
    """
    保存一轮对话
    
    Args:
        user_content: 用户消息
        assistant_content: 助手回复
        conversation_id: 对话 ID（可选）
    """
    from datetime import datetime
    
    ts = datetime.now().isoformat()
    conv_id = conversation_id or f"conv_{datetime.now().timestamp()}"
    
    # 保存用户消息
    auto_saver.save_user_message(
        content=user_content,
        message_id=f"{conv_id}_user",
        timestamp=ts
    )
    
    # 保存助手回复
    auto_saver.save_assistant_message(
        content=assistant_content,
        message_id=f"{conv_id}_assistant",
        timestamp=ts
    )
    
    print(f"✅ 对话已保存：{conv_id}")


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        user_msg = sys.argv[1]
        assistant_msg = sys.argv[2]
        conv_id = sys.argv[3] if len(sys.argv) > 3 else None
        
        save_conversation(user_msg, assistant_msg, conv_id)
    else:
        print("用法：python3 save_message.py \"用户消息\" \"助手回复\" [对话 ID]")
        print("\n示例:")
        print('python3 save_message.py "你好" "你好！有什么我可以帮你的吗？"')
