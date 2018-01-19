#!/usr/bin/python
# -*- coding: utf8-*-
import os, commands, time, glob

def func_excute_count(pid, times=100000, desfile="func_count.txt"):
	'''
	该函数负责在规定测次数下统计对应进程下每个函数的执行次数，然后将最终结果写入给定的文件.
	pid: 进程号
	times:执行次数
	desfile:目标文件,默认写在当前执行的路径下
	'''

	haspid = commands.getoutput(" ".join(["ps", "aux | grep ", str(pid), " | grep -v grep"]))
	if not haspid:
		print "进程没有运行"
		return
	pstack_cmd = ["pstack", str(pid)]
	func_dict = {}
	i = 0
	sublist = lambda res, str, offset=0: [result[result.find(str)+offset:] for result in res]
	while i < times:
		i += 1
		status, resultstr = commands.getstatusoutput(" ".join(pstack_cmd))
		resultstr = resultstr[resultstr.find("Thread 1 ("):]
		resultlist =sublist(resultstr.split("\n")[1:], "in", 3)
		for result in resultlist:
			index = result.find('()')
			other = result[index+2:]
			if other:
				continue
			if not func_dict.has_key(result):
				func_dict[result] = 1
			else:
				func_dict[result] += 1
	#写入对应文件
	with open(desfile, "w") as file:
		print func_dict
		for key in func_dict.keys():
			file.write(key + "执行次数--->"+str(func_dict[key]) + "\n")

#计算函数运行时间
def func_excute_cost_time(fun, args=()):
	'''
	该函数负责统计给定函数运行的时间
	arg:arg是一个tuple,tuple中的元素依次为给定函数的常规参数
	'''
	start = time.time()
	fun(*args)
	end = time.time()
	print "cost time is(seconds):", end - start

#待增加一个参数，确定字符串是用单引号还是双引号
def func_file_to_dict(filedir, globstr, desfile="des.txt"):
	'''
	将目录下指定格式文件中“=”号连接的文本转换成字典，然后写入其他文件
	'''
	filedir = os.path.normpath(filedir)
	filter_file_str = os.path.join(filedir, "*."+globstr)
	filelist = glob.glob(filter_file_str)
	des_dict = {}
	if not filelist:
		print("目录下无指定格式的文件")
		return
	for file in filelist:
		file_key = os.path.split(file)[1]
		if not des_dict.has_key(file_key):
			des_dict[file_key] = {}
		with open(file, "r") as f:
			for line in f.readlines():
				if line.find("=") == -1:
					continue
				index = line.find("=")
				key = line[:index].strip()
				des_dict[file_key][key] = line[index+1:].strip()
	#格式化输出到文件
	i = 1
	with open(desfile, "w") as wf:
		wf.write('{')
		for fkey in des_dict:
			wf.write("'" + fkey +"':\n    {")
			for lkey in des_dict[fkey]:
				wf.write("'"+lkey+"' : "+"'"+des_dict[fkey][lkey]+"',")
				if i % 3 == 0 :
					wf.write("\n    ")
				i += 1
			wf.write("    },\n")
		wf.write("}")


if __name__ == "__main__":
	func_excute_cost_time(func_excute_count,(22851,10000,"func_count.txt"))
