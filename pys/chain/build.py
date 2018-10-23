# coding:utf-8

import os
import sys
import shutil

from pys import path
from pys import utils
from pys.log import logger
from pys.log import consoler
from pys.chain.parser import ConfigConfs
from pys.chain import data
from pys.node import build
from pys.node import temp_node
from pys.exp import MCError

from pys.node.fisco_version import Fisco
from pys.chain.port import AllChainPort

def chain_build(cfg, fisco_path):
    """parser input config file, build install pacakge by 

    Arguments:
        cfg {string} --config, maybe a config.json ora dictionary of conf,eg：./conf/config.conf or ./conf
        fisco_path {string} -- path of fisco-bcos, eg：/usr/local/bin/fisco-bcos
    Returns:
        null
    """

    logger.debug('build cfg is %s, fisco is %s ', cfg, fisco_path)

    try:
        # parser fisco-bcos version and check it.
        fisco = Fisco(fisco_path)
        if not fisco.is_13_version():
            logger.error(' fisco-bcos is not 1.3.x version, not support now, versin is %s', fisco)
            raise MCError(' fisco-bcos is not 1.3.x version, not support now, versin is %s' % fisco)
        
        # parser and check config if valid
        ccs = ConfigConfs(cfg).get_ccs()

        # build all chain
        if len(ccs) != 0:
            for cc in ccs.itervalues():
                build_cfg(cc, fisco)
        else:
            consoler.info(' build operation will do nothing.')

    except MCError as me:
        consoler.error(me)
    except Exception as e:
        consoler.error(' Unkown exception, e is %s' % e)

    logger.info(' chain build end.')


def build_cfg(cc, fisco):
    """build all install package for one chain base on cc 

    Arguments:
        cc {ConfigConf} -- ConfigConf object  
        fisco {Fisco} -- Fisco object

    Raises:
        Exception -- exception description
    """

    logger.info('building, cc is %s, fisco is %s', cc, fisco)

    port = cc.get_port()
    chain = cc.get_chain()
    dir = chain.data_dir()

    consoler.info(' \t build install package for chain %s version %s .',
                  chain.get_id(), chain.get_version())

    # create dir base on version of the chain.
    if os.path.isdir(dir):
        logger.warn(' chain_id:%s chain_version:%s aleady exist !!!.',
                    chain.get_id(), chain.get_version())
        consoler.error(' \t chain_id:%s chain_version:%s aleady exist !!!.',
                       chain.get_id(), chain.get_version())
        return

    try:

        acp = AllChainPort()
        # port check
        for node in cc.get_nodes():
            for index in range(node.get_node_num()):
                # create dir for every node on the server
                acp.port_conflicts(node.get_host_ip(), port)
                
        os.makedirs(dir)

        # generate bootstrapsnode.json
        utils.create_bootstrapnodes(cc.get_nodes(), port, dir)

        # create common dir
        build.build_common_dir(chain, fisco)

        if fisco.is_gm():
            # create temp node for export genesis.json file
            temp_node.GM_temp_node_build(dir, port, fisco)
        else:
            # create temp node for export genesis.json file
            temp_node.temp_node_build(dir, port, fisco)
        # start temp node
        temp_node.start_temp_node(dir, port)

        # build install dir for every server
        for node in cc.get_nodes():
            build.build_host_dir(chain, node, port, fisco, temp_node)

        # stop temp node and export for genesis.json file
        temp_node.stop_temp_node(dir)
        temp_node.export_genesis(dir)
        temp_node.clean_temp_node(dir)

        # copy genesis.json bootstrapnodes.json
        for node in cc.get_nodes():
            for index in range(node.get_node_num()):
                shutil.copy(dir + '/genesis.json', dir + '/' + node.get_host_ip() + '/node' + str(index))

        utils.replace(dir + '/common/web3sdk/conf/applicationContext.xml',
                      'NODE@HOSTIP', 'node0@127.0.0.1:%d' % port.get_channel_port())

        logger.info(' build end ok, chain is %s', chain)
        consoler.info('\t build install package for chain %s version %s success.',
                      chain.get_id(), chain.get_version())
    
    except Exception as e:
        consoler.error('\t build package for chain %s version %s failed, exception is %s',
                       chain.get_id(), chain.get_version(), e)

        temp_node.clean_temp_node(dir)
        if os.path.exists(dir):
            shutil.rmtree(dir)

