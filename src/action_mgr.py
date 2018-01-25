import os, time, commands, glob, hashlib, urllib, urllib2, sys, share
from command_mgr import CommandMgr
from share import *

post_url, post_key = '',''

class Action():
	def __init__(self):
		global app
		self.__app = app
		self.moudel = globals()  # 反射模块action_mgr中的包含的类
		self.domain = app.conf.domain
		self.server_name = ""
		self.plan_id = ""
		self.centos_info = self.getdb().find_centos_info(self.getconf().domain)

	def action_type(self):
		assert False

	# 返回app
	def getapp(self):
		return self.__app

	#返回数据库对象
	def getdb(self):
		return self.__app.db

	#返回配置参数
	def getconf(self):
		return self.__app.conf

	#返回反射的对象
	def getaction(self, action_str):
		# if hasattr(self.moudel, action_str):        #若模块中存在属性
		#     return getattr(self.moudel, action_str)      #返回一个与action_str同名的类
		if self.moudel.has_key(action_str):
			return self.moudel[action_str]
		return None

	#休眠
	def serversleep(self, seconds):
		time.sleep(seconds)

	#获得端口号
	def getportnu(self, path):
		try:
			with open(path) as f:
				port = int(f.readlines()[0])
				return port
		except IOError:
			self.pwarn("在%s下没有找到centd.port文件" % path)
			return 0

	def pdebug(self, log_str):
		self.getapp().pdebug(self.action_type(), log_str, self.plan_id)

	def pwarn(self, log_str):
		self.getapp().pwarn(self.action_type(), log_str, self.plan_id)

	def perror(self, log_str):
		self.getapp().perror(self.action_type(), log_str, self.plan_id)

	def pinfo(self, log_str):
		self.getapp().pinfo(self.action_type(), log_str, self.plan_id)

	#专用于启动中心服
	def start_cent(self, serverinfo):
		path = serverinfo["path"]
		self.killcent(path)		#启动前先kill
		initpath = os.getcwd()
		os.chdir("/home")
		svr_mgr_path = self.centos_info["server_mgr_git_path"]
		centpath = os.path.normpath(svr_mgr_path + "/centd/centd")
		etcpath = path + os.sep + "etc" + os.sep + "centd.conf"
		logpath = path + os.sep + "log" + os.sep + "_centd.out"
		cent_argv = ["nohup", centpath, "-c", etcpath, ">", logpath, "2>&1", "&"]
		self.pdebug("启动中心服的命令为:" + " ".join(cent_argv))
		os.system(" ".join(["chmod", "-R", "777", path + os.sep + "bin" + os.sep + "*"]))
		if os.system(" ".join(cent_argv)) != 0:
			self.perror("中心服启动失败，启动命令有误:" + " ".join(cent_argv))
			os.chdir(initpath)
			return False
		self.pdebug("中心服启动成功")
		os.chdir(initpath)
		return True
	#启动世界服的中心服
	def start_world_cent(self, serverinfo):
		path = serverinfo["path"]
		initpath = os.getcwd()
		os.chdir("/home")
		svr_mgr_path = self.centos_info["server_mgr_git_path"]
		centpath = os.path.normpath(svr_mgr_path + "/centd/centd")
		etcpath = path + os.sep + "centd.conf"
		logpath = path + os.sep + "log" + os.sep + "_centd.out"
		cent_argv = ["nohup", centpath, "-c", etcpath, ">", logpath, "2>&1", "&"]
		self.pdebug("启动世界服中心服的命令为:" + " ".join(cent_argv))
		os.system(" ".join(["chmod", "-R", "777", path + os.sep + "runcore"]))
		if os.system(" ".join(cent_argv)) != 0:
			self.perror("世界服中心服启动失败，启动命令有误:" + " ".join(cent_argv))
			os.chdir(initpath)
			return False
		self.pdebug("世界服中心服启动成功")
		os.chdir(initpath)
		return True

	#专用于逻辑服务器状态改变
	def change_runstate(self, sername, statecode):
		self.pdebug("修改逻辑服务器%s状态为：%u" % (sername, statecode))
		self.getdb().update_runstate(sername, statecode)

	#专用于关闭中心副
	def killcent(self, despath, isworldserver=False):
		etcpath = os.path.normpath(despath + os.sep + "etc" + os.sep + "centd.conf")
		if isworldserver == True:
			self.pinfo("kill world server centd !")
			etcpath = os.path.normpath(despath + os.sep + "centd.conf")
			#shell = "kill -9 `ps -ef|grep runcore | grep logind_main.lua | grep -v grep|awk {'print $2'}` "
			#self.pdebug(shell)
			#os.system(shell)
		shell = "kill -9 `ps -ef|grep %s|grep -v grep|awk {'print $2'}` " % etcpath
		status, results = commands.getstatusoutput("ps -ef | grep %s | grep -v grep" % etcpath)
		if status == 0:  #进程存在，则执行kill
			self.pdebug(shell)
			return os.system(shell)
	#kill掉进程
	def killotherserver(self, despath, etcpath):
		shell = "kill -9 `ps -ef|grep %s | grep %s |grep -v grep|awk {'print $2'}` " % (despath, etcpath)
		self.pdebug(shell)
		return os.system(shell)

	#关闭网关服
	def killnetgd(self, despath):
		shell = "kill -9 `ps -ef|grep %s%s%s%s%s|grep -v grep|awk {'print $2'}` " % (
			despath, os.sep, "bin", os.sep, "netgd")
		self.pdebug(shell)
		return os.system(shell)

	#关闭客户端安全认证进程
	def killcrossdmd(self, despath):
		shell = "kill -9 `ps -ef|grep %s%s%s%s%s|grep -v grep|awk {'print $2'}` " % (
			despath, os.sep, "bin", os.sep, "crossdmd")
		self.pdebug(shell)
		return os.system(shell)

	#专用于启动网关服
	def start_netgd(self, path):
		#self.killnetgd(path)
		initpath = os.getcwd()
		os.chdir("/home")
		full_name = path + "%sbin%snetgd" % (os.sep, os.sep)
		if not os.path.exists(full_name):
			self.pinfo("启动网关时,文件 %s 不存在!!!" % full_name)
			return False
		netgd_port = self.centos_info["netgd_port"]
		internal_netgd_port = self.centos_info["netgd_internal_port"]
		cent_argv = ["nohup", full_name, "-p", netgd_port, "-P", internal_netgd_port, "-n", "8",
					 " > /home/log/_netgd.out 2>&1", "&"]
		if self.getconf().wulongju != 0:
			cent_argv = ["nohup", full_name, "-H 0.0.0.0", "-p", netgd_port, "-P", internal_netgd_port, "-d", "-n", "8",
						 " > /home/log/_netgd.out 2>&1", "&"]
		self.pdebug("启动网关命令为:" + " ".join(cent_argv))
		if os.system(" ".join(cent_argv)) != 0:
			self.perror("网关服启动失败，启动命令可能有误:" + " ".join(cent_argv))
			os.chdir(initpath)
			return False
		self.pdebug("网关服启动成功")
		os.chdir(initpath)
		return True
	def start_world_netgd(self, path, netgd_port):
		initpath = os.getcwd()
		os.chdir("/home")
		full_name = path + "%sbin%snetgd" % (os.sep, os.sep)
		if not os.path.exists(full_name):
			self.pinfo("启动世界服网关时,文件 %s 不存在!!!" % full_name)
			return False
		netgd_argv = ["nohup", full_name, "-p", str(netgd_port), "-P", str(netgd_port+1),
					 " >> /home/log/_netgd_world.out 2>&1", "&"]
		if self.getconf().wulongju != 0:
			netgd_argv = ["nohup", full_name, "-H 0.0.0.0", "-p", str(netgd_port), "-P", str(netgd_port+1),
						 " >> /home/log/_netgd_world.out 2>&1", "&"]
		self.pdebug("启动世界服网关命令为:" + " ".join(netgd_argv))
		if os.system(" ".join(netgd_argv)) != 0:
			self.perror("世界服网关服启动失败，启动命令可能有误:" + " ".join(netgd_argv))
			os.chdir(initpath)
			return False

		os.chdir(initpath)
		return True

	#客户端安全认证进程
	def start_crossdmd(self, path):
		full_name = path + "%sbin%scrossdmd" % (os.sep, os.sep)
		if not os.path.exists(full_name):
			self.pinfo("启动客户端安全认证时,文件 %s 不存在!!!" % full_name)
			return False
		cent_argv = ["nohup", full_name, "843", ">> /home/log/_crossdmd.out 2>&1", "&"]
		self.pdebug("启动客户端安全认证命令为:" + " ".join(cent_argv))
		if os.system(" ".join(cent_argv)) != 0:
			self.perror("客户端安全认证进程启动失败，启动命令有误:" + " ".join(cent_argv))
			return False
		self.pdebug("客户端安全认证进程启动成功")
		return True

	def generate_data_and_post(self, id, type, domain, pid, servername, run_result):
		#为空则从oper_config配置表load下
		global post_url
		global post_key
		if not post_url or not post_key:
			url = self.getdb().find_post_url()
			key = self.getdb().find_post_key()
			if url is not None and key is not None:
				post_url = url
				post_key = key
		#post地址不为空才post
		if not (post_url and post_key):
			return
		try:
			run_result = str(run_result)
			self.pinfo("post推送数据开始: id %s  , type %s  , domain  %s , pid %s, server_name %s, result %s" % (id, type, domain, pid, servername, run_result))
			sign = hashlib.md5("%s%s%s%s" % (id, type, run_result, post_key)).hexdigest()
			values = {'id': id, 'plan_type': type, 'domain': domain, 'server_name': servername, 'result':run_result, 'pid':pid, 'sign': sign}
			data = urllib.urlencode(values)
			self.pinfo("post数据: %s" % data)
			req = urllib2.Request(post_url, data)
			response = urllib2.urlopen(req)
			result = response.read()
			self.pinfo("post返回值 : %s" % result)
			self.pinfo("post推送数据结束: id %s  , type %s , domain  %s , pid %s, server_name %s, result %s" % (id, type, domain, pid, servername, run_result))
			return result
		except:
			self.perror("post推送数据失败了 %s %s fail." % (id, type))

	# 用于git整个项目迁出
	def git_clone(self, despath, source_path, branch = "master"):
		oldpath = os.getcwd()
		self.pdebug("git 克隆目的路径:" + despath)
		self.pdebug("git 克隆源路径:" + source_path)
		self.pdebug("git 分支:" + branch)
		os.chdir(source_path)
		status, result = commands.getstatusoutput("git branch")
		if status != 0:
			self.perror("克隆前查看远程分支时执行失败,command为: git branch")
			return True
		index = result.find(branch)
		if index == -1:
			self.perror("克隆前没有找到相应的分支, branch: %s"%branch)
			return True
		coargv = ["git", "clone", source_path, despath, "--depth 1"]
		#／home目录下就签出镜像
		#if is_mirror:
			#coargv.append('--mirror')
		self.pdebug("git clone command:" + " ".join(coargv))
		if not os.system(" ".join(coargv)):
			#切到指定的分支
			os.chdir(despath)
			if os.system("git checkout "+branch):
				self.perror("从路径%s克隆到%s后,切到指定分支%s失败!!"%(source_path, despath, branch))
			os.chdir(oldpath)
			return False
		os.chdir(oldpath)
		return True

	#用于git更新,相应的分支存不存在反正外层判断
	def git_update(self, basepath, branch = "master"):
		self.pdebug("git更新路径: updatepath = %s  branch = %s"%(basepath,branch))
		if not os.path.exists(basepath):
			return False
		oldpath = os.getcwd()
		os.chdir(basepath)

		#如果分支为空,而事实上是多分支会导致更新失败
		#先这样处理linbc 20150326
		if branch == None or len(branch) == 0:
			return False

		#执行pull 之前必须先切到相应的分支
		if os.system("git checkout "+branch):
			self.perror("切到指定分支%s失败!!" % branch)
			return False

		upargv2 = ["git", "pull", "origin", branch]
		resultcode = os.system(" ".join(upargv2))
		os.chdir(oldpath)
		if not resultcode:
			self.pdebug("git更新成功%s" % basepath)
			return True
		else:
			self.perror("git更新失败:%s" % basepath)
			return False

	def start_new_tool(self, path):
		full_name = path + "%ssrc%ssoft_mgr_agent.py" % (os.sep, os.sep)
		self.pdebug("启动一个新运维工具路径: %s" % full_name)
		if not os.path.exists(full_name):
			self.pinfo("启动一个新的运维工具时,文件%s不存在!!!" % full_name)
			return False

		params = "--action=" + self.getconf().action + " " + "--db_host=" + self.getconf().db_host + " " + "--db_port=" + str(
			self.getconf().db_port) \
				 + " " + "--db_username=" + self.getconf().db_username + " " + "--db_password=" + self.getconf().db_password \
				 + " " + "--domain=" + self.getconf().domain + " " + "--log_level=" + str(
			self.getconf().log_level) + " " + "--game_db_str=" + self.getconf().game_db_str \
				 + " " + "--wulongju=" + str(self.getconf().wulongju)

		logpath = "/home/log/action." + time.strftime('%Y%m%d', time.localtime(time.time())) + ".log"
		if self.getconf().action == "plan":
			logpath = "/home/log/plan." + time.strftime('%Y%m%d', time.localtime(time.time())) + ".log"
		if self.getconf().wulongju != 0:
			logpath = "/home/log/term." + time.strftime('%Y%m%d', time.localtime(time.time())) + ".log"
			if self.getconf().action == "plan":
				logpath = "/home/log/plan." + time.strftime('%Y%m%d', time.localtime(time.time())) + ".log"
		self.pdebug("启动一个新的运维工具时,日志输出文件logpath = %s" % logpath)
		cent_argv = ["nohup", "python", "-u", full_name, params, ">>", logpath, "2>&1", "&"]
		self.pdebug("启动一个新的运维工具命令为:" + " ".join(cent_argv))
		if os.system(" ".join(cent_argv)) != 0:
			self.perror("运维工具启动失败，启动命令有误:" + " ".join(cent_argv))
			return False
		self.pdebug("运维工具启动成功 action = %s" % self.getconf().action)
		return True

	#配置文件的生成
	def mange_file(self,filename, centport, centd_host, netgdport, loglv, logkey, repath,
				   platform_id, serid, gameid, dbstr, nochangefile, test_type, server_type):
		cat_usual = lambda key, value:key +" = " + value + "\n"
		cat_str = lambda key, value:key +" = " + str(value) + "\n"
		cat_quote = lambda key, value:key +' = "' +str(value)+'"\n'
		with open(filename, mode="wb") as writefile:
			data_conf = CONFIG_DICT[filename]
			for key in data_conf.keys():
				if filename in nochangefile:
					writefile.write(cat_usual(key, data_conf[key]))
					continue
				if key =="centd_port":
					if centport != "10000":
						writefile.write(cat_str(key, centport))
				elif key =="gm_open":
					if self.getconf().wulongju != 0:
						writefile.write(cat_quote(key, "Y"))
				elif key =="check_session_key_time":
					if self.getconf().wulongju != 0:
						writefile.write(cat_quote(key, "N"))
					else:
						writefile.write(cat_usual(key, data_conf[key]))
				elif key =="centd_host":
					if centd_host == "0.0.0.0":
						writefile.write(cat_str(key, centd_host))
					else:
						writefile.write(cat_str(key, data_conf[key]))
				elif key =="db_chars_log":
						value = repath + os.sep + "log" + os.sep + "db_chars"
						writefile.write(cat_usual(key, value))
				#elif key =="logdb_log":
				#		value = repath + os.sep + "log" + os.sep + "logdb_chars"
				#		writefile.write(cat_usual(key, value))
				elif key =="log_folder":
						value =  ' "' + repath + os.sep + "log" + os.sep + '"'
						writefile.write(cat_usual(key, value))
				elif key =="login_key":
						writefile.write(cat_quote(key, logkey))
				elif key =="netgd_port":
						writefile.write(cat_str(key, netgdport))
				elif key =="log_level":
						writefile.write(cat_str(key, loglv))
				elif key =="platform_id":
						writefile.write(cat_str(key, platform_id))
				elif key =="server_id":
						writefile.write(cat_str(key, serid))
				elif key =="db_character":
						writefile.write(cat_str(key, dbstr))
				#elif key == "logdb_character":
				#		writefile.write(cat_str(key, dbstr))
				elif key =="process_method":
						value = data_conf[key].replace("N", "Y")
						writefile.write(cat_usual(key, value))
				elif key =="data_folder":
						value =  ' "' + repath + os.sep + "template/" + '"'
						writefile.write(cat_usual(key, value))
				elif key =="map_folder":
						value = ' "' + repath + os.sep + "maps/" + '"'
						writefile.write(cat_usual(key, value))
				elif key =="script_folder":
						value = ' "' + repath + os.sep + "scripts/" + '"'
						writefile.write(cat_usual(key, value))
				elif key =="etc_folder":
						value =   ' "' + repath + os.sep + "etc/" + '"'
						writefile.write(cat_usual(key, value))
				elif key =="bin_folder":
						value = ' "' + repath + os.sep + "bin/" + '"'
						writefile.write(cat_usual(key, value))
				elif key == "playerinfo_cache_local_hdd_path":
						value = ' "' + repath + os.sep + "var/" + '"'
						writefile.write(cat_usual(key, value))
				elif key == "do_post":
						if self.getconf().wulongju != 0:
							writefile.write(cat_quote(key, "N"))
						else:
							writefile.write(cat_quote(key, "Y"))
				else:
						writefile.write(cat_usual(key, data_conf[key]))
			if writefile.name == "logind.conf":
				s = "game_id " + "=" + " " + str(gameid) + "\n"
				s += "server_type" + " =" + " " + str(server_type) + "\n"
				world_host = self.getdb().find_world_host()
				if world_host != None:
					s += "world_host" + " = " + str(world_host) + "\n"
				world_port = self.getdb().find_world_port()
				if world_port != None:
					s += "world_port" + " = " + str(world_port) + "\n"
				s += "logdb_log" + " = " + repath + os.sep + "log" + os.sep + "logind_logdb_chars.txt\n"
				s += "logdb_character" + " = " + '"' + "127.0.0.1;27017;dev;asdf;;" + '"' + "\n"
				s += "showhand_netgd_host" + " = " + "showhand.tianshu.game2.com.cn\n"
				s += "showhand_netgd_port" + " = " + "2500" + "\n"
				s += "backup_hdd_path" + " = " + repath + os.sep + "var/\n"
				s += "player_data_hdd_path" + " = " + repath + os.sep + "data/\n"
				s += 'conf_svr = "http://127.0.0.1:30080/"\n'
				s += 'ext_web_interface = "http://127.0.0.1:30081/"\n'
				writefile.write(s)
			if writefile.name == "policed.conf":
				s = "game_id " + "=" + " " + str(gameid) + "\n"
				writefile.write(s)
			if writefile.name == "centd.conf":
				s = "s_test_type " + "=" + " " + str(test_type) + "\n"
				writefile.write(s)
			writefile.close()

	#path表示文件生成的路径，repath表示文件生成目录的父目录
	def create_file(self, serverinfo, nochangefile=["netgd.conf", "robotd.conf"],loglv=3):
		#定义不变的量
		serid = serverinfo["sid"] or "0"
		gameid = serverinfo["game_id"] or 0
		platform_id = serverinfo["pid"] or 24
		logkey = serverinfo["login_key"]
		dbstr = self.getconf().game_db_str
		netgdport = self.centos_info["netgd_internal_port"]
		centport = "10000"
		centdhost = "127.0.0.1"
		test_type = serverinfo["s_test_type"]
		if test_type != "1" and self.getconf().wulongju != 0:
			centport = serverinfo["centd_port"]
			centdhost = "0.0.0.0"
		#服务器类型
		server_type = 0
		if serverinfo.has_key("i_server_type"):
			server_type = int(serverinfo["i_server_type"])

		#路径相关的量
		path = os.path.normpath(serverinfo["path"])
		etcpath = path + os.sep + "etc"
		nowpath = os.getcwd()
		os.chdir(etcpath)
		self.pdebug("创建文件:" + path)
		for filename in CONFIG_DICT.keys():
			self.mange_file(filename, centport, centdhost, netgdport, loglv, logkey, path,
							platform_id, serid, gameid, dbstr, nochangefile,test_type, server_type)
		os.chdir(nowpath)

	#生成config.lua配置文件
	def create_config_lua(self, serverinfo):
		svr_instal_path = os.path.normpath(serverinfo["path"])
		robotswitch = "N"
		ischatpost = "N"
		max_player_count = '1000'
		lang = "CN"
		if serverinfo.has_key("params"):
			params = serverinfo["params"].split(',')
			size = len(params)
			if size >= 1:
				ischatpost = params[0]
			if size >= 2:
				robotswitch = params[1]
			if size >= 3:
				max_player_count = params[2]
			if size >= 4:
				lang = params[3]

		oldpath = os.getcwd()
		os.chdir(svr_instal_path + os.sep + "scripts")
		if ischatpost == "N" or ischatpost == "n":
			ischatpost = "false"
		else:
			ischatpost = "true"
		if robotswitch == "N" or robotswitch == "n":
			robotswitch = "false"
		else:
			robotswitch = "true"
		with open("config.lua", "wb") as file:
			file.write("post_chat = "+ischatpost+"\n")
			file.write("changan_robot_open = "+robotswitch+"\n")
			file.write("max_player_count = "+max_player_count+"\n")
			file.write("lang = '" + lang + "'\n")
			file.close()
		os.chdir(oldpath)

