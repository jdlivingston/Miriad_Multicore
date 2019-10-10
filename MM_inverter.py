import os
import subprocess,shlex,shutil
import sys,getopt
import glob
from multiprocessing import Pool

# Miriad Multicore Inverter
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
            -b <field_size> = size of field in pixels 
            -n <core_num> = number of cores to run task on
    '''
    freq = ''
    mfs = False
    clean = False
    try:
        opts, args = getopt.getopt(argv,"hcf:s:1:2:d:b:n:",["freq=","source=","start_chan=",
                                                          "end_chan=","step_size=","field_size="
                                                          ,"core_num="])
        print(opts,args)
    except getopt.GetoptError:
        print('input error, check format')
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
            -b <field_size> = size of field in pixels 
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
        elif opt in ("-b", "--field_size"):
            field = int(arg)
        elif opt in ("-n", "--core_num"):
            core = int(arg)
    return freq,source,schan,echan,step,field,core

# Get the inputs before calling next function
freq,source,schan,echan,step,field,core=inputs(sys.argv[1:])

def grid_images(t):
    '''
    Takes inputs and runs miriad invert from command line producing dirty maps and beams
    
    User Inputs:
    t = core index
    
    Other Inputs:
    outputs from inputs function above
    
    Outputs:
    for each channel band produces dirty maps (.map) for each Stokes parameter and beam images
    '''
    #Get all uvaver files
    uvaver_locations=glob.glob(f'../*/*/{source}*.uvaver') #!only works for where my files are stored!
    var_strs=','.join(uvaver_locations)
    # make images for all sources in a directory
    stokespars = ['i','q','u','v']
    print(f'Loading in {var_strs}')
    
    # Cycle over the channels which are split for multicore
    start=1+int((schan-echan)/core)*t
    end=int((echan-schan)/core)*(t+1)
    
    for chan in range(start,end,step):
        im,qm,um,vm = [f'{source}.{freq}.{chan:04d}.{a}.map' for a in stokespars] 
        beam = f'{source}.{freq}.{chan:04d}.beam'
        maps=','.join([im,qm,um,vm])

    #Check if the maps have already been created
        if not os.path.isdir(im) and not os.path.isdir(beam):
    # Do the imaging
            chan_str = f'chan,{step},{chan}'
            stokes_str = ','.join(stokespars)
            cmd = f'invert vis={var_strs} map={maps} beam={beam} line={chan_str} imsize={field},{field} cell=1,1 robust=+0.6 stokes={stokes_str} options=double,mfs'
            print(cmd)
            args=shlex.split(cmd)
            p=subprocess.Popen(args, stdout=subprocess.PIPE)
            
    # Print the output
            for line in p.stdout:
               print(line)
            p.wait()
            
#Makes list of processors
pool = Pool(processes=core)
#Runs each chunk of freq on new processor 
pool.map(grid_images, list(range(0,core,1)))
