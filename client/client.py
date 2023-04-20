import socket
import time
import os
import numpy as np
from GBN_SR import *

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(('', 8000))
server_address = ('localhost', 8888)
# 协议配置
GBN_or_SR = 'SR'
n = 4
to = 1
temp = GBN_SR(win_size=n, max_size=512, files_dir=r'D:\code\socket\client')
server_files = ['server_30K.txt', 'server_7M.txt', 'server_700K.png', 'server_200K.pdf', 'server_8M.mp4']
client_files = ['client_100K.txt', 'client_40K.jpg', 'client_12M.pdf']
expectedseqnum = 0
now_seqnum_send = 0
now_seqnum_recv = 0
drop_flag = 0
drop_ratio = 0.1

def drop_packet_by_index(seqnum):
    """
    丢失指定序号的包
    """
    global drop_flag
    if seqnum == 10 and drop_flag == 0:
        seqnum -= 1
        drop_flag = 1
        return True, seqnum
    else:
        return False, seqnum

def drop_packet_by_ratio(seqnum):
    """
    按指定丢包率丢包
    """
    global expectedseqnum
    global drop_ratio
    if np.random.random() <= drop_ratio:
        seqnum = expectedseqnum - 1
        return True, seqnum
    else:
        return False, seqnum

def download_file():
    """
    客户端从服务器下载文件
    """
    global client_socket, now_seqnum_send, now_seqnum_recv, expectedseqnum, drop_flag, temp

    print('<服务器文件列表>')
    for i in range(len(server_files)):
        print(i + 1, end='. ')
        print(server_files[i])
    send_data = input('输入要下载文件的序号：').strip()
    # 更新客户端文件列表并创建要下载的文件
    filename = server_files[int(send_data) - 1]
    client_files.append(filename)
    Recieve_File = open(filename,'wb', buffering = 0)
    if GBN_or_SR == 'GBN':
        client_socket.sendto(GBN_SR(seqnum=now_seqnum_send, gbn=1, sr=0, data=filename.encode()).to_packet(), server_address)
    elif GBN_or_SR == 'SR':
        client_socket.sendto(GBN_SR(seqnum=now_seqnum_send, gbn=0, sr=1, data=filename.encode()).to_packet(), server_address)

    now_seqnum_send += 1
    # 初始化
    expectedseqnum = 0
    drop_flag = 0
    fin_num = -1
    flag = 0
    print('文件开始下载...')
    print('---------------------------------------------------')
    sr_buffer = []
    sr_buffer_index = []
    start = time.time()
    while True:
        packet, addr = client_socket.recvfrom(1024)
        packet_obj = Packet_to_Object(packet)
        now_seqnum_recv = packet_obj.seqnum
        # TODO
        # 丢包测试
        # drop, now_seqnum_recv = drop_packet_by_index(now_seqnum_recv)
        drop, now_seqnum_recv = drop_packet_by_ratio(now_seqnum_recv)
        if drop:
            continue
        # TODO
        # 判断是否按序
        if GBN_or_SR == 'GBN':
            if now_seqnum_recv == expectedseqnum:
                # 按序，返回ACK，写入文件
                print('Received expected packet ', now_seqnum_recv, ' ^_^')
                client_socket.sendto(GBN_SR(seqnum=now_seqnum_send, acknum=now_seqnum_recv, gbn=1, sr=0, ack=1).to_packet(), server_address)
                print('Sending ACK:', now_seqnum_recv)
                # 发送完成标志
                if packet_obj.fin == 1:
                    break
                else:
                    Recieve_File.write(packet_obj.data)
                expectedseqnum += 1
            else:
                # 不按序，丢弃
                print('Received wrong packet ', now_seqnum_recv, ', drop it!')
        elif GBN_or_SR == 'SR':
            if now_seqnum_recv >= expectedseqnum:
                # 按序，返回ACK，写入文件
                print('Received expected packet ', now_seqnum_recv, ' ^_^')
                client_socket.sendto(GBN_SR(seqnum=now_seqnum_send, acknum=now_seqnum_recv, gbn=0, sr=1, ack=1).to_packet(), server_address)
                print('Sending ACK:', now_seqnum_recv)
                if now_seqnum_recv == expectedseqnum:
                    # 发送完成标志
                    if packet_obj.fin == 1:
                            break
                    else:
                        Recieve_File.write(packet_obj.data)
                        expectedseqnum += 1
                        while expectedseqnum in sr_buffer_index:
                            Recieve_File.write(sr_buffer[sr_buffer_index.index(expectedseqnum)])
                            if expectedseqnum == fin_num:
                                flag = 1
                                break
                            expectedseqnum += 1
                        if flag == 1:
                            break
                elif now_seqnum_recv > expectedseqnum:
                    sr_buffer_index.append(now_seqnum_recv)
                    sr_buffer.append(packet_obj.data)
                    if packet_obj.fin == 1:
                        fin_num = now_seqnum_recv
    end = time.time()
    print('---------------------------------------------------')
    print('文件 %s 下载完毕！' %filename)
    time_cost = (end - start)*1000
    print('传输耗时 %.4f ms' %(time_cost), end=', ')
    file_size = os.path.getsize(os.path.abspath(filename))
    print('传输平均速率 %.4f B/s\n' %(file_size / time_cost * 1000))