class MainAction(Action):
	"""轮询数据库server_opt表，通过反射产生相应的行为对象进入栈顶"""

	def __init__(self):
		Action.__init__(self)
		self.load_server_opt_timer = 0
		self.check_server_timer = 0
		self.check_tarplayerinfo_timer = 0
		self.server_restart_count = {}
		self.LIMITCOUNT = 10
		self.say_hello_count_dict = {}
		self.SAYHELLO_COUNT = 3   #say hello 允许的失败次数

	def action_type(self):
		return "Main"


	def update(self, diff):
		self.load_server_opt_timer -= diff
		self.check_server_timer -= diff
		self.check_tarplayerinfo_timer -= diff
		self.check_netgdserver()

		if (self.check_server_timer <= 0):
			self.check_server_timer = 3000
			#self.pdebug("--------------轮询服务器----------->")
			for singleserver in self.getdb().find_my_server_info():
				server_key = singleserver["server_name"]
				if not self.server_restart_count.has_key(server_key):
					self.server_restart_count[server_key] = 0
				if self.server_restart_count[server_key] >= self.LIMITCOUNT:
					#重启服务器次数超过上限,todo
					self.pinfo("服务器 %s 启动次数已达上限" % server_key)
					continue
				self.check_server(singleserver)
			# 如果是内部运维工具，则终端启动以后，检测有没有自己domain的centos_info信息，若没有，则自动插入
			if self.getconf().wulongju != 0:
				info = self.getdb().find_centos_info(self.domain)
				if info == None:
					self.getdb().save_centos_info(self.domain)

		if (self.load_server_opt_timer <= 0):
			self.load_server_opt_timer = 10000
			#self.pdebug("-----------轮询数据库---------->")
			for every_opt in list(self.getdb().find_server_opts()):  # 只轮询未执行且domain与命令中输入相同的操作
				if every_opt["opt"] == "update":
					self.server_restart_count[every_opt["server_name"]] = 0
				action_str = every_opt["opt"][0].upper() + every_opt["opt"][1:] + "Action"
				self.pinfo("发现个新的操作: %s" % action_str)
				theaction = self.getaction(action_str)(every_opt)
				if theaction:  #theaction非空
					self.pdebug("push " + action_str)
					self.getapp().push_action(theaction)
				else:
					self.perror("action %s create fail, paln id%s" % (action_str, every_opt["plan_task_info_id"]))
				return True
		if (self.check_tarplayerinfo_timer <= 0):
			#self.pdebug("-----------开始打包玩家信息：%s---------->"% self.domain)
			self.check_tarplayerinfo_timer = self.get_tar_time() * 1000      #每天凌晨12点半执行一次
			self.getapp().push_action(self.moudel["CompressPlayerInfoAction"]())
		return True

	def get_tar_time(self):
		#获得当前时间到每天00：30的间隔秒数
		checktime = 0
		now = time.time()
		nowtime = time.localtime(now)
		if nowtime.tm_hour <= 0:
			if nowtime.tm_min < 30:
				checktime = (30 - nowtime.tm_min) * 60
			else:
				checktime = 24 * 3600 - (nowtime.tm_min - 30) * 60
		else:
			if nowtime.tm_min < 30:
				checktime = (30 - nowtime.tm_min) * 60 + (24 - nowtime.tm_hour) * 3600
			else:
				checktime = (24 - nowtime.tm_hour) * 3600 - (nowtime.tm_min - 30) * 60
		return checktime

	def check_netgdserver(self):
		if self.centos_info is None:
			return
		# 检测网关服进程
		if not self.centos_info.has_key("server_mgr_git_path"):
			self.perror("物理服信息表中domain为:%s的配置中没有找到server_mgr的git路径!!!"%self.domain)
			return
		netgdpath = self.centos_info["server_mgr_git_path"]
		if not netgdpath:
			self.perror("物理服信息表中domain为:%s的配置中server_mgr的git路径为空!!!"%self.domain)
			return
		internal_netgd_port = self.centos_info["netgd_internal_port"]
		extern_port = self.centos_info["netgd_port"]
		netgd_status, netgd_results = commands.getstatusoutput(
			"ps -ef | grep %s%sbin%snetgd | grep %d | grep %d | grep -v grep" % (netgdpath, os.sep, os.sep, int(extern_port), int(internal_netgd_port)))
		if netgd_status != 0:  #进程不存在，则重启网关服
			self.pinfo("启动网关服进程 %s " % netgdpath)
			if not self.start_netgd(netgdpath):
				self.perror("网关服启动失败!!!")
				return
			else:
				self.pinfo("网关服启动 success !!!")
		crossmd_status, crossmd_results = commands.getstatusoutput(
			"ps -ef | grep %s%sbin%scrossdmd | grep -v grep" % (netgdpath, os.sep, os.sep))
		if crossmd_status != 0:  #进程不存在，则重启客户端安全验证
			self.pinfo("启动客户端安全验证进程 %s " % netgdpath)
			if not self.start_crossdmd(netgdpath):
				self.perror("客户端安全验证动失败!!!")
				return
			else:
				self.pinfo("客户端安全验证启动 success !!!")
		#轮询世界服网关
		worldsvrinfo = self.getdb().find_world_server_info()
		world_netgd_port = self.getdb().find_world_port()
		if worldsvrinfo is not None and world_netgd_port is not None :
			world_netgd_status, world_netgd_results = commands.getstatusoutput(
			"ps -ef | grep %s%sbin%snetgd | grep %d | grep -v grep" % (netgdpath, os.sep, os.sep, int(world_netgd_port)))
			if world_netgd_status != 0:  #进程不存在，则重启网关服
				self.pinfo("启动世界服网关服进程 %s " % netgdpath)
				if not self.start_world_netgd(netgdpath, int(world_netgd_port)):
					self.perror("世界服网关服启动失败!!!")
					return
				else:
					self.pinfo("世界服网关服启动 success !!!")



	def check_server(self, server_info):
		if self.centos_info is None:
			return
		# 获得中心服路径
		if not self.centos_info.has_key("server_mgr_git_path"):
			self.perror("物理服信息表中domain为:%s的配置中没有找到server_mgr的git路径!!!"%self.domain)
			return
		svr_mgr_path = self.centos_info["server_mgr_git_path"]
		if not svr_mgr_path:
			self.perror("物理服信息表中domain为:%s的配置中server_mgr的git路径为空!!!"%self.domain)
			return

		localpath = server_info["path"]
		server_name = server_info["server_name"]
		self.pdebug("逻辑服务器的安装路径: localpath = %s" % localpath)
		if os.path.exists(localpath):
			etcpath = localpath + os.sep + "etc" + os.sep + "centd.conf"
			centpath = os.path.normpath(svr_mgr_path + "/centd/centd")
			status, results = commands.getstatusoutput("ps -ef | grep %s | grep %s | grep -v grep" % (centpath, etcpath))
			if status != 0:  #进程不存在，则重启中心服
				self.pinfo("ps -ef | grep %s | grep %s | grep -v grep" % (centpath, etcpath))
				self.start_cent(server_info)
				self.server_restart_count[server_name] += 1       #上限次数+1
				if server_info["i_run_status"] != 3:
					self.change_runstate(server_name, 3)
				return
			port = self.getportnu(localpath + os.sep + "log" + os.sep + "centd.port")
			if port == 0:
				self.pinfo("%s port file not found, restart server" % server_name)
				self.start_cent(server_info)
				self.server_restart_count[server_name] += 1       #上限次数+1
				if server_info["i_run_status"] != 3:
					self.change_runstate(server_name, 3)
				return
			#self.pdebug("server_name %s port is %u, say hello." % (server_name, port))
			#if not self.say_hello_count_dict.has_key(server_name):
				#self.say_hello_count_dict[server_name] = 0
			#sayhello_count = self.say_hello_count_dict[server_name]
			#cmd = CommandMgr("127.0.0.1", port)
			#result = cmd.get_status()
			#if result is None:  #没有响应说明服务器已关闭，重启
			#	sayhello_count += 1
			#	self.pinfo("%s say hello fail count %d" % (server_name, sayhello_count))
			#	if sayhello_count >= self.SAYHELLO_COUNT: #say hello次数超过上限则重启中心服
			#		self.pinfo("%s say hello fail count %d, restart server" % (server_name, sayhello_count))
			#		self.say_hello_count_dict[server_name] = 0
			#		self.start_cent(server_info)
			#		self.server_restart_count[server_name] += 1       #上限次数+1
			#		if server_info["i_run_status"] != 3:
			#			self.change_runstate(server_name, 3)
			#	self.say_hello_count_dict[server_name] = sayhello_count
			#else:
			#	self.pdebug("say hello ok.")
			#	self.say_hello_count_dict[server_name] = 0
		else:
			self.perror("轮询服务器的时候, server_name:%s的安装路径:%s不存在" % (server_name, localpath))
			self.change_runstate(server_name, 4)
	#检测世界服中心服
	def check_world_centd(self, server_info):
		svr_mgr_path = self.centos_info["server_mgr_git_path"]
		localpath = server_info["path"]
		server_name = server_info["server_name"]
		self.pdebug("世界服服务器的安装路径: localpath = %s" % localpath)
		if os.path.exists(localpath):
			etcpath = os.path.normpath(localpath + "/centd.conf")
			centpath = os.path.normpath(svr_mgr_path + "/centd/centd")
			status, results = commands.getstatusoutput("ps -ef | grep %s | grep %s | grep -v grep" % (centpath, etcpath))
			if status != 0:  #进程不存在，则重启中心服
				self.pinfo("ps -ef | grep %s | grep %s | grep -v grep" % (centpath, etcpath))
				self.start_world_cent(server_info)
				self.server_restart_count[server_name] += 1       #上限次数+1
				if server_info["i_run_status"] != 3:
					self.change_runstate(server_name, 3)
				return
			port = self.getportnu(localpath + os.sep + "log" + os.sep + "centd.port")
			if port == 0:
				self.pinfo("%s port file not found, restart server" % server_name)
				self.start_world_cent(server_info)
				self.server_restart_count[server_name] += 1       #上限次数+1
				if server_info["i_run_status"] != 3:
					self.change_runstate(server_name, 3)
				return
			self.pdebug("server_name %s port is %u, say hello." % (server_name, port))
			cmd = CommandMgr("127.0.0.1", port)
			result = cmd.get_status()
			if result is None:  #没有响应说明服务器以关闭，重启
				self.pinfo("%s say hello fail, restart server" % server_name)
				self.start_world_cent(server_info)
				self.server_restart_count[server_name] += 1       #上限次数+1
				if server_info["i_run_status"] != 3:
					self.change_runstate(server_name, 3)
			else:
				self.pdebug("say hello ok.")
		else:
			self.perror("轮询世界服服务器的时候, server_name:%s的安装路径:%s不存在" % (server_name, localpath))
			self.change_runstate(server_name, 4)


