# Run as script:
#   python tests/test_close_client.py <optional_port>

import sys
sys.path.insert(0, '..')

from socket_tcp import SocketTCP

# This script demonstrates the client-side close path using `close()`.
# It connects to a server, sends a test message, and performs an active close
# (send FIN, wait for FIN+ACK, send final ACKs).
def test_close_client(port=9001):    
    # Create a client SocketTCP and establish the handshake with server
    client = SocketTCP()
    print("[Client] Connecting to server...")
    client.connect(("localhost", port))
    print(f"[Client] Connected successfully")
    print(f"[Client] Connection state: {client.state}")
    print(f"[Client] Current seq: {client.sequence_number}, peer seq: {client.last_peer_seq}")
    
    # Send a test message to the server
    message = "Hello from client!"
    bytes_sent = client.send(message)
    print(f"[Client] Sent {bytes_sent} bytes: {message}")
    
    # Active close: call close() which performs the FIN/FIN+ACK/ACK exchange
    print(f"[Client] Calling close()...")
    client.close()
    print(f"[Client] Connection state after close: {client.state}")
    print(f"[Client] Final seq: {client.sequence_number}, peer seq: {client.last_peer_seq}")
    print("[Client] Close sequence complete!")


if __name__ == "__main__":
    # Optional port argument, default is 9001
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    test_close_client(port)
