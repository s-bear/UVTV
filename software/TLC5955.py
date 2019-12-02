

#from pyserial at_protocol example
import logging
import serial
import serial.threaded
import threading

try:
    import queue
except ImportError:
    import Queue as queue

class SCPIException(Exception):
    pass

class SCPIPacketizer(serial.threaded.Packetizer):
    TERMINATOR = b'\r\n'

    def __init__(self, response_queue: queue.Queue):
        super(SCPIPacketizer, self).__init__()
        self._response_queue = response_queue
    
    @staticmethod
    def factory(response_queue: queue.Queue):
        return lambda: SCPIPacketizer(response_queue)

    def _parse_scpi(self, token: bytes):
        if len(token) == 0: return None
        if token[0] == b'#':
            if len(token) == 1: return None
            elif token[1] in b'hH': #hex number
                return int(token[2:],16)
            elif token[1] in b'qQ': #octal
                return int(token[2:],8)
            elif token[1] in b'bB': #binary
                return int(token[2:],2)
            elif token[1] in b'123456789': #arbitrary data
                n = int(token[1]) #number of digits of length
                n = int(token[2:2+n]) #length
                data = token[2+n:]
                if len(data) != n:
                    raise SCPIException('Error parsing arbitrary data {}'.format(token))
                return data
        elif token[0] == b'"' and token[-1] == b'"':
            return str(token[1:-1],'utf-8')
        else:
            try:
                return float(token)
            except ValueError:
                raise SCPIException('Error parsing SCPI data {}'.format(token))

    def handle_packet(self, packet: bytes):
        tokens = packet.split(b',')
        response = [self._parse_scpi(token) for token in tokens]
        self._response_queue.put(response)

class SCPIProtocol:
    def __init__(self, serial_instance):
        self.responses = queue.Queue()
        self._read_thread = serial.threaded.ReaderThread(serial_instance, SCPIPacketizer.factory(self.responses))
        
    def stop(self):
        self._read_thread.stop()
    
    def close(self):
        self._read_thread.close()

    def connect(self):
        return self._read_thread.connect()
    
    def __enter__(self):
        return self._read_thread.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._read_thread.__exit__(exc_type, exc_val, exc_tb)

    def command(self, command, wait_for_response=True, timeout=5):
        self._read_thread.write(command)
        if wait_for_response:
            return self.response(timeout)
        else:
            return None

    def response(self, timeout=5):
        try:
            return self.responses.get(timeout=timeout)
        except queue.Empty:
            raise SCPIException('SCPI response timeout')