# 🔌 OpenClaw 消息自动保存插件

> **创建时间：** 2026-03-24 17:37  
> **状态：** ✅ 已创建  
> **优势：** 不需要 User Access Token

---

## 📁 文件位置

```
记忆库/memory-system/plugins/message_auto_saver.py
```

---

## 🎯 核心优势

### vs 定时任务方案

| 特性 | 定时任务方案 | 插件方案 |
|------|------------|---------|
| **Token 需求** | ❌ 需要 User Token | ✅ 不需要 |
| **实时性** | ⏰ 每分钟保存 | ⚡ 实时保存 |
| **可靠性** | ⚠️ 可能遗漏 | ✅ 不会遗漏 |
| **配置复杂度** | 🔧 需要 Cron | 🔌 一次集成 |
| **维护成本** | 📊 需要监控 | 🎉 自动运行 |

---

## 🚀 工作原理

```
用户消息 → OpenClaw 接收 → 插件保存 → 我处理 → 回复 → 插件保存
   ↓                                              ↓
保存到向量库                                    保存到向量库
```

**流程：**
1. 用户发送消息
2. OpenClaw 收到消息
3. **自动调用 `on_message_received()`**
4. 保存到向量库
5. 我生成回复
6. **自动调用 `on_reply_sent()`**
7. 保存到向量库

---

## 🔧 集成方法

### 方法 1：修改 OpenClaw Agent 配置（推荐 ⭐）

在 OpenClaw 的 agent 配置文件中添加：

```yaml
# ~/.openclaw/agents/personal-assistant/config.yaml

plugins:
  - message_auto_saver

hooks:
  on_message_received:
    - message_auto_saver.on_message_received
  on_reply_sent:
    - message_auto_saver.on_reply_sent
```

---

### 方法 2：修改 Agent 代码

在 agent 初始化代码中添加：

```python
# ~/.openclaw/agents/personal-assistant/agent.py

from 记忆库.memory-system.plugins.message_auto_saver import (
    on_message_received,
    on_reply_sent
)

# 注册钩子
register_hook('on_message_received', on_message_received)
register_hook('on_reply_sent', on_reply_sent)
```

---

### 方法 3：手动调用（临时方案）

在需要保存消息时手动调用：

```python
from 记忆库.memory-system.plugins.message_auto_saver import auto_saver

# 保存用户消息
auto_saver.save_user_message(
    content="用户消息内容",
    message_id="消息 ID",
    timestamp="时间戳"
)

# 保存助手回复
auto_saver.save_assistant_message(
    content="助手回复内容",
    message_id="消息 ID",
    timestamp="时间戳"
)
```

---

## 📝 API 说明

### `save_user_message(content, message_id, timestamp, metadata)`

保存用户消息

**参数：**
- `content` (str): 消息内容
- `message_id` (str, optional): 消息 ID
- `timestamp` (str, optional): 时间戳
- `metadata` (dict, optional): 额外元数据

**返回：**
- `bool`: 是否保存成功

**示例：**
```python
auto_saver.save_user_message(
    content="你好，今天天气怎么样？",
    message_id="msg_001",
    timestamp="2026-03-24T17:37:00"
)
```

---

### `save_assistant_message(content, message_id, timestamp, metadata)`

保存助手回复

**参数：** 同上

**示例：**
```python
auto_saver.save_assistant_message(
    content="今天天气很好，阳光明媚！",
    message_id="msg_002",
    timestamp="2026-03-24T17:37:05"
)
```

---

### `save_conversation(user_content, assistant_content, message_id, timestamp)`

保存一轮对话（用户 + 助手）

**参数：**
- `user_content` (str): 用户消息
- `assistant_content` (str): 助手回复
- `message_id` (str, optional): 对话 ID
- `timestamp` (str, optional): 时间戳

**示例：**
```python
auto_saver.save_conversation(
    user_content="你好",
    assistant_content="你好！有什么我可以帮你的吗？",
    message_id="conv_001"
)
```

---

## 🧪 测试方法

### 运行测试脚本

```bash
cd 记忆库/memory-system/plugins
python3 message_auto_saver.py
```

**预期输出：**
```
============================================================
测试消息自动保存功能
============================================================

1️⃣ 测试保存用户消息...
   结果：✅ 成功

2️⃣ 测试保存助手回复...
   结果：✅ 成功

3️⃣ 测试保存完整对话...
   结果：✅ 成功

4️⃣ 当前统计信息...
   总消息数：11
   最后存储：2026-03-24T17:37:31

============================================================
✅ 测试完成！
============================================================
```

---

## 📊 日志查看

**日志位置：**
```
记忆库/memory-system/logs/archiver.log
```

**查看实时日志：**
```bash
tail -f 记忆库/memory-system/logs/archiver.log
```

**示例日志：**
```
2026-03-24 17:37:31,479 - MessageSaver - INFO - MessageAutoSaver initialized
2026-03-24 17:37:32,123 - MessageSaver - INFO - ✅ Saved user message: msg_001...
2026-03-24 17:37:35,456 - MessageSaver - INFO - ✅ Saved assistant message: msg_002...
```

---

## 🎯 集成检查清单

- [ ] 复制插件文件到正确位置
- [ ] 修改 OpenClaw 配置文件
- [ ] 注册钩子函数
- [ ] 运行测试脚本
- [ ] 检查日志输出
- [ ] 验证消息保存

---

## 💡 常见问题

### Q: 插件不工作怎么办？

**A:** 检查以下几点：
1. 插件路径是否正确
2. 钩子是否已注册
3. 查看日志是否有错误

### Q: 保存的消息在哪里查看？

**A:** 在向量库中查看：
```bash
cd 记忆库/memory-system
python3 -c "
import sys
sys.path.insert(0, 'src')
from archiver import archiver
stats = archiver.get_collection_stats()
print(f'总消息数：{stats[\"total_count\"]}')
"
```

### Q: 会影响消息处理速度吗？

**A:** 影响很小：
- 保存操作是异步的
- 向量计算很快（约 10-50ms）
- 不会明显影响回复速度

---

## 🎉 优势总结

1. ✅ **不需要 User Access Token** - 不依赖飞书 API
2. ✅ **实时保存** - 每条消息都保存
3. ✅ **不会遗漏** - 不依赖定时任务
4. ✅ **一次集成** - 永久有效
5. ✅ **简单可靠** - 代码简洁，易于维护

---

_文档版本：v1.0_  
_创建时间：2026-03-24 17:37_  
_维护者：纳西妲_
