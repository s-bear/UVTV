EESchema Schematic File Version 4
LIBS:UVTV-cache
EELAYER 26 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "UVTV Prototype"
Date "2019-04-04"
Rev "2"
Comp "Queensland Brain Institute, University of Queensland"
Comment1 "Samuel B. Powell"
Comment2 ""
Comment3 ""
Comment4 "Use expand_netlist.py to generate netlist for PCB and BOM"
$EndDescr
$Comp
L archive:Device_C C[1:2][A:E]`1
U 1 1 5BE2CB9E
P 3400 6500
F 0 "C[1:2][A:E]`1" H 3515 6546 50  0000 L CNN
F 1 "0.1u" H 3515 6455 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric_Pad1.05x0.95mm_HandSolder" H 3438 6350 50  0001 C CNN
F 3 "~" H 3400 6500 50  0001 C CNN
F 4 "~" H 0   1900 50  0001 C CNN "Tolerance"
F 5 "6V" H 0   1900 50  0001 C CNN "Voltage"
F 6 "Samsung" H 3400 6500 50  0001 C CNN "Manufacturer"
F 7 "CL10F104ZO8NNNC" H 3400 6500 50  0001 C CNN "Part #"
F 8 "Digikey" H 3400 6500 50  0001 C CNN "Vendor"
F 9 "1276-1258" H 0   1900 50  0001 C CNN "Order #"
	1    3400 6500
	1    0    0    -1  
$EndComp
Wire Wire Line
	3400 6650 3400 6750
$Comp
L archive:power_GND #PWR0102
U 1 1 5BE310A9
P 3400 6750
F 0 "#PWR0102" H 3400 6500 50  0001 C CNN
F 1 "GND" H 3405 6577 50  0000 C CNN
F 2 "" H 3400 6750 50  0001 C CNN
F 3 "" H 3400 6750 50  0001 C CNN
	1    3400 6750
	1    0    0    -1  
$EndComp
Text Notes 3250 7000 1    50   ~ 0
Decoupling for LED drivers
Wire Wire Line
	3400 6250 3400 6350
$Comp
L Mechanical:MountingHole MH[1:2][A:B]`1
U 1 1 5BDBFEFF
P 2900 3250
F 0 "MH[1:2][A:B]`1" H 3000 3296 50  0000 L CNN
F 1 "MountingHole" H 3000 3205 50  0000 L CNN
F 2 "MountingHole:MountingHole_2.2mm_M2" H 2900 3250 50  0001 C CNN
F 3 "~" H 2900 3250 50  0001 C CNN
F 4 "~" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "~" H 0   0   50  0001 C CNN "Order #"
F 6 "~" H 0   0   50  0001 C CNN "Part #"
F 7 "~" H 0   0   50  0001 C CNN "Vendor"
	1    2900 3250
	1    0    0    -1  
$EndComp
Wire Wire Line
	9650 5550 10450 5550
Wire Wire Line
	9750 5450 10450 5450
Wire Wire Line
	9550 5650 10450 5650
Wire Wire Line
	7900 5550 8700 5550
Wire Wire Line
	8000 5450 8700 5450
Wire Wire Line
	7800 5650 8700 5650
Wire Wire Line
	6150 5550 6950 5550
Wire Wire Line
	6250 5450 6950 5450
Wire Wire Line
	6050 5650 6950 5650
Wire Wire Line
	4400 5550 5200 5550
Wire Wire Line
	4500 5450 5200 5450
Wire Wire Line
	4300 5650 5200 5650
Wire Wire Line
	2650 5550 3450 5550
Wire Wire Line
	2750 5450 3450 5450
Wire Wire Line
	2550 5650 3450 5650
Wire Wire Line
	900  6250 1650 6250
Wire Wire Line
	900  6450 1650 6450
Wire Wire Line
	1650 6650 900  6650
Wire Wire Line
	900  7100 1750 7100
Wire Wire Line
	900  7550 1750 7550
Text Label 900  6650 0    50   ~ 0
B[1:2][A:C][0:15]
Text Label 900  7550 0    50   ~ 0
V[1:2][A:C][0:15]
Text Label 900  7100 0    50   ~ 0
UV[1:2][A:C][0:15]
Wire Wire Line
	2300 7550 2050 7550
Wire Wire Line
	2300 7100 2300 7550
Connection ~ 2300 7100
Wire Wire Line
	2300 7100 2050 7100
