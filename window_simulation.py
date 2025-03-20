import socket
import time
import argparse
import matplotlib.pyplot as plt

class TCPWindowClient:
    def __init__(self, host='localhost', port=8888, window_size=1024, total_data=50000):
        self.host = host
        self.port = port
        self.window_size = window_size
        self.total_data = total_data
        self.sent = 0
        self.acknowledged = 0
        self.client_socket = None
        
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    def send_data(self):
        start_time = time.time()
        last_progress = 0
        ack_count = 0
        
        try:
            print(f"Window size: {self.window_size} bytes | Starting transfer of {self.total_data} bytes")
            print("-" * 70)
            print("Progress |  Sent (B) | Acknowledged (B) | Window Utilization")
            print("-" * 70)
            
            while self.acknowledged < self.total_data:
                # Calculate how much data we can send in the current window
                can_send = min(self.window_size - (self.sent - self.acknowledged), 
                               self.total_data - self.sent)
                
                if can_send > 0:
                    # Generate test data
                    data = b'X' * can_send
                    self.client_socket.sendall(data)
                    self.sent += can_send
                    
                    # Check for acknowledgements
                    ack_data = self.client_socket.recv(4096)
                    if ack_data:
                        self.acknowledged += len(ack_data)
                        ack_count += 1
                else:
                    # Wait for server acknowledgment before sending more
                    ack_data = self.client_socket.recv(4096)
                    if ack_data:
                        self.acknowledged += len(ack_data)
                        ack_count += 1
                
                # Print progress every 10%
                current_progress = int(self.acknowledged / self.total_data * 100)
                if current_progress >= last_progress + 10:
                    last_progress = current_progress
                    window_usage = (self.sent - self.acknowledged) / self.window_size * 100
                    print(f"{current_progress:7}% | {self.sent:9} | {self.acknowledged:16} | {window_usage:6.1f}%")
            
            # Calculate final metrics
            end_time = time.time()
            transfer_time = end_time - start_time
            throughput = self.total_data / transfer_time
            
            # Print summary
            print("-" * 70)
            print(f"Transfer complete in {transfer_time:.2f} seconds")
            print(f"Throughput: {throughput:.0f} bytes/sec")
            print(f"Total ACKs received: {ack_count}")
            print(f"Average bytes per ACK: {self.total_data / ack_count:.1f}")
            
            return transfer_time, throughput, ack_count
            
        except Exception as e:
            print(f"Error: {e}")
            return None, None, None
        finally:
            self.client_socket.close()
            print("Connection closed")

def run_simulation(host, port, window_sizes, data_size=50000):
    print(f"Starting simulation with {len(window_sizes)} window sizes...")
    results = []
    
    for i, window_size in enumerate(window_sizes):
        print(f"\n=== Test {i+1}/{len(window_sizes)}: Window Size {window_size} bytes ===")
        client = TCPWindowClient(host, port, window_size, data_size)
        
        if client.connect():
            transfer_time, throughput, ack_count = client.send_data()
            
            if transfer_time:
                results.append((window_size, transfer_time, throughput, ack_count))
                time.sleep(0.5)  # Brief pause between tests
    
    # Display results table
    if results:
        print("\n=== SUMMARY RESULTS ===")
        print("Window Size (B) | Transfer Time (s) | Throughput (B/s) | ACK Count | Bytes/ACK")
        print("--------------- | ----------------- | ---------------- | --------- | ---------")
        for size, time_taken, tput, acks in results:
            bytes_per_ack = data_size / acks if acks else 0
            print(f"{size:13} | {time_taken:17.2f} | {tput:14.0f} | {acks:9} | {bytes_per_ack:9.1f}")
        
        # Create and save plot
        plot_results(results, data_size)
    
    return results

def plot_results(results, data_size):
    window_sizes = [r[0] for r in results]
    transfer_times = [r[1] for r in results]
    throughputs = [r[2] for r in results]
    ack_counts = [r[3] for r in results]
    
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 2, 1)
    plt.plot(window_sizes, transfer_times, marker='o', color='blue')
    plt.title('Window Size vs Transfer Time')
    plt.xlabel('Window Size (bytes)')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    
    plt.subplot(2, 2, 2)
    plt.plot(window_sizes, throughputs, marker='o', color='green')
    plt.title('Window Size vs Throughput')
    plt.xlabel('Window Size (bytes)')
    plt.ylabel('Throughput (bytes/s)')
    plt.grid(True)
    
    plt.subplot(2, 2, 3)
    plt.plot(window_sizes, ack_counts, marker='o', color='red')
    plt.title('Window Size vs ACK Count')
    plt.xlabel('Window Size (bytes)')
    plt.ylabel('Number of ACKs')
    plt.grid(True)
    
    plt.subplot(2, 2, 4)
    bytes_per_ack = [data_size / count if count else 0 for count in ack_counts]
    plt.plot(window_sizes, bytes_per_ack, marker='o', color='purple')
    plt.title('Window Size vs Bytes per ACK')
    plt.xlabel('Window Size (bytes)')
    plt.ylabel('Bytes per ACK')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('tcp_window_results.png')
    print("\nResults chart saved to tcp_window_results.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Window Size Simulation')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8888, help='Server port')
    parser.add_argument('--data-size', type=int, default=50000, 
                        help='Data size in bytes')
    parser.add_argument('--window-sizes', type=int, nargs='+', 
                        default=[512, 1024, 2048, 4096, 8192],
                        help='Window sizes to test')
    
    args = parser.parse_args()
    
    print("TCP Window Size Simulation")
    print(f"Server: {args.host}:{args.port}")
    print(f"Data Size: {args.data_size} bytes")
    print(f"Window Sizes: {args.window_sizes}")
    
    input("Make sure your TCP server is running. Press Enter to start...")
    
    run_simulation(args.host, args.port, args.window_sizes, args.data_size)