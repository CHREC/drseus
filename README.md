Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.

# DrSEUs
## The Dynamic Robust Single Event Upset Simulator, Created by Dr. Ed Carlisle IV

Fault injection framework and application for performing CPU fault injection on:

* P2020RDB (Using BDI3000 JTAG debugger)
* ZedBoard (Using BDI3000 or Integrated JTAG debugger)
* PYNQ (Using Integrated JTAG debugger)
* Simics simulation of P2020RDB
* Simics simulation of CoreTile Express A9x4 (Only two cores simulated)

Support for automatially power cycling devices is included using this device: https://dlidirect.com/products/web-power-switch-7

DrSEUs Terminology:

* Campaign: contains gold execution run of target application without fault injections that is used for comparison with one or more iterations
* Iteration: monitored execution run of target application with one or more injections
* Injection: single bit flip of randomly selected register or TLB entry

Run drseus.py --help for usage information

Use arguments in files by prefixing with "@", for example: "drseus.py @conf/sample/p2020"

Example:

* drseus.py new ppc_fi_2d_conv_fft_omp -s -a "lena.bmp out.bmp" -f lena.bmp -o out.bmp
    * Creates a Simics fault-injection campaign
    * Sends binary file "ppc_fi_2d_conv_fft_omp" and input file "lena.bmp" to the device under test
    * Runs "ppc_fi_2d_conv_fft_omp lena.bmp out.bmp" on the device under test
    * Checks for output file "out.bmp"
* drseus.py inject -n 100 -p 8
    * Performs 100 injection iterations using 8 processes
* drseus.py log
    * Starts log server
    * Navigate to http://localhost:8000 in your web browser

Before using DrSEUs for the first time, you must first run "scripts/install_dependencies.sh" then run "scripts/setup_environment.sh"

Adding support for new architectures:

* Create a new debugger that extends jtag class (use src/jtag/bdi.py or src/jtag/openocd.py as a guide)
* Define injection targets as json file (use src/targets/a9.json or src/targets/p2020.json as a guide)
    * Any modifications to the jtag.json or simics.json in src/targets/a9/ or src/targets/p2020/ requires running scripts/merge.py to regenerate src/targets/a9.json and src/targets/p2020.json as only these files are used by DrSEUs
    * If architecture does not require Simics or jtag specific behavior (e.g. only adding jtag support), only the top level "targets" dictionary is required to be defined
* Modify __init_\_() in src/fault_injectory.py to use your new debugger class
* In order to automatically detect USB devices, find_devices() in src/jtag/__init_\_.py will need to be modified to detect the corresponding VENDOR_ID and MODEL_ID
* In order for DrSEUs to automatically spawn child processes for injecting on multiple hardware devices in parallel (without invoking drseus.py for each device), support must be added to injection_campaign() in src/utilities.py
* Additional modifications for adding a new device to Simics:
    * Modify __init_\_() in src/simics/__init_\_.py to use the new board's name for the new architecture
    * Modify launch_simics() in src/simics/__init_\_.py to properly initialize the new device in Simics

## Installation for Debian-based systems

    * Run the install dependencies script
        ./scripts/install_dependencies.sh
        be sure to select no when prompted to install simics unless you have a license
    * Run the setup environment script
        ./scripts/setup_environment
    * Setup tftp server
        ./scripts/setup_tftp.sh
    * Make sure you have a cross-compiler for your desired architecture
        e.g. arm-linux-gnueabihf-gcc/g++
