#include "TLC5955.h"
#include <Arduino.h>

TLC5955::TLC5955(KINETISK_SPI_t &spi) : spi(spi), sclk(0), mosi(0), miso(0), latch(0)
{}

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
    *(uint16_t *)(buffer + 2 * pixel) = value;
}

uint16_t TLC5955::get_pwm(uint8_t *buffer, size_t pixel)
{
    return *(uint16_t *)(buffer + 2 * pixel);
}

/* Communication code */
void TLC5955::transfer_pwm(size_t n, const uint8_t *out, uint8_t *in)
{
    spi_init();
    for(size_t i = n; i > 0; --i) {
        const uint8_t *o = (out == nullptr ? out : out + 96*(i-1));
        uint8_t *n = (in == nullptr ? in : in + 96*(i-1));
        transfer(false, o, n);
    }
    
    spi_stop();
    toggle_latch();
}

void TLC5955::transfer_control(size_t n, const uint8_t *out, uint8_t *in)
{
    spi_init();
    for(size_t i = n; i > 0; --i) {
        const uint8_t *o = (out == nullptr ? out : out + 48 * (i - 1));
        uint8_t *n = (in == nullptr ? in : in + 96 * (i - 1));
        transfer(true, o, n);
    }
    spi_stop();
    toggle_latch();
}

void TLC5955::transfer(bool ctrl, const uint8_t *out, uint8_t *in) 
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

    //reverse the pointers so that we write in reverse
    const uint8_t *out_end;
    if(out) {
        out_end = out-1;
        out += (ctrl ? 47 : 95); //48-1, 96-1
    } else {
        out_end = nullptr;
    }
    
    const uint8_t *in_end;
    if(in) {
        in_end = in-1;
        in += 95;
    }  else {
        in_end = nullptr;
    }

    //write the first 9-bit frame with the flag bit
    // SPI_PUSHR_CONT = keep CS0 high after this word
    // SPI_PUSHR_CTAS(1) = use CTAR1 settings (9 bit words)
    uint32_t w = SPI_PUSHR_CONT | SPI_PUSHR_CTAS(1);
    w |= ctrl_flag | (out ? *out-- : 0);
    spi.PUSHR = w;

    //write padding bytes
    for(size_t i = 0; i < pad;) {
        uint32_t sr = spi.SR;        //read status register
        if((sr & 0xf000) < 0x3000) { //there's space in the TX FIFO
            spi.PUSHR = SPI_PUSHR_CONT; 
            ++i; //only increment i when we've pushed a byte
        }
        if(sr & 0xf0) { //there's bytes to read in the RX FIFO
            if(in) *in-- = uint8_t(spi.POPR & 0xff); //&0xff to chop off the flag bit
            else dummy = spi.POPR;
        }
    }
    
    //write the buffer
    while (out != out_end) {
        uint32_t sr = spi.SR;        //read status register
        if ((sr & 0xf000) < 0x3000) { //there's space in the TX FIFO
            spi.PUSHR = SPI_PUSHR_CONT | *out--;
        }
        if (sr & 0xf0) { //there's bytes to read in the RX FIFO
            if (in) *in-- = uint8_t(spi.POPR & 0xff); //&0xff to chop off the flag bit
            else dummy = spi.POPR;
        }
    }

    //read any remaining bytes
    while (in != in_end) {
        if (spi.SR & 0xf0) {
            *in-- = uint8_t(spi.POPR & 0xff);
        }
    }
}

void TLC5955::toggle_latch()
{
    noInterrupts();
    delayMicroseconds(1); //minimum 5 ns
    digitalWrite(this->latch,1);
    delayMicroseconds(1); //minimum 30 ns
    digitalWrite(this->latch,0);
    delayMicroseconds(1); //minimum 40 ns
    interrupts();
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
    //CTAR0: 8-bit frame, 24 MHz clock
    spi.CTAR0 = SPI_CTAR_FMSZ(7) | SPI_CTAR_BR(1);
    //CTAR1: 9-bit frame, 24 MHz clock
    spi.CTAR1 = SPI_CTAR_FMSZ(8) | SPI_CTAR_BR(1);
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
