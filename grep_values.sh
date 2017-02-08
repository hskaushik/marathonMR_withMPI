#!/bin/sh

#local variables
PHASERPDB=${1}.1.pdb

cd results
#Read Phaser and grep it
#echo "Template_pdbid,LLG_score,TFZ_score"
if [ -f "$PHASERPDB" ]
then
    
    title=${1}
    LLG=`grep Log-Likelihood ${PHASERPDB} | awk '{print $4}'`
    TFZ=`grep TFZ ${PHASERPDB} | awk '{print $3}'| cut -d"=" -f2`
    echo "$title,$LLG,$TFZ" >> ../collated_results.csv
fi
