

#from pyserial at_protocol example
import serial
import serial.threaded

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
        elif token[0] == ord('"') and token[-1] == ord('"'):
            return str(token[1:-1],'utf-8')
        else:
            try:
                return int(token)
            except ValueError:
                pass
            try:
                return float(token)
            except ValueError:
                return token

    def handle_packet(self, packet: bytes):
        tokens = packet.split(b',')
        response = [self._parse_scpi(token) for token in tokens]
        self._response_queue.put(response)

class SCPIProtocol:
    def __init__(self, serial_instance):
        self.responses = queue.Queue()
        self._read_thread = serial.threaded.ReaderThread(serial_instance, SCPIPacketizer.factory(self.responses))

    def start(self):
        self._read_thread.start()
        
    def stop(self):
        self._read_thread.stop()
    
    def close(self):
        self._read_thread.close()
    
    def __enter__(self):
        self._read_thread.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._read_thread.__exit__(exc_type, exc_val, exc_tb)

    def command(self, command: bytes, wait_for_response=True, timeout=5):
        if type(command) is str:
            command = bytes(command, 'utf-8')
        self._read_thread.write(command)
        self._read_thread.write(SCPIPacketizer.TERMINATOR)
        if wait_for_response:
            return self.response(timeout)
        else:
            return None

    def response(self, timeout=5):
        try:
            return self.responses.get(timeout=timeout)
        except queue.Empty:
            raise SCPIException('SCPI response timeout')

class TLC5955:
    DSPRPT=(1 << 0)
    TMGRST=(1 << 1)
    RFRESH=(1 << 2)
    ESPWM = (1 << 3)
    LSDVLT = (1 << 4)

    @staticmethod    
    def mode(dsprpt=False,tmgrst=False,rfresh=False,espwm=False,lsdvlt=False):
        m = 0
        if dsprpt: m |= TLC5955.DSPRPT
        if tmgrst: m |= TLC5955.TMGRST
        if rfresh: m |= TLC5955.RFRESH
        if espwm: m |= TLC5955.ESPWM
        if lsdvlt: m |= TLC5955.LSDVLT
        return m