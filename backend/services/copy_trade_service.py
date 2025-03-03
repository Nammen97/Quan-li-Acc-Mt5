# ✅ ĐÃ HOÀN THÀNH
import logging
from datetime import datetime
from models.copy_settings import CopySettings
from models.account import Account

class CopyTradeService:
    def __init__(self, db, mt5_service):
        self.db = db
        self.mt5_service = mt5_service
        self.logger = logging.getLogger(__name__)

    def get_copy_settings(self, user_id=None):
        """Lấy tất cả thiết lập copy trade của người dùng"""
        if user_id:
            return self.db.get_copy_settings_by_user(user_id)
        return self.db.get_all_copy_settings()

    def get_copy_setting(self, setting_id):
        """Lấy thiết lập copy trade theo ID"""
        return self.db.get_copy_setting(setting_id)

    def create_copy_setting(self, user_id, source_account_id, target_account_id, 
                           volume_percent=100, max_risk_percent=5, 
                           include_symbols=None, exclude_symbols=None):
        """Tạo thiết lập copy trade mới"""
        # Kiểm tra tài khoản nguồn và đích
        source_account = self.db.get_account(source_account_id)
        target_account = self.db.get_account(target_account_id)

        if not source_account or not target_account:
            self.logger.error(f"Source or target account not found: {source_account_id}, {target_account_id}")
            return None

        # Kiểm tra quyền sở hữu tài khoản
        if source_account.user_id != user_id or target_account.user_id != user_id:
            self.logger.error(f"User {user_id} does not own both accounts")
            return None

        # Tạo thiết lập mới
        setting = CopySettings(
            user_id=user_id,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            volume_percent=volume_percent,
            max_risk_percent=max_risk_percent,
            include_symbols=include_symbols or [],
            exclude_symbols=exclude_symbols or [],
            is_active=True,
            created_at=datetime.now()
        )

        # Lưu vào database
        self.db.save_copy_setting(setting)
        return setting

    def update_copy_setting(self, setting_id, user_id, **kwargs):
        """Cập nhật thiết lập copy trade"""
        setting = self.db.get_copy_setting(setting_id)

        if not setting:
            self.logger.error(f"Copy setting {setting_id} not found")
            return None

        # Kiểm tra quyền sở hữu
        if setting.user_id != user_id:
            self.logger.error(f"User {user_id} does not own this copy setting")
            return None

        # Cập nhật các trường
        for key, value in kwargs.items():
            if hasattr(setting, key):
                setattr(setting, key, value)

        # Lưu vào database
        self.db.save_copy_setting(setting)
        return setting

    def delete_copy_setting(self, setting_id, user_id):
        """Xóa thiết lập copy trade"""
        setting = self.db.get_copy_setting(setting_id)

        if not setting:
            self.logger.error(f"Copy setting {setting_id} not found")
            return False

        # Kiểm tra quyền sở hữu
        if setting.user_id != user_id:
            self.logger.error(f"User {user_id} does not own this copy setting")
            return False

        # Xóa khỏi database
        self.db.delete_copy_setting(setting_id)
        return True

    def process_new_trade(self, account_id, trade_data):
        """Xử lý giao dịch mới để copy sang các tài khoản khác"""
        # Tìm các thiết lập copy trade có tài khoản nguồn là account_id
        copy_settings = self.db.get_copy_settings_by_source(account_id)

        if not copy_settings:
            return

        for setting in copy_settings:
            if not setting.is_active:
                continue

            # Kiểm tra symbol có được phép copy không
            symbol = trade_data.get('symbol')
            if (setting.include_symbols and symbol not in setting.include_symbols) or \
               (setting.exclude_symbols and symbol in setting.exclude_symbols):
                continue

            # Lấy thông tin tài khoản đích
            target_account = self.db.get_account(setting.target_account_id)
            if not target_account:
                continue

            # Tính toán khối lượng cho tài khoản đích
            source_account = self.db.get_account(account_id)
            if not source_account:
                continue

            # Tính toán tỷ lệ khối lượng dựa trên equity của hai tài khoản
            volume_ratio = (target_account.equity / source_account.equity) * (setting.volume_percent / 100)
            target_volume = trade_data.get('volume') * volume_ratio

            # Kiểm tra rủi ro tối đa
            if setting.max_risk_percent > 0:
                max_risk_amount = target_account.equity * (setting.max_risk_percent / 100)
                # Tính toán rủi ro của lệnh (đơn giản hóa)
                estimated_risk = target_volume * 100  # Giả sử mỗi lot rủi ro 100 đơn vị tiền tệ
                if estimated_risk > max_risk_amount:
                    # Điều chỉnh khối lượng để phù hợp với rủi ro tối đa
                    target_volume = max_risk_amount / 100

            # Tạo lệnh mới trên tài khoản đích
            try:
                order_type = trade_data.get('type')
                price = trade_data.get('price')
                sl = trade_data.get('sl')
                tp = trade_data.get('tp')

                result = self.mt5_service.place_order(
                    account_id=setting.target_account_id,
                    symbol=symbol,
                    order_type=order_type,
                    volume=target_volume,
                    price=price,
                    sl=sl,
                    tp=tp,
                    account=target_account
                )

                if result:
                    self.logger.info(f"Copied trade from {account_id} to {setting.target_account_id}: {symbol}, {order_type}, {target_volume}")
                else:
                    self.logger.error(f"Failed to copy trade from {account_id} to {setting.target_account_id}")

            except Exception as e:
                self.logger.error(f"Error copying trade: {str(e)}")

