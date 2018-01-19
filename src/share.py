#!/usr/bin/python
# -*- coding: utf8-*-
import os

RUN_STATIC_NONE = 0				#未执行
RUN_STATIC_SUCCESS = 1			#已执行成功
RUN_STATIC_HASDEL = 2			#已删除
RUN_STATIC_FAILED = 3			#失败
RUN_STATIC_RUNNING = 4			#正在执行

#文件生成配置
CONFIG_DICT = {'appd.conf':
    {'netgd_port' : '846','log_name' : 'appd','centd_host' : '127.0.0.1',
    'log_folder' : 'log/','load_pingbi' : 'Y','open_sleep_time' : '3000',
    'data_folder' : '"SERVER_ROOT/template/"','netgd_host' : '127.0.0.1','log_level' : '0',
    'script_folder' : '"SERVER_ROOT/scripts/"','centd_port' : '847','map_folder' : '"SERVER_ROOT/maps/"',
        },
'netgd.conf':
    {'internal_host' : '127.0.0.1','log_name' : 'netgd','log_path' : 'log/',
    'internal_port' : '7001','external_handles' : '8000','external_host' : '0.0.0.0',
    'internal_handles' : '5','log_level' : '3','external_port' : '443',
        },
'centd.conf':
    {'netgd_port' : '846','bin_folder' : '"SERVER_ROOT/bin/"','log_name' : 'centd',
    'centd_host' : '127.0.0.1','log_folder' : 'log/','process_method' : '"N"',
    'etc_folder' : '"SERVER_ROOT/etc/"','netgd_host' : '127.0.0.1',
    'log_level' : '0','script_folder' : '"SERVER_ROOT/scripts/"','centd_port' : '847',},
'logind.conf':
    {'netgd_port' : '846','platform_id' : '24',
    'server_id' : '"0"','log_folder' : 'log/','log_name' : 'logind',
    'centd_host' : '127.0.0.1','db_chars_log' : '"log/db_chars"','db_character' : '"127.0.0.1;27017;dev;asdf;cow_char"',
    'load_pingbi' : 'Y','data_folder' : '"SERVER_ROOT/template/"','login_queue_interval' : '3000',
    'db_chars_connection' : '1','login_key' : '"kKQDyPpWdJH46ulUf3MwxNZRjXoIzaGV"','netgd_host' : '127.0.0.1',
    'versions_requirements_internal' : '20','log_level' : '0',
    'script_folder' : '"SERVER_ROOT/scripts/"','centd_port' : '847','map_folder' : '"SERVER_ROOT/maps/"',
	'gm_open':'N','check_session_key_time':"Y",
        },
'policed.conf':
    {'netgd_port' : '846','msg_post_src' : '"http://interface.game2.cn/sms.php"','data_folder' : '"SERVER_ROOT/template/"',
    'centd_host' : '127.0.0.1','lock_ip_max' : '10','log_level' : '0',
    'log_folder' : 'game_log/','write_rsync' : '1',
    'chat_post_src' : '"http://14.17.113.196:9999/chat.php"','open_sleep_time' : '5000','check_oper' : '1',
    'netgd_host' : '127.0.0.1','log_name' : 'policed','do_post' : 'N',
    'script_folder' : '"SERVER_ROOT/scripts/"','centd_port' : '847','#post_src' : '"http://jiulongchao.api.cy2009.com/"',
    'key' :'"htZZKKq1GnBlFaoaXQli9p3A5Jde46Hj"'    },
'robotd.conf':
    {'netgd_port' : '2591','server_id' : '2500','log_name' : 'robot',
    'centd_host' : '127.0.0.1','min_quit_rand_time' : '500000','robot_action' : '"30|30"',
    'log_folder' : 'log/','platform_id' : '2','open_sleep_time' : '5000',
    'data_folder' : '"/home/linbc/workspace/12j/contrib/data/"','login_key' : '"84adc98ee63b26e2063a796ac982ad77"','netgd_host' : '127.0.0.1',
    'max_quit_rand_time' : '1000000','log_level' : '0','#robot_action' : '"3|27|2|27"',
    'max_robot_count' : '30','script_folder' : '"/home/linbc/workspace/12j/contrib/scripts/"','centd_port' : '847',
    'map_folder' : '"/home/linbc/workspace/12j/contrib/maps/"',  },
'scened.conf':
    {'netgd_port' : '846','log_name' : 'scened',
    'centd_host' : '127.0.0.1','log_folder' : '"log/"','load_creature_path' : 'Y',
    'load_pingbi' : 'Y','error_distance' : '2','data_folder' : '"SERVER_ROOT/template/"',
    'netgd_host' : '127.0.0.1','log_level' : '0','script_folder' : '"SERVER_ROOT/scripts/"',
    'centd_port' : '847','map_folder' : '"SERVER_ROOT/maps/"',   },
'datad.conf':
    {'netgd_host' : '127.0.0.1', 'netgd_port' : '7001','log_name' : 'datad',
    'centd_host' : '127.0.0.1', 'centd_port' : '10000', 'log_folder' : '"log/"',   
    'log_level' : '0','script_folder' : '"SERVER_ROOT/scripts/"','playerinfo_cache_local_hdd_path':'"SERVER_ROOT/var"'},
}



