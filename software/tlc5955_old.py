from math import ceil

class tlc5955:

    #mode bits
    _DSPRPT = 1
    _TMGRST = 2
    _RFRESH = 4
    _ESPWM = 8
    _LSDVLT = 16

    def __init__(self,index=0):
        self.index = index
        self.pixel_addr = index*48
        self.config_addr = index*24
        self.mode = 0
        self.pixel_order = list(range(16))
        self.pixels = [0]*48
        self.dot_correct = [0]*48
        self.max_current = [0]*3
        self.brightness = [0]*3
    
    @staticmethod
    def maxcurrent_to_code(Imax_mA):
        """picks the largest allowed current less than or equal to the given current"""
        Imcs = [3.2,8,11.2,15.9,19.1,23.9,27.1,31.9]
        for i,Imc in enumerate(Imcs):
            if Imc > Imax_mA:
                break
        if i > 0: return i-1
        else: return 0
    
    @staticmethod
    def brightness_to_code(brightness):
        """brightness within 0.1 to 1"""
        return min(max(round((brightness-0.1)*(127/0.9)),0),127)
    
    @staticmethod
    def dotcorrect_to_code(dot_correct):
        """dot correct within 0.262 to 1"""
        return min(max(round((dot_correct-0.262)*(127/0.738)),0),127)
    
    @staticmethod
    def codes_to_values(mc, bc, dc):
        Imcs = [3.2, 8, 11.2, 15.9, 19.1, 23.9, 27.1, 31.9]
        if bc < 0 or bc > 127:
            raise RuntimeError("bc out of range")
        if dc < 0 or dc > 127:
            raise RuntimeError("dc out of range")
        return (Imcs[mc], (0.1 + 0.9*bc/127), (0.262 + 0.738*dc/127))

    @staticmethod
    def codes_to_current(mc,bc,dc):
        Imc,b,d = codes_to_values(mc,bc,dc)
        return Imc*b*d

    @staticmethod
    def current_to_codes(Iout_mA, mc=None, bc=None, dc=None):
        """selects mc, bc, and dc to approximately match the given current
        Note that bc cannot be used to pull the current below 1 mA, so there
        are some combinations of mc, bc, dc that are not valid. This routine
        greedily selects mc, followed by bc, followed by dc, so expect some
        error.
        """
        Imcs = [3.2,8,11.2,15.9,19.1,23.9,27.1,31.9]
        if mc is None:
            xbc, xdc = 1.0, 1.0
            if bc is not None: xbc = (0.1 + 0.9*bc/127)
            if dc is not None: xdc = (0.262 + 0.738*dc/127)
            for mc, Imc in enumerate(Imcs):
                if Imc*xbc*xdc >= Iout_mA and Imc*xbc >= 1.0: break
        else:
            Imc = Imcs[mc]
        if bc is None:
            #we can't use BC to take the current below 1 mA
            x = max(Iout_mA,1.0)/Imc 
            if dc is not None:
                x /= (0.262 + 0.738*dc/127)
            bc = min(max(ceil((x-0.1)*127/0.9),0),127)
        Ibc = Imc*(0.1 + 0.9*bc/127)
        if dc is None:
            x = Iout_mA/Ibc
            dc = min(max(round((x-0.262)*127/0.738),0),127)
        return (mc,bc,dc)

    @staticmethod
    def pixel_to_code(pixel):
        """pixel within 0 to 1"""
        if pixel < 0: return 0
        elif pixel > 1: return 0xffff
        else: return int(pixel*0xffff)

    def set_mode(self, dsprpt=None, tmgrst=None, rfresh=None, espwm=None, lsdvlt=None):
        set_mask  = tlc5955._DSPRPT * (dsprpt is not None)
        set_mask |= tlc5955._TMGRST * (tmgrst is not None)
        set_mask |= tlc5955._RFRESH * (rfresh is not None)
        set_mask |= tlc5955._ESPWM  * (espwm  is not None)
        set_mask |= tlc5955._LSDVLT * (lsdvlt is not None)

        set_value  = tlc5955._DSPRPT * bool(dsprpt)
        set_value |= tlc5955._TMGRST * bool(tmgrst)
        set_value |= tlc5955._RFRESH * bool(rfresh)
        set_value |= tlc5955._ESPWM  * bool(espwm)
        set_value |= tlc5955._LSDVLT * bool(lsdvlt)

        self.mode = ((set_mask & set_value) | (~set_mask & self.mode)) & 0x1F

    def reorder_index(self, i):
        return 3*self.pixel_order[i//3] + (i%3)

    def pixel_bytes(self, i=None):
        #rearrange pixels and pack them into a bytearray buffer
        buf = bytearray(2*48)
        for i, p in enumerate(self.pixels):
            i = self.reorder_index(i)
            p = tlc5955.pixel_to_code(p)
            tlc5955.pack_bits(buf, 16*i, 16, p)
        return buf

    def config_bytes(self):
        #bit-stuff the values into a list of ints
        #then use struct to convert into a bytes object
        buf = bytearray(2*24)
        for i, dc in enumerate(self.dot_correct):
            i = self.reorder_index(i)
            dc = tlc5955.dotcorrect_to_code(dc)
            tlc5955.pack_bits(buf, 7*i, 7, dc)
        
        for i, b in enumerate(self.brightness):
            b = tlc5955.brightness_to_code(b)
            tlc5955.pack_bits(buf, 345 + 7*i, 7, b)
        
        for i, mi in enumerate(self.max_current):
            mi = tlc5955.maxcurrent_to_code(mi)
            tlc5955.pack_bits(buf, 336 + 3*i, 3, mi)
        
        tlc5955.pack_bits(buf, 366, 5, self.mode)

        return buf
    
    @staticmethod
    def pack_bits(buffer, offset, nbits, value):
        """pack nbits of value into buffer at offset.
        offset is in bits"""
        #buffer index
        idx = offset // 8
        dst_bit = offset - 8*idx
        #read the byte that's already in the buffer
        dst_byte = buffer[idx]
        while nbits > 0:
            if dst_bit == 8:
                #write back to the buffer
                buffer[idx] = dst_byte
                #advance to the next byte
                idx += 1
                dst_byte = buffer[idx]
                dst_bit = 0
            #how many bits can we write?
            nb = min(8-dst_bit, nbits)
            #which bits do we take from value?
            value_mask = (1 << nb) - 1
            #which bits do we keep from dst_byte
            keep_mask = 0xFF ^ (value_mask << dst_bit)
            #write the bits
            dst_byte = (dst_byte & keep_mask) | (
                (value & value_mask) << dst_bit)
            #shift the bits we took out of value
            value >>= nb
            #advance the counters
            nbits -= nb
            dst_bit += nb
        #write back the last byte we worked on
        buffer[idx] = dst_byte

def to_hex(buf, wordsize, sep=' '):
    """return bytes as a string in wordsize hex chunks, separated by sep"""
    fmt = '{{:0{}X}}'.format(2*wordsize)
    s = ''
    for i in range(0,len(buf),wordsize):
        word = int.from_bytes(buf[i:i+wordsize],'little')
        if i == 0: s += fmt.format(word)
        else: s += sep + fmt.format(word)
    return s


if __name__ == "__main__":
    rgb = tlc5955()
    uv = tlc5955()

    rgb.pixel_order = [8, 12, 9, 13, 14, 10, 15, 11, 7, 3, 6, 2, 1, 5, 0, 4]
    uv.pixel_order = [4, 0, 5, 1, 2, 6, 3, 7, 11, 15, 10, 14, 13, 9, 12, 8]

    rgb.set_mode(dsprpt=True, espwm=True)
    uv.set_mode(dsprpt=True, espwm=True)

    rgb.max_current = [11.2, 11.2, 8] #[R,G,B] mA
    uv.max_current = [0.0, 8.0, 11.2] #[x,V,UV] mA

    rgb.brightness = [0.804,0.893,0.5]
    uv.brightness = [0.0, 1.0, 0.804]

    rgb.dot_correct = [1.0]*48
    uv.dot_correct =  [1.0]*48

    rgb.pixels = [1.0, 0.0, 0.0]*16
    uv.pixels = [0.0, 0.0, 0.0]*16

    rgb_pix = to_hex(rgb.pixel_bytes(),2)
    uv_pix = to_hex(uv.pixel_bytes(),2)
    rgb_cfg = to_hex(rgb.config_bytes(),2)
    uv_cfg = to_hex(uv.config_bytes(),2)
    
    
    print('//RGB Pixels')
    print(rgb_pix)
    print('//UV Pixels')
    print(uv_pix)

    print('//RGB Config')
    print(rgb_cfg)
    print('//UV Config')
    print(uv_cfg)

    cmd_str = 'G1;G2654613;'
    cmd_str += ' '.join(('Wp00',rgb_pix,uv_pix,rgb_pix,uv_pix))+';'
    cmd_str += ' '.join(('Wc00',rgb_cfg,uv_cfg,rgb_cfg,uv_cfg))+';'
    cmd_str += 'G0CCPDG1'
    
    print('// Command string')
    print('//',cmd_str)
    print('//',len(cmd_str),'bytes')
    print(to_hex(bytes(cmd_str,'ascii'),1))
