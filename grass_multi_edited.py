import asyncio
import json
import time
import uuid
import ssl
from datetime import datetime
from pathlib import Path
import aiohttp
from websockets import connect, exceptions
from loguru import logger

class ProxyManager:
    """Manages proxy rotation and health tracking"""
    
    def __init__(self, proxy_file="proxy.txt"):
        self.proxy_file = proxy_file
        self.proxies = []
        self.proxy_stats = {}  # Track success/fail per proxy
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file"""
        try:
            if not Path(self.proxy_file).exists():
                logger.warning(f"⚠️ {self.proxy_file} not found, creating template...")
                with open(self.proxy_file, 'w') as f:
                    f.write("# Format: http://user:pass@ip:port or socks5://user:pass@ip:port\n")
                    f.write("# One proxy per line\n")
                    f.write("# Example:\n")
                    f.write("# http://username:password@proxy1.com:8080\n")
                    f.write("# socks5://user:pass@proxy2.com:1080\n")
                logger.info(f"✅ Created {self.proxy_file} template")
                return
            
            with open(self.proxy_file, 'r') as f:
                lines = f.readlines()
            
            self.proxies = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.proxies.append(line)
                    self.proxy_stats[line] = {'success': 0, 'fail': 0, 'last_used': None}
            
            if self.proxies:
                logger.success(f"✅ Loaded {len(self.proxies)} proxies from {self.proxy_file}")
            else:
                logger.warning(f"⚠️ No proxies found in {self.proxy_file}")
        
        except Exception as e:
            logger.error(f"❌ Error loading proxies: {e}")
    
    def get_best_proxy(self, exclude=None):
        """Get the best proxy based on success rate"""
        if not self.proxies:
            return None
        
        available = [p for p in self.proxies if p != exclude]
        if not available:
            return None
        
        # Sort by success rate (success / total attempts)
        def score(proxy):
            stats = self.proxy_stats[proxy]
            total = stats['success'] + stats['fail']
            if total == 0:
                return 1.0  # New proxy gets priority
            return stats['success'] / total
        
        available.sort(key=score, reverse=True)
        return available[0]
    
    def mark_success(self, proxy):
        """Mark proxy as successful"""
        if proxy and proxy in self.proxy_stats:
            self.proxy_stats[proxy]['success'] += 1
            self.proxy_stats[proxy]['last_used'] = datetime.now()
    
    def mark_failure(self, proxy):
        """Mark proxy as failed"""
        if proxy and proxy in self.proxy_stats:
            self.proxy_stats[proxy]['fail'] += 1
    
    def get_stats(self, proxy):
        """Get proxy statistics"""
        if proxy and proxy in self.proxy_stats:
            return self.proxy_stats[proxy]
        return None

class GrassBot:
    def __init__(self, user_id, username, proxy_manager=None, device_type="extension", 
                 ping_min=18, ping_max=25, static_proxy=None):
        self.user_id = user_id
        self.username = username
        self.proxy_manager = proxy_manager
        self.static_proxy = static_proxy  # For fixed proxy per account
        self.current_proxy = static_proxy or (proxy_manager.get_best_proxy() if proxy_manager else None)
        self.device_type = device_type.lower()
        self.ping_min = ping_min
        self.ping_max = ping_max
        self.browser_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, user_id + (self.current_proxy or "")))
        self.device_id = str(uuid.uuid4())
        
        import random
        if self.device_type == "mobile":
            mobile_user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.169 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
                "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
            ]
            self.user_agent = random.choice(mobile_user_agents)
            logger.warning(f"[{self.username}] 📱 Mode: MOBILE (3.00x) - Pastikan pakai mobile proxy!")
        else:
            desktop_user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
            ]
            self.user_agent = random.choice(desktop_user_agents)
            self.device_type = "extension"
            logger.info(f"[{self.username}] 💻 Mode: EXTENSION (2.00x) - Aman & stabil")
        
        self.connected = False
        self.retry_count = 0
        self.ping_count = 0
        self.start_time = datetime.now()
        self.rate_limit_count = 0
        self.proxy_rotation_count = 0
    
    def rotate_proxy(self):
        """Rotate to next best proxy"""
        if not self.proxy_manager or self.static_proxy:
            return False
        
        old_proxy = self.current_proxy
        self.current_proxy = self.proxy_manager.get_best_proxy(exclude=old_proxy)
        
        if self.current_proxy and self.current_proxy != old_proxy:
            self.proxy_rotation_count += 1
            proxy_display = self.current_proxy.split('@')[-1] if '@' in self.current_proxy else self.current_proxy
            logger.warning(f"[{self.username}] 🔄 Rotating proxy #{self.proxy_rotation_count} -> {proxy_display}")
            
            # Update browser_id with new proxy
            self.browser_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, self.user_id + (self.current_proxy or "")))
            return True
        
        return False
    
    async def checkin(self):
        """Get WebSocket URL with token"""
        try:
            url = "https://director.getgrass.io/checkin"
            headers = {
                "accept": "*/*",
                "content-type": "application/json",
                "user-agent": self.user_agent
            }
            data = {
                "browserId": self.browser_id,
                "userId": self.user_id,
                "version": "4.26.2",
                "extensionId": "lkbnfiajjmbhnfledhphioinpickokdi",
                "userAgent": self.user_agent,
                "deviceType": self.device_type
            }
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                kwargs = {"headers": headers, "json": data, "timeout": aiohttp.ClientTimeout(total=30)}
                
                if self.current_proxy:
                    kwargs["proxy"] = self.current_proxy
                
                async with session.post(url, **kwargs) as response:
                    if response.status in [200, 201]:
                        text = await response.text()
                        try:
                            result = json.loads(text)
                            url_ip = result['destinations'][0]
                            token = result['token']
                            ws_url = f'wss://{url_ip}/?token={token}'
                            logger.success(f"[{self.username}] ✅ Checkin OK")
                            
                            # Mark proxy as successful
                            if self.proxy_manager and self.current_proxy:
                                self.proxy_manager.mark_success(self.current_proxy)
                            
                            self.rate_limit_count = 0
                            return ws_url
                        except Exception as e:
                            logger.error(f"[{self.username}] Parse error: {e}")
                            return None
                    
                    elif response.status == 429:
                        self.rate_limit_count += 1
                        wait_time = min(300, 60 * self.rate_limit_count)
                        logger.error(f"[{self.username}] ⛔ Rate limited (429) - attempt #{self.rate_limit_count}")
                        logger.warning(f"[{self.username}] ⏳ Waiting {wait_time}s before retry...")
                        
                        # Try rotating proxy on rate limit
                        if self.proxy_manager and not self.static_proxy:
                            self.proxy_manager.mark_failure(self.current_proxy)
                            if self.rotate_proxy():
                                logger.info(f"[{self.username}] 🔄 Retrying with new proxy...")
                                await asyncio.sleep(5)
                                return await self.checkin()  # Retry with new proxy
                        
                        await asyncio.sleep(wait_time)
                        return None
                    
                    else:
                        text = await response.text()
                        logger.error(f"[{self.username}] Checkin failed ({response.status}): {text[:100]}")
                        
                        # Mark proxy as failed
                        if self.proxy_manager and self.current_proxy:
                            self.proxy_manager.mark_failure(self.current_proxy)
                        
                        return None
        
        except Exception as e:
            logger.error(f"[{self.username}] Checkin error: {e}")
            
            # Mark proxy as failed and try rotation
            if self.proxy_manager and self.current_proxy:
                self.proxy_manager.mark_failure(self.current_proxy)
                if not self.static_proxy and self.rotate_proxy():
                    logger.info(f"[{self.username}] 🔄 Retrying with new proxy...")
                    await asyncio.sleep(3)
                    return await self.checkin()
            
            return None
    
    async def send_ping(self, websocket):
        """Send ping to keep alive with random interval"""
        import random
        while self.connected:
            try:
                ping = {
                    "id": str(uuid.uuid4()),
                    "version": "1.0.0",
                    "action": "PING",
                    "data": {}
                }
                await websocket.send(json.dumps(ping))
                self.ping_count += 1
                
                next_ping = random.uniform(self.ping_min, self.ping_max)
                logger.info(f"[{self.username}] 📡 Ping #{self.ping_count} (next in {next_ping:.1f}s)")
                
                await asyncio.sleep(next_ping)
            except:
                break
    
    async def send_pong(self, websocket, msg_id):
        """Send pong response"""
        try:
            pong = {"id": msg_id, "origin_action": "PONG"}
            await websocket.send(json.dumps(pong))
        except Exception as e:
            logger.debug(f"[{self.username}] Pong error: {e}")
    
    async def authenticate(self, websocket, connection_id):
        """Authenticate"""
        auth = {
            "id": connection_id,
            "origin_action": "AUTH",
            "result": {
                "browser_id": self.browser_id,
                "user_id": self.user_id,
                "user_agent": self.user_agent,
                "timestamp": int(time.time()),
                "device_type": self.device_type,
                "version": "4.26.2",
                "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
            }
        }
        await websocket.send(json.dumps(auth))
        logger.info(f"[{self.username}] 🔐 Auth sent")
    
    async def handle_message(self, websocket, message):
        """Handle incoming messages"""
        try:
            data = json.loads(message)
            action = data.get("action")
            msg_id = data.get("id")
            
            if action == "AUTH":
                await self.authenticate(websocket, msg_id)
                logger.success(f"[{self.username}] ✅ AUTHENTICATED!")
                self.retry_count = 0
                
                # Mark proxy as successful on auth
                if self.proxy_manager and self.current_proxy:
                    self.proxy_manager.mark_success(self.current_proxy)
            
            elif action == "PING":
                await self.send_pong(websocket, msg_id)
            
            elif action == "HTTP_REQUEST":
                logger.info(f"[{self.username}] 🌐 Proxy request")
        
        except Exception as e:
            logger.debug(f"[{self.username}] Handle error: {e}")
    
    async def connect_to_grass(self):
        """Main connection loop"""
        while True:
            try:
                logger.info(f"[{self.username}] 🔄 Checking in...")
                
                if self.current_proxy:
                    proxy_display = self.current_proxy.split('@')[-1] if '@' in self.current_proxy else self.current_proxy
                    logger.info(f"[{self.username}] 🌐 Via: {proxy_display}")
                    
                    # Show proxy stats if available
                    if self.proxy_manager:
                        stats = self.proxy_manager.get_stats(self.current_proxy)
                        if stats and (stats['success'] + stats['fail']) > 0:
                            total = stats['success'] + stats['fail']
                            success_rate = (stats['success'] / total) * 100
                            logger.info(f"[{self.username}] 📊 Proxy: {stats['success']}/{total} ({success_rate:.1f}% success)")
                
                ws_url = await self.checkin()
                if not ws_url:
                    if self.rate_limit_count > 0:
                        wait = min(600, 120 * self.rate_limit_count)
                        logger.error(f"[{self.username}] ❌ Checkin failed - Rate limited")
                        logger.info(f"[{self.username}] 💤 Sleeping {wait}s to cool down...")
                    else:
                        wait = 30
                        logger.error(f"[{self.username}] ❌ Checkin failed")
                        
                        # Try proxy rotation before waiting
                        if self.proxy_manager and not self.static_proxy:
                            if self.rotate_proxy():
                                wait = 5  # Shorter wait after rotation
                    
                    await asyncio.sleep(wait)
                    continue
                
                logger.info(f"[{self.username}] 🔄 Connecting...")
                
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with connect(ws_url, ssl=ssl_context, ping_interval=None) as ws:
                    self.connected = True
                    logger.success(f"[{self.username}] ✅ Connected & Mining!")
                    
                    ping_task = asyncio.create_task(self.send_ping(ws))
                    
                    try:
                        async for msg in ws:
                            await self.handle_message(ws, msg)
                    except exceptions.ConnectionClosed:
                        logger.warning(f"[{self.username}] ⚠️ Disconnected")
                    finally:
                        ping_task.cancel()
                        self.connected = False
            
            except Exception as e:
                self.connected = False
                self.retry_count += 1
                logger.error(f"[{self.username}] ❌ Error: {str(e)[:100]}")
                
                # Try proxy rotation on error
                if self.proxy_manager and self.current_proxy and not self.static_proxy:
                    self.proxy_manager.mark_failure(self.current_proxy)
                    if self.rotate_proxy():
                        wait = 10  # Shorter wait after rotation
                    else:
                        wait = min(120, 30 + (self.retry_count * 10))
                else:
                    wait = min(120, 30 + (self.retry_count * 10))
                
                uptime = datetime.now() - self.start_time
                hours = int(uptime.total_seconds() // 3600)
                minutes = int((uptime.total_seconds() % 3600) // 60)
                
                logger.info(f"[{self.username}] ⏰ Uptime: {hours}h {minutes}m | Pings: {self.ping_count}")
                if self.proxy_rotation_count > 0:
                    logger.info(f"[{self.username}] 🔄 Proxy rotations: {self.proxy_rotation_count}")
                logger.info(f"[{self.username}] 🔄 Retry in {wait}s")
                
                await asyncio.sleep(wait)
    
    async def start(self):
        """Start bot"""
        logger.info(f"[{self.username}] 🚀 Starting")
        logger.info(f"[{self.username}] 👤 ID: {self.user_id}")
        await self.connect_to_grass()

async def run_bots(accounts, settings=None, proxy_manager=None):
    """Run multiple accounts"""
    import random
    tasks = []
    
    ping_min = 18
    ping_max = 25
    
    if settings:
        ping_min = settings.get('ping_interval_min', 18)
        ping_max = settings.get('ping_interval_max', 25)
    
    for idx, acc in enumerate(accounts):
        # Check if account has static proxy or should use rotation
        static_proxy = acc.get('proxy')
        
        bot = GrassBot(
            user_id=acc['user_id'],
            username=acc['username'],
            proxy_manager=proxy_manager if not static_proxy else None,
            static_proxy=static_proxy,
            device_type=acc.get('device_type', 'extension'),
            ping_min=ping_min,
            ping_max=ping_max
        )
        
        tasks.append(bot.start())
        
        if idx < len(accounts) - 1:
            stagger_delay = random.uniform(2, 5)
            logger.info(f"⏳ Stagger delay: {stagger_delay:.1f}s before next account...")
            await asyncio.sleep(stagger_delay)
    
    await asyncio.gather(*tasks)

def load_config():
    """Load config from file"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("❌ config.json not found!")
        logger.info("Creating default config.json...")
        
        default_config = {
            "accounts": [
                {
                    "user_id": "YOUR_USER_ID_HERE",
                    "username": "Account_1",
                    "proxy": None,
                    "device_type": "extension"
                }
            ],
            "settings": {
                "ping_interval_min": 18,
                "ping_interval_max": 25,
                "use_proxy_rotation": True,
                "proxy_file": "proxy.txt"
            }
        }
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info("✅ config.json created! Please edit it and run again.")
        exit(0)

