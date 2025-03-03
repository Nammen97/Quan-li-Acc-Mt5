# ✅ ĐÃ HOÀN THÀNH

import os
import json
from datetime import datetime

# Tạo secret key nếu chưa có
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-for-jwt')

# Cấu hình cơ bản
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000
DB_PATH = os.path.join('data', 'mt5_manager.db')

# Tạo thư mục data nếu chưa có
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Cấu hình MT5
MT5_PATH = 'C:/Program Files/MetaTrader 5/terminal64.exe'
CONNECTION_TIMEOUT = 10  # seconds

# Khoảng thời gian kiểm tra
ACCOUNT_MONITOR_INTERVAL = 60  # seconds

# Cấu hình cảnh báo
ALERT_CONFIG = {
    'email_enabled': False,
    'email_settings': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_user': 'your-email@gmail.com',
        'smtp_password': 'your-password'
    },
    'log_enabled': True
}

# Cấu hình copy trade
COPY_TRADE_CONFIG = {
    'check_interval': 1,  # seconds
    'default_volume_percent': 100,
    'max_slippage': 5
}

# Cấu hình rủi ro
RISK_SETTINGS = {
    'max_risk_per_trade': 2,  # % vốn tối đa cho mỗi giao dịch
    'max_open_trades': 10,    # Số lệnh mở tối đa
    'max_daily_loss': 5,      # % tổn thất tối đa trong ngày
    'margin_level_min': 200   # Mức margin tối thiểu (%)
}

# Ngưỡng cảnh báo
ALERT_THRESHOLDS = {
    'margin_level': 150,  # %
    'daily_loss': 5,      # %
    'equity_drop': 10     # %
}

# Tải cấu hình từ file (nếu có)
def load_config():
    config_path = 'config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            # Cập nhật các biến toàn cục
            for key, value in config_data.items():
                if key in globals():
                    globals()[key] = value

# Lưu cấu hình ra file
def save_config():
    config_path = 'config.json'
    config_data = {key: value for key, value in globals().items() 
                  if not key.startswith('__') and not callable(value)}
    
    # Loại bỏ các module và hàm
    for key in list(config_data.keys()):
        if key in ['os', 'json', 'datetime', 'load_config', 'save_config']:
            del config_data[key]
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=4)

# Tải cấu hình khi import module
load_config()