$Comp
L archive:Device_LED V[1:2][A:C][0:15]`1
U 1 1 5CC5FB2F
P 1900 7550
AR Path="/5CC5FB2F" Ref="V[1:2][A:C][0:15]`1"  Part="1" 
AR Path="/5CC2BDB8/5CC5FB2F" Ref="V[0:47]`?"  Part="1" 
AR Path="/5CC436B9/5CC5FB2F" Ref="V[0:47]`?"  Part="1" 
AR Path="/5CC4529E/5CC5FB2F" Ref="V[0:47]`?"  Part="1" 
F 0 "V[1:2][A:C][0:15]`1" H 1891 7766 50  0000 C CNN
F 1 "SM0603UV-395" H 1891 7675 50  0000 C CNN
F 2 "UVTV:LED_0603_1608Metric" H 1900 7550 50  0001 C CNN
F 3 "SM0603UV-395.pdf" H 1900 7550 50  0001 C CNN
F 4 "400 nm" H -5650 1800 50  0001 C CNN "Note"
F 5 "SM0603UV-395" H -5650 1800 50  0001 C CNN "Part #"
F 6 "Bivar Inc" H 0   0   50  0001 C CNN "Manufacturer"
F 7 "492-1949" H 0   0   50  0001 C CNN "Order #"
F 8 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    1900 7550
	1    0    0    -1  
$EndComp
$Comp
L archive:Device_LED UV[1:2][A:C][0:15]`1
U 1 1 5CC5FB38
P 1900 7100
AR Path="/5CC5FB38" Ref="UV[1:2][A:C][0:15]`1"  Part="1" 
AR Path="/5CC2BDB8/5CC5FB38" Ref="UV[0:47]`?"  Part="1" 
AR Path="/5CC436B9/5CC5FB38" Ref="UV[0:47]`?"  Part="1" 
AR Path="/5CC4529E/5CC5FB38" Ref="UV[0:47]`?"  Part="1" 
F 0 "UV[1:2][A:C][0:15]`1" H 1891 7316 50  0000 C CNN
F 1 "VLMU1610-365" H 1891 7225 50  0000 C CNN
F 2 "UVTV:D_0606_1616Metric" H 1900 7100 50  0001 C CNN
F 3 "vlmu1610-365-135.pdf" H 1900 7100 50  0001 C CNN
F 4 "365 nm" H -5650 1800 50  0001 C CNN "Note"
F 5 "VLMU1610-365-135" H -5650 1800 50  0001 C CNN "Part #"
F 6 "Vishay Semiconductor Opto Division" H 0   0   50  0001 C CNN "Manufacturer"
F 7 "VLMU1610-365-135" H 0   0   50  0001 C CNN "Order #"
F 8 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    1900 7100
	1    0    0    -1  
$EndComp
Text Label 900  6450 0    50   ~ 0
G[1:2][A:C][0:15]
Text Label 900  6250 0    50   ~ 0
R[1:2][A:C][0:15]
Wire Wire Line
	2300 7100 2300 6450
Wire Wire Line
	2300 6150 2300 6450
Connection ~ 2300 6450
Wire Wire Line
	2300 6450 2050 6450
$Comp
L UVTV:LED_BGAR RGB[1:2][A:C][0:15]`1
U 1 1 5CC5FB46
P 1850 6450
AR Path="/5CC5FB46" Ref="RGB[1:2][A:C][0:15]`1"  Part="1" 
AR Path="/5CC2BDB8/5CC5FB46" Ref="RGB[0:47]`?"  Part="1" 
AR Path="/5CC436B9/5CC5FB46" Ref="RGB[0:47]`?"  Part="1" 
AR Path="/5CC4529E/5CC5FB46" Ref="RGB[0:47]`?"  Part="1" 
F 0 "RGB[1:2][A:C][0:15]`1" H 1850 6947 50  0000 C CNN
F 1 "EAST1616RGB" H 1850 6856 50  0000 C CNN
F 2 "UVTV:EAST1616RGBA" H 1850 6400 50  0001 C CNN
F 3 "EAST1616RGBA3.pdf" H 1850 6400 50  0001 C CNN
F 4 "EAST1616RGBA3" H -5650 1800 50  0001 C CNN "Part #"
F 5 "Everlight Electronics Co Ltd" H 0   0   50  0001 C CNN "Manufacturer"
F 6 "1080-1550" H 0   0   50  0001 C CNN "Order #"
F 7 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    1850 6450
	1    0    0    -1  
