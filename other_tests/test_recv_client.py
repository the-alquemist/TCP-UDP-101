# Run as script:
#   python tests/test_recv_client.py <optional_port>

import sys
sys.path.insert(0, '..')

import socket_tcp

# This test script demonstrates client-side usage of SocketTCP.
# It connects to the server, sends several messages (including a
# message designed to be split across multiple recv() calls), and then
# performs an active close using `close()`.
def test_recv_client(port=9000):
	# The server address we will connect to
	address = ("localhost", port)

	# Create a client SocketTCP and perform the handshake with the server
	client_socketTCP = socket_tcp.SocketTCP()
	client_socketTCP.connect(address)

	# Test 1: send a 16-byte message that matches the chunk size
	message = "Mensje de len=16".encode()
	client_socketTCP.send(message)

	# Test 2: send a 19-byte message that fits in a single recv(buffer)
	message = "Mensaje de largo 19".encode()
	client_socketTCP.send(message)

	# Test 3: send the same 19-byte message again so the server can
	# demonstrate split recv behaviour (e.g., two recv(14) calls).
	message = "Mensaje de largo 19".encode()
	client_socketTCP.send(message)

	# Active close: send FIN and finish the connection
	client_socketTCP.close()


if __name__ == "__main__":
	# Optional port argument, default 9000
	port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
	test_recv_client(port)