class OptAction(Action):
	def __init__(self, opt):
		Action.__init__(self)
		self.opt_id = opt["_id"]
		self.plan_id = opt["plan_task_info_id"]
		self.opt_type = opt["opt"]
		self.server_name = opt["server_name"]
		self.param1 = opt["param1"]
		self.param2 = opt["param2"]
		self.serverinfo = self.getdb().find_server_info_by_server_name(self.server_name)

	def post(self, result=0,servername=""):
		pid = ""
		if self.serverinfo is not None:
			pid = self.serverinfo["pid"]
		if len(servername) != 0:
			sign = self.generate_data_and_post(self.plan_id, self.opt_type, self.domain, pid, servername, result)
		else:
			sign = self.generate_data_and_post(self.plan_id, self.opt_type, self.domain, pid, self.server_name, result)


	# 专用于操作完毕后对操作的一些数据进行更新
	def update_database_opt(self, result_code, result_txt):
		self.getdb().update_opts(self.opt_id, long(time.time()), result_code, result_txt)
		return True

	#stop中心服务器
	def mangerstopcent(self, host, port):
		cmd = CommandMgr(host, port)
		result = cmd.stop_centd()
		if result == "succeed":
			return True
		return False
		#return getresultcmdloop(host,port,cmdnumber)

	#对etc中的文件的追加操作
	def addtext(self, filename, addstr):
		try:
			with open(filename, "a") as f:
				f.write(addstr)
		except:
			self.pdebug("写" + addstr + "到" + filename + "失败")

	#用于创建若干的文件在目标目录
	def create_dirtory(self, despath, filelist=["data", "log", "var"]):
		self.pdebug("create_folder path:" + despath)
		basepath = os.getcwd()
		os.chdir(despath)
		for i in filelist:
			os.mkdir(i)
		if not os.path.exists("etc"):
			os.mkdir('etc')

		os.chdir(basepath)

	#更新本机git服务器
	def git_update_domain(self):
		if self.getconf().wulongju != 0:
			return 0
		if not self.centos_info.has_key("contrib_git_path"):
			return 1
		self.pinfo("%s git pull local server begin" % self.getconf().domain)
		basepath = self.centos_info["contrib_git_path"]
		if not os.path.exists(basepath):
			return 2
		#切换到要更新的目录更新完回来
		oldpath = os.getcwd()
		os.chdir(basepath)
		resultcode = os.system("git remote update")
		os.chdir(oldpath)
		if resultcode:
			self.perror("git_update_domain更新失败:%s" % basepath)
			return 3
		self.pinfo("%s git pull local server end" % self.getconf().domain)
		return 0

	def get_git_version(self, path):
		a, b = commands.getstatusoutput("cd %s && git show" % path)
		try:
			s = b.split("\n")[4].split("    ")[1]
		finally:
			return ""
		return s

	def work(self, diff):
		assert False

	def update(self, diff):
		self.getdb().update_opt_running(self.opt_id)
		try:
			self.work(diff)
			#post
		except Exception, e:
			err_str = str(e)
			self.perror("执行出错，抛异常：%s" % err_str)
			self.update_database_opt(RUN_STATIC_FAILED, err_str)
		finally:
			return False

	def create_world_config_file(self):
		oldpath = os.getcwd()
		install_path = self.serverinfo["path"]
		os.chdir(install_path)
		prefix = 'conf.'
		#netgd_host = self.getdb().find_world_host()
		netgd_port = int(self.getdb().find_world_port()) + 1
		log_path = os.path.normpath(install_path+"/log")
		ip_dat_path = os.path.normpath(install_path+"/template/qqwry.dat")
		with open("config.lua", "wb") as file:
			file.write(prefix+"netgd_host = '127.0.0.1'" + "\n")
			file.write(prefix+"netgd_port = "+str(netgd_port)+"\n")
			file.write(prefix+"centd_host = '127.0.0.1'" + "\n")
			file.write(prefix+"log_path = '"+log_path+"'\n")
			file.write(prefix+"mongodb_log_name = '"+os.path.normpath(log_path+"/logindb")+"'\n")
			file.write(prefix+"mongodb_string = '"+self.getconf().game_db_str+"'\n")
			file.write(prefix+"ip_dat_path = '"+ip_dat_path+"'\n")
			if self.getconf().wulongju == 0:
				file.write(prefix+"showhand_same_ip_limit = 'Y'"+"\n")
				file.write(prefix+"is_rand_zbtx_faction_number = 'N'"+"\n")
			else:
				file.write(prefix+"showhand_same_ip_limit = 'N'"+"\n")
				file.write(prefix+"is_rand_zbtx_faction_number = 'Y'"+"\n")
			file.close()
		os.chdir(oldpath)

	def create_world_centd_config_file(self):
		svr_mgr_path = self.centos_info["server_mgr_git_path"]
		svr_mgr_path = os.path.normpath(svr_mgr_path+"/centd")
		oldpath = os.getcwd()
		install_path = self.serverinfo["path"]
		scripts_path = os.path.normpath(svr_mgr_path + "/scripts/")
		log_path = os.path.normpath(install_path+"/log")
		netgd_port = int(self.getdb().find_world_port()) + 1
		os.chdir(install_path)
		with open("centd.conf", "wb") as file:
			file.write('log_folder = "'+log_path+'"\n')
			file.write('bin_folder = "'+install_path+'/"\n')
			file.write("netgd_host = 127.0.0.1"+"\n")
			file.write("netgd_port = "+str(netgd_port)+"\n")
			file.write("log_level = 0"+"\n")
			file.write("centd_host = 127.0.0.1"+"\n")
			file.write("centd_port = 10000"+"\n")
			file.write('script_folder = "'+scripts_path+'"\n')
			file.write("process_method = Y\n")
			file.write("log_name = centd \n")
			file.write("s_test_type = 11"+"\n")
			file.close()
		os.chdir(oldpath)

	def create_start_shell_file(self):
		install_path = self.serverinfo["path"]
		oldpath = os.getcwd()
		os.chdir(install_path)
		#启动登录服脚本
		with open("start_logind.sh", "wb") as file:
			file.write("#!/bin/bash \n")
			file.write("if [ $# -eq 3 ]; then \n")
			file.write("  cd $1 \n")
			file.write("  nohup ./runcore logind_main.lua $2 $3 >> /home/log/_runcore_logind.out 2>&1 &\n")
			file.write("  cd - \n")
			file.write("fi\n")
			file.write("sleep 1\n")
			file.close()
		os.system(" ".join(["chmod", "-R", "777", "start_logind.sh"]))
		#启动应用服脚本
		with open("start_appd.sh", "wb") as file:
			file.write("#!/bin/bash \n")
			file.write("if [ $# -eq 3 ]; then \n")
			file.write("  cd $1 \n")
			file.write("  nohup ./runcore appd_main.lua $2 $3 >> /home/log/_runcore_appd.out 2>&1 &\n")
			file.write("  cd - \n")
			file.write("fi\n")
			file.write("sleep 1\n")
			file.close()
		os.system(" ".join(["chmod", "-R", "777", "start_appd.sh"]))
		os.chdir(oldpath)


class SetupAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.version = self.param1

	def action_type(self):
		return "Setup"

	def check_test_type(self, server_name):
		test_type = self.serverinfo["s_test_type"]
		wulongju = self.getconf().wulongju
		if wulongju == 0 and test_type != "1" and test_type != "11":
			#外网部署时11,特殊处理,认为是世界服的部署
			self.perror("外网部署%s的启动类型不为1" % server_name)
			return False
		if wulongju != 0 and test_type != "1" and test_type != "11":
			try:
				centd_port = self.serverinfo["centd_port"]
			except KeyError, e:
				self.perror("内网部署%s的启动类型为%s时，server_info中需要提供个centd_port字段" % (server_name, test_type))
				return False
			if len(centd_port) == 0:
				return False
			return int(centd_port) != 0
		return True

	def work(self, diff):
		self.pinfo("%s,%s setup action begin" % (self.getconf().domain, self.server_name))
		if self.centos_info is None:
			self.pinfo("domain %s 对应的centos_info没有相应的记录!"%self.getconf().domain)
			return False
		if self.serverinfo is None:
			raise Exception("数据库中没找到server_info")
		if not self.check_test_type(self.server_name):
			self.post(1)
			return False

		login_key = self.serverinfo['login_key']
		if login_key is None:
			raise Exception("没找到游戏登陆密钥")

		branch = "master"
		if self.serverinfo.has_key("branch"):
			branch = self.serverinfo["branch"]

		#创建本地镜像
		update_domain = self.git_update_domain()
		if update_domain == 1:
			self.perror("部署的时候更新镜像库失败, 物理服务器信息中contrib_git_path路径配置没找到, domain = %s, pain id = %s" % (
				self.getconf().domain, self.plan_id))
			self.post(1)
			return False
		elif update_domain == 2:
			self.perror("部署的时候更新镜像库失败,请检查物理服务器信息中contrib_git_path路径配置, pian id = %s" % self.plan_id)
			self.post(1)
			return False
		elif update_domain == 3:
			self.perror("部署的时候更新镜像库失败,git服务器繁忙超时了, pian id = %s" % self.plan_id)
			#git繁忙超时了，10s后再试下
			self.pwarn("休眠10s后再重试下")
			self.serversleep(10)
			update_domain = self.git_update_domain()
			if update_domain == 3:
				#既然10s后重试还是超时那就不继续执行了
				self.perror("更新镜像库还是超时, pian id = %s" % self.plan_id)
				self.post(1)
				return False
		source_path = self.centos_info["contrib_git_path"]
		basepath = self.serverinfo["path"]
		self.pdebug("部署的安装路径为:%s" % basepath)
		despath = basepath
		# 创建路径，并移动到目标路径
		initpath = os.getcwd()  #记录原始路径
		if os.path.exists(despath):
			self.pwarn("domain:%s, server_name:%s 要部署安装的路径已经存在!" % (self.getconf().domain, self.server_name))
			self.update_database_opt(RUN_STATIC_FAILED, "存储路径重复，setup失败！")
			self.post(1)
			return False

		#执行setup任务
		self.pdebug("开始安装部署....")
		if self.git_clone(despath, source_path, branch):
			self.perror("%s,%s git 克隆失败!" % (self.getconf().domain, self.server_name))
			self.update_database_opt(RUN_STATIC_FAILED, "目录迁出失败")
			self.post(1)
			return False
		#先建几个文件夹
		self.create_dirtory(despath)
		local_git_version = self.get_git_version(despath)
		self.pdebug("git 克隆成功!! git版本:%s" % local_git_version)

		#修改etc下的文件，并生成新的同名文件()
		self.pdebug("开始创建配置文件.....")
		etcpath = despath + os.sep + "etc" + os.sep
		self.create_file(self.serverinfo)
		self.create_config_lua(self.serverinfo)
		os.chdir(initpath)
		self.pdebug("恭喜,所有配置文件创建成功!")
		self.update_database_opt(RUN_STATIC_SUCCESS, "恭喜,安装部署成功！！")
		self.getdb().save_server_info_after_setup(self.server_name, local_git_version)
		self.getdb().save_cow_config_server_list(self.server_name, self.server_name)
		self.change_runstate(self.server_name, 2)
		self.post()
		self.pinfo("%s,%s 安装部署成功,部署结束" % (self.getconf().domain, self.server_name))
		server_type = 0
		if self.serverinfo.has_key("i_server_type"):
			server_type = int(self.serverinfo["i_server_type"])
		#存在别名就存到cow_config.server_alias
		if self.serverinfo.has_key("alias"):
			if self.getdb().find_server_alias_by_server_name(self.server_name) is None:
				self.getdb().save_server_alias_info(self.server_name, self.serverinfo["alias"])
			else:
				self.getdb().update_server_alias_info(self.server_name, self.serverinfo["alias"])

		if self.getdb().find_cow_config_by_server_name(self.server_name) is None:
			#主动在cow_config插一条server_info的记录
			self.getdb().save_cow_config_server_info(self.getconf().domain, self.centos_info["netgd_port"],
													 self.server_name, server_type)
		else:
			#已经存在则执行更新
			self.getdb().update_cow_config_server_info(self.getconf().domain, self.server_name)
		return False
	#世界服部署
	def setup_world_server(self):
		world_host = self.getdb().find_world_host()
		if world_host is None:
			self.perror('部署世界服时发现oper_tool.world_config下没有world_host配置,请确认！')
			return False
		world_port = self.getdb().find_world_port()
		if world_port is None:
			self.perror('部署世界服时发现oper_tool.world_config下没有world_port配置,请确认！')
			return False
		#校验路径有没有配
		if not self.centos_info.has_key("world_git_path"):
			self.pinfo("部署世界服时,centos_info中没找到git目录, domain:"% self.getconf().domain)
			return False
		self.pinfo("%s git pull local world server begin" % self.getconf().domain)
		#全部拿下来
		if not self.git_update(self.centos_info["world_git_path"],""):
			return False
		self.pinfo("%s git pull local world server end" % self.getconf().domain)

		world_git_path = self.centos_info["world_git_path"]
		install_path = self.serverinfo["path"]
		self.pdebug("部署的安装路径为:%s" % install_path)
		# 创建路径，并移动到目标路径
		oldpath = os.getcwd()  #记录原始路径
		if os.path.exists(install_path):
			self.pwarn("domain:%s, server_name:%s 要部署安装的路径已经存在!" % (self.getconf().domain, self.server_name))
			self.update_database_opt(RUN_STATIC_FAILED, "存储路径重复，setup失败！")
			return False
		branch = "master"
		if self.serverinfo.has_key("branch"):
			branch = self.serverinfo["branch"]
		#执行setup任务
		self.pdebug("开始安装部署....")
		if self.git_clone(install_path, world_git_path, branch):
			self.perror("%s,%s git 克隆失败!" % (self.getconf().domain, self.server_name))
			self.update_database_opt(RUN_STATIC_FAILED, "目录迁出失败")
			return False
		local_git_version = self.get_git_version(install_path)
		self.pdebug("git 克隆成功!! git版本:%s" % local_git_version)
		self.create_dirtory(install_path, ["log"])

		#生成配置文件
		self.pdebug("开始创建世界服配置文件.....")
		self.pinfo("开始生成config.lua配置")
		self.create_world_config_file()
		self.pinfo("生成config.lua配置结束")
		self.pinfo("开始生成centd.conf配置")
		self.create_world_centd_config_file()
		self.pinfo("生成centd.conf配置结束")
		self.pinfo("生成启动runcore shell脚本")
		self.create_start_shell_file()
		self.pinfo("生成启动runcore shell脚本结束")

		#到这了已经成功了
		self.update_database_opt(RUN_STATIC_SUCCESS, "恭喜,安装部署成功！！")
		self.getdb().save_server_info_after_setup(self.server_name, local_git_version)
		self.getdb().save_cow_config_server_list(self.server_name, self.server_name)
		self.change_runstate(self.server_name, 2)
		self.pinfo("%s,%s 世界服安装部署成功,部署结束" % (self.getconf().domain, self.server_name))
		if self.getdb().find_cow_config_by_server_name(self.server_name) is None:
			#主动在cow_config插一条server_info的记录
			self.getdb().save_cow_config_server_info(self.getconf().domain, self.centos_info["netgd_port"],
													 self.server_name, 0)
		os.chdir(oldpath)
		return True


class StopAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)

	def action_type(self):
		return "Stop"

	def work(self, diff):
		# kill掉中心服,然后将其i_run_status置为5
		self.pinfo("%s,%s 开始执行停服action" % (self.getconf().domain, self.server_name))
		self.change_runstate(self.serverinfo["server_name"], 5)
		despath = self.serverinfo["path"]
		host = "127.0.0.1"
		port = self.getportnu(despath + os.sep + "log" + os.sep + "centd.port")
		if port == 0:
			self.perror("%s,%s 执行停服action时centd.port没找到!"%(self.getconf().domain, self.server_name))
			self.post(1)
			return False
		self.mangerstopcent(host, port)
		self.pdebug("休眠 10")
		self.serversleep(10)
		isworldserver = False
		if self.serverinfo["s_test_type"] == "11":
			isworldserver = True
		self.killcent(despath, isworldserver)
		self.update_database_opt(RUN_STATIC_SUCCESS, "成功停服!")
		self.post()
		self.pinfo("%s,%s 停服action执行结束" % (self.getconf().domain, self.server_name))
		return False

class UpdateAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.version = self.param1
		self.restart_type = self.param2
		self.centd_git_path = self.centos_info["server_mgr_git_path"]

	def action_type(self):
		return "Update"

	def work(self, diff):
		self.pinfo(
			"%s,%s 开始执行更新action, %s,%s" % (self.getconf().domain, self.server_name, self.version, self.restart_type))

		if self.serverinfo is None:
			raise Exception("数据库中没找到server_info")

		#切割更新参数
		update_params = self.restart_type.split(";")
		if len(update_params) != 8:
			self.pinfo('更新方式参数个数不符合要求 %s len %d' % (self.restart_type, len(update_params)))
			self.post(1)
			return False


		despath = self.serverinfo["path"]
		#获得端口号
		host = "127.0.0.1"
		port = self.getportnu(despath + os.sep + "log" + os.sep + "centd.port")
		if update_params[0] == '1':#更新镜像库
			self.pinfo('开始更新镜像库')
			#取得分支名
			branch = "master"
			if self.serverinfo.has_key("branch"):
				branch = self.serverinfo["branch"]

			update_domain = self.git_update_domain()
			if update_domain == 1:
				self.perror("执行更新action的时候更新镜像库失败, 物理服务器信息中contrib_git_path路径配置没找到, domain = %s, pain id = %s" % (
					self.getconf().domain, self.plan_id))
				self.post(1)
				return False
			elif update_domain == 2:
				self.perror("执行更新action的时候更新镜像库失败,请检查物理服务器信息中contrib_git_path路径配置, pian id = %s" % self.plan_id)
				self.post(1)
				return False
			elif update_domain == 3:
				self.perror("执行更新action的时候更新镜像库失败,git服务器繁忙超时了, pian id = %s" % self.plan_id)
				#git繁忙超时了，10s后再试下
				self.pwarn("休眠10s后再重试下")
				self.serversleep(10)
				update_domain = self.git_update_domain()
				if update_domain == 3:
					#既然10s后重试还是超时那就不继续执行了
					self.perror("更新镜像库还是超时, pian id = %s" % self.plan_id)
					self.post(1)
					return False

			self.pdebug("开始更新了....")
			self.pinfo("在domain:%s,server_name:%s 上开始更新服务器 %s" % (self.getconf().domain, self.server_name, despath))

			#判断远程是否有这个分支
			oldpath = os.getcwd()
			os.chdir(despath)
			status, result = commands.getstatusoutput("git branch -r")
			if status != 0:
				self.perror("更新前查看远程分支时执行失败,command为: git branch -r")
				return False
			index = result.find(branch)
			if index == -1:
				self.perror("更新时没有找到相应的分支, branch: %s"%branch)
				return False
			os.chdir(oldpath)
			# 更新本地文件的状态
			if not self.git_update(despath, branch):
				self.update_database_opt(RUN_STATIC_FAILED, despath + "更新失败～～\n")
				self.perror("路径%s的服务更新失败 " % despath)
				self.post(1)
				return False
			self.serversleep(1)

		if update_params[1] == '1':#重启中心服
			self.pinfo('开始重启中心服')
			if port == 0:
				self.update_database_opt(RUN_STATIC_FAILED, "读取端口号失败～～ ")
				self.post(1)
				return False

			#先关闭
			result = self.mangerstopcent(host, port)
			if result == True:
				self.pdebug("休眠10秒后关闭中心副")
				self.serversleep(10)
				self.pdebug("关闭中心副")
				if self.killcent(despath) != 0:
					self.update_database_opt(RUN_STATIC_FAILED, "关闭中心服务失败")
					self.post(1)
					return False
			self.serversleep(1)

		if update_params[2] == '1':#重启数据服
			self.pdebug("开始重启数据服")
			datadpath = despath + os.sep + "etc" + os.sep + "datad.conf"
			status, results = commands.getstatusoutput("ps -ef | grep %s | grep %s | grep -v grep" % (despath, datadpath))
			if status == 0:  #进程存在，则kill
				self.pinfo("ps -ef | grep %s | grep %s | grep -v grep" % (despath, datadpath))
				self.killotherserver(despath, datadpath)
			self.mangerestar(True, "重启数据服")
			self.serversleep(1)

		if update_params[3] == '1':#重启登录服
			self.pdebug("开始重启登录服")		#直接kill掉进程
			logindpath = despath + os.sep + "etc" + os.sep + "logind.conf"
			status, results = commands.getstatusoutput("ps -ef | grep %s | grep %s | grep -v grep" % (despath, logindpath))
			if status == 0:  #进程存在，则kill
				self.pinfo("ps -ef | grep %s | grep %s | grep -v grep" % (despath, logindpath))
				self.killotherserver(despath, logindpath)
			self.mangerestar(True, "重启登录服")
			self.serversleep(1)

		if update_params[4] == '1':#重启应用服
			self.pdebug("开始重启应用服")
			appdpath = despath + os.sep + "etc" + os.sep + "appd.conf"
			status, results = commands.getstatusoutput("ps -ef | grep %s | grep %s | grep -v grep" % (despath, appdpath))
			if status == 0:  #进程存在，则kill
				self.pinfo("ps -ef | grep %s | grep %s | grep -v grep" % (despath, appdpath))
				self.killotherserver(despath, appdpath)
			self.mangerestar(True, "重启应用服")
			self.serversleep(1)

		if update_params[5] == '1':#重启场景服
			self.pdebug("开始重启所有场景服")
			result = self.restar_no_cent(host, port, 1)
			self.mangerestar(result, "所有场景服重启")
			self.serversleep(1)

		if update_params[6] == '1':#重启日志服
			self.pdebug("开始重启日志服")
			policeddpath = despath + os.sep + "etc" + os.sep + "policed.conf"
			status, results = commands.getstatusoutput("ps -ef | grep %s | grep %s | grep -v grep" % (despath, policeddpath))
			if status == 0:  #进程存在，则kill
				self.pinfo("ps -ef | grep %s | grep %s | grep -v grep" % (despath, policeddpath))
				self.killotherserver(despath, policeddpath)
			self.mangerestar(True, "重启日志服")
			self.serversleep(1)

		if update_params[7] == '1':#@脚本
			#@脚本和素材
			self.create_config_lua(self.serverinfo)
			self.serversleep(1)
			self.pinfo('开始@脚本')
			self.scrtmp(host, port)
			self.serversleep(1)

		self.update_database_opt(RUN_STATIC_SUCCESS, "更新成功")
		local_git_version = self.get_git_version(despath)
		self.getdb().update_server_info_update_tm(self.server_name, local_git_version)
		self.pinfo("更新后,重启完成, 启动类型: " + str(self.restart_type) + ",更新路径:" + despath)
		self.pinfo(
			"%s,%s 更新action执行完毕, %s,%s" % (self.getconf().domain, self.server_name, self.version, self.restart_type))
		self.post()
		return False

	def update_world_server(self):
		self.pinfo("%s git pull local world server begin" % self.getconf().domain)
		#全部拿下来
		if not self.git_update(self.centos_info["world_git_path"],""):
			return False
		self.pinfo("%s git pull local world server end" % self.getconf().domain)
		self.pdebug("开始世界服更新了....")
		despath = self.serverinfo["path"]
		self.pinfo("在domain:%s,server_name:%s 上开始更新服务器 %s" % (self.getconf().domain, self.server_name, despath))
		branch = "master"
		if self.serverinfo.has_key("branch"):
			branch = self.serverinfo["branch"]
		#判断远程是否有这个分支
		oldpath = os.getcwd()
		os.chdir(despath)
		status, result = commands.getstatusoutput("git branch -r")
		if status != 0:
			self.perror("更新前查看远程分支时执行失败,command为: git branch -r")
			return False
		index = result.find(branch)
		if index == -1:
			self.perror("更新时没有找到相应的分支, branch: %s"%branch)
			return False
		os.chdir(oldpath)
		# 更新本地文件的状态
		if not self.git_update(despath, branch):
			self.update_database_opt(RUN_STATIC_FAILED, despath + "更新失败～～\n")
			self.perror("路径%s的服务更新失败 " % despath)
			return False

		host = "127.0.0.1"
		port = self.getportnu(despath + os.sep + "log" + os.sep + "centd.port")
		self.pdebug("port = %s"% str(port))
		self.pdebug("更新世界服后启动类型:" + self.restart_type)
		if self.restart_type == "0":   #中心服和runcore都重启
			#中心服重启前先更新中心服
			self.pinfo("世界服中心服重启前先更新中心服,中心服的git路径:%s"%self.centd_git_path)
			if len(self.centd_git_path) == 0:
				self.perror("世界服中心服的路径为空,请确认oper_tool.centos_info的server_mgr_git_path是否为空!")
				self.post(1)
				return False
			if not self.git_update(self.centd_git_path):
				self.pdebug("error: 更新世界服中心服 failed!!!")
				self.post(1)
				return False
			#先关闭
			result = self.mangerstopcent(host, port)
			if result == True:
				self.pdebug("休眠10秒后关闭中心服")
				self.serversleep(10)
				self.pdebug("关闭中心服")
				if self.killcent(despath, True) != 0:
					self.update_database_opt(RUN_STATIC_FAILED, "关闭中心服务失败")
					return False

		elif self.restart_type == "1": #runcore重启， 中心服不重启
			self.pdebug("重启runcore")
			r1 = self.restar_no_cent(host, port, 2)
			self.mangerestar(r1, "runcore重启")
			self.pdebug("成功重启runcore\n")

		self.update_database_opt(RUN_STATIC_SUCCESS, "更新成功")
		local_git_version = self.get_git_version(despath)
		self.getdb().update_server_info_update_tm(self.server_name, local_git_version)
		self.pinfo("更新世界服后,重启完成, 启动类型: " + str(self.restart_type) + ",更新路径:" + despath)
		self.pinfo(
			"%s,%s 更新action执行完毕, %s,%s" % (self.getconf().domain, self.server_name, self.version, self.restart_type))
		return True

	# 获得指令编号
	def getcmdnb(self, path):
		number = 0
		try:  #先读
			f = open(path, "r")
			number = int(f.readlines()[0])
			number = number + 1
			f.close()
		except IOError:  #当第一次读取文件不存在时
			f = open(path, "w")
			f.write(str(number + 1))
			f.close()
		finally:  #再写
			f = open(path, "w")
			f.write(str(number))
			f.close()
			return number

	#重启非中心服的操作
	def restar_no_cent(self, host, port, server_number):
		cmd = CommandMgr(host, port)
		result = cmd.restart_server(server_number)
		if result == "succeed":
			return True
		else:
			return False

	#获得轮询服务结果
	def getresultcmdloop(self, host, port, cmdnumber, seconds=60, persecond=5):
		self.pdebug("操作number：" + cmdnumber)
		overtimes = 0
		while True:
			if overtimes >= seconds / persecond:
				self.pwarn("超时！")
				return None
			cmd = CommandMgr(host, port)
			result = cmd.get_cmd_result(cmdnumber)
			if result == "running":
				self.serversleep(persecond)
				overtimes = overtimes + 1
			else:
				if result == "succeed":
					return True
				else:
					return False

	#处理轮询的操作的结果
	def mangerestar(self, result, typ):
		if result == None:  #超时
			self.update_database_opt(RUN_STATIC_FAILED, typ + "超时")
		elif result == True:
			self.update_database_opt(RUN_STATIC_SUCCESS, typ + "成功")
		else:
			self.update_database_opt(RUN_STATIC_FAILED, typ + "错误")

	#@脚本和素材
	def scrtmp(self, host, port):
		cmd = CommandMgr(host, port)
		cmd.reload_script()
		cmd = CommandMgr(host, port)
		cmd.reload_template()



class HefuAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.despath = self.serverinfo["path"]  # 获得被合服服务器的部署路径
		self.hefu_file = self.despath + os.sep + "var" + os.sep + "is_merge_server.blg"
		self.mergefilepath = self.despath + os.sep + "var"
		self.hefu_timer = 3600000*3  # 五分钟都还没合完就认为是不正常
		self.merge_server_name = self.param1
		self.perror("HefuAction: %s 服合到 %s 服"%(self.server_name, self.merge_server_name))


	def action_type(self):
		return "Hefu"

	def update(self, diff):
		self.getdb().update_opt_running(self.opt_id)
		run_result = True
		self.hefu_timer -= diff
		try:
			run_result = self.work(diff)
			if self.hefu_timer <= 0:
				self.pinfo("%s 合到 %s 时, 合服超时了" % (self.server_name, self.merge_server_name))
				run_result = False
				self.post(1)
				# post
		except Exception, e:
			err_str = str(e)
			self.perror("执行出错，抛异常：%s" % err_str)
			self.update_database_opt(RUN_STATIC_FAILED, err_str)
		finally:
			return run_result


	def work(self, diff):
		status = self.getdb().find_hefu_opt_status(self.server_name, self.merge_server_name)
		self.pdebug("正在心跳检测 %s 服合到 %s 服, 合服状态:%u "%(self.server_name, self.merge_server_name, status))
		if status == 3:
			#检测合服成功
			self.pinfo("检测合服成功 %s 合到 %s " % (self.server_name, self.merge_server_name))
			#生成合服文件
			self.pinfo("生成合服文件: %s"%self.hefu_file)
			if not os.path.exists(self.hefu_file):
				oldpath = os.getcwd()
				os.chdir(self.mergefilepath)
				with open("is_merge_server.blg", "wb") as file:
					file.write("time = "+str(time.time())+"\n")	#当前时间戳
					file.close()
				os.chdir(oldpath)

			#关掉被合服的服务器进程
			self.killcent(self.despath)
			#更新被合服的server_info的状态为已被合服(6)
			self.getdb().update_runstate(self.server_name, 6)
			#更新opt状态，以免重复执行
			self.update_database_opt(RUN_STATIC_SUCCESS, "%s合到%s 合服成功！" % (self.server_name, self.merge_server_name))
			self.post(0,self.server_name)
			return False

		return True

# 内网客户端后台更新action
class UpdateinternalclientAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.clientpath = self.param1  #取出客户端的目录

	def action_type(self):
		return "updateinternalclient"

	def work(self, diff):
		self.pdebug("---------内网客户端后台action执行....")
		oldpath = os.getcwd()
		os.chdir(self.clientpath)
		os.system("svn up")
		if os.path.exists(r"./revision.sh"):
			os.system("./revision.sh")

		os.chdir(oldpath)
		return True


#更新网关服action
class UpdateserverAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.netgd_update_path = self.centos_info["server_mgr_git_path"]

	def action_type(self):
		return "Updateserver"

	def work(self, diff):
		self.pdebug("server_mgr更新....")
		if len(self.netgd_update_path) == 0:
			self.post(1)
			return False
		if not self.git_update(self.netgd_update_path):
			self.pdebug("error: 更新server failed!!!")
			self.post(1)
			return False

		#更新网关服前先停服
		#host = "127.0.0.1"
		#for singleserver in self.getdb().find_my_runing_server_info():
		#	self.pdebug("关闭%s的中心服" % singleserver["server_name"])
		#	despath = singleserver["path"]
		#	isworldserver = False
		#	if singleserver["s_test_type"] == "11":
		#		isworldserver = True
		#	port = self.getportnu(despath + os.sep + "log" + os.sep + "centd.port")
		#	if port != 0:
		#		self.mangerstopcent(host, port)
		#		self.pdebug("休眠 10")
		#		self.serversleep(10)
		#		self.killcent(despath, isworldserver)
		#把网关进程关掉
		#self.killnetgd(self.netgd_update_path)
		#self.killcrossdmd(self.netgd_update_path)
		os.system('ldconfig')
		self.pinfo("server_mgr 更新成功!!!")
		self.post()

		return True


#运维工具自身的更新
class UpdateselfAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.self_update_path = self.centos_info["safe_mgr_git_path"]

	def action_type(self):
		return "Updateself"

	def work(self, diff):
		self.pdebug("------------运维工具自身的更新开始....")
		if len(self.self_update_path) == 0:
			self.perror("运维工具自身更新的git路径为空!!!")
			self.post(1)
			return False
		if not self.git_update(self.self_update_path):
			self.pdebug("error: 运维工具自身的更新 failed!!!")
			self.post(1)
			return False
		self.pdebug("运维工具自身更新成功!!!")
		self.post()
		#启动一个新的，然后把旧的关掉
		if self.start_new_tool(self.self_update_path):
			os._exit(1)  #关掉本进程

		return True


#更新服务器到指定的分支
class UpdatebranchAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.git_branch = self.param1
		self.client_version = ""  #客户端模块版本号
		self.client_moudels = []  #客户端模块
		self.svr_install_path = self.serverinfo["path"]

	def action_type(self):
		return "Updatebranch"

	def work(self, diff):
		self.pdebug("------------更新服务器%s到指定的分支:%s...."%(self.server_name,self.git_branch))
		if len(self.param2) != 0:
			params = self.param2.split(",")
			self.client_version = params[0]
			for i in range(1,len(params)):
				self.client_moudels.append(params[i])

		update_domain = self.git_update_domain()
		if update_domain == 1:
			self.perror("执行更新分支action的时候更新镜像库失败, 物理服务器信息中contrib_git_path路径配置没找到, domain = %s, pain id = %s" % (
				self.getconf().domain, self.plan_id))
			self.post(1)
			return False
		elif update_domain == 2:
			self.perror("执行更新分支action的时候更新镜像库失败,请检查物理服务器信息中contrib_git_path路径配置, pian_id = %s" % self.plan_id)
			self.post(1)
			return False
		elif update_domain == 3:
			self.perror("执行更新分支action的时候更新镜像库失败,git服务器繁忙超时了, pian id = %s" % self.plan_id)
			#git繁忙超时了，10s后再试下
			self.pwarn("休眠10s后再重试下")
			self.serversleep(10)
			update_domain = self.git_update_domain()
			if update_domain == 3:
				#既然10s后重试还是超时那就不继续执行了
				self.perror("更新镜像库还是超时, pian id = %s" % self.plan_id)
				self.post(1)
				return False

		oldpath = os.getcwd()
		os.chdir(self.svr_install_path)
		#不管怎样先更新
		if not self.git_update(self.svr_install_path, ""):
			self.pdebug("error: 更新服务器%s到指定的分支 failed!!!"%self.server_name)
			self.post(1)
			os.chdir(oldpath)
			return False
		#判断远程是否有这个分支
		status, result = commands.getstatusoutput("git branch -r")
		if status != 0:
			self.perror("更新分支后查看远程分支时执行失败,command为: git branch -r")
			self.post(1)
			os.chdir(oldpath)
			return False
		index = result.find(self.git_branch)
		if index == -1:
			self.perror("更新分支后没有找到相应的分支, branch: %s"%self.git_branch)
			self.post(1)
			os.chdir(oldpath)
			return False
		#对应的分支存在,则切到相应的分支
		if not os.system("git checkout "+self.git_branch):
			self.pdebug("更新服务器%s到指定的分支%s 成功!!!"%(self.server_name,self.git_branch))
			self.getdb().update_server_info_branch(self.server_name, self.git_branch)
			#插入相应的客户端模块版本号
			if len(self.client_version) != 0 and len(self.client_moudels) != 0:
				for val in self.client_moudels:
					desc = "更新服务器"+self.server_name+"到指定的分支"+self.git_branch+"成功后,插入客户端模块版本号:"+self.client_version+"模块:"+val
					self.getdb().save_client_opt(self.server_name, int(val), self.client_version, desc)
			self.post()
		else:
			self.perror("更新服务器%s到指定的分支%s 后,切换时失败!!!"%(self.server_name,self.git_branch))
			self.post(1)
		return True

class UpdateconfigfileAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)

	def action_type(self):
		return "Updateconfigfile"

	def work(self, diff):
		# kill掉中心服,然后将其i_run_status置为5
		self.pinfo("%s,%s 开始执行重新生成游戏服配置action" % (self.getconf().domain, self.server_name))
		self.create_file(self.serverinfo)  #更新的时候就补充下生成配置文件了
		self.create_config_lua(self.serverinfo)
		self.post()
		self.pinfo("%s,%s 重新生成游戏服配置action执行结束" % (self.getconf().domain, self.server_name))
		return False

class HoutaiAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)

	def action_type(self):
		return "Houtai"

	def work(self, diff):
		# 后台命令执行action
		self.pinfo("%s,%s 后台命令执行action" % (self.getconf().domain, self.server_name))
		if self.serverinfo is None:
			self.pinfo('逻辑服%s不存在'% self.server_name)
			return False

		host = "127.0.0.1"
		port = self.getportnu(self.serverinfo['path'] + os.sep + "log" + os.sep + "centd.port")
		cmd = CommandMgr(host, port)
		self.pinfo('save_houtai: server_name %s data_str %s'%(self.server_name, self.param1))
		cmd.send_to_game_svr(self.param1)
		self.pinfo("%s,%s 后台命令执行action" % (self.getconf().domain, self.server_name))
		return False

class SavealldatatodbAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)

	def action_type(self):
		return "Savealldatatodb"

	def work(self, diff):
		# 后台命令执行action
		self.pinfo("%s,%s 执行SavealldatatodbAction" % (self.getconf().domain, self.server_name))
		if self.serverinfo is None:
			self.pinfo('逻辑服%s不存在'% self.server_name)
			return False

		host = "127.0.0.1"
		port = self.getportnu(self.serverinfo['path'] + os.sep + "log" + os.sep + "centd.port")
		cmd = CommandMgr(host, port)
		self.pinfo('Savealldatatodb: server_name %s'%(self.server_name))
		cmd.send_to_game_svr_savedb()
		self.pinfo("%s,%s 执行Savealldatatodb 结束" % (self.getconf().domain, self.server_name))
		return False