$EndComp
Wire Wire Line
	9550 4950 10450 4950
Wire Wire Line
	9750 5150 9750 5450
Wire Wire Line
	9550 5150 9750 5150
Wire Wire Line
	9650 5250 9650 5550
Wire Wire Line
	9550 5250 9650 5250
Wire Wire Line
	9550 5350 9550 5650
Wire Wire Line
	9700 4650 9700 4700
$Comp
L power:GND #PWR?
U 1 1 5CC5FB58
P 9700 4700
AR Path="/5CC2BDB8/5CC5FB58" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FB58" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FB58" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FB58" Ref="#PWR0103"  Part="1" 
F 0 "#PWR0103" H 9700 4450 50  0001 C CNN
F 1 "GND" H 9705 4527 50  0000 C CNN
F 2 "" H 9700 4700 50  0001 C CNN
F 3 "" H 9700 4700 50  0001 C CNN
	1    9700 4700
	1    0    0    -1  
$EndComp
Wire Wire Line
	9550 4650 9700 4650
Wire Wire Line
	8500 4650 8500 4550
$Comp
L power:+3.3V #PWR?
U 1 1 5CC5FB60
P 8500 4550
AR Path="/5CC2BDB8/5CC5FB60" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FB60" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FB60" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FB60" Ref="#PWR0104"  Part="1" 
F 0 "#PWR0104" H 8500 4400 50  0001 C CNN
F 1 "+3.3V" H 8515 4723 50  0000 C CNN
F 2 "" H 8500 4550 50  0001 C CNN
F 3 "" H 8500 4550 50  0001 C CNN
	1    8500 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	8700 4650 8500 4650
Wire Wire Line
	8700 5050 8100 5050
Wire Wire Line
	8700 4950 7800 4950
Wire Wire Line
	8700 4850 8050 4850
Wire Wire Line
	8700 4750 8050 4750
$Comp
L UVTV:TLC5955-RTQ U?
U 1 1 5CC5FB6B
P 9150 4550
AR Path="/5CC2BDB8/5CC5FB6B" Ref="U?"  Part="1" 
AR Path="/5CC436B9/5CC5FB6B" Ref="U?"  Part="1" 
AR Path="/5CC4529E/5CC5FB6B" Ref="U?"  Part="1" 
AR Path="/5CC5FB6B" Ref="U-RGB[1:2]C`1"  Part="1" 
F 0 "U-RGB[1:2]C`1" H 9356 4675 50  0000 C CNN
F 1 "TLC5955-RTQ" H 9356 4584 50  0000 C CNN
F 2 "UVTV:QFN-56-1EP_8x8mm_P0.5mm_EP5.6x5.6mm" H 9150 4550 50  0001 C CNN
F 3 "" H 9150 4550 50  0001 C CNN
F 4 "Texas Instruments" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "296-40588" H 0   0   50  0001 C CNN "Order #"
F 6 "TLC5955RTQR" H 0   0   50  0001 C CNN "Part #"
F 7 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    9150 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	8000 5150 8000 5450
Wire Wire Line
	7800 5150 8000 5150
Wire Wire Line
	7900 5250 7900 5550
Wire Wire Line
	7800 5250 7900 5250
Wire Wire Line
	7800 5350 7800 5650
Wire Wire Line
	7950 4650 7950 4700
$Comp
L power:GND #PWR?
U 1 1 5CC5FB7B
P 7950 4700
AR Path="/5CC2BDB8/5CC5FB7B" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FB7B" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FB7B" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FB7B" Ref="#PWR0105"  Part="1" 
F 0 "#PWR0105" H 7950 4450 50  0001 C CNN
F 1 "GND" H 7955 4527 50  0000 C CNN
F 2 "" H 7950 4700 50  0001 C CNN
F 3 "" H 7950 4700 50  0001 C CNN
	1    7950 4700
	1    0    0    -1  
$EndComp
Wire Wire Line
	7800 4650 7950 4650
Wire Wire Line
	6750 4650 6750 4550
