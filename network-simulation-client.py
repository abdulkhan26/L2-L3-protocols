import socket
import time
import argparse
import threading
import random
import sys

class NetworkSimulationClient:
    def __init__(self, server_host='localhost', server_port=8888, latency=100):
        self.server_host = server_host
        self.server_port = server_port
        self.base_latency = latency
        self.socket = None
        self.running = True
        self.message = "Hello, Server!"
        self.attempts = 5  # Default number of attempts
        
    def connect(self):
        try:
            # Close any existing connection
            if self.socket:
                self.socket.close()
                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            print(f"✅ Connected to {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def send_message(self, message):
        if not self.socket:
            print("No connection available.")
            return None

        try:
            self.socket.sendall(message.encode('utf-8'))
            print(f"Sent: {message}")

            response = self.socket.recv(4096)
            return response.decode('utf-8')
        except Exception as e:
            print(f"Error in communication: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return None

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Connection closed.")

    def simulate_normal(self):
        """Run a normal simulation without any network issues"""
        print("\n=== Running Normal Simulation ===")
        
        if not self.connect():
            print("Failed to connect. Exiting simulation.")
            return
            
        for i in range(1, self.attempts + 1):
            message = f"{self.message} (Attempt {i})"
            print(f"\n➡️ Sending: {message}")
            response = self.send_message(message)
            
            if response:
                print(f"✅ Response: {response}")
            else:
                print("❌ No response received")
                
            # Reconnect if connection was lost
            if not self.socket:
                print("Connection lost. Reconnecting...")
                if not self.connect():
                    print("Failed to reconnect. Ending simulation.")
                    break
                    
            time.sleep(1)  # Wait between messages
            
        self.close()
        print("\n✅ Normal simulation completed")

    def simulate_packet_loss(self):
        """Simulate packet loss"""
        print("\n=== Running Packet Loss Simulation ===")
        loss_rate = 0.4  # 40% packet loss
        
        if not self.connect():
            print("Failed to connect. Exiting simulation.")
            return
            
        for i in range(1, self.attempts + 1):
            message = f"{self.message} (Attempt {i})"
            print(f"\n➡️ Sending: {message}")
            
            # Simulate packet loss
            if random.random() < loss_rate:
                print(f"[Simulated packet loss] Message dropped: '{message}'")
                time.sleep(1)  # Wait before next attempt
                continue
                
            response = self.send_message(message)
            
            if response:
                print(f"✅ Response: {response}")
                
                # Simulate response packet loss
                if random.random() < loss_rate:
                    print(f"[Simulated packet loss] Response dropped after processing")
            else:
                print("❌ No response received")
                
            # Reconnect if connection was lost
            if not self.socket:
                print("Connection lost. Reconnecting...")
                if not self.connect():
                    print("Failed to reconnect. Ending simulation.")
                    break
                    
            time.sleep(1)  # Wait between messages
            
        self.close()
        print("\n✅ Packet loss simulation completed")

    def simulate_connection_failure(self):
        """Simulate random connection failures"""
        print("\n=== Running Connection Failure Simulation ===")
        failure_rate = 0.3  # 30% connection failure rate
        reconnect_delay = 2  # seconds
        
        if not self.connect():
            print("Failed to connect. Exiting simulation.")
            return
            
        for i in range(1, self.attempts + 1):
            message = f"{self.message} (Attempt {i})"
            print(f"\n➡️ Sending: {message}")
            
            # Simulate connection failure before sending
            if random.random() < failure_rate:
                print(f"[Simulated connection failure] Connection dropped before sending: '{message}'")
                self.socket.close()
                self.socket = None
                print(f"Waiting {reconnect_delay} seconds before reconnecting...")
                time.sleep(reconnect_delay)
                
                if not self.connect():
                    print("Failed to reconnect. Ending simulation.")
                    break
                    
                continue
                
            response = self.send_message(message)
            
            if response:
                print(f"✅ Response: {response}")
                
                # Simulate connection failure after response
                if random.random() < failure_rate:
                    print(f"[Simulated connection failure] Connection dropped after response")
                    self.socket.close()
                    self.socket = None
            else:
                print("❌ No response received")
                
            # Reconnect if connection was lost
            if not self.socket:
                print(f"Connection lost. Waiting {reconnect_delay} seconds before reconnecting...")
                time.sleep(reconnect_delay)
                if not self.connect():
                    print("Failed to reconnect. Ending simulation.")
                    break
                    
            time.sleep(1)  # Wait between messages
            
        self.close()
        print("\n✅ Connection failure simulation completed")

    def simulate_packet_reordering(self):
        """Simulate packet reordering"""
        print("\n=== Running Packet Reordering Simulation ===")
        
        if not self.connect():
            print("Failed to connect. Exiting simulation.")
            return
            
        # Prepare messages
        messages = []
        for i in range(1, self.attempts + 1):
            messages.append(f"{self.message} (Attempt {i})")
            
        # Shuffle messages to simulate reordering
        random.shuffle(messages)
        print("[Simulated reordering] Messages will be sent in this order:")
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. {msg}")
            
        for message in messages:
            print(f"\n➡️ Sending (reordered): {message}")
            
            # Variable latency for better reordering simulation
            latency = self.base_latency * (0.5 + random.random())
            print(f"[Simulated variable latency] Using {latency:.0f}ms")
            time.sleep(latency / 1000.0)
            
            response = self.send_message(message)
            
            if response:
                print(f"✅ Response: {response}")
            else:
                print("❌ No response received")
                
            # Reconnect if connection was lost
            if not self.socket:
                print("Connection lost. Reconnecting...")
                if not self.connect():
                    print("Failed to reconnect. Ending simulation.")
                    break
                    
            time.sleep(1)  # Wait between messages
            
        self.close()
        print("\n✅ Packet reordering simulation completed")

    def simulate_duplicate_packets(self):
        """Simulate duplicate packets"""
        print("\n=== Running Duplicate Packets Simulation ===")
        duplicate_rate = 0.5  # 50% chance of duplication
        
        if not self.connect():
            print("Failed to connect. Exiting simulation.")
            return
            
        for i in range(1, self.attempts + 1):
            message = f"{self.message} (Attempt {i})"
            print(f"\n➡️ Sending: {message}")
            
            # Send the original message
            response = self.send_message(message)
            
            if response:
                print(f"✅ Response: {response}")
            else:
                print("❌ No response received")
                
            # Simulate duplicate packet
            if random.random() < duplicate_rate:
                print(f"[Simulated duplicate] Sending duplicate of: '{message}'")
                time.sleep(0.2)  # Small delay between original and duplicate
                
                duplicate_response = self.send_message(message)
                
                if duplicate_response:
                    print(f"✅ Duplicate response: {duplicate_response}")
                else:
                    print("❌ No response to duplicate")
                    
            # Reconnect if connection was lost
            if not self.socket:
                print("Connection lost. Reconnecting...")
                if not self.connect():
                    print("Failed to reconnect. Ending simulation.")
                    break
                    
            time.sleep(1)  # Wait between messages
            
        self.close()
        print("\n✅ Duplicate packets simulation completed")

def show_menu():
    """Display the simulation selection menu"""
    print("\n===== NETWORK SIMULATION CLIENT =====")
    print("1. Run Normal Simulation")
    print("2. Simulate Packet Loss")
    print("3. Simulate Connection Failure")
    print("4. Simulate Packet Reordering")
    print("5. Simulate Duplicate Packets")
    print("0. Exit")
    return input("Select simulation (0-5): ")

def run_client(host, port, latency, attempts, message):
    client = NetworkSimulationClient(host, port, latency)
    client.attempts = attempts
    client.message = message
    
    print(f"Network Simulation Client initialized:")
    print(f"- Server: {host}:{port}")
    print(f"- Latency: {latency}ms")
    print(f"- Message: {message}")
    print(f"- Attempts per simulation: {attempts}")
    
    while True:
        choice = show_menu()
        
        if choice == '0':
            print("Exiting...")
            break
        elif choice == '1':
            client.simulate_normal()
        elif choice == '2':
            client.simulate_packet_loss()
        elif choice == '3':
            client.simulate_connection_failure()
        elif choice == '4':
            client.simulate_packet_reordering()
        elif choice == '5':
            client.simulate_duplicate_packets()
        else:
            print("Invalid selection. Please try again.")
            
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Network Simulation Client')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8888, help='Server port')
    parser.add_argument('--message', default='Hello, Server!', help='Message to send')
    parser.add_argument('--latency', type=int, default=100, help='Base latency in milliseconds')
    parser.add_argument('--attempts', type=int, default=5, help='Number of attempts per simulation')

    args = parser.parse_args()

    run_client(args.host, args.port, args.latency, args.attempts, args.message)