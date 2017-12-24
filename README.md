# Echolocation
An acoustic echolocation sensor to measure the distance between a smartphone and a reflector. 

The general idea is to extract the channel impulse response of the system continuously and calculate the distance 
between line of sight channel and reflected peaks in CIR. The CIR is computed by continously transmitting sound signals of 
different frequencies and then implementing basic signal processing techniques. A laptop is used to transmit sound signals and 
a smartphone is used to process the received signals and calculate the distance. 

