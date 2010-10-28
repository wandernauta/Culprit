#!/usr/bin/python

import urllib
import sys
import readline
import getpass
import curses
import curses.wrapper
import time
import csv
import StringIO
import subprocess
import re

class Credentials:
    raddress = "192.168.0.1"
    username = "admin"
    password = ""
    override = ""

    def auth(self):
        self.raddress = raw_input('Router IP: ')
        self.username = raw_input('Username: ')
        self.password = getpass.getpass('Password: ')

    def geturl(self):
        if self.override != "":
            return self.override
        else:
            return '%s:%s@%s' % (self.username, self.password, self.raddress)

class Requester:
    cred = Credentials()

    def fetch(self):
        url = '%s/goform/updateIptAccount' % (self.cred.geturl())
        return urllib.urlopen('http://' + url).read()

class DHCPResolver:
    cred = Credentials()
    lookup = dict()

    def prepare(self):
        url = '%s/lan_dhcp_clients.asp' % (self.cred.geturl())
        data = urllib.urlopen('http://' + url).read()
        dataline = re.search(r'var dhcpList=new Array\((.*?)\)', data).group(1)
        records = dataline.split(',')
        srecords = dict(list(x.strip("'").split(';')[:2] for x in records))
        mydict = dict((v,k) for k,v in srecords.iteritems())
        self.lookup = mydict

    def resolve(self, ip):
        if self.lookup.has_key(ip):
            return self.lookup[ip]
        else:
            return ip

resolver = DHCPResolver()
requester = Requester()

def main():
    global resolver, requester
    c = Credentials()

    if len(sys.argv) > 1:
        c.override = sys.argv[1]
    else:
        c.auth()
    requester.cred = c
    resolver.cred = c
    resolver.prepare()
    curses.wrapper(cmain)

def status(statusbar, message):
    statusbar.clear()
    statusbar.bkgd(' ', curses.A_BOLD)
    statusbar.addstr('  ' + message, curses.A_BOLD)
    statusbar.move(0,0)
    statusbar.refresh()

def parse(text):
    global resolver

    reader = csv.reader(StringIO.StringIO(text), delimiter=';')
    records = []
    for row in reader:
        record = {}
        record['ip'] = row[0]
        record['hostname'] = resolver.resolve(row[0])
        record['uprate'] = float(row[1])
        record['downrate'] = float(row[2])
        # Sent packages (3) is skipped
        record['sendmb'] = float(row[4])
        # Received packages (5) is skipped
        record['recvmb'] = float(row[6])
        records.append(record)

    reversedrecords = reversed(sorted(records, key=lambda k: k['uprate']))
    sumup = sum(record['uprate'] for record in records)
    sumdown = sum(record['downrate'] for record in records)
    return (reversedrecords, sumup, sumdown)

def window(mainwin, text):
    mainwin.clear()
    mainwin.move(0,0)
    maxlines = mainwin.getmaxyx()[0] - 3

    (records, sumup, sumdown) = parse(text)

    mainwin.addstr("Culprit.py 0.1 - Total up: {0} Total down: {1} \n".format(sumup, sumdown))
    mainwin.addstr("\n")
    mainwin.addstr("{0:<15} {1:>8} {2:>8} {3:>15} {4:>15}\n".format("IP/HOST", "UPLOAD", "DOWNLOAD", "SENT MB", "RECV MB"), curses.A_BOLD)

    i = 0
    for record in records:
        if i == maxlines:
            break
        if record['hostname'] == record['ip']:
            attr = curses.A_DIM
        else:
            attr = curses.A_NORMAL

        try:
            mainwin.addstr("{0[hostname]:<15} {0[uprate]:>8.2f} {0[downrate]:>8.2f} {0[sendmb]:>15.2f} {0[recvmb]:>15.2f}\n".format(record), attr)
        except curses.error:
            pass
        i += 1
    mainwin.move(0,0)
    mainwin.refresh()

def cmain(stdscr):
    global requester

    (maxy, maxx) = stdscr.getmaxyx()
    curses.sb = curses.newwin(1, maxx, maxy-1, 0)
    mainwin = curses.newwin(maxy-1, maxx, 0, 0)

    while True:
        status(curses.sb, "Fetching...")
        dat = requester.fetch()
        status(curses.sb, "Parsing...")
        window(mainwin, dat)
        status(curses.sb, "Fetched %d records" % len(dat.split('\n')))
        time.sleep(5)

if __name__ == '__main__':
    main()
