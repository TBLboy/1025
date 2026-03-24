#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书聊天文件下载 - 正确版本
根据诊断报告修正：
1. API 路径：/resources/ 而不是 /attachments/
2. 添加 type 参数
3. 使用 tenant_access_token
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

print("=" * 60)
print("飞书文件下载测试 - 修正版本")
print("=" * 60)

# 1. 获取 Tenant Token
print("\n1️⃣ 获取 Tenant Access Token...")
token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
token_resp = requests.post(token_url, json={
    "app_id": app_id,
    "app_secret": app_secret
})
tenant_token = token_resp.json().get('tenant_access_token')

if not tenant_token:
    print(f"❌ 获取 Tenant Token 失败：{token_resp.json()}")
    exit(1)

print(f"✅ Tenant Token: {tenant_token[:50]}...")

# 2. 获取消息列表
print("\n2️⃣ 获取消息列表...")
chat_id = "oc_6ca477feac7842bef1e83daa8a649e70"
message_url = "https://open.feishu.cn/open-apis/im/v1/messages"
params = {
    'container_id_type': 'chat',
    'container_id': chat_id,
    'page_size': 50
}
headers = {
    'Authorization': f'Bearer {tenant_token}'
}

resp = requests.get(message_url, headers=headers, params=params)
result = resp.json()

if result.get('code') != 0:
    print(f"❌ 获取消息失败：{result}")
    exit(1)

messages = result.get('data', {}).get('items', [])
print(f"✅ 获取到 {len(messages)} 条消息")

# 3. 查找文件消息
print("\n3️⃣ 查找文件消息...")
file_messages = []
for msg in messages:
    if msg.get('msg_type') == 'file':
        file_messages.append(msg)
        print(f"  📎 找到文件：{msg.get('body', {}).get('content', '{}')[:100]}...")

if not file_messages:
    print("❌ 没有找到文件消息")
    exit(1)

# 4. 下载文件（使用正确的 API）
print("\n4️⃣ 下载文件（使用正确的 API）...")
msg = file_messages[0]
msg_id = msg.get('message_id')

file_info = msg.get('body', {}).get('content', {})
if isinstance(file_info, str):
    import json
    file_info = json.loads(file_info)

file_key = file_info.get('file_key')
file_name = file_info.get('file_name')

print(f"  Message ID: {msg_id}")
print(f"  File Key: {file_key}")
print(f"  File Name: {file_name}")

# 正确的 API 路径和参数
base_url = "https://open.feishu.cn/open-apis"
url = f"{base_url}/im/v1/messages/{msg_id}/resources/{file_key}"
download_params = {"type": "file"}  # 关键参数！

print(f"\n  📥 下载 URL: {url}")
print(f"  参数：{download_params}")

download_resp = requests.get(url, headers=headers, params=download_params, stream=True)

print(f"\n  状态码：{download_resp.status_code}")

if download_resp.status_code == 200:
    # 保存文件
    save_path = Path('/tmp') / file_name
    with open(save_path, 'wb') as f:
        f.write(download_resp.content)
    
    print(f"\n  ✅ 下载成功！")
    print(f"  📄 文件大小：{len(download_resp.content)} bytes")
    print(f"  💾 保存位置：{save_path}")
    
    # 如果是文本文件，显示内容预览
    if file_name.endswith('.txt') or file_name.endswith('.md'):
        print(f"\n  📝 内容预览:")
        print("  " + "=" * 50)
        content = download_resp.content.decode('utf-8')[:500]
        print(f"  {content}")
        print("  " + "=" * 50)
else:
    print(f"\n  ❌ 下载失败：{download_resp.text[:200]}")
    print(f"\n  请检查:")
    print(f"  1. 机器人是否在群组中")
    print(f"  2. 权限是否已配置 (im:message:readAsBot)")
    print(f"  3. file_key 是否正确")

print("\n" + "=" * 60)
