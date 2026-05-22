"""
Beta server test script.

Usage as script:
    python3 test_beta_server.py <optional_port>

This server accepts a connection and runs three recv() tests:
  - Test 1: recv(16) receives a 16-byte payload
  - Test 2: recv(19) receives a 19-byte payload
  - Test 3: two recv(14) calls reassemble a 19-byte payload

After tests complete the server performs a passive close via recv_close().
"""

import sys
sys.path.insert(0, '..')

from socket_tcp import SocketTCP


def test_server(port=8000):
    # Create and bind a listening SocketTCP
    server = SocketTCP()
    server.bind(("localhost", port))
    print(f"[Server] Listening on localhost:{port}...")

    try:
        # Perform accept() which completes the handshake and returns
        # a connected SocketTCP instance bound to an ephemeral port.
        conn, new_address = server.accept()
        print(f"[Server] Handshake completed! New connection from {new_address}")
        print(f"[Server] Server state: {server.state}")
        print(f"[Server] Connection state: {conn.state}")

        # Test 1: exact-size recv
        buff_size = 16
        full_message = conn.recv(buff_size)
        print("[Server] Test 1 received:", full_message)
        if full_message == "Mensje de len=16".encode():
            print("[Server] Test 1: Passed")
        else:
            print("[Server] Test 1: Failed")

        # Test 2: single recv with buffer >= message length
        buff_size = 19
        full_message = conn.recv(buff_size)
        print("[Server] Test 2 received:", full_message)
        if full_message == "Mensaje de largo 19".encode():
            print("[Server] Test 2: Passed")
        else:
            print("[Server] Test 2: Failed")

        # Test 3: split recv — read the same 19-byte message in two calls
        buff_size = 14
        message_part_1 = conn.recv(buff_size)
        message_part_2 = conn.recv(buff_size)
        combined = message_part_1 + message_part_2
        print("[Server] Test 3 received:", combined)
        if combined == "Mensaje de largo 19".encode():
            print("[Server] Test 3: Passed")
        else:
            print("[Server] Test 3: Failed")

        # Perform passive close and show final sequence numbers
        print(f"[Server] Calling recv_close() for localhost:{port}...")
        conn.recv_close()
        print(f"[Server] Connection state after recv_close: {conn.state}")
        print(f"[Server] Final seq: {conn.sequence_number}, peer seq: {conn.last_peer_seq}")
        print("[Server] All server tests complete!")
    finally:
        server.close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    test_server(port)
