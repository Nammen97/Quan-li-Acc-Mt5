# ✅ ĐÃ HOÀN THÀNH

from flask import Blueprint, request, jsonify
import jwt
import datetime
from models.user import User
from functools import wraps

auth_routes = Blueprint('auth_routes', __name__)

# Middleware để kiểm tra token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from app import app
        
        token = None
        
        # Lấy token từ header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token is missing'
            }), 401
        
        try:
            # Giải mã token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Lấy user từ database
            from app import db
            current_user = db.get_user(data['user_id'])
            
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'Invalid token'
                }), 401
                
        except:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        # Truyền user vào hàm gọi
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_routes.route('/login', methods=['POST'])
def login():
    """Đăng nhập và lấy token"""
    from app import db, app
    
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
    
    # Lấy user từ database
    user = db.get_user_by_username(data['username'])
    if not user:
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401
    
    # Kiểm tra mật khẩu
    if not user.verify_password(data['password']):
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401
    
    # Tạo token
    token = jwt.encode({
        'user_id': user.id,
        'is_admin': user.is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    })

@auth_routes.route('/register', methods=['POST'])
def register():
    """Đăng ký người dùng mới"""
    from app import db
    
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
        'message': 'User registered successfully',
        'user_id': user_id
    })

@auth_routes.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Đổi mật khẩu"""
    from app import db
    
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Kiểm tra dữ liệu
    required_fields = ['old_password', 'new_password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Kiểm tra mật khẩu cũ
    if not current_user.verify_password(data['old_password']):
        return jsonify({
            'success': False,
            'message': 'Invalid old password'
        }), 401
    
    # Đổi mật khẩu
    current_user.set_password(data['new_password'])
    
    # Lưu vào database
    db.save_user(current_user)
    
    return jsonify({
        'success': True,
        'message': 'Password changed successfully'
    })

@auth_routes.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    """Lấy thông tin người dùng hiện tại"""
    return jsonify({
        'success': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'is_admin': current_user.is_admin
        }
    })