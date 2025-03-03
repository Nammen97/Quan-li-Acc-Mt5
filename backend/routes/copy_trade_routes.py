from flask import Blueprint, request, jsonify, g
from utils.auth import login_required

copy_trade_bp = Blueprint('copy_trade', __name__)

@copy_trade_bp.route('/settings', methods=['GET'])
@login_required
def get_copy_settings():
    """Lấy tất cả thiết lập copy trade của người dùng"""
    from app import copy_trade_service

    settings = copy_trade_service.get_copy_settings(g.user.id)
    return jsonify({
        'success': True,
        'data': [setting.to_dict() for setting in settings]
    })

@copy_trade_bp.route('/settings/<setting_id>', methods=['GET'])
@login_required
def get_copy_setting(setting_id):
    """Lấy chi tiết thiết lập copy trade"""
    from app import copy_trade_service

    setting = copy_trade_service.get_copy_setting(setting_id)
    if not setting or setting.user_id != g.user.id:
        return jsonify({
            'success': False,
            'message': 'Copy setting not found'
        }), 404

    return jsonify({
        'success': True,
        'data': setting.to_dict()
    })

@copy_trade_bp.route('/settings', methods=['POST'])
@login_required
def create_copy_setting():
    """Tạo thiết lập copy trade mới"""
    from app import copy_trade_service

    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400

    required_fields = ['source_account_id', 'target_account_id']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400

    # Tạo thiết lập mới
    setting = copy_trade_service.create_copy_setting(
        user_id=g.user.id,
        source_account_id=data['source_account_id'],
        target_account_id=data['target_account_id'],
        volume_percent=data.get('volume_percent', 100),
        max_risk_percent=data.get('max_risk_percent', 5),
        include_symbols=data.get('include_symbols'),
        exclude_symbols=data.get('exclude_symbols')
    )

    if not setting:
        return jsonify({
            'success': False,
            'message': 'Failed to create copy setting'
        }), 400

    return jsonify({
        'success': True,
        'message': 'Copy setting created successfully',
        'data': setting.to_dict()
    }), 201

@copy_trade_bp.route('/settings/<setting_id>', methods=['PUT'])
@login_required
def update_copy_setting(setting_id):
    """Cập nhật thiết lập copy trade"""
    from app import copy_trade_service

    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400

    # Cập nhật thiết lập
    setting = copy_trade_service.update_copy_setting(
        setting_id=setting_id,
        user_id=g.user.id,
        **data
    )

    if not setting:
        return jsonify({
            'success': False,
            'message': 'Failed to update copy setting'
        }), 400

    return jsonify({
        'success': True,
        'message': 'Copy setting updated successfully',
        'data': setting.to_dict()