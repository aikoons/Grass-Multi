import asyncio
import json
import time
import uuid
import ssl
from datetime import datetime
import aiohttp
from websockets import connect, exceptions
from loguru import logger

class GrassBot:
    def __init__(self, user_id, username, proxy=None):
        self.user_id = user_id
        self.username = username
        self.proxy = proxy
        
        # Device info
        self.browser_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, user_id + (proxy or "")))
        self.device_id = str(uuid.uuid4())
        
        # User agent - randomize untuk setiap akun
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        import random
        self.user_agent = random.choice(user_agents)
        
        # State
        self.connected = False
        self.retry_count = 0
        self.ping_count = 0
        self.start_time = datetime.now()
        
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
                "deviceType": "extension"
            }
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                kwargs = {"headers": headers, "json": data, "timeout": aiohttp.ClientTimeout(total=30)}
                if self.proxy:
                    kwargs["proxy"] = self.proxy
                
                async with session.post(url, **kwargs) as response:
                    if response.status in [200, 201]:
                        text = await response.text()
                        try:
                            result = json.loads(text)
                            url_ip = result['destinations'][0]
                            token = result['token']
                            ws_url = f'wss://{url_ip}/?token={token}'
                            logger.success(f"[{self.username}] ✅ Checkin OK")
                            return ws_url
                        except Exception as e:
                            logger.error(f"[{self.username}] Parse error: {e}")
                            return None
                    else:
                        text = await response.text()
                        logger.error(f"[{self.username}] Checkin failed ({response.status}): {text[:100]}")
                        return None
        except Exception as e:
            logger.error(f"[{self.username}] Checkin error: {e}")
            return None
    
    async def send_ping(self, websocket):
        """Send ping to keep alive"""
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
                logger.info(f"[{self.username}] 📡 Ping #{self.ping_count}")
                await asyncio.sleep(20)
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
                "device_type": "extension",
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
                if self.proxy:
                    proxy_display = self.proxy.split('@')[-1] if '@' in self.proxy else self.proxy
                    logger.info(f"[{self.username}] 🌐 Via: {proxy_display}")
                
                ws_url = await self.checkin()
                
                if not ws_url:
                    logger.error(f"[{self.username}] ❌ Checkin failed")
                    await asyncio.sleep(30)
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
                
                wait = min(120, 30 + (self.retry_count * 10))
                uptime = datetime.now() - self.start_time
                hours = int(uptime.total_seconds() // 3600)
                minutes = int((uptime.total_seconds() % 3600) // 60)
                
                logger.info(f"[{self.username}] ⏰ Uptime: {hours}h {minutes}m | Pings: {self.ping_count}")
                logger.info(f"[{self.username}] 🔄 Retry in {wait}s")
                
                await asyncio.sleep(wait)
    
    async def start(self):
        """Start bot"""
        logger.info(f"[{self.username}] 🚀 Starting")
        logger.info(f"[{self.username}] 👤 ID: {self.user_id}")
        await self.connect_to_grass()


async def run_bots(accounts):
    """Run multiple accounts"""
    tasks = []
    for acc in accounts:
        bot = GrassBot(
            user_id=acc['user_id'],
            username=acc['username'],
            proxy=acc.get('proxy')
        )
        tasks.append(bot.start())
    
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
                    "proxy": None
                }
            ],
            "settings": {
                "ping_interval": 20,
                "reconnect_delay": 30
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
    logger.info("🌱 GRASS BOT - Multi Account + Proxy")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # Load config
    config = load_config()
    accounts = config.get('accounts', [])
    
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
    
    # Show proxy info
    with_proxy = [a for a in valid_accounts if a.get('proxy')]
    without_proxy = [a for a in valid_accounts if not a.get('proxy')]
    
    if with_proxy:
        logger.info(f"🌐 With proxy: {len(with_proxy)} account(s)")
    if without_proxy:
        logger.info(f"🔓 Without proxy: {len(without_proxy)} account(s)")
        logger.warning("⚠️ Make sure VPN is active for accounts without proxy!")
    
    logger.info("")
    
    try:
        asyncio.run(run_bots(valid_accounts))
    except KeyboardInterrupt:
        logger.info("\n⏹️ Stopped by user")


if __name__ == "__main__":
    main()
