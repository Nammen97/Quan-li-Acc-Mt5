# ✅ ĐÃ HOÀN THÀNH

from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime

# Import các route
from routes.account_routes import account_routes
from routes.auth_routes import auth_routes
from routes.copy_trade_routes import copy_trade_routes
from routes.monitor_routes import monitor_routes
from routes.user_routes import user_routes

# Import các model và service
from models.database import Database
from services.mt5_service import MT5Service
from services.account_monitor_service import AccountMonitorService
from services.copy_trade_service import CopyTradeService
from services.performance_service import PerformanceService
from utils.alerting import AlertingSystem
from utils.trade_validator import TradeValidator

# Import cấu hình
import config

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'app_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)

# Tạo thư mục logs nếu chưa có
os.makedirs('logs', exist_ok=True)

# Khởi tạo Flask app
app = Flask(__name__)
CORS(app)  # Cho phép Cross-Origin Resource Sharing

# Thiết lập cấu hình
app.config['SECRET_KEY'] = config.SECRET_KEY

# Khởi tạo các service
db = Database(config.DB_PATH)
db.connect()
db.init_db()

mt5_service = MT5Service()
alert_service = AlertingSystem(config.ALERT_CONFIG)
trade_validator = TradeValidator(config.RISK_SETTINGS if hasattr(config, 'RISK_SETTINGS') else None)
account_monitor_service = AccountMonitorService(db, mt5_service, alert_service, config.ACCOUNT_MONITOR_INTERVAL)
copy_trade_service = CopyTradeService(db, mt5_service, trade_validator, config.COPY_TRADE_CONFIG['check_interval'])
performance_service = PerformanceService(db, mt5_service)

# Đăng ký các blueprint
app.register_blueprint(account_routes, url_prefix='/api')
app.register_blueprint(auth_routes, url_prefix='/api')
app.register_blueprint(copy_trade_routes, url_prefix='/api')
app.register_blueprint(monitor_routes, url_prefix='/api')
app.register_blueprint(user_routes, url_prefix='/api')

# Route mặc định
@app.route('/')
def index():
    return jsonify({
        'app': 'MT5 Account Manager',
        'version': '1.0.0',
        'status': 'running'
    })

# Khởi động các dịch vụ khi ứng dụng khởi động
@app.before_first_request
def before_first_request():
    # Khởi tạo MT5
    mt5_service.initialize_mt5()
    
    # Khởi động dịch vụ giám sát tài khoản
    account_monitor_service.start_monitoring()
    
    # Khởi động dịch vụ copy trade
    copy_trade_service.start_copy_service()
    
    logging.info("All services started")

# Dừng các dịch vụ khi đóng ứng dụng
@app.teardown_appcontext
def teardown_appcontext(exception=None):
    account_monitor_service.stop_monitoring()
    copy_trade_service.stop_copy_service()
    db.close()
    logging.info("All services stopped")

# Xử lý lỗi 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

# Xử lý lỗi 500
@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Thêm cấu hình của thư mục static cho frontend
    app.static_folder = 'frontend/build'
    
    # Khởi động server
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )