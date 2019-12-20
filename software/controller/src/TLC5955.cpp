#include "TLC5955.h"
#include <Arduino.h>

TLC5955::TLC5955(KINETISK_SPI_t &spi) : spi(spi), sclk(0), mosi(0), miso(0), latch(0)
{
}

void TLC5955::set_pins(uint8_t sclk, uint8_t mosi, uint8_t miso, uint8_t latch)
{
    this->sclk = sclk;
    this->mosi = mosi;
    this->miso = miso;
    this->latch = latch;

    //configure pin mux to attach pins to SPI0
    *portConfigRegister(sclk) = PORT_PCR_MUX(2);
    *portConfigRegister(miso) = PORT_PCR_MUX(2);
    *portConfigRegister(mosi) = PORT_PCR_MUX(2);
    //latch is GPIO output, high drive strength
    pinMode(latch, OUTPUT);
    digitalWrite(latch, 0);
}

void TLC5955::set_magic(uint8_t *buffer)
{
    *(buffer + 47) = 0x96;
}

void TLC5955::set_mode(uint8_t *buffer, uint8_t code)
{
    copy_bits(FC_BITS, &code, 0, buffer, FC_OFFSET);
}

uint8_t TLC5955::get_mode(const uint8_t *buffer)
{
    uint8_t code = 0;
    copy_bits(FC_BITS, buffer, FC_OFFSET, &code, 0);
    return code;
}

void TLC5955::set_max_current(uint8_t *buffer, uint8_t channel, uint8_t code)
{
    copy_bits(MC_BITS, &code, 0, buffer, MC_OFFSET(channel));
}

uint8_t TLC5955::get_max_current(const uint8_t *buffer, uint8_t channel)
{
    uint8_t code = 0;
    copy_bits(MC_BITS, buffer, MC_OFFSET(channel), &code, 0);
    return code;
}

void TLC5955::set_brightness(uint8_t *buffer, uint8_t channel, uint8_t code)
{
    copy_bits(BC_BITS, &code, 0, buffer, BC_OFFSET(channel));
}

uint8_t TLC5955::get_brightness(const uint8_t *buffer, uint8_t channel)
{
    uint8_t code = 0;
    copy_bits(BC_BITS, buffer, BC_OFFSET(channel), &code, 0);
    return code;
}

void TLC5955::set_dot_correct(uint8_t *buffer, size_t pixel, uint8_t code)
{
    copy_bits(DC_BITS, &code, 0, buffer, DC_OFFSET(pixel));
}

uint8_t TLC5955::get_dot_correct(const uint8_t *buffer, size_t pixel)
{
    uint8_t code = 0;
    copy_bits(DC_BITS, buffer, DC_OFFSET(pixel), &code, 0);
    return code;
}

void TLC5955::set_pwm(uint8_t *buffer, size_t pixel, uint16_t value)
{
    uint8_t *b = buffer + 2*pixel;
    *(b+1) = uint8_t((value >> 8) & 0xff); //big endian
    *(b) = uint8_t(value & 0xff);
}

uint16_t TLC5955::get_pwm(uint8_t *buffer, size_t pixel)
{
    uint8_t *b = buffer + 2 * pixel;
    return (uint16_t(*(b+1)) << 8) | uint16_t(*(b)); //big endian
}

/* Communication code */
void TLC5955::transfer_pwm(size_t n, const uint8_t *out, uint8_t *in)
{
    size_t count;
    spi_init();
    for (size_t i = n; i > 0; --i)
    {
        const uint8_t *o = (out == nullptr ? out : out + 96 * (i - 1));
        uint8_t *n = (in == nullptr ? in : in + 96 * (i - 1));
        count += transfer(false, o, n);
    }

    spi_stop();
    toggle_latch();
    //Serial.printf("PWM: Send %d bytes",count);
}

void TLC5955::transfer_control(size_t n, const uint8_t *out, uint8_t *in)
{
    spi_init();
    size_t count;
    for (size_t i = n; i > 0; --i)
    {
        const uint8_t *o = (out == nullptr ? out : out + 48 * (i - 1));
        uint8_t *n = (in == nullptr ? in : in + 96 * (i - 1));
        count += transfer(true, o, n);
    }
    spi_stop();
    toggle_latch();
    //Serial.printf("CTRL: Send %d bytes", count);
}

