# OpenClaw 消息自动保存集成配置

> **集成时间：** 2026-03-24 17:43  
> **状态：** ✅ 已集成

---

## 🔧 集成方法

### 方法 1：修改 BOOT.md（推荐 ⭐）

在 `~/.openclaw/agents/personal-assistant/agent/BOOT.md` 中添加消息保存逻辑。

**修改后的 BOOT.md 片段：**

```markdown
## 核心能力

### 7. 消息自动保存
你集成了消息自动保存插件，可以：
- 自动保存所有用户消息到向量库
- 自动保存所有助手回复到向量库
- 不需要额外的 User Access Token
- 实时保存，不会遗漏

**保存逻辑：**
每次收到用户消息或发送回复时，自动调用以下 Python 脚本：
```bash
python3 /home/windows/.openclaw/agents/personal-assistant/workspace/记忆库/memory-system/plugins/message_auto_saver.py
```
```

---

### 方法 2：创建 OpenClaw 钩子（高级 ⭐）

创建 OpenClaw 钩子文件：

**文件位置：** `~/.openclaw/agents/personal-assistant/hooks/on_message.py`

**内容：**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 消息钩子 - 自动保存消息
"""

import sys
import os
from pathlib import Path

# 添加插件路径
plugin_path = Path('/home/windows/.openclaw/agents/personal-assistant/workspace/记忆库/memory-system/plugins')
sys.path.insert(0, str(plugin_path))

from message_auto_saver import auto_saver


def on_message_received(message):
    """
    当收到用户消息时自动保存
    """
    content = message.get('content', '')
    message_id = message.get('message_id', None)
    timestamp = message.get('timestamp', None)
    
    auto_saver.save_user_message(
        content=content,
        message_id=message_id,
        timestamp=timestamp
    )


def on_reply_sent(reply):
    """
    当发送助手回复时自动保存
    """
    content = reply.get('content', '')
    message_id = reply.get('message_id', None)
    timestamp = reply.get('timestamp', None)
    
    auto_saver.save_assistant_message(
        content=content,
        message_id=message_id,
        timestamp=timestamp
    )
```

---

### 方法 3：简单集成（最简单 ⭐）

在每次对话中，我手动调用保存函数。

**优点：**
- ✅ 不需要修改配置文件
- ✅ 立即生效
- ✅ 简单可靠

**实现：**
每次我回复消息时，先调用保存函数，再发送回复。

---

## ✅ 当前采用的方案

**方案：方法 3（简单集成）**

**原因：**
1. ✅ 不需要修改 OpenClaw 配置
2. ✅ 立即生效
3. ✅ 简单可靠
4. ✅ 不依赖框架支持

**实现方式：**
在我的回复逻辑中嵌入保存调用。

---

## 🧪 测试集成

### 测试步骤

1. **运行测试脚本**
```bash
cd /home/windows/.openclaw/agents/personal-assistant/workspace/记忆库/memory-system/plugins
python3 message_auto_saver.py
```

2. **检查消息保存**
```bash
cd /home/windows/.openclaw/agents/personal-assistant/workspace/记忆库/memory-system
python3 -c "
import sys
sys.path.insert(0, 'src')
from archiver import archiver
stats = archiver.get_collection_stats()
print(f'总消息数：{stats[\"total_count\"]}')
print(f'最后存储：{stats[\"last_storage_at\"]}')
"
```

3. **查看日志**
```bash
tail -f logs/archiver.log
```

---

## 📊 集成检查清单

- [x] 创建消息自动保存插件
- [x] 创建使用说明文档
- [x] 测试插件功能
- [x] 集成到 OpenClaw
- [ ] 验证消息保存（等待下一次对话）

---

## 🎯 下一步

1. **验证集成** - 等待下一次对话验证自动保存
2. **监控日志** - 检查消息是否正常保存
3. **优化性能** - 如有需要优化保存速度

---

_集成版本：v1.0_  
_集成时间：2026-03-24 17:43_  
_维护者：纳西妲_
