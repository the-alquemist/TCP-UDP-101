#!/usr/bin/env python3

# Client final test script: connect using SocketTCP and send stdin contents.
# Usage:
#   python3 client.py [host] [port] < archivo.txt
# Defaults: host=localhost, port=8000
import sys
import argparse
from socket_tcp import SocketTCP


def main():
    # Parse the optional host and port arguments.
    parser = argparse.ArgumentParser(description="Send stdin file to server using SocketTCP")
    parser.add_argument("host", nargs="?", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("port", nargs="?", type=int, default=8000, help="Server port (default: 8000)")
    args = parser.parse_args()

    # Allow shorthand usage.
    if len(sys.argv) == 2:
        val = sys.argv[1]
        if val.isdigit():
            args.port = int(val)
            args.host = "localhost"
        else:
            args.host = val

    # Read the full input file from stdin.
    try:
        data = sys.stdin.buffer.read()
    except Exception as e:
        print(f"Error reading stdin: {e}", file=sys.stderr)
        sys.exit(1)

    # Create the client socket and connect to the server.
    client = SocketTCP()
    try:
        print(f"[Client] Connecting to {args.host}:{args.port}...")
        client.connect((args.host, args.port))
        print("[Client] Handshake completed on client side!")

        # Send the payload only if stdin had data.
        if not data:
            print("[Client] No data to send (stdin empty)")
        else:
            bytes_sent = client.send(data)
            print(f"[Client] Sent {bytes_sent} bytes")

        # Close the client side of the connection.
        client.close()
        print("[Client] Connection closed")
    except Exception as e:
        # If something fails, report the error and still try to close cleanly.
        print(f"Client error: {e}", file=sys.stderr)
        try:
            client.close()
        except Exception:
            pass
        sys.exit(2)


if __name__ == "__main__":
    main()