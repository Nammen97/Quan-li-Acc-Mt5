# ✅ ĐÃ HOÀN THÀNH
from datetime import datetime

class Trade:
    def __init__(self, ticket, account_id, symbol, type, volume, 
                 open_price, open_time, sl=None, tp=None):
        self.id = None
        self.ticket = ticket
        self.account_id = account_id
        self.symbol = symbol
        self.type = type.upper()  # "BUY" hoặc "SELL"
        self.volume = volume
        self.open_price = open_price
        self.open_time = open_time
        self.close_price = None
        self.close_time = None
        self.profit = 0
        self.sl = sl  # Stop Loss
        self.tp = tp  # Take Profit
        self.copied_from = None  # ID của lệnh gốc nếu đây là lệnh copy
        
    def is_open(self):
        """Kiểm tra xem lệnh có đang mở không"""
        return self.close_time is None
        
    def close(self, close_price, close_time, profit):
        """Đóng lệnh"""
        self.close_price = close_price
        self.close_time = close_time
        self.profit = profit
        
    def to_dict(self):
        """Chuyển đối tượng thành dictionary"""
        return {
            'id': self.id,
            'ticket': self.ticket,
            'account_id': self.account_id,
            'symbol': self.symbol,
            'type': self.type,
            'volume': self.volume,
            'open_price': self.open_price,
            'open_time': self.open_time.isoformat() if isinstance(self.open_time, datetime) else self.open_time,
            'close_price': self.close_price,
            'close_time': self.close_time.isoformat() if isinstance(self.close_time, datetime) else self.close_time,
            'profit': self.profit,
            'sl': self.sl,
            'tp': self.tp,
            'copied_from': self.copied_from
        }
        
    @classmethod
    def from_dict(cls, data):
        """Tạo đối tượng từ dictionary"""
        if not data:
            return None
            
        # Chuyển đổi chuỗi thời gian thành đối tượng datetime
        open_time = data.get('open_time')
        if open_time and isinstance(open_time, str):
            try:
                open_time = datetime.fromisoformat(open_time)
            except ValueError:
                open_time = None
                
        close_time = data.get('close_time')
        if close_time and isinstance(close_time, str):
            try:
                close_time = datetime.fromisoformat(close_time)
            except ValueError:
                close_time = None
                
        trade = cls(
            ticket=data.get('ticket'),
            account_id=data.get('account_id'),
            symbol=data.get('symbol'),
            type=data.get('type'),
            volume=data.get('volume'),
            open_price=data.get('open_price'),
            open_time=open_time,
            sl=data.get('sl'),
            tp=data.get('tp')
        )
        
        trade.id = data.get('id')
        trade.close_price = data.get('close_price')
        trade.close_time = close_time
        trade.profit = data.get('profit', 0)
        trade.copied_from = data.get('copied_from')
        
        return trade