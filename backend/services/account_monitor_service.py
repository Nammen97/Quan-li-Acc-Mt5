# ✅ ĐÃ HOÀN THÀNH
import threading
import time
import logging
from datetime import datetime, timedelta
from models.account import Account

class AccountMonitorService:
    def __init__(self, db, mt5_service, alert_service=None, update_interval=60):
        self.db = db
        self.mt5_service = mt5_service
        self.alert_service = alert_service
        self.update_interval = update_interval  # Seconds
        self.is_running = False
        self.monitor_thread = None
        self.logger = logging.getLogger('account_monitor')
        
    def start_monitoring(self):
        """Bắt đầu theo dõi tài khoản"""
        if self.is_running:
            return
            
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Account monitoring started")
        
    def stop_monitoring(self):
        """Dừng theo dõi tài khoản"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None
        self.logger.info("Account monitoring stopped")
        
    def _monitoring_loop(self):
        """Vòng lặp kiểm tra và cập nhật thông tin tài khoản"""
        while self.is_running:
            try:
                accounts = self.db.get_all_accounts()
                for account in accounts:
                    try:
                        self.update_account_info(account)
                    except Exception as e:
                        self.logger.error(f"Error updating account {account.login}: {str(e)}")
                        
                # Cập nhật thống kê tài khoản hàng ngày
                self._update_daily_stats()
                        
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                
            # Đợi trước khi vòng lặp tiếp theo
            time.sleep(self.update_interval)
    
    def update_account_info(self, account):
        """Cập nhật thông tin tài khoản từ MT5"""
        # Lấy thông tin tài khoản từ MT5
        account_info = self.mt5_service.get_account_info(account.account_id, account)
        
        if not account_info:
            # Nếu không lấy được thông tin, đánh dấu là mất kết nối
            account.is_connected = False
            self.db.save_account(account)
            
            # Gửi cảnh báo
            if self.alert_service:
                self.alert_service.send_alert(
                    f"Connection lost",
                    f"Lost connection to account {account.name} ({account.login})",
                    'WARNING'
                )
            return False
        
        # Lưu thông tin cũ để kiểm tra thay đổi
        old_equity = account.equity
        old_balance = account.balance
        old_margin_level = (account.equity / account.margin * 100) if account.margin > 0 else 0
        
        # Cập nhật thông tin tài khoản
        account.update_stats(account_info)
        
        # Tính toán margin level mới
        new_margin_level = (account.equity / account.margin * 100) if account.margin > 0 else 0
        
        # Kiểm tra cảnh báo
        if self.alert_service:
            # Cảnh báo mức margin thấp
            if new_margin_level < 200 and old_margin_level >= 200:
                self.alert_service.send_alert(
                    f"Low margin level",
                    f"Account {account.name} ({account.login}) has margin level {new_margin_level:.2f}%",
                    'WARNING'
                )
                
            # Cảnh báo lỗ lớn
            equity_change_percent = ((account.equity - old_equity) / old_equity * 100) if old_equity > 0 else 0
            if equity_change_percent < -5:
                self.alert_service.send_alert(
                    f"Significant equity drop",
                    f"Account {account.name} ({account.login}) equity dropped by {abs(equity_change_percent):.2f}%",
                    'WARNING'
                )
        
        # Lưu thông tin vào database
        self.db.save_account(account)
        return True
    
    def _update_daily_stats(self):
        """Cập nhật thống kê hàng ngày"""
        # Kiểm tra xem có cần cập nhật hay không (chỉ cập nhật 1 lần mỗi ngày)
        now = datetime.now()
        last_update_time = self._get_last_stats_update_time()
        
        if last_update_time and last_update_time.date() == now.date():
            return  # Đã cập nhật trong ngày hôm nay
            
        try:
            # Lấy tất cả tài khoản
            accounts = self.db.get_all_accounts()
            
            for account in accounts:
                # Lấy thống kê giao dịch
                self.get_account_stats(account.account_id)
                
            # Lưu thời gian cập nhật
            self._save_last_stats_update_time(now)
            
        except Exception as e:
            self.logger.error(f"Error updating daily stats: {str(e)}")
    
    def _get_last_stats_update_time(self):
        """Lấy thời gian cập nhật thống kê gần nhất"""
        # Todo: Implement lấy từ database hoặc file
        return None
    
    def _save_last_stats_update_time(self, time):
        """Lưu thời gian cập nhật thống kê"""
        # Todo: Implement lưu vào database hoặc file
        pass
    
    def get_account_stats(self, account_id):
        """Lấy thống kê giao dịch của tài khoản"""
        # Lấy tài khoản
        account = self.db.get_account(account_id)
        if not account:
            return None
            
        # Lấy giao dịch trong 30 ngày gần nhất
        from_date = datetime.now() - timedelta(days=30)
        trades = self.mt5_service.get_order_history(account_id, from_date, account=account)
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit': 0,
                'loss': 0,
                'net_profit': 0
            }
            
        # Tính toán thống kê
        winning_trades = [t for t in trades if t['profit'] > 0]
        losing_trades = [t for t in trades if t['profit'] < 0]
        
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
        total_profit = sum(t['profit'] for t in winning_trades)
        total_loss = sum(t['profit'] for t in losing_trades)
        net_profit = total_profit + total_loss
        
        stats = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'profit': round(total_profit, 2),
            'loss': round(total_loss, 2),
            'net_profit': round(net_profit, 2)
        }
        
        # Todo: Lưu thống kê vào database
        
        return stats
    
    def get_dashboard_data(self):
        """Lấy dữ liệu tổng quan cho dashboard"""
        accounts = self.db.get_all_accounts()
        
        total_balance = sum(a.balance for a in accounts)
        total_equity = sum(a.equity for a in accounts)
        total_profit = sum(a.profit for a in accounts)
        
        connected_accounts = sum(1 for a in accounts if a.is_connected)
        
        return {
            'total_accounts': len(accounts),
            'connected_accounts': connected_accounts,
            'disconnected_accounts': len(accounts) - connected_accounts,
            'total_balance': round(total_balance, 2),
            'total_equity': round(total_equity, 2),
            'total_profit': round(total_profit, 2),
            'accounts': [a.to_dict() for a in accounts]
        }