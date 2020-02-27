import os
import subprocess,shlex,shutil
import sys,getopt
import glob
from multiprocessing import Pool
import tqdm 

# Miriad Multicore Cleaner
# Work through making images from .uvaver miriad files
# J. Livingston 10 Oct 2019
# Modified from RC polarimetry script from 10 August 2016 and N. McClure-Griffiths 10 Dec 2018
# WORKS FOR PYTHON 3

def get_noise(source,freq,chan):
    '''
    Generates noise cutoff from stokes v image to use for cleaning
    
    Auto Inputs:
    args = source,freq,chan
    
    Outputs:
    float that will be used as cutoff for cleaning process
    '''
    from astropy.io import fits
    import numpy as np
    noise=-100.0
    stokes='v'
    maps = f'{source}.{freq}.{chan}.{stokes}.map'
    log_file = 'error_noise.log'
    if os.path.isdir(maps):
        fitsfile = f'{maps}.fits'
        cmd = f'fits in={maps} out={fitsfile} op=xyout '
        #print(cmd)
        args=shlex.split(cmd)
        with open(log_file,'a') as log:
            p=subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Print the output
        #for line in p.stdout:
        #    print(line)
            p.wait()
    # Open the FITS file
        hdul = fits.open(fitsfile)
        data = hdul[0].data
        noise=np.std(data)/2
        #print(f"RMS = {noise}")
        os.remove(fitsfile)
    return noise


def clean_images(args):
    '''
    Takes inputs and runs miriad invert from command line producing dirty maps and beams
    
    User Inputs:
    args = chan, source, freq, region, nit
    
    Outputs:
    cleans dirty maps and produces fits images for each stokes parameter
    '''
    chan, source, freq, region, nit = args
    stokespars = ['i','q','u','v']
    # Cycle over the channels

    # Gets noise for clean cutoff from stokes v
    cut_noise = get_noise(source,freq,chan)

    # Create names for files
    for stokes in stokespars:
        mod = f'{source}.{freq}.{chan:04d}.{stokes}.mod'
        cln = f'{source}.{freq}.{chan:04d}.{stokes}.cln'
        pbcorr = f'{source}.{freq}.{chan:04d}.{stokes}.pbcorr'
        maps = f'{source}.{freq}.{chan:04d}.{stokes}.map'
        beam = f'{source}.{freq}.{chan:04d}.beam'
        rms = f'{source}.{freq}.{chan:04d}.{stokes}.rms'
        outfile = f'{source}.{freq}.{chan:04d}.{stokes}.cln.fits'
        log_file = 'error_cln.log'
    # Check that the map exists before trying
        if not os.path.isdir(maps) and not os.path.isdir(beam):
            #print(f"Map {maps} does not exist")
            pass
        else:
    # Run through clean
            cmd = f'clean map={maps} beam={beam} region=percentage({region}) niters={nit} cutoff={cut_noise} out={mod}'
            #print(cmd)
            args=shlex.split(cmd)  # Splits the cmd into a string for subprocess
            with open(log_file,'a') as log:
                p=subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Print the output
            #for line in p.stdout:
            #     print(line)
                p.wait()
     # Restor the images
            cmd = f'restor map={maps} beam={beam} model={mod} out={pbcorr}'
            #print(cmd)
            args=shlex.split(cmd)
            with open(log_file,'a') as log:
                p=subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         #Print the output
            #for line in p.stdout:
                # print(line)
                p.wait()

#         # Primary Beam Correction
            cmd = f'linmos in={pbcorr} out={cln}'
            #print(cmd)
            args=shlex.split(cmd)
            with open(log_file,'a') as log:
                p=subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         #Print the output
            #for line in p.stdout:
            #      print(line)
                p.wait()

#         # Copy missing RMS after primary beam correction
            cmd = f'gethd in={pbcorr}/rms log={rms}'
            #print(cmd)
            args=shlex.split(cmd)
            with open(log_file,'a') as log:
                p=subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         #Print the output
            #for line in p.stdout:
            #      print(line)
                p.wait()

#         # Paste missing RMS onto primary beam correction
            cmd = f'puthd in={cln}/rms value=@{rms}'
            #print(cmd)
            args=shlex.split(cmd)
            with open(log_file,'a') as log:
                p=subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         #Print the output
            #for line in p.stdout:
            #      print(line)
                p.wait()

#         #convert to fits
            cmd =f'fits in={cln} out={outfile} op=xyout'
            #print(cmd)
            args=shlex.split(cmd)  # Splits the cmd into a string for subprocess
            with open(log_file,'a') as log:
                p=subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=log)
      # Print the output
            #for line in p.stdout:
            #      print(line)
                p.wait()

    return



def main(pool, args):

    inputs = [[i, args.source, args.freq, args.region, args.n_iters] for i in range(args.start_chan, args.end_chan, args.step_size)]

    #Runs each chunk of freq on new processor
    print('Cleaning Images')
    for _ in tqdm.tqdm(pool.imap(clean_images, inputs),total=len(inputs)):
        pass
    pool.close()


if __name__ == "__main__":
    import argparse
    import schwimmbad


    # Help string to be shown using the -h option
    descStr = """
    Takes dirty maps produced using MM_inverter.py and uses miriad clean, linmos, 
    and restor to generate beam corrected clean images.
    """

    # Parse the command line options
    parser = argparse.ArgumentParser(description=descStr,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-s", dest="source",
                        type=str, help="Source name in RA-DEC convention from miriad")

    parser.add_argument("-f", dest="freq", type=int, default=2100,
                        help="centre frequency in MHz")

    parser.add_argument("-1", dest="start_chan", type=int, default=1,
                        help="starting channel number")

    parser.add_argument("-2", dest="end_chan", type=int, default=1500,
                        help="final channel number")

    parser.add_argument("-d", dest="step_size", type=int, default=5,
                        help="channel step_size for images")

    parser.add_argument("-i", dest="n_iters", type=int, default=1000,
                        help="number of iterations to clean")

    parser.add_argument("-r", dest="region", type=float, default=95,
                        help="region (percentage) to clean as percentage of image")



    group = parser.add_mutually_exclusive_group()

    group.add_argument("--ncores", dest="n_cores", default=1,
                       type=int, help="Number of processes (uses multiprocessing).")
    group.add_argument("--mpi", dest="mpi", default=False,
                       action="store_true", help="Run with MPI.")


    args = parser.parse_args()
    pool = schwimmbad.choose_pool(mpi=args.mpi, processes=args.n_cores)
    #pool = schwimmbad.SerialPool()

    if args.mpi:
        if not pool.is_master():
            pool.wait()
            sys.exit(0)


    # Clean the images
    main(pool, args)