size_t TLC5955::transfer(bool ctrl, const uint8_t *out, uint8_t *in)
{
    //this function implements the somewhat peculiar TLC5955 communication protocol

    //each transfer is 96 bytes plus 1 extra flag bit (set by ctrl)
    //the flag is transmitted first, then the bytes MSb first

    //the PWM data buffer is 96 bytes, control data is 48 bytes
    //the input buffer is always 96 bytes if not null

    // when transmitting PWM data, all bytes are transferred in reverse order

    // when transmitting the control data, the first (magic) byte is transferred
    //  with the flag bit, then 48 0s are transmitted to fill the space and and
    //  finally the control data is transmitted in reverse order

    //how many padding bytes do we need?
    size_t pad = (out ? (ctrl ? 48 : 0) : 95); //only 95 in the null case bcs of the special case for the first word
    uint32_t ctrl_flag = (ctrl ? 1 : 0) << 8;
    uint32_t dummy;
    size_t count;
    //reverse the pointers so that we write in reverse
    const uint8_t *out_last = out;
    if (out) out += (ctrl ? 47 : 95); //48-1, 96-1

    const uint8_t *in_last = in;
    if (in) in += 95;
    
    //write the first 9-bit frame with the flag bit
    // SPI_PUSHR_CONT = keep CS0 high after this word
    // SPI_PUSHR_CTAS(1) = use CTAR1 settings (9 bit words)
    uint32_t w = SPI_PUSHR_CONT | SPI_PUSHR_CTAS(1);
    w |= ctrl_flag | (out ? *out-- : 0);
    spi.PUSHR = w;

    //write padding bytes
    for (size_t i = 0; i < pad;)
    {
        uint32_t sr = spi.SR; //read status register
        if ((sr & 0xf000) < 0x3000)
        { //there's space in the TX FIFO
            ++i; //only increment i when we've pushed a byte
            if(out == nullptr && i == pad)
                spi.PUSHR = SPI_PUSHR_EOQ;
            else spi.PUSHR = SPI_PUSHR_CONT;
            
        }
        if (sr & 0xf0)
        { //there's bytes to read in the RX FIFO
            if (in)
                *in-- = uint8_t(spi.POPR & 0xff); //&0xff to chop off the flag bit
            else
                dummy = spi.POPR;
        }
    }

    //write the buffer
    while (out && out >= out_last)
    {
        uint32_t sr = spi.SR; //read status register
        
        if ((sr & 0xf000) < 0x3000) //SPI_SR_TXCTR
        { //there's space in the TX FIFO
            if(out == out_last) 
                spi.PUSHR = SPI_PUSHR_EOQ | *out--; //mark end of queue
            else 
                spi.PUSHR = SPI_PUSHR_CONT | *out--;
            count++;
        }
        if ((sr & 0xf0) > 0) //RXCTR
        { //there's bytes to read in the RX FIFO
            if (in)
                *in-- = uint8_t(spi.POPR & 0xff); //&0xff to chop off the flag bit
            else
                dummy = spi.POPR;
        }
    }
    
    //read any remaining bytes
    while (in && in >= in_last)
    {
        if (spi.SR & 0xf0)
        {
            *in-- = uint8_t(spi.POPR & 0xff);
        }
    }
    //wait for the EOQ flag to be asserted
    while((spi.SR & SPI_SR_EOQF) == 0) delayMicroseconds(10);
    spi.SR = SPI_SR_EOQF; //clear the flag
    return count;
}

void TLC5955::toggle_latch()
{
    noInterrupts();
    delayMicroseconds(1); //minimum 5 ns
    digitalWrite(this->latch, 1);
    delayMicroseconds(1); //minimum 30 ns
    digitalWrite(this->latch, 0);
    delayMicroseconds(1); //minimum 40 ns
    interrupts();
}

uint32_t spi_baudrate(uint8_t PBR, uint8_t DBR, uint32_t BR)
{
    static uint32_t PBR_lut[4] = {2, 3, 5, 7};
    return (F_CPU * uint32_t(1 + DBR)) / (PBR_lut[PBR] * (2 << BR));
}

uint32_t TLC5955::set_baudrate(uint32_t rate)
{
    //2 + {0,1,3,5}
    //find PBR, DBR, and BR that get closest to rate
    //rate = (F_CPU / PBR) * (1+DBR)/ (2**(BR+1))
    uint8_t best_PBR = 0, best_DBR = 1, best_BR = 0;
    uint32_t best_rate = spi_baudrate(best_PBR, best_DBR, best_BR);
    uint32_t best_error = best_rate > rate ? best_rate - rate : rate - best_rate;
    //Serial.printf("Target baudrate %d\n",rate);
    for (uint8_t DBR = 0; DBR < 2; ++DBR)
    {
        for (uint8_t PBR = 0; PBR < 4; ++PBR)
        {
            uint32_t base = spi_baudrate(PBR, 1 - DBR, 0);

            //might underestimate BR bcs integer division
            uint32_t ratio = base / rate;
            uint32_t BR = ratio > 0 ? 31 - __builtin_clz(ratio) : 15;
            //Serial.printf("DBR %d, PBR %d : base = %d\n, ratio = %d\n", 1-DBR, PBR, base, ratio);

            for (uint32_t BRx = 0; BRx < 2 && BR + BRx < 16; ++BRx)
            {
                uint32_t guess = spi_baudrate(PBR, 1 - DBR, BR + BRx);
                uint32_t error = guess > rate ? guess - rate : rate - guess;
                //Serial.printf("  BR %d : guess = %d, error = %d\n",BR+BRx,guess,error);
                if (error <= best_error)
                {
                    //Serial.println("Accepted");
                    best_error = error;
                    best_rate = guess;
                    best_DBR = 1 - DBR;
                    best_PBR = PBR;
                    best_BR = BR + BRx;
                }
            }
        }
    }

    SPI_BR_FLAGS = SPI_CTAR_PBR(best_PBR) | (SPI_CTAR_DBR * best_DBR) | SPI_CTAR_BR(best_BR);
    return best_rate;
}

