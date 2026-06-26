## Wavemeter Measurements
After our *Pizza-Seminar* and the discussion that followed, I decided to do some more wavemeter measurements.\
This time, I tried setting the pump current to 23 A in hopes of getting slower thermal oscillations.\
The measurements were taken on 24.06.2026.

### Time-series
<img src="./fig/T_S_24-06_15-18.png" alt="Wavemeter Measurement" width="1100">

This is one of the full time series I took.\
Thanks to the higher pump current I could leave the exposure time of the wavemeter at a single value.\
The measurement took roughly 35 minutes, and there are some interesting features in the data.\
First of all there are lots of mode jumps in the data, which is not surprising since the temperature is still oscillating.\
One more interesting feature is that there are some prominent minima and maxima in the frequency data.\
For example, there are some minima at around 200 and 1200 seconds.

This made me look into the temperature data of TEC4 which at this point is the one closest to the GC.

<img src="./fig/TEC4_24-06_26.png" alt="TEC4 Temperature Measurement" width="1100">

Here we can also see an oscillation, with a very similar period to the frequency oscillation.\
This strengthens my suspicion, that the mode jumps are mostly caused by the temperature of the GC oscillating.

### Segmentation
To get a better understanding of the frequency stability and since I only care about the frequency stability in one mode, I segmented the data to only include one mode.\
I don't care about the frequency stability during mode jumps, as it is the goal to run the laser in one mode.

<img src="./fig/T_S_24-06_15-18_segments.png" alt="Segmented Wavemeter Measurement" width="1100">

Here I took the longest segment of the data, captured in one mode.\
The frequency distribution of this segment looks like this:

<img src="./fig/hist_24-06_15-18_segments.png" alt="Histogram of Frequency Distribution" width="600">

This shows a typical distribution as expected for a minimum in my time series.

### Allan Deviation
Using this segment, I calculated the allan deviation of the frequency and power.\
The results look like this:

<img src="./fig/AD_24-06_15-18_segments.png" alt="Allan Deviation of Frequency" width="600">
<img src="./fig/AD_pow_24-06_15-18_segments.png" alt="Allan Deviation of Power" width="600">

For the frequency we can see an allan deviation of around 150-500 kHz for timescales of 20-100 ms.\
I noticed that Tobi was using larger timescales in his thesis, so to have a better comparison:
* Tobi's results for 90-250 ms: $\sim$ 1.3 MHz
* My results for 90-250 ms: $\sim$ 0.5 - 1.5 MHz

I don't know if Tobi used the mean or median value for this timescale, but I think it is safe to say that my results are in line with his.

### Conclusion
The wavemeter measurements show that the frequency stability of the laser is in line with Tobi's results.\
The frequency stability is around 150-500 kHz for timescales of 20-100 ms.\
The power stability is around 0.1-0.3 mW for timescales of 20-100 ms.

One thing to notice:
**Since the time series used to calculate the allan deviation is the minimum of the frequency oscillation and not completely representative of the whole time series, this allan deviaiton is to be seen as a lower bound of the frequency stability.**