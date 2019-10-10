import os
import subprocess,shlex,shutil
import sys,getopt
import glob
from multiprocessing import Pool

# Miriad Multicore Cleaner
# Work through making images from .uvaver miriad files
# J. Livingston 10 Oct 2019
# Modified from RC polarimetry script from 10 August 2016 and N. McClure-Griffiths 10 Dec 2018
# WORKS FOR PYTHON 3

def inputs(argv):
    '''
    Takes inputs from command line. 
            Inputs:
            -f <freq> = centre frequency in MHz
            -s <source> = source name in RA-DEC convention from miriad
            -1 <start_chan> = starting channel number
            -2 <end_chan> = final channel number
            -d <step_size> = channel step_size for images
            -i <n_iters> = number of iterations to clean
            -r <region> = region to clean as percentage of image
            -n <core_num> = number of cores to run task on
    '''
    freq = ''
    mfs = False
    clean = False
    try:
        opts, args = getopt.getopt(argv,"hcf:s:1:2:d:i:r:n:",["freq=","source=","start_chan=",
                                                          "end_chan=","step_size=","n_iters=",
                                                            "region=",
                                                          ,"core_num="])
        print(opts,args)
    except getopt.GetoptError:
        print('input error, check format of input parameters')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('''
            Takes inputs from command line. 
            Inputs:
            -f <freq> = centre frequency in MHz
            -s <source> = source name in RA-DEC convention from miriad
            -1 <start_chan> = starting channel number
            -2 <end_chan> = final channel number
            -d <step_size> = channel step_size for images
            -i <n_iters> = number of iterations to clean
            -r <region> = region to clean as percentage of image
            -n <core_num> = number of cores to run task on
            ''')
            
            sys.exit()
        elif opt in ("-f", "--freq"):
            freq = arg
        elif opt in ("-1", "--start_chan"):
            schan = int(arg)
        elif opt in ("-2", "--end_chan"):
            echan = int(arg)
        elif opt in ("-s", "--source"):
            source = arg
        elif opt in ("-d", "--step_size"):
            step = int(arg)
        elif opt in ("-i", "--n_iters"):
            nit = int(arg)
        elif opt in ("-r", "--region"):
            region = int(arg)
        elif opt in ("-n", "--core_num"):
            core = int(arg)
    return freq,source,schan,echan,step,nit,region,core


def get_noise(source,freq,chan):
    from astropy.io import fits
    import numpy as np
    noise=-100.0
    stokes='v'
    maps = f'{source}.{freq}.{chan}.{stokes}.map'
    if os.path.isdir(maps):
        fitsfile = f'{maps}.fits'
        cmd = f'fits in={maps} out={fitsfile} op=xyout ' % (map,fitsfile)
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
        print(f"RMS = {noise}")
        os.remove(fitsfile)
    return noise

# Get the inputs before calling next function
freq,source,schan,echan,step,nit,core=inputs(sys.argv[1:])

def clean_images(t):
    stokespars = ['i','q','u','v']
    # Cycle over the channels
    start=1+int((schan-echan)/core)*t
    end=int((echan-schan)/core)*(t+1)
    
    for chan in range(start,end,step):
        cut_noise= get_noise(source,freq,chan)
 
        for stokes in stokespars: 
            mod = f'{source}.{freq}.{chan:04d}.{stokes}.mod' 
            cln = f'{source}.{freq}.{chan:04d}.{stokes}.cln' 
            pbcorr = f'{source}.{freq}.{chan:04d}.{stokes}.pbcorr' 
            maps = f'{source}.{freq}.{chan:04d}.{stokes}.map' 
            beam = f'{source}.{freq}.{chan:04d}.{stokes}am'
            rms = f'{source}.{freq}.{chan:04d}.{stokes}.rms' 
            outfile = f'{source}.{freq}.{chan:04d}.{stokes}.cln.fits' 
            
        # Check that the map exists before trying
            if not os.path.isdir(maps) and not os.path.isdir(beam):
                print(f"Map {maps} does not exist")
            else:
        # Run through first clean of central source
                cmd = f'clean map={maps} beam={beam} region=percentage({region}) niters={nit} cutoff={cut_noise} out={mod}'
                print(cmd)
                args=shlex.split(cmd)  # Splits the cmd into a string for subprocess
                p=subprocess.Popen(args, stdout=subprocess.PIPE)
        # Print the output
                for line in p.stdout:
                    print(line)
                p.wait()
        # Restor the images
                cmd =f'restor map={maps} beam={beam} model={mod} out={pbcorr}'
                print(cmd)
                args=shlex.split(cmd)
                p=subprocess.Popen(args, stdout=subprocess.PIPE)     
        #Print the output
                for line in p.stdout:
                    print(line)
                p.wait()  
                
        # Primary Beam Correction
                cmd =f'linmos in={pbcorr} out={cln}'
                print(cmd)
                args=shlex.split(cmd)
                p=subprocess.Popen(args, stdout=subprocess.PIPE)     
        #Print the output
                for line in p.stdout:
                    print(line)
                p.wait() 
                
        # Copy missing RMS after primary beam correction 
                cmd =f'gethd in={pbcorr}/rms log={rms}'
                print(cmd)
                args=shlex.split(cmd)
                p=subprocess.Popen(args, stdout=subprocess.PIPE)     
        #Print the output
                for line in p.stdout:
                    print(line)
                p.wait()  
                
        # Paste missing RMS onto primary beam correction
                cmd =f'puthd in={cln}/rms value=@{rms}'
                print(cmd)
                args=shlex.split(cmd)
                p=subprocess.Popen(args, stdout=subprocess.PIPE)     
        #Print the output
                for line in p.stdout:
                    print(line)
                p.wait()
                
        #convert to fits
                cmd =f'fits in={cln} out={outfile} op=xyout'
                print(cmd)
                args=shlex.split(cmd)  # Splits the cmd into a string for subprocess
                p=subprocess.Popen(args, stdout=subprocess.PIPE)
                    # Print the output
                for line in p.stdout:
                    print(line)
                p.wait()
                
        #delete dirty maps, beams, uncorrected clean images, and models 
                try:
                    shutil.rmtree(maps)
                except OSError:
                    print(f"Unable to remove file {maps}")
                try:
                    shutil.rmtree(pbcorr)
                except OSError:
                    print(f"Unable to remove file {pbcorr}")
                try:
                    shutil.rmtree(beam)
                except OSError:
                    print(f"Unable to remove file {beam}")
                try:
                    shutil.rmtree(mod)
                except OSError:
                    print(f"Unable to remove file {mod}")
    return

#Makes list of processors
pool = Pool(processes=core)
#Runs each chunk of freq on new processor 
pool.map(clean_images, list(range(0,core,1)))
