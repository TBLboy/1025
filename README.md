# 记忆向量库系统

基于 ChromaDB + BGE-M3 嵌入模型的本地记忆存储和检索系统。

## 🎯 功能特性

- **实时归档**: 每分钟自动检查并存储新消息
- **每日备份**: 每天凌晨生成摘要并归档
- **Git 同步**: 自动推送到 GitHub 远程仓库
- **语义检索**: 支持关键词和时间过滤的智能搜索
- **持久化存储**: 数据本地存储，安全可控

## 📁 目录结构

```
memory-system/
├── src/                    # Python 源代码
│   ├── config.py          # 配置管理
│   ├── feishu_api.py      # 飞书 API 封装
│   ├── archiver.py        # 归档核心
│   ├── archiver_runner.py # 归档运行脚本
│   ├── retriever.py       # 检索模块
│   ├── daily_backup.py    # 每日备份逻辑
│   ├── daily_backup_runner.py # 备份运行脚本
│   └── sync_git.py        # Git 同步
├── vector_db/             # ChromaDB 向量数据
├── archive/               # JSON 备份文件
├── backup/                # Git 同步备份
├── logs/                  # 日志文件
├── config.yaml            # 配置文件
├── .credentials           # 敏感凭证（已加入.gitignore）
├── requirements.txt       # Python 依赖
└── crontab.txt           # Cron 配置模板
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/windows/.openclaw/agents/personal-assistant/workspace/记忆库/memory-system

# 安装 pip（如果需要）
sudo apt install python3-pip

# 安装 Python 依赖
pip3 install -r requirements.txt
```

### 2. 配置 Cron 定时任务

```bash
# 查看 crontab 模板
cat crontab.txt

# 编辑 crontab
crontab -e

# 粘贴 crontab.txt 中的内容并保存
```

### 3. 测试运行

```bash
# 测试归档脚本
python3 src/archiver_runner.py

# 测试每日备份
python3 src/daily_backup_runner.py

# 测试 Git 同步
python3 src/sync_git.py
```

### 4. 查看日志

```bash
# 实时查看归档日志
tail -f logs/archiver.log

# 查看备份日志
tail -f logs/daily_backup.log
```

## 📖 使用示例

### 存储消息

```python
from archiver import archiver

message = {
    'message_id': 'om_x100b532...',
    'content': '这是一条消息',
    'sender': 'user',
    'timestamp': '2026-03-24T09:00:00+08:00'
}

archiver.store_message(message)
```

### 检索记忆

```python
from retriever import retriever

# 语义搜索
results = retriever.search("向量库相关的内容", top_k=5)

# 按日期搜索
results = retriever.search_by_time("2026-03-24", query="消融实验")

# 获取最近记忆
recent = retriever.get_recent(limit=10)
```

## ⚙️ 配置说明

### config.yaml

```yaml
# Feishu API 配置
feishu:
  app_id: "cli_xxxxxxxxx"
  app_secret: "xxxxxxxxxxxxx"

# ChromaDB 配置
chromadb:
  persist_directory: "./vector_db"
  collection_name: "memory_collection"

# 嵌入模型配置
embedding:
  model_name: "BAAI/bge-m3"

# Git 同步配置
git:
  enabled: true
  remote: "origin"
  auto_push: true
```

### .credentials（敏感信息）

```yaml
git:
  remote_url: "https://github.com/username/repo.git"
  token: "ghp_xxxxxxxxxxxxx"

feishu:
  app_id: "cli_xxxxxxxxx"
  app_secret: "xxxxxxxxxxxxx"
```

## 🔧 故障排查

### 常见问题

1. **pip 未安装**
   ```bash
   sudo apt update && sudo apt install python3-pip
   ```

2. **依赖安装失败**
   ```bash
   pip3 install --upgrade pip
   pip3 install -r requirements.txt --break-system-packages
   ```

3. **Cron 未执行**
   ```bash
   # 检查 cron 服务状态
   systemctl status cron
   
   # 查看 cron 日志
   grep CRON /var/log/syslog
   ```

4. **Git 推送失败**
   ```bash
   # 检查凭证配置
   cat .credentials
   
   # 手动测试推送
   python3 src/sync_git.py
   ```

## 📊 监控和维护

### 查看存储统计

```python
from archiver import archiver
stats = archiver.get_collection_stats()
print(stats)
```

### 清理旧数据

定期清理日志文件：
```bash
# 保留最近 5 个日志文件
find logs/ -name "*.log" -mtime +30 -delete
```

## 📝 更新日志

- 2026-03-24: 初始版本创建

---

_最后更新：2026-03-24_
