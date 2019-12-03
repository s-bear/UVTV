#include <cinttypes>
#include <algorithm>
#include <core_pins.h>

struct TLC5955
{
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
    static uint16_t get_pwm(uint8_t *buffer, size_t pixel);

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