$Comp
L power:+3.3V #PWR?
U 1 1 5CC5FB83
P 6750 4550
AR Path="/5CC2BDB8/5CC5FB83" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FB83" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FB83" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FB83" Ref="#PWR0106"  Part="1" 
F 0 "#PWR0106" H 6750 4400 50  0001 C CNN
F 1 "+3.3V" H 6765 4723 50  0000 C CNN
F 2 "" H 6750 4550 50  0001 C CNN
F 3 "" H 6750 4550 50  0001 C CNN
	1    6750 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	6950 4650 6750 4650
Wire Wire Line
	6950 5050 6300 5050
Wire Wire Line
	6950 4950 6050 4950
Wire Wire Line
	6950 4850 6300 4850
Wire Wire Line
	6950 4750 6300 4750
$Comp
L UVTV:TLC5955-RTQ U?
U 1 1 5CC5FB8E
P 7400 4550
AR Path="/5CC2BDB8/5CC5FB8E" Ref="U?"  Part="1" 
AR Path="/5CC436B9/5CC5FB8E" Ref="U?"  Part="1" 
AR Path="/5CC4529E/5CC5FB8E" Ref="U?"  Part="1" 
AR Path="/5CC5FB8E" Ref="U-UV[1:2]C`1"  Part="1" 
F 0 "U-UV[1:2]C`1" H 7606 4675 50  0000 C CNN
F 1 "TLC5955-RTQ" H 7606 4584 50  0000 C CNN
F 2 "UVTV:QFN-56-1EP_8x8mm_P0.5mm_EP5.6x5.6mm" H 7400 4550 50  0001 C CNN
F 3 "" H 7400 4550 50  0001 C CNN
F 4 "Texas Instruments" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "296-40588" H 0   0   50  0001 C CNN "Order #"
F 6 "TLC5955RTQR" H 0   0   50  0001 C CNN "Part #"
F 7 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    7400 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	6250 5150 6250 5450
Wire Wire Line
	6050 5150 6250 5150
Wire Wire Line
	6150 5250 6150 5550
Wire Wire Line
	6050 5250 6150 5250
Wire Wire Line
	6050 5350 6050 5650
Wire Wire Line
	6200 4650 6200 4700
$Comp
L power:GND #PWR?
U 1 1 5CC5FB9E
P 6200 4700
AR Path="/5CC2BDB8/5CC5FB9E" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FB9E" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FB9E" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FB9E" Ref="#PWR0107"  Part="1" 
F 0 "#PWR0107" H 6200 4450 50  0001 C CNN
F 1 "GND" H 6205 4527 50  0000 C CNN
F 2 "" H 6200 4700 50  0001 C CNN
F 3 "" H 6200 4700 50  0001 C CNN
	1    6200 4700
	1    0    0    -1  
$EndComp
Wire Wire Line
	6050 4650 6200 4650
Wire Wire Line
	5000 4650 5000 4550
$Comp
L power:+3.3V #PWR?
U 1 1 5CC5FBA6
P 5000 4550
AR Path="/5CC2BDB8/5CC5FBA6" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FBA6" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FBA6" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FBA6" Ref="#PWR0108"  Part="1" 
F 0 "#PWR0108" H 5000 4400 50  0001 C CNN
F 1 "+3.3V" H 5015 4723 50  0000 C CNN
F 2 "" H 5000 4550 50  0001 C CNN
F 3 "" H 5000 4550 50  0001 C CNN
	1    5000 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	5200 4650 5000 4650
Wire Wire Line
	5200 5050 4600 5050
Wire Wire Line
	5200 4950 4300 4950
Wire Wire Line
	5200 4850 4600 4850
Wire Wire Line
	5200 4750 4600 4750
$Comp
L UVTV:TLC5955-RTQ U?
U 1 1 5CC5FBB1
P 5650 4550
AR Path="/5CC2BDB8/5CC5FBB1" Ref="U?"  Part="1" 
AR Path="/5CC436B9/5CC5FBB1" Ref="U?"  Part="1" 
AR Path="/5CC4529E/5CC5FBB1" Ref="U?"  Part="1" 
AR Path="/5CC5FBB1" Ref="U-RGB[1:2]B`1"  Part="1" 
F 0 "U-RGB[1:2]B`1" H 5856 4675 50  0000 C CNN
F 1 "TLC5955-RTQ" H 5856 4584 50  0000 C CNN
F 2 "UVTV:QFN-56-1EP_8x8mm_P0.5mm_EP5.6x5.6mm" H 5650 4550 50  0001 C CNN
F 3 "" H 5650 4550 50  0001 C CNN
F 4 "Texas Instruments" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "296-40588" H 0   0   50  0001 C CNN "Order #"
F 6 "TLC5955RTQR" H 0   0   50  0001 C CNN "Part #"
F 7 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    5650 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	4500 5150 4500 5450
Wire Wire Line
	4300 5150 4500 5150
