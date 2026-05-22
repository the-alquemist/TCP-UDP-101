# Run as script:
#   python tests/test_handshake_server.py <optional_port>

import sys
sys.path.insert(0, '..')

import socket_tcp

# This script demonstrates the three-way handshake from the server side.
# It binds a listening `SocketTCP`, waits for a SYN, replies SYN-ACK from
# an ephemeral socket, and finishes the handshake when the final ACK
# arrives on the new socket.
def test_handshake_server(port=9000):
    # Address to bind and listen on
    address = ("localhost", port)

    # Create the listening SocketTCP and bind to the address
    server_socketTCP = socket_tcp.SocketTCP()
    server_socketTCP.bind(address)
    print(f"Server listening on {address}...")

    try:
        # Accept performs the server-side handshake and returns a new
        # connected SocketTCP bound to an ephemeral port.
        connection_socketTCP, new_address = server_socketTCP.accept()
        print(f"Handshake completed! New connection from {new_address}")
        print(f"Server state: {server_socketTCP}")
        print(f"Connection state: {connection_socketTCP}")

        # Close the connection socket (server closes its side)
        connection_socketTCP.close()
    except Exception as e:
        # Print any unexpected errors during handshake
        print(f"Server error: {e}")
    finally:
        # Ensure listening socket is closed on exit
        server_socketTCP.close()


if __name__ == "__main__":
    # Allow optional port argument, default to 9000
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    test_handshake_server(port)
