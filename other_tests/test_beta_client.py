"""
Beta client test script.

Usage as script:
    python3 test_beta_client.py <optional_port>

This client connects to the beta server and sends three test messages
then performs an active close using `close()`.
"""

import sys
sys.path.insert(0, '..')

from socket_tcp import SocketTCP
import time


def test_client(port=8000):
    # Small delay so the server has time to bind and listen
    time.sleep(0.5)

    # Create client SocketTCP and perform the handshake
    client = SocketTCP()
    print(f"[Client] Connecting to localhost:{port}...")
    client.connect(("localhost", port))
    print("[Client] Handshake completed on client side!")
    print(f"[Client] State: {client.state}")
    print(f"[Client] Current seq: {client.sequence_number}, peer seq: {client.last_peer_seq}")

    # Test 1: send 16-byte message
    message_1 = "Mensje de len=16".encode()
    client.send(message_1)
    print(f"[Client] Test 1 sent: {message_1}")

    # Test 2: send 19-byte message
    message_2 = "Mensaje de largo 19".encode()
    client.send(message_2)
    print(f"[Client] Test 2 sent: {message_2}")

    # Test 3: repeat the 19-byte message for split-recv demonstration
    message_3 = "Mensaje de largo 19".encode()
    client.send(message_3)
    print(f"[Client] Test 3 sent: {message_3}")

    # Active close: close the connection from the client side
    print(f"[Client] Calling close() on localhost:{port}...")
    client.close()
    print(f"[Client] Connection state after close: {client.state}")
    print("[Client] All client tests complete!")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    test_client(port)
