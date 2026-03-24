#!/bin/bash
# 记忆库系统健康检查脚本

echo "=========================================="
echo "  记忆库系统健康检查"
echo "=========================================="
echo ""

# 1. 检查 Cron 服务
echo "1. Cron 服务状态:"
if pgrep -x cron > /dev/null; then
    echo "   ✅ Cron 服务正在运行"
else
    echo "   ❌ Cron 服务未运行"
    echo "   尝试启动..."
    sudo service cron start 2>/dev/null || service cron start 2>/dev/null
fi
echo ""

# 2. 检查 Crontab 配置
echo "2. Crontab 配置:"
if crontab -l 2>/dev/null | grep -q "archiver_runner.py"; then
    echo "   ✅ 归档任务已配置"
else
    echo "   ❌ 归档任务未配置"
fi
if crontab -l 2>/dev/null | grep -q "daily_backup_runner.py"; then
    echo "   ✅ 备份任务已配置"
else
    echo "   ❌ 备份任务未配置"
fi
echo ""

# 3. 检查环境变量
echo "3. 环境变量:"
if [ -n "$HF_ENDPOINT" ]; then
    echo "   ✅ HF_ENDPOINT: $HF_ENDPOINT"
else
    echo "   ❌ HF_ENDPOINT 未设置"
fi
if [ -n "$MEMORY_SYSTEM_DIR" ]; then
    echo "   ✅ MEMORY_SYSTEM_DIR: $MEMORY_SYSTEM_DIR"
else
    echo "   ❌ MEMORY_SYSTEM_DIR 未设置"
fi
echo ""

# 4. 检查向量库状态
echo "4. 向量库状态:"
if [ -f "$MEMORY_SYSTEM_DIR/vector_db/chroma.sqlite3" ]; then
    COUNT=$(cd "$MEMORY_SYSTEM_DIR" && python3 -c "import sys; sys.path.insert(0, 'src'); from archiver import archiver; print(archiver.get_collection_stats()['total_count'])" 2>/dev/null || echo "未知")
    echo "   ✅ ChromaDB 存在，消息数：$COUNT"
else
    echo "   ❌ ChromaDB 不存在"
fi
echo ""

# 5. 检查 Git 状态
echo "5. Git 同步状态:"
if [ -d "$MEMORY_SYSTEM_DIR/.git" ]; then
    echo "   ✅ Git 仓库已初始化"
    cd "$MEMORY_SYSTEM_DIR" && git status --short 2>/dev/null | head -5
else
    echo "   ❌ Git 仓库未初始化"
fi
echo ""

echo "=========================================="
echo "  检查完成！"
echo "=========================================="
