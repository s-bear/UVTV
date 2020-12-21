This is example flatfield calibration data from the 2nd UVTV board made.

0.7z, 1.7z, and 2.7z hold compressed data captured before calibration (0) and 
after 1 and 2 iterations of the procedure respectively. Decompress using
7-zip to replicate the procedure.

The "test_panel.py" script was run to show the "corners", "red", "green",
"blue", "violet", and "uv" images.
For the initial run, the script was configured with:
    reset_config = True
    save_config = False
    config_path = 'board 2 data/0'
Setting "reset_config = True" means the script generates "panel_config.npz" with
default data (lines 30-37).

Photos of the display were taken at each stage of the script using a modified
Olympus E-PL5 camera, the raw ORF files saved in 'board 2 data/0'.

The ORF files were converted to tiff using RawTherapee, with the settings
stored in the associated pp3 files.

"pixel_stats.py" was run with
    config_path = 'board 2 data/0'
to generate "pixel_stats.npz"

"flatfield.py" was run with
    config_path = 'board 2 data/0'
to update "panel_config.npz" with new dotcorrect coefficients.

The procedure was then repeated again, running "test_panel.py" with
    reset_config = False
    save_config = False
    config_path = 'board 2 data/0'

The new images were saved into "board 2 data/1" and "0/panel_config.npz" was
copied to "1/panel_config.npz" so that "flatfield.py" could update it with new
coefficients.

The final round of images was generated using these coefficients and saved into
"board 2 data/2" for validation and to generate figures showing uniformity.