from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from datetime import datetime
from urllib.parse import parse_qs
import hashlib
import hmac

class handler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理 POST 请求 - 验证激活码"""
        
        # CORS 头
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            license_code = data.get('license_code', '').strip()
            machine_id = data.get('machine_id', '').strip()
            
            if not license_code or not machine_id:
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': '激活码或机器ID不能为空'
                }).encode('utf-8'))
                return
            
            # 查询 Supabase
            supabase_url = "https://xsiqdhhhfytbofwwedeq.supabase.co"
            supabase_key = "sb_publishable_8RIvH_HjMjuoiq3GF1U-oA_ChYXfcCH"
            
            query_url = f"{supabase_url}/rest/v1/licenses?license_code=eq.{license_code}"
            headers = {
                "Content-Type": "application/json",
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }
            
            response = requests.get(query_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f'数据库查询失败: {response.status_code}'
                }).encode('utf-8'))
                return
            
            licenses = response.json()
            
            if not licenses or len(licenses) == 0:
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': '激活码不存在'
                }).encode('utf-8'))
                return
            
            license_record = licenses[0]
            
            # 检查激活状态
            if not license_record.get('is_active', False):
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': '激活码已被禁用'
                }).encode('utf-8'))
                return
            
            # 检查过期时间
            expire_date_str = license_record.get('expire_date', '')
            expire_date = datetime.fromisoformat(expire_date_str.replace('Z', '+00:00'))
            
            if expire_date < datetime.now(expire_date.tzinfo):
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': '激活码已过期'
                }).encode('utf-8'))
                return
            
            # 检查机器码绑定
            stored_machine_id = license_record.get('machine_id')
            
            if stored_machine_id and stored_machine_id != machine_id:
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': '激活码已绑定到其他设备，无法在此设备使用'
                }).encode('utf-8'))
                return
            
            # 如果首次使用，保存机器码
            if not stored_machine_id:
                try:
                    update_url = f"{supabase_url}/rest/v1/licenses?id=eq.{license_record['id']}"
                    requests.patch(
                        update_url,
                        json={'machine_id': machine_id},
                        headers=headers,
                        timeout=10
                    )
                except Exception as e:
                    print(f"Warning: Could not save machine_id: {e}")
            
            # ✅ 验证成功
            self.wfile.write(json.dumps({
                'success': True,
                'message': '验证成功',
                'user_id': license_record.get('user_id'),
                'subscription_type': license_record.get('subscription_type'),
                'expire_date': license_record.get('expire_date'),
                'license_code': license_code
            }).encode('utf-8'))
        
        except Exception as e:
            self.wfile.write(json.dumps({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }).encode('utf-8'))

    def do_GET(self):
        """处理 GET 请求 - 健康检查"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(json.dumps({
            'status': 'ok',
            'message': 'links-AE Backend is running'
        }).encode('utf-8'))

    def log_message(self, format, *args):
        """禁用默认日志"""
        pass

