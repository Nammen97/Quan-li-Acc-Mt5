# ✅ ĐÃ HOÀN THÀNH

from flask import Blueprint, request, jsonify
from models.account import Account

account_routes = Blueprint('account_routes', __name__)

@account_routes.route('/accounts', methods=['GET'])
def get_all_accounts():
    """Lấy danh sách tất cả tài khoản"""
    from app import db, account_monitor_service
    
    accounts = db.get_all_accounts()
    return jsonify({
        'success': True,
        'accounts': [account.to_dict() for account in accounts]
    })

@account_routes.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    """Lấy thông tin chi tiết một tài khoản"""
    from app import db, account_monitor_service
    
    account = db.get_account(account_id)
    if not account:
        return jsonify({
            'success': False,
            'message': f'Account with ID {account_id} not found'
        }), 404
    
    # Cập nhật thông tin từ MT5 nếu tài khoản đã kết nối
    if account.is_connected:
        account_monitor_service.update_account_info(account)
    
    return jsonify({
        'success': True,
        'account': account.to_dict()
    })

@account_routes.route('/accounts', methods=['POST'])
def create_account():
    """Tạo tài khoản mới"""
    from app import db, mt5_service
    
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Kiểm tra dữ liệu
    required_fields = ['login', 'password', 'server']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Tạo tài khoản mới
    account = Account(
        login=data['login'],
        password=data['password'],
        server=data['server'],
        name=data.get('name')
    )
    
    # Kiểm tra kết nối
    if mt5_service.connect_account(account):
        # Cập nhật thông tin tài khoản
        account_info = mt5_service.get_account_info(None, account)
        if account_info:
            account.update_stats(account_info)
    
    # Lưu vào database
    account_id = db.save_account(account)
    
    return jsonify({
        'success': True,
        'message': 'Account created successfully',
        'account_id': account_id
    })

@account_routes.route('/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """Cập nhật thông tin tài khoản"""
    from app import db, mt5_service
    
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Lấy tài khoản
    account = db.get_account(account_id)
    if not account:
        return jsonify({
            'success': False,
            'message': f'Account with ID {account_id} not found'
        }), 404
    
    # Cập nhật thông tin
    if 'name' in data:
        account.name = data['name']
    if 'password' in data:
        account.password = data['password']
    if 'server' in data:
        account.server = data['server']
    
    # Cập nhật kết nối nếu thông tin đăng nhập thay đổi
    if 'password' in data or 'server' in data:
        if mt5_service.connect_account(account):
            # Cập nhật thông tin tài khoản
            account_info = mt5_service.get_account_info(account_id, account)
            if account_info:
                account.update_stats(account_info)
    
    # Lưu vào database
    db.save_account(account)
    
    return jsonify({
        'success': True,
        'message': 'Account updated successfully'
    })

@account_routes.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Xóa tài khoản"""
    from app import db, mt5_service
    
    # Lấy tài khoản
    account = db.get_account(account_id)
    if not account:
        return jsonify({
            'success': False,
            'message': f'Account with ID {account_id} not found'
        }), 404
    
    # Ngắt kết nối trước khi xóa
    if account.is_connected:
        mt5_service.disconnect_account(account_id)
    
    # Xóa khỏi database
    if db.delete_account(account_id):
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to delete account'
        }), 500

@account_routes.route('/accounts/<int:account_id>/connect', methods=['POST'])
def connect_account(account_id):
    """Kết nối tới tài khoản MT5"""
    from app import db, mt5_service, account_monitor_service
    
    # Lấy tài khoản
    account = db.get_account(account_id)
    if not account:
        return jsonify({
            'success': False,
            'message': f'Account with ID {account_id} not found'
        }), 404
    
    # Kết nối tài khoản
    if mt5_service.connect_account(account):
        # Cập nhật thông tin tài khoản
        account_monitor_service.update_account_info(account)
        
        return jsonify({
            'success': True,
            'message': 'Account connected successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to connect account'
        }), 500

@account_routes.route('/accounts/<int:account_id>/disconnect', methods=['POST'])
def disconnect_account(account_id):
    """Ngắt kết nối tài khoản MT5"""
    from app import db, mt5_service
    
    # Ngắt kết nối tài khoản
    if mt5_service.disconnect_account(account_id):
        # Cập nhật trạng thái tài khoản
        account = db.get_account(account_id)
        if account:
            account.is_connected = False
            db.save_account(account)
            
        return jsonify({
            'success': True,
            'message': 'Account disconnected successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to disconnect account'
        }), 500