def upload_file():
    """
    客户端向服务器上传文件
    """
    global client_socket, now_seqnum_send, now_seqnum_recv, expectedseqnum, drop_flag, temp

    print('<本机文件列表>')
    for i in range(len(client_files)):
        print(i + 1, end='. ')
        print(client_files[i])
    up = input('输入要上传文件的序号：').strip()
    # 更新对服务器的记录
    filename = client_files[int(up) - 1]
    server_files.append(filename)
    if GBN_or_SR == 'GBN':
        client_socket.sendto(GBN_SR(seqnum=now_seqnum_send, gbn=1, sr=0, data=filename.encode()).to_packet(), server_address)
    elif GBN_or_SR == 'SR':
        client_socket.sendto(GBN_SR(seqnum=now_seqnum_send, gbn=0, sr=1, data=filename.encode()).to_packet(), server_address)
    print('文件开始下载...')
    print('---------------------------------------------------')
    start = time.time()
    packets = File_to_Packets(temp, filename)
    # 初始化
    base = 0
    now_seqnum = 0
    ack = -1
    # 发送数据包
    while True:
        # 窗口有空才发送
        while now_seqnum < base + temp.win_size and now_seqnum < len(packets):
            packets[now_seqnum].set_seqnum(now_seqnum)
            client_socket.sendto(packets[now_seqnum].to_packet(), server_address)
            print('Sending packet:', now_seqnum)
            now_seqnum += 1
        # 接收ACK
        client_socket.settimeout(to)
        try:
            ack, addr = client_socket.recvfrom(1024)
            ack_obj = Packet_to_Object(ack)
            ack = int(ack_obj.acknum)
            print('Received ACK:', ack)
            base = ack + 1
        except socket.timeout:
            print('Timeout')
            now_seqnum = base
        if ack == len(packets) - 1:
            break
    end = time.time()
    print('---------------------------------------------------')
    print('文件 %s 上传完毕！' %filename)
    time_cost = (end - start)*1000
    print('传输耗时 %.4f ms' %(time_cost), end=', ')
    file_size = os.path.getsize(os.path.abspath(filename))
    print('传输平均速率 %.4f B/s\n' %(file_size / time_cost * 1000))
    
if __name__ == '__main__':
    while True:
        print('<传输协议配置>')
        GBN_or_SR = input('请输入选择的协议的序号(GBN 或 SR): ').strip()
        n = int(input('请输入窗口长度N: '))
        to = int(input('请输入超时时间TO(ms): '))
        temp.set_protocol(GBN_or_SR)
        temp.set_win(n)
        temp.set_to(to)
        print('\n<传输类型>')
        print('1. 下载文件')
        print('2. 上传文件')
        choice = input('输入对应的序号：').strip()
        print('---------------------------------------------------')
        choice = int(choice)
        if choice == 1:
            download_file()
        elif choice == 2:
            upload_file()