#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 同步脚本
将备份推送到 GitHub 远程仓库
"""

import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import config


logger = logging.getLogger(__name__)


class GitSync:
    """Git 同步管理器"""
    
    def __init__(self):
        self.repo_dir = config.config_dir
        self.backup_dir = config.backup_dir
        self.remote = config.get('git.remote', 'origin')
        self.token = config.git_token
        self.remote_url = config.git_remote_url
        
        # 配置 Git 凭证
        self.authenticated_url = self._build_authenticated_url()
    
    def _build_authenticated_url(self) -> str:
        """构建带认证的远程 URL"""
        if not self.token or not self.remote_url:
            return self.remote_url
        
        # 插入 token 到 URL
        if '://' in self.remote_url:
            protocol, rest = self.remote_url.split('://', 1)
            return f"{protocol}://{self.token}@{rest}"
        return self.remote_url
    
    def _run_git(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        """运行 Git 命令"""
        cmd = ['git'] + list(args)
        logger.debug(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if check and result.returncode != 0:
            logger.error(f"Git command failed: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd)
        
        return result
    
    def setup_credentials(self):
        """配置 Git 凭证"""
        if self.authenticated_url:
            self._run_git('remote', 'set-url', self.remote, self.authenticated_url, check=False)
            logger.info("Git credentials configured")
    
    def add_changes(self):
        """添加变更"""
        self._run_git('add', '-A')
        logger.debug("Changes added")
    
    def has_changes(self) -> bool:
        """检查是否有变更"""
        result = self._run_git('status', '--porcelain')
        return bool(result.stdout.strip())
    
    def commit(self, message: str):
        """提交变更"""
        self._run_git('config', 'user.email', 'personal-assistant@openclaw.local')
        self._run_git('config', 'user.name', 'Personal Assistant')
        self._run_git('commit', '-m', message)
        logger.info(f"Committed: {message}")
    
    def push(self, branch: str = 'master'):
        """推送到远程"""
        self._run_git('push', self.remote, branch)
        logger.info(f"Pushed to {self.remote}/{branch}")
    
    def pull(self, branch: str = 'master'):
        """从远程拉取"""
        self._run_git('pull', self.remote, branch)
        logger.info(f"Pulled from {self.remote}/{branch}")
    
    def sync(self, commit_message: Optional[str] = None):
        """
        完整同步流程
        
        Args:
            commit_message: 提交信息（可选，自动生成）
        """
        logger.info("Starting Git sync...")
        
        # 配置凭证
        self.setup_credentials()
        
        # 先拉取最新代码
        try:
            self.pull()
        except Exception as e:
            logger.warning(f"Pull failed (might be first sync): {e}")
        
        # 检查是否有变更
        if not self.has_changes():
            logger.info("No changes to sync")
            return {'status': 'no_changes'}
        
        # 添加变更
        self.add_changes()
        
        # 生成提交信息
        if not commit_message:
            date = datetime.now().strftime('%Y-%m-%d %H:%M')
            commit_message = f"Backup: {date} - Auto sync"
        
        # 提交
        self.commit(commit_message)
        
        # 推送
        self.push()
        
        logger.info("Git sync completed!")
        return {'status': 'success', 'commit_message': commit_message}


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    sync = GitSync()
    result = sync.sync()
    print(f"Sync result: {result}")
