import socket
from GBN_SR import *

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('localhost', 8888))
# 协议配置
GBN_or_SR = 'SR'
n = 4
to = 1
temp = GBN_SR(win_size=n, max_size=512, files_dir=r'/root/socket/server')
server_files = ['server_30K.txt', 'server_7M.txt', 'server_700K.png', 'server_200K.pdf', 'server_8M.mp4']
expectedseqnum = 0
now_seqnum_send = 0
now_seqnum_recv = 0
pkt_loss = 0
pkt_resend = 0

def send_file(recv_name, addr):
    """
    服务器向客户端发送文件
    """
    global server_socket, temp, pkt_loss, pkt_resend, to, GBN_or_SR
    
    print('开始向客户端发送文件...')
    print('---------------------------------------------------')
    packets = File_to_Packets(temp, recv_name)
    # 初始化
    base = 0
    now_seqnum = 0
    pkt_loss = 0
    pkt_resend = 0
    # 发送数据包
    ack = -1
    ack_list = []
    while True:
        if GBN_or_SR == 'GBN':
            # 窗口有空才发送
            while now_seqnum < base + temp.win_size and now_seqnum < len(packets):
                packets[now_seqnum].set_seqnum(now_seqnum)
                server_socket.sendto(packets[now_seqnum].to_packet(), addr)
                print('Sending packet:', now_seqnum)
                now_seqnum += 1
            # 接收ACK
            server_socket.settimeout(to)
            try:
                ack, addr = server_socket.recvfrom(1024)
                ack_obj = Packet_to_Object(ack)
                ack = int(ack_obj.acknum)
                print('Received ACK:', ack)
                base = ack + 1
            except socket.timeout:
                print('Timeout')
                pkt_loss += 1
                pkt_resend += now_seqnum - base
                now_seqnum = base
        elif GBN_or_SR == 'SR':
            # 窗口有空才发送
            while now_seqnum < base + temp.win_size and now_seqnum < len(packets):
                if now_seqnum not in ack_list: 
                    packets[now_seqnum].set_seqnum(now_seqnum)
                    server_socket.sendto(packets[now_seqnum].to_packet(), addr)
                    print('Sending packet:', now_seqnum)
                now_seqnum += 1
            # 接收ACK
            server_socket.settimeout(to)
            try:
                ack, addr = server_socket.recvfrom(1024)
                ack_obj = Packet_to_Object(ack)
                ack = int(ack_obj.acknum)
                ack_list.append(ack)
                print('Received ACK:', ack)
                if base == ack:
                    base = ack + 1
                    while base in ack_list:
                        base += 1
            except socket.timeout:
                print('Timeout')
                pkt_loss += 1
                pkt_resend += 1
                now_seqnum = base

        # 等待客户端下次请求
        if base == len(packets):
            server_socket.settimeout(500)
            break
    print('---------------------------------------------------')
    print('成功向客户端发送文件：%s\n' %recv_name)
    print('丢包率: ', (pkt_loss / len(packets)), end=', ')
    print('重传率: ', (pkt_resend / len(packets)))

def recieve_file(recv_name, addr):
    """
    服务器接收客户端上传的文件
    """
    global server_socket, temp, expectedseqnum, now_seqnum_send, now_seqnum_recv, GBN_or_SR

    print('开始从客户端接收文件...')
    print('---------------------------------------------------')
    server_socket.sendto(GBN_SR(seqnum=now_seqnum_send, data=recv_name.encode()).to_packet(), addr)
    server_files.append(recv_name)
    Recieve_File = open(recv_name,'wb', buffering = 0) # TODO
    now_seqnum_send += 1
    # 初始化
    expectedseqnum = 0
    while True:
        packet, addr = server_socket.recvfrom(1024)
        packet_obj = Packet_to_Object(packet)
        now_seqnum_recv = packet_obj.seqnum
        # 判定是否按序
        if now_seqnum_recv == expectedseqnum:
            # 按序，返回ACK，写入文件
            print('Received expected packet ', now_seqnum_recv, ' from client ', addr)
            server_socket.sendto(GBN_SR(seqnum=now_seqnum_send, acknum=now_seqnum_recv, ack=1).to_packet(), addr)
            print('Sending ACK ', now_seqnum_recv, 'to client ', addr)
            # 发送完成标志
            if packet_obj.fin == 1:
                    break
            else:
                Recieve_File.write(packet_obj.data)
            expectedseqnum += 1
        else:
            # 不按序，丢弃
            print('Received wrong packet ', now_seqnum_recv, ', drop it!')
    print('---------------------------------------------------')
    print('从客户端接收文件 %s 完毕！' %recv_name)

if __name__ == '__main__':
    while True:
        # 分析客户端请求
        print('等待客户端请求...')  
        req, addr = server_socket.recvfrom(1024)
        req_obj = Packet_to_Object(req)
        if req_obj.gbn == 1:
            GBN_or_SR = 'GBN'
        elif req_obj.sr == 1:
            GBN_or_SR = 'SR'
        n = req_obj.win_size
        to = req_obj.to
        recv_name = req_obj.data.decode()
        if recv_name in server_files:
            send_file(recv_name, addr)
        else:
            recieve_file(recv_name, addr)