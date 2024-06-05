import socket
import signal
import sys
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

for section in config.sections():
    for key, value in config.items(section):
        if key=='host':
            HOST = value
        elif key=='port':
            PORT = int(value)



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python client.py <command> <params>")
        sys.exit(1)

    command = sys.argv[1]
    message_json = None
    if command=='CheckLocalFile':
        if len(sys.argv)!=4:
            print('Wrong params')
            sys.exit(1)
        else:
            param1 = sys.argv[2]
            param2 = sys.argv[3]
            message = {'command1':command, 'params': {'param1':param1,'param2':param2}}
            message_json = json.dumps(message)
    elif command=='QuarantineLocalFile':
        if len(sys.argv)!=3:
            print('Wrong params')
            sys.exit(1)
        else:
            param1 = sys.argv[2]
            message = {'command1':command, 'params': {'param1':param1}}
            message_json = json.dumps(message)

    if message_json is not None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 3228))

            def signal_handler(sig, frame):
                print('Shutting down client...')
                s.close()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)

            try:
                s.send(message_json.encode())
                response = s.recv(1024).decode()
                print(f'Server response: {response}')
            except ConnectionResetError:
                print("Server closed the connection")
            sys.exit(0)

        
    # send_messages()