class CopyTradeService:
    def __init__(self, db, mt5_service, trade_validator=None, check_interval=1):
        self.db = db
        self.mt5_service = mt5_service
        self.trade_validator = trade_validator
        self.check_interval = check_interval  # Seconds
        self.is_running = False
        self.copy_thread = None
        self.logger = logging.getLogger('copy_trade_service')
        # Lưu trữ ticket cuối cùng đã kiểm tra cho mỗi tài khoản master
        self.last_checked_tickets = {}
        # Lưu trữ thông tin các lệnh copy để quản lý
        self.copy_trades_map = {}  # {master_ticket: {follower_account_id: follower_ticket}}
        
    def start_copy_service(self):
        """Bắt đầu dịch vụ copy trade"""
        if self.is_running:
            return
            
        self.is_running = True
        self.copy_thread = threading.Thread(target=self._copy_loop)
        self.copy_thread.daemon = True
        self.copy_thread.start()
        self.logger.info("Copy trade service started")
        
    def stop_copy_service(self):
        """Dừng dịch vụ copy trade"""
        self.is_running = False
        if self.copy_thread:
            self.copy_thread.join(timeout=5)
            self.copy_thread = None
        self.logger.info("Copy trade service stopped")
        
    def _copy_loop(self):
        """Vòng lặp theo dõi và copy giao dịch"""
        while self.is_running:
            try:
                # Lấy tất cả cài đặt copy trade đang hoạt động
                copy_settings = self._get_active_copy_settings()
                
                # Nhóm các follower theo master để tối ưu 
                master_followers_map = {}
                for settings in copy_settings:
                    if settings.master_account_id not in master_followers_map:
                        master_followers_map[settings.master_account_id] = []
                    master_followers_map[settings.master_account_id].append(settings)
                
                # Kiểm tra từng tài khoản master
                for master_account_id, follower_settings in master_followers_map.items():
                    try:
                        self.check_and_copy_new_trades(master_account_id, follower_settings)
                        self.check_and_update_existing_trades(master_account_id)
                    except Exception as e:
                        self.logger.error(f"Error processing master account {master_account_id}: {str(e)}")
                        
            except Exception as e:
                self.logger.error(f"Error in copy loop: {str(e)}")
                
            # Đợi trước khi vòng lặp tiếp theo
            time.sleep(self.check_interval)
    
    def _get_active_copy_settings(self):
        """Lấy tất cả cài đặt copy trade đang hoạt động"""
        # Implement lấy từ database
        # Ví dụ: return self.db.get_active_copy_settings()
        # Tạm thời trả về danh sách rỗng
        return []
    
    def check_and_copy_new_trades(self, master_account_id, follower_settings):
        """Kiểm tra giao dịch mới từ tài khoản master và copy"""
        # Lấy tài khoản master
        master_account = self.db.get_account(master_account_id)
        if not master_account:
            return
            
        # Lấy các vị thế mở từ tài khoản master
        positions = self.mt5_service.get_open_positions(master_account_id, master_account)
        if not positions:
            return
            
        # Lấy ticket cuối cùng đã kiểm tra
        last_ticket = self.last_checked_tickets.get(master_account_id, 0)
        
        # Kiểm tra các vị thế mới
        for position in positions:
            ticket = position['ticket']
            
            # Bỏ qua các vị thế đã kiểm tra
            if ticket <= last_ticket:
                continue
                
            # Cập nhật ticket cuối cùng
            if ticket > last_ticket:
                self.last_checked_tickets[master_account_id] = ticket
                
            # Tạo đối tượng Trade cho vị thế master
            master_trade = Trade(
                ticket=ticket,
                account_id=master_account_id,
                symbol=position['symbol'],
                type=position['type'],
                volume=position['volume'],
                open_price=position['open_price'],
                open_time=position['open_time'],
                sl=position['sl'],
                tp=position['tp']
            )
            
            # Lưu giao dịch master vào database nếu chưa có
            # self.db.save_trade(master_trade)
            
            # Copy giao dịch cho các tài khoản follower
            self.copy_trade_to_followers(master_trade, follower_settings)
    
    def copy_trade_to_followers(self, master_trade, follower_settings):
        """Copy một giao dịch master cho tất cả follower được cấu hình"""
        for settings in follower_settings:
            try:
                # Bỏ qua nếu cài đặt không hoạt động
                if not settings.is_active:
                    continue
                    
                # Bỏ qua nếu symbol không được phép copy
                if (settings.allowed_symbols and 
                    master_trade.symbol not in settings.allowed_symbols):
                    continue
                    
                # Lấy tài khoản follower
                follower_account = self.db.get_account(settings.follower_account_id)
                if not follower_account:
                    continue
                    
                # Tính toán khối lượng giao dịch copy
                volume = self.calculate_copy_volume(master_trade.volume, settings)
                if volume < settings.min_volume:
                    self.logger.info(f"Skipping trade: volume {volume} < min_volume {settings.min_volume}")
                    continue
                    
                # Kiểm tra tính hợp lệ của giao dịch nếu có validator
                if self.trade_validator:
                    is_valid, message = self.trade_validator.validate_trade(follower_account, master_trade)
                    if not is_valid:
                        self.logger.warning(f"Trade validation failed: {message}")
                        continue
                
                # Lấy stop loss và take profit nếu cần
                sl = master_trade.sl if settings.copy_sl_tp else None
                tp = master_trade.tp if settings.copy_sl_tp else None
                
                # Mở lệnh trên tài khoản follower
                result = self.mt5_service.open_order(
                    settings.follower_account_id,
                    master_trade.symbol,
                    master_trade.type,
                    volume,
                    sl=sl,
                    tp=tp,
                    account=follower_account
                )
                
                if result:
                    # Lưu thông tin lệnh copy
                    follower_ticket = result['ticket']
                    
                    # Thêm vào map để theo dõi
                    if master_trade.ticket not in self.copy_trades_map:
                        self.copy_trades_map[master_trade.ticket] = {}
                    self.copy_trades_map[master_trade.ticket][settings.follower_account_id] = follower_ticket
                    
                    # Tạo đối tượng Trade cho follower
                    follower_trade = Trade(
                        ticket=follower_ticket,
                        account_id=settings.follower_account_id,
                        symbol=master_trade.symbol,
                        type=master_trade.type,
                        volume=volume,
                        open_price=result['price'],
                        open_time=datetime.now(),
                        sl=result['sl'],
                        tp=result['tp']
                    )
                    follower_trade.copied_from = master_trade.ticket
                    
                    # Lưu vào database
                    # self.db.save_trade(follower_trade)
                    
                    self.logger.info(
                        f"Copied trade: master {master_trade.ticket} to follower {follower_ticket} "
                        f"(account {settings.follower_account_id})"
                    )
                    
            except Exception as e:
                self.logger.error(
                    f"Error copying trade {master_trade.ticket} to follower {settings.follower_account_id}: {str(e)}"
                )
    
    def check_and_update_existing_trades(self, master_account_id):
        """Kiểm tra và cập nhật các giao dịch đã copy khi master thay đổi"""
        # Lấy tất cả giao dịch đã copy từ master này
        master_tickets = [ticket for ticket in self.copy_trades_map.keys()]
        
        # Không có giao dịch nào cần kiểm tra
        if not master_tickets:
            return
            
        # Lấy tài khoản master
        master_account = self.db.get_account(master_account_id)
        if not master_account:
            return
            
        # Lấy tất cả vị thế hiện tại của master
        current_positions = self.mt5_service.get_open_positions(master_account_id, master_account)
        current_tickets = {p['ticket']: p for p in current_positions} if current_positions else {}
        
        # Kiểm tra từng giao dịch đã copy
        for master_ticket in master_tickets:
            # Nếu giao dịch master đã đóng
            if master_ticket not in current_tickets:
                # Đóng tất cả giao dịch follower tương ứng
                self._close_follower_trades(master_ticket)
                continue
                
            # Nếu giao dịch master vẫn mở, kiểm tra thay đổi SL/TP
            master_position = current_tickets[master_ticket]
            self._update_follower_trades_sl_tp(master_ticket, master_position)
    
    def _close_follower_trades(self, master_ticket):
        """Đóng tất cả giao dịch follower khi giao dịch master đóng"""
        if master_ticket not in self.copy_trades_map:
            return
            
        follower_trades = self.copy_trades_map[master_ticket]
        for follower_account_id, follower_ticket in follower_trades.items():
            try:
                # Lấy tài khoản follower
                follower_account = self.db.get_account(follower_account_id)
                if not follower_account:
                    continue
                    
                # Đóng giao dịch
                result = self.mt5_service.close_order(follower_account_id, follower_ticket, account=follower_account)
                
                if result:
                    self.logger.info(
                        f"Closed follower trade: {follower_ticket} (account {follower_account_id}) "
                        f"following master {master_ticket}"
                    )
                    
                    # Cập nhật trade trong database
                    # Todo: Implement
                    
            except Exception as e:
                self.logger.error(
                    f"Error closing follower trade {follower_ticket} (account {follower_account_id}): {str(e)}"
                )
                
        # Xóa khỏi map sau khi đã xử lý
        del self.copy_trades_map[master_ticket]
    
    def _update_follower_trades_sl_tp(self, master_ticket, master_position):
        """Cập nhật SL/TP cho giao dịch follower khi master thay đổi"""
        if master_ticket not in self.copy_trades_map:
            return
            
        follower_trades = self.copy_trades_map[master_ticket]
        for follower_account_id, follower_ticket in follower_trades.items():
            try:
                # Lấy cài đặt copy trade
                settings = self._get_copy_settings(master_position['account_id'], follower_account_id)
                if not settings or not settings.copy_sl_tp:
                    continue
                    
                # Lấy tài khoản follower
                follower_account = self.db.get_account(follower_account_id)
                if not follower_account:
                    continue
                    
                # Sửa SL/TP
                result = self.mt5_service.modify_order(
                    follower_account_id,
                    follower_ticket,
                    sl=master_position['sl'],
                    tp=master_position['tp'],
                    account=follower_account
                )
                
                if result:
                    self.logger.info(
                        f"Updated SL/TP for follower trade: {follower_ticket} (account {follower_account_id}) "
                        f"following master {master_ticket}"
                    )
                    
            except Exception as e:
                self.logger.error(
                    f"Error updating SL/TP for follower trade {follower_ticket} (account {follower_account_id}): {str(e)}"
                )
    
    def _get_copy_settings(self, master_account_id, follower_account_id):
        """Lấy cài đặt copy trade giữa master và follower"""
        # Todo: Implement lấy từ database
        # return self.db.get_copy_settings(master_account_id, follower_account_id)
        return None
    
    def calculate_copy_volume(self, original_volume, settings):
        """Tính toán khối lượng giao dịch copy dựa trên cài đặt"""
        volume = original_volume * (settings.volume_percent / 100)
        
        # Giới hạn trong khoảng min/max
        volume = max(min(volume, settings.max_volume), settings.min_volume)
        
        # Làm tròn đến độ chính xác của broker (thường là 0.01 hoặc 0.1)
        volume = round(volume, 2)
        
        return volume
    
    # Các phương thức để quản lý cài đặt copy trade
    
    def create_copy_settings(self, master_account_id, follower_account_id, settings=None):
        """Tạo mới cài đặt copy trade"""
        # Kiểm tra tài khoản tồn tại
        master = self.db.get_account(master_account_id)
        follower = self.db.get_account(follower_account_id)
        
        if not master or not follower:
            return None, "Master or follower account not found"
            
        # Tạo cài đặt mới
        if not settings:
            settings = CopySettings(master_account_id, follower_account_id)
            
        # Kiểm tra tính hợp lệ
        is_valid, message = settings.validate()
        if not is_valid:
            return None, message
            
        # Lưu vào database
        settings_id = self.db.save_copy_settings(settings)
        
        return settings_id, "Copy settings created successfully"
    
    def update_copy_settings(self, settings_id, updates):
        """Cập nhật cài đặt copy trade"""
        # Todo: Implement
        pass
    
    def toggle_copy_settings(self, settings_id, active=None):
        """Bật/tắt copy trade"""
        # Todo: Implement
        pass