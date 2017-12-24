import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import wave
import struct
from struct import pack
from math import cos, pi
import random
import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
WAVE_OUTPUT_FILENAME = "chirp.wav"

# Generate wav file to transmit sound
wv = wave.open(WAVE_OUTPUT_FILENAME, 'w')
wv.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
maxVol=2**15-1.0 #maximum amplitude
wvData=b""
freq = 10200

# Load in samples from a cosine wave at frequency 10.2 kHz
for i in range(0, int(RATE*0.003)):
   wvData+=pack('h', round(maxVol*cos(i*2*pi*freq/RATE)))

  
wv.writeframes(wvData)
wv.close()

# Prepare to reopen the file for transmission
p = pyaudio.PyAudio()

# Define stream chunk    
chunkCount = 0
framesLeft = []
framesRight = []
starttime = time.time()

# Transmit the chirp
print("Transmitting")
try:
	while True:
		 
		wav = wave.open(r"stereo.wav","rb") 
		fs, dataX = wavfile.read("stereo.wav")

		stream = p.open(format = p.get_format_from_width(wav.getsampwidth()),  
		                channels = wav.getnchannels(),  
		                rate = wav.getframerate(),  
		                output = True)  
		# Read data  
		data = wav.readframes(CHUNK) 

		# Play stream  
		while data:  
			stream.write(data)
			data = wav.readframes(CHUNK)

		# Wait 100 ms before chirping again
		time.sleep(0.1 - ((time.time() - starttime) % 0.1))

except KeyboardInterrupt:

	stream.stop_stream()
	stream.close()

	p.terminate()
