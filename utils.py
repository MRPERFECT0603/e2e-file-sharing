from Crypto.Random import get_random_bytes
import os
from colorama import Fore, Style

def generate_key_and_nonce():
    key = get_random_bytes(16) # Random 16 Byte Key (Different for each transfer)
    nonce = get_random_bytes(16) # Random 16 Byte Nonce (Different for each transfer)

    with open(f'{os.getenv("HOME")}/.e2e_key', 'wb') as kh:
        kh.write(key)

    with open(f'{os.getenv("HOME")}/.e2e_nonce', 'wb') as nh:
        nh.write(nonce)

def cleanup():
    os.remove(f'{os.getenv("HOME")}/.e2e_key')
    os.remove(f'{os.getenv("HOME")}/.e2e_nonce')

def print_success(msg):
    print(f"{Style.BRIGHT}{Fore.GREEN}[+] {msg}{Fore.RESET}{Style.RESET_ALL}")

def print_warning(msg):
    print(f"{Style.BRIGHT}{Fore.YELLOW}[!] {msg}{Fore.RESET}{Style.RESET_ALL}")

def print_error(msg):
    print(f"{Style.BRIGHT}{Fore.RED}[X] {msg}{Fore.RESET}{Style.RESET_ALL}")

def print_info(msg, end=False):
    if end: print()
    print(f"{Style.BRIGHT}{Fore.BLUE}[*] {msg}{Fore.RESET}{Style.RESET_ALL}")