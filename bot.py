from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from datetime import datetime
from colorama import *
import asyncio, random, string, json, re, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class Humanoid:
    def __init__(self) -> None:
        self.BASE_API = "https://prelaunch.humanoidnetwork.org"
        self.HF_API = "https://huggingface.co"
        self.REF_CODE = "HKH4KB" # 可以替换成您的邀请码
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Humanoid {Fore.BLUE + Style.BRIGHT}自动任务机器人
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}版本 {Fore.YELLOW + Style.BRIGHT}<v1.0.0>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}未找到代理文件: {filename}{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}代理列表为空{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}代理总数  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}加载代理失败: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("不支持的代理类型")
        
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            return address
        except Exception as e:
            return None
    
    def generate_payload(self, account: str, address: str, message: str):
        try:
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            return {
                "walletAddress": address,
                "signature": signature,
                "message": message
            }
        except Exception as e:
            raise Exception(f"生成请求负载失败: {str(e)}")
        
    def generate_random_x_handle(self, min_len=5, max_len=12):
        chars = string.ascii_lowercase + string.digits
        length = random.randint(min_len, max_len)
        return ''.join(random.choice(chars) for _ in range(length))
        
    def generate_tweet_id(self, x_handle):
        if x_handle is None:
            x_handle = self.generate_random_x_handle()

        tweet_id = str(random.randint(10**17, 10**18 - 1))

        return { "tweetId": f"https://x.com/{x_handle}/status/{tweet_id}" }
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. 使用代理运行{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. 不使用代理运行{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}请选择 [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "使用" if proxy_choice == 1 else 
                        "不使用"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}已选择{proxy_type}代理{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}请输入1或2{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}无效输入，请输入数字1或2{Style.RESET_ALL}")

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}代理失败时自动切换? [y/n] -> {Style.RESET_ALL}").strip().lower()

                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}无效输入，请输入 'y' 或 'n'{Style.RESET_ALL}")

        return proxy_choice, rotate_proxy
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}状态  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} 连接失败 {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def auth_nonce(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/auth/nonce"
        data = json.dumps({"walletAddress": address})
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}状态  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 获取Nonce失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_authenticate(self, account: str, address: str, message: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/auth/authenticate"
        data = json.dumps(self.generate_payload(account, address, message))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}状态  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 登录失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def user_data(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/user"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}状态  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 获取用户数据失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def apply_ref(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/referral/apply"
        data = json.dumps({"referralCode": self.REF_CODE})
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        if response.status == 400: return None
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}状态  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 应用推荐码失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def training_progress(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/training/progress"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}训练进度:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 获取进度数据失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def scrape_huggingface(self, endpoint: str, limit: int, proxy_url=None, retries=5):
        url = f"{self.HF_API}/api/{endpoint}"
        params = {"limit": limit, "sort": "lastModified", "direction": -1}
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   状态 :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 从HuggingFace获取{endpoint}数据失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def submit_training(self, address: str, training_data: dict, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/training"
        data = json.dumps(training_data)
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   状态 :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 提交失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def task_lists(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/tasks"
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}任务列表:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 获取任务数据失败 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def complete_task(self, address: str, task_id: str, title: str, recurements: dict, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/tasks"
        data = json.dumps({"taskId": task_id,"data": recurements})
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(1)
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        if response.status == 400:
                            self.log(
                                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} 任务已完成 {Style.RESET_ALL}"
                            )
                            return False
                        
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} 任务未完成 {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}代理   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue

                return False

            return True
    
    async def process_auth_login(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            nonce = await self.auth_nonce(address, proxy)
            if not nonce: return False

            message = nonce.get("message")

            authenticate = await self.auth_authenticate(account, address, message, proxy)
            if not authenticate: return False
            
            self.access_tokens[address] = authenticate.get("token")

            self.log(
                f"{Fore.CYAN + Style.BRIGHT}状态  :{Style.RESET_ALL}"
                f"{Fore.GREEN + Style.BRIGHT} 登录成功 {Style.RESET_ALL}"
            )
            return True

    async def process_accounts(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        logined = await self.process_auth_login(account, address, use_proxy, rotate_proxy)
        if logined:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            user = await self.user_data(address, proxy)
            if not user: return False

            refer_by = user.get("user", {}).get("referredBy", None)
            x_handle = user.get("user", {}).get("twitterId", None)
            total_points = user.get("totalPoints")

            if refer_by is None:
                await self.apply_ref(address, proxy)

            self.log(
                f"{Fore.CYAN + Style.BRIGHT}积分  :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {total_points} {Style.RESET_ALL}"
            )

            progress = await self.training_progress(address, proxy)
            if progress:
                self.log(f"{Fore.CYAN+Style.BRIGHT}训练进度:{Style.RESET_ALL}")

                models_completed = progress.get("daily", {}).get("models", {}).get("completed")
                models_limit = progress.get("daily", {}).get("models", {}).get("limit")
                models_remaining = progress.get("daily", {}).get("models", {}).get("remaining")

                self.log(f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}模型训练{Style.RESET_ALL}"
                )
                if models_remaining > 0:
                    models = await self.scrape_huggingface("models", models_remaining, proxy)
                    if models:
                        for model in models:
                            model_name = model["id"]
                            model_url = f"{self.HF_API}/{model['id']}"

                            training_data = {
                                "fileName": model_name,
                                "fileUrl": model_url,
                                "fileType": "model",
                                "recaptchaToken": ""
                            }

                            self.log(
                                f"{Fore.BLUE+Style.BRIGHT}   ==={Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT} 第 {models_completed+1} 个 / 共 {models_limit} 个 {Style.RESET_ALL}"
                                f"{Fore.BLUE+Style.BRIGHT}==={Style.RESET_ALL}"
                            )

                            submit = await self.submit_training(address, training_data, proxy)
                            if submit:
                                self.log(
                                    f"{Fore.BLUE+Style.BRIGHT}   状态 :{Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT} 模型提交成功 {Style.RESET_ALL}"
                                )
                                self.log(
                                    f"{Fore.BLUE+Style.BRIGHT}   名称 :{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {model_name} {Style.RESET_ALL}"
                                )
                                self.log(
                                    f"{Fore.BLUE+Style.BRIGHT}   链接 :{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {model_url} {Style.RESET_ALL}"
                                )

                            models_completed+=1

                else:
                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   状态 :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} 每日模型训练次数已用完 [{models_completed}/{models_limit}] {Style.RESET_ALL}"
                    )

                datasets_completed = progress.get("daily", {}).get("datasets", {}).get("completed")
                datasets_limit = progress.get("daily", {}).get("datasets", {}).get("limit")
                datasets_remaining = progress.get("daily", {}).get("datasets", {}).get("remaining")

                self.log(f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}数据集训练{Style.RESET_ALL}"
                )
                if datasets_remaining > 0:
                    datasets = await self.scrape_huggingface("datasets", datasets_remaining, proxy)
                    if datasets:
                        for dataset in datasets:
                            dataset_name = dataset["id"]
                            dataset_url = f"{self.HF_API}/datasets/{dataset['id']}"

                            training_data = {
                                "fileName": dataset_name,
                                "fileUrl": dataset_url,
                                "fileType": "dataset",
                                "recaptchaToken": ""
                            }

                            self.log(
                                f"{Fore.BLUE+Style.BRIGHT}   ==={Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT} 第 {datasets_completed+1} 个 / 共 {datasets_limit} 个 {Style.RESET_ALL}"
                                f"{Fore.BLUE+Style.BRIGHT}==={Style.RESET_ALL}"
                            )

                            submit = await self.submit_training(address, training_data, proxy)
                            if submit:
                                self.log(
                                    f"{Fore.BLUE+Style.BRIGHT}   状态 :{Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT} 数据集提交成功 {Style.RESET_ALL}"
                                )
                                self.log(
                                    f"{Fore.BLUE+Style.BRIGHT}   名称 :{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {dataset_name} {Style.RESET_ALL}"
                                )
                                self.log(
                                    f"{Fore.BLUE+Style.BRIGHT}   链接 :{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {dataset_url} {Style.RESET_ALL}"
                                )

                            datasets_completed+=1

                else:
                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   状态 :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} 每日数据集训练次数已用完 [{datasets_completed}/{datasets_limit}] {Style.RESET_ALL}"
                    )

            tasks = await self.task_lists(address, proxy)
            if tasks:
                self.log(f"{Fore.CYAN+Style.BRIGHT}任务列表:{Style.RESET_ALL}")

                for task in tasks:
                    task_id = task.get("id")
                    title = task.get("title")
                    type = task.get("type")
                    recurements = task.get("requirements")
                    reward = task.get("points")

                    if type == "SOCIAL_TWEET":
                        recurements = self.generate_tweet_id(x_handle)

                    complete = await self.complete_task(address, task_id, title, recurements, proxy)
                    if complete:
                        self.log(
                            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} 任务完成 {Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT} 奖励: {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{reward} 积分{Style.RESET_ALL}"
                        )
            
    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            proxy_choice, rotate_proxy = self.print_question()
            total_accounts = len(accounts)  # 获取账号总数

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}账号总数: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{total_accounts}{Style.RESET_ALL}"
                )

                use_proxy = proxy_choice == 1
                if use_proxy:
                    await self.load_proxies()

                separator = "=" * 25
                for idx, account in enumerate(accounts, start=1):
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} 账号 {idx}/{total_accounts} {Style.RESET_ALL}"  # 显示当前账号/总账号数
                            f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}状态  :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} 私钥无效或库版本不受支持 {Style.RESET_ALL}"
                            )
                            continue

                        self.HEADERS[address] = {
                            "Accept": "*/*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://prelaunch.humanoidnetwork.org",
                            "Referer": "https://prelaunch.humanoidnetwork.org/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-origin",
                            "User-Agent": FakeUserAgent().random
                        }
                        
                        await self.process_accounts(account, address, use_proxy, rotate_proxy)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                
                delay = 12 * 60 * 60  # 12小时
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ 等待{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}所有账号处理完成，等待下次执行...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    delay -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}未找到 'accounts.txt' 文件{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}错误: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Humanoid()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ 退出 ] Humanoid - 机器人{Style.RESET_ALL}                                       "                              
        )
