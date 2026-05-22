# TCP-like socket implementation over UDP - Actividad 3

"""
Author Declaration

Code Author: Joaquín Acosta

Acknowledgements:
- Guidance/Assistance: Ivana Bachmann
- Other contributors: Lady Esquivel
- AI was used for code optimization and debugging, core logic and structure were designed by the author.
"""

import socket
import random
import time

class SocketTCP:
    
    def __init__(self):
        # UDP socket for underlying transport
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Local address and port, bind()
        self.local_address = None
        self.local_port = None
        
        # Remote address and port, connect() or recvfrom()
        self.remote_address = None
        self.remote_port = None
        
        # Sequence number for tracking sent packets
        self.sequence_number = 0
        
        # Last sequence number received from the peer
        self.last_peer_seq = 0
        
        # Connection state: 'closed', 'listening', 'connected'
        self.state = "closed"
        
        # Buffer for incomplete data
        self.buffer = b""

        # Total bytes left to return for the current incoming message
        self.bytes_remaining = 0

        # Length of the current incoming message
        self.message_length = 0
        
        # Timeout setting for socket operations
        self.timeout = None
    
    def bind(self, address):
        try:
            host, port = address
        except Exception:
            raise TypeError("address must be a (host, port) tuple")
        self.socket.bind((host, port))
        self.local_address = host
        self.local_port = port
        self.state = "listening"
        print(f"[SocketTCP] bind: listening on {host}:{port}")
    
    def connect(self, address):
        try:
            host, port = address
        except Exception:
            raise TypeError("address must be a (host, port) tuple")
        self.remote_address = host
        self.remote_port = port

        print(f"[SocketTCP] connect: initiating to {host}:{port}")

        # choose initial sequence number
        self.sequence_number = random.randint(0, 100)

        # send SYN and keep retrying until a valid SYN-ACK arrives.
        syn_header = {"SYN": 1, "ACK": 0, "FIN": 0, "seq": self.sequence_number}
        syn_seg = SocketTCP.create_segment(syn_header)
        self.socket.sendto(syn_seg, (host, port))
        print(f"[SocketTCP] connect: sent SYN seq={self.sequence_number} -> {host}:{port}")

        while True:
            data, (addr, pr) = self.socket.recvfrom(4096)

            try:
                header, _ = SocketTCP.parse_segment(data)
            except Exception:
                self.socket.sendto(syn_seg, (host, port))
                continue

            if header.get("SYN") == 1 and header.get("ACK") == 1:
                # bare-minimum handshake: the server replies with seq = client_seq + 1
                expected_server_seq = self.sequence_number + 1
                if header.get("seq") != expected_server_seq:
                    self.socket.sendto(syn_seg, (host, port))
                    continue

                # remember the peer's sequence and send final ACK with seq = client_seq + 2
                # send ACK back to the address we received the SYN-ACK from (server's new port)
                self.last_peer_seq = expected_server_seq
                self.sequence_number = expected_server_seq + 1
                ack_header = {"SYN": 0, "ACK": 1, "FIN": 0, "seq": self.sequence_number}
                ack_seg = SocketTCP.create_segment(ack_header)
                self.socket.sendto(ack_seg, (addr, pr))
                print(f"[SocketTCP] connect: received SYN-ACK seq={header.get('seq')} from {addr}:{pr}, sent ACK seq={self.sequence_number}")

                # The connection continues over the server's new socket endpoint.
                self.remote_address = addr
                self.remote_port = pr

                self.state = "connected"
                return

            self.socket.sendto(syn_seg, (host, port))
    
    def send(self, message):
        if self.state != "connected":
            raise RuntimeError("Socket is not connected")

        try:
            print(f"[SocketTCP] send: {type(message).__name__} len=? starting; seq={self.sequence_number}")
            # str-like objects
            message_bytes = message.encode("utf-8")
        except Exception:
            try:
                # bytes/bytearray-like objects
                message_bytes = bytes(message)
            except Exception:
                raise TypeError("message must be str or bytes-like")

        chunk_size = 16
        timeout_seconds = 1.0

        # First segment informs the total payload size in bytes.
        length_payload = str(len(message_bytes)).encode("utf-8")
        segments = [length_payload]

        for i in range(0, len(message_bytes), chunk_size):
            chunk = message_bytes[i:i + chunk_size]
            segments.append(chunk)

        previous_timeout = self.socket.gettimeout()
        self.socket.settimeout(timeout_seconds)

        try:
            for segment_index, payload in enumerate(segments):
                header = {"SYN": 1, "ACK": 0, "FIN": 0, "seq": self.sequence_number}
                segment = SocketTCP.create_segment(header, payload)
                expected_ack_seq = self.sequence_number + len(payload)
                is_last_segment = segment_index == len(segments) - 1
                last_segment_timeout_count = 0
                print(f"[SocketTCP] send: sending seq={self.sequence_number} len={len(payload)} expected_ack={expected_ack_seq}")

                # Stop & Wait: retransmit until matching ACK for this seq arrives.
                while True:
                    self.socket.sendto(segment, (self.remote_address, self.remote_port))
                    try:
                        ack_data, (ack_addr, ack_port) = self.socket.recvfrom(4096)
                    except socket.timeout:
                        if is_last_segment:
                            last_segment_timeout_count += 1
                            if last_segment_timeout_count >= 6:
                                # Prevent infinite loop on final chunk when its ACK is repeatedly lost.
                                print(f"[SocketTCP] send: final segment seq={self.sequence_number} timed out 6 times, assuming delivered")
                                self.sequence_number = expected_ack_seq
                                self.last_peer_seq = expected_ack_seq
                                break
                        print(f"[SocketTCP] send: timeout waiting for ack seq={expected_ack_seq}, retransmitting...")
                        continue

                    if ack_addr != self.remote_address or ack_port != self.remote_port:
                        continue

                    try:
                        ack_header, _ = SocketTCP.parse_segment(ack_data)
                    except Exception:
                        continue

                    if ack_header.get("SYN") == 0 and ack_header.get("ACK") == 1 and ack_header.get("seq") == expected_ack_seq:
                        self.last_peer_seq = ack_header.get("seq")
                        self.sequence_number = expected_ack_seq
                        print(f"[SocketTCP] send: ack received seq={ack_header.get('seq')}")
                        break
                    elif ack_header.get("SYN") == 1 and ack_header.get("ACK") == 1 and ack_header.get("seq") == self.last_peer_seq:
                        # Stale handshake SYN-ACK: final ACK didn't reach server. Resend it.
                        final_ack_header = {"SYN": 0, "ACK": 1, "FIN": 0, "seq": self.sequence_number}
                        final_ack_seg = SocketTCP.create_segment(final_ack_header)
                        self.socket.sendto(final_ack_seg, (self.remote_address, self.remote_port))
                        print("[SocketTCP] send: detected stale SYN-ACK, resent final ACK")
                        continue
        finally:
            self.socket.settimeout(previous_timeout)

        return len(message_bytes)
    
    def recv(self, buffer_size=1024):
        if self.state != "connected":
            raise RuntimeError("Socket is not connected")

        if buffer_size <= 0:
            raise ValueError("buffer_size must be greater than 0")

        udp_buffer_size = 4096
        print(f"[SocketTCP] recv: called with buffer_size={buffer_size}, bytes_remaining={self.bytes_remaining}")

        # Helper to send a simple ACK for a given sequence value
        def send_ack(seq_value):
            ack_header = {"SYN": 0, "ACK": 1, "FIN": 0, "seq": seq_value}
            ack_segment = SocketTCP.create_segment(ack_header)
            self.socket.sendto(ack_segment, (self.remote_address, self.remote_port))

        # Start a new message if needed by reading the first length segment.
        if self.bytes_remaining == 0 and not self.buffer:
            while True:
                data, (address, port) = self.socket.recvfrom(udp_buffer_size)
                try:
                    header, payload = SocketTCP.parse_segment(data)
                except Exception:
                    continue

                self.remote_address = address
                self.remote_port = port

                # Handle leftover handshake packets: if we get a SYN-ACK that matches
                # the last seen server seq, it means the client's final ACK might
                # not have been received. Resend the final ACK and keep listening.
                if header.get("SYN") == 1 and header.get("ACK") == 1 and header.get("seq") == self.last_peer_seq:
                    final_ack_header = {"SYN": 0, "ACK": 1, "FIN": 0, "seq": self.sequence_number}
                    final_ack_seg = SocketTCP.create_segment(final_ack_header)
                    self.socket.sendto(final_ack_seg, (self.remote_address, self.remote_port))
                    continue

                # Expect the first data segment to be a SYN=1,ACK=0 length announcement
                if header.get("SYN") == 1 and header.get("ACK") == 0 and header.get("seq") == self.last_peer_seq:
                    print(f"[SocketTCP] recv: received length segment seq={header.get('seq')} payload_len={len(payload)}")
                    try:
                        self.message_length = int(payload.decode("utf-8"))
                    except Exception:
                        self.message_length = 0

                    # Record how many bytes we expect and ACK the length segment
                    self.bytes_remaining = self.message_length
                    send_ack(header.get("seq") + len(payload))
                    self.last_peer_seq = header.get("seq") + len(payload)
                    break
                elif header.get("SYN") == 1 and header.get("ACK") == 0 and header.get("seq") < self.last_peer_seq:
                    # Duplicate length segment: ACK it again, but do not restart the message.
                    send_ack(header.get("seq") + len(payload))
                    print(f"[SocketTCP] recv: duplicate length segment seq={header.get('seq')} acked")

        # Keep receiving until we have enough bytes to return for this call,
        # or until the whole message has been received.
        target_size = min(buffer_size, self.bytes_remaining)
        while len(self.buffer) < target_size and self.bytes_remaining > 0:
            data, (address, port) = self.socket.recvfrom(udp_buffer_size)
            try:
                header, payload = SocketTCP.parse_segment(data)
            except Exception:
                continue

            self.remote_address = address
            self.remote_port = port

            # Accept in-order data segments and ACK them; ignore duplicates
            if header.get("SYN") == 1 and header.get("ACK") == 0 and header.get("seq") == self.last_peer_seq:
                self.buffer += payload
                send_ack(header.get("seq") + len(payload))
                self.last_peer_seq = header.get("seq") + len(payload)
                print(f"[SocketTCP] recv: accepted data seq={header.get('seq')} len={len(payload)} buffer_len={len(self.buffer)} last_peer_seq={self.last_peer_seq}")
            elif header.get("SYN") == 1 and header.get("ACK") == 0 and header.get("seq") < self.last_peer_seq:
                # Duplicate segment: ACK it again, but do not append it twice.
                send_ack(header.get("seq") + len(payload))
                print(f"[SocketTCP] recv: duplicate data seq={header.get('seq')} acked")

        bytes_to_return = min(buffer_size, self.bytes_remaining, len(self.buffer))
        result = self.buffer[:bytes_to_return]
        self.buffer = self.buffer[bytes_to_return:]
        self.bytes_remaining -= bytes_to_return

        print(f"[SocketTCP] recv: returning {len(result)} bytes, bytes_remaining now {self.bytes_remaining}")
        return result
    
    def close(self):
        if self.state != "connected":
            if self.socket:
                self.socket.close()
            self.state = "closed"
            return

        timeout_seconds = 1.0
        previous_timeout = self.socket.gettimeout()
        self.socket.settimeout(timeout_seconds)

        # Active close (client): initiate FIN exchange
        print(f"[SocketTCP] close: initiating close seq={self.sequence_number}")
        try:
            # Client side: send FIN and wait for server FIN+ACK.
            fin_seq = self.sequence_number
            fin_header = {"SYN": 0, "ACK": 0, "FIN": 1, "seq": fin_seq}
            fin_segment = SocketTCP.create_segment(fin_header)
            timeout_count = 0

            # Send FIN and wait for FIN+ACK from the peer. Retry a few times.
            while timeout_count < 3:
                self.socket.sendto(fin_segment, (self.remote_address, self.remote_port))
                print(f"[SocketTCP] close: sent FIN seq={fin_seq}")
                try:
                    response_data, (response_addr, response_port) = self.socket.recvfrom(4096)
                except socket.timeout:
                    timeout_count += 1
                    print(f"[SocketTCP] close: timeout {timeout_count}/3 waiting for FIN+ACK")
                    continue

                # Ignore packets from unexpected sources during close
                if response_addr != self.remote_address or response_port != self.remote_port:
                    continue

                try:
                    response_header, _ = SocketTCP.parse_segment(response_data)
                except Exception:
                    continue

                # Expect a FIN+ACK whose seq equals our FIN seq + 1
                if response_header.get("FIN") == 1 and response_header.get("ACK") == 1 and response_header.get("seq") == fin_seq + 1:
                    self.last_peer_seq = response_header.get("seq")
                    self.sequence_number = fin_seq + 1
                    break

            if timeout_count >= 3:
                print("[SocketTCP] close: assuming peer already closed after 3 timeouts")
                if self.socket:
                    self.socket.close()
                self.state = "closed"
                return

            # Final ACK back to the server.
            final_ack_seq = self.sequence_number + 1
            final_ack_header = {"SYN": 0, "ACK": 1, "FIN": 0, "seq": final_ack_seq}
            final_ack_segment = SocketTCP.create_segment(final_ack_header)
            for ack_index in range(3):
                self.socket.sendto(final_ack_segment, (self.remote_address, self.remote_port))
                print(f"[SocketTCP] close: sent final ACK {ack_index + 1}/3 seq={final_ack_seq}")
                self.last_peer_seq = final_ack_seq
                self.sequence_number = final_ack_seq
                if ack_index < 2:
                    time.sleep(timeout_seconds)
        finally:
            if self.socket:
                try:
                    self.socket.settimeout(previous_timeout)
                except OSError:
                    pass

        if self.socket:
            self.socket.close()
        self.state = "closed"

    def recv_close(self):
        if self.state != "connected":
            raise RuntimeError("Socket is not connected")

        timeout_seconds = 1.0
        previous_timeout = self.socket.gettimeout()
        self.socket.settimeout(timeout_seconds)

        # Passive close (server): wait for client's FIN, reply FIN+ACK, then wait for final ACK
        print("[SocketTCP] recv_close: waiting for FIN from peer")
        try:
            # Server side: wait for the client's FIN.
            while True:
                try:
                    fin_data, (fin_addr, fin_port) = self.socket.recvfrom(4096)
                except socket.timeout:
                    continue

                # Ignore packets from unexpected sources while waiting for FIN
                if fin_addr != self.remote_address or fin_port != self.remote_port:
                    continue

                try:
                    fin_header, _ = SocketTCP.parse_segment(fin_data)
                except Exception:
                    continue

                # If this is the client's FIN (no ACK flag), reply with FIN+ACK
                if fin_header.get("FIN") == 1 and fin_header.get("ACK") == 0:
                    client_fin_seq = fin_header.get("seq")
                    self.last_peer_seq = client_fin_seq

                    # Reply with FIN+ACK using seq = client_fin_seq + 1.
                    fin_ack_header = {"SYN": 0, "ACK": 1, "FIN": 1, "seq": client_fin_seq + 1}
                    fin_ack_segment = SocketTCP.create_segment(fin_ack_header)
                    self.socket.sendto(fin_ack_segment, (self.remote_address, self.remote_port))
                    print(f"[SocketTCP] recv_close: received FIN seq={client_fin_seq}, sent FIN+ACK seq={client_fin_seq+1}")
                    self.sequence_number = client_fin_seq + 1

                    # Wait for the client's final ACK (seq = client_fin_seq + 2).
                    timeout_count = 0
                    while True:
                        try:
                            ack_data, (ack_addr, ack_port) = self.socket.recvfrom(4096)
                        except socket.timeout:
                            timeout_count += 1
                            print(f"[SocketTCP] recv_close: timeout {timeout_count}/3 waiting for final ACK")
                            if timeout_count >= 3:
                                print("[SocketTCP] recv_close: assuming peer already closed after 3 timeouts")
                                break
                            continue

                        # Ignore packets not from the expected peer during final ACK wait
                        if ack_addr != self.remote_address or ack_port != self.remote_port:
                            continue

                        try:
                            ack_header, _ = SocketTCP.parse_segment(ack_data)
                        except Exception:
                            continue

                        if ack_header.get("ACK") == 1 and ack_header.get("FIN") == 0 and ack_header.get("seq") == client_fin_seq + 2:
                            self.last_peer_seq = ack_header.get("seq")
                            self.sequence_number = client_fin_seq + 2
                            print(f"[SocketTCP] recv_close: received final ACK seq={ack_header.get('seq')}")
                            break

                    break
        finally:
            self.socket.settimeout(previous_timeout)

        if self.socket:
            self.socket.close()
        self.state = "closed"
        
    def accept(self):
        if self.state != "listening":
            raise RuntimeError("Socket is not listening")

        # wait for SYN on the listening socket
        while True:
            data, (client_addr, client_port) = self.socket.recvfrom(4096)
            try:
                header, _ = SocketTCP.parse_segment(data)
            except Exception:
                continue

            if header.get("SYN") == 1 and header.get("ACK") == 0:
                client_isn = header.get("seq")
                break

        # create new socket to handle the connection, bind to another port
        new_sock = SocketTCP()
        bind_host = self.local_address if self.local_address is not None else ""
        new_sock.socket.bind((bind_host, 0))
        new_host, new_port = new_sock.socket.getsockname()
        new_sock.local_address = new_host
        new_sock.local_port = new_port

        # record remote endpoint
        new_sock.remote_address = client_addr
        new_sock.remote_port = client_port

        # bare-minimum handshake: server uses client_isn + 1 as its sequence
        new_sock.sequence_number = client_isn + 1
        new_sock.last_peer_seq = client_isn

        # send SYN-ACK from the new socket
        # Server responds with SYN-ACK from the new socket
        synack_header = {"SYN": 1, "ACK": 1, "FIN": 0, "seq": new_sock.sequence_number}
        synack_seg = SocketTCP.create_segment(synack_header)
        new_sock.socket.sendto(synack_seg, (client_addr, client_port))

        # wait for final ACK on the new socket without using a timeout.
        while True:
            data, (addr, pr) = new_sock.socket.recvfrom(4096)

            try:
                header, _ = SocketTCP.parse_segment(data)
            except Exception:
                new_sock.socket.sendto(synack_seg, (client_addr, client_port))
                continue

            # expect ACK with seq == client_isn + 2
            if header.get("ACK") == 1 and header.get("seq") == client_isn + 2:
                new_sock.remote_address = addr
                new_sock.remote_port = pr
                new_sock.last_peer_seq = header.get("seq")
                new_sock.sequence_number = header.get("seq")
                new_sock.state = "connected"
                return new_sock, (new_host, new_port)

            new_sock.socket.sendto(synack_seg, (client_addr, client_port))

    def create_segment(header: dict, payload: bytes = b"") -> bytes:
        # Create a simple header using '|||' as a separator followed by payload.
        # Header layout: SYN|||ACK|||FIN|||SEQ|||<payload bytes>
        sep = "|||"
        syn = "1" if header.get("SYN") else "0"
        ack = "1" if header.get("ACK") else "0"
        fin = "1" if header.get("FIN") else "0"
        seq = str(int(header.get("seq", 0)))
        header_str = sep.join([syn, ack, fin, seq, ""])
        header_bytes = header_str.encode("utf-8")
        if payload is None:
            payload = b""
        return header_bytes + payload

    def parse_segment(segment: bytes) -> tuple:
        # Parse the simple '|||' delimited header and return (header_dict, payload_bytes)
        if segment is None:
            raise TypeError("segment must be bytes or str")

        sep = b"|||"
        try:
            parts = segment.split(sep, 4)
        except TypeError:
            # If split with bytes separator fails, try to encode (assume str-like)
            try:
                segment = segment.encode("utf-8")
                parts = segment.split(sep, 4)
            except Exception:
                raise TypeError("segment must be bytes or str")
        # parts: [syn, ack, fin, seq, payload]
        if len(parts) < 4:
            raise ValueError("segment does not contain a complete header")

        syn_b = parts[0].decode("utf-8") if parts[0] else "0"
        ack_b = parts[1].decode("utf-8") if parts[1] else "0"
        fin_b = parts[2].decode("utf-8") if parts[2] else "0"
        seq_s = parts[3].decode("utf-8") if parts[3] else "0"
        try:
            seq = int(seq_s)
        except ValueError:
            seq = 0

        payload = parts[4] if len(parts) > 4 else b""

        header = {
            "SYN": 1 if syn_b == "1" else 0,
            "ACK": 1 if ack_b == "1" else 0,
            "FIN": 1 if fin_b == "1" else 0,
            "seq": seq,
        }

        return header, payload
    
    def __repr__(self):
        return (f"SocketTCP(local={self.local_address}:{self.local_port}, "
                f"remote={self.remote_address}:{self.remote_port}, "
                f"seq={self.sequence_number}, peer_seq={self.last_peer_seq}, "
                f"state='{self.state}')")