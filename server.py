import socket
import threading
import signal
import sys
from _thread import *
from utils import generate_key_and_nonce, cleanup, print_info, print_error,print_success, print_warning

clients = {}
client_db_lock = threading.Lock()

def parse_headers(header_string):
    return header_string.split("<SEP>")

def receive_file(client_sock):
    done = False
    file_bytes = b""
    while not done:
        data = client_sock.recv(1024)
        file_bytes += data
        if file_bytes[-5:] == b"<END>":
            done = True
    return file_bytes[:-5]

def client_thread(client_sock, addr):
    print_info(f"Got Connection from {addr[0]}:{addr[1]}")
    client_db_lock.acquire()
    client_id = len(clients) + 1
    clients[client_id] = client_sock
    client_db_lock.release()

    client_sock.send(f"Your Client ID is: {client_id}".encode())

    while True:
        # Do action
        try:
            headers = client_sock.recv(1024).decode()
            if headers == b"":
                continue
            filename, size, receiver = parse_headers(headers)
            client_sock.send(b"ACK")

            rcvr = clients.get(int(receiver), None)
            if rcvr is None:
                break

            file_data = receive_file(client_sock)
            
            # start_new_thread(write_enc, (filename, file_data))
            # file_hash = b""
            # while file_hash[-6:] == b"<HASH>":
            #     file_hash = client_sock.recv(1024)
            # print(f"Hash of file. {file_hash}")
            print_info("Got Encrypted Data, Sending to receiver")
            header = f"{filename}<SEP>{size}".encode()
            header += (" "*(45-len(header))).encode()
            rcvr.send(header)

            rcvr.sendall(file_data)
            rcvr.send(b"<END>")
            break
        except ConnectionResetError as e:
            for cid, sock in clients.items():
                if sock == client_sock:
                    del clients[cid]
                    break
            print_warning(f"Client Disconnected")
            break
        except Exception as e:
            print_error(f"ERROR: {e}")
            client_sock.close()
            for cid, sock in clients.items():
                if sock == client_sock:
                    del clients[cid]
                    break
            break
    client_sock.close()


def main():
    generate_key_and_nonce()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    HOST = ''
    PORT = 50000

    ADDR = (HOST, PORT)
    server_socket.bind(ADDR)

    print_info(f"Binding to port {PORT}")
    server_socket.listen(10)

    print_success(f"Listening on port {PORT}")

    def signal_handler(signal, frame):
        print_info(f"Closing Server", end=True)
        server_socket.close()
        print_info(f"Performing Cleanup...")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        client_sock, addr = server_socket.accept()

        start_new_thread(client_thread, (client_sock, addr))

if __name__ == '__main__':
    main()
        