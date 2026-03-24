#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送文件到飞书聊天 - 正确版本
根据官方文档：
1. 先上传文件到飞书（使用 /im/v1/files 接口）
2. 然后用 file_key 发送文件消息
"""

import requests
from requests_toolbelt import MultipartEncoder
import yaml
from pathlib import Path
import json

# 读取凭证
cred_path = Path(__file__).parent.parent / ".credentials"
with open(cred_path, 'r') as f:
    creds = yaml.safe_load(f)

app_id = creds['feishu']['app_id']
app_secret = creds['feishu']['app_secret']

print("=" * 60)
print("发送文件到飞书聊天 - 正确版本")
print("=" * 60)

# 1. 获取 Tenant Token
print("\n1️⃣ 获取 Tenant Token...")
token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
token_resp = requests.post(token_url, json={
    "app_id": app_id,
    "app_secret": app_secret
})
tenant_token = token_resp.json().get('tenant_access_token')

if not tenant_token:
    print(f"❌ 获取 Token 失败：{token_resp.json()}")
    exit(1)

print(f"✅ Tenant Token: {tenant_token[:50]}...")

# 2. 准备要发送的文件
print("\n2️⃣ 准备文件...")
file_path = Path('/tmp/ai-future-presentation.html')

if not file_path.exists():
    print(f"❌ 文件不存在：{file_path}")
    exit(1)

print(f"📄 文件：{file_path.name}")
print(f"📊 大小：{file_path.stat().st_size} bytes")

# 3. 上传文件到飞书（使用正确的 API）
print("\n3️⃣ 上传文件到飞书...")

# 正确的文件上传 API
upload_url = "https://open.feishu.cn/open-apis/im/v1/files"

# 读取文件内容
with open(file_path, 'rb') as f:
    file_content = f.read()

# 使用 MultipartEncoder 发送 multipart/form-data
# 关键修正：
# 1. file_type 使用 stream（不是 html）
# 2. MIME type 使用 application/octet-stream
# 3. 不手动设置 Content-Type
form = MultipartEncoder(
    fields={
        'file_type': 'stream',  # 关键：使用 stream 而不是 html
        'file_name': file_path.name,
        'file': (file_path.name, file_content, 'application/octet-stream')
    }
)

# 设置 headers，包括 Content-Type
headers = {
    'Authorization': f'Bearer {tenant_token}'
}

# 发送请求时，requests 会自动从 form 获取 Content-Type
upload_resp = requests.post(
    upload_url,
    headers=headers,
    data=form,
    timeout=60
)
    
print(f"上传状态码：{upload_resp.status_code}")

try:
    upload_result = upload_resp.json()
    print(f"上传结果：{upload_result}")
    
    if upload_result.get('code') == 0:
        file_key = upload_result['data']['file_key']
        print(f"\n✅ 文件上传成功！")
        print(f"📄 File Key: {file_key}")
        
        # 4. 发送文件消息到聊天
        print("\n4️⃣ 发送文件消息到聊天...")
        
        chat_id = "oc_6ca477feac7842bef1e83daa8a649e70"
        
        message_url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": "chat_id"}
        
        # 构建文件消息内容
        file_content = {
            "file_key": file_key,
            "file_name": file_path.name
        }
        
        message_data = {
            "receive_id": chat_id,
            "msg_type": "file",
            "content": json.dumps(file_content)
        }
        
        message_resp = requests.post(message_url, headers=headers, params=params, json=message_data)
        
        print(f"发送状态码：{message_resp.status_code}")
        message_result = message_resp.json()
        print(f"发送结果：{message_result}")
        
        if message_result.get('code') == 0:
            print(f"\n🎉 文件发送成功！")
            print(f"📱 请在飞书聊天窗口查看文件：{file_path.name}")
        else:
            print(f"\n❌ 发送失败：{message_result.get('msg')}")
            print(f"错误详情：{message_result}")
    else:
        print(f"\n❌ 上传失败：{upload_result.get('msg')}")
        print(f"错误详情：{upload_result}")
except Exception as e:
    print(f"\n❌ 错误：{e}")
    print(f"响应内容：{upload_resp.text[:500]}")

print("\n" + "=" * 60)
