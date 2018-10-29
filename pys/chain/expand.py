#coding:utf-8
import os
import sys
import shutil

from pys import path
from pys import utils
from pys.log import logger
from pys.log import consoler
from pys.chain import parser
from pys.chain import data
from pys.node import build
from pys.node import temp_node
from pys.exp import MCError
from pys.node.bootstrapsnode import P2pHosts
from pys.node.bootstrapsnode import P2pHost
from pys.chain.parser import ConfigConf
from pys.chain.port import AllChainPort

from pys.node.fisco_version import Fisco

def expand_on_exist_chain(cc):

    chain = cc.get_chain()
    port = cc.get_port()
    chain_id = chain.get_id()
    chain_version = chain.get_version()

    # expand on exist chain, check common、 genesis.json、 bootstrapnodes.json file exist.
    if not os.path.exists(chain.data_dir() + '/common'):
        raise MCError(' chain dir exist ,but common dir not exist, chain_id %s、chain_version %s' % (
            chain_id, chain_version))
    if not os.path.exists(chain.data_dir() + '/genesis.json'):
        raise MCError(' chain dir exist ,but genesis.json not exist, chain_id %s、chain_version %s' % (
            chain_id, chain_version))
    if not os.path.exists(chain.data_dir() + '/bootstrapnodes.json'):
        raise MCError(' chain dir exist ,but bootstrapnodes.json not exist, chain_id %s、and chain_version %s' % (
            chain_id, chain_version))
    
    acp = AllChainPort()
    # port check
    for node in cc.get_nodes():
        for index in range(node.get_node_num()):
            # create dir for every node on the server
            acp.port_conflicts_outside_chain(chain.get_id(), node.get_host_ip(), port.to_port(index))
            acp.port_conflicts_inside_chain(node.get_host_ip(), port.to_port(index) ,chain.get_id(), chain.get_version())

    fisco = Fisco(chain.data_dir() + '/' + 'common' + '/' + 'fisco-bcos')
    
    # expand install dir for every server
    for node in cc.get_nodes():
        try:
            build.expand_host_dir(chain, node, port, fisco)
        except Exception as e:
            logger.error(' expand failed, chain id is %s, chain version is %s, exception is %s.',
                     chain_id, chain_version, e)
            raise MCError(' expand failed, chain id is %s, chain version is %s, exception is %s' % (
            chain_id, chain_version, e))

def expand_on_nonexist_chain(cc, fisco_path, genesisjson, bootstrapnodesjson):
    
    # check if fisco-bcos、genesis.json、bootstrapsnode.json exist.
    if not os.path.exists(fisco_path):
        raise MCError(
            ' fisco bcos not exist, fisco bcos path is %s' % fisco_path)
    if not os.path.exists(genesisjson):
        raise MCError(
            ' genesis.json not exist, genesis.json path is %s' % genesisjson)
    if not os.path.exists(bootstrapnodesjson):
        raise MCError(
            ' bootstrapnodes.json not exist, bootstrapnodes.json path is %s' % bootstrapnodesjson)

    chain = cc.get_chain()
    port = cc.get_port()
    chain_id = chain.get_id()
    chain_version = chain.get_version()

    # parser fisco-bcos version and check it.
    fisco = Fisco(fisco_path)
    if not fisco.is_13_version():
        raise MCError(
            ' fisco-bcos is not 1.3.x version, not support now, version is %s' % fisco)

    acp = AllChainPort()
    # port check
    for node in cc.get_nodes():
        for index in range(node.get_node_num()):
            # create dir for every node on the server
            acp.port_conflicts_outside_chain(chain.get_id(), node.get_host_ip(), port.to_port(index))
            acp.port_conflicts_inside_chain(node.get_host_ip(), port.to_port(index) ,chain.get_id(), chain.get_version())

    try:
        # create host dir
        os.makedirs(chain.data_dir())
        # copy genesis.json bootstrapnodes.json to chain dir.
        shutil.copy(genesisjson, chain.data_dir() + '/')
        shutil.copy(bootstrapnodesjson, chain.data_dir() + '/')

        # create common dir
        build.build_common_dir(chain, fisco, False)

        # build install dir for every server
        for node in cc.get_nodes():
            build.expand_host_dir(chain, node, port, fisco)

    except Exception as e:
        if os.path.exists(chain.data_dir()):
            shutil.rmtree(chain.data_dir())
        logger.error(' expand failed, chain id is %s, chain version is %s, exception is %s.',
                     chain_id, chain_version, e)
        raise MCError(' expand failed, chain id is %s, chain version is %s, exception is %s' % (
            chain_id, chain_version, e))

def chain_expand(cfg, args):
    """expand operation 
    
    Arguments:
        cfg {string} -- config file path
        fisco_path {string} -- fisco-bcos file path
        genesisjson {string} -- genesis.json file path
        bootstrapnodesjson {string} -- bootstrapsnodes.json file path
    """

    logger.debug(' cfg is %s, args is %s', cfg, args)

    fisco_path = ''
    genesisjson = ''
    bootstrapnodesjson = ''

    if len(args) > 1:
        fisco_path = args[0]
    if len(args) > 2:
        genesisjson = args[1]
    if len(args) > 3:
        bootstrapnodesjson = args[2]

    try:
        try:
            # parser and check config if valid
            cc = ConfigConf(cfg)
        except Exception as e:
            raise MCError(
                ' parser config failed, invalid format, config is %s, exception is %s' % (cfg, e))

        if os.path.exists(cc.get_chain().data_dir()):
            expand_on_exist_chain(cc)
        else:
            expand_on_nonexist_chain(cc, fisco_path, genesisjson, bootstrapnodesjson)
            consoler.info(' expand install package for chain %s version %s success.', cc.get_chain().get_id(), cc.get_chain().get_version())

    except MCError as me:
        consoler.error(me)
        logger.error(me)
