# 🔄 Token 自动刷新机制

> **更新时间：** 2026-03-24  
> **状态：** ✅ 已实现自动刷新

---

## 📊 Token 有效期

| Token 类型 | 有效期 | 自动刷新 | 说明 |
|-----------|--------|---------|------|
| Tenant Access Token | 2 小时 | ✅ 自动 | 用于应用级 API |
| User Access Token | 2 小时 | ✅ 自动 | 用于用户级 API |
| Refresh Token | 7 天 | ✅ 自动 | 用于刷新 User Token |

---

## 🎯 自动刷新流程

### User Access Token 刷新

```
User Token 即将过期
    ↓
使用 Refresh Token 刷新
    ↓
获取新的 User Token + Refresh Token
    ↓
自动保存到 .credentials 文件
    ↓
继续正常工作 ✅
```

### Refresh Token 刷新

```
Refresh Token 即将过期（7 天）
    ↓
检测到 20037 错误
    ↓
记录错误日志
    ↓
需要手动重新授权 ⚠️
```

---

## 📋 配置说明

### 凭证文件位置

```
~/.openclaw/agents/personal-assistant/workspace/记忆库/memory-system/.credentials
```

### 文件内容

```yaml
feishu:
  app_id: "cli_a9310c516a389bc2"
  app_secret: "WFVrPdx0iFqHcbBsxY0f4fkR2fhNuGVA"
  user_access_token: "eyJhbGci..."  # 自动更新
  refresh_token: "eyJhbGci..."        # 自动更新
  user_id: "ou_ce3ee0995da167ac887b8ef308e2a388"

git:
  remote_url: "https://github.com/TBLboy/1025.git"
  token: "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"
```

---

## ⚠️ 需要手动授权的情况

### 情况 1：Refresh Token 过期（7 天后）

**症状：**
```
ERROR: Refresh token expired. Please re-authorize.
```

**解决方案：**
1. 重新打开 OAuth 授权链接
2. 获取新的授权码
3. 换取新的 Refresh Token

### 情况 2：应用权限变更

**症状：**
```
ERROR: Unauthorized. You do not have permission...
```

**解决方案：**
1. 在飞书开放平台添加权限
2. 重新发布应用
3. 重新授权

---

## 🔧 维护建议

### 每周检查一次

```bash
# 查看 Token 状态
cd 记忆库/memory-system
cat .credentials | grep -A2 "feishu:"
```

### 查看刷新日志

```bash
tail -f logs/archiver.log | grep -i "token"
```

### 设置提醒

**建议：** 每 6 天检查一次 Refresh Token 状态

---

## 📊 自动保存功能影响

### Token 刷新期间

| 场景 | 影响 | 说明 |
|------|------|------|
| User Token 刷新 | ✅ 无影响 | 自动刷新，用户无感知 |
| Refresh Token 刷新 | ✅ 无影响 | 自动刷新，用户无感知 |
| Refresh Token 过期 | ⚠️ 暂停保存 | 需要手动重新授权 |

### 最佳实践

1. **每 6 天重新授权一次**（在 Refresh Token 过期前）
2. **监控日志**（发现错误及时处理）
3. **备份凭证文件**（防止意外丢失）

---

## 🎯 使用流程

### 首次配置（只需一次）

1. 打开 OAuth 授权链接
2. 获取授权码
3. 换取 Refresh Token
4. 保存到 `.credentials`

### 日常使用（自动）

1. ✅ 系统自动检测 Token 过期
2. ✅ 自动使用 Refresh Token 刷新
3. ✅ 自动保存新 Token
4. ✅ 继续正常工作

### 7 天后（手动）

1. ⚠️ 收到 Refresh Token 过期警告
2. ⚠️ 重新打开授权链接
3. ⚠️ 获取新的 Refresh Token
4. ✅ 继续自动运行

---

## 💡 优化建议

### 计划任务（可选）

添加一个每周执行的 Cron 任务，自动提醒刷新：

```bash
# 每周日上午 10 点检查 Token 状态
0 10 * * 0 cd $MEMORY_SYSTEM_DIR && python3 src/check_token_status.py
```

### 通知机制（可选）

Token 即将过期时发送飞书消息提醒：

```python
# 在 archiver_runner.py 中添加
if token_expires_soon():
    send_feishu_notification("Token 即将过期，请重新授权")
```

---

_文档版本：v1.0_  
_最后更新：2026-03-24_
