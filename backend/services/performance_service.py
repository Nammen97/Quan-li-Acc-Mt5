# ✅ ĐÃ HOÀN THÀNH

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PerformanceService:
    def __init__(self, db, mt5_service):
        self.db = db
        self.mt5_service = mt5_service
        
    def calculate_daily_performance(self, account_id, days=30):
        """Tính toán hiệu suất hàng ngày trong khoảng thời gian"""
        # Lấy tài khoản
        account = self.db.get_account(account_id)
        if not account:
            return None
            
        # Thiết lập thời gian
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Lấy lịch sử giao dịch
        history = self.mt5_service.get_order_history(account_id, start_date, end_date, account)
        if not history:
            return pd.DataFrame()
            
        # Chuyển đổi thành DataFrame
        df = pd.DataFrame(history)
        
        # Chuyển đổi cột thời gian thành đúng định dạng
        df['date'] = pd.to_datetime(df['time']).dt.date
        
        # Tính toán lợi nhuận hàng ngày
        daily_profit = df.groupby('date')['profit'].sum()
        
        # Tạo DataFrame cho tất cả các ngày trong khoảng
        date_range = pd.date_range(start=start_date.date(), end=end_date.date(), freq='D')
        result = pd.DataFrame({'date': date_range})
        
        # Hợp nhất với kết quả đã tính
        result = result.set_index('date').join(daily_profit).fillna(0).reset_index()
        
        # Tính toán lợi nhuận tích lũy
        result['cumulative_profit'] = result['profit'].cumsum()
        
        return result
    
    def calculate_monthly_performance(self, account_id, months=12):
        """Tính toán hiệu suất hàng tháng"""
        # Lấy tài khoản
        account = self.db.get_account(account_id)
        if not account:
            return None
            
        # Thiết lập thời gian
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30*months)
        
        # Lấy lịch sử giao dịch
        history = self.mt5_service.get_order_history(account_id, start_date, end_date, account)
        if not history:
            return pd.DataFrame()
            
        # Chuyển đổi thành DataFrame
        df = pd.DataFrame(history)
        
        # Chuyển đổi cột thời gian thành đúng định dạng
        df['time'] = pd.to_datetime(df['time'])
        df['month'] = df['time'].dt.to_period('M')
        
        # Tính toán lợi nhuận hàng tháng
        monthly_profit = df.groupby('month')['profit'].sum()
        
        # Tạo DataFrame cho tất cả các tháng trong khoảng
        month_range = pd.period_range(start=start_date.to_period('M'), end=end_date.to_period('M'), freq='M')
        result = pd.DataFrame({'month': month_range})
        
        # Hợp nhất với kết quả đã tính
        result = result.set_index('month').join(monthly_profit).fillna(0).reset_index()
        
        # Chuyển đổi tháng thành chuỗi để dễ đọc
        result['month_str'] = result['month'].astype(str)
        
        # Tính toán lợi nhuận tích lũy
        result['cumulative_profit'] = result['profit'].cumsum()
        
        return result
    
    def calculate_drawdown(self, account_id):
        """Tính toán drawdown lớn nhất"""
        # Lấy hiệu suất hàng ngày
        daily_performance = self.calculate_daily_performance(account_id, days=365)
        if daily_performance.empty:
            return 0
            
        # Tính toán drawdown
        cumulative = daily_performance['cumulative_profit']
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max * 100
        
        # Trả về drawdown lớn nhất (giá trị âm)
        max_drawdown = drawdown.min()
        
        return abs(max_drawdown) if not np.isnan(max_drawdown) else 0
    
    def calculate_win_rate(self, account_id):
        """Tính tỷ lệ thắng"""
        # Lấy tài khoản
        account = self.db.get_account(account_id)
        if not account:
            return 0
            
        # Lấy lịch sử giao dịch trong 3 tháng gần nhất
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        history = self.mt5_service.get_order_history(account_id, start_date, end_date, account)
        if not history:
            return 0
            
        # Đếm số giao dịch thắng/thua
        winning_trades = sum(1 for trade in history if trade['profit'] > 0)
        total_trades = len(history)
        
        # Tính tỷ lệ thắng
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return round(win_rate, 2)
    
    def calculate_profit_factor(self, account_id):
        """Tính hệ số lợi nhuận (tổng lãi / tổng lỗ)"""
        # Lấy tài khoản
        account = self.db.get_account(account_id)
        if not account:
            return 0
            
        # Lấy lịch sử giao dịch trong 3 tháng gần nhất
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        history = self.mt5_service.get_order_history(account_id, start_date, end_date, account)
        if not history:
            return 0
            
        # Tính tổng lãi và tổng lỗ
        total_profit = sum(trade['profit'] for trade in history if trade['profit'] > 0)
        total_loss = abs(sum(trade['profit'] for trade in history if trade['profit'] < 0))
        
        # Tính hệ số lợi nhuận
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')
        
        return round(profit_factor, 2)
    
    def compare_accounts(self, account_ids):
        """So sánh hiệu suất giữa các tài khoản"""
        result = []
        
        for account_id in account_ids:
            account = self.db.get_account(account_id)
            if not account:
                continue
                
            # Tính các chỉ số
            win_rate = self.calculate_win_rate(account_id)
            profit_factor = self.calculate_profit_factor(account_id)
            max_drawdown = self.calculate_drawdown(account_id)
            
            # Lấy thông tin tài khoản
            account_info = {
                'account_id': account_id,
                'name': account.name,
                'login': account.login,
                'balance': account.balance,
                'equity': account.equity,
                'profit': account.profit,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown
            }
            
            result.append(account_info)
            
        return result
    
    def generate_performance_report(self, account_id):
        """Tạo báo cáo hiệu suất đầy đủ"""
        account = self.db.get_account(account_id)
        if not account:
            return None
            
        # Tính các chỉ số
        win_rate = self.calculate_win_rate(account_id)
        profit_factor = self.calculate_profit_factor(account_id)
        max_drawdown = self.calculate_drawdown(account_id)
        
        # Lấy hiệu suất hàng ngày và hàng tháng
        daily_performance = self.calculate_daily_performance(account_id, days=30)
        monthly_performance = self.calculate_monthly_performance(account_id, months=12)
        
        # Tạo báo cáo
        report = {
            'account': {
                'account_id': account_id,
                'name': account.name,
                'login': account.login,
                'server': account.server,
                'balance': account.balance,
                'equity': account.equity,
                'profit': account.profit,
                'leverage': account.leverage
            },
            'metrics': {
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown
            },
            'daily_performance': daily_performance.to_dict('records') if not daily_performance.empty else [],
            'monthly_performance': monthly_performance.to_dict('records') if not monthly_performance.empty else []
        }
        
        return report