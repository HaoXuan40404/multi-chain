#coding:utf-8

import re
import subprocess
from pys.log import logger
from pys.log import consoler
from pys.node.bootstrapsnode import P2pHosts
from pys.node.bootstrapsnode import P2pHost

def valid_chain_id(chain_id):
    """[Determine if the chain id is valid]
    
    Arguments:
        ip {[string]} -- [chain id]
    
    Returns:
        [bool] -- [true or false]
    """

    try: 
        int(chain_id)
        return True
    except Exception as e:
        logger.error('%s is not a valid chain_id', e)
        return False

def valid_ip(ip):
    """[Determine if the host ip is valid]
    
    Arguments:
        ip {[string]} -- [host ip]
    
    Returns:
        [bool] -- [true or false]
    """

    p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(ip):
        return True
    else:
        return False

def valid_port(port):
    """[Determine if the port is valid]
    
    Arguments:
        ip {[string]} -- [port number]
    
    Returns:
        [bool] -- [true or false]
    """

    if isinstance(port, int) and (port > 0) and (port <= 65535):
        return True
    else:
        return False

def valid_string(s):
    """[Determine if the string->s is valid]
    
    Arguments:
        ip {[string]} -- [a string outside the function]
    
    Returns:
        [bool] -- [true or false]
    """
    
    if (isinstance(s, str) or isinstance(s, unicode)) and (len(s) > 0):
        return True
    else:
        return False

def replace(filepath, old, new):
    """[replace old string to new from filepath]
    
    Arguments:
        filepath {[path]} -- [file path that needs to be replaced]
        old {[string]} -- [old string]
        new {[string]} -- [new string]
    """

    with open(filepath, 'r+') as f:
        all_lines = f.readlines()
        f.seek(0)  
        f.truncate() 
        for line in all_lines:
            line = line.replace(old, new)
            f.write(line)

def getstatusoutput(cmd):
    """replace commands.getstatusoutput
    
    Arguments:
        cmd {[string]}
    """

    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.communicate()
    out = ret[0]
    err = ret[1]
    output = ''
    if not out is None:
        output = output + out.decode('utf-8')
    if not err is None:
        output = output + err.decode('utf-8')
    return (p.returncode, output)

def port_in_use(port):
    """using cmd nc to check if the port is occupied.
    
    Arguments:
        port {string} -- port number
    
    Returns:
        bool -- True or False.
    """

    cmd = 'nc -z 127.0.0.1' + (' %d' % port)
    status,output = getstatusoutput(cmd)

    logger.debug('port is %s, status is %s, output is %s', port, status, output)

    return status == 0


def create_bootstrapnodes(nodes, port, path):
    """generate bootstrapnodes.json file
    """

    phs = P2pHosts()
    for node in nodes:
        for index in range(node.get_node_num()):
            phs.add_p2p_host(
                P2pHost(node.get_p2p_ip(), port.get_p2p_port() + index))
    with open(path + '/bootstrapnodes.json', "w+") as f:
        f.write(phs.to_json())




