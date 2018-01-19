#!/usr/bin/python
# -*- coding: utf8-*-
"""
需求：
1.该程序要主要目的通过对远程数据库的论询获得操作并执行
2.通过tcp与受控程序建立长连接，当连接丢失的时候就是服务器被关闭的时候
	可以根据服务器的状态选择记录日志后重启等后续操作
"""

from db_access import DBAccess
import context, time, telnetlib
import sock_app, random

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

def usage():
    print "usage:\n\tsoft_mgr_agent.py --action=term --db_host=127.0.0.1 --db_port=27017"\
     " --db_username=dev --db_password=asdf --domain=s1.9.game2.com.cn"\
     " --log_level=0 --game_db_str=HgAAAByUz/iLLPzag5dTbXDweHfSrMv/ZEW0uzthZG1pbgA="\
     " --wulongju=0"
    sys.exit()

class Conf:
    """配置信息，从命令行中可以取得"""
    def __init__(self, conf_str):
        self.domain = ''
        self.action = ''
        self.db_username = 'tsoperation'
        self.db_password = 'jzb041KppyJPuME2'
        self.db_host = '127.0.0.1'
        self.db_port = 27021
        self.host = '127.0.0.1'
        self.port = random.randrange(20000,25000)
        self.log_level = 0
        self.game_db_str = 'HgAAAByUz/iLLPzag5dTbXDweHfSrMv/ZEW0uzthZG1pbgA='
        self.wulongju = 0
        if len(conf_str) > 0:
            self.parse(conf_str)
        
        
    def parse(self,conf_str):
        import getopt
        try:
            opts,args = getopt.getopt(conf_str.split(), 'p:', ['help','domain=','db_username=','db_password='\
															,'db_host=','db_port=','action=','log_level='\
															,'game_db_str=','wulongju='])
        except getopt.GetoptError:
            usage()
        for opt,arg in opts:
            if opt == '--domain':
                self.domain = arg
            elif opt == '--db_username':
                self.db_username = arg
            elif opt == '--db_password':
                self.db_password = arg
            elif opt == '--db_host':
                self.db_host = arg
            elif opt == '--db_port':                
                self.db_port = int(arg)
            elif opt == '--action':
                self.action = arg
            elif opt == '--port':
                self.port = int(arg)
            elif opt == '--log_level':
                self.log_level = int(arg)
            elif opt == '--game_db_str':
                self.game_db_str = arg
            elif opt == '--wulongju':
                self.wulongju = int(arg)
            elif opt == '--help' or opt == '-h':
                usage()



class SoftMgrAgent(sock_app.App):
    def __init__(self, conf):
        sock_app.App.__init__(self,SoftMgrAgent.hanlder_create_proc_connection)
        self.db = None
        self.conf = conf
        self.domain_name = conf.domain
        self.actions = []

    def hanlder_create_proc_connection(self, s, m):
        #根据所给的socket及map构造进程过来的连接实例
        return context.Context(s, m)

    def handle_update(self,diff):
        #在心跳里面主要有三个行为
        #1)守护进程，维护所有的服务器的所有相关进程，以及每台物理机的进程，当进程非正常关闭时自动重启
        #  要实现守护进程的功能,需要维护一份期望的进程列表，及取得现在的进程列表，然后产生相应的操作栈去完成补充进程的目的
        #  启动时先载入所有的物理服务器信息，产生一个初始化理论逻辑服务器的进程列表
        
        #2)操作行为栈，通过一个主动轮询行为栈产生相应的操作栈并且完成后返回继续轮询
        action_num = len(self.actions)
        if action_num > 0 and not self.actions[action_num-1].update(diff):
            self.actions.pop()

    #3)特殊的复合操作，无法通过简单的行为栈自由组合，比如说合服等复杂操作
    def push_action(self,action):
        self.actions.append(action)
    #写操作信息到数据库中的日志
    def writetolog(self, typ, opt_typ, logstr, plan_id=""):
        if not self.db is None:
            self.db.log(typ, opt_typ, logstr,plan_id)
        
    def pdebug(self, opt_typ, log_str, plan_id):
        if self.conf.log_level > 0:
            return
        print "%s	%s	%s"%(opt_typ, time.strftime('%Y-%m-%d %H:%M:%S DEBUG    '), log_str)
    
    def pwarn(self, opt_typ, log_str, plan_id=""):
        if self.conf.log_level > 1:
            return
        print "%s	%s	%s"%(opt_typ, time.strftime('%Y-%m-%d %H:%M:%S WARN     '), log_str)
        self.writetolog('warn', opt_typ, log_str, plan_id)
    
    def perror(self, opt_typ, log_str, plan_id=""):
        if self.conf.log_level > 2:
            return
        print "%s	%s	%s"%(opt_typ, time.strftime('%Y-%m-%d %H:%M:%S ERROR    '), log_str)
        self.writetolog('error', opt_typ, log_str, plan_id)
    
    def pinfo(self, opt_typ, log_str, plan_id=""):
        print "%s	%s	%s"%(opt_typ, time.strftime('%Y-%m-%d %H:%M:%S INFO     '), log_str)
        self.writetolog('info', opt_typ, log_str, plan_id)

def appinstance():
    global app
    return app

def main():
    # 先从启动的参数中获得信息后用于启动
    conf_str = ' '.join(sys.argv[1:])
    if len(conf_str) == 0:
        usage()

    conf = Conf(conf_str)
    if conf.action == 'term':
        if len(conf.domain) == 0:#主机名不可为空
            print 'ERROR:主机名不可为空'
            usage()
    elif conf.action == 'plan':
        conf.domain = 'plan'
    else:
        print 'action 必须为 term(终端) 或者 plan(计划任务)'
        usage()
        
    global app
    # 构造应用程序后尝试开始数据库并且开始监听
    app = SoftMgrAgent(conf)
    tn = telnetlib.Telnet()
    for i in range(1,1000):
        try:
            tn.open(conf.host, conf.port)
            tn.close()
        except:
            tn.close()
            break
        print 'listen %s:%d fail, next try.'%(conf.host,conf.port)
        conf.port = conf.port + 1
    print "listen on %s:%d"%(conf.host,conf.port)
    app.start_listen(conf.host, conf.port)
    # 初始化数据库环境
    #print "connect to mongodb %s@%s:%d/%s  %s"%(conf.db_username,conf.db_host,conf.db_port,conf.db_password,conf.domain)
    try:
        app.db = DBAccess(conf.domain, conf.db_host, conf.db_port, conf.db_username, conf.db_password)
    except Exception as e:
        print 'open db fail!'
        print str(e)
        usage()

    moudel = __import__("action_mgr")   
    moudel.app = app
    app.pinfo('Main','%s 运维工具启动,版本号:15.07.17.001'%app.conf.domain)
    if conf.action == 'term':
        app.push_action(getattr(moudel,"MainAction")())
    else:
        app.push_action(getattr(moudel,"PlanTaskAction")())
    
    # 进入心跳
    sock_app.loop(app,1)
    print "程序正常退出"
     
if __name__ == "__main__":
    main()

