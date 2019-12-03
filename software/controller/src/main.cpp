#include "Arduino.h"
#include "TLC5955.h"
#include "scpi.h"

#include <array>

//use Serial for USB, Serial1 for UART
#define SER Serial

#define SYSTEM_HELP                                                                    \
  "UVTV System Help\r\n"                                                               \
  "  This system uses the SCPI standard for communication and control.\r\n"            \
  "  Send any of the following commands followed by ENTER to execute them.\r\n"        \
  "  Commands are not case-sensitive, but have short and long forms. The short \r\n"   \
  "  form is indicated by capitals. [] indicate optional parts.\r\n"                   \
  "  E.g. STATus:ERRor[:NEXT]?  can be executed by entering any of the following:\r\n" \
  "    \"STAT:err?\" or \"status:error?\" or \"STATus:error:next?\" etc.\r\n"          \
  "  N.B. Many of the mandated commands are not implemented on this system.\r\n"       \
  "\r\n"                                                                               \
  "  Image data is specified in a row-major interleaved format. Each pixel is\r\n"     \
  "  5 16-bit values: R,G,B,V,UV where 0000 is off and FFFF is on. Additionally,\r\n"  \
  "  each color channel has a 3-bit maximum current and 7-bit brightness, and\r\n"     \
  "  each pixel has a 7-bit dot correction, all of which control the LED drive\r\n"    \
  "  current. See the TLC5955 datasheet for more information.\r\n"                     \
  "  Binary data is encoded using the SCPI block format: #<d><len><data>, where\r\n"   \
  "    <d> and <len> are ASCII encoded decimal numbers,\r\n"                           \
  "    <d> is a single decimal digit, the number of digits in <len>, and\r\n"          \
  "    <len> is the number of bytes in <data>."                                        \
  "\r\n\r\nCommands:\r\n"

//TODO:
// - address translation will need modification to support panels wider than 12

constexpr uint32_t PANEL_WIDTH = 12;
constexpr uint32_t PANEL_HEIGHT = 8;
constexpr uint32_t PANEL_CHANNELS = 5;
constexpr uint32_t PANEL_DIMS[3] = {PANEL_WIDTH, PANEL_HEIGHT, PANEL_CHANNELS};

constexpr size_t PANEL_CHIPS = 10;
constexpr size_t NUM_LEDS = PANEL_CHIPS * TLC5955::NUM_LEDS;

constexpr int PIN_GCLK = 20, PIN_SCLK = 14, PIN_MOSI = 11, PIN_MISO = 12, PIN_LATCH = 10;

bool echo = true, enabled = false;

template <typename T, size_t N>
constexpr size_t alen(const T (&arr)[N]) { return N; }

//LED globals
TLC5955 leds(KINETISK_SPI0);
uint8_t pwm_buffer[PANEL_CHIPS * TLC5955::PWM_BUFFER_SIZE];
uint8_t ctrl_buffer[PANEL_CHIPS * TLC5955::CTRL_BUFFER_SIZE];

/* PIXEL -> LED ADDRESS TRANSLATION

We receive pixels in a row-major interleaved format (y, x, c) with dimensions
 (PANEL_HEIGHT, PANEL_WIDTH, 5).
The LED driver chips, however, each control a rectangular patch of 48 LEDs.
The RGB chips each control a 4x4x3 patch while the VUV chips control 4x6x2.
The chips are daisy chained in groups of 5: RGB-VUV-RGB-VUV-RGB
*/

size_t rgb_chips[] = {0, 2, 4, 5, 7, 9}; // RGB chip indices, terminated in (size_t)(-1)
size_t uv_chips[] = {1, 3, 6, 8};        // UV chip indices, terminated in (size_t)(-1)
size_t ctrl_addr(size_t chip)
{
  return chip * TLC5955::CTRL_BUFFER_SIZE;
}

//give the index of the RGB LED at (y,x,c) in a single chain
size_t pixel_addr_rgb(size_t y, size_t x, size_t c)
{
  size_t cy = y / 4, cx = x / 4; //chip coordinates
  y -= 4 * cy;
  x -= 4 * cx; //pixel coordinates in the chip
  return cy * (5 * 0x30) + cx * 0x60 + y * 12 + x * 3 + c;
}

