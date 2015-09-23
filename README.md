# DrSEUs
## (D)ynamic (r)obust (S)ingle (E)vent (U)pset (s)imulator

Fault injection framework and application for performing CPU fault injection on:

* P2020RDB (Using BDI3000 JTAG debugger)
* ZedBoard (Using BDI3000 JTAG debugger)
* Simics simulation of P2020RDB
* Simics simulation of CoreTile Express A9x4 (Only two cores simulated)

DrSEUs Terminology:

* Campaign: contains gold execution run of target application without fault
            injections that is used for comparison with one or more iterations
* Iteration: monitored execution run of target application with one or more
             injections
* Injection: single bit flip of randomly selected register or TLB entry

Run drseus.py -h for usage information
