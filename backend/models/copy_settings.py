# ✅ ĐÃ HOÀN THÀNH
from datetime import datetime

class CopySettings:
    def __init__(self, master_account_id, follower_account_id):
        self.id = None
        self.master_account_id = master_account_id
        self.follower_account_id = follower_account_id
        self.volume_percent = 100  # Tỷ lệ khối lượng copy (%)
        self.copy_sl_tp = True     # Copy Stop Loss/Take Profit
        self.min_volume = 0.01     # Khối lượng giao dịch tối thiểu
        self.max_volume = 100.0    # Khối lượng giao dịch tối đa
        self.allowed_symbols = []  # Các cặp tiền được phép copy
        self.is_active = True
        self.created_at = None
        
    def validate(self):
        """Kiểm tra tính hợp lệ của cài đặt"""
        if not self.master_account_id or not self.follower_account_id:
            return False, "Master account and follower account are required"
            
        if self.master_account_id == self.follower_account_id:
            return False, "Master account and follower account cannot be the same"
            
        if self.volume_percent <= 0:
            return False, "Volume percentage must be greater than 0"
            
        if self.min_volume <= 0:
            return False, "Minimum volume must be greater than 0"
            
        if self.max_volume < self.min_volume:
            return False, "Maximum volume cannot be less than minimum volume"
            
        return True, ""
        
    def to_dict(self):
        """Chuyển đối tượng thành dictionary"""
        return {
            'id': self.id,
            'master_account_id': self.master_account_id,
            'follower_account_id': self.follower_account_id,
            'volume_percent': self.volume_percent,
            'copy_sl_tp': self.copy_sl_tp,
            'min_volume': self.min_volume,
            'max_volume': self.max_volume,
            'allowed_symbols': self.allowed_symbols,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
    @classmethod
    def from_dict(cls, data):
        """Tạo đối tượng từ dictionary"""
        if not data:
            return None
            
        settings = cls(
            master_account_id=data.get('master_account_id'),
            follower_account_id=data.get('follower_account_id')
        )
        
        settings.id = data.get('id')
        settings.volume_percent = data.get('volume_percent', 100)
        settings.copy_sl_tp = data.get('copy_sl_tp', True)
        settings.min_volume = data.get('min_volume', 0.01)
        settings.max_volume = data.get('max_volume', 100.0)
        settings.allowed_symbols = data.get('allowed_symbols', [])
        settings.is_active = data.get('is_active', True)
        
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                settings.created_at = datetime.fromisoformat(created_at)
            except ValueError:
                settings.created_at = None
        else:
            settings.created_at = created_at
            
        return settings