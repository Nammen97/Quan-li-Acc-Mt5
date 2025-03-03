# ✅ ĐÃ HOÀN THÀNH

from flask import Blueprint, request, jsonify
from auth_routes import token_required

monitor_routes = Blueprint('monitor_routes', __name__)

@monitor_routes.route('/monitor/dashboard', methods=['GET'])
@token_required
def get_dashboard_data(current_user):
    """Lấy dữ liệu tổng quan cho dashboard"""
    from app import account_monitor_service
    
    data = account_monitor_service.get_dashboard_data()
    return jsonify({
        'success': True,
        'data': data
    })

@monitor_routes.route('/monitor/accounts/<int:account_id>/trades', methods=['GET'])
@token_required
def get_account_trades(current_user, account_id):
    """Lấy danh sách giao dịch của tài khoản"""
    from app import db, mt5_service
    
    # Lấy tài khoản
    account = db.get_account(account_id)
    if not account:
        return jsonify({
            'success': False,
            'message': f'Account with ID {account_id} not found'
        }), 404
    
    # Lấy các vị thế mở
    positions = mt5_service.get_open_positions(account_id, account)
    
    return jsonify({
        'success': True,
        'positions': positions
    })

@monitor_routes.route('/monitor/accounts/<int:account_id>/stats', methods=['GET'])
@token_required
def get_account_stats(current_user, account_id):
    """Lấy thống kê của tài khoản"""
    from app import account_monitor_service
    
    stats = account_monitor_service.get_account_stats(account_id)
    if not stats:
        return jsonify({
            'success': False,
            'message': f'Account with ID {account_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'stats': stats
    })

@monitor_routes.route('/monitor/accounts/<int:account_id>/performance', methods=['GET'])
@token_required
def get_account_performance(current_user, account_id):
    """Lấy thống kê hiệu suất của tài khoản"""
    from app import performance_service
    
    # Lấy các tham số từ query string
    time_range = request.args.get('range', 'monthly')
    
    if time_range == 'daily':
        days = int(request.args.get('days', 30))
        performance = performance_service.calculate_daily_performance(account_id, days)
        if performance is None:
            return jsonify({
                'success': False,
                'message': f'Account with ID {account_id} not found'
            }), 404
            
        # Chuyển DataFrame thành list
        performance_data = performance.to_dict('records') if not performance.empty else []
    else:  # monthly
        months = int(request.args.get('months', 12))
        performance = performance_service.calculate_monthly_performance(account_id, months)
        if performance is None:
            return jsonify({
                'success': False,
                'message': f'Account with ID {account_id} not found'
            }), 404
            
        # Chuyển DataFrame thành list
        performance_data = performance.to_dict('records') if not performance.empty else []
    
    return jsonify({
        'success': True,
        'performance': performance_data
    })

@monitor_routes.route('/monitor/accounts/<int:account_id>/report', methods=['GET'])
@token_required
def get_account_report(current_user, account_id):
    """Lấy báo cáo hiệu suất đầy đủ"""
    from app import performance_service
    
    report = performance_service.generate_performance_report(account_id)
    if not report:
        return jsonify({
            'success': False,
            'message': f'Account with ID {account_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'report': report
    })

@monitor_routes.route('/monitor/compare', methods=['GET'])
@token_required
def compare_accounts(current_user):
    """So sánh hiệu suất giữa các tài khoản"""
    from app import performance_service
    
    # Lấy danh sách tài khoản từ query string
    account_ids = request.args.get('accounts', '')
    if not account_ids:
        return jsonify({
            'success': False,
            'message': 'No accounts specified'
        }), 400
    
    # Chuyển đổi thành list các ID
    account_ids = [int(id) for id in account_ids.split(',')]
    
    comparison = performance_service.compare_accounts(account_ids)
    return jsonify({
        'success': True,
        'comparison': comparison
    })