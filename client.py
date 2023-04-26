import socket
import os
from _thread import *

from PyInquirer import prompt
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TaskProgressColumn, TimeRemainingColumn
from Crypto.Cipher import AES
from utils import print_error, print_info, print_success, print_warning

import hashlib
import signal

def read_key():
    key = b""
    with open(f'{os.getenv("HOME")}/.e2e_key', 'rb') as kr:
        key = kr.read()
    return key

def read_nonce():
    nonce = b""
    with open(f'{os.getenv("HOME")}/.e2e_nonce', "rb") as nr:
        nonce = nr.read()
    return nonce

def encrypt(data):
    key = read_key()
    nonce = read_nonce()
    cipher = AES.new(key, AES.MODE_EAX, nonce)

    return cipher.encrypt(data)

def decrypt(data):
    key = read_key()
    nonce = read_nonce()
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    
    return cipher.decrypt(data)

def compute_hash(file):
    pass

initial_questions = [
    {
        'type': 'list',
        'name': 'mode',
        'message': 'Choose Mode?',
        'choices': ['Send', 'Receive']
    }
]

action_ques = [
    {
        'type': 'list',
        'name': 'option',
        'message': 'Choose Action?',
        'choices': ['Send File', 'Exit']
    }
]

file_questions = [
    {
        'type': 'input',
        'name': 'filepath',
        'message': 'Enter File Path'
    },
    {
        'type': 'input',
        'name': 'receiver',
        'message': 'Enter Receiver ID'
    }
]

confirm_ques = [
    {
        'type': 'confirm',
        'name': 'reconnect',
        'message': 'Do you want to reconnect?',
        'default': False
    }
]

def main():
    opt = prompt(initial_questions)
    mode = None
    if opt['mode'] == "Send":
        mode = "SEND"
    else:
        mode = "RECV"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    HOST = '127.0.0.1'
    PORT = 50000
    ADDR = (HOST, PORT)

    sock.connect(ADDR)

    print_success(f"Connected to Server")
    client_id = sock.recv(1024).decode()
    print_info(f"{client_id}")

    if mode == "SEND":
        while True:
            opt = prompt(action_ques)
            if opt['option'] == "Exit":
                sock.close()
                print(f"[!] Disconnected")
                break
            data = prompt(file_questions)
            filepath = data['filepath']
            filename = filepath.split('/')[-1]
            filesize = os.path.getsize(filepath)

            receiver = data['receiver']

            header = f"{filename}<SEP>{filesize}<SEP>{receiver}"
            sock.send(header.encode())

            resp = sock.recv(1024).decode()
            if resp == "ACK":
                progress = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    DownloadColumn(binary_units=True),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    transient=True
                )

                file_hash = ""
                with progress:
                    task = progress.add_task(f"Sending {filename} to Receiver {receiver}", total=int(filesize))
                    with open(filepath, 'rb') as file_handle:
                        file_hash = hashlib.sha256()
                        while True:
                            bytes_data = file_handle.read(1024)
                            if bytes_data == b'':
                                sock.send(b"<END>")
                                progress.advance(task, int(filesize))
                                print_success(f"File Sent")
                                file_hash = file_hash.hexdigest()
                                break
                            file_hash.update(bytes_data)
                            sock.send(encrypt(bytes_data))
                            progress.advance(task, 1024)
                    print_info(f"Hash of the file is {file_hash}")
                    sock.close()
                    break
            else:
                print_error(f"Headers lost. Disconnecting")
                sock.close()

    else:
        while True:
            header = sock.recv(45).decode()
            filename, size = header.strip().split("<SEP>")
            print_success(f"Receiving {filename} of Size: {size} bytes")

            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(binary_units=True),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                transient=True
            )
            
            with progress:
                f_hash = hashlib.sha256()
                remaining_bytes = int(size)
                task = progress.add_task(f"Receiving {filename}", total=int(size))
                with open(filename, 'wb') as fh:
                    done = False
                    while not done:
                        recv_size = 1024 if remaining_bytes > 1024 else remaining_bytes
                        data = sock.recv(recv_size)
                        decrypted_data = decrypt(data)
                        f_hash.update(decrypted_data)
                        fh.write(decrypted_data)
                        progress.advance(task, int(recv_size))
                        remaining_bytes -= recv_size
                        if remaining_bytes <= 0:
                            done = True
                            f_hash = f_hash.hexdigest()
                            progress.advance(task, int(remaining_bytes))
                
                print_success(f"Saved to {filename}")
                print_info(f"Hash of the Received File: {f_hash}")
                sock.close()
                break
    
    cnf = prompt(confirm_ques)
    if cnf['reconnect']:
        main()
    else:
        return

    
if __name__ == '__main__':
    main()