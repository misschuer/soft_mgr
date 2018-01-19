#!/usr/bin/python
# -*- coding: utf8-*-
import commands, sys, os, time

class StackSnapshoot(object):
	"""docstring for StackSnapshoot"""
	def __init__(self,text):
		super(StackSnapshoot, self).__init__()
		self.text = text



def func_stats_count(pid, times, interval,desfile="func_stats_info.txt"):
	'''
	该函数负责在规定测次数下统计对应进程下每个函数的执行次数，然后将最终结果写入给定的文件.
	pid: 进程号
	interval：执行的频率 -单位毫秒
	times:执行次数
	desfile:目标文件,默认写在当前执行的路径下
	'''
	haspid = commands.getoutput(" ".join(["ps", "aux | grep ", str(pid), " | grep -v grep"]))
	if not haspid:
		print "进程没有运行"
		return
	pstack_cmd = ["pstack", str(pid)]
	func_dict = {}

	#函数出现总次数
	total_times = 0
		
	i = 0
	sublist = lambda res, str, offset=0: [result[result.find(str)+offset:] for result in res]
	while i < times:

		i += 1
		#获取执行获取堆栈命令的结果 、堆栈的字符串
		status, resultstr = commands.getstatusoutput(" ".join(pstack_cmd))

		#第一次过滤，多线程的话，通过截取字符串子串过滤掉线程1以外的无用字符串信息
		find_index = resultstr.find("Thread 1 (")
		if(find_index != -1):
			resultstr = resultstr[find_index:]

		#用换行符切割整个字符串，同时去掉第一行无用信息，取出每一行前面的不用的字符串
		resultlist =sublist(resultstr.split("\n")[1:], "in", 3)

		#最后一次筛选，函数扩胡后面还有内容的说明内容无用，同时进行统计
		for result in resultlist:
			index = result.find('()')
			other = result[index+2:]
			if other:
				continue
			total_times += 1
			if not func_dict.has_key(result):
				func_dict[result] = 1
			else:
				func_dict[result] += 1
	
		#休眠一下，当定时器用
		time.sleep(float(interval)/1000.0)
	#根据出现次数降序排序
	func_dict_new = sorted(func_dict.iteritems(),key=lambda a:a[1],reverse = True)
	#计算百分比
	#写入对应文件
	with open(desfile, "w") as file:
		for key,cur_times in func_dict_new:
			file.write(''.join(['function:', key,' 次数',str(cur_times),',百分比-->',str(float(cur_times)/float(total_times)*100.0),'\n']))



if __name__ == "__main__":

	#output = commands.getoutput("ps -ef|grep ying")
#	output = """#0 0x00002ba1f8152650 in __nanosleep_nocancel () from /lib64/libc.so.6
#1 0x00002ba1f8152489 in sleep () from /lib64/libc.so.6
#2 0x00000000004007bb in ha_ha ()
#3 0x0000000000400a53 in main ()
#"""
#	lines = output.split('\n')
#	for l in lines:
#		word = l.split(' ')
#		print word
	#sublist = lambda res, str, offset=0: [result[result.find(str)+offset:] for result in res]
#	sys.exit()

	if len(sys.argv) < 4:
		print "格式错误 格式为>>python coll_pstack.py 进程号 截取堆栈次数 截取间隔"
		sys.exit()

	#获取执行次数 默认100000次
	try:
		times = int(sys.argv[2])
	except:
		times = 100
	#获取执行间隔毫秒数。默认200毫秒
	try: 
		interval = int(sys.argv[3])
	except:
		interval = 20
	#获取写入文件 默认写在当前执行文件目录的func_count.txt中
	try:
		desfile = sys.argv[4]
	except:
		desfile = sys.argv[1]+"func_count.txt"
	__time1 = time.time()
	print('开始截取统计堆栈，截取'+str(times)+'次,每次截取间隔'+str(interval)+'毫秒')
	func_stats_count(int(sys.argv[1]), times,interval, desfile)
	print('统计结束，请查看当前目录下的pid+func_count.txt')





















