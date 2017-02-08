#!/usr/bin/env python
import os
import sys
import subprocess
import time
import signal
from mpi4py import MPI
from Queue import Queue

def wait_timeout(proc, seconds,poll_interval=5):
    """Wait for a process to finish, or kill after timeout"""
    start = time.time()
    end = start + seconds
    interval = poll_interval

    while True:
        result = proc.poll()
        if result is not None:
            return result
        if time.time() >= end:
            print "Process timed out"
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM) 
        time.sleep(interval)
        


WORKTAG = 1
DIETAG = 0

class Work(object):
    def __init__(self, inp_file):
        # importat: sort by file size in decreasing order!
        #files.sort(key=lambda f: os.stat(f).st_size, reverse=True)
        q = Queue()
        with open(inp_file) as f:
            for line in f:
                line = line.strip('\n')
                q.put(line)
            self.work = q

    def get_next(self):
        if self.work.empty():
            return None
        return self.work.get()


def do_work(cmd,timeout):
    print cmd
    #proc = subprocess.Popen('sleep 10',shell=True,preexec_fn=os.setsid)
    proc = subprocess.Popen(cmd,shell=True,preexec_fn=os.setsid)
    print proc.pid
    wait_timeout(proc,timeout)
    return (0)


def process_result(basePath,pdb_id):
    print "MASTER result :",pdb_id
    cmd="%s/grep_value.sh %s"%( basePath,pdb_id)
    print cmd
    proc = subprocess.Popen(cmd,shell=True,preexec_fn=os.setsid)
    wait_timeout(proc,30,1)
    #os.system(cmd)


def master(comm,list_of_models_file,work_dir,basePath):
    
    num_procs = comm.Get_size()
    status = MPI.Status()
    print "MASTER process",num_procs
    # generate work queue
    wq = Work(list_of_models_file)
    results_dir=work_dir +"/results"
    if not os.path.isdir(results_dir):
        os.mkdir(results_dir)
    send_cnt = 0
    recv_cnt = 0
    # Seed the slaves, send one unit of work to each slave (rank)
    for rank in xrange(1, num_procs):
        work = wq.get_next()
        if not work: break
        comm.send(work, dest=rank, tag=WORKTAG)
        send_cnt += 1

    # Loop over getting new work requests until there is no more work to be done
    while True:
        work = wq.get_next()
        if not work: break

        # Receive results from a slave
        pdb_id = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        recv_cnt += 1
        process_result(basePath,pdb_id)

        # Send the slave a new work unit
        comm.send(work, dest=status.Get_source(), tag=WORKTAG)
        send_cnt += 1

    # No more work to be done, receive all outstanding results from slaves
    for rank in xrange(1, num_procs):
        if send_cnt == recv_cnt : break
        pdb_id = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        recv_cnt += 1
        process_result(basePath,pdb_id)

    # Tell all the slaves to exit by sending an empty message with DIETAG
    for rank in xrange(1, num_procs):
        comm.send(0, dest=rank, tag=DIETAG)
    print "MASTER process DONE"


def slave(comm,basePath,work_dir,diffraction_dataset,pdb_path,timeout):
    my_rank = comm.Get_rank()
    status = MPI.Status()
    print "SLAVE PROCESS",my_rank
    while True:
        # Receive a message from the master
        work = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)

        # Check the tag of the received message
        if status.Get_tag() == DIETAG:
            print "SLAVE DIETAG recieved",my_rank
            break 

        # Do the work
        print "SLAVE PROCESS WORK start:",my_rank,work
        cmd="%s/function.sh %s %s %s %s"%( basePath,work,work_dir,diffraction_dataset,pdb_path)
        result = do_work(cmd,timeout)
        print "SLAVE PROCESS WORK end:",my_rank,work
        # Send the result back
        comm.send(work, dest=0, tag=0)


def main():
    import sys
    import argparse
    

    parser = argparse.ArgumentParser(description="A tool to carry out molecular replacement")
    parser.add_argument('-i', dest="diffraction_dataset",required = True,help="Input scaled and merged diffraction dataset, in either MTZ or SCALA format")
    parser.add_argument('-wd', dest="work_dir",required = True,help="Working Directory - where all the pdb and structure factor files are written")
    parser.add_argument('-pdb', dest="pdb_dir",required = True,help="Path to processed poly alanine PDB models")
    parser.add_argument('-timeout', dest="timeout",type=int,default=1800,help="Time out in secs to kill individual jobs")
    args = parser.parse_args()
    basePath = os.path.dirname(os.path.realpath(__file__))
    #print basePath
    work_dir = os.path.abspath(args.work_dir)
    if not os.path.isdir(work_dir):    
        print "Path to work dir does not exist :",work_dir
        exit (1)
    pdb_path = os.path.abspath(args.pdb_dir)
    if not os.path.isdir(pdb_path):
            print "ERROR: Path to PDB dir does not exist :",pdb_path
            exit (1)
    if not os.path.isfile(pdb_path+'/list_of_phasing_models.txt'):
            print "ERROR: Path to list of phasing models does not exist :",pdb_path+'/list_of_phasing_models.txt'
            exit (1)
            
    diffraction_dataset = os.path.abspath(args.diffraction_dataset)
    
    if not os.path.isfile(diffraction_dataset):
            print "ERROR: Diffraction file does not exist :",diffraction_dataset
            exit (1)

#    if not which("phenix.phaser") :
#        print "ERROR: Program 'phenix.phaser' not found. Please check the installation and set PATH variable appropriately. Please refer README.txt."
#        exit (1)

    #print pdb_path
    #print jobs_in_parallel
    #print time_out
    try :
        os.chdir(args.work_dir)
    except OSError, e :
        print "ERROR: Could not set workdir to :",args.work_dir,e.strerror
        exit (1)
        
    
    
    comm = MPI.COMM_WORLD
    my_rank = comm.Get_rank()
    my_name = MPI.Get_processor_name()
    #comm.Barrier()
    #start = MPI.Wtime()
    if my_rank == 0:
        master(comm,pdb_path+'/list_of_phasing_models.txt',work_dir,basePath)
    else:
        slave(comm,basePath,work_dir,diffraction_dataset,pdb_path,args.timeout)

    #comm.Barrier()
    #end = MPI.Wtime()
    #print 'time:', end - start


if __name__ == '__main__':
    main()
