# ✅ ĐÃ HOÀN THÀNH

import hashlib
import os
from datetime import datetime

class User:
    def __init__(self, username, password_hash=None, is_admin=False):
        self.id = None
        self.username = username
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = None
        
    def set_password(self, password):
        """Thiết lập mật khẩu (băm + muối)"""
        salt = os.urandom(32)
        self.password_hash = self._hash_password(password, salt)
        
    def verify_password(self, password):
        """Kiểm tra mật khẩu"""
        if not self.password_hash:
            return False
            
        # Tách muối và hash
        stored_salt = self.password_hash[:32]
        stored_hash = self.password_hash[32:]
        
        # Băm mật khẩu nhập vào với muối đã lưu
        hash_attempt = self._hash_password(password, stored_salt)[32:]
        
        # So sánh hash
        return stored_hash == hash_attempt
        
    def _hash_password(self, password, salt):
        """Hàm băm mật khẩu với muối"""
        pw_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt, 
            100000
        )
        return salt + pw_hash
        
    def to_dict(self):
        """Chuyển đối tượng thành dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
    @classmethod
    def from_dict(cls, data):
        """Tạo đối tượng từ dictionary"""
        if not data:
            return None
            
        user = cls(
            username=data.get('username'),
            password_hash=data.get('password_hash'),
            is_admin=data.get('is_admin', False)
        )
        
        user.id = data.get('id')
        
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                user.created_at = datetime.fromisoformat(created_at)
            except ValueError:
                user.created_at = None
        else:
            user.created_at = created_at
            
        return user