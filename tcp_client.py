import socket
import argparse

class TCPClient:
    def __init__(self, server_host='localhost', server_port=8888):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        print(f"Connected to server at {self.server_host}:{self.server_port}")

    def send_data(self, data):
        if not self.client_socket:
            raise ConnectionError("Not connected to server")
        self.client_socket.sendall(data)
        return self.client_socket.recv(len(data))

    def close(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        print("Connection closed")


def run_client(host, port, message):
    client = TCPClient(host, port)
    try:
        client.connect()
        response = client.send_data(message.encode('utf-8'))
        print(f"Received response: {response.decode('utf-8')}")
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Client Simulation')
    parser.add_argument('--host', default='localhost', help='Server host address')
    parser.add_argument('--port', type=int, default=8888, help='Server port number')
    parser.add_argument('--message', default='Hello, TCP World!', help='Message to send to server')

    args = parser.parse_args()
    run_client(args.host, args.port, args.message)