Wire Wire Line
	4400 5250 4400 5550
Wire Wire Line
	4300 5250 4400 5250
Wire Wire Line
	4300 5350 4300 5650
Wire Wire Line
	4450 4650 4450 4700
$Comp
L power:GND #PWR?
U 1 1 5CC5FBC1
P 4450 4700
AR Path="/5CC2BDB8/5CC5FBC1" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FBC1" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FBC1" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FBC1" Ref="#PWR0109"  Part="1" 
F 0 "#PWR0109" H 4450 4450 50  0001 C CNN
F 1 "GND" H 4455 4527 50  0000 C CNN
F 2 "" H 4450 4700 50  0001 C CNN
F 3 "" H 4450 4700 50  0001 C CNN
	1    4450 4700
	1    0    0    -1  
$EndComp
Wire Wire Line
	4300 4650 4450 4650
Wire Wire Line
	3250 4650 3250 4550
$Comp
L power:+3.3V #PWR?
U 1 1 5CC5FBC9
P 3250 4550
AR Path="/5CC2BDB8/5CC5FBC9" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FBC9" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FBC9" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FBC9" Ref="#PWR0110"  Part="1" 
F 0 "#PWR0110" H 3250 4400 50  0001 C CNN
F 1 "+3.3V" H 3265 4723 50  0000 C CNN
F 2 "" H 3250 4550 50  0001 C CNN
F 3 "" H 3250 4550 50  0001 C CNN
	1    3250 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	3450 4650 3250 4650
Wire Wire Line
	3450 5050 2850 5050
Wire Wire Line
	3450 4950 2550 4950
Wire Wire Line
	3450 4850 2850 4850
Wire Wire Line
	3450 4750 2850 4750
$Comp
L UVTV:TLC5955-RTQ U?
U 1 1 5CC5FBD4
P 3900 4550
AR Path="/5CC2BDB8/5CC5FBD4" Ref="U?"  Part="1" 
AR Path="/5CC436B9/5CC5FBD4" Ref="U?"  Part="1" 
AR Path="/5CC4529E/5CC5FBD4" Ref="U?"  Part="1" 
AR Path="/5CC5FBD4" Ref="U-UV[1:2]A`1"  Part="1" 
F 0 "U-UV[1:2]A`1" H 4106 4675 50  0000 C CNN
F 1 "TLC5955-RTQ" H 4106 4584 50  0000 C CNN
F 2 "UVTV:QFN-56-1EP_8x8mm_P0.5mm_EP5.6x5.6mm" H 3900 4550 50  0001 C CNN
F 3 "" H 3900 4550 50  0001 C CNN
F 4 "Texas Instruments" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "296-40588" H 0   0   50  0001 C CNN "Order #"
F 6 "TLC5955RTQR" H 0   0   50  0001 C CNN "Part #"
F 7 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    3900 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	2750 5150 2750 5450
Wire Wire Line
	2550 5150 2750 5150
Wire Wire Line
	2650 5250 2650 5550
Wire Wire Line
	2550 5250 2650 5250
Wire Wire Line
	2550 5350 2550 5650
Wire Wire Line
	2700 4650 2700 4700
$Comp
L power:GND #PWR?
U 1 1 5CC5FBE1
P 2700 4700
AR Path="/5CC2BDB8/5CC5FBE1" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FBE1" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FBE1" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FBE1" Ref="#PWR0111"  Part="1" 
F 0 "#PWR0111" H 2700 4450 50  0001 C CNN
F 1 "GND" H 2705 4527 50  0000 C CNN
F 2 "" H 2700 4700 50  0001 C CNN
F 3 "" H 2700 4700 50  0001 C CNN
	1    2700 4700
	1    0    0    -1  
$EndComp
Wire Wire Line
	2550 4650 2700 4650
Wire Wire Line
	1500 4650 1500 4550
