import os
import subprocess,shlex,shutil
import sys,getopt
import glob

# Miriad Single Cleaner
# Work through cleaning single image from MM_single_inverter.py
# J. Livingston 23 Oct 2019
# Modified from RC polarimetry script from 10 August 2016 and N. McClure-Griffiths 10 Dec 2018
# WORKS FOR PYTHON 3


def clean_images(args):
    '''
    Cleans mfs dirty map generated from MM_single_inverter.py and converts to fits file
    
    User Inputs:
    args = source, freq, region, nit
    
    Outputs:
    cleans mfs dirty map and produces fits image for each stokes parameter
    '''
    source, freq, region, nit = args
    stokespars = ['i','q','u','v']
    # Cycle over the channels
    cut_noise = get_noise(source,freq)
    for stokes in stokespars[0:3]:  # Only clean I, Q, U
        mod = f'{source}.{freq}.{stokes}.mod'
        cln = f'{source}.{freq}.{stokes}.cln'
        maps = f'{source}.{freq}.{stokes}.map'
        beam = f'{source}.{freq}.beam' 
        fits = f'{source}.{freq}.{stokes}.single.fits'
        # Run through first clean of central source
        cmd = f'mfclean map={maps} beam={beam} region=percentage({region}) niters={nit} cutoff={cut_noise} out={mod}'
        print(cmd)
        args=shlex.split(cmd)  # Splits the cmd into a string for subprocess
        p=subprocess.Popen(args, stdout=subprocess.PIPE)
        # Print the output
        for line in p.stdout:
            print(line)
        p.wait()
        # Restor the images
        cmd = f'restor map={maps} beam={beam} model={mod} out={cln}'
        print(cmd)
        args=shlex.split(cmd)
        p=subprocess.Popen(args, stdout=subprocess.PIPE)
        for line in p.stdout:
            print(line)
        p.wait()
        
        # FITS convert
        cmd = f'fits in={cln} out={fits} op=xyout'
        print(cmd)
        args=shlex.split(cmd)
        p=subprocess.Popen(args, stdout=subprocess.PIPE)
        for line in p.stdout:
            print(line)
        p.wait()
    return

def get_noise(source,freq):
    from astropy.io import fits
    import numpy as np
    noise=-100.0
    stokes='v'
    maps = f'{source}.{freq}.{stokes}.map'
    if os.path.isdir(maps):
        fitsfile = f'{maps}.fits'
        cmd = f'fits in={maps} out={fitsfile} op=xyout '
        print(cmd)
        args=shlex.split(cmd)
        p=subprocess.Popen(args, stdout=subprocess.PIPE)
    # Print the output
        for line in p.stdout:
            print(line)
        p.wait()
    # Open the FITS file
        hdul = fits.open(fitsfile)
        data = hdul[0].data
        noise=np.std(data)/2
        print(f"Triple Noise {noise:f}")
        os.remove(fitsfile)
    return noise

def main(args):

    inputs = [args.source, args.freq, args.region, args.n_iters]
    clean_images(inputs)
    print('Done')

if __name__ == "__main__":
    import argparse


    # Help string to be shown using the -h option
    descStr = """
    Takes mfs dirty map and runs miriad clean from command line producing single mfs clean map

    """

    # Parse the command line options
    parser = argparse.ArgumentParser(description=descStr,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-s", dest="source",
                        type=str, help="Source name in RA-DEC convention from miriad")

    parser.add_argument("-f", dest="freq", type=int, default=2100,
                        help="centre frequency in MHz")

    parser.add_argument("-i", dest="n_iters", type=int, default=1000,
                        help="number of iterations to clean")

    parser.add_argument("-r", dest="region", type=float, default=95,
                        help="region (percentage) to clean as percentage of image")

    args = parser.parse_args()

    # Clean the images
    main(args)





