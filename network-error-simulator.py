import socket
import random
import time
import argparse
from contextlib import contextmanager

class ErrorSimulator:
  
    def __init__(self, target_host, target_port, listen_port=None, 
                 packet_loss_rate=0.1, latency_ms=100, corruption_rate=0.05, 
                 disconnect_rate=0.01, disconnect_duration=5):
        self.target_host = target_host
        self.target_port = target_port
        self.listen_port = listen_port if listen_port else target_port + 1000
        
        # Error simulation parameters
        self.packet_loss_rate = packet_loss_rate
        self.latency_ms = latency_ms
        self.corruption_rate = corruption_rate
        self.disconnect_rate = disconnect_rate
        self.disconnect_duration = disconnect_duration
        
        self.running = False
        self.server_socket = None
        self.connections = []
    
    def start(self):
        """Start the error simulation proxy server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.listen_port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"Error simulator running on port {self.listen_port}")
        print(f"Redirecting to {self.target_host}:{self.target_port}")
        print(f"Packet loss rate: {self.packet_loss_rate*100}%")
        print(f"Latency: {self.latency_ms}ms")
        print(f"Corruption rate: {self.corruption_rate*100}%")
        print(f"Disconnect rate: {self.disconnect_rate*100}%")
        
        try:
            while self.running:
                client_socket, address = self.server_socket.accept()
                print(f"Connection from {address} established")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
                self.connections.append((client_socket, address))
        except KeyboardInterrupt:
            print("Error simulator shutting down...")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, address):
        """Handle client connection with error simulation"""
        try:
            # Connect to the target server
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((self.target_host, self.target_port))
            
            # Set up bidirectional communication
            client_to_target = threading.Thread(
                target=self.proxy_data, 
                args=(client_socket, target_socket, f"Client {address}", "Server")
            )
            target_to_client = threading.Thread(
                target=self.proxy_data, 
                args=(target_socket, client_socket, "Server", f"Client {address}")
            )
            
            client_to_target.daemon = True
            target_to_client.daemon = True
            
            client_to_target.start()
            target_to_client.start()
            
            client_to_target.join()
            target_to_client.join()
            
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            try:
                client_socket.close()
                target_socket.close()
            except:
                pass
            if (client_socket, address) in self.connections:
                self.connections.remove((client_socket, address))
            print(f"Connection from {address} closed")
    
    def simulate_disconnect(self):
        """Simulate a temporary disconnect"""
        if random.random() < self.disconnect_rate:
            print(f"Simulating disconnect for {self.disconnect_duration} seconds")
            time.sleep(self.disconnect_duration)
            return True
        return False
    
    def add_latency(self):
        """Add artificial latency"""
        # Convert ms to seconds and add some jitter
        delay = self.latency_ms / 1000.0
        jitter = random.uniform(-delay/4, delay/4)
        time.sleep(max(0, delay + jitter))
    
    def corrupt_data(self, data):
        """Potentially corrupt the data"""
        if random.random() < self.corruption_rate:
            # Convert to bytearray for mutation
            data_array = bytearray(data)
            # Corrupt 1-3 random bytes
            for _ in range(random.randint(1, 3)):
                if len(data_array) > 0:
                    pos = random.randint(0, len(data_array) - 1)
                    data_array[pos] = random.randint(0, 255)
            print(f"Corrupted data packet ({len(data)} bytes)")
            return bytes(data_array)
        return data
    
    def proxy_data(self, source, destination, source_name, dest_name):
        """Proxy data from source to destination with error simulation"""
        try:
            while self.running:
                # Receive data from source
                data = source.recv(4096)
                if not data:
                    break
                
                # Simulate packet loss
                if random.random() < self.packet_loss_rate:
                    print(f"Dropping packet from {source_name} to {dest_name} ({len(data)} bytes)")
                    continue
                
                # Add latency
                self.add_latency()
                
                # Simulate disconnection
                if self.simulate_disconnect():
                    print(f"Connection between {source_name} and {dest_name} restored")
                
                # Corrupt data
                data = self.corrupt_data(data)
                
                # Forward to destination
                print(f"Forwarding: {source_name} -> {dest_name} ({len(data)} bytes)")
                destination.sendall(data)
                
        except Exception as e:
            print(f"Error in proxy: {e}")
    
    def stop(self):
        """Stop the error simulator"""
        self.running = False
        for client_socket, _ in self.connections:
            try:
                client_socket.close()
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        print("Error simulator stopped")


@contextmanager
def simulate_packet_loss(probability=0.1):
    """Context manager to simulate packet loss for a single operation"""
    if random.random() < probability:
        raise socket.error("Simulated packet loss")
    yield


class UnreliableSocket(socket.socket):
    """A socket wrapper that simulates unreliable network conditions"""
    def __init__(self, *args, **kwargs):
        self.packet_loss_rate = kwargs.pop('packet_loss_rate', 0.1)
        self.latency_ms = kwargs.pop('latency_ms', 100)
        self.corruption_rate = kwargs.pop('corruption_rate', 0.05)
        super().__init__(*args, **kwargs)
    
    def sendall(self, data, *args, **kwargs):
        """Override sendall to simulate errors"""
        # Simulate packet loss
        if random.random() < self.packet_loss_rate:
            print(f"Simulating packet loss (dropping {len(data)} bytes)")
            return
        
        # Simulate latency
        time.sleep(self.latency_ms / 1000.0)
        
        # Simulate data corruption
        if random.random() < self.corruption_rate:
            data_array = bytearray(data)
            for _ in range(random.randint(1, min(3, len(data)))):
                if len(data_array) > 0:
                    pos = random.randint(0, len(data_array) - 1)
                    data_array[pos] = random.randint(0, 255)
            data = bytes(data_array)
            print(f"Corrupted data packet ({len(data)} bytes)")
        
        # Send the data
        super().sendall(data, *args, **kwargs)


class UnreliableTCPClient:
    """A modified version of TCPClient that simulates network errors"""
    def __init__(self, server_host='localhost', server_port=8888, 
                 packet_loss_rate=0.1, latency_ms=100, corruption_rate=0.05):
        self.server_host = server_host
        self.server_port = server_port
        self.packet_loss_rate = packet_loss_rate
        self.latency_ms = latency_ms
        self.corruption_rate = corruption_rate
        self.client_socket = None
    
    def connect(self):
        """Connect to the server with unreliable socket"""
        self.client_socket = UnreliableSocket(
            socket.AF_INET, socket.SOCK_STREAM,
            packet_loss_rate=self.packet_loss_rate,
            latency_ms=self.latency_ms,
            corruption_rate=self.corruption_rate
        )
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to server at {self.server_host}:{self.server_port}")
        except socket.error as e:
            print(f"Connection failed: {e}")
            self.client_socket = None
            raise
    
    def send_data(self, data):
        """Send data with error simulation"""
        if not self.client_socket:
            raise ConnectionError("Not connected to server")
        
        try:
            self.client_socket.sendall(data)
            
            # Simulate receiving errors
            if random.random() < self.packet_loss_rate:
                print("Simulating packet loss during reception")
                return b"ERROR: Packet loss"
            
            # Add latency to reception
            time.sleep(self.latency_ms / 1000.0)
            
            # Receive response
            response = self.client_socket.recv(4096)
            
            # Simulate corruption in received data
            if random.random() < self.corruption_rate:
                response_array = bytearray(response)
                for _ in range(random.randint(1, min(3, len(response)))):
                    if len(response_array) > 0:
                        pos = random.randint(0, len(response_array) - 1)
                        response_array[pos] = random.randint(0, 255)
                response = bytes(response_array)
                print("Corrupted received data")
            
            return response
            
        except socket.error as e:
            print(f"Error sending data: {e}")
            return b"ERROR: Connection issue"
    
    def close(self):
        """Close the connection"""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        print("Connection closed")


def run_unreliable_client(host, port, message, packet_loss_rate, latency_ms, corruption_rate):
    """Run the unreliable client with the specified parameters"""
    client = UnreliableTCPClient(
        host, port, 
        packet_loss_rate=packet_loss_rate,
        latency_ms=latency_ms,
        corruption_rate=corruption_rate
    )
    
    try:
        client.connect()
        print(f"Sending message: {message}")
        response = client.send_data(message.encode('utf-8'))
        print(f"Received response: {response.decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"Error during client operation: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    # Import threading only when running as main
    import threading
    
    parser = argparse.ArgumentParser(description='Network Error Simulator')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Proxy mode
    proxy_parser = subparsers.add_parser('proxy', help='Run as a proxy between client and server')
    proxy_parser.add_argument('--target-host', default='localhost', help='Target server host')
    proxy_parser.add_argument('--target-port', type=int, default=8888, help='Target server port')
    proxy_parser.add_argument('--listen-port', type=int, default=9888, help='Port to listen on')
    proxy_parser.add_argument('--packet-loss', type=float, default=0.1, help='Packet loss rate (0-1)')
    proxy_parser.add_argument('--latency', type=int, default=100, help='Latency in milliseconds')
    proxy_parser.add_argument('--corruption', type=float, default=0.05, help='Data corruption rate (0-1)')
    proxy_parser.add_argument('--disconnect', type=float, default=0.01, help='Disconnect rate (0-1)')
    proxy_parser.add_argument('--disconnect-time', type=int, default=5, help='Disconnect duration in seconds')
    
    # Client mode
    client_parser = subparsers.add_parser('client', help='Run as an unreliable client')
    client_parser.add_argument('--host', default='localhost', help='Server host address')
    client_parser.add_argument('--port', type=int, default=8888, help='Server port number')
    client_parser.add_argument('--message', default='Hello, Unreliable World!', help='Message to send')
    client_parser.add_argument('--packet-loss', type=float, default=0.1, help='Packet loss rate (0-1)')
    client_parser.add_argument('--latency', type=int, default=100, help='Latency in milliseconds')
    client_parser.add_argument('--corruption', type=float, default=0.05, help='Data corruption rate (0-1)')
    
    args = parser.parse_args()
    
    if args.command == 'proxy':
        simulator = ErrorSimulator(
            args.target_host, args.target_port, args.listen_port,
            args.packet_loss, args.latency, args.corruption,
            args.disconnect, args.disconnect_time
        )
        simulator.start()
    elif args.command == 'client':
        run_unreliable_client(
            args.host, args.port, args.message,
            args.packet_loss, args.latency, args.corruption
        )
    else:
        parser.print_help()
