#!/usr/bin/python
# -*- coding: utf8 -*-

import asyncore, socket

from packet import packet


class Connection(asyncore.dispatcher_with_send):   
    def __init__(self, s, m):        
        asyncore.dispatcher_with_send.__init__(self, s, m)
        self.func_map = {}  # 包处理函数路由
        self.__cur_packet = None        
        
    def handle_read(self):
        try:
            data = self.recv(8192)   
            # 解包了,好开心
            while len(data) > 0:
                if(self.__cur_packet == None):
                    self.__cur_packet = packet()                
    
                # 需要读多少数据
                need_size = 0
                if len(self.__cur_packet.bytes) < 2:
                    need_size = 2 - len(self.__cur_packet.bytes)                
                else:
                    need_size = self.__cur_packet.getLength() - len(self.__cur_packet.bytes)
                data = self.__cur_packet.parsefrom(data, need_size)
                
                # 解包完成
                if self.__cur_packet.is_ok():
                    self.handle_packet(self.__cur_packet)              
                    self.__cur_packet = None
        except:
            raise   
    
    def send_packet(self, packet):
        packet.updateHead()
        self.send(packet.bytes)

    def handle_packet(self, packet):
        packet.reset()
        assert packet.getLength() == len(packet.bytes)
        func = self.func_map.get(packet.getOptcode())        
        if func:
            func(self, packet)
        else:
            self.default_packet_func(packet)
    
    def default_packet_func(self, packet):        
        print "Connection:default_packet_func unsurport optcode %u" % packet.getOptcode()

    def handle_update(self, diff):     
        pass

class App(asyncore.dispatcher):
    """服务器程序运维管理接口"""
    def __init__(self, create_func):
        asyncore.dispatcher.__init__(self, None, {})        
        self.running = False
        self.create_func = create_func    
        
    def start_listen(self, host, port):
        # 开始监听，设置为非阻塞并且绑定后
        # 当新连接到来的时候会触发
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        
    def start_connect(self, host, port, create_func):
        """阻塞式连接到服务器连接成功后加入socket列表"""        
        conn = create_func(None, self._map)  # 工厂方法            
        conn.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = conn.socket                            
        sock.setblocking(1)
        conn.connect((host, port))  # 阻塞式的连接到服务器        
        sock.setblocking(0)        
        return True
        
    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            # 构建的时候自然会被插入map
            #self.create_func(sock, self._map)
    
    def handle_update(self,diff):
        pass

    def update(self, diff, sleep_ms):
        """对每个连接进行心跳"""
        for v in self._map.values():
            v.handle_update(diff)
        # 网络心跳
        if len(self._map) > 0:
            asyncore.loop(sleep_ms, False, self._map, 1)
    def try_stop(self):
        self.running = False

def loop(self,tick_long = 0.05):
    try:
        self.running = True
        import timeit
        cur, prev, sleep_ms = 0, timeit.default_timer(), 0
        while self.running:
            cur = timeit.default_timer()
            diff = cur - prev
            prev = cur
            # 以20帧的精度进行心跳
            if diff <= tick_long + sleep_ms:
                sleep_ms = tick_long + sleep_ms - diff
            else:
                sleep_ms = 0
            self.update(int(diff * 1000), sleep_ms)
    except KeyboardInterrupt:
        print '程序被强制中止'
        self.running = False

#-------------------------------------------
# 单元测试在这里
#-------------------------------------------

def sock_app_test():
    def on_server_pingpong(self, pkt):
        tick = pkt.read_int32()
        tick = tick + 1
        send_pkt = packet(99)       
        send_pkt.write_int32(tick)   
        # 计数+1后返回
        self.send_packet(send_pkt)     
        
    def create_server_sessoin(s, m):
        server_conn = Connection(s, m)       
        server_conn.func_map[99] = on_server_pingpong
        return server_conn
        
        
    # 服务器
    server = App(create_server_sessoin)
    server.start_listen('127.0.0.1', 20609)
    
    #############
    # 利用多线程先把服务器跑起来
    import threading
    class ServerThread(threading.Thread):
        def run(self):
            loop(server)
    server_thread = ServerThread()
    server_thread.start() 

    # 客户端
    client_app = App(None)    
    
    def on_client_pingpong(self, pkt):
        tick = pkt.read_int32()
        assert tick == 2
        server.try_stop()
        client_app.try_stop()
        print '测试通过'
        
    def create_client_session(s, m):
        class ClientConnection(Connection):            
            def handle_connect(self):
                asyncore.dispatcher_with_send(self)
                # 客户端先主动发一个包
                pkt = packet(99)
                pkt.write_int32(1)
                self.send_packet(pkt)
                
        client_session = ClientConnection(s, m)       
        client_session.func_map[99] = on_client_pingpong       
        
        return client_session
    client_app.start_connect('127.0.0.1', 20609, create_client_session)
    loop(client_app)
    server_thread.join()
    
if __name__ == '__main__':
    sock_app_test()
