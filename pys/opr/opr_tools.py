# coding:utf-8

import os
import json
import shutil
from pys import path
from pys import ansible, utils
from pys.chain.meta import Meta
from pys.chain.package import AllChain
from pys.chain.package import ChainVers
from pys.chain.package import VerHosts
from pys.chain.package import HostNodeDirs
from pys.chain.port import AllChainPort
from pys.log import logger
from pys.log import consoler
from pys.chain import data
from pys.chain import package


def telnet_ansible(server):
    """[Test ansible operation to all server in operation server]
    
    Arguments:
        server {[list]} -- [host ip]
    """

    if server[0] == 'all':
        server = ['all']

    for i in range(len(server)):
        if utils.valid_ip(server[i]) or server[i] == 'all':
            if ansible.telnet_module(server[i]):
                consoler.info(' telnet test success, host is %s.', server[i])
            else:
                consoler.error(' telnet test failed, host is %s.', server[i])
        else:
            consoler.error(' Not invalid host, skip, host is %s.', server[i])

def do_cmd(dst, cmd):
    """do cmd on remote server, dst can be one server, one chain or all server
    
    Arguments:
        dst {string} -- host ip or chain id or 'all'
        cmd {string} -- shell cmd or shell file
    """

    if dst == 'all': 
        ansible.cmd_module('all', cmd)
    elif utils.valid_chain_id(dst):
        mm = Meta(dst)
        if not mm.exist():
            consoler.error(' chain is not published, can not cmd action, chain_id is %s', dst)
        else:
            consoler.info(' => do cmd, chain id is %s', dst)
            for k in mm.get_nodes().keys():
                logger.debug('host ip is ' + k)
                ansible.cmd_module(k, cmd)
    elif utils.valid_ip(dst):
        ansible.cmd_module(dst, cmd)
    else:
        consoler.error(' invalid docmd dst, dst is %s, dst should be invalid chain_id or invali host ip or \'all\'.', dst)

def push_file(host, src, dst):
    """push file to remote server
    
    Arguments:
        host {string} -- host ip or chain id or 'all'
        src {string} -- file or dir
        dst {string} -- dst dir
    """

    if not os.path.exists(src):
        consoler.error(' src is not exist, src is %s.', src)
        return

    logger.info(' host is %s, src is %s, dst is %s', host, src, dst)

    if host == 'all':
        if mkdir_and_push(host, src, dst):
            consoler.info(' push %s to %s of all server success.', src, dst)
    elif utils.valid_chain_id(host):
        consoler.info(' => push %s to %s of chain %s.', src, dst, host)
        mm = Meta(dst)
        if not mm.exist():
            consoler.error(' chain is not published, can not push file action, chain_id is %s', host)
        else:
            consoler.info(' => do cmd, chain id is %s', host)
            for k in mm.get_nodes().keys():
                logger.debug(' host is %s', k)
                if mkdir_and_push(k, src, dst):
                    consoler.info(' \t\t push %s to %s of %s server success.', src, dst, k)
        consoler.info(' => push %s to %s of chain %s end.', src, dst, host)
    elif utils.valid_ip(host):
        if mkdir_and_push(host, src, dst):
            consoler.info(' push %s to %s of %s server success.', src, dst, host)
    else:
        consoler.error(' invalid push file host, host is %s, dst should be invalid chain_id or invali host ip or \'all\'.', host)


def mkdir_and_push(host, src, dst):
    # create dir on the target server
    ret = ansible.mkdir_module(host, dst)
    if not ret:
        logger.error(' mkdir dir on server %s failed, dir is %s.', host, dst)
        return ret

    # push file
    ret = ansible.copy_module(host, src, dst + '/')
    if not ret:
        logger.error(
            ' push file to %s failed, src is %s, dst is %s.', host, src, dst)
        return ret

    return True
