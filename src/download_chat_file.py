#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载飞书聊天中的文件
使用正确的 API：GET /open-apis/im/v1/messages/{message_id}/attachments/{file_key}
"""

import requests
import yaml
from pathlib import Path

# 读取凭证
cred_path = Path(__file__).parent.parent / ".credentials"
with open(cred_path, 'r') as f:
    creds = yaml.safe_load(f)

app_id = creds['feishu']['app_id']
app_secret = creds['feishu']['app_secret']
user_token = creds['feishu'].get('user_access_token', '')

# 优先使用 User Token（文件所有者有访问权限）
if user_token:
    token = user_token
    token_type = "User Access Token"
    print(f"✅ 使用 User Token: {token[:50]}...")
else:
    # 如果没有 User Token，使用 Tenant Token
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token_resp = requests.post(token_url, json={
        "app_id": app_id,
        "app_secret": app_secret
    })
    token = token_resp.json().get('tenant_access_token')
    token_type = "Tenant Access Token"
    print(f"⚠️ 使用 Tenant Token: {token[:50]}...")

# 聊天 ID（我们之前的聊天）
chat_id = "oc_6ca477feac7842bef1e83daa8a649e70"

# 获取消息列表
message_url = "https://open.feishu.cn/open-apis/im/v1/messages"
params = {
    'container_id_type': 'chat',
    'container_id': chat_id,
    'page_size': 50
}
headers = {
    'Authorization': f'Bearer {token}'
}

print(f"📥 获取消息列表...")
resp = requests.get(message_url, headers=headers, params=params)
result = resp.json()

if result.get('code') == 0:
    messages = result.get('data', {}).get('items', [])
    print(f"✅ 获取到 {len(messages)} 条消息")
    
    # 查找包含文件的消息
    for msg in messages:
        msg_type = msg.get('msg_type', '')
        if msg_type == 'file':
            print(f"\n📎 找到文件消息:")
            print(f"  Message ID: {msg.get('message_id')}")
            print(f"  Content: {msg.get('body', {})}")
            
            # 获取文件信息
            file_info = msg.get('body', {}).get('content', {})
            if isinstance(file_info, str):
                import json
                file_info = json.loads(file_info)
            
            file_key = file_info.get('file_key')
            file_name = file_info.get('file_name')
            
            print(f"  File Key: {file_key}")
            print(f"  File Name: {file_name}")
            
            # 下载文件
            if file_key:
                download_url = f"https://open.feishu.cn/open-apis/im/v1/messages/{msg.get('message_id')}/attachments/{file_key}"
                
                print(f"\n📥 下载文件：{file_name}")
                download_resp = requests.get(download_url, headers=headers)
                
                if download_resp.status_code == 200:
                    # 保存到本地
                    save_path = Path('/tmp') / file_name
                    with open(save_path, 'wb') as f:
                        f.write(download_resp.content)
                    
                    print(f"✅ 文件已保存到：{save_path}")
                    print(f"📄 文件大小：{len(download_resp.content)} bytes")
                    
                    # 显示文件内容（如果是文本）
                    if file_name.endswith('.txt'):
                        print(f"\n📝 文件内容预览:")
                        print("=" * 50)
                        print(download_resp.content.decode('utf-8')[:500])
                        print("=" * 50)
                else:
                    print(f"❌ 下载失败：{download_resp.status_code}")
                    print(f"响应：{download_resp.text[:200]}")
else:
    print(f"❌ 获取消息失败：{result}")
