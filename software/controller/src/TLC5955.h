/* TLC5955.h

Copyright 2020 Samuel B. Powell
samuel.powell@uq.edu.au

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include <cinttypes>
#include <algorithm>
#include <core_pins.h>

/*
TLC5955 LED driver configuration and communication.
This struct keeps a reference to the SPI device and pins being used to communicate
with the LED driver, but does not keep the buffers for storing any data.
*/
struct TLC5955
{
    //Table of max current values in Q5.11 format
    static constexpr uint32_t MC_VALUE[] = {
        6554, 16384, 22938, 32563, 39117, 48947, 55501, 65331};
    //Table of brightness coefficient values in Q1.16 format (max 7.0e-6 error).
    //  BC_VALUE[i] = round(65536*(i*0.9/127 + 0.1))
    static constexpr uint32_t BC_VALUE[] = {
        6554, 7018, 7482, 7947, 8411, 8876, 9340, 9805, 10269,
        10733, 11198, 11662, 12127, 12591, 13056, 13520, 13984, 14449,
        14913, 15378, 15842, 16307, 16771, 17235, 17700, 18164, 18629,
        19093, 19558, 20022, 20486, 20951, 21415, 21880, 22344, 22809,
        23273, 23737, 24202, 24666, 25131, 25595, 26060, 26524, 26988,
        27453, 27917, 28382, 28846, 29311, 29775, 30239, 30704, 31168,
        31633, 32097, 32562, 33026, 33490, 33955, 34419, 34884, 35348,
        35813, 36277, 36741, 37206, 37670, 38135, 38599, 39064, 39528,
        39992, 40457, 40921, 41386, 41850, 42315, 42779, 43243, 43708,
        44172, 44637, 45101, 45566, 46030, 46494, 46959, 47423, 47888,
        48352, 48817, 49281, 49745, 50210, 50674, 51139, 51603, 52068,
        52532, 52996, 53461, 53925, 54390, 54854, 55319, 55783, 56247,
        56712, 57176, 57641, 58105, 58570, 59034, 59498, 59963, 60427,
        60892, 61356, 61821, 62285, 62749, 63214, 63678, 64143, 64607,
        65072, 65536};
    //Table of dotcorrect coefficient values in Q1.16 format (max 7.6e-6 error)
    //  DC_VALUE[i] = round(65536*(i*0.738/127 + 0.262))
    static constexpr uint32_t DC_VALUE[] = {
        17170, 17551, 17932, 18313, 18694, 19075, 19455, 19836, 20217,
        20598, 20979, 21360, 21740, 22121, 22502, 22883, 23264, 23645,
        24025, 24406, 24787, 25168, 25549, 25930, 26310, 26691, 27072,
        27453, 27834, 28215, 28595, 28976, 29357, 29738, 30119, 30500,
        30880, 31261, 31642, 32023, 32404, 32785, 33165, 33546, 33927,
        34308, 34689, 35070, 35450, 35831, 36212, 36593, 36974, 37354,
        37735, 38116, 38497, 38878, 39259, 39639, 40020, 40401, 40782,
        41163, 41544, 41924, 42305, 42686, 43067, 43448, 43829, 44209,
        44590, 44971, 45352, 45733, 46114, 46494, 46875, 47256, 47637,
        48018, 48399, 48779, 49160, 49541, 49922, 50303, 50684, 51064,
        51445, 51826, 52207, 52588, 52969, 53349, 53730, 54111, 54492,
        54873, 55254, 55634, 56015, 56396, 56777, 57158, 57539, 57919,
        58300, 58681, 59062, 59443, 59824, 60204, 60585, 60966, 61347,
        61728, 62109, 62489, 62870, 63251, 63632, 64013, 64394, 64774,
        65155, 65536};
    static constexpr size_t PWM_BUFFER_SIZE = 96;
    static constexpr size_t CTRL_BUFFER_SIZE = 48;
    static constexpr size_t NUM_LEDS = 48;

    static constexpr size_t DC_BITS = 7; //Dot Correct word size
    //Dot Correct offset (bits) -- handles multiple chips
    static constexpr size_t DC_OFFSET(size_t pixel)
    {
        return 8 * CTRL_BUFFER_SIZE * (pixel / NUM_LEDS) + DC_BITS * (pixel % NUM_LEDS);
    }

