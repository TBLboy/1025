#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载飞书聊天文件的另一种方法
使用消息 API 获取文件内容
"""

import requests
import yaml
from pathlib import Path

# 读取凭证
cred_path = Path(__file__).parent.parent / ".credentials"
with open(cred_path, 'r') as f:
    creds = yaml.safe_load(f)

user_token = creds['feishu'].get('user_access_token', '')

print(f"使用 User Token: {user_token[:50]}...")

# 聊天 ID
chat_id = "oc_6ca477feac7842bef1e83daa8a649e70"

# 获取消息列表
message_url = "https://open.feishu.cn/open-apis/im/v1/messages"
params = {
    'container_id_type': 'chat',
    'container_id': chat_id,
    'page_size': 50
}
headers = {
    'Authorization': f'Bearer {user_token}'
}

print(f"\n📥 获取消息列表...")
resp = requests.get(message_url, headers=headers, params=params)
result = resp.json()

if result.get('code') == 0:
    messages = result.get('data', {}).get('items', [])
    print(f"✅ 获取到 {len(messages)} 条消息")
    
    # 查找文件消息
    for msg in messages:
        msg_type = msg.get('msg_type', '')
        if msg_type == 'file':
            print(f"\n📎 找到文件消息:")
            msg_id = msg.get('message_id')
            print(f"  Message ID: {msg_id}")
            
            # 尝试获取消息详情
            detail_url = f"https://open.feishu.cn/open-apis/im/v1/messages/{msg_id}"
            detail_resp = requests.get(detail_url, headers=headers)
            detail_result = detail_resp.json()
            
            print(f"  消息详情：{detail_result}")
            
            # 尝试直接下载文件
            file_info = msg.get('body', {}).get('content', {})
            if isinstance(file_info, str):
                import json
                file_info = json.loads(file_info)
            
            file_key = file_info.get('file_key')
            file_name = file_info.get('file_name')
            
            print(f"  File Key: {file_key}")
            print(f"  File Name: {file_name}")
            
            # 尝试不同的下载 API
            download_urls = [
                f"https://open.feishu.cn/open-apis/im/v1/messages/{msg_id}/attachments/{file_key}",
                f"https://open.feishu.cn/open-apis/imin/v1/messages/{msg_id}/attachments/{file_key}",
                f"https://open.feishu.cn/open-apis/drive/v1/files/{file_key}/download",
                f"https://open.feishu.cn/open-apis/drive/v1/medias/{file_key}/download",
            ]
            
            for url in download_urls:
                print(f"\n  尝试下载：{url}")
                download_resp = requests.get(url, headers=headers)
                print(f"  状态码：{download_resp.status_code}")
                
                if download_resp.status_code == 200:
                    # 保存文件
                    save_path = Path('/tmp') / file_name
                    with open(save_path, 'wb') as f:
                        f.write(download_resp.content)
                    print(f"  ✅ 下载成功！保存到：{save_path}")
                    break
                else:
                    print(f"  ❌ 失败：{download_resp.text[:100]}")
else:
    print(f"❌ 获取消息失败：{result}")
