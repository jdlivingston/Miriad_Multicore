# Miriad_Multicore :frog:

* This repo uses python to image and clean miriad maps using mutliple cores. 
* MM_inverter.py takes command line inputs and uses miriad *invert* on uvaver files from miriad to create a series of dirty image maps and beams. 
* MM_cleaner.py cleans dirty maps from MM_inverter.py using miriad *clean*, beam corrects them using *linmos*, deconvolves them using *restor*, and converts them into .fits images using miriad *fits*.
* MM_single_inverter.py takes command line inputs and uses miriad *invert* to create a single mfs dirty map and beam.
* MM_single_cleaner.py cleans mfs dirty map from MM_single_inverter.py using miriad *clean*, deconvolves it using *restor*, and converts it into a .fits image using miriad *fits*.

- [miriad](https://www.atnf.csiro.au/computing/software/miriad/)
- [miriad paper](https://ui.adsabs.harvard.edu/abs/1995ASPC...77..433S)