class PlanTaskAction(Action):
	def __init__(self):
		Action.__init__(self)
		oldpath = os.getcwd()
		curpath = os.path.realpath(__file__)
		curpath = os.path.dirname(curpath)
		os.chdir(curpath)
		os.chdir("..")
		self.self_update_path = os.getcwd()
		os.chdir(oldpath)
		self.pdebug("-----------> 计划任务更新路径:%s " % self.self_update_path)


	def action_type(self):
		return "Plan"

	def update(self, diff):
		self.pdebug("--------------- 轮询计划任务 -------------->")
		for plan in list(self.getdb().find_plan_task_info()):
			plan_id = plan["_id"]
			self.plan_id = plan_id
			plan_type = plan["plan_type"]
			param = plan["param"]
			desc = plan["desc"]
			self.pinfo('轮询到一个新的计划任务, 任务id:%s,任务类型:%s,任务参数%s,任务描述:%s' % (plan_id, plan_type, param, desc))
			params = param.split(',')
			result = -1
			if plan_type == "setup":
				result = self.save_setup_opt(plan_id, params, desc)
			elif plan_type == "update":
				result = self.save_update_opt(plan_id, params, desc)
			elif plan_type == "hefu":
				result = self.save_hefu_opt(plan_id, params, desc)
			elif plan_type == "huidang":
				result = self.save_huidang_opt(plan_id, params, desc)
				self.post(plan_id, plan_type)
			elif plan_type == "stop":
				result = self.save_stop_opt(plan_id, params, desc)
			elif plan_type == "start":
				result = self.save_start_opt(plan_id, params, desc)
				self.post(plan_id, plan_type)
			elif plan_type == "client":
				result = self.save_client_opt(plan_id, params, desc)
			elif plan_type == "update_server_mgr":
				result = self.save_update_server_opt(plan_id, params, desc)
			elif plan_type == "update_self":
				result = self.save_update_self_opt(plan_id, params, desc)
			elif plan_type == "update_internal_client":
				result = self.save_update_internal_client_opt(plan_id, params, desc)
			elif plan_type == "update_branch":
				result = self.save_update_branch_opt(plan_id, params, desc)
			elif plan_type == "change_open_time":
				result = self.change_open_time_opt(plan_id, params, desc)
				self.post(plan_id, plan_type)
			elif plan_type == "update_configfile":
				result = self.update_configfile(plan_id, params, desc)
				self.post(plan_id, plan_type)
			elif plan_type == "houtai":
				result = self.save_houtai(plan_id, params, desc)
				self.post(plan_id, plan_type)
			elif plan_type == "savealldatatodb":
				result = self.save_savealldatatodb(plan_id, params, desc)
				self.post(plan_id, plan_type)
			if result == -1:
				self.perror("没有找到对应的计划任务类型:%s"%plan_type)
				self.getdb().update_plan_task_info(plan_id, 3)
			elif result == 0:
				self.getdb().update_plan_task_info(plan_id, 1)
				if plan_type == "update_self":
					#计划任务也重启下
					self.pdebug("计划任务更新路径: %s" % self.self_update_path)
					if not self.git_update(self.self_update_path):
						self.pdebug("error: 计划任务的更新 failed!!!")
						return False
					if self.start_new_tool(self.self_update_path):
						os._exit(1)  #关掉本进程
			else:
				self.perror("计划任务执行失败,plan_type:%s  plan_id:%s"%(plan_type, plan_id))
				self.getdb().update_plan_task_info(plan_id, 3)

		self.serversleep(2)
		return True

 	def post(self, id, type, domain="", server_name="", result=0, pid=""):
		sing = self.generate_data_and_post(id, type, domain, pid, server_name,result)



	def get_domain(self, server_name):
		info = self.getdb().find_server_info_by_server_name(server_name)
		if info != None:
			return info["domain"]
		return None

	def get_netgd_port(self, domain):
		info = self.getdb().find_centos_info(domain)
		if info != None:
			return info["netgd_port"]
		return None

	def save_setup_opt(self, plan_id, params, desc):
		server_name = params[0]
		domain = self.get_domain(server_name)
		if domain == None:
			self.perror("部署服务器%s前请先在server_info中添加相应的逻辑服信息" % server_name)
			return 1
		netgd_port = self.get_netgd_port(domain)
		if netgd_port is None:
			self.perror("部署服务器%s时,相应的物理服务器信息中没有找到网关端口" % server_name)
			return 1
		# if self.getconf().wulongju == 0:
		# 	if self.getdb().find_cow_config_by_server_name(server_name) is None:
		# 		self.perror("部署%s前请先在cow_config下插入相应的server_info信息"%server_name)
		# 		return 1
		git_version = params[1]
		self.save_addr_info(domain, netgd_port, server_name)
		self.getdb().save_setup_opt(plan_id, domain, server_name, git_version, desc)

		serverinfo = self.getdb().find_server_info_by_server_name(server_name)
		if serverinfo is not None and serverinfo.has_key("merge_server_names"):
			#服务器迁移
		  	temp_list = self.handle_str_to_list(serverinfo["merge_server_names"])
			for svr_name in temp_list:
				self.save_addr_info(domain, netgd_port, svr_name)
		return 0

	def save_update_server_opt(self, plan_id, params, desc):
		update_type = int(params[0])
		if update_type == 1:  #更新指定的domain
			domain = params[1]
			self.getdb().save_update_server_opt(plan_id, domain, desc)
		elif update_type == 0:  #更新所有
			for centosinfo in self.getdb().find_all_centos_info():
				domain = centosinfo["domain"]
				self.getdb().save_update_server_opt(plan_id, domain, desc)
		return 0

	def save_update_self_opt(self, plan_id, params, desc):
		update_type = int(params[0])
		if update_type == 1:  #更新指定的domain
			domain = params[1]
			self.getdb().save_update_self_opt(plan_id, domain, desc)
		elif update_type == 0:  #更新所有
			for centosinfo in self.getdb().find_all_centos_info():
				domain = centosinfo["domain"]
				self.getdb().save_update_self_opt(plan_id, domain, desc)
		return 0

	def save_update_opt(self, plan_id, params, desc):
		git_version = params[0]
		update_type = params[1]
		server_type = params[2]
		merge_server_names = ""
		if server_type == "0":
			server_name = params[3]
			domain = self.get_domain(server_name)
			if self.getdb().find_server_info_by_server_name(server_name) is None:
				self.perror("更新%s时没有找到相应的逻辑服信息,请确认!!!"%server_name)
				return 1
			merge_server_names = self.get_merge_server_names(server_name)
			self.getdb().save_update_opt(plan_id, domain, server_name, git_version, update_type, desc,
										 merge_server_names)
		elif server_type == "1":
			for singleserver in self.getdb().find_all_server_info():
				domain = singleserver["domain"]
				server_name = singleserver["server_name"]
				merge_server_names = self.get_merge_server_names(server_name)
				self.getdb().save_update_opt(plan_id, domain, server_name, git_version, update_type, desc,
											 merge_server_names)
		elif server_type == "2":
			pid = params[3]
			for singleserver in self.getdb().find_server_info_by_pid(pid):
				domain = singleserver["domain"]
				server_name = singleserver["server_name"]
				merge_server_names = self.get_merge_server_names(server_name)
				self.getdb().save_update_opt(plan_id, domain, server_name, git_version, update_type, desc,
											 merge_server_names)
		elif server_type == "3":
			pid = params[3]
			sid_begin = int(params[4])
			sid_end = int(params[5])
			for singleserver in self.getdb().find_server_info_by_pid(pid):
				sid = int(singleserver["sid"])
				if sid >= sid_begin and sid <= sid_end:
					domain = singleserver["domain"]
					server_name = singleserver["server_name"]
					merge_server_names = self.get_merge_server_names(server_name)
					self.getdb().save_update_opt(plan_id, domain, server_name, git_version, update_type, desc,
												 merge_server_names)
		elif server_type == "4":
			branch = params[3]
			for singleserver in self.getdb().find_server_info_by_branch(branch):
				domain = singleserver["domain"]
				server_name = singleserver["server_name"]
				merge_server_names = self.get_merge_server_names(server_name)
				self.getdb().save_update_opt(plan_id, domain, server_name, git_version, update_type, desc,
											 merge_server_names)
		return 0

	def save_update_branch_opt(self, plan_id, params, desc):
		size = len(params)
		git_branch = params[0]
		server_name = params[1]
		moudels = params[2:]
		moudels = ",".join(moudels) #再用逗号拼接成字串
		domain = self.get_domain(server_name)
		if domain is None:
			self.perror("更新%s分支%s时没有找到相应的逻辑服信息,请确认!!!"%(server_name, git_branch))
			return 1

		self.getdb().save_update_branch_opt(plan_id, domain, server_name, git_branch, moudels, desc)
		return 0

	#通过servname取得被合服到改服的所有子服
	def get_merge_server_names(self, server_name):
		serverinfo = self.getdb().find_server_info_by_server_name(server_name)
		result = ""
		if serverinfo is None:
			return result
		if serverinfo.has_key("merge_server_names"):
			result = serverinfo["merge_server_names"]
		return result

	def save_update_internal_client_opt(self, plan_id, params, desc):
		clientpath = params[0]
		domain = "192.168.3.6"
		if len(params) == 2:
			domain = params[1]
		self.getdb().save_update_internal_client_opt(plan_id, domain, clientpath, desc)
		return 0

	def save_hefu_opt(self, plan_id, params, desc):
		server_name = params[0]
		domain = self.get_domain(server_name)
		netgd_port = self.get_netgd_port(domain)
		serverinfo = self.getdb().find_server_info_by_server_name(server_name)
		if serverinfo is None:
			self.perror("保存合服操作时server_name为%s的逻辑服信息不存在,请确认!!!" % server_name)
			return 1
		cowserverinfo = self.getdb().find_cow_config_by_server_name(server_name)
		if cowserverinfo is None:
			self.perror("保存合服操作时,cow_config下的server_info集合中没有找到server_name为%s的信息，请确认!!!" % server_name)
			return 1
		for i in range(1, len(params)):
			merge_server_name = params[i]
			merge_serverinfo = self.getdb().find_server_info_by_server_name(merge_server_name)
			if merge_serverinfo is None:
				self.perror("保存合服操作时server_name为%s的逻辑服信息不存在,请确认!!!" % merge_server_name)
				return 1
			cowserverinfo = self.getdb().find_cow_config_by_server_name(merge_server_name)
			if cowserverinfo is None:
				self.perror("保存合服操作时,cow_config下的server_info集合中没有找到server_name为%s的信息，请确认!!!" % merge_server_name)
				return 1

		merge_server_names = ""
		if serverinfo.has_key("merge_server_names"):
			merge_server_names = serverinfo["merge_server_names"]
		for i in range(1, len(params)):
			merge_server_name = params[i]
			self.save_addr_info(domain, netgd_port, merge_server_name)
			#维护下子服
			if len(merge_server_names) == 0:
				merge_server_names = merge_server_name
			else:
				merge_server_names = merge_server_names + "," + merge_server_name
			merge_serverinfo = self.getdb().find_server_info_by_server_name(merge_server_name)
			temp_merge_server_names = ""
			if merge_serverinfo.has_key("merge_server_names"):
				temp_merge_server_names = merge_serverinfo["merge_server_names"]
				temp_list = self.handle_str_to_list(temp_merge_server_names)
				for svr_name in temp_list:
					self.save_addr_info(domain, netgd_port, svr_name)
			if len(temp_merge_server_names) != 0:
				merge_server_names = merge_server_names + "," + temp_merge_server_names
			merge_domain = self.get_domain(merge_server_name)
			self.getdb().save_hefu_opt(merge_server_name, server_name)
			self.getdb().save_hefu_opt1(plan_id, merge_domain, merge_server_name, server_name, desc)
		svr_name_list = self.handle_str_to_list(merge_server_names)
		merge_server_names = self.handle_list_to_str(svr_name_list)
		self.getdb().update_server_info_merge_server_names(server_name, merge_server_names)

		return 0

	def save_huidang_opt(self, plan_id, params, desc):
		server_name = params[0]
		player_guid = params[1]
		tm = params[2]
		domain = self.get_domain(server_name)
		if domain is None:
			self.perror("回档的时候没有找到%s对应的domain信息,请确认!!!"%server_name)
			return 1
		self.getdb().save_huidang_opt(plan_id, domain, server_name, player_guid, tm, desc)
		return 0

	def save_stop_opt(self, plan_id, params, desc):
		server_name = params[0]
		domain = self.get_domain(server_name)
		if domain is None:
			self.perror("停服的时候没有找到%s对应的domain信息,请确认!!!"%server_name)
			return 1
		self.getdb().save_stop_opt(plan_id, domain, server_name, desc)
		return 0

	def save_start_opt(self, plan_id, params, desc):
		server_name = params[0]
		self.change_runstate(server_name, 3)
		return 0

	def update_configfile(self, plan_id, params, desc):
		server_name = params[0]
		domain = self.get_domain(server_name)
		if domain is None:
			self.perror("生成配置时没有找到%s对应的domain信息,请确认!!!"%server_name)
			return 1
		self.getdb().save_update_configfile_opt(plan_id, domain, server_name, desc)
		return 0

	def save_houtai(self, plan_id, params, desc):
		#print params
		server_name = params[0]
		data_str = params[1]
		domain = self.get_domain(server_name)
		if domain is None:
			self.perror("生成配置时没有找到%s对应的domain信息,请确认!!!"%server_name)
			return 1
		self.getdb().save_houtai_opt(plan_id, domain, server_name, data_str, desc)
		return 0

	def save_savealldatatodb(self, plan_id, params, desc):
		typed = params[0]

		if typed == '0':
			if len(params) != 2:
				self.perror("参数个数%d != 2 typed:%s"%(len(params), typed))
				return 1
			server_name = params[1]
			#print "----------> typed == 0 ", server_name
			domain = self.get_domain(server_name)
			if domain is None:
				self.perror("保存的时候没有找到%s对应的domain信息,请确认!!!"%server_name)
				return 1

			self.getdb().save_savealldatatodb_opt(plan_id, domain, server_name, desc)
		elif typed == '1':
			for singleserver in self.getdb().find_all_server_info():
				domain = singleserver["domain"]
				server_name = singleserver["server_name"]
				#print "----------> typed == 1 ", server_name
				self.getdb().save_savealldatatodb_opt(plan_id, domain, server_name, desc)

		elif typed == '2':
			if len(params) != 2:
				self.perror("参数个数%d != 2 typed:%s"%(len(params), typed))
				return 1
			pid = params[1]
			for singleserver in self.getdb().find_server_info_by_pid(pid):
				domain = singleserver["domain"]
				server_name = singleserver["server_name"]
				#print "----------> typed == 2 ", pid, server_name
				self.getdb().save_savealldatatodb_opt(plan_id, domain, server_name, desc)

		elif typed == "3":
			if len(params) != 4:
				self.perror("参数个数%d != 4 typed:%s"%(len(params), typed))
				return 1
			pid = params[1]
			sid_begin = int(params[2])
			sid_end = int(params[3])
			for singleserver in self.getdb().find_server_info_by_pid(pid):
				sid = int(singleserver["sid"])
				if sid >= sid_begin and sid <= sid_end:
					domain = singleserver["domain"]
					server_name = singleserver["server_name"]
					#print "----------> typed == 3 ", pid, server_name
					self.getdb().save_savealldatatodb_opt(plan_id, domain, server_name, desc)
		return 0


	def change_open_time_opt(self, plan_id, params, desc):
		server_name = params[0]
		open_time = long(params[1])
		self.getdb().update_open_time_by_server_name(server_name, open_time)

		return 0

	def save_client_opt(self, plan_id, params, desc):
		if len(params) < 3:
			self.perror("参数个数%d < 3"%(len(params)))
			return 1
		moudel = int(params[0])
		version = params[1]
		server_type = params[2]
		if server_type == "0":
			if len(params) != 4:
				self.perror("参数个数%d != 4 server_type:%s"%(len(params), server_type))
				return 1
			server_name = params[3]
			self.post(plan_id, "client", "", server_name)
			self.getdb().save_client_opt(server_name, moudel, version, desc)
		elif server_type == "1":
			for singleserver in self.getdb().find_all_server_info():
				server_name = singleserver["server_name"]
				self.post(plan_id, "client", "", server_name)
				self.getdb().save_client_opt(server_name, moudel, version, desc)
		elif server_type == "2":
			if len(params) != 4:
				self.perror("参数个数%d != 4 server_type:%s"%(len(params), server_type))
				return 1
			pid = params[3]
			for singleserver in self.getdb().find_server_info_by_pid(pid):
				server_name = singleserver["server_name"]
				self.post(plan_id, "client", "", server_name)
				self.getdb().save_client_opt(server_name, moudel, version, desc)
		elif server_type == "3":
			if len(params) != 6:
				self.perror("参数个数%d != 6 server_type:%s"%(len(params), server_type))
				return 1
			pid = params[3]
			sid_begin = int(params[4])
			sid_end = int(params[5])
			for singleserver in self.getdb().find_server_info_by_pid(pid):
				sid = int(singleserver["sid"])
				if sid >= sid_begin and sid <= sid_end:
					server_name = singleserver["server_name"]
					self.post(plan_id, "client", "", server_name)
					self.getdb().save_client_opt(server_name, moudel, version, desc)
		return 0
	def save_addr_info(self, domain, port, server_name):
		host_port = domain + ":" + port
		all_info = self.getdb().find_addr_info()
		need_update = False
		find_hp = False
		for info in all_info:
			sn_list = info["server_name_list"].split(';')
			sn_count = len(sn_list)
			need_save = False
			if host_port == info["host_port"]:
				find_hp = True
				find_sn = False
				for i in range(0, sn_count):
					if sn_list[i] == server_name:
						find_sn = True
						break
				if find_sn == False:
					need_save = True
					sn_list.append(server_name)
			else:
				for i in range(0, sn_count):
					if sn_list[i] == server_name:
						need_save = True
						del sn_list[i]
						break
			if need_save:
				need_update = True
				sn_list_str = ';'.join(sn_list)
				self.pinfo("update addr info %s    %s" % (host_port, sn_list_str))
				self.getdb().update_addr_info(info["host_port"], sn_list_str)
		if find_hp == False:
			need_update = True
			self.getdb().save_addr_info(host_port, server_name)
		if need_update:
			self.pinfo("addr info update sing")
			self.getdb().update_addr_info_sign()
	def handle_str_to_list(self, basestr):
		strlist = []
		midlist = []
		pre = None
		if len(basestr) == 0:
			return strlist

		for s in basestr.split(","):
			if s.find("~") != -1:
				midlist = s.split("~")
			else:
				if s not in strlist: strlist.append(s)
			if midlist:
				pre, start = midlist[0].split("_")
				end = midlist[1].split("_")[1]
				for i in range(int(start), int(end) + 1):
					st = pre + "_" + str(i)
					#print st
					if st not in strlist: strlist.append(st)
		vallist = []
		for val in strlist:
			if pre is None:
				pre = val.split("_")[0]
			vallist.append(int(val.split("_")[1]))
		strlist = []
		vallist.sort()
		for val in vallist:
			strlist.append(pre+"_"+str(val))

		return strlist

	def handle_list_to_str(self, baselist):
		finally_list = []
		str_dict = {}
		for st in baselist:
			pre, num = st.split("_")
			num = int(num)
			try:
				if (isinstance(str_dict[pre], list)):
					if num not in str_dict[pre]: str_dict[pre].append(num)
			except:
				str_dict[pre] = []
				str_dict[pre].append(num)
		for keypre in str_dict.keys():
			numlist = str_dict[keypre]
			i = 0
			while i < len(numlist):
				start = numlist[i]
				end = None
				while True:
					if i < len(numlist) - 1 and numlist[i] + 1 == numlist[i + 1]:
						i += 1
					else:
						end = numlist[i]
						break
				i += 1
				#添加到finally_list中
				if start == end:
					finastr = keypre + "_" + str(start)
				else:
					finastr = keypre + "_" + str(start) + "~" + keypre + "_" + str(end)
				finally_list.append(finastr)
		return ",".join(finally_list)