    static constexpr size_t BC_BITS = 7; //Brightness Control word size
    //Brightness control offset (bits)
    static constexpr size_t BC_OFFSET(size_t channel)
    {
        return BC_BITS * channel + 345;
    }

    static constexpr size_t MC_BITS = 3; //Max Current word size
    //Max Current offset (bits)
    static constexpr size_t MC_OFFSET(size_t channel)
    {
        return MC_BITS * channel + 336;
    }
    static constexpr size_t FC_BITS = 5;     //Function Control word size
    static constexpr size_t FC_OFFSET = 366; //Function Control offset (bits)

    enum mode_t : uint8_t
    {
        DSPRPT = 0x1, //display repeat
        TMGRST = 0x2, //timing reset
        RFRESH = 0x4, //auto data refresh
        ESPWM = 0x8,  //enhanced spectrum PWM
        LSDVLT = 0x10 //LED short detect voltage
    };

    KINETISK_SPI_t &spi;
    uint8_t sclk, mosi, miso, latch;

    uint32_t SPI_BR_FLAGS = 0;

    TLC5955(KINETISK_SPI_t &spi);

    void set_pins(uint8_t sclk, uint8_t mosi, uint8_t miso, uint8_t latch);
    uint32_t set_baudrate(uint32_t rate);
    uint32_t get_baudrate();
    void set_br_flags(uint32_t flags);
    uint32_t get_br_flags();

    /** transfers pwm codes to a daisy chain of n TLC5955 chips
     * size_t n: number of chips, must be at least 1
     * const uint8_t *out: buffer of n*96 bytes that will be sent to the chips
     *                     if out == nullptr, then all zeros will be sent.
     * uint8_t *in: buffer of n*96 bytes to store the chips' responses
     */
    void transfer_pwm(size_t n, const uint8_t *out, uint8_t *in);

    /** transfers control codes to a daisy chain of n TLC5955 chips
     * size_t n: number of chips, must be at least 1
     * const uint8_t *out: buffer of n*48 bytes that will be sent to the chips
     * uint8_t *in: buffer of n*96 bytes to store the chips' responses
     */
    void transfer_control(size_t n, const uint8_t *out, uint8_t *in);

    //access control buffer
    //dot correction -- 7-bit words per pixel starting at bit 0 (bytes 0-41)
    static void set_dot_correct(uint8_t *buffer, size_t pixel, uint8_t code);
    static uint8_t get_dot_correct(const uint8_t *buffer, size_t pixel);

    //max current -- 3-bit words per channel starting at bit 336 (bytes 42-43)
    static void set_max_current(uint8_t *buffer, uint8_t channel, uint8_t code);
    static uint8_t get_max_current(const uint8_t *buffer, uint8_t channel);

    //brightness -- 7-bit words per channel starting at bit 345 (bytes 43-45)
    static void set_brightness(uint8_t *buffer, uint8_t channel, uint8_t code);
    static uint8_t get_brightness(const uint8_t *buffer, uint8_t channel);

    //mode bits -- 5 bits starting at bit 366 (bytes 45-46)
    static void set_mode(uint8_t *buffer, uint8_t code);
    static uint8_t get_mode(const uint8_t *buffer);

    //write the magic byte (0x96) to byte 47
    static void set_magic(uint8_t *buffer);

    //pwm buffer
    //16-bit words per pixel, starting at 0
    static void set_pwm(uint8_t *buffer, size_t pixel, uint16_t value);
    static uint16_t get_pwm(const uint8_t *buffer, size_t pixel);

    //Estimate the current consumption for the given chip in mA, in Q14.18 format
    static uint32_t get_current(const uint8_t *ctrl_buffer, const uint8_t *pwm_buffer);

    /** Copy from one buffer to another at arbitrary bit offsets
     * 
     * size_t n_bits : number of bits to copy
     * const uint8_t *src : pointer to source bytes
     * size_t src_bit : *bit* offset into src for reading
     * uint8_t *dst : pointer to destination bytes
     * size_t dst_bit : *bit* offset into dst for writing
     */
        static void copy_bits(size_t n_bits, const uint8_t *src, size_t src_bit, uint8_t *dst, size_t dst_bit);

protected:
    size_t transfer(bool ctrl, const uint8_t *out, uint8_t *in);
    void toggle_latch();

    //initialize and shut downt the SPI unit
    void spi_init();
    void spi_stop();
};
