#!/bin/bash
#copy_module
function copy_module()
{
    local package_config=$1
    local ansible_src=$2
    local ansible_dest=$3
    ansible ${package_config} -m synchronize -a "src=${ansible_src} dest=${ansible_dest}"
}

###unarchive_module###
function unarchive_module()
{
    local package_config=$1
    local ansible_src=$2
    local ansible_dest=$3
    ansible ${package_config} -m unarchive -a "src=${ansible_src} dest=${ansible_dest}, mode=0755 copy=yes"

}

###start_module###
function start_module()
{
    local package_config=$1
    local start_path=$2
    ansible ${package_config} -m shell -a "bash ${start_path}/start.sh"
}

###stop_module###
function stop_module()
{
    local package_config=$1
    local stop_path=$2
    ansible ${package_config} -m shell -a "bash ${stop_path}/stop.sh"
}

###mkdir_module###
function mkdir_module()
{
    local package_config=$1
    local mkdir_path=$2
    ansible ${package_config} -m file -a "path=${mkdir_path} state=directory mode=0755"
}
###check_module###
function check_module()
{
    local package_config=$1
    local check_path=$2
    ansible ${package_config} -m shell -a "bash  ${check_path}/check.sh"
}
###diagnose_module###
function diagnose_module()
{
    local package_config=$1
    local diagnose_path=$2
    ansible ${package_config} -m shell -a "bash  ${diagnose_path}/diagnose.sh"
}

###register_module###
function register_module()
{
    local package_config=$1
    local register_path=$2
    local index=$3
    ansible ${package_config} -m shell -a "bash  ${register_path}/register.sh ${index}"
}

###unregister_module###
function unregister_module()
{
    local package_config=$1
    local unregister_path=$2
    local index=$3
    ansible ${package_config} -m shell -a "bash  ${unregister_path}/unregister.sh ${index}"
}

###telnet_module###
function telnet_module()
{
    local package_config=$1
    local msg=$2
    ansible ${package_config} -m shell -a "echo $msg" 
}

###env_check### ansible远程调用检查目标服务器的操作系统版本;依赖项;
function env_check_module()
{
    local package_config=$1
    local check_path=$2
    # ansible ${package_config} -m script -a "${check_path}/scripts/tools/os_check.sh" -s
    ansible ${package_config} -m script -a "${check_path}/scripts/tools/deps.sh all" -s
    #ansible ${package_config} -m script -a "${check_path}/scripts/tools/os_check.sh && bash  ${check_path}/scripts/tools/deps_install.sh && bash  ${check_path}/scripts/tools/deps_check.sh "
}

###cmd_module###
function cmd_module()
{
    for arg in $@
    do 
        if [ "${arg}" = "$1" ];then
            msg=$msg
        else
            msg=$msg' '${arg}
    fi
    done
    local package_config=$1

    if [ -f $msg 2> /dev/null ];then
        ansible ${package_config} -m script -a "$msg"
    else
        ansible ${package_config} -m shell -a "$msg"
    fi
}


###file_module####
function file_module()
{
    local package_config=$1
    local ansible_src=$2
    local ansible_dest=$3
    ansible ${package_config} -m synchronize -a "src=${ansible_src} dest=${ansible_dest}"
}

case $1 in
    copy) copy_module $2 $3 $4;;
    unarchive) unarchive_module $2 $3 $4;;
    start) start_module $2 $3;;
    stop) stop_module $2 $3;;
    register) register_module $2 $3 $4;;
    unregister) unregister_module $2 $3 $4;;
    mkdir) mkdir_module $2 $3;;
    check) check_module $2 $3;;
    diagnose) diagnose_module $2 $3;;
    env_check) env_check_module $2 $3;;
    telnet) telnet_module $2 $3;;
    cmd) cmd_module $2 $3;;
    file) file_module $2 $3;;


    *) echo "others case";;
esac