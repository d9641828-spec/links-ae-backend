import json
import urllib.request
from datetime import datetime

def handler(req):
    if req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    if req.method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'status': 'ok', 'message': 'Backend is running'})
        }
    
    if req.method != 'POST':
        return {'statusCode': 405, 'body': 'Method not allowed'}
    
    try:
        body = json.loads(req.body) if isinstance(req.body, str) else req.body
        license_code = body.get('license_code', '').strip()
        machine_id = body.get('machine_id', '').strip()
        
        if not license_code or not machine_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'message': '激活码或机器ID不能为空'})
            }
        
        # 查询 Supabase
        supabase_url = 'https://xsiqdhhhfytbofwwedeq.supabase.co'
        supabase_key = 'sb_publishable_8RIvH_HjMjuoiq3GF1U-oA_ChYXfcCH'
        
        url = f'{supabase_url}/rest/v1/licenses?license_code=eq.{license_code}'
        request = urllib.request.Request(url)
        request.add_header('Content-Type', 'application/json')
        request.add_header('apikey', supabase_key)
        request.add_header('Authorization', f'Bearer {supabase_key}')
        
        response = urllib.request.urlopen(request, timeout=10)
        licenses = json.loads(response.read().decode())
        
        if not licenses:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'message': '激活码不存在'})
            }
        
        license_record = licenses[0]
        
        if not license_record.get('is_active'):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'message': '激活码已被禁用'})
            }
        
        expire_date = datetime.fromisoformat(license_record['expire_date'].replace('Z', '+00:00'))
        if expire_date < datetime.now(expire_date.tzinfo):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'message': '激活码已过期'})
            }
        
        if license_record.get('machine_id') and license_record['machine_id'] != machine_id:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'message': '激活码已绑定到其他设备'})
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': True,
                'message': '验证成功',
                'user_id': license_record.get('user_id'),
                'subscription_type': license_record.get('subscription_type'),
                'expire_date': license_record.get('expire_date'),
                'license_code': license_code
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'success': False, 'message': f'错误: {str(e)}'})
        }

