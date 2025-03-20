import socket
import time
import threading
import argparse
import os


class ThroughputServer:
    def __init__(self, host='localhost', port=8889):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Throughput Server started on {self.host}:{self.port}")
        
        try:
            while self.running:
                client_socket, address = self.server_socket.accept()
                print(f"Connection from {address} established")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, address):
        try:
            # First receive the total expected data size
            size_data = client_socket.recv(10).decode('utf-8')
            expected_size = int(size_data)
            print(f"Expected to receive {expected_size} bytes from {address}")
            
            # Acknowledge the size
            client_socket.sendall(b'ACK')
            
            start_time = time.time()
            bytes_received = 0
            
            # Receive the data in chunks
            while bytes_received < expected_size:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                bytes_received += len(chunk)
                
                # Print progress
                progress = bytes_received / expected_size * 100
                print(f"\rReceived: {bytes_received}/{expected_size} bytes ({progress:.2f}%)", end='')
            
            end_time = time.time()
            duration = end_time - start_time
            throughput = bytes_received / duration / 1024 / 1024  # MB/s
            
            print(f"\nReceived {bytes_received} bytes in {duration:.2f} seconds")
            print(f"Throughput: {throughput:.2f} MB/s")
            
            # Send throughput results back to client
            result = f"{throughput:.2f}"
            client_socket.sendall(result.encode('utf-8'))
            
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection from {address} closed")
    
    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("Server stopped")


class ThroughputClient:
    def __init__(self, server_host='localhost', server_port=8889):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
    
    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        print(f"Connected to server at {self.server_host}:{self.server_port}")
    
    def measure_throughput(self, data_size_mb=10, chunk_size=4096):
        if not self.client_socket:
            raise ConnectionError("Not connected to server")
        
        # Convert MB to bytes
        data_size_bytes = data_size_mb * 1024 * 1024
        
        # Send the expected data size
        self.client_socket.sendall(f"{data_size_bytes}".zfill(10).encode('utf-8'))
        
        # Wait for acknowledgment
        ack = self.client_socket.recv(3)
        if ack != b'ACK':
            raise RuntimeError("Failed to receive acknowledgment from server")
        
        print(f"Starting throughput test with {data_size_mb} MB of data")
        
        # Generate random data (a block of random bytes repeated)
        block_size = min(chunk_size, 1024 * 1024)  # Use 1MB or chunk_size, whichever is smaller
        data_block = os.urandom(block_size)
        
        start_time = time.time()
        bytes_sent = 0
        
        # Send data in chunks
        while bytes_sent < data_size_bytes:
            remaining = data_size_bytes - bytes_sent
            chunk = data_block if remaining >= block_size else data_block[:remaining]
            self.client_socket.sendall(chunk)
            bytes_sent += len(chunk)
            
            # Print progress
            progress = bytes_sent / data_size_bytes * 100
            print(f"\rSent: {bytes_sent}/{data_size_bytes} bytes ({progress:.2f}%)", end='')
        
        end_time = time.time()
        duration = end_time - start_time
        client_throughput = bytes_sent / duration / 1024 / 1024  # MB/s
        
        print(f"\nSent {bytes_sent} bytes in {duration:.2f} seconds")
        print(f"Client-side throughput: {client_throughput:.2f} MB/s")
        
        # Receive server's throughput calculation
        server_result = self.client_socket.recv(20).decode('utf-8')
        print(f"Server-side throughput: {server_result} MB/s")
        
        return client_throughput, float(server_result)
    
    def close(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        print("Connection closed")


def run_throughput_server(host, port):
    server = ThroughputServer(host, port)
    server.start()


def run_throughput_client(host, port, data_size):
    client = ThroughputClient(host, port)
    try:
        client.connect()
        client_throughput, server_throughput = client.measure_throughput(data_size)
        print(f"Test completed. Client: {client_throughput:.2f} MB/s, Server: {server_throughput} MB/s")
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Throughput Measurement')
    parser.add_argument('--mode', choices=['server', 'client'], required=True, help='Run as server or client')
    parser.add_argument('--host', default='localhost', help='Host address')
    parser.add_argument('--port', type=int, default=8889, help='Port number')
    parser.add_argument('--data-size', type=int, default=10, help='Size of data to send in MB (client mode only)')

    args = parser.parse_args()

    if args.mode == 'server':
        run_throughput_server(args.host, args.port)
    else:
        run_throughput_client(args.host, args.port, args.data_size)