def main():
    """Main"""
    logger.add("grass_{time}.log", rotation="1 day", retention="7 days")
    
    logger.info("=" * 70)
    logger.info("🌱 GRASS BOT - Multi Account + Auto-Rotating Proxy")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    config = load_config()
    accounts = config.get('accounts', [])
    settings = config.get('settings', {})
    
    if not accounts:
        logger.error("❌ No accounts found in config.json!")
        exit(1)
    
    # Validate accounts
    valid_accounts = []
    for acc in accounts:
        if not acc.get('user_id') or acc['user_id'] == "YOUR_USER_ID_HERE":
            logger.warning(f"⚠️ Skipping invalid account: {acc.get('username', 'Unknown')}")
            continue
        valid_accounts.append(acc)
    
    if not valid_accounts:
        logger.error("❌ No valid accounts found!")
        logger.info("Please edit config.json and add your User IDs")
        exit(1)
    
    logger.info(f"📊 Total accounts: {len(valid_accounts)}")
    
    # Initialize proxy manager
    proxy_manager = None
    use_rotation = settings.get('use_proxy_rotation', True)
    proxy_file = settings.get('proxy_file', 'proxy.txt')
    
    if use_rotation:
        proxy_manager = ProxyManager(proxy_file)
        if proxy_manager.proxies:
            logger.success(f"✅ Proxy rotation enabled with {len(proxy_manager.proxies)} proxies")
        else:
            logger.warning(f"⚠️ No proxies in {proxy_file}, rotation disabled")
            proxy_manager = None
    
    # Count proxy types
    with_static_proxy = [a for a in valid_accounts if a.get('proxy')]
    with_rotation = [a for a in valid_accounts if not a.get('proxy') and proxy_manager]
    without_proxy = [a for a in valid_accounts if not a.get('proxy') and not proxy_manager]
    
    if with_static_proxy:
        logger.info(f"🔒 Static proxy: {len(with_static_proxy)} account(s)")
    if with_rotation:
        logger.info(f"🔄 Auto-rotating proxy: {len(with_rotation)} account(s)")
    if without_proxy:
        logger.info(f"🔓 Without proxy: {len(without_proxy)} account(s)")
        logger.warning("⚠️ Make sure VPN is active for accounts without proxy!")
    
    logger.info("")
    
    ping_min = settings.get('ping_interval_min', 18)
    ping_max = settings.get('ping_interval_max', 25)
    logger.info(f"⏱️ Ping interval: {ping_min}-{ping_max} seconds (randomized)")
    logger.info("")
    
    try:
        asyncio.run(run_bots(valid_accounts, settings, proxy_manager))
    except KeyboardInterrupt:
        logger.info("\n⏹️ Stopped by user")

if __name__ == "__main__":
    main()