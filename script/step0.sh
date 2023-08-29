#! /bin/bash

date=$(basename $(pwd))

reac_file_abs=$(ls -S ~/reac/reac-${date}-10*.pcap | head -n 1)
reac_file=$(basename ${reac_file_abs})

cat <<-EOF
date=${date}
reac_file=${reac_file}
reac_file_abs=${reac_file_abs}

EOF
