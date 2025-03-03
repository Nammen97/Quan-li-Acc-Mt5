# ✅ ĐÃ HOÀN THÀNH
import MetaTrader5 as mt5
import time
import threading
import logging
from datetime import datetime, timedelta
import pandas as pd

class MT5Service:
    def __init__(self):
        self.connected_accounts = {}  # {account_id: {mt5_instance, login, is_connected}}
        self.lock = threading.Lock()
        self.logger = logging.getLogger('mt5_service')
        
    def initialize_mt5(self):
        """Khởi tạo MT5"""
        if not mt5.initialize():
            self.logger.error(f"MT5 initialization failed! Error: {mt5.last_error()}")
            return False
        return True
    
    def connect_account(self, account):
        """Kết nối đến tài khoản MT5"""
        with self.lock:
            # Kiểm tra nếu tài khoản đã kết nối
            if account.account_id in self.connected_accounts and self.connected_accounts[account.account_id]['is_connected']:
                return True
                
            # Đảm bảo MT5 đã được khởi tạo
            if not mt5.terminal_info():
                if not self.initialize_mt5():
                    return False
            
            # Thử đăng nhập vào tài khoản
            login_result = mt5.login(
                login=account.login,
                password=account.password,
                server=account.server
            )
            
            if not login_result:
                error = mt5.last_error()
                self.logger.error(f"MT5 login failed for account {account.login}! Error: {error}")
                return False
                
            # Lưu thông tin kết nối
            self.connected_accounts[account.account_id] = {
                'login': account.login,
                'is_connected': True,
                'last_check': datetime.now()
            }
            
            return True
    
    def disconnect_account(self, account_id):
        """Ngắt kết nối tài khoản MT5"""
        with self.lock:
            if account_id in self.connected_accounts:
                # Chỉ cần đánh dấu là đã ngắt kết nối
                self.connected_accounts[account_id]['is_connected'] = False
                # Không thực sự đăng xuất khỏi MT5 vì sẽ ảnh hưởng đến các tài khoản khác
                return True
            return False
    
    def check_connection(self, account_id):
        """Kiểm tra kết nối của tài khoản"""
        with self.lock:
            if account_id not in self.connected_accounts:
                return False
                
            account_info = self.connected_accounts[account_id]
            
            # Kiểm tra xem tài khoản hiện tại có phải là tài khoản đang đăng nhập không
            if mt5.account_info() and mt5.account_info().login == account_info['login']:
                account_info['is_connected'] = True
                account_info['last_check'] = datetime.now()
                return True
                
            # Nếu không phải, thử đăng nhập lại
            return False
    
    def get_account_info(self, account_id, account=None):
        """Lấy thông tin tài khoản (balance, equity, leverage...)"""
        # Kiểm tra và kết nối tài khoản nếu cần
        if not self.check_connection(account_id):
            if not account:
                return None
            if not self.connect_account(account):
                return None
        
        # Lấy thông tin tài khoản từ MT5
        account_info = mt5.account_info()
        if not account_info:
            self.logger.error(f"Failed to get account info for {account_id}! Error: {mt5.last_error()}")
            return None
            
        # Trả về thông tin cần thiết
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'leverage': account_info.leverage,
            'profit': account_info.profit
        }
    
    def get_open_positions(self, account_id, account=None):
        """Lấy danh sách vị thế mở"""
        # Kiểm tra và kết nối tài khoản nếu cần
        if not self.check_connection(account_id):
            if not account:
                return []
            if not self.connect_account(account):
                return []
        
        # Lấy tất cả vị thế mở
        positions = mt5.positions_get()
        if positions is None:
            self.logger.error(f"No positions found for account {account_id}! Error: {mt5.last_error()}")
            return []
            
        # Chuyển đổi thành danh sách các dictionary
        result = []
        for position in positions:
            result.append({
                'ticket': position.ticket,
                'symbol': position.symbol,
                'type': 'BUY' if position.type == mt5.POSITION_TYPE_BUY else 'SELL',
                'volume': position.volume,
                'open_price': position.price_open,
                'open_time': datetime.fromtimestamp(position.time),
                'current_price': position.price_current,
                'sl': position.sl,
                'tp': position.tp,
                'profit': position.profit
            })
            
        return result
    
    def get_order_history(self, account_id, from_date, to_date=None, account=None):
        """Lấy lịch sử giao dịch"""
        # Kiểm tra và kết nối tài khoản nếu cần
        if not self.check_connection(account_id):
            if not account:
                return []
            if not self.connect_account(account):
                return []
        
        # Thiết lập thời gian
        if not to_date:
            to_date = datetime.now()
            
        # Chuyển đổi thành timestamp
        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())
        
        # Lấy lịch sử giao dịch
        history = mt5.history_deals_get(from_timestamp, to_timestamp)
        if history is None:
            self.logger.error(f"No history found for account {account_id}! Error: {mt5.last_error()}")
            return []
            
        # Chuyển đổi thành danh sách các dictionary
        result = []
        for deal in history:
            result.append({
                'ticket': deal.ticket,
                'symbol': deal.symbol,
                'type': 'BUY' if deal.type == mt5.DEAL_TYPE_BUY else 'SELL',
                'volume': deal.volume,
                'price': deal.price,
                'time': datetime.fromtimestamp(deal.time),
                'profit': deal.profit,
                'commission': deal.commission,
                'swap': deal.swap,
                'fee': deal.fee
            })
            
        return result
    
    def open_order(self, account_id, symbol, order_type, volume, price=None, sl=None, tp=None, account=None):
        """Mở lệnh giao dịch mới"""
        # Kiểm tra và kết nối tài khoản nếu cần
        if not self.check_connection(account_id):
            if not account:
                return None
            if not self.connect_account(account):
                return None
        
        # Thiết lập loại giao dịch
        if order_type.upper() == 'BUY':
            mt5_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        elif order_type.upper() == 'SELL':
            mt5_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            self.logger.error(f"Invalid order type: {order_type}")
            return None
            
        # Chuẩn bị request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": mt5_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,  # Độ lệch giá cho phép
            "magic": 123456,  # ID để nhận diện lệnh
            "comment": f"Copy Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        # Gửi lệnh
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Order failed! Error code: {result.retcode}")
            return None
            
        # Trả về thông tin lệnh
        return {
            'ticket': result.order,
            'volume': volume,
            'price': price,
            'sl': sl,
            'tp': tp
        }
    
    def close_order(self, account_id, ticket, account=None):
        """Đóng lệnh giao dịch"""
        # Kiểm tra và kết nối tài khoản nếu cần
        if not self.check_connection(account_id):
            if not account:
                return False
            if not self.connect_account(account):
                return False
        
        # Lấy thông tin vị thế
        position = mt5.positions_get(ticket=ticket)
        if not position:
            self.logger.error(f"Position {ticket} not found! Error: {mt5.last_error()}")
            return False
            
        position = position[0]
        
        # Thiết lập loại đóng lệnh (ngược với loại mở lệnh)
        if position.type == mt5.POSITION_TYPE_BUY:
            mt5_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(position.symbol).bid
        else:  # POSITION_TYPE_SELL
            mt5_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).ask
            
        # Chuẩn bị request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5_type,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "Close by Copy Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        # Gửi lệnh
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Close order failed! Error code: {result.retcode}")
            return False
            
        return True
    
    def modify_order(self, account_id, ticket, price=None, sl=None, tp=None, account=None):
        """Sửa đổi lệnh giao dịch"""
        # Kiểm tra và kết nối tài khoản nếu cần
        if not self.check_connection(account_id):
            if not account:
                return False
            if not self.connect_account(account):
                return False
        
        # Lấy thông tin vị thế
        position = mt5.positions_get(ticket=ticket)
        if not position:
            self.logger.error(f"Position {ticket} not found! Error: {mt5.last_error()}")
            return False
            
        position = position[0]
        
        # Chuẩn bị request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position.symbol,
            "sl": sl if sl is not None else position.sl,
            "tp": tp if tp is not None else position.tp,
        }
        
        # Gửi lệnh
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Modify order failed! Error code: {result.retcode}")
            return False
            
        return True