#玩家信息压缩
class CompressPlayerInfoAction(Action):
	def __init__(self):
		Action.__init__(self)
		self.pathlist = self.get_path_list()
		self.homedatapath = r'/data'

	def action_type(self):
		return "CompressPlayerInfoAction"

	def update(self, diff):
		try:
			for everypath in self.pathlist:
				datepath = os.path.normpath(self.homedatapath) + os.sep + os.path.split(everypath)[1]
				self.get_needtar_files(everypath, datepath)
		except Exception, e:
			self.perror("打包失败%s"% e)
		finally:
			return False

	def get_path_list(self):
		server_path_list = []
		server_info = self.getdb().find_server_info_by_domain(self.domain)
		for info in server_info:
			if info['server_name'] != "world_server": #世界服就不需要压缩备份了
				server_path_list.append(info["path"])
		return server_path_list

	def get_needtar_files(self, path, datepath, interval=1):
		'''
        path表示需要打包文件的所在服务器路径
        datapath表示文件打包后，压缩包所存放的路径
        interval表示当前日期偏移的天数
        '''
		path = os.path.normpath(path)
		path += os.sep + "var"
		cacultime = time.time() - 86400 * interval
		finatimestr = str(time.strftime("%Y%m%d", time.localtime(cacultime)))
		if not os.path.exists(path):
			# self.perror("%s 路径不存在！" % path)
			return
		file_list = os.listdir(path)
		tar_dict = {}
		for f in file_list:
			if not os.path.isdir(path + os.sep + f):
				continue
			if len(f) != 12 :
				continue
			tar_key = f[:8]  #获得当前年月日作为键
			if tar_key < finatimestr:
				if not tar_dict.has_key(tar_key):
					tar_dict[tar_key] = []
				#将符合当前条件年月日的文件加入对应的列表
				tar_dict[tar_key].append(f)
		#进行批量打包和删除
		for day in tar_dict.keys():
			if not os.path.exists(datepath):
				self.pdebug("------->create tar path: %s"% datepath)
				if (os.system(" ".join(["mkdir", "-p", datepath])) != 0):
					self.pdebug("%s 存放路径创建失败" % datepath)
					return
			tar_despath = os.path.join(datepath, day + ".tar.gz")
			files_str = os.path.join(path, day + "*")
			self.pdebug("打包路径：%s, 存放路径:%s" % (path, tar_despath))
			tarcmd = ["tar", "-zcPf", tar_despath, files_str]
			rmcmd = ["rm", "-rf", files_str]
			if (os.system(" ".join(tarcmd)) != 0):
				self.pdebug("%s 压缩失败！" % day)
				return
			if (os.system(" ".join(rmcmd))):
				self.pdebug("%s 删除失败！" % day)
				return
			self.pdebug("玩家信息打包成功！～")


#回档
class HuidangAction(OptAction):
	def __init__(self, opt):
		OptAction.__init__(self, opt)
		self.homedatapath = r"/data"   #打包的回档信息根路径

	def action_type(self):
		return "HuidangAction"

	def handle_player_huidang(self, path, playerguid, backtimestr):
		path = os.path.normpath(path)
		#确定各种路径
		destipath = path + os.sep +"var"    #玩家回档信息最终存放路径
		file_name = playerguid + ".blg"
		self.pinfo("路径 %s   %s"%(destipath, backtimestr))
		if not os.path.exists(destipath):
			self.perror("回档的时候路径不存在: %s"%destipath)
			return False
		file_list = os.listdir(destipath)
		#两种情况：1.当前路径找到了   2.当前路径没有，只能去解压
		if backtimestr in file_list:  #还要判断玩家的文件夹有没有在这个时间内
			playerhddpath = destipath + os.sep + backtimestr
			file_list2 = os.listdir(playerhddpath)
			if file_name in file_list2:
				return True

		self.pinfo("找不到文件夹")
		#当前路径下没有
		#根据规则拼接压缩路径 ex: /data/12j_client/20150108.tar.gz
		tarpath = os.path.normpath(self.homedatapath) + os.sep + os.path.split(path)[1]
		for tar_file in os.listdir(tarpath):
			if tar_file.find(backtimestr[:8]) != -1:
				#将解压缩的路径变更
				tar_file_path = os.path.join(tarpath, tar_file)
				playertarpath = destipath + os.sep + backtimestr + os.sep + file_name  #解压绝对路径
				tar_cmd = ["tar", "zxvPf", tar_file_path, playertarpath]
				if(os.system(" ".join(tar_cmd)) == 0):
					return True #解压成功的话直接就解压到目标路径了 ,回档完成后就不删除了，等下一次备份硬盘的时候自然就盖成新的了
				else:
					self.perror("解压文件时没有对应玩家信息. 解压的文件绝对路径为:%s"%playertarpath)
					return False
		self.pinfo("解压缩文件失败，应该是找不到文件夹")
		return False

	def work(self, diff):
		#1.找到端口，发送送回档信息
		self.pinfo("开始回档: 服务器名：%s, 玩家guid：%s 回档的时间:%s " % (self.server_name, self.param1, self.param2))
		playerguid, backtimestr = self.param1, self.param2
		port = self.getportnu(self.serverinfo["path"] + os.sep + "log" + os.sep + "centd.port")
		if port == 0:
			self.perror("%s 执行回档action时centd.port没找到!"% self.server_name)
			self.post(1)
			return

		cmd = CommandMgr("127.0.0.1", port)
		self.pinfo("发送玩家是否可以回档请求")
		cmdresult = cmd.send_huidangstart(",".join([self.server_name, playerguid]))
		if cmdresult != "succeed":
			self.perror("回档响应失败:%s" % cmdresult)
			self.post(1)
			return
		self.pdebug("开始回档处理")
		#2.处理玩家回档
		handle_result = self.handle_player_huidang(self.serverinfo["path"], playerguid, backtimestr)
		if handle_result == False:
			self.pinfo("玩家%s回档%s失败"%(playerguid, backtimestr))
			return
		else:
			self.pinfo("玩家%s回档%s成功" % (playerguid, backtimestr))
			self.pdebug("通知游戏服执行回档操作")
			cmdresult = cmd.send_huidangend(",".join([playerguid, backtimestr]))  #发送回档成功消息
			if cmdresult == "succeed":
				self.post()
			else:
				self.post(1)
			return









