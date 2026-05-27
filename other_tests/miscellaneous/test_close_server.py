# Run as script:
#   python tests/test_close_server.py <optional_port>

import sys
sys.path.insert(0, '..')

from socket_tcp import SocketTCP

# This script demonstrates the server-side close path using `recv_close()`.
# It accepts a connection, receives data, and then performs the passive
# close sequence (receive FIN, send FIN+ACK, wait for final ACK).
def test_close_server(port=9001):
    # Create and bind the listening socket
    server = SocketTCP()
    server.bind(("localhost", port))
    print(f"Server listening on {server.local_address}:{server.local_port}...")
    
    # Accept an incoming connection and inspect connection metadata
    conn, (client_addr, client_port) = server.accept()
    print(f"[Server] Accepted connection from {client_addr}:{client_port}")
    print(f"[Server] Connection state: {conn.state}")
    print(f"[Server] Initial seq: {conn.sequence_number}, peer_seq: {conn.last_peer_seq}")
    
    # Receive some data from the client (demonstrating recv behavior)
    data1 = conn.recv(50)
    print(f"[Server] Received: {data1.decode('utf-8')}")
    
    # Passive close: call recv_close() to perform the FIN/FIN+ACK/ACK handshake
    print(f"[Server] Calling recv_close()...")
    conn.recv_close()
    print(f"[Server] Connection state after recv_close: {conn.state}")
    print(f"[Server] Final seq: {conn.sequence_number}, peer_seq: {conn.last_peer_seq}")
    print("[Server] Close sequence complete!")


if __name__ == "__main__":
    # Optional port argument; default 9001
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    test_close_server(port)
