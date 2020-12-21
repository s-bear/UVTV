

#from pyserial at_protocol example
import serial
import serial.threaded
import numpy as np

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
        if token[0] == ord('#'):
            if len(token) == 1: return None
            elif token[1] in b'hH': #hex number
                return int(token[2:],16)
            elif token[1] in b'qQ': #octal
                return int(token[2:],8)
            elif token[1] in b'bB': #binary
                return int(token[2:],2)
            elif token[1] in b'123456789': #arbitrary data
                d = int(token[1:2]) #number of digits of length
                n = int(token[2:2+d]) #length
                data = token[2+d:]
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
        self.port = serial_instance
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

    def command(self, command: bytes, wait_for_response=False, timeout=5):
        if type(command) is str:
            command = bytes(command, 'utf-8')
        self._read_thread.write(command)
        self._read_thread.write(SCPIPacketizer.TERMINATOR)
        if wait_for_response:
            return self.response(timeout)
        else:
            return None

    def format_bytes(self, data: bytes):
        n = '{}'.format(len(data))
        d = '{}'.format(len(n))
        return bytes('#'+d+n,'utf-8') + data

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
    def mode_code(dsprpt=False,tmgrst=False,rfresh=False,espwm=False,lsdvlt=False):
        m  = TLC5955.DSPRPT * bool(dsprpt)
        m |= TLC5955.TMGRST * bool(tmgrst)
        m |= TLC5955.RFRESH * bool(rfresh)
        m |= TLC5955.ESPWM  * bool(espwm)
        m |= TLC5955.LSDVLT * bool(lsdvlt)
        return m
    
    @staticmethod
    def maxcurrent_code(Imax_mA):
        """picks the largest allowed current less than or equal to the given current"""
        Imcs = [3.2,8,11.2,15.9,19.1,23.9,27.1,31.9]
        for i,Imc in enumerate(Imcs):
            if Imc > Imax_mA:
                break
        if i > 0: return i-1
        else: return 0
    
    @staticmethod
    def brightness_code(brightness):
        """brightness within 0.1 to 1"""
        return np.clip(np.floor((brightness-0.1)*np.nextafter(128,0)/0.9),0,127)
    
    @staticmethod
    def dotcorrect_code(dot_correct_img):
        """dot correct within 0.262 to 1"""
        dot_correct_img = np.asarray(dot_correct_img)
        dot_correct_img[np.isnan(dot_correct_img)] = 1.0 #dead pixels have a dc of nan
        return np.clip(np.floor((dot_correct_img - 0.262)*np.nextafter(128,0)/0.738),0,127).astype(np.uint8)

    @staticmethod
    def pwm_code(img):
        """pwm values from 0.0 to 1.0"""
        return np.clip(np.floor(np.nextafter(65536,0)*img),0,65535).astype(np.uint16)
    