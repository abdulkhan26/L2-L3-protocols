import socket
import threading
import argparse
import datetime


class TCPServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.connections = []

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Server started on {self.host}:{self.port}")

        try:
            while self.running:
                client_socket, address = self.server_socket.accept()
                print(f"Connection from {address} established")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
                self.connections.append((client_socket, address))
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.stop()

    def handle_client(self, client_socket, address):
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                message = data.decode('utf-8')
                print(f"[{timestamp}] Received from {address}: {message} ({len(data)} bytes)")
                # Echo the data back to the client
                client_socket.sendall(data)
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            if (client_socket, address) in self.connections:
                self.connections.remove((client_socket, address))
            print(f"Connection from {address} closed")


    def stop(self):
        self.running = False
        for client_socket, _ in self.connections:
            try:
                client_socket.close()
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        print("Server stopped")


def run_server(host, port):
    server = TCPServer(host, port)
    server.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Server Simulation')
    parser.add_argument('--host', default='localhost', help='Host address')
    parser.add_argument('--port', type=int, default=8888, help='Port number')

    args = parser.parse_args()
    run_server(args.host, args.port)
