#!/bin/bash
# 记忆库系统 - 完整健康检查脚本

echo "=========================================="
echo "  记忆库系统 - 完整健康检查"
echo "  检查时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

PASS=0
FAIL=0

# 检查函数
check_pass() {
    echo "   ✅ $1"
    ((PASS++))
}

check_fail() {
    echo "   ❌ $1"
    ((FAIL++))
}

# 1. 检查环境变量配置
echo "1️⃣  环境变量配置:"
if grep -q "HF_ENDPOINT" ~/.bashrc 2>/dev/null; then
    check_pass "HF_ENDPOINT 已配置在 .bashrc"
else
    check_fail "HF_ENDPOINT 未配置在 .bashrc"
fi

if grep -q "MEMORY_SYSTEM_DIR" ~/.bashrc 2>/dev/null; then
    check_pass "MEMORY_SYSTEM_DIR 已配置在 .bashrc"
else
    check_fail "MEMORY_SYSTEM_DIR 未配置在 .bashrc"
fi

if grep -q "openclaw gateway" ~/.bashrc 2>/dev/null; then
    check_pass "OpenClaw Gateway 自启已配置"
else
    check_fail "OpenClaw Gateway 自启未配置"
fi
echo ""

# 2. 检查 Cron 服务
echo "2️⃣  Cron 服务状态:"
if pgrep -x cron > /dev/null; then
    check_pass "Cron 服务正在运行 (PID: $(pgrep -x cron))"
else
    check_fail "Cron 服务未运行"
    echo "   尝试启动..."
    sudo service cron start 2>/dev/null || service cron start 2>/dev/null
    sleep 1
    if pgrep -x cron > /dev/null; then
        echo "   ✅ Cron 服务已启动"
    else
        echo "   ❌ 无法启动 Cron 服务"
    fi
fi
echo ""

# 3. 检查 Crontab 配置
echo "3️⃣  Crontab 定时任务:"
CRONTAB_LIST=$(crontab -l 2>/dev/null)

if echo "$CRONTAB_LIST" | grep -q "archiver_runner.py"; then
    check_pass "归档任务已配置 (每分钟)"
else
    check_fail "归档任务未配置"
fi

if echo "$CRONTAB_LIST" | grep -q "daily_backup_runner.py"; then
    check_pass "备份任务已配置 (每天 00:00)"
else
    check_fail "备份任务未配置"
fi

if echo "$CRONTAB_LIST" | grep -q "MEMORY_SYSTEM_DIR"; then
    check_pass "环境变量已在 crontab 中定义"
else
    check_fail "环境变量未在 crontab 中定义"
fi
echo ""

# 4. 检查记忆库系统文件
echo "4️⃣  记忆库系统文件:"
MEMORY_DIR="$HOME/.openclaw/agents/personal-assistant/workspace/记忆库/memory-system"

if [ -d "$MEMORY_DIR" ]; then
    check_pass "记忆库目录存在"
else
    check_fail "记忆库目录不存在"
fi

if [ -f "$MEMORY_DIR/src/archiver_runner.py" ]; then
    check_pass "归档脚本存在"
else
    check_fail "归档脚本不存在"
fi

if [ -f "$MEMORY_DIR/src/daily_backup_runner.py" ]; then
    check_pass "备份脚本存在"
else
    check_fail "备份脚本不存在"
fi

if [ -f "$MEMORY_DIR/config.yaml" ]; then
    check_pass "配置文件存在"
else
    check_fail "配置文件不存在"
fi

if [ -f "$MEMORY_DIR/.credentials" ]; then
    check_pass "凭证文件存在"
else
    check_fail "凭证文件不存在"
fi
echo ""

# 5. 检查向量库状态
echo "5️⃣  向量库状态:"
if [ -f "$MEMORY_DIR/vector_db/chroma.sqlite3" ]; then
    DB_SIZE=$(du -h "$MEMORY_DIR/vector_db/chroma.sqlite3" 2>/dev/null | cut -f1)
    check_pass "ChromaDB 存在 (大小：$DB_SIZE)"
    
    # 尝试获取消息数量
    if command -v python3 &> /dev/null; then
        MSG_COUNT=$(cd "$MEMORY_DIR" && python3 -c "
import sys
sys.path.insert(0, 'src')
from archiver import archiver
print(archiver.get_collection_stats()['total_count'])
" 2>/dev/null || echo "0")
        check_pass "已存储消息数：$MSG_COUNT 条"
    fi
else
    check_fail "ChromaDB 不存在（首次运行后会自动创建）"
fi
echo ""

# 6. 检查 Git 仓库
echo "6️⃣  Git 仓库状态:"
if [ -d "$MEMORY_DIR/.git" ]; then
    check_pass "Git 仓库已初始化"
    
    cd "$MEMORY_DIR"
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    check_pass "当前分支：$BRANCH"
    
    UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l)
    if [ "$UNCOMMITTED" -eq 0 ]; then
        check_pass "工作区干净，无未提交更改"
    else
        echo "   ⚠️  有 $UNCOMMITTED 个未提交的更改"
    fi
    
    # 检查远程仓库
    REMOTE=$(git remote get-url origin 2>/dev/null || echo "none")
    if [ "$REMOTE" != "none" ]; then
        check_pass "远程仓库已配置：$REMOTE"
    else
        check_fail "远程仓库未配置"
    fi
