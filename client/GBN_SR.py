"""
DBN_SR协议类定义
以及相关方法
"""

class GBN_SR(object):
    def __init__(self, seqnum = 0, acknum = 0, win_size = 4, 
                 gbn = 1, sr = 0, ack = 0, fin = 0, 
                 len = 0, to = 1, data = b'',
                 max_size = 512, files_dir = r' '
                 ):
        self.seqnum = seqnum
        self.acknum = acknum
        self.win_size = win_size
        self.gbn = gbn
        self.sr = sr
        self.ack = ack
        self.fin = fin
        self.len = len
        self.to = to
        self.data = data
        self.max_size = max_size
        self.files_dir = files_dir

    def to_packet(self):
        self.len = len(self.data)
        return (str(self.seqnum).zfill(8) + str(self.acknum).zfill(8) + str(self.win_size).zfill(3)
                 + str(self.gbn) + str(self.sr) + str(self.ack) + str(self.fin)
                 + str(self.len).zfill(4) + str(self.to).zfill(3)).encode() + self.data
    
    def set_seqnum(self, seqnum):
        self.seqnum = seqnum

    def set_protocol(self, choice):
        if choice == 'GBN':
            self.gbn = 1
            self.sr = 0
        elif choice == 'SR':
            self.gbn = 0
            self.sr = 1

    def set_win(self, win):
        self.win_size = win
        
    def set_to(self, to):
        self.to = to

def File_to_Packets(temp:GBN_SR, filename:str):
    """
    将要传输的文件封装为数据包

    Parameters
    ----------
    temp : 协议模板
    filename : 文件名    
    """
    packets = []

    with open('%s/%s' % (temp.files_dir, filename), 'rb') as f:
        while(True):
            data = f.read(temp.max_size)
            if not data:
                break
            packets.append(GBN_SR(data = data))

    packets.append(GBN_SR(fin = 1))
    return packets

def FixedLenStr_to_Int(str):
    num = 0
    for i in range(len(str)):
        num += int(str[i]) * 10**(len(str) - i -1)
    return num

def Packet_to_Object(packet):
    obj = GBN_SR()
    num = packet[0: 8].decode()
    obj.seqnum = FixedLenStr_to_Int(num)
    num = packet[8: 16].decode()
    obj.acknum = FixedLenStr_to_Int(num)
    num = packet[16: 19].decode()
    obj.win_size = FixedLenStr_to_Int(num)
    num = packet[19: 20].decode()
    obj.gbn = FixedLenStr_to_Int(num)
    num = packet[20: 21].decode()
    obj.sr = FixedLenStr_to_Int(num)
    num = packet[21: 22].decode()
    obj.ack = FixedLenStr_to_Int(num)
    num = packet[22: 23].decode()
    obj.fin = FixedLenStr_to_Int(num)
    num = packet[23: 27].decode()
    obj.len = FixedLenStr_to_Int(num)
    num = packet[27:30].decode()
    obj.to = FixedLenStr_to_Int(num)
    obj.data = packet[30: len(packet)]
    return obj