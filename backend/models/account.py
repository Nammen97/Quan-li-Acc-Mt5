
# ✅ ĐÃ HOÀN THÀNH
from datetime import datetime

class Account:
    def __init__(self, account_id=None, login=None, password=None, server=None, name=None):
        self.account_id = account_id
        self.login = login
        self.password = password
        self.server = server
        self.name = name or f"Account {login}"
        self.balance = 0
        self.equity = 0
        self.margin = 0
        self.free_margin = 0
        self.leverage = 0
        self.profit = 0
        self.is_connected = False
        self.last_update = None
        
    def update_stats(self, stats):
        """Cập nhật thông số tài khoản từ dictionary"""
        if not stats:
            return False
            
        self.balance = stats.get('balance', self.balance)
        self.equity = stats.get('equity', self.equity)
        self.margin = stats.get('margin', self.margin)
        self.free_margin = stats.get('free_margin', self.free_margin)
        self.leverage = stats.get('leverage', self.leverage)
        self.profit = stats.get('profit', self.profit)
        self.is_connected = True
        self.last_update = datetime.now()
        return True
        
    def to_dict(self):
        """Tạo dictionary từ thông tin tài khoản (để lưu DB hoặc JSON)"""
        return {
            'account_id': self.account_id,
            'login': self.login,
            'password': self.password,
            'server': self.server,
            'name': self.name,
            'balance': self.balance,
            'equity': self.equity,
            'margin': self.margin,
            'free_margin': self.free_margin,
            'leverage': self.leverage,
            'profit': self.profit,
            'is_connected': self.is_connected,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
        
    @classmethod
    def from_dict(cls, data):
        """Tạo đối tượng Account từ dictionary"""
        account = cls(
            account_id=data.get('account_id'),
            login=data.get('login'),
            password=data.get('password'),
            server=data.get('server'),
            name=data.get('name')
        )
        
        account.balance = data.get('balance', 0)
        account.equity = data.get('equity', 0)
        account.margin = data.get('margin', 0)
        account.free_margin = data.get('free_margin', 0)
        account.leverage = data.get('leverage', 0)
        account.profit = data.get('profit', 0)
        account.is_connected = data.get('is_connected', False)
        
        last_update = data.get('last_update')
        if last_update and isinstance(last_update, str):
            try:
                account.last_update = datetime.fromisoformat(last_update)
            except ValueError:
                account.last_update = None
        else:
            account.last_update = last_update
            
        return account