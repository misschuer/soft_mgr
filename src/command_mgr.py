# -*- coding: utf8 -*-

import socket
from packet import *

class TcpConnection:
    def __init__(self,host,port):        
        self.host = host
        self.port = port
        self.__cur_packet = None
        self.__last_data = ''
        self.s = None

    def getTkKey(self, s):
        import hashlib
        import struct
        m = hashlib.md5(s)
        t = struct.unpack('iiii', m.digest())
        return [t[0],t[1],t[2],t[3]]
        
    def open(self):
        assert self.s == None
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((self.host, self.port))    
            self.s.settimeout(10)#设置超时
            return True
        except:
            print 'connect to centd %s:%u failed!'%(self.host, self.port)        
            #exit()
            return False
    
    def close(self):
        assert self.s
        self.s.close()
        self.s = None
    
    def send_packet(self,pkt):
        """发送数据包"""
        pkt.updateHead()
        self.s.send(pkt.bytes)
        
    def recv_packet(self):
        try:
            #如果上次解包没有剩余数据则再尝试收数据
            data = self.__last_data
            if len(data) == 0:
                assert self.s
                try:
                    data = data + self.s.recv(8192)
                except:
                    return None
            #解包了,好开心
            while len(data) > 0:
                if self.__cur_packet == None :
                    self.__cur_packet = packet()                

                #需要读多少数据
                need_size = 0
                if len(self.__cur_packet.bytes) < 2:
                    need_size = 2 - len(self.__cur_packet.bytes)                
                else:
                    need_size = self.__cur_packet.getLength() - len(self.__cur_packet.bytes)
                data = self.__cur_packet.parsefrom(data, need_size)

                #解包完成,返回单包
                if self.__cur_packet.is_ok():                      
                    self.__last_data = data
                    pkt = self.__cur_packet                    
                    self.__cur_packet = None
                    pkt.reset()
                    return pkt
                elif need_size > len(data):
                    data = data + self.s.recv(need_size - len(data))
               
        except:
            raise        

    def once_packet(self,host,port,pkt):
        """静态方法只发送单包后关闭连接"""
        conn = AdminConnection(host,port)
        conn.send_packet(pkt)
        conn.s.close()
    
class AdminConnection(TcpConnection):
    def __init__(self,host,port):    
        TcpConnection.__init__(self,host,port)
        
    def open(self):
        if TcpConnection.open(self):
            #会先收到一个pack_reg_server
            return self.recv_packet() != None            
            
        return False
class CommandMgr(AdminConnection):


    def __init__(self, host, port):
        AdminConnection.__init__(self, host, port)

    def __str__(self):
        return "host:"+ str(self.host) + "\nport:" + str(self.port)

    def create_packet2(self):
        pkt = packet(12)
        pkt.write_uint32(0)
        pkt.write_uint32(0)
        return pkt

    def send_command(self, cmd):
        #print "start conn to centd : %u"%self.port
        if not self.open():
            #print '端口连接失败'
            return None
        #print "生成指令包"
        pkt = self.create_packet2()
        pkt.write_str(cmd)
        #print "发送指令包"
        self.send_packet(pkt)
        #print "接收返回包"
        pkt = self.recv_packet()
        #print "关闭连接\n"
        self.close()
        if pkt is None:
            print "timeout\n"
            return 'timeout'
        else:
            return pkt.read_str()

    def reload_script(self):
        result = self.send_command("reload_script")
        return result

    def reload_template(self):
        result = self.send_command("reload_template")
        return result

    def send_to_game_svr(self, data_str):
        result = self.send_command("restore_system,"+data_str)
        return result

    def send_to_game_svr_savedb(self):
        result = self.send_command("save_to_db")
        return result

    def get_cmd_result(self, cmdnb):
        result = self.send_command("get_cmd_result,"+str(cmdnb))
        return result

    def restart_server(self, server_num):
        print "指令为：","restart_server," +str(server_num)
        result = self.send_command("restart_server," +str(server_num))
        #print result
        return result

    def stop_centd(self):
        print "关闭中心服务器"
        result = self.send_command("stop_centd")
        return result

    def get_status(self):
        result = self.send_command("hello_world")
        return result

    def send_huidangstart(self, val):
        #val:server_name,playerguid,用逗号连接服务器名字和玩家guid
		#result: success 则成功
        result = self.send_command("iscanhuidang,"+val)
        return result

    def send_huidangend(self, val):
        #val:playerguid,玩家guid
        result = self.send_command("dohuidang,"+val)
        return result

    def send_test_timeout(self):
        result = self.send_command("abcdefg")
        return result