$Comp
L power:+3.3V #PWR?
U 1 1 5CC5FBE9
P 1500 4550
AR Path="/5CC2BDB8/5CC5FBE9" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CC5FBE9" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CC5FBE9" Ref="#PWR?"  Part="1" 
AR Path="/5CC5FBE9" Ref="#PWR0112"  Part="1" 
F 0 "#PWR0112" H 1500 4400 50  0001 C CNN
F 1 "+3.3V" H 1515 4723 50  0000 C CNN
F 2 "" H 1500 4550 50  0001 C CNN
F 3 "" H 1500 4550 50  0001 C CNN
	1    1500 4550
	1    0    0    -1  
$EndComp
Wire Wire Line
	1700 4650 1500 4650
Wire Wire Line
	1700 5050 1050 5050
Wire Wire Line
	1700 4950 1050 4950
Wire Wire Line
	1700 4850 1050 4850
Wire Wire Line
	1700 4750 1050 4750
$Comp
L power:+3.3V #PWR?
U 1 1 5CCA419D
P 2300 6150
AR Path="/5CC2BDB8/5CCA419D" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CCA419D" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CCA419D" Ref="#PWR?"  Part="1" 
AR Path="/5CCA419D" Ref="#PWR0113"  Part="1" 
F 0 "#PWR0113" H 2300 6000 50  0001 C CNN
F 1 "+3.3V" H 2450 6200 50  0000 C CNN
F 2 "" H 2300 6150 50  0001 C CNN
F 3 "" H 2300 6150 50  0001 C CNN
	1    2300 6150
	1    0    0    -1  
$EndComp
Text Label 1050 4750 0    50   ~ 0
GSCLK[1:2]
Text Label 1050 4850 0    50   ~ 0
SCLK[1:2]
Text Label 1050 4950 0    50   ~ 0
SIN[1:2]
Text Label 1050 5050 0    50   ~ 0
LAT[1:2]
Text Label 10450 4950 2    50   ~ 0
SOUT[1:2]
$Comp
L power:+3.3V #PWR?
U 1 1 5CD622CE
P 3400 6250
AR Path="/5CC2BDB8/5CD622CE" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CD622CE" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CD622CE" Ref="#PWR?"  Part="1" 
AR Path="/5CD622CE" Ref="#PWR0114"  Part="1" 
F 0 "#PWR0114" H 3400 6100 50  0001 C CNN
F 1 "+3.3V" H 3415 6423 50  0000 C CNN
F 2 "" H 3400 6250 50  0001 C CNN
F 3 "" H 3400 6250 50  0001 C CNN
	1    3400 6250
	1    0    0    -1  
$EndComp
Text Label 2850 4750 0    50   ~ 0
GSCLK[1:2]
$Comp
L UVTV:TLC5955-RTQ U?
U 1 1 5CC5FBF8
P 2150 4550
AR Path="/5CC2BDB8/5CC5FBF8" Ref="U?"  Part="1" 
AR Path="/5CC436B9/5CC5FBF8" Ref="U?"  Part="1" 
AR Path="/5CC4529E/5CC5FBF8" Ref="U?"  Part="1" 
AR Path="/5CC5FBF8" Ref="U-RGB[1:2]A`1"  Part="1" 
F 0 "U-RGB[1:2]A`1" H 2356 4675 50  0000 C CNN
F 1 "TLC5955-RTQ" H 2356 4584 50  0000 C CNN
F 2 "UVTV:QFN-56-1EP_8x8mm_P0.5mm_EP5.6x5.6mm" H 2150 4550 50  0001 C CNN
F 3 "" H 2150 4550 50  0001 C CNN
F 4 "Digikey" H 2150 4550 50  0001 C CNN "Vendor"
F 5 "296-40588" H 2150 4550 50  0001 C CNN "Order #"
F 6 "Texas Instruments" H 0   0   50  0001 C CNN "Manufacturer"
F 7 "TLC5955RTQR" H 0   0   50  0001 C CNN "Part #"
	1    2150 4550
	1    0    0    -1  
