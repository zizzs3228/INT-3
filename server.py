import socket
import threading
import signal
import sys
import json
import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

for section in config.sections():
    for key, value in config.items(section):
        if key=='host':
            HOST = value
        elif key=='port':
            PORT = int(value)
        elif key=='NUM_THREADS':
            NUM_THREADS=value
        elif key=='QUORANTINE_DIR':
            QUARANTINE_dir=value


NUM_THREADS = 2
QUARANTINE_dir = r'quarantine'


def check_local_file(file_path:str, signature:str):
    signature = bytes.fromhex(signature)
    with open(file_path, "rb") as file:
        data = file.read()
        offsets = []
        index = 0
        while index <= len(data) - len(signature):
            if data[index:index + len(signature)] == signature:
                offsets.append(index)
            index += 1
        return offsets

def handle_client_connection(client_socket:socket.socket):
    try:
        response = client_socket.recv(1024).decode()
        message_dict = json.loads(response)
        command = message_dict['command1']
        params = message_dict.get('params')
        param1 = params.get('param1')
        param2 = params.get('param2')
        print(command,param1,param2)
        if command == 'CheckLocalFile':
            if param1 is None or param2 is None:
                client_socket.send('Wrong params'.encode())
            elif not os.path.isfile(param1):
                client_socket.send('File does not exists'.encode())
            else:
                offsets = check_local_file(param1,param2)
                if offsets==[]:
                    client_socket.send('Signatures not found'.encode())
                else:
                    counter = 0 
                    dict_to_send = {}
                    for off in offsets:
                        dict_to_send[f'offset{counter}'] = off
                        counter+=1
                    dict_to_send = {'Offsets':dict_to_send}
                    json_to_send = json.dumps(dict_to_send)
                    client_socket.send(f'Successful! {json_to_send}'.encode())
        elif command == 'QuarantineLocalFile':
            if param1 is None:
                client_socket.send('Wrong params'.encode())
            elif not os.path.isfile(param1):
                client_socket.send('File does not exists'.encode())
            elif os.path.isdir(param1):
                client_socket.send('File is directory'.encode())
            else:
                if os.path.exists(QUARANTINE_dir):
                    os.rename(param1,os.path.join(QUARANTINE_dir,param1))
                else:
                    os.mkdir(QUARANTINE_dir)
                    os.rename(param1,os.path.join(QUARANTINE_dir,param1))
                client_socket.send('Successfull! Quorantined'.encode())
    except Exception as e:
        client_socket.send(f'Error {e}'.encode())
    finally:
        client_socket.close()
    return None


def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"Server listening on {HOST}:{PORT}")

    def signal_handler(sig, frame):
        print('Shutting down server...')
        server_socket.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    all_threads = []
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        all_threads = [th for th in all_threads if th.is_alive()]
        if len(all_threads)>=NUM_THREADS:
            print(f"Max connections reached. Rejecting connection from {addr}")
            client_socket.send(f"Max number of connections received. Rejected".encode())
            client_socket.close()
            continue
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        all_threads.append(client_handler)
        client_handler.start()
        

if __name__ == "__main__":
    start_server()
