# ✅ ĐÃ HOÀN THÀNH

from flask import Blueprint, request, jsonify
from models.user import User
from auth_routes import token_required

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    """Lấy danh sách người dùng (chỉ admin)"""
    from app import db
    
    # Kiểm tra quyền admin
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    users = db.get_all_users()
    return jsonify({
        'success': True,
        'users': [{
            'id': u.id,
            'username': u.username,
            'is_admin': u.is_admin,
            'created_at': u.created_at.isoformat() if u.created_at else None
        } for u in users]
    })

@user_routes.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """Lấy thông tin chi tiết người dùng (chỉ admin hoặc chính người dùng)"""
    from app import db
    
    # Kiểm tra quyền
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    user = db.get_user(user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': f'User with ID {user_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    })

@user_routes.route('/users', methods=['POST'])
@token_required
def create_user(current_user):
    """Tạo người dùng mới (chỉ admin)"""
    from app import db
    
    # Kiểm tra quyền admin
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Kiểm tra dữ liệu
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Kiểm tra username đã tồn tại chưa
    existing_user = db.get_user_by_username(data['username'])
    if existing_user:
        return jsonify({
            'success': False,
            'message': 'Username already exists'
        }), 400
    
    # Tạo user mới
    user = User(data['username'])
    user.set_password(data['password'])
    user.is_admin = data.get('is_admin', False)
    
    # Lưu vào database
    user_id = db.save_user(user)
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'user_id': user_id
    })

@user_routes.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """Cập nhật thông tin người dùng (chỉ admin hoặc chính người dùng)"""
    from app import db
    
    # Kiểm tra quyền
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Lấy user
    user = db.get_user(user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': f'User with ID {user_id} not found'
        }), 404
    
    # Cập nhật thông tin
    if 'username' in data and current_user.is_admin:
        # Chỉ admin mới có thể đổi username
        # Kiểm tra username đã tồn tại chưa
        if data['username'] != user.username:
            existing_user = db.get_user_by_username(data['username'])
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'Username already exists'
                }), 400
        user.username = data['username']
    
    if 'password' in data:
        # Đổi mật khẩu
        user.set_password(data['password'])
    
    if 'is_admin' in data and current_user.is_admin:
        # Chỉ admin mới có thể đổi quyền admin
        user.is_admin = data['is_admin']
    
    # Lưu vào database
    db.save_user(user)
    
    return jsonify({
        'success': True,
        'message': 'User updated successfully'
    })

@user_routes.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    """Xóa người dùng (chỉ admin)"""
    from app import db
    
    # Kiểm tra quyền admin
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    # Không thể xóa chính mình
    if current_user.id == user_id:
        return jsonify({
            'success': False,
            'message': 'Cannot delete yourself'
        }), 400
    
    # Xóa khỏi database
    if db.delete_user(user_id):
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to delete user'
        }), 500