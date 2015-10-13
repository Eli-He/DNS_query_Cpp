﻿__author__ = 'rex686568'

name_server_list = ['202.117.0.20',
                    '202.117.0.21']


Timeout = 2

minTTL = 600

import dns.resolver
import dns.name
import dns.message
import dns.query
import dns.rdatatype
from dns import *
import Queue
import threading
import time

maxthreads = 3000
wrongCnt = 0
numofthreads = 0
alllogs = []

def query(domain, name_server):
    domain = dns.name.from_text(domain)
    if not domain.is_absolute():
        domain = domain.concatenate(dns.name.root)

    
    request = dns.message.make_query(qname = domain,
                                     rdtype = dns.rdatatype.A)
    request.flags &= ~dns.flags.RD

    response = dns.query.udp(q=request,
                             where=name_server,
                             timeout=Timeout)
    return response



def getAnswer(domain, q, name_server):
    global wrongCnt,numofthreads,alllogs,currenttimeinseconds
    
    try:
        response = query(domain, name_server)
        if len(response.answer) != 0:
            ttl = response.answer[0].ttl
            if ttl == 0:
                ttl = 1
            q.put(domain + ' ' + str(response.answer[0].ttl) + ' ' + str(currenttimeinseconds))
        else:
            q.put(domain + ' ' + str(0) + ' ' + str(currenttimeinseconds))

        # all logs

        log = '  ' + '\n'
        log+=domain + ' ' + str(currenttimeinseconds) + '\n'
        for i in response.answer:
            log+= str(i) + '\n'
        for i in response.authority:
            log+= str(i) + '\n'
        for i in response.additional:
            log+= str(i) + '\n'
        alllogs.append(log)

    except dns.exception.Timeout:
        wrongCnt += 1


f = open("maxTTL.txt")
domains = Queue.PriorityQueue()
currenttimeinseconds = time.time()

for line in f.readlines():
    urlandmaxTTL = str(line).strip().split()
    url = urlandmaxTTL[0]
    maxTTL = int(urlandmaxTTL[1])
    if maxTTL != 0:
        if maxTTL < minTTL:  #waive too short ones
            maxTTL = minTTL
        for name_server in name_server_list:
            domains.put((currenttimeinseconds,#+ maxTTL
                         [url,
                          maxTTL,
                          name_server]))
    

q = Queue.Queue()



pastwrongCnt=0


while True:
    
    currenttimeinseconds = time.time()

    stuff = domains.get()
    deltaSeconds = stuff[0] - currenttimeinseconds
    if  deltaSeconds > 0:
        domains.put(stuff)
        time.sleep(deltaSeconds)
    else:
        domain = stuff[1][0]
        maxTTL = stuff[1][1]
        DNS=stuff[1][2]
        refreshstuff = (maxTTL + currenttimeinseconds,
                      stuff[1])
        t = threading.Thread(target=getAnswer,
                             args=(domain,
                                   q,
                                   DNS))
        t.daemon = True
        t.start()
        domains.put(refreshstuff)



    numofthreads += 1

    if numofthreads > maxthreads:
            numofthreads = 0
        #    time.sleep(Timeout+1)
    
    f = open("remainTTL.csv", mode='a')
    while not q.empty():
        line = q.get()
        #print(line)
        f.write(line + '\n')
    f.close()

    f = open("log.txt", mode='a')
    while len(alllogs) != 0:
        f.write(alllogs.pop())    
    f.close()

    if pastwrongCnt!=wrongCnt:
        print 'errorCnt',str(wrongCnt)
        pastwrongCnt=wrongCnt


time.sleep(Timeout + 1)
