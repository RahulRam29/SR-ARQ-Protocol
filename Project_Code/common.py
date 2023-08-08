import socket 
import pickle 
from random import randint 
SEQ_NO_BIT_WIDTH = 3 
 
MAX_SEQ_NO = (2 ** SEQ_NO_BIT_WIDTH) - 1 
SRP_WINDOW_SIZE=2 ** (SEQ_NO_BIT_WIDTH - 1) 
 
class Packet: 
    TYPE_DATA, TYPE_ACK, TYPE_NACK = range(3) 
   
    def __init__(self , seq_no,data='', ptype=TYPE_DATA):
        self.seq_no = seq_no       
        self.data = data         
        self.ptype = ptype 
        self.corrupt = 0 
 
    def is_corrupt(self):
        if not self.corrupt:
            self.corrupt = randint(1,10)
        return self.corrupt<3
     
    def __str__(self):
        if self.ptype == Packet.TYPE_DATA:
            return 'Packet(seq_no=%d, data=%s) ' % (self.seq_no, str(self.data))
        elif self.ptype == Packet.TYPE_NACK:
            return 'Packet(nack_no=%d)' % self.seq_no
        elif self.ptype == Packet.TYPE_ACK:
            return 'Packet(ack_no=%d)' % self.seq_no
 
def read_k_bytes(s, rem=0):
        ret=b''         
        while rem > 0: 
            d = s.recv(rem)             
            if len(d)<=0: 
                k=0 
                return k.to_bytes(4, byteorder='big') 
            ret += d             
            rem -= len(d) 
        return ret 
 
def send_packet(s, pack):
    if pack is None or (s is None or type(s) != socket.socket):
        return 
    pack_raw_bytes = pickle.dumps(pack)
    dsize = len(pack_raw_bytes)
    s.sendall(dsize.to_bytes(4, byteorder='big'))
    s.sendall(pack_raw_bytes)
    return True
 
def recv_packet(s, timeout=None):
    if s is None or type(s) != socket.socket: 
        raise TypeError('Socket Expected!')         
    if timeout is not None:             
        s.settimeout(timeout)         
    try: 
        pack_len = int.from_bytes(read_k_bytes(s,4), 'big')            
        if pack_len==0: 
            return 0             
        s.settimeout(None)             
        pack = pickle.loads(read_k_bytes(s, pack_len))         
    except socket.timeout: 
        pack = None
    finally: 
        s.settimeout(None) 
    return pack
 
def recv_packet_nblock(s):
        s.setblocking(False)
        try:
            size = int.from_bytes(read_k_bytes(s,4), 'big')
            s.setblocking(True)
            return pickle.loads(read_k_bytes(s, size))
        except BlockingIOError as be:
            return None
        finally:
            s.setblocking(True)
