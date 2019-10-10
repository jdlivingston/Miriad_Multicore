# Miriad_Multicore
---------------------
# This repo uses python to image miriad maps using mutliple cores
# It requires python 3 and the following python modules: os, subprocess, shlex, shutil, sys, getopt, glob, multiprocessing
--------------------

MM_inverter.py takes command line inputs and uses miriad invert 

MM_cleaner.py cleans dirty maps from MM_inverter.py using miriad clean and converts them into .fits images using miriad fits
