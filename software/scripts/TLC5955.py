

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
        
    def _parse_scpi(self, packet : bytes):
        if len(packet) == 0: return []
        responses = []
        i = 0
        
        while i < len(packet):
            c = packet[i]
            if c == ord(','):
                i += 1 #pop c
                continue #discard delimiters between items
            elif c == ord('#'): #hex, octal, or binary number; or arbitrary data
                i += 1 #pop c
                c = packet[i] #peek at next character
                if c in b'hHqQbB': 
                    #number -- parse to the comma
                    i += 1 #pop c
                    j = packet.find(b',',i)
                    if j == -1:
                        j = len(packet) #not found -- consume to end of packet
                    base = None
                    if c in b'hH': base = 16
                    elif c in b'qQ': base = 8
                    elif c in b'bB': base = 2
                    x = int(packet[i:j],base)
                    i = j #pop number (leave the comma)
                    responses.append(x)
                    continue
                elif c in b'123456789':
                    #arbitrary data -- length delimited, but still has a comma after it!
                    d = int(chr(c)) #number of digits in length
                    i += 1 #pop d
                    n = int(packet[i:i+d]) #length
                    i += d #pop n
                    data = bytes(packet[i:i+n])
                    if len(data) != n:
                        raise SCPIException(f'ERROR: end of packet while parsing arbitrary data. Expected {n} bytes, got {len(data)}.')
                    i += n #pop data (leave the comma)
                    responses.append(data)
                    continue
                else:
                    raise SCPIException(f'ERROR: Unexpected character: {c}')
            elif c == ord('"'): #string
                i += 1 #pop c
                j = packet.find(b'"',i)
                if j == -1: #no closing quote
                    raise SCPIException('ERROR: Unterminated string')
                s = str(packet[i:j],'utf-8')
                i = j+1 #pop string & quote (leave the comma)
                responses.append(s)
                continue
            else:
                #decimal integer, float, or naked string response
                #parse to comma
                j = packet.find(b',',i)
                if j == -1: #no trailing comma -- parse to end
                    j = len(packet)
                try:
                    x = int(packet[i:j])
                except ValueError:
                    #not an int ... try float
                    try:
                        x = float(packet[i:j])
                    except ValueError:
                        #not a float, try string
                        x = str(packet[i:j],'utf-8')
                i = j #pop number (leave the comma)
                responses.append(x)
        return responses
    
    def handle_packet(self, packet: bytes):
        response = self._parse_scpi(packet)
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
    def mode(mc):
        modes = {}
        modes['dsprpt'] = bool(mc & TLC5955.DSPRPT)
        modes['tmgrst'] = bool(mc & TLC5955.TMGRST)
        modes['rfresh'] = bool(mc & TLC5955.RFRESH)
        modes['espwm'] = bool(mc & TLC5955.ESPWM)
        modes['lsdvlt'] = bool(mc & TLC5955.LSDVLT)
        return modes
    
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
    def maxcurrent_mA(Imax_code):
        """return the current in mA for a given maxcurrent code"""
        Imcs = [3.2,8,11.2,15.9,19.1,23.9,27.1,31.9]
        return Imcs[Imax_code]
    
    @staticmethod
    def brightness_code(brightness):
        """brightness within 0.1 to 1"""
        return np.clip(np.floor((brightness-0.1)*np.nextafter(128,0)/0.9),0,127).astype(np.uint8)
    
    @staticmethod
    def brightness(brightness_code):
        """return brightness coefficient from a given brightness code"""
        return np.clip(0.1 + 0.9*brightness_code/127, 0.1, 1.0)
    
    @staticmethod
    def dotcorrect_code(dc_img):
        """dot correct within 0.262 to 1."""
        dc_img = np.asarray(dc_img)
        dc_img[np.isnan(dc_img)] = 1.0 #dead pixels have a dc of nan
        return np.clip(np.floor((dc_img - 0.262)*np.nextafter(128,0)/0.738),0,127).astype(np.uint8)
    
    @staticmethod
    def dotcorrect_img(dc_code):
        """dot correct coefficient given a code."""
        dc_code = np.asarray(dc_code)
        return np.clip(0.262 + 0.738*dc_code/127,0.262,1.0)
    
    @staticmethod
    def pwm_code(img):
        """pwm values from 0.0 to 1.0"""
        return np.clip(np.floor(np.nextafter(65536,0)*img),0,65535).astype(np.uint16)
    
    @staticmethod
    def pwm_img(pwm_code):
        """pwm ratio from a given code"""
        return np.clip(pwm_code/65535,0.0,1.0)
    