import axios from 'axios';

export default async (req, res) => {
  // 处理 CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, message: 'Method not allowed' });
  }

  try {
    const { license_code, machine_id } = req.body;

    if (!license_code || !machine_id) {
      return res.status(400).json({
        success: false,
        message: '激活码或机器ID不能为空'
      });
    }

    // 查询 Supabase
    const supabaseUrl = 'https://xsiqdhhhfytbofwwedeq.supabase.co';
    const supabaseKey = 'sb_publishable_8RIvH_HjMjuoiq3GF1U-oA_ChYXfcCH';

    const response = await axios.get(
      `${supabaseUrl}/rest/v1/licenses?license_code=eq.${license_code}`,
      {
        headers: {
          'Content-Type': 'application/json',
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`
        }
      }
    );

    const licenses = response.data;

    if (!licenses || licenses.length === 0) {
      return res.status(404).json({
        success: false,
        message: '激活码不存在'
      });
    }

    const license = licenses[0];

    // 检查激活状态
    if (!license.is_active) {
      return res.status(403).json({
        success: false,
        message: '激活码已被禁用'
      });
    }

    // 检查过期时间
    const expireDate = new Date(license.expire_date);
    if (expireDate < new Date()) {
      return res.status(403).json({
        success: false,
        message: '激活码已过期'
      });
    }

    // 检查机器码绑定
    if (license.machine_id && license.machine_id !== machine_id) {
      return res.status(403).json({
        success: false,
        message: '激活码已绑定到其他设备'
      });
    }

    // 如果首次使用，保存机器码
    if (!license.machine_id) {
      try {
        await axios.patch(
          `${supabaseUrl}/rest/v1/licenses?id=eq.${license.id}`,
          { machine_id: machine_id },
          {
            headers: {
              'Content-Type': 'application/json',
              'apikey': supabaseKey,
              'Authorization': `Bearer ${supabaseKey}`
            }
          }
        );
      } catch (e) {
        console.log('Warning: Could not save machine_id:', e.message);
      }
    }

    // ✅ 验证成功
    return res.status(200).json({
      success: true,
      message: '验证成功',
      user_id: license.user_id,
      subscription_type: license.subscription_type,
      expire_date: license.expire_date,
      license_code: license_code
    });

  } catch (error) {
    console.error('Server error:', error);
    return res.status(500).json({
      success: false,
      message: `服务器错误: ${error.message}`
    });
  }
};

