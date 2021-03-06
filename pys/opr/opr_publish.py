# coding:utf-8
import os
from pys.tool import utils
from pys.tool import ansible
from pys.log import logger
from pys.log import consoler
from pys.data_mgr import meta
from pys.data_mgr import data
from pys.data_mgr.chain import Chain
from pys.build import config
from pys.data_mgr.port import HostPort
from pys.data_mgr.package import HostNodeDirs

from pys.data_mgr.chain import Chain
from pys.error.exp import MCError


def publish_chain(chains, force = False):
    """Publish a chain to designated servers 
    using publish_server
    
    Arguments:
        chains {list} -- chain which you wanto published, type chain_id:chain_version.
    
    Returns:
        null
    """
    pchains = []
    for i in range(len(chains)):
        chain = chains[i].split(':')
        if len(chain) != 2:
            logger.error('not chain_id:chain_version format, str is %s', chains[i])
            consoler.error(' \033[1;31m skip, invalid publish format, chain_id:chain_version should require, chain is %s \033[0m', chain)
            continue

        chain_id = chain[0]
        chain_version = chain[1]

        pchains.append(Chain(chain_id, chain_version))
        # consoler.info('\t append publish chain, chain_id %s:chain_version %s', chain_id, chain_version)

        logger.debug('chain_id is %s, chain_version is %s', chain_id, chain_version)
            
    if len(pchains) != 0:
        for chain in pchains:
            logger.info('publish, chain_id is %s, chain_version is %s', chain_id, chain_version)
            publish_server(chain.get_id(), chain.get_version(), force)


def publish_server(chain_id, chain_version, force=False):
    """publish one chain.

    Arguments:
        chain_id {string} -- chain id.
        chain_version {string} -- chain version.
        force {bool}
    """

    chain = Chain(chain_id, chain_version)
    dir = chain.data_dir()
    if not os.path.isdir(dir):
        consoler.info(
            ' No build version exist for chain_id:%s chain_version:%s, do nothing.', chain_id, chain_version)
        logger.warn(
            ' No build version exist for chain_id:%s chain_version:%s, do nothing.', chain_id, chain_version)
        return

    mm = meta.Meta(chain_id)
    if force:
        # force is set, publish this chain again.
        mm.clear()
        mm.set_chain_version(chain_version)
    else:
        if mm.exist():
            if chain_version != mm.get_chain_version():
                consoler.error(
                    ' \033[1;31m chain %s already publish %s version, if you want publish annother version, --force/-f need to be set.\033[0m ', chain_id, mm.get_chain_version())
                return
        else:
            mm.set_chain_version(chain_version)

    consoler.info(' publish package for chain %s version %s begin.',
                  chain_id, chain_version)

    for host in os.listdir(dir):
        if not utils.valid_ip(host):
            logger.debug(' skip, not invalid host_ip ' + host)
            continue
        ret = push_package(dir, host, chain_id, chain_version, mm, force)
        if ret:
            hp = HostPort(chain_id, chain_version, host)
            for node_dir, p in hp.get_ports().items():
                logger.debug(' node_dir is %s, port is %s', node_dir, p)
                if not mm.host_node_exist(host, node_dir):
                    mm.append(meta.MetaNode(host, p.get_rpc_port(), p.get_p2p_port(), p.get_channel_port(), node_dir))
            consoler.info(' \t push package : %s success.', host)
        else:
            consoler.error(' \033[1;31m \t push package : %s  failed. \033[0m', host)
    # record meta info, write meta.json file
    mm.write_to_file()
    consoler.info(' publish package for chain %s version %s end.', chain_id, chain_version)

def push_package(dir, host, chain_id, version, meta, force = True):
    """push install package of one server
    
    Arguments:
        dir {string} -- package install dir       
        host {string} -- server host
        chain_id {string} -- chain id
        version {string} -- chain version
        force {string} -- is push all node dir or not published
    
    Returns:
        [bool] -- success return True, if not False will return.
    """
    # check if common dir exist.
    if not os.path.exists(dir + '/common'):
        logger.warn(' common dir is not exist, dir is %s, host is %s', dir, host)
        return False

    # check if host dir exist.
    if not os.path.exists(dir + '/' + host):
        logger.warn(' host dir is not exist, dir is %s, host is %s', dir, host)
        return False
    
    try:
        if meta.get_host_nodes(host):
            pass
    except MCError as me:
        # create dir on the target server
        ret = ansible.mkdir_module(host, ansible.get_dir() + '/' + chain_id)
        if not ret:
            return ret
        
        # push common package
        ret = ansible.copy_module(host, dir + '/common/', ansible.get_dir() + '/' + chain_id)
        if not ret:
            return ret
    
    if force:
        logger.debug(' force is set, push all package, chain_id is %s, chain_version is %s, host is %s',chain_id, version, host)
        # push host dir
        ret = ansible.copy_module(host, dir + '/' + host + '/', ansible.get_dir() + '/' + chain_id)
        if not ret:
            return ret
    else:
        # push node${index} dir in host dir not published
        hnd = HostNodeDirs(chain_id, version, host)
        for node_dir in hnd.get_node_dirs():
            if meta.host_node_exist(host, node_dir):
                logger.info(' %s already published, skip', node_dir)
                continue
            logger.info(' publish nodedir, chain_id is %s, chain_version is %s, node is %s', chain_id, version, node_dir)
            # push host dir
            ret = ansible.copy_module(host, dir + '/' + host + '/' + node_dir, ansible.get_dir() + '/' + chain_id)
            if not ret:
                return ret

    
    logger.info('push package success, dir is %s, host is %s, chain_id is %s, chain_version is %s', dir, host, chain_id, version)
    
    return True  




    

    





