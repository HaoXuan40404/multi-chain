# coding:utf-8

import os
import sys
import shutil
import json
import time

from pys import path
from pys.data_mgr import data
from pys.log import logger
from pys.error.exp import MCError
from pys.data_mgr.port import Port

class MetaNode:

    def __init__(self, host_ip, rpc_port, p2p_port, channel_port, node):
        self.host_ip = host_ip
        self.rpc_port = rpc_port
        self.p2p_port = p2p_port
        self.channel_port = channel_port
        self.node = node
    
    def get_rpc(self):
        return self.rpc_port
    
    def get_p2p(self):
        return self.p2p_port
    
    def get_channel(self):
        return self.channel_port
    
    def get_node(self):
        return self.node
    
    def get_host(self):
        return self.host_ip

    def __repr__(self):
        return 'host %s, node %s, rpc %s, p2p %s, channel %s' % (self.host_ip, self.node, self.rpc_port, self.p2p_port, self.channel_port)

class Meta:

    def __init__(self, chain_id, chain_version = ''):
        self.chain_id = chain_id
        self.chain_version = chain_version
        self.nodes = {}
        self.load()

    def get_chain_id(self):
        return self.chain_id
    
    def get_chain_version(self):
        return self.chain_version

    def set_chain_version(self, chain_version):
        self.chain_version = chain_version

    def get_host_nodes(self, host_ip):

        if host_ip in self.nodes:
            host_nodes = self.nodes[host_ip]
            logger.info(' get host nodes, host is %s, hm is %s',
                        host_ip, host_nodes)
            return host_nodes
        # raise or not ???
        logger.info(' get host nodes failed, host is %s', host_ip)
        raise MCError(' not found meta node, chain_id is %s, host is %s' % (self.chain_id, host_ip))
    
    def get_host_node(self, host_ip, node):

        if host_ip in self.nodes:
            host_nodes = self.nodes[host_ip]
            for n in host_nodes:
                if node == n.node:
                    logger.debug(
                        ' host is %s, node is %s, n is %s', host_ip, node, n)
                    return n
            logger.debug(' node not exist, node is %s ', node)
            raise MCError(' node not exist in the chain, node is %s' % node)
        logger.debug(' host not exist, host is %s.', host_ip)
        raise MCError(' host not exist in the chain, host is %s' % host_ip)
    
    def host_node_exist(self, host_ip, node):
        try:
            self.get_host_node(host_ip, node)
            return True
        except Exception as e:
            return False

    def append(self, m):
        if self.host_node_exist(m.host_ip, m.node):
            return False
        if m.host_ip in self.nodes:
            host_nodes = self.nodes[m.host_ip]
            host_nodes.append(m)
        else:
            host_nodes = []
            host_nodes.append(m)
            self.nodes[m.host_ip] = host_nodes
        logger.info(' append mn, mn is %s, hm is %s', m, host_nodes)
        return True

    def get_nodes(self):
        return self.nodes

    def clear(self):
        self.chain_version = ''
        self.nodes = {}

    def to_json(self):
        return json.dumps(self, default=lambda obj: obj.__dict__, indent=4)

    def write_to_file(self):
        #if len(self.nodes) == 0:
        #    logger.debug('nodes empty, write return')
        #    return
        if not data.meta_dir_exist(self.chain_id):
            data.create_meta_dir(self.chain_id)

        meta_file = data.meta_dir(self.chain_id) + '/meta.json'
        meta_bak_file = meta_file + '_bak_' + \
            time.strftime("%Y-%m-%d_%H-%M%S", time.localtime())
        if os.path.exists(meta_file):
            shutil.copy(meta_file, meta_bak_file)
            logger.info(
                'meta.json is exist, backup it, name is ' + meta_bak_file)
        try:
            with open(data.meta_dir(self.chain_id) + '/meta.json', "w+") as f:
                f.write(self.to_json())
                logger.info(
                    'write info meta.json, content is ' + self.to_json())
        except Exception as e:
            logger.error(
                ' write meta failed, chaind id is %s, exception is %s', self.chain_id, e)
            # raise or not ???
            raise MCError(' write meta.json failed, chain id is %s, exception is %s' % (self.chain_id, e))

    def exist(self):
        return os.path.exists(data.meta_dir(self.chain_id) + '/meta.json')
    
    def empty(self):
        return len(self.nodes) == 0

    def load(self):
        self.clear()
        if not self.exist():
            logger.info(' meta.json not exist, chain_id is ' + self.chain_id)
            return

        try:
            with open(data.meta_dir(self.chain_id) + '/meta.json', 'r') as f:
                jsondata = json.load(f)

                if 'chain_version' in jsondata:
                    self.chain_version = str(jsondata['chain_version'])

                if 'nodes' in jsondata:
                    for hm in jsondata['nodes'].values():
                        for v in hm:
                            mn = MetaNode(v['host_ip'], v['rpc_port'], v['p2p_port'], v['channel_port'], v['node'])
                            logger.info(
                                'load from meta.json, meta node is %s', mn)
                            self.append(mn)
            logger.info(' Meta is %s', self.to_json())
        except Exception as e:
            logger.error(
                ' load meta failed, chaind id is %s, exception is %s', self.chain_id, e)
            # raise or not ???
            raise MCError(' load meta.json data failed, chain id is %s, exception is %s' % (self.chain_id, e))

class AllMeta:
    def __init__(self):
        self.metas = {}
        self.load()

    def get_metas(self):
        return self.metas

    def get_meta_by_chain_id(self, chain_id):
        if chain_id in self.metas:
            return self.metas[chain_id]
        # raise or not ???
        raise MCError(' not found meta, chain_id is %s' % (chain_id))
    
    def load(self):

        dir = data.meta_dir_base()
        for chain_id in  os.listdir(dir):
            try:
                meta = Meta(chain_id)
                self.metas[chain_id] = meta
            except Exception as e:
                pass
    
def get_meta_ports_by_host(host, am = None):

    if not am is None:
        am = AllMeta()

    metas = []
    for meta in am.get_metas().values():
        try:
            host_nodes = meta.get_host_nodes(host)
            if len(host_nodes) == 0:
                continue
            logger.debug(' host is %s, meta is %s', host, meta)
            metas.append(meta)
        except Exception as e:
            pass

    return metas
