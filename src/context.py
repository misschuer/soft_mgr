#!/usr/bin/python
# -*- coding: utf8-*-

import logic_server_info


SVR_STATE_INIT = 0  # 该服务属于启动阶段
SVR_STATE_START = 1
SVR_STATE_CRASH = 2
SVR_STATE_STOP = 3
SVR_STATE_UPING = 4

# 协议号
INTERNAL_OPT_REG_SERVER = 1  # 注册服务器,服务器连接到网关服,由此确定身份

class Context:
    def __init__(self):
        self.connect_tm = 0
        self.__proc_info = None
    
    def getProc(self):
        return self.__proc_info
    
    def setProc(self, p):
        self.__proc_info = p 
        
    def on_connected(self):        
        pass
    
    def on_reg_svr(self, pkt):
        """连接建立成功后，修改相应的服务器的相应进程修改状态
        协议：连接ID/服务器类型/进程号/场景服类型
        """
        the_connid = pkt.read_uint32()
        server_type = pkt.read_int32()
        the_proc_id = pkt.read_int32()
        the_scened_typ = pkt.read_int32()
        # 用所给进程号找到相应的服务进程信息
        procinfo = logic_server_info.get_proc(the_proc_id)
        assert procinfo.getProcessID() == the_proc_id
        assert procinfo.server_type == server_type
        assert procinfo.scened_type == the_scened_typ
    
    def on_disconnected(self):
        """当连接断开时检查一下服务器必须的状态，如果是异常断开则需要自动重启服务器"""
        pass
