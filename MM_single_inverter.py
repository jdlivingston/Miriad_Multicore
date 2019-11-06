import os
import subprocess,shlex,shutil
import sys,getopt
import glob

# Miriad Single Inverter
# Work through making single image from .uvaver miriad files
# J. Livingston 23 Oct 2019
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
    source, freq, field = args
    #Get all uvaver files
    uvaver_locations=glob.glob(f'../../*/*/{source}*.uvaver') #!only works for where my files are stored!
    var_strs=','.join(uvaver_locations)
    # make images for all sources in a directory
    stokespars = ['i','q','u','v']
    
    # Cycle over the channels
    im,qm,um,vm = [f'{source}.{freq}.{a}.map' for a in stokespars] 
    beam = f'{source}.{freq}.beam'
    maps=','.join([im,qm,um,vm])

    #Check if the maps have already been created
    if not os.path.isdir(im) and not os.path.isdir(beam):
    # Do the imaging
            stokes_str = ','.join(stokespars)
            cmd =f'invert vis={var_strs} map={maps} beam={beam} imsize={field},{field} cell=1,1 robust=+0.6 stokes={stokes_str} options=double,sdb,mfs'
            print(cmd)
            args=shlex.split(cmd)
            p=subprocess.Popen(args, stdout=subprocess.PIPE)
            
    # Print the output
            for line in p.stdout:
               print(line)
            p.wait()
    return

def main(args):

    inputs = [args.source, args.freq, args.field_size]

    #Runs each chunk of freq on new processor
    grid_images(inputs)
    print('Done')
    
if __name__ == "__main__":
    import argparse
    
    # Help string to be shown using the -h option
    descStr = """
    Takes uvaver files and runs miriad invert from command line producing single mfs dirty map and beam
    """

    # Parse the command line options
    parser = argparse.ArgumentParser(description=descStr,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-s", dest="source",
                        type=str, help="Source name in RA-DEC convention from miriad")

    parser.add_argument("-f", dest="freq", type=int, default=2100,
                        help="centre frequency in MHz")

    parser.add_argument("-b", dest="field_size", type=int, default=2000,
                        help="size of field in pixels sqr")

    args = parser.parse_args()

    # Create the images
    main(args)