else
    check_fail "Git 仓库未初始化"
fi
echo ""

# 7. 检查 OpenClaw Gateway
echo "7️⃣  OpenClaw Gateway 状态:"
if pgrep -f "openclaw gateway" > /dev/null; then
    GW_PID=$(pgrep -f "openclaw gateway")
    check_pass "Gateway 正在运行 (PID: $GW_PID)"
else
    check_fail "Gateway 未运行"
    echo "   提示：重启 terminal 后会自动启动"
fi
echo ""

# 8. 检查日志文件
echo "8️⃣  日志文件状态:"
if [ -d "$MEMORY_DIR/logs" ]; then
    check_pass "日志目录存在"
    
    if [ -f "$MEMORY_DIR/logs/archiver.log" ]; then
        LOG_SIZE=$(du -h "$MEMORY_DIR/logs/archiver.log" 2>/dev/null | cut -f1)
        LAST_LINE=$(tail -1 "$MEMORY_DIR/logs/archiver.log" 2>/dev/null | cut -c1-60)
        check_pass "归档日志存在 (大小：$LOG_SIZE)"
        echo "   最后更新：$LAST_LINE..."
    else
        check_fail "归档日志不存在（首次运行后会自动创建）"
    fi
    
    if [ -f "$MEMORY_DIR/logs/daily_backup.log" ]; then
        LOG_SIZE=$(du -h "$MEMORY_DIR/logs/daily_backup.log" 2>/dev/null | cut -f1)
        check_pass "备份日志存在 (大小：$LOG_SIZE)"
    else
        check_fail "备份日志不存在（首次运行后会自动创建）"
    fi
else
    check_fail "日志目录不存在"
fi
echo ""

# 9. 检查 Python 依赖
echo "9️⃣  Python 依赖:"
if python3 -c "import chromadb" 2>/dev/null; then
    check_pass "chromadb 已安装"
else
    check_fail "chromadb 未安装"
fi

if python3 -c "import sentence_transformers" 2>/dev/null; then
    check_pass "sentence-transformers 已安装"
else
    check_fail "sentence-transformers 未安装"
fi

if python3 -c "import requests" 2>/dev/null; then
    check_pass "requests 已安装"
else
    check_fail "requests 未安装"
fi

if python3 -c "import yaml" 2>/dev/null; then
    check_pass "PyYAML 已安装"
else
    check_fail "PyYAML 未安装"
fi
echo ""

# 10. 检查备份文件
echo "🔟  备份文件状态:"
if [ -d "$MEMORY_DIR/backup" ]; then
    check_pass "备份目录存在"
    
    BACKUP_COUNT=$(find "$MEMORY_DIR/backup" -name "*.json" 2>/dev/null | wc -l)
    check_pass "Git 备份文件数：$BACKUP_COUNT"
else
    check_fail "备份目录不存在"
fi

if [ -d "$MEMORY_DIR/archive" ]; then
    check_pass "归档目录存在"
    
    ARCHIVE_COUNT=$(find "$MEMORY_DIR/archive" -name "*.json" 2>/dev/null | wc -l)
    check_pass "JSON 归档文件数：$ARCHIVE_COUNT"
else
    check_fail "归档目录不存在"
fi
echo ""

# 总结
echo "=========================================="
echo "  检查完成！"
echo "=========================================="
echo ""
echo "📊 统计结果:"
echo "   ✅ 通过：$PASS 项"
echo "   ❌ 失败：$FAIL 项"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 太棒了！所有检查都通过啦！"
    echo ""
    echo "💡 提示:"
    echo "   - 记忆库系统已完全配置好"
    echo "   - 重启 terminal 后所有服务会自动启动"
    echo "   - 每分钟自动存储新消息"
    echo "   - 每天凌晨自动备份到 GitHub"
    exit 0
else
    echo "⚠️  有 $FAIL 项检查未通过，请检查上面的输出"
    echo ""
    echo "💡 建议:"
    echo "   1. 重启 terminal 让环境变量生效"
    echo "   2. 再次运行此脚本检查"
    echo "   3. 查看文档：开机自启配置指南.md"
    exit 1
fi
