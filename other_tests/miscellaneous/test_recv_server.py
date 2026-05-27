# Run as script:
#   python tests/test_recv_server.py <optional_port>

import sys
sys.path.insert(0, '..')

import socket_tcp

# This test script demonstrates server-side `recv()` behaviour.
# It binds a listening `SocketTCP`, accepts a connection, and performs
# several `recv(buffer_size)` calls to show full and split reads.

def test_recv_server(port=9000):
	# Prepare the server listening address
	address = ("localhost", port)

	# Create the server socket and bind to the chosen address
	server_socketTCP = socket_tcp.SocketTCP()
	server_socketTCP.bind(address)

	# Accept an incoming connection (returns the connection socket)
	connection_socketTCP, new_address = server_socketTCP.accept()

	# Test 1: single recv that exactly matches a 16-byte payload
	buff_size = 16
	full_message = connection_socketTCP.recv(buff_size)
	print("Test 1 received:", full_message)
	if full_message == "Mensje de len=16".encode(): print("Test 1: Passed")
	else: print("Test 1: Failed")

	# Test 2: single recv for a 19-byte message (buffer >= message length)
	buff_size = 19
	full_message = connection_socketTCP.recv(buff_size)
	print("Test 2 received:", full_message)
	if full_message == "Mensaje de largo 19".encode(): print("Test 2: Passed")
	else: print("Test 2: Failed")

	# Test 3: split recv — call recv(14) twice to reconstruct a 19-byte message
	buff_size = 14
	message_part_1 = connection_socketTCP.recv(buff_size)
	message_part_2 = connection_socketTCP.recv(buff_size)
	print("Test 3 received:", message_part_1 + message_part_2)
	if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode(): print("Test 3: Passed")
	else: print("Test 3: Failed")

	# Close the connection socket (active close) and then the listening socket
	connection_socketTCP.close()
	server_socketTCP.close()


if __name__ == "__main__":
	# Allow optional port from command line, default to 9000
	port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
	test_recv_server(port)