void TLC5955::spi_init()
{
    //enable clock to SPI0
    SIM_SCGC6 |= SIM_SCGC6_SPI0;
    //use module configuration register (MCR) to
    // stop any transfers and disable
    spi.MCR = SPI_MCR_MDIS | SPI_MCR_HALT;
    //set up clock & transfer attributes (CTARx)
    //this register sets the frame size, clock and timing
    //except for the frame size, the defaults are all good
    //Baud rate = (F_CPU / PBR) * (1+DBR) / BR
    // SPI_CTAR_BR(N) -> BR = 2**(N+1)
    // SPI_CTAR_PBR(N) -> PBR = {2, 3, 5, 7}[N]
    // e.g. spi.CTAR0 = SPI_CTAR_BR(1) gives a 12 MHz clock
    //CTAR0: 8-bit frame, 12 MHz clock
    spi.CTAR0 = SPI_CTAR_FMSZ(7) | SPI_BR_FLAGS;
    //CTAR1: 9-bit frame, 12 MHz clock
    spi.CTAR1 = SPI_CTAR_FMSZ(8) | SPI_BR_FLAGS;
    //enable, master mode, clear queues
    spi.MCR = SPI_MCR_MSTR | SPI_MCR_CLR_RXF | SPI_MCR_CLR_TXF;
}

void TLC5955::spi_stop()
{
    //stop any transfers and disable
    spi.MCR = SPI_MCR_MDIS | SPI_MCR_HALT;
    //disable clock to SPI0
    SIM_SCGC6 &= ~SIM_SCGC6_SPI0;
}

/** Copy from one buffer to another at arbitrary bit offsets
 * 
 * size_t n_bits : number of bits to copy
 * const uint8_t *src : pointer to source bytes
 * size_t src_bit : *bit* offset into src for reading
 * uint8_t *dst : pointer to destination bytes
 * size_t dst_bit : *bit* offset into dst for writing
 */
void TLC5955::copy_bits(size_t n_bits, const uint8_t *src, size_t src_bit, uint8_t *dst, size_t dst_bit)
{
    //start and stop byte indices in the source
    size_t src_index = src_bit / 8;
    //size_t src_stop = (src_bit + n_bits - 1) / 8 + 1;
    //translate offset so that it's relative to the byte
    src_bit -= 8 * src_index;

    //start and stop bytes in the destination
    size_t dst_index = dst_bit / 8;
    //size_t dst_stop = (dst_bit + n_bits - 1) / 8 + 1;
    //translate offset so that it's relative to the byte
    dst_bit -= 8 * dst_index;

    //read the first src and dst bytes
    uint8_t src_byte = src[src_index];
    uint8_t dst_byte = dst[dst_index];
    //shift src_byte by the offset so that the bits we want are at 0
    src_byte >>= src_bit;

    //loop until there's nothing left to write
    while (n_bits > 0)
    {
        // when we hit an offset of 8 we need to advance to the next byte
        if (src_bit == 8)
        {
            src_byte = src[++src_index];
            src_bit = 0;
        }
        if (dst_bit == 8)
        {
            //before we advance the destination byte, we need to write the previous one back
            dst[dst_index] = dst_byte;
            dst_byte = dst[++dst_index];
            dst_bit = 0;
        }
        //how many bits can we read or write with the current offsets?
        size_t nb = std::min(std::min(8 - src_bit, 8 - dst_bit), n_bits);
        //which bits are we taking from src_byte?
        uint8_t src_mask = (1 << nb) - 1;
        //which bits are we keeping (not writing) in dst_byte?
        uint8_t keep_mask = 0xff ^ (src_mask << dst_bit);
        //write the bits
        dst_byte = (dst_byte & keep_mask) | ((src_byte & src_mask) << dst_bit);
        //shift the src_byte right to keep bits we want are at 0
        src_byte >>= nb;
        //advance counters
        n_bits -= nb;
        src_bit += nb;
        dst_bit += nb;
    }
    //write back the last byte we worked on
    dst[dst_index] = dst_byte;
}
