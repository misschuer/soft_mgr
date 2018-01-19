#!/usr/bin/python
# -*- coding: utf8-*-

#-------------------------------------
# 保存着所有逻辑服务器的所有状态
# 所有有服务器由多个进程组成
# 所有进程相关联的当前运行信息由相关context进行控制
#-------------------------------------


###################################################
SERVER_TYPE_NETGD = 0  # 网关服
SERVER_TYPE_CENTD = 1  # 中心服
SERVER_TYPE_LOGIND = 2  # 登录服
SERVER_TYPE_APPD = 3  # 应用服
SERVER_TYPE_POLICED = 4  # 日志服
SERVER_TYPE_ROBOTD = 5  # 机器人服
SERVER_TYPE_SCENED = 6  # 场景服

SCENED_TYPE_NONE = 0  # 场景实例保留类型
SCENED_TYPE_NO_INST = 1  # 非副本类型
SCENED_TYPE_ACTIVI = 2  # 活动地图
SCENED_TYPE_INST = 3  # 副本地图
MAX_SCENED_TYPE = 4

class ProcInfo:
    def __init__(self, svr, typ):
        self.server_type = typ
        self.scened_type = 0  # 场景服类型,仅对场景服有效
        self.logic_server = svr  # 属于的逻辑服务器
        self.__context = None
        self.__process_id = 0
        
    def getProcessID(self):
        return self.__process_id
    
    def setProcessID(self, pid):
        self.__process_id = pid
    
    def getContext(self):
        return self.__context
    
    def setContext(self, c):
        self.__context = c
        
# 这里存着所有的逻辑服务器信息树根 server_name => LogicServerInfo
logic_svr_map = {}

# 根据进程ID找到相应进程信息，当然上面也保存着逻辑服务器的信息
def get_proc(pid):
    for s in logic_svr_map.values():
        if s.get_proc(pid):
            return s
    return None 

class LogicServerInfo:
    def __init__(self, svr_name, scened_num=4):
        self.server_name = svr_name
        self.centd = ProcInfo(self, SERVER_TYPE_CENTD)  # 中心服       
        self.appd = ProcInfo(self, SERVER_TYPE_APPD)  # 应用服
        self.logind = ProcInfo(self, SERVER_TYPE_LOGIND)  # 登录服
        self.policed = ProcInfo(self, SERVER_TYPE_POLICED)  # 日志服
        for i in xrange(scened_num):  # 场景服列表
            s = ProcInfo(self, SERVER_TYPE_SCENED)
            s.scened_type = i % MAX_SCENED_TYPE
            self.sceneds.append(s)
        # i插入逻辑服务器信息到表中
        assert logic_svr_map[svr_name] == None
        logic_svr_map[svr_name] = self
            
    def get_proc(self, pid):
        """根据进程号取得进程信息"""
        if self.centd.getProcessID() == pid:
            return self.centd
        if self.appd.getProcessID() == pid:
            return self.appd
        if self.logind.getProcessID() == pid:
            return self.logind
        if self.policed.getProcessID() == pid:
            return self.policed
        for s in self.sceneds:
            if s.getProcessID() == pid:
                return s
        return None

