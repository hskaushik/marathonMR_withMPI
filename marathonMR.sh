#!/bin/sh
basePath=${1}
wd=${2}
mtz=${3}
pdb_path=${4}
jobs_in_parallel=${5}
time_out=${6}
PBS_NODEFILE=${7}

rm ${wd}/COMPLETED
touch ${wd}/INPROGRESS
chmod +x ${wd}/INPROGRESS

cat ${pdb_path}/list_of_phasing_models.txt | parallel -j ${jobs_in_parallel} --timeout ${time_out}  --sshloginfile $PBS_NODEFILE ${basePath}/function.sh {} ${wd} ${mtz} ${pdb_path}
cat ${pdb_path}/list_of_phasing_models.txt | parallel -j ${jobs_in_parallel}  --sshloginfile $PBS_NODEFILE ${basePath}/grep_values.sh {}
touch ${wd}/COMPLETED
chmod +x ${wd}/COMPLETED
rm ${wd}/INPROGRESS
echo "marathonMR COMPLETED all runs." >> ${wd}/marathonMR_timeline.log