//give the index of the V/UV LED at (y,x,c) in a single chain
//in this case, c = 0: V, 1: UV
size_t pixel_addr_vuv(size_t y, size_t x, size_t c)
{
  static size_t lut[] = {
      0, 1, 3, 6, 7, 9,  //V indices along the top row
      2, 4, 5, 8, 10, 11 //UV indices along the top row
  };
  size_t cy = y / 4, cx = x / 6; //chip coordinates
  y -= 4 * cy;
  x -= 6 * cx; //pixel coordinates in the chip
  return cy * (5 * 0x30) + cx * 0x60 + 0x30 + y * 12 + lut[c * 6 + x];
}

//give the index of the first LED of the chip that covers pixel (y,x) given
// the channel c
size_t pixel_addr(size_t y, size_t x, size_t c)
{
  if (c < 3)
    return pixel_addr_rgb(y, x, c);
  else
    return pixel_addr_vuv(y, x, c - 3);
}

//global look-up table for reordering pixels
constexpr size_t lut_addr(size_t y, size_t x, size_t c)
{
  return c + PANEL_CHANNELS * (x + PANEL_WIDTH * y);
}

size_t pixel_addr_lut[lut_addr(PANEL_HEIGHT, 0, 0)];

void init_pixel_addr_lut()
{
  for (size_t y = 0; y < PANEL_HEIGHT; ++y)
    for (size_t x = 0; x < PANEL_WIDTH; ++x)
      for (size_t c = 0; c < PANEL_CHANNELS; ++c)
        pixel_addr_lut[lut_addr(y, x, c)] = pixel_addr(y, x, c);
}

/* SCPI Commands */
constexpr size_t SCPI_INPUT_BUFFER_SIZE = 1024;
constexpr size_t SCPI_ERROR_QUEUE_SIZE = 4;
const char *SCPI_IDN1 = "\"Samuel Powell\""; //Manufacturer
const char *SCPI_IDN2 = "UVTV";              //Model
const char *SCPI_IDN3 = "0000";              //Serial #
const char *SCPI_IDN4 = "0";                 //Revision

namespace System
{ //use a namespace to aid code browsing
scpi_result_t Help(scpi_t *ctx);
scpi_result_t Prog(scpi_t *ctx);
scpi_result_t ErrAllQ(scpi_t *ctx);
scpi_result_t CommEcho(scpi_t *ctx);
scpi_result_t CommEchoQ(scpi_t *ctx);
} // namespace System

namespace Display
{
scpi_result_t GeomQ(scpi_t *ctx);

scpi_result_t Mode(scpi_t *ctx);
scpi_result_t ModeQ(scpi_t *ctx);

scpi_result_t Maxc(scpi_t *ctx);
scpi_result_t MaxcQ(scpi_t *ctx);

scpi_result_t Bri(scpi_t *ctx);
scpi_result_t BriQ(scpi_t *ctx);

scpi_result_t Dotc(scpi_t *ctx);
scpi_result_t DotcQ(scpi_t *ctx);

scpi_result_t DotcAll(scpi_t *ctx);
scpi_result_t DotcAllQ(scpi_t *ctx);

scpi_result_t Pwm(scpi_t *ctx);
scpi_result_t PwmQ(scpi_t *ctx);

scpi_result_t PwmAll(scpi_t *ctx);
scpi_result_t PwmAllQ(scpi_t *ctx);

scpi_result_t En(scpi_t *ctx);
scpi_result_t EnQ(scpi_t *ctx);

scpi_result_t Refr(scpi_t *ctx);

scpi_result_t SPIFreq(scpi_t *ctx);

scpi_result_t LutQ(scpi_t *ctx);
} // namespace Display

