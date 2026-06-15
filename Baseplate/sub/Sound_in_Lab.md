## Sound in Lab

### Data acquisition
Using the microphone of my phone, I was able to record some audio directly to a ".WAV" file via a [Python script](../../../Sound%20in%20Lab/Record_to_WAV.py). 

* Sampling frequency
  * The highes sampling frequency my phone supported was 48kHz
* Recording duration
  * I recorded for 10 - 20 minutes

### Data analysis
The recorded audio files were analyzed using ```numpy.fft.fft``` to obtain the frequency spectrum.\
Then the peaks are identified using ```scipy.signal.find_peaks``` and plotted using.

#### Measurement 1 20-05-2026
![FFT of measurement 1](../fig/FFT_from_WAV.png)

<small>10 min. measurement</small>

On this day there were some problems with the scroll-pump which might have caused some peaks in the spectrum. \
The measurement was taken ontop of the optical table, where the VECSEL is mounted.

#### Measurement 2 12-06-2026
![FFT of measurement 2](../fig/FFT_from_WAV_2.png)

<small>20 min. measurement</small>

On this day there were fewer people in the lab and the scroll-pump was working normally again. \
The measurement was taken on the workbench.