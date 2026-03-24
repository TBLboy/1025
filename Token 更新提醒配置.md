# 🔔 Token 更新提醒配置

> **创建时间：** 2026-03-24  
> **状态：** ✅ 已配置

---

## ✅ 已配置的定时任务

### 每 7 天自动提醒

**时间：** 每周一上午 10:00  
**脚本：** `token_check.py`  
**日志：** `logs/token_check.log`

**Crontab 配置：**
```bash
# 每 7 天检查一次 Token 状态并提醒（周一上午 10 点）
0 10 * * 1 cd $MEMORY_SYSTEM_DIR && /usr/bin/python3 src/token_check.py >> $MEMORY_SYSTEM_DIR/logs/token_check.log 2>&1
```

---

## 📋 提醒内容

### 情况 1：Refresh Token 未配置

```
⚠️ Token 更新提醒

Refresh Token 未配置！

请重新授权获取新的 Refresh Token。

授权链接：
https://accounts.feishu.cn/open-apis/authen/v1/authorize...
```

### 情况 2：Refresh Token 即将过期（7 天）

```
🔔 Token 更新提醒

距离上次授权已过去约 7 天，Refresh Token 即将过期。

为了确保持续自动保存，请重新授权获取新的 Refresh Token。

📝 操作步骤：
1. 打开授权链接
2. 复制授权码 (code)
3. 告诉纳西妲换取新 Token

🔗 授权链接：
https://accounts.feishu.cn/open-apis/authen/v1/authorize...
```

---

## 🎯 工作流程

```
每周一 10:00 AM
    ↓
执行 token_check.py
    ↓
检查 Token 状态
    ↓
发送飞书提醒消息
    ↓
记录到 logs/token_check.log
    ↓
哥哥收到提醒 → 重新授权
```

---

## 📊 查看所有定时任务

```bash
crontab -l
```

**当前任务列表：**

| 频率 | 时间 | 任务 | 说明 |
|------|------|------|------|
| 每分钟 | * * * * * | archiver_runner.py | 自动保存消息 |
| 每天 | 00:00 | daily_backup_runner.py | 每日备份 |
| **每 7 天** | **周一 10:00** | **token_check.py** | **Token 更新提醒** ⭐ |

---

## 🔧 手动触发提醒（测试用）

```bash
cd 记忆库/memory-system
python3 src/token_check.py
```

**查看日志：**
```bash
tail -f logs/token_check.log
```

---

## 📝 修改提醒频率

如果想改为其他频率，编辑 crontab：

```bash
crontab -e
```

**示例：**

| 频率 | Crontab 表达式 | 说明 |
|------|--------------|------|
| 每周一次 | `0 10 * * 1` | 每周一 10:00 ✅ 当前 |
| 每 10 天一次 | `0 10 */10 * *` | 每 10 天 10:00 |
| 每月一次 | `0 10 1 * *` | 每月 1 号 10:00 |
| 每天一次 | `0 10 * * *` | 每天 10:00 |

---

## ⚠️ 注意事项

1. **确保 Cron 服务运行**
   ```bash
   service cron status
   ```

2. **检查日志文件**
   ```bash
   tail -f logs/token_check.log
   ```

3. **如果收不到提醒**
   - 检查飞书消息通知设置
   - 查看日志是否有错误
   - 确认 Token 是否有效

---

## 🎯 哥哥需要做的

**收到提醒后：**

1. **打开飞书消息中的授权链接**
2. **授权并复制 code**
3. **告诉纳西妲："这是新的授权码：xxxxx"**
4. ✅ 纳西妲自动换取新 Token 并保存

**之后又自动运行 7 天！** 🎉

---

_文档版本：v1.0_  
_最后更新：2026-03-24_