$EndComp
Text Label 2850 4850 0    50   ~ 0
SCLK[1:2]
Text Label 4600 4850 0    50   ~ 0
SCLK[1:2]
Text Label 6300 4850 0    50   ~ 0
SCLK[1:2]
Text Label 8050 4850 0    50   ~ 0
SCLK[1:2]
Text Label 4600 4750 0    50   ~ 0
GSCLK[1:2]
Text Label 6300 4750 0    50   ~ 0
GSCLK[1:2]
Text Label 8050 4750 0    50   ~ 0
GSCLK[1:2]
Text Label 2850 5050 0    50   ~ 0
LAT[1:2]
Text Label 4600 5050 0    50   ~ 0
LAT[1:2]
Text Label 6300 5050 0    50   ~ 0
LAT[1:2]
Text Label 8100 5050 0    50   ~ 0
LAT[1:2]
Text Label 5200 5650 2    50   ~ 0
$4[1:2][B][0:7]{V,UV}
Text Label 8700 5650 2    50   ~ 0
$4[1:2][B][8:15]{V,UV}
Text Label 3450 5550 2    50   ~ 0
R[1:2][A][0:15]
Text Label 6950 5550 2    50   ~ 0
R[1:2][B][0:15]
Text Label 10450 5550 2    50   ~ 0
R[1:2][C][0:15]
Text Label 3450 5650 2    50   ~ 0
G[1:2][A][0:15]
Text Label 6950 5650 2    50   ~ 0
G[1:2][B][0:15]
Text Label 10450 5650 2    50   ~ 0
G[1:2][C][0:15]
Text Label 3450 5450 2    50   ~ 0
B[1:2][A][0:15]
Text Label 6950 5450 2    50   ~ 0
B[1:2][B][0:15]
Text Label 10450 5450 2    50   ~ 0
B[1:2][C][0:15]
Text Label 5200 5450 2    50   ~ 0
UV[1:2][A][0:15]
Text Label 8700 5450 2    50   ~ 0
UV[1:2][C][0:15]
Text Label 5200 5550 2    50   ~ 0
V[1:2][A][0:15]
Text Label 8700 5550 2    50   ~ 0
V[1:2][C][0:15]
$Comp
L Connector_Generic:Conn_01x15 J1
U 1 1 5CDC67ED
P 1500 2700
F 0 "J1" H 1420 3617 50  0000 C CNN
F 1 "Conn_01x15" H 1420 3526 50  0000 C CNN
F 2 "UVTV:Hirose_FH19SC-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal" H 1500 2700 50  0001 C CNN
F 3 "~" H 1500 2700 50  0001 C CNN
F 4 "Hirose" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "H125831" H 0   0   50  0001 C CNN "Order #"
F 6 "FH19SC-15S-0.5SH(09)" H 0   0   50  0001 C CNN "Part #"
F 7 "Digikey" H 0   0   50  0001 C CNN "Vendor"
	1    1500 2700
	-1   0    0    -1  
$EndComp
Wire Wire Line
	1700 2000 2500 2000
Wire Wire Line
	1700 2500 2150 2500
Wire Wire Line
	1700 2600 2150 2600
Wire Wire Line
	1700 2800 2150 2800
Wire Wire Line
	1700 3200 2150 3200
Wire Wire Line
	1700 3300 2150 3300
Wire Wire Line
	1700 3400 2500 3400
Text Label 2150 2100 2    50   ~ 0
GSCLK1
Text Label 2150 2800 2    50   ~ 0
GSCLK2
Text Label 2150 2500 2    50   ~ 0
LAT1
Text Label 2150 2600 2    50   ~ 0
SOUT1
Text Label 2150 3200 2    50   ~ 0
LAT2
Text Label 2150 3300 2    50   ~ 0
SOUT2
Wire Wire Line
	2500 3400 2500 3500
Connection ~ 2500 3400
$Comp
L power:GND #PWR?
U 1 1 5CEC6DDC
P 2500 3500
AR Path="/5CC2BDB8/5CEC6DDC" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CEC6DDC" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CEC6DDC" Ref="#PWR?"  Part="1" 
AR Path="/5CEC6DDC" Ref="#PWR0101"  Part="1" 
F 0 "#PWR0101" H 2500 3250 50  0001 C CNN
F 1 "GND" H 2505 3327 50  0000 C CNN
F 2 "" H 2500 3500 50  0001 C CNN
F 3 "" H 2500 3500 50  0001 C CNN
	1    2500 3500
	1    0    0    -1  
$EndComp
Wire Wire Line
	1700 3100 2150 3100
Text Label 2150 3100 2    50   ~ 0
SCLK2
Wire Wire Line
	1700 2400 2150 2400
Text Label 2150 2400 2    50   ~ 0
SCLK1
Connection ~ 2500 2700
Wire Wire Line
	1700 2700 2500 2700
