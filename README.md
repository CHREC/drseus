# DrSEUs
## (D)ynamic (r)obust (S)ingle (E)vent (U)pset (s)imulator

Fault injection framework and application for performing CPU fault injection on:

* P2020RDB (Using BDI3000 JTAG debugger)
* ZedBoard (Using BDI3000 or Integrated JTAG debugger)
* Simics simulation of P2020RDB
* Simics simulation of CoreTile Express A9x4 (Only two cores simulated)

DrSEUs Terminology:

* Campaign: contains gold execution run of target application without fault injections that is used for comparison with one or more iterations
* Iteration: monitored execution run of target application with one or more injections
* Injection: single bit flip of randomly selected register or TLB entry

Run drseus.py --help for usage information

Usage Example:

* drseus.py -s -C 1000 -c ppc_fi_2d_conv_fft_omp -a "lena.bmp out.bmp" -f lena.bmp -o out.bmp
    * Creates a Simics fault-injection campaign with 1000 checkpoints
    * Sends binary file "ppc_fi_2d_conv_fft_omp" and input file "lena.bmp" to the device under test
    * Runs "ppc_fi_2d_conv_fft_omp lena.bmp out.bmp" on the device under test
    * Checks for output file "out.bmp"
* drseus.py -i -n 100 -p 8
    * Performs 100 injection iterations using 8 processes
* drseus.py -l
    * Starts log server
    * Navigate to http://localhost:8000 in your web browser