scpi_command_t scpi_commands[] = { //{pattern, callback, tag}
    //Standard commands
    SCPI_CMDS_BASIC,
    //System
    {"HELP", System::Help, 0},
    {"SYSTem:HELP:HEADers?", System::Help, 1},
    {"SYSTem:PROGram", System::Prog, 0},
    {"SYSTem:ERRor:ALL?", System::ErrAllQ, 0},
    {"SYSTem:COMMunicate:ECHO", System::CommEcho, 0},
    {"SYSTem:COMMunicate:ECHO?", System::CommEchoQ, 0},
    {"DISPlay[:ENable]", Display::En, 0},
    {"DISPlay[:ENable]?", Display::EnQ, 0},
    {"DISPlay:MODE", Display::Mode, 0},
    {"DISPlay:MODE?", Display::ModeQ, 0},
    {"DISPlay:GEOMetry?", Display::GeomQ, 0},
    {"DISPlay:MAXCurrent", Display::Maxc, 0},
    {"DISPlay:MAXCurrent?", Display::MaxcQ, 0},
    {"DISPlay:BRIghtness", Display::Bri, 0},
    {"DISPlay:BRIghtness?", Display::BriQ, 0},
    {"DISPlay:DOTCorrect", Display::Dotc, 0},
    {"DISPlay:DOTCorrect?", Display::DotcQ, 0},
    {"DISPlay:DOTCorrect:ALL", Display::DotcAll, 0},
    {"DISPlay:DOTCorrect:ALL?", Display::DotcAllQ, 0},
    {"DISPlay:PWM", Display::Pwm, 0},
    {"DISPlay:PWM?", Display::PwmQ, 0},
    {"DISPlay:PWM:ALL", Display::PwmAll, 0},
    {"DISPlay:PWM:ALL?", Display::PwmAllQ, 0},
    {"DISPlay:SPIFrequency", Display::SPIFreq, 0},
    {"DISPlay:REFResh", Display::Refr, 0},
    {"DISPlay:LUT?", Display::LutQ, 0},
    SCPI_CMD_LIST_END};

scpi_help_t scpi_help[] = {
    {"HELP", "Print this help message"},
    {"SYSTem:HELP:HEADers?", "List all commands"},
    SCPI_HELP_BASIC,
    {"SYSTem:ERRor:ALL?", "List all current errors"},
    {"SYSTem:PROGram", "Reboot into bootloader for programming"},
    {"SYSTem:COMMunicate:ECHO[?] ON|OFF", "Enable serial echo"},
    {"DISPlay[:ENable][?]", "Turn panel on or off"},
    {"DISPlay:GEOMetry?", "Return WIDTH,HEIGHT,CHANNELS of the panel"},
    {"DISPlay:MODE[?]", "5-bit Function Control register. Accepts a number or a list of named options:\r\n    Dsprpt, Tmgrst, Rfresh, Espwm, Lsdvlt\r\n  D,E is probably what you want."},
    {"DISPlay:MAXCurrent[?]", "R,G,B,V: 4x 3-bit maximum current code. UV uses the same max current as V."},
    {"DISPlay:BRIghtness[?]", "R,G,B,V: 4x 7-bit brightness code. UV uses the same brightness as V."},
    {"DISPlay:DOTCorrect[?]", "x,y,c[,DC]: 7-bit dot correct code for LED at (x,y,c)"},
    {"DISPlay:DOTCorrect:ALL[?]", "All dot correct codes, binary encoded each in 1 byte."},
    {"DISPlay:PWM[?]", "x,y,c[,PWM]: 16-bit PWM code for LED at (x,y,c)"},
    {"DISPlay:PWM:ALL[?]", "All PWM codes, binary encoded each in 2 bytes."},
    {"DISPlay:SPIFrequency", "f: set frequency, returns actual."},
    {"DISPlay:REFResh", "(Re)send PWM codes to panel."},
    SCPI_HELP_LIST_END};

size_t scpi_write(scpi_t *ctx, const char *data, size_t len)
{
  return SER.write(data, len);
}

void restart()
{
  //ARM Cortex-M: write SYSRESETREQ to NVIC Application Interrupt and Reset Control
  *((uint32_t *)0xE000ED0C) = 0x5FA0004;
}

scpi_result_t scpi_reset(scpi_t *ctx)
{
  SCPI_ResultCharacters(ctx, "**RESET**", 9);
  SER.flush();
  delay(100);
  restart();
  return SCPI_RES_OK;
}

int scpi_error(scpi_t *ctx, int_fast16_t err)
{
  if (err != SCPI_ERROR_NO_ERROR)
    SCPI_ResultCharacters(ctx, "**ERROR**", 9);
  return 0;
}

scpi_interface_t scpi_interface =
    {scpi_error, scpi_write, nullptr, nullptr, scpi_reset};

char scpi_input_buffer[SCPI_INPUT_BUFFER_SIZE];

scpi_error_t scpi_error_queue[SCPI_ERROR_QUEUE_SIZE];

scpi_t scpi_context;

