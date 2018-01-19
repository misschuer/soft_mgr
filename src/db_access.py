#!/usr/bin/python
# -*- coding: utf8-*-

from pymongo import MongoClient, DESCENDING
#from pymongo import Connection
import time

class DBAccess:
    def __init__(self,domain,host,port,user,passwd):
        self._domain = domain
        self._host = host
        self._port = port
        self._user = user
        self._passwd = passwd
        self.max_logs_index = 0
        self._conn = MongoClient(host, port)
        if user != "":
            self._conn["admin"].authenticate(user, passwd)    #获得权限
         #load库，纠正下日志的最大索引
        result = list(self._conn['oper_tool']["logs"].find({"domain":self._domain}).sort("i_index", DESCENDING))
        if len(result) != 0:
            self.max_logs_index = result[0]["i_index"] + 1
	#print "--------->",self.max_logs_index    

    def getLogicServer(self):
        """根据所给的服务器名称返回所有的逻辑服务器信息"""
        log_map = {}
        information = self._conn['oper_tool']["server_info"]
        for i in information.find():
            log_map[i['domain']] = i
        return log_map

    def get_opts(self,gt_create_tm):
        """根据主机名及大于操作插入时间返回一批操作记录"""
        opts_list = []
        get_obj = self._conn['oper_tool']["server_opts"]
        for infor in get_obj.find({"u_create_tm":{"$gt":gt_create_tm}}):
            opts_list.append(infor)
        return opts_list

    def update_opts(self,objectId,finish_tm,result_code,result_txt):
        """根据所给的对象ID更新这三个字段"""
        up_set = {"u_finish_tm":finish_tm,"i_result_code":result_code,"result_txt":result_txt}
        self._conn['oper_tool']["server_opts"].update({"_id":objectId},{"$set":up_set})

    def update_opt_running(self, opt_id):
        up_set = {"u_start_tm":long(time.time()),"i_result_code":1}
        self._conn['oper_tool']["server_opts"].update({"_id":opt_id},{"$set":up_set})

    def log(self,typ, opt_typ,txt,plan_id):
        self._conn['oper_tool']["logs"].insert({"domain":self._domain,"i_index":self.max_logs_index,"u_create_tm":long(time.time()),"msg_typ":typ, "opt_typ":opt_typ,"plan_id":plan_id, "log":txt})
        self.max_logs_index = self.max_logs_index + 1

    def update_runstate(self, sername, run_status):
        if run_status == 2:
            """run_status=2,update install_tm"""
            self._conn['oper_tool']["server_info"].update({"server_name":sername},
                {"$set":{"i_run_status":run_status, "u_install_tm":long(time.time())}})
        else:
            """根据所给服务器guid，更新对应服务器的状态"""
            self._conn['oper_tool']["server_info"].update({"server_name":sername},{"$set":{"i_run_status":run_status}})

    def save_server_info_after_setup(self, server_name, git_version):
        self._conn['oper_tool']["server_info"].update({"server_name":server_name},
            {"$set":{"i_run_status":2,"u_install_tm":long(time.time()),
            "u_last_update_tm":long(time.time()),"git_version":git_version}})

    def update_server_info_update_tm(self, server_name, git_version):
        self._conn['oper_tool']["server_info"].update({"server_name":server_name},
            {"$set":{"u_last_update_tm":long(time.time()), "git_version":git_version}})

    def update_server_info_merge_server_names(self, server_name, merge_server_names):
        self._conn['oper_tool']["server_info"].update({"server_name":server_name},
            {"$set":{"merge_server_names":merge_server_names}})

    def update_server_info_branch(self, server_name, branch):
        self._conn['oper_tool']["server_info"].update({"server_name":server_name},
            {"$set":{"branch":branch}})

    def db_insert(self, *args):
        idtable = []
        for table in args:
            idtable.append(self._conn['oper_tool'][table.keys()[0]].insert(table.values()[0]))
        return idtable

    def db_insert_single(self, dic):
        myid = self._conn['oper_tool'][dic.keys()[0]].insert(dic.values()[0])
        return myid
    
    def db_insert_cow_config_single(self, dic):
        myid = self._conn['cow_config'][dic.keys()[0]].insert(dic.values()[0])
        return myid

    #根据所给表名对象id，更新或增加字段
    def update_or_add(self,name, objid, dic):
        if isinstance(dic, dict):
            self._conn['oper_tool'][name].update({"_id":objid},{"$set":dic})
        else:
            print "更新失败，所传集合有误"
    
    #查找操作指令
    def find_server_opts(self):
        return self._conn['oper_tool']["server_opts"].find({"i_result_code":{"$lte":0},"domain":self._domain})
    def find_machine_room(self, u_id):
        return self._conn['oper_tool']["machine_room"].find_one({"u_id":u_id})
    def find_centos_info(self, domain):
        return self._conn['oper_tool']["centos_info"].find_one({"domain":domain})
    def find_all_centos_info(self):
        return self._conn['oper_tool']["centos_info"].find()

    def find_all_server_info(self):
        return self._conn['oper_tool']["server_info"].find({"i_run_status":{"$gt":1,"$lt":4}})
    def find_my_server_info(self):
        return self._conn['oper_tool']["server_info"].find({"i_run_status":{"$gt":1,"$lt":4},"domain":self._domain})
    def find_world_server_info(self):
        return self._conn['oper_tool']["server_info"].find_one({"server_name":"world_server","s_test_type":"11","domain":self._domain})
    def find_my_runing_server_info(self):
        return self._conn['oper_tool']["server_info"].find({"i_run_status":{"$gt":2,"$lt":4},"domain":self._domain})
    def find_server_info_by_server_name(self, server_name):
        return self._conn['oper_tool']["server_info"].find_one({"server_name":server_name})
    def find_cow_config_by_server_name(self, server_name):
        return self._conn['cow_config']["server_info"].find_one({"server_name":server_name})
    def find_server_alias_by_server_name(self, server_name):
        return self._conn['cow_config']["server_alias"].find_one({"server_name":server_name})
    def find_server_info_by_pid(self, pid):
        return self._conn['oper_tool']["server_info"].find({"i_run_status":{"$gt":1,"$lt":4},"pid":pid})
    def find_server_info_by_branch(self, branch):
        return self._conn['oper_tool']["server_info"].find({"i_run_status":{"$gt":1,"$lt":4},"branch":branch})

    def find_server_info_by_domain(self, domain):
		return self._conn['oper_tool']["server_info"].find({"i_run_status":{"$gt":2,"$lt":4},"domain":domain})

    def find_plan_task_info(self):
        return self._conn['oper_tool']['plan_task_info'].find({"i_plan_status":{"$lt":1},"u_plan_excu_time":{"$lt":long(time.time())}})
    def update_plan_task_info(self, _id, status):
        self.update_or_add("plan_task_info", _id, {"i_plan_status":status})
    
    def save_centos_info(self, domain):
        self.db_insert_single({"centos_info":{"domain":domain,"u_server_reg_tm":long(0),"netgd_internal_port":"7001","netgd_port":"443",
            "safe_mgr_git_path":"/home/soft_mgr", "contrib_git_path":"/home/12j-contrib.git","server_mgr_git_path":"/home/server-mgr"}})

    def save_cow_config_server_info(self, domain, port, server_name, server_type):
        self.db_insert_cow_config_single({"server_info":{"host": domain,"i_merge_status":0,"i_port":port,"server_name":server_name,"i_server_type":server_type,"u_open_time":long(time.time())}})
    
    def save_server_alias_info(self, server_name, alias):
        self.db_insert_cow_config_single({"server_alias":{"server_name":server_name, "alias":alias}})

    def update_cow_config_server_info(self, domain, server_name):
        self._conn['cow_config']["server_info"].update({"server_name":server_name},{"$set":{"host": domain}})

    def update_server_alias_info(self, server_name, alias):
        self._conn['cow_config']["server_alias"].update({"server_name":server_name},{"$set":{"alias": alias}})

    def update_open_time_by_server_name(self, server_name, opentime):
        self._conn['cow_config']["server_info"].update({"server_name":server_name},{"$set":{"u_open_time":long(opentime)}})

    def save_cow_config_server_list(self, server_name, merge_server):
        self.db_insert_cow_config_single({"merge_server_list":{"server_name": server_name,"merge_server":merge_server}})

    def find_addr_info(self, host_port):
        return self._conn['cow_config']['addr_info'].find({"host_port":host_port})

    def update_addr_info(self, host_port, server_name_list):
        self._conn['cow_config']["addr_info"].update({"host_port":host_port},{"$set":{"server_name_list":server_name_list}})

    def save_addr_info(self, host_port, server_name_list):
        self._conn['cow_config']["addr_info"].insert({"host_port":host_port,"server_name_list":server_name_list})

    def save_setup_opt(self, plan_id, domain, server_name, git_version, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,"server_name":server_name,
            "opt":"setup", "param1":git_version,"param2":"","memo":desc,"u_finish_tm":0,
            "i_result_code":0,"result_txt":""} })
        
    def save_update_opt(self, plan_id, domain, server_name, git_version, update_type, desc, merge_server_names):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":server_name,"opt":"update", "param1":git_version,"param2":update_type,
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":"", "merge_server_names":merge_server_names}})

    def save_update_branch_opt(self, plan_id, domain, server_name, git_branch, moudels, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":server_name,"opt":"updatebranch", "param1":git_branch,"param2":moudels,
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":"", "merge_server_names":""}})

    def save_update_server_opt(self, plan_id, domain, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":"","opt":"updateserver", "param1":"","param2":"",
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":""}})

    def save_update_self_opt(self, plan_id, domain, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":"","opt":"updateself", "param1":"","param2":"",
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":""}})

    def save_update_internal_client_opt(self, plan_id, domain, clientpath, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":"","opt":"updateinternalclient", "param1":clientpath,"param2":"",
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":""}})

    def find_hefu_opt_status(self, server_name, merge_server_name):
        result = self._conn['cow_config']["merge_server_config"].find_one({"server_name":server_name,"merge_server_name":merge_server_name})
        if result is None:
            print "merge_server_config result is none",server_name,merge_server_name
            return None
        return result["i_opt_status"]

    def save_hefu_opt(self, server_name, merge_server_name):
        self.db_insert_cow_config_single({"merge_server_config":{"server_name":server_name,
                                                                "merge_server_name":merge_server_name,"i_opt_status":0}})
    def save_hefu_opt1(self, plan_id, domain, merge_server_name, server_name, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,"server_name":merge_server_name,
            "opt":"hefu", "param1":server_name,"param2":"","memo":desc,"u_finish_tm":0,
            "i_result_code":0,"result_txt":""} })
        
    def save_huidang_opt(self, plan_id, domain, server_name, player_guid, tm, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,"server_name":server_name,
            "opt":"huidang", "param1":player_guid,"param2":tm,"memo":desc,"u_finish_tm":0,
            "i_result_code":0,"result_txt":""}})
        
    def save_stop_opt(self, plan_id, domain, server_name, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":server_name,"opt":"stop", "param1":"","param2":"",
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":""}})

    def save_savealldatatodb_opt(self, plan_id, domain, server_name, desc):
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":server_name,"opt":"savealldatatodb", "param1":"","param2":"",
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":""}})
    
    def save_update_configfile_opt(self, plan_id, domain, server_name, desc):           
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":server_name,"opt":"updateconfigfile", "param1":"","param2":"",
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":""}})

    def save_houtai_opt(self, plan_id, domain, server_name, data_str, desc):           
        self.db_insert_single({"server_opts":{"plan_task_info_id":plan_id,"domain":domain,
            "u_create_tm":long(time.time()),"u_start_tm":0,
            "server_name":server_name,"opt":"houtai", "param1":data_str,"param2":"",
            "memo":desc,"u_finish_tm":0, "i_result_code":0,"result_txt":""}})

    def save_client_opt(self, server_name, moudel, version, desc):
        self._conn['server']["versions_requirements"].insert({"server_name":server_name,"u_create_time":long(time.time()),"version":version,
                                                             "i_module_type":moudel,"comment":desc})    
    def update_addr_info_sign(self):
        result = self._conn['cow_config']["addr_update_sign"].find_one()
        if result is None:
            self._conn['cow_config']["addr_update_sign"].insert({"u_update_time":long(1)})
        else:
            tm = result["u_update_time"]
            self._conn['cow_config']["addr_update_sign"].remove()
            self._conn['cow_config']["addr_update_sign"].insert({"u_update_time":long(tm + 1)})

    def find_addr_info(self): 
        return self._conn['cow_config']["addr_info"].find()

    def save_addr_info(self, host_port, sn_list):
        self.db_insert_cow_config_single({"addr_info":{"host_port":host_port, "server_name_list":sn_list}})

    def update_addr_info(self, host_port, sn_list):
        self._conn['cow_config']["addr_info"].update({"host_port":host_port},{"$set":{"server_name_list":sn_list}})

    #获得世界服的主机ip
    def find_world_host(self):
        #把world_config表里的数据全load出来
        results = self._conn['oper_tool']["world_config"].find({})
        for result in results:
            if result.has_key("world_host"):
                return result["world_host"]
    #获得世界服的主机port
    def find_world_port(self):
        #把world_config表里的数据全load出来
        results = self._conn['oper_tool']["world_config"].find({})
        for result in results:
            if result.has_key("world_port"):
                return result["world_port"]

    #获得世界服的主机ip
    def find_showhand_host(self):
        #把world_config表里的数据全load出来
        results = self._conn['oper_tool']["world_config"].find({})
        for result in results:
            if result.has_key("showhand_netgd_host"):
                return result["showhand_netgd_host"]
    #获得世界服的主机port
    def find_showhand_port(self):
        #把world_config表里的数据全load出来
        results = self._conn['oper_tool']["world_config"].find({})
        for result in results:
            if result.has_key("showhand_netgd_port"):
                return result["showhand_netgd_port"]
    

    #获得争霸天下服务器 server_name
    def find_zbtx_server_name(self):
        #把world_config表里的数据全load出来
        results = self._conn['oper_tool']["world_config"].find({})
        for result in results:
            if result.has_key("zbtx_server_name"):
                return result["zbtx_server_name"]
    def find_world_centd_port(self):
        #把world_config表里的数据全load出来
        results = self._conn['oper_tool']["world_config"].find({})
        for result in results:
            if result.has_key("world_centd_port"):
                return result["world_centd_port"]
    def find_world_server_name(self):
        #把world_config表里的数据全load出来
        results = self._conn['oper_tool']["world_config"].find({})
        for result in results:
            if result.has_key("world_server_name"):
                return result["world_server_name"]
    def save_world_centd_config(self, world_server_name, world_centd_port):
        self.db_insert_single({"world_config":{"world_server_name":world_server_name}})
        self.db_insert_single({"world_config":{"world_centd_port":world_centd_port}})
    def save_world_netgd_host_port(self, world_host, world_port):
        self.db_insert_single({"world_config":{"world_host":world_host}})
        self.db_insert_single({"world_config":{"world_port":world_port}})

    #获得post地址
    def find_post_url(self):
        #把oper_config表里的数据全load出来
        results = self._conn['oper_tool']["oper_config"].find({})
        for result in results:
            if result.has_key("post_url"):
                return result["post_url"]
    #post密钥
    def find_post_key(self):
        #把oper_config表里的数据全load出来
        results = self._conn['oper_tool']["oper_config"].find({})
        for result in results:
            if result.has_key("post_key"):
                return result["post_key"]
    


