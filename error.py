import socket
import time
import argparse
import threading

class ControlledErrorClient:
    def __init__(self, server_host='localhost', server_port=8888, latency=100, attempts=5, message='Hello, Server!'):
        self.server_host = server_host
        self.server_port = server_port
        self.latency = latency
        self.socket = None
        self.force_packet_loss = False
        self.attempts = attempts
        self.message = message
        self.simulation_thread = None
        self.simulation_running = False

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.server_host, self.server_port))
            print(f"✅ Connected to {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def send_message(self, message):
        if not self.socket:
            return None

        if self.force_packet_loss:
            print(f"[Simulated packet loss] Skipping send/receive for: '{message}'")
            return None

        if self.latency > 0:
            time.sleep(self.latency / 1000.0)

        try:
            self.socket.sendall(message.encode('utf-8'))
            print(f"Sent: {message}")

            if self.latency > 0:
                time.sleep(self.latency / 1000.0)

            response = self.socket.recv(1024)
            return response.decode('utf-8')
        except Exception as e:
            print(f"Error in communication: {e}")
            return None

    def start_simulation(self):
        self.simulation_running = True
        self.simulation_thread = threading.Thread(target=self.simulate_traffic)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def simulate_traffic(self):
        attempt = 1
        while attempt <= self.attempts and self.simulation_running:
            print(f"\n➡️ Attempt {attempt}/{self.attempts}")
            response = self.send_message(f"{self.message} (Attempt {attempt})")
            if response:
                print(f"✅ Response: {response}")
            else:
                print("❌ No response (simulated loss or error)")
            attempt += 1
            time.sleep(1)
        print("\n✅ Simulation attempts finished.")
        self.simulation_running = False

    def close(self):
        self.simulation_running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
        if self.socket:
            self.socket.close()
            print("Connection closed.")

    def toggle_packet_loss(self):
        self.force_packet_loss = not self.force_packet_loss
        print(f"Packet loss simulation {'ENABLED' if self.force_packet_loss else 'DISABLED'}.")

def run_client(host, port, message, latency, attempts):
    client = ControlledErrorClient(host, port, latency, attempts, message)

    if not client.connect():
        return

    print("\n=== Initial successful attempt ===")
    response = client.send_message(message)
    if response:
        print(f"✅ Initial response: {response}")
    else:
        print("❌ Initial attempt failed, exiting.")
        client.close()
        return

    # Ask user about packet loss simulation before starting
    while True:
        choice = input("\nDo you want to simulate packet loss? (y/n): ").strip().lower()
        if choice == 'y':
            client.force_packet_loss = True
            print("Packet loss simulation ENABLED.")
            break
        elif choice == 'n':
            print("Packet loss simulation DISABLED.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    client.start_simulation()


    # Command processing loop
    while True:
        cmd = input("Command (p/q): ").strip().lower()
        if cmd == 'p':
            client.toggle_packet_loss()
        elif cmd == 'q':
            print("Quitting simulation...")
            client.simulation_running = False
            break
        
        # Check if simulation has completed on its own
        if not client.simulation_running and not client.simulation_thread.is_alive():
            print("Simulation has completed.")
            break

    client.close()
    print("Simulation ended.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Controlled Error and Packet Loss Client')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8888, help='Server port')
    parser.add_argument('--message', default='Hello, Server!', help='Message to send')
    parser.add_argument('--latency', type=int, default=100, help='Latency in milliseconds')
    parser.add_argument('--attempts', type=int, default=5, help='Number of attempts')

    args = parser.parse_args()

    run_client(args.host, args.port, args.message, args.latency, args.attempts)