scpi_result_t System::Help(scpi_t *ctx)
{
  switch (SCPI_CmdTag(ctx))
  {
  case 0: //HELP
    SER.print(SYSTEM_HELP);
    for (auto *help = scpi_help; help->syntax != nullptr; ++help)
    {
      SER.printf("%s\r\n  %s\r\n", help->syntax, help->description);
    }
    break;
  case 1: //SYSTem:HELP:HEADers?
    for (auto *help = scpi_help; help->syntax != nullptr; ++help)
    {
      SER.println(help->syntax);
    }
    break;
  default:
    return SCPI_RES_ERR;
  }
  return SCPI_RES_OK;
}

scpi_result_t System::ErrAllQ(scpi_t *ctx)
{
  //comma seperated list of all errors. always returns at least 1 item
  scpi_error_t err;
  SCPI_ErrorPop(ctx, &err);
  SCPI_ResultError(ctx, &err);
  while (SCPI_ErrorPop(ctx, &err) && err.error_code != SCPI_ERROR_NO_ERROR)
  {
    SCPI_ResultError(ctx, &err);
  }
  return SCPI_RES_OK;
}

scpi_result_t System::Prog(scpi_t *ctx)
{
  _reboot_Teensyduino_();
  return SCPI_RES_OK;
}

scpi_result_t System::CommEcho(scpi_t *ctx)
{
  bool value;
  if (SCPI_ParamBool(ctx, &value, true))
  {
    echo = value;
    return SCPI_RES_OK;
  }
  return SCPI_RES_ERR;
}

scpi_result_t System::CommEchoQ(scpi_t *ctx)
{
  SCPI_ResultBool(ctx, echo);
  return SCPI_RES_OK;
}

scpi_result_t Display::GeomQ(scpi_t *ctx)
{
  SCPI_ResultArrayUInt32(ctx, PANEL_DIMS, alen(PANEL_DIMS), SCPI_FORMAT_ASCII);
  return SCPI_RES_OK;
}

scpi_result_t Display::Maxc(scpi_t *ctx)
{
  uint32_t r, g, b, v;
  if (!SCPI_ParamUInt32(ctx, &r, true))
    return SCPI_RES_ERR;
  if (!SCPI_ParamUInt32(ctx, &g, true))
    return SCPI_RES_ERR;
  if (!SCPI_ParamUInt32(ctx, &b, true))
    return SCPI_RES_ERR;
  if (!SCPI_ParamUInt32(ctx, &v, true))
    return SCPI_RES_ERR;
  if (r > 7 || g > 7 || b > 7 || v > 7)
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  for (size_t i : rgb_chips)
  {
    uint8_t *buf = ctrl_buffer + ctrl_addr(i);
    TLC5955::set_max_current(buf, 0, (uint8_t)r);
    TLC5955::set_max_current(buf, 1, (uint8_t)g);
    TLC5955::set_max_current(buf, 2, (uint8_t)b);
  }
  for (size_t i : uv_chips)
  {
    uint8_t *buf = ctrl_buffer + ctrl_addr(i);
    TLC5955::set_max_current(buf, 0, (uint8_t)v);
    TLC5955::set_max_current(buf, 1, (uint8_t)v);
    TLC5955::set_max_current(buf, 2, (uint8_t)v);
  }
  return SCPI_RES_OK;
}

scpi_result_t Display::SPIFreq(scpi_t *ctx)
{
  uint32_t val;
  if (!SCPI_ParamUInt32(ctx, &val, true))
    return SCPI_RES_ERR;
  val = leds.set_baudrate(val);
  SCPI_ResultUInt32(ctx, val);
  return SCPI_RES_OK;
}

scpi_result_t Display::MaxcQ(scpi_t *ctx)
{
  uint8_t rgbv[4];
  uint8_t *buf = ctrl_buffer + ctrl_addr(rgb_chips[0]);
  rgbv[0] = TLC5955::get_max_current(buf, 0);
  rgbv[1] = TLC5955::get_max_current(buf, 1);
  rgbv[2] = TLC5955::get_max_current(buf, 2);

  buf = ctrl_buffer + ctrl_addr(uv_chips[0]);
  rgbv[3] = TLC5955::get_max_current(buf, 0);

  SCPI_ResultArrayUInt8(ctx, rgbv, 4, SCPI_FORMAT_ASCII);
  return SCPI_RES_OK;
}

