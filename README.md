[![DOI](https://zenodo.org/badge/225283253.svg)](https://zenodo.org/badge/latestdoi/225283253)

# UVTV
RGB-V-UV LED display, as published in "A five-channel LED display to investigate UV perception" in Methods in Ecology and Evolution, 2021.

## TO DO
- Display: Compactness and seamless edge-to-edge display panelling is *not* a priority any more. There are a few places where these design goals made things quite difficult and any new production should have these changes made:
  - [ ] Point-of-Load power supply on display board for LEDs.
  - [ ] Separate LED power from TLC5955 power.
  - [ ] Increase margins and put mounting holes in sane places.
  - [ ] Use larger connectors for the flat-flex cables. Assess signal integrity and see if more conductors would be useful for shielding.
  - [ ] Another layer of PCB might be in order to ease routing of control signals, especially if there are signal integrity issues at higher speeds.
- Controller: A higher-speed controller is necessary to use the full potential of the display panel. There are several viable alternatives:
  1. A high-speed microcontroller module, such as the Teensy 4.1 (600 MHz), using built-in SPI or bit-banging to communicate with TLC5955 chips.
  2. A microcontroller + FPGA combo -- using the microcontroller to handle USB and FPGA to handle the TLC5955 communication.
  3. An FPGA to handle both USB and TLC5955.
- 3D Models
  - [ ] Redraw in an open source CAD tool, e.g. FreeCAD.
