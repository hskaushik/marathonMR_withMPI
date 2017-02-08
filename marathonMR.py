#!/usr/bin/env python
#import subprocess
import os
import ConfigParser
import time
import datetime

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

if __name__ == "__main__":
    import sys
    import argparse
    

    parser = argparse.ArgumentParser(description="A tool to carry out molecular replacement")
    parser.add_argument('-i', dest="diffraction_dataset",required = True,help="Input scaled and merged diffraction dataset, in either MTZ or SCALA format")
    parser.add_argument('-wd', dest="work_dir",required = True,help="Wimport datetimeorking Directory - where all the pdb and structure factor files are written")
    parser.add_argument('-pdb', dest="pdb_dir",required = True,help="Path to processed poly alanine PDB models")
    parser.add_argument('-j', dest="jobs_in_parallel",default='80%',help="Number of jobslots.Run up to N jobs in parallel.0 means as many as possible.Default is %(default)s which will use %(default)s of available CPU,with a minimum of 1 CPU core")
    parser.add_argument('-timeout', dest="time_out",type=int,default=600,help="Maximum allowed execution time for a given phaser job")
    parser.add_argument('-nodelist', dest="node_list",help="List of nodes in case of multi node cluster")
    args = parser.parse_args()
    basePath = os.path.dirname(os.path.realpath(__file__))
    print basePath
    work_dir = os.path.abspath(args.work_dir)
    if not os.path.isdir(work_dir):    
        print "Path to work dir does not exist :",work_dir
        print "Creating :",work_dir
        os.mkdir(work_dir)
    results_dir=args.work_dir +"/results"
    if not os.path.isdir(results_dir):
        os.mkdir(results_dir)
    pdb_path = os.path.abspath(args.pdb_dir)
    if not os.path.isdir(pdb_path):
            print "ERROR: Path to PDB dir does not exist :",pdb_path
            exit (1)
    if not os.path.isfile(pdb_path+'/list_of_phasing_models.txt'):
            print "ERROR: Path to list of phasing models does not exist :",pdb_path+'/list_of_phasing_models.txt'
            exit (1)
            
    diffraction_dataset = os.path.abspath(args.diffraction_dataset)
    
    marathon_log = work_dir + '/marathonMR_timeline.log'
    if os.path.isfile(marathon_log):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d%H:%M:%S')
        marathon_bkup_log = "%s/marathonMR_timeline_%s.log"%(work_dir,st)
        print "Marathon log file exists, backing up to :",marathon_bkup_log
        os.system("mv %s %s"%(marathon_log,marathon_bkup_log))
        
    collated_results = work_dir + '/collated_results.csv'
    if os.path.isfile(collated_results):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d%H:%M:%S')
        collated_results_bkup = "%s/collated_results_%s.csv"%(work_dir,st)
        print "Collated results exists, backing up to :",collated_results_bkup
        os.system("mv %s %s"%(collated_results,collated_results_bkup))
        
    if not os.path.isfile(diffraction_dataset):
            print "ERROR: Diffraction file does not exist :",diffraction_dataset
            exit (1)

    if not which("parallel") :
        print "ERROR: Program 'parallel' not found. Please check the installation and set PATH variable appropriately. Please refer README.txt."
        exit (1)

    if not which("phenix.phaser") :
        print "ERROR: Program 'phenix.phaser' not found. Please check the installation and set PATH variable appropriately. Please refer README.txt."
        exit (1)

    jobs_in_parallel = args.jobs_in_parallel
    time_out = args.time_out
    node_list = args.node_list    
    #print pdb_path
    #print jobs_in_parallel
    #print time_out
    try :
        os.chdir(args.work_dir)
    except OSError, e :
        print "ERROR: Could not set workdir to :",args.work_dir,e.strerror
        exit (1)
    
    try :
        cmd = "`%s/marathonMR.sh %s %s %s %s %s %s %s>/dev/null 2>&1` "%(basePath,basePath,work_dir,diffraction_dataset,pdb_path,jobs_in_parallel,time_out,node_list)
        #cmd = "`%s/marathonMR.sh %s %s %s %s %s %s %s` "%(basePath,basePath,work_dir,diffraction_dataset,pdb_path,jobs_in_parallel,time_out,node_list)
        #print cmd
        print "MarathanMR initiated in background!"
        print "Please check the log file marathonMR_timeline.log in :",work_dir
        print "An empty file called COMPLETED or INPROGRESS will be created in :",work_dir," to indicate status of marathonMR"
        os.system(cmd)
    except Exception, e:
        print "ERROR: Unable to invoke parallel on phaser jobs.Check if parallel is installed and locally available"
        exit (1)

        

    
        
