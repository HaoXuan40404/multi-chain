#!/bin/bash
    dirpath="$(cd "$(dirname "$0")" && pwd)"
    cd $dirpath
    curdir=$PWD
    node=$(basename ${curdir})
    ulimit -c unlimited
    weth_pid=`ps aux|grep "${curdir}/config.json"|grep -v grep|awk '{print $2}'`
    if [ ! -z $weth_pid ];then
        echo "${node} is running, pid is $weth_pid."
    else
        echo "start ${node} ..."
        chmod a+x ../fisco-bcos
        nohup ../fisco-bcos  --genesis ${curdir}/genesis.json  --config ${curdir}/config.json  >> ${curdir}/log/log 2>&1 &
    fi