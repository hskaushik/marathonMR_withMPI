#!/bin/sh

#local variables
scopID=${1}
wd=${2}
mtz=${3}
pdb_path=${4}

bpath=`dirname $0`
template=$bpath/template.eff
#echo ${scopID}


cd ${wd}/results

poly_ala=${pdb_path}/${scopID}_polyala.pdb
#cp $template ${scopID}.eff
#sed -i "s|\$SCOP_ID|${scopID}|g" $scopID.eff
#sed -i "s|\$PDB_POLY_ALA|${poly_ala}|g" $scopID.eff
#sed -i "s|\$RESULTS_DIR|${wd}/results|g"  $scopID.eff

##job start time
startTime=`date`

#phenix.phaser ${scopID}_output.eff
phenix.phaser $poly_ala $mtz model_rmsd=2 search_copies=1 root=${scopID} > /dev/null

finishTime=`date`
echo "${scopID} started at ${startTime} and completed at ${finishTime}..." >> ${wd}/marathonMR_timeline.log