scpi_result_t Display::Bri(scpi_t *ctx)
{
  uint32_t r, g, b, v;
  if (!SCPI_ParamUInt32(ctx, &r, true))
    return SCPI_RES_ERR;
  if (!SCPI_ParamUInt32(ctx, &g, true))
    return SCPI_RES_ERR;
  if (!SCPI_ParamUInt32(ctx, &b, true))
    return SCPI_RES_ERR;
  if (!SCPI_ParamUInt32(ctx, &v, true))
    return SCPI_RES_ERR;
  if (r > 127 || g > 127 || b > 127 || v > 127)
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  for (size_t i : rgb_chips)
  {
    uint8_t *buf = ctrl_buffer + ctrl_addr(i);
    TLC5955::set_brightness(buf, 0, (uint8_t)r);
    TLC5955::set_brightness(buf, 1, (uint8_t)g);
    TLC5955::set_brightness(buf, 2, (uint8_t)b);
  }
  for (size_t i : uv_chips)
  {
    uint8_t *buf = ctrl_buffer + ctrl_addr(i);
    TLC5955::set_brightness(buf, 0, (uint8_t)v);
    TLC5955::set_brightness(buf, 1, (uint8_t)v);
    TLC5955::set_brightness(buf, 2, (uint8_t)v);
  }
  return SCPI_RES_OK;
}

scpi_result_t Display::BriQ(scpi_t *ctx)
{
  uint8_t rgbv[4];
  uint8_t *buf = ctrl_buffer + ctrl_addr(rgb_chips[0]);
  rgbv[0] = TLC5955::get_brightness(buf, 0);
  rgbv[1] = TLC5955::get_brightness(buf, 1);
  rgbv[2] = TLC5955::get_brightness(buf, 2);

  buf = ctrl_buffer + ctrl_addr(uv_chips[0]);
  rgbv[3] = TLC5955::get_brightness(buf, 0);

  SCPI_ResultArrayUInt8(ctx, rgbv, 4, SCPI_FORMAT_ASCII);
  return SCPI_RES_OK;
}

scpi_result_t Display::Dotc(scpi_t *ctx)
{
  uint32_t xycv[4];
  size_t len;
  if (!SCPI_ParamArrayUInt32(ctx, xycv, alen(xycv), &len, SCPI_FORMAT_ASCII, true))
    return SCPI_RES_ERR;
  uint32_t &x = xycv[0], &y = xycv[1], &c = xycv[2], &v = xycv[3];
  if (len != 4 || x >= PANEL_WIDTH || y >= PANEL_HEIGHT || c >= PANEL_CHANNELS || v > 0x7f)
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  TLC5955::set_dot_correct(ctrl_buffer, pixel_addr_lut[lut_addr(y, x, c)], uint8_t(v));
  return SCPI_RES_OK;
}

scpi_result_t Display::DotcQ(scpi_t *ctx)
{
  uint32_t xyc[3];
  size_t len;
  if (!SCPI_ParamArrayUInt32(ctx, xyc, alen(xyc), &len, SCPI_FORMAT_ASCII, true))
    return SCPI_RES_ERR;
  uint32_t &x = xyc[0], &y = xyc[1], &c = xyc[2];
  if (len != 3 || x >= PANEL_WIDTH || y >= PANEL_HEIGHT || c >= PANEL_CHANNELS)
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  uint8_t dc = TLC5955::get_dot_correct(ctrl_buffer, pixel_addr_lut[lut_addr(y, x, c)]);
  SCPI_ResultUInt8(ctx, dc);
  return SCPI_RES_OK;
}

