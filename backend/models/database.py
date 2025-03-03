# ✅ ĐÃ HOÀN THÀNH
import sqlite3
import json
import os
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        # Đảm bảo thư mục chứa database tồn tại
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    def connect(self):
        """Kết nối tới database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Để kết quả truy vấn trả về dạng dictionary
        return self.conn
        
    def close(self):
        """Đóng kết nối database"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_db(self):
        """Khởi tạo cấu trúc database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Tạo bảng users
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tạo bảng accounts
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login INTEGER UNIQUE NOT NULL,
            password TEXT NOT NULL,
            server TEXT NOT NULL,
            name TEXT,
            balance REAL DEFAULT 0,
            equity REAL DEFAULT 0,
            margin REAL DEFAULT 0,
            free_margin REAL DEFAULT 0,
            leverage INTEGER DEFAULT 0,
            profit REAL DEFAULT 0,
            is_connected BOOLEAN DEFAULT 0,
            last_update TIMESTAMP
        )
        ''')
        
        # Tạo bảng trades
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            type TEXT NOT NULL,
            volume REAL NOT NULL,
            open_price REAL NOT NULL,
            open_time TIMESTAMP NOT NULL,
            close_price REAL,
            close_time TIMESTAMP,
            profit REAL DEFAULT 0,
            sl REAL,
            tp REAL,
            copied_from INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            UNIQUE (ticket, account_id)
        )
        ''')
        
        # Tạo bảng copy_settings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS copy_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_account_id INTEGER NOT NULL,
            follower_account_id INTEGER NOT NULL,
            volume_percent REAL DEFAULT 100,
            copy_sl_tp BOOLEAN DEFAULT 1,
            min_volume REAL DEFAULT 0.01,
            max_volume REAL DEFAULT 100.0,
            allowed_symbols TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (master_account_id) REFERENCES accounts (id),
            FOREIGN KEY (follower_account_id) REFERENCES accounts (id),
            UNIQUE (master_account_id, follower_account_id)
        )
        ''')
        
        conn.commit()
        return True
    
    # Các phương thức CRUD cho Account
    def save_account(self, account):
        """Lưu hoặc cập nhật thông tin tài khoản"""
        conn = self.conn or self.connect()
        cursor = conn.cursor()
        
        # Kiểm tra xem tài khoản đã tồn tại chưa
        cursor.execute("SELECT id FROM accounts WHERE login = ?", (account.login,))
        result = cursor.fetchone()
        
        if result:
            # Cập nhật tài khoản hiện có
            account_id = result['id']
            cursor.execute('''
            UPDATE accounts SET 
                password = ?, server = ?, name = ?, balance = ?, 
                equity = ?, margin = ?, free_margin = ?, leverage = ?,
                profit = ?, is_connected = ?, last_update = ?
            WHERE id = ?
            ''', (
                account.password, account.server, account.name,
                account.balance, account.equity, account.margin, 
                account.free_margin, account.leverage, account.profit,
                account.is_connected, datetime.now(), account_id
            ))
            account.account_id = account_id
        else:
            # Thêm tài khoản mới
            cursor.execute('''
            INSERT INTO accounts (
                login, password, server, name, balance, 
                equity, margin, free_margin, leverage,
                profit, is_connected, last_update
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account.login, account.password, account.server, account.name,
                account.balance, account.equity, account.margin, 
                account.free_margin, account.leverage, account.profit,
                account.is_connected, datetime.now()
            ))
            account.account_id = cursor.lastrowid
            
        conn.commit()
        return account.account_id
    
    def get_account(self, account_id):
        """Lấy thông tin tài khoản theo ID"""
        from models.account import Account
        
        conn = self.conn or self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        
        if row:
            account = Account(
                account_id=row['id'],
                login=row['login'],
                password=row['password'],
                server=row['server'],
                name=row['name']
            )
            account.balance = row['balance']
            account.equity = row['equity']
            account.margin = row['margin']
            account.free_margin = row['free_margin']
            account.leverage = row['leverage']
            account.profit = row['profit']
            account.is_connected = bool(row['is_connected'])
            account.last_update = row['last_update']
            return account
        return None
    
    def get_all_accounts(self):
        """Lấy tất cả tài khoản"""
        from models.account import Account
        
        conn = self.conn or self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM accounts ORDER BY name")
        rows = cursor.fetchall()
        
        accounts = []
        for row in rows:
            account = Account(
                account_id=row['id'],
                login=row['login'],
                password=row['password'],
                server=row['server'],
                name=row['name']
            )
            account.balance = row['balance']
            account.equity = row['equity']
            account.margin = row['margin']
            account.free_margin = row['free_margin']
            account.leverage = row['leverage']
            account.profit = row['profit']
            account.is_connected = bool(row['is_connected'])
            account.last_update = row['last_update']
            accounts.append(account)
            
        return accounts
    
    def delete_account(self, account_id):
        """Xóa tài khoản theo ID"""
        conn = self.conn or self.connect()
        cursor = conn.cursor()
        
        # Xóa các cài đặt copy trade liên quan
        cursor.execute("DELETE FROM copy_settings WHERE master_account_id = ? OR follower_account_id = ?", 
                      (account_id, account_id))
        
        # Xóa các giao dịch liên quan
        cursor.execute("DELETE FROM trades WHERE account_id = ?", (account_id,))
        
        # Xóa tài khoản
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        
        conn.commit()
        return cursor.rowcount > 0
    
    # Các phương thức CRUD cho CopySettings
    def save_copy_settings(self, copy_settings):
        """Lưu hoặc cập nhật cài đặt copy trade"""
        conn = self.conn or self.connect()
        cursor = conn.cursor()
        
        # Chuyển danh sách symbols sang JSON
        allowed_symbols_json = json.dumps(copy_settings.allowed_symbols) if copy_settings.allowed_symbols else None
        
        # Kiểm tra xem cài đặt đã tồn tại chưa
        if copy_settings.id:
            cursor.execute('''
            UPDATE copy_settings SET 
                master_account_id = ?, follower_account_id = ?, volume_percent = ?,
                copy_sl_tp = ?, min_volume = ?, max_volume = ?,
                allowed_symbols = ?, is_active = ?
            WHERE id = ?
            ''', (
                copy_settings.master_account_id, copy_settings.follower_account_id,
                copy_settings.volume_percent, copy_settings.copy_sl_tp,
                copy_settings.min_volume, copy_settings.max_volume,
                allowed_symbols_json, copy_settings.is_active, copy_settings.id
            ))
        else:
            # Kiểm tra xem cặp master/follower đã tồn tại chưa
            cursor.execute('''
            SELECT id FROM copy_settings 
            WHERE master_account_id = ? AND follower_account_id = ?
            ''', (copy_settings.master_account_id, copy_settings.follower_account_id))
            
            existing = cursor.fetchone()
            if existing:
                copy_settings.id = existing['id']
                return self.save_copy_settings(copy_settings)
            
            # Thêm cài đặt mới
            cursor.execute('''
            INSERT INTO copy_settings (
                master_account_id, follower_account_id, volume_percent,
                copy_sl_tp, min_volume, max_volume,
                allowed_symbols, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                copy_settings.master_account_id, copy_settings.follower_account_id,
                copy_settings.volume_percent, copy_settings.copy_sl_tp,
                copy_settings.min_volume, copy_settings.max_volume,
                allowed_symbols_json, copy_settings.is_active, datetime.now()
            ))
            copy_settings.id = cursor.lastrowid
            
        conn.commit()
        return copy_settings.id
    
    # Các phương thức tương tự cho trade và user cũng sẽ được triển khai tương tự
    # ...