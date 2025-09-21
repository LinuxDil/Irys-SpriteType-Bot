from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account import Account
from datetime import datetime
from colorama import *
import asyncio, hashlib, random, time, json, re, os, pytz
from pyfiglet import Figlet
import shutil

wib = pytz.timezone('Asia/Jakarta')

class Irys:
    def __init__(self) -> None:
        self.BASE_API = "https://spritetype.irys.xyz/api"
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.game_count = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        figlet = Figlet(font='ansi_shadow')
        banner_lines = figlet.renderText('BG WIN').splitlines()
        term_width = shutil.get_terminal_size().columns

        for line in banner_lines:
            print(Fore.GREEN + Style.BRIGHT + line.center(term_width) + Style.RESET_ALL
        )


    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
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

        raise Exception("Unsupported Proxy Type.")
        
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address

            return address
        except Exception as e:
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
    
    def generate_random_game_stats(self):
        time = random.choice([15, 30, 60, 120])

        wpm_target = int(random.choices(
            [random.randint(20, 50), random.randint(50, 80), random.randint(80, 120)],
            weights=[0.4, 0.4, 0.2]
        )[0])

        total_chars = int(wpm_target * 5 * (time / 60))
        total_chars += random.randint(-10, 10)
        total_chars = max(50, total_chars)

        incorrect_ratio = random.choices(
            [random.uniform(0, 0.03), random.uniform(0.03, 0.08), random.uniform(0.08, 0.15)],
            weights=[0.7, 0.2, 0.1]
        )[0]

        incorrect_chars = int(total_chars * incorrect_ratio)
        correct_chars = max(1, total_chars - incorrect_chars)

        wpm = round(correct_chars / 5 / (time / 60))
        wpm = max(0, min(wpm, 300))

        accuracy = round(correct_chars / total_chars * 100)

        return {
            "wpm": wpm,
            "accuracy": accuracy,
            "time": time,
            "correctChars": correct_chars,
            "incorrectChars": incorrect_chars,
            "progressData": []
        }

    def generate_anti_cheat_hash(self, address: str, game_stats: dict):
        wpm = game_stats["wpm"]
        accuracy = game_stats["accuracy"]
        time = game_stats["time"]
        correct_chars = game_stats["correctChars"]
        incorrect_chars = game_stats["incorrectChars"]

        l = correct_chars + incorrect_chars

        n = (
            0 + 23 * wpm + 89 * accuracy + 41 * time +
            67 * correct_chars + 13 * incorrect_chars + 97 * l
        )

        char_sum = sum(ord(c) * (i + 1) for i, c in enumerate(address))
        n += 31 * char_sum

        multiplier = float(int("178ba57548d", 16))
        max_safe_integer = float(2**53 - 1)

        checksum = int((multiplier * n) % max_safe_integer)

        base_string = f"{address.lower()}_{wpm}_{accuracy}_{time}_{correct_chars}_{incorrect_chars}_{checksum}"

        hash_result = hashlib.sha256(base_string.encode()).hexdigest()
        return hash_result[:32]
    
    def generate_payload(self, address: str, game_stats: dict):
        try:
            anti_cheat_hash = self.generate_anti_cheat_hash(address, game_stats)

            payload = {
                "walletAddress": address,
                "gameStats": game_stats,
                "antiCheatHash": anti_cheat_hash,
                "timestamp": int(time.time() * 1000)
            }

            return payload
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")
        
    async def print_timer(self, delay: int, message: str):
        for remaining in range(delay, 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For {message}...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_question(self):
        while True:
            try:
                game_count = int(input(f"{Fore.GREEN + Style.BRIGHT}Enter Games Count -> {Style.RESET_ALL}").strip())
                if game_count > 0:
                    self.game_count = game_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Games Count Must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid Input. Enter a Number.{Style.RESET_ALL}")
        
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return proxy_choice, rotate_proxy
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=10)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
    
    async def submit_result(self, address: str, game_stats: dict, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/submit-result"
        data = json.dumps(self.generate_payload(address, game_stats))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        if response.status == 400:
                            result = await response.json()
                            err_msg = result.get("error")
                            return {"success": False, "message": err_msg}
                        
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Submit Result Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                return None
            
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy    :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue

                return False
            
            return True

    async def process_accounts(self, address: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            self.log(f"{Fore.CYAN+Style.BRIGHT}Games    :{Style.RESET_ALL}                                   ")

            for i in range(self.game_count):
                self.log(
                    f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT}Game{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {i+1} {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}Of{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {self.game_count} {Style.RESET_ALL}                                   "
                )

                game_stats = self.generate_random_game_stats()

                submit = await self.submit_result(address, game_stats, proxy)
                if submit is None: continue

                if submit and submit.get("success"):
                    message = submit.get("message")
                    receipt = submit.get("data", {}).get("receiptId")

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} {message} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Receipt  :{Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT} {receipt} {Style.RESET_ALL}"
                    )

                else:
                    err_msg = submit.get("message")
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                    )

                    if err_msg == "Hourly submission limit reached. Try again later.": break

                await self.print_timer(30, "Next Games...")

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            proxy_choice, rotate_proxy = self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                use_proxy = True if proxy_choice == 1 else False
                if use_proxy:
                    await self.load_proxies()

                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)

                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status   :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        self.HEADERS[address] = {
                            "Accept": "*/*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://spritetype.irys.xyz",
                            "Referer": "https://spritetype.irys.xyz/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-origin",
                            "User-Agent": FakeUserAgent().random
                        }

                        await self.process_accounts(address, use_proxy, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Irys()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Irys Sprite Type - BOT{Style.RESET_ALL}                                       "                              
        )
