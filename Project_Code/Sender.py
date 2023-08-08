import socket
from tkinter import *
import sys
import os
import logging
from math import floor
from collections import deque
from threading import *
from common import *
from time import sleep,time 
import socket
import pickle
from random import randint

logging.basicConfig(level=logging.DEBUG,
  format='%(asctime)s.%(msecs)-03d : %(message)s',
  datefmt='%H:%M:%S')

message,msglen,next_msg_char='',0,0
pbuffer=[None]*SRP_WINDOW_SIZE
timers=[None]*SRP_WINDOW_SIZE
S_n,S_f,outstanding_frames=0,0,0
sock,client=None,None
client_sync_lock=Lock()

def callback_timeout(index):
 with client_sync_lock:
  if pbuffer[index] is not None:
    logging.info('[TIMEOUT] : Resending %s'%pbuffer[index])
    str2 = "[TIMEOUT] : Resending " + str(pbuffer[index])+'\n'
    text.insert(END,str2)
    send_packet(client,pbuffer[index])
    start_timer(index)
 
def start_timer(ind):
 timers[ind]=Timer(3000,callback_timeout,args=(ind, ))
 timers[ind].start()
 
def stop_timer(ind):
 if timers[ind] is None:
    pass
 if timers[ind].is_alive():
    timers[ind].cancel()
    timers[ind]=None
    return

def is_valid_ackno(ack):
 if outstanding_frames<=0 :
    return False
 seq=(S_f)%(MAX_SEQ_NO+1)
 while 1:
  if ack==seq : return True
  if seq==S_n :break
  seq=(seq+1)%(MAX_SEQ_NO+1)
 return False

def acknowledge_frames(ackno):
 global S_f,outstanding_frames
 if is_valid_ackno(ackno):
    if S_f!=ackno:
       ind=ackno%SRP_WINDOW_SIZE
       pbuffer[ind]=None
       stop_timer(ind)
       outstanding_frames-=1
       return ackno

 if S_f==ackno:
    ind=ackno%SRP_WINDOW_SIZE
    pbuffer[ind]=None
    stop_timer(ind)
    S_f=(S_f+1)%(MAX_SEQ_NO+1)
    outstanding_frames-=1
    if S_n==S_f:
       return
    t=S_f
    while 1:
     if t==S_n:
       if outstanding_frames==0:
          S_f=(S_f+1) % (MAX_SEQ_NO+1)
       break
     t=(t+1)%(MAX_SEQ_NO+1)
     if t==0:
       if pbuffer[7 % SRP_WINDOW_SIZE] is None:
          S_f=t
          continue
       else:
          break
     elif pbuffer[(t-1) % SRP_WINDOW_SIZE] is None:
       S_f=t
       continue
     else:
       break
    return ackno
 return -1

def handle_recvd_pkt(pkt_recvd):
 global outstanding_frames , S_f
 if pkt_recvd is None: return
 
 if pkt_recvd.is_corrupt():
  ind=pkt_recvd.seq_no%SRP_WINDOW_SIZE
  logging.info('[CHKSUMERR] :%s',pkt_recvd)
  window.update()
  str3 = "[CHKSUMERR] : " + str(pkt_recvd)+'\n'
  text.insert(END,str3)
  window.update()
  stop_timer(ind)
  send_packet(client,pbuffer[ind])
  start_timer(ind)
  return

 elif pkt_recvd.ptype==Packet.TYPE_NACK :
  logging.info('[RECV] : Received at handle %s.',pkt_recvd)
  window.update()
  str4 = "[RECV] : Packet Recieved" + str(pkt_recvd)+'\n'
  window.update()
  text.insert(END,str4)
  ind=pkt_recvd.seq_no%SRP_WINDOW_SIZE
 
  if pbuffer[ind] and pbuffer[ind].seq_no==pkt_recvd.seq_no:
   logging.info('[NACK_SEND] :%s. ',pbuffer[ind])
   str4 = "[NACK_SEND] : " + str(pbuffer[ind])+'\n'
   text.insert(END,str4)
   window.update()
   stop_timer(ind)
   send_packet(client,pbuffer[ind])
   start_timer(ind)
   return 
 
 elif pkt_recvd.ptype==Packet.TYPE_ACK:
  logging.info('[RECV] : Received at handle %s.',pkt_recvd)
  str5 = "[RECV] : Recieved Packet " + str(pkt_recvd)+'\n'
  text.insert(END,str5)
  window.update()
  ind=(pkt_recvd.seq_no)%SRP_WINDOW_SIZE
  ackno=pkt_recvd.seq_no
  frames=acknowledge_frames(ackno)
 
 else:
  print("Unknown Packet type")

def main():
  global outstanding_frames,S_n,next_msg_char
  while 1:
   try:
    if outstanding_frames<SRP_WINDOW_SIZE and next_msg_char < msglen:
     if (S_n>=S_f and S_n-S_f<4)or (S_n<=S_f and S_f-S_n>4 and S_f-S_n<=7):
       seq_no=S_n
       data=message[next_msg_char]
       ptype=Packet.TYPE_DATA
       pkt = Packet(seq_no,data,ptype)
       next_msg_char+=1
       ind=S_n%SRP_WINDOW_SIZE
       pbuffer[ind]=pkt
       logging.info('[SEND] :%s',pkt)
       window.update()
       str1 = "[SEND] : Sending " + str(pkt)+'\n'
       window.update()
       text.insert(END,str1)
       #ACQUIRE LOCK BEFORE WRITING TO CLIENT SOCKET.
       with client_sync_lock:
         print("Sending Packet with data as : ",data)
         send_packet(client,pkt)
       #LOCK IS BEING RELEASED DURING _ exit _ PHASE
       start_timer(ind)
       S_n=(S_n+1)%(MAX_SEQ_NO+1)
       outstanding_frames+=1
    #Wait a second
    sleep(1)
    #Check for an incoming Packet
    if outstanding_frames == 0 and next_msg_char >=msglen:
     logging.info("Transfer Complete ")
     text.insert(END, "\nTransfer Complete")
     client.close()
     sock.close()
     print("closed socket and client")
     window.update()
     text.insert(END, "\nConnection closed")
     break
    pkt_recvd = recv_packet_nblock(client)
    handle_recvd_pkt(pkt_recvd)
   except Exception as e:
    print(e, type(e))
    break

def submit():
 global message,msglen,client
 message = var.get()
 print(message)
 msglen=len(message)
 print("Started From Server")
 text.insert(END, "Started From Server \n")
 sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 port=8000
 ip=socket.gethostname()
 sock.bind(('',port))
 sock.listen(5)
 client,_addr=sock.accept()
 window.update()
 main()
 print("Connection is closing ")
 window.update()
 print("System Exit ")
 text.insert(END, "\nConnection is closing ")
 sock.close()
 client.close()
 
if __name__=='__main__':
 
 window = Tk()
 window.wm_title("Sender Window")
 window['bg']='grey'
 Label(window, text= "Type a word: ").grid(row = 0, column = 0)
 var = StringVar()
 Entry(window, textvariable = var, width= 50, borderwidth = 5). grid(row = 0, column = 1) 
 text = Text(window)
 text.grid(row = 2, column = 0)
 photo = PhotoImage(file = r"D:\cnimage\submit.png")
 photoimage = photo.subsample(5,5)
 button = Button(window,text="Submit",image = photoimage,command=submit)
 button.grid(row = 1, column = 0)
 window.mainloop()



