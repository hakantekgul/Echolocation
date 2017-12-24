import pyaudio
import wave
from scipy.io import wavfile
from scipy.fftpack import fft, fftfreq, ifft
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
import struct
from struct import pack
from math import cos, pi
import peakutils

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
RECORD_SECONDS = 0.5
WAVE_OUTPUT_FILENAME = "received.wav"
SPEED_OF_SOUND = 343 # m/s
MIN_DIST = 24
AVERAGE_NUM = 3

# Recreate the known preamble (the chirp)
wv = wave.open('transmitted.wav', 'w')
wv.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
maxVol=2**15-1.0 #maximum amplitude
wvData=b""
freq = 10200

for i in range(0, int(RATE*0.003)):
	wvData+=pack('h', round(maxVol*cos(i*2*pi*freq/RATE)))


wv.writeframes(wvData)
wv.close()

# Get the raw audio data of the chirp
fs, dataX = wavfile.read("transmitted.wav")

# plt.plot(dataX)
# plt.title('Chirp Signal')
# plt.show()

# Prepare to listen for the transmission
p = pyaudio.PyAudio()

lastChunk = []
currChunk = []

SPEAKERS = p.get_default_output_device_info()["hostApi"]

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_host_api_specific_stream_info=SPEAKERS)

# Listen, record, and process received data
try:
	print("Receiving")
	lastDistance = 0
	k = 1
	runningTotal = 0
	while True:

		frames = []
		for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
		    data = stream.read(CHUNK)
		    frames.append(data)
	
		# Write the received data to a wav file
		wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
		wf.setnchannels(CHANNELS)
		wf.setsampwidth(p.get_sample_size(FORMAT))
		wf.setframerate(RATE)
		wf.writeframes(b''.join(frames))
		wf.close()


		# Process the signal received at the smartphone on the computer 
		fs, dataY = wavfile.read(WAVE_OUTPUT_FILENAME)
		
		N = len(dataX) + len(dataY) - 1

		fftX = fft(dataX, n=N)
		freqs = fftfreq(N, 1/RATE)
		intensitiesX = abs(fftX)

		# plt.plot(freqs, intensitiesX)
		# plt.title('Chirp Signal Frequency')
		# plt.show()

		fftY = fft(dataY, n=N)
		freqs = fftfreq(N, 1/RATE)
		intensitiesY = abs(fftY)

		# plt.plot(dataY)
		# plt.title('Received Signal')
		# plt.show()

		# plt.plot(freqs, intensitiesY)
		# plt.title('Received Signal Frequency')
		# plt.show()

	
		# Get the channel in the frequency domain by dividing the FFT's
		hf = np.divide(fftY, fftX)
		intensity_hf = abs(hf)
		
		# plt.plot(freqs, intensity_hf)
		# plt.title('Channel Frequency Response')
		# plt.show()

		# Get the channel impulse response by taking an IFFT
		ht = np.abs(ifft(hf))

		times = np.linspace(0, len(hf)/RATE, len(hf))

		peaks = peakutils.indexes(ht, thres=0.5, min_dist=MIN_DIST)
		
		if len(peaks) < 2:
			continue

		# Find the closest two peaks in the CIR to get the time between
		# the LOS path and the reflected path
		peakTime = times[peaks][0]
		reflectedPeakTime = times[peaks][1]
		currPeakTime = times[peaks][1]
		for i in range(2,len(peaks)):
			tempPeakTime = times[peaks][i]
			if (tempPeakTime - currPeakTime) < (reflectedPeakTime - peakTime):
				peakTime = currPeakTime
				reflectedPeakTime = tempPeakTime
			
			currPeakTime = tempPeakTime

		# Get the time difference, and then the distance
		deltaTime = reflectedPeakTime - peakTime
		distance = (SPEED_OF_SOUND * deltaTime) / 2

		# Only update the estimated distance every AVERAGE_NUM readings
		# to improve stability
		if k % AVERAGE_NUM != 0:
			runningTotal += distance
			k += 1
			continue
		else:
			runningTotal += distance
			distance = runningTotal / AVERAGE_NUM
			runningTotal = 0
			k = 1


		# If the change in distance is too drastic, it is likely an error
		# and should be ignored
		if lastDistance == 0:
			lastDistance = distance
		elif distance > lastDistance + 2:
			continue
		else:
			lastDistance = distance

		print("Distance to Reflector: " + str(distance*100) + " centimeters")

		# plt.plot(times[peaks], ht[peaks], 'ro')
		# plt.plot(times, ht)
		# plt.title('Channel Impulse Response')
		# plt.show()

except KeyboardInterrupt:
	stream.stop_stream()
	stream.close()
	p.terminate()
