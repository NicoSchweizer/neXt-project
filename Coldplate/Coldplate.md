## Coldplate
This is a log of receiving, testing I did and problems I may have encountered with the coldplate.

### Design and manufacturing
Santiago produced a coldplate by milling channels into two opposing aluminum-plates and then gluing them together with a special glue.\
The channels are designed to allow for mostly laminar flow of the coolant, which should prevent further vibrations near the VECSEL.\
The channels look something like this:

<img src="./fig/Sketch_coldplate.jpeg" alt="Sketch of coldplate channels" width="300"/>

### Receiving and testing
The coldplate was received on the 17th of June, and we immediately started testing it to see if it was water tight.\
We connected the coldplate to a spare chiller from the lab and ran it for a few hours. We did not observe any leaks.\
Out of curiosity I put my ear to the coldplate to see if I could hear any vibrations, and at pump speeds *high* could hear a continuous sound.\
When changing the pump speed to *low* the sound was not audible anymore.

### Sound measurements
To get a better idea and maybe quantify my observations, I decided to do some sound measurements. I used a similar setup as seen in the [Baseplate section](../Baseplate/sub/Sound_in_Lab.md).\
The setup looks like this:

<img src="./fig/Picture_setup.jpg" alt="Picture of sound measurement setup" width="300"/>

<img src="./fig/Picture_phone.jpg" alt="Picture of phone used for sound measurement" width="300"/>

I did 3 measurements, one with pump speed *high*, one with pump speed *low* and one with the pump turned off but the chiller still on.\
The results are shown in the following figure:

<img src="./fig/FFT_coldplate_noise.png" alt="FFT of sound measurements" width="600"/>

*This plot shows the FFT of the recorded audio from 3 different conditions: pump speed high, pump speed low and pump off. Each measurement took 10 min. The x-axis represents the frequency in Hz, while the y-axis represents the absolute amplitude.*

The plot indicates, that there is a significant increase in amplitude for some frequencies but also the reverse at different ones.\
This leads us to the problem with these measurements. They were taken from a phone, which might introduce some uncontrollable processing of the audio. This might explain the increase for some of the frequencies when the pump is off.\
The phone might for example set its absolute amplitude in reference to the current ambient noise, which is different for each measurement.

I still believe the measurements show something interesting, to emphasize this, I tried to subtract the background noise (*pump off*).

$\text{FFT}_{\text{high}}^\text{reduced} = \text{FFT}_{\text{high}} - \text{FFT}_{\text{off}}$

*Same for $\text{FFT}_{\text{low}}^\text{reduced}$.\
Negative values as a result of high amplitude in the *off* measurement are removed.*

The results of this are shown in the following figure:

<img src="./fig/FFT_coldplate_noise_peaks.png" alt="FFT of sound measurements with background noise subtracted" width="600"/>

*This plot shows the reduced FFT of the recorded audio from 2 different conditions: pump speed high and pump speed low. Each measurement took 10 min. The x-axis represents the frequency in Hz, while the y-axis represents the absolute amplitude.*

Here we can clearly see that the frequency peak at 238 Hz is significantly reduced by lowering the pump speed. This is probably the frequency I noticed when putting my ear to the coldplate.\
There are still some peaks in both spectra, that have a significant amplitude, but their origin is still unknown.\
For the moment I can't improve the measurements, since I don't know how my phone processes the audio and since this isn't the final setup.\
Adding longer hoses might attenuate some of the frequencies, for this test I used short hoses with a length of below 1 m each.

### Conclusion
The coldplate seems to be water tight and does not show any leaks.\
There is a significant sound at a frequency of 238 Hz when the pump is running at high speed, which is significantly reduced when lowering the pump speed.\
I'm hoping to reduce the sound further by adding longer hoses in the final setup.