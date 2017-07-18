# DrSEUs
## The Dynamic Robust Single Event Upset Simulator, Created by Ed Carlisle IV

Fault injection framework and application for performing CPU fault injection on:

* P2020RDB (Using BDI3000 JTAG debugger)
* ZedBoard (Using BDI3000 or Integrated JTAG debugger)
* PYNQ (Using Integrated JTAG debugger)
* Simics simulation of P2020RDB
* Simics simulation of CoreTile Express A9x4 (Only two cores simulated)

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
