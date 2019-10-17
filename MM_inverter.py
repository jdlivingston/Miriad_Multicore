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

def grid_images(args):
    '''
    Takes inputs and runs miriad invert from command line producing dirty maps and beams
    
    User Inputs:
    t = core index
    
    Other Inputs:
    outputs from inputs function above
    
    Outputs:
    for each channel band produces dirty maps (.map) for each Stokes parameter and beam images
    '''
    chan, step, source, freq, field = args
    #Get all uvaver files
    uvaver_locations=glob.glob(f'../../*/*/{source}*.uvaver') #!only works for where my files are stored!
    var_strs=','.join(uvaver_locations)
    # make images for all sources in a directory
    stokespars = ['i','q','u','v']
    print(f'Loading in {var_strs}')
    
    # Cycle over the channels which are split for multicore
   
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
            
def main(pool, args):

    inputs = [[i, args.step_size, args.source, args.freq, args.field_size] for i in range(args.start_chan, args.end_chan, args.step_size)]

    #Runs each chunk of freq on new processor
    pool.map(grid_images, inputs)
    pool.close()
    print('Done')


if __name__ == "__main__":
    import argparse
    import schwimmbad


    # Help string to be shown using the -h option
    descStr = """
    Takes uvaver files and runs miriad invert from command line producing dirty maps and beams
    """

    # Parse the command line options
    parser = argparse.ArgumentParser(description=descStr,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("source", metavar="source", nargs=1,
                        type=str, help="Source name in RA-DEC convention from miriad")

    parser.add_argument("-f", dest="freq", type=int, default=2100,
                        help="centre frequency in MHz")

    parser.add_argument("-1", dest="start_chan", type=int, default=1,
                        help="starting channel number")

    parser.add_argument("-2", dest="end_chan", type=int, default=1500,
                        help="final channel number")

    parser.add_argument("-d", dest="step_size", type=int, default=5,
                        help="channel step_size for images")

    parser.add_argument("-b", dest="field_size", type=int, default=2000,
                        help="size of field in pixels sqr")



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

