# Run as script:
#   python tests/test_handshake_client.py <optional_port>

import sys
sys.path.insert(0, '..')

import socket_tcp

# This script demonstrates the client side of the three-way handshake.
# It creates a `SocketTCP`, connects to the server (SYN), receives the
# SYN-ACK and sends the final ACK, then optionally closes.
def test_handshake_client(port=9000):
    # Server address to connect to
    address = ("localhost", port)

    try:
        # Create the client socket and initiate the handshake
        client_socketTCP = socket_tcp.SocketTCP()
        print("Client connecting...")
        client_socketTCP.connect(address)
        print("Handshake completed on client side!")
        print(f"Client state: {client_socketTCP}")

        # Active close from the client side
        client_socketTCP.close()
    except Exception as e:
        # Report any errors encountered during handshake or close
        print(f"Client error: {e}")


if __name__ == "__main__":
    # Allow an optional port argument; default to 9000
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    test_handshake_client(port)