scpi_result_t Display::DotcAll(scpi_t *ctx)
{
  const char *value;
  size_t len;
  if (!SCPI_ParamArbitraryBlock(ctx, &value, &len, true))
    return SCPI_RES_ERR;
  if (len != NUM_LEDS)
  { //1 byte per LED
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  for (size_t i = 0; i < NUM_LEDS; ++i)
  {
    TLC5955::set_dot_correct(ctrl_buffer, pixel_addr_lut[i], value[i]);
  }
  return SCPI_RES_OK;
}

scpi_result_t Display::DotcAllQ(scpi_t *ctx)
{
  //1 byte per LED
  uint8_t dc[NUM_LEDS];
  for (size_t i = 0; i < NUM_LEDS; ++i)
  {
    dc[i] = TLC5955::get_dot_correct(ctrl_buffer, pixel_addr_lut[i]);
  }
  SCPI_ResultArbitraryBlock(ctx, dc, sizeof(dc));
  return SCPI_RES_OK;
}

scpi_result_t Display::Pwm(scpi_t *ctx)
{
  uint32_t xycv[4];
  size_t len;
  if (!SCPI_ParamArrayUInt32(ctx, xycv, alen(xycv), &len, SCPI_FORMAT_ASCII, true))
    return SCPI_RES_ERR;
  uint32_t &x = xycv[0], &y = xycv[1], &c = xycv[2], &v = xycv[3];
  if (len != alen(xycv) || x >= PANEL_WIDTH || y >= PANEL_HEIGHT || c >= PANEL_CHANNELS || v > 0xffff)
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  TLC5955::set_pwm(pwm_buffer, pixel_addr_lut[lut_addr(y, x, c)], uint16_t(v));
  return SCPI_RES_OK;
}

scpi_result_t Display::PwmQ(scpi_t *ctx)
{
  uint32_t xyc[3];
  size_t len;
  if (!SCPI_ParamArrayUInt32(ctx, xyc, alen(xyc), &len, SCPI_FORMAT_ASCII, true))
    return SCPI_RES_ERR;
  uint32_t &x = xyc[0], &y = xyc[1], &c = xyc[2];
  if (len != alen(xyc) || x >= PANEL_WIDTH || y >= PANEL_HEIGHT || c >= PANEL_CHANNELS)
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  uint16_t pwm = TLC5955::get_pwm(pwm_buffer, pixel_addr_lut[lut_addr(y, x, c)]);
  SCPI_ResultUInt16Base(ctx, pwm, 16);
  return SCPI_RES_OK;
}

scpi_result_t Display::PwmAll(scpi_t *ctx)
{
  const char *value;
  size_t len;
  if (!SCPI_ParamArbitraryBlock(ctx, &value, &len, true))
    return SCPI_RES_ERR;
  if (len != sizeof(pwm_buffer))
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  const uint16_t *pwm_vals = (uint16_t *)value;
  for (size_t i = 0; i < NUM_LEDS; ++i)
  {
    TLC5955::set_pwm(pwm_buffer, pixel_addr_lut[i], pwm_vals[i]);
  }
  return SCPI_RES_OK;
}

scpi_result_t Display::PwmAllQ(scpi_t *ctx)
{
  uint16_t pwm[NUM_LEDS];
  for (size_t i = 0; i < NUM_LEDS; ++i)
  {
    pwm[i] = TLC5955::get_pwm(pwm_buffer, pixel_addr_lut[i]);
  }
  SCPI_ResultArbitraryBlock(ctx, pwm, sizeof(pwm));
  return SCPI_RES_OK;
}

//TODO: delete?
scpi_result_t Display::LutQ(scpi_t *ctx)
{
  uint32_t xyc[3];
  size_t len;
  if (!SCPI_ParamArrayUInt32(ctx, xyc, alen(xyc), &len, SCPI_FORMAT_ASCII, true))
    return SCPI_RES_ERR;
  uint32_t &x = xyc[0], &y = xyc[1], &c = xyc[2];
  if (len != 3 || x >= PANEL_WIDTH || y >= PANEL_HEIGHT || c >= PANEL_CHANNELS)
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
    return SCPI_RES_ERR;
  }
  SCPI_ResultUInt32(ctx, pixel_addr_lut[lut_addr(y, x, c)]);
  return SCPI_RES_OK;
}

const scpi_choice_def_t disp_mode_choices[]{
    {"Dsprpt", 0},
    {"Tmgrst", 1},
    {"Rfresh", 2},
    {"Espwm", 3},
    {"Lsdvlt", 4},
    SCPI_CHOICE_LIST_END};

