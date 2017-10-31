#!/bin/bash
# pmp - "Poor man's profiler" - Inspired by http://poormansprofiler.org/
# See also: http://dom.as/tag/gdb/

nsamples=$1
sleeptime=0.1 # seconds
pid=$2
outgdb=$3  # /tmp/out.gdb
outsvg=$4  # /tmp/out.svg
flamegraphpath=$5

# Sample stack traces:
for x in $(seq 1 $nsamples); do
    gdb -ex "set pagination 0" -ex "thread apply all bt" -batch -p $pid 2> /dev/null >> $outgdb
    if ! ((x % 5)); then
	cat $outgdb | $flamegraphpath/stackcollapse-gdb.pl | grep TTreePlayer::Process | $flamegraphpath/flamegraph.pl > $outsvg
	if [ $? -ne 0 ]; then
	    echo "Did you set the proper permissions for gdb? Try 'gdb -p <your_pid>' first"
	    break
	fi
    fi
    sleep $sleeptime
done
