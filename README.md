# Miriad_Multicore

* This repo uses python to image and clean miriad maps using mutliple cores. 
* MM_inverter.py takes command line inputs and uses miriad *invert* on uvaver files from miriad. 
* MM_cleaner.py cleans dirty maps from MM_inverter.py using miriad *clean* and converts them into .fits images using miriad *fits* and *restor*.