scpi_result_t Display::Mode(scpi_t *ctx)
{
  uint8_t mode;
  scpi_parameter_t param;
  int32_t choice;
  if (!SCPI_Parameter(ctx, &param, true))
    return SCPI_RES_ERR;
  if (SCPI_ParamIsNumber(&param, false))
  {
    uint32_t val = 0;
    if (!SCPI_ParamToUInt32(ctx, &param, &val) || val > 0x1f)
    {
      SCPI_ErrorPush(ctx, SCPI_ERROR_ILLEGAL_PARAMETER_VALUE);
      return SCPI_RES_ERR;
    }
    mode = val;
  }
  else if (SCPI_ParamToChoice(ctx, &param, disp_mode_choices, &choice))
  {
    mode |= (1 << choice);
    while (SCPI_Parameter(ctx, &param, false))
    {
      if (SCPI_ParamToChoice(ctx, &param, disp_mode_choices, &choice))
      {
        mode |= (1 << choice);
      }
      else
      {
        SCPI_ErrorPush(ctx, SCPI_ERROR_DATA_TYPE_ERROR);
        return SCPI_RES_ERR;
      }
    }
    if (!SCPI_ParamIsValid(&param))
      return SCPI_RES_ERR; //parser error
  }
  else
  {
    SCPI_ErrorPush(ctx, SCPI_ERROR_DATA_TYPE_ERROR);
    return SCPI_RES_ERR;
  }
  for (size_t i = 0; i < PANEL_CHIPS; ++i)
  {
    TLC5955::set_mode(ctrl_buffer + ctrl_addr(i), mode);
  }
  return SCPI_RES_OK;
}

scpi_result_t Display::ModeQ(scpi_t *ctx)
{
  SCPI_ResultUInt32(ctx, TLC5955::get_mode(ctrl_buffer));
  return SCPI_RES_OK;
}

scpi_result_t Display::En(scpi_t *ctx)
{
  scpi_bool_t en = true;
  if (!SCPI_ParamBool(ctx, &en, false))
  {
    if (SCPI_ErrorCount(ctx))
      return SCPI_RES_ERR;
  }
  if (en)
  {
    //transfer control data twice
    leds.transfer_control(PANEL_CHIPS, ctrl_buffer, nullptr);
    leds.transfer_control(PANEL_CHIPS, ctrl_buffer, nullptr);
    //transfer pwm data
    leds.transfer_pwm(PANEL_CHIPS, pwm_buffer, nullptr);
    //start clock
    analogWrite(PIN_GCLK, 1);
    enabled = true;
  }
  else
  {
    //transfer 0s
    leds.transfer_pwm(PANEL_CHIPS, nullptr, nullptr);
    delay(1); //wait for it to latch, just in case
    //stop clock
    analogWrite(PIN_GCLK, 0);
    enabled = false;
  }
  return SCPI_RES_OK;
}

scpi_result_t Display::EnQ(scpi_t *ctx)
{
  SCPI_ResultBool(ctx, enabled);
  return SCPI_RES_OK;
}

scpi_result_t Display::Refr(scpi_t *ctx)
{
  leds.transfer_pwm(PANEL_CHIPS, pwm_buffer, nullptr);
  return SCPI_RES_OK;
}

/* */

void setup()
{
  SER.begin(9600);
  SER.println("Booting");
  SER.setTimeout(100);
  init_pixel_addr_lut();

  //write magic bytes into control buffer
  for (size_t i = 0; i < PANEL_CHIPS; ++i)
  {
    TLC5955::set_magic(ctrl_buffer + ctrl_addr(i));
  }
  //initialize SCPI parser
  SCPI_Init(&scpi_context, scpi_commands,
            &scpi_interface, scpi_units_def,
            SCPI_IDN1, SCPI_IDN2, SCPI_IDN3, SCPI_IDN4,
            scpi_input_buffer, SCPI_INPUT_BUFFER_SIZE,
            scpi_error_queue, SCPI_ERROR_QUEUE_SIZE);
  //set up clock
  analogWriteResolution(1);
  analogWriteFrequency(PIN_GCLK, 12e6);
  analogWrite(PIN_GCLK, 0);
  //and LED driver pins
  leds.set_pins(PIN_SCLK, PIN_MOSI, PIN_MISO, PIN_LATCH);
}

constexpr size_t SER_BUFFER_LEN = 16;
char ser_buffer[SER_BUFFER_LEN];

void loop()
{
  size_t read_len = SER.available();
  read_len = SER.readBytes(ser_buffer, min(SER_BUFFER_LEN, read_len));
  if (read_len > 0)
  {
    if (echo)
      SER.write(ser_buffer, read_len);
    SCPI_Input(&scpi_context, ser_buffer, read_len);
  }
}