Wire Wire Line
	1700 2100 2150 2100
Wire Wire Line
	2500 2000 2500 2300
Wire Wire Line
	2500 2700 2500 3000
Wire Wire Line
	1700 2200 2150 2200
Wire Wire Line
	1700 2900 2150 2900
Text Label 2150 2200 2    50   ~ 0
SIN1
Wire Wire Line
	1700 2300 2500 2300
Connection ~ 2500 2300
Wire Wire Line
	2500 2300 2500 2700
Wire Wire Line
	1700 3000 2500 3000
Connection ~ 2500 3000
Wire Wire Line
	2500 3000 2500 3400
Text Label 2150 2900 2    50   ~ 0
SIN2
$Comp
L power:GND #PWR?
U 1 1 5CDE1D83
P 3300 2550
AR Path="/5CC2BDB8/5CDE1D83" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CDE1D83" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CDE1D83" Ref="#PWR?"  Part="1" 
AR Path="/5CDE1D83" Ref="#PWR0115"  Part="1" 
F 0 "#PWR0115" H 3300 2300 50  0001 C CNN
F 1 "GND" H 3305 2377 50  0000 C CNN
F 2 "" H 3300 2550 50  0001 C CNN
F 3 "" H 3300 2550 50  0001 C CNN
	1    3300 2550
	1    0    0    -1  
$EndComp
Wire Wire Line
	3300 2550 3300 2400
Wire Wire Line
	3800 2050 3800 2200
$Comp
L power:+3.3V #PWR?
U 1 1 5CDF032B
P 3800 2050
AR Path="/5CC2BDB8/5CDF032B" Ref="#PWR?"  Part="1" 
AR Path="/5CC436B9/5CDF032B" Ref="#PWR?"  Part="1" 
AR Path="/5CC4529E/5CDF032B" Ref="#PWR?"  Part="1" 
AR Path="/5CDF032B" Ref="#PWR0116"  Part="1" 
F 0 "#PWR0116" H 3800 1900 50  0001 C CNN
F 1 "+3.3V" H 3815 2223 50  0000 C CNN
F 2 "" H 3800 2050 50  0001 C CNN
F 3 "" H 3800 2050 50  0001 C CNN
	1    3800 2050
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x02 J2
U 1 1 5CDFEE00
P 3000 2300
F 0 "J2" H 2920 1975 50  0000 C CNN
F 1 "Conn_01x02" H 2920 2066 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 3000 2300 50  0001 C CNN
F 3 "~" H 3000 2300 50  0001 C CNN
F 4 "~" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "~" H 0   0   50  0001 C CNN "Order #"
F 6 "~" H 0   0   50  0001 C CNN "Part #"
F 7 "~" H 0   0   50  0001 C CNN "Vendor"
	1    3000 2300
	-1   0    0    1   
$EndComp
Wire Wire Line
	3300 2400 3200 2400
Wire Wire Line
	3300 2400 3300 2300
Wire Wire Line
	3300 2200 3200 2200
Connection ~ 3300 2400
Wire Wire Line
	3200 2300 3300 2300
Connection ~ 3300 2300
Wire Wire Line
	3300 2300 3300 2200
$Comp
L Connector_Generic:Conn_01x02 J3
U 1 1 5CE0DF87
P 3500 2300
F 0 "J3" H 3420 1975 50  0000 C CNN
F 1 "Conn_01x03" H 3420 2066 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 3500 2300 50  0001 C CNN
F 3 "~" H 3500 2300 50  0001 C CNN
F 4 "~" H 0   0   50  0001 C CNN "Manufacturer"
F 5 "~" H 0   0   50  0001 C CNN "Order #"
F 6 "~" H 0   0   50  0001 C CNN "Part #"
F 7 "~" H 0   0   50  0001 C CNN "Vendor"
	1    3500 2300
	-1   0    0    1   
$EndComp
Wire Wire Line
	3800 2200 3700 2200
Wire Wire Line
	3800 2200 3800 2300
Wire Wire Line
	3800 2400 3700 2400
Connection ~ 3800 2200
Wire Wire Line
	3700 2300 3800 2300
Connection ~ 3800 2300
Wire Wire Line
	3800 2300 3800 2400
Text Notes 7400 1200 0    197  ~ 39
TO DO:
Text Notes 7500 1400 0    98   ~ 0
- Separate LED and Driver power supplies
$EndSCHEMATC
