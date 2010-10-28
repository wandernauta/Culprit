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

smbcache = {}

class Requester:
	raddress = "192.168.0.1"
	username = "admin"
	password = ""

	def auth(self):
		self.raddress = raw_input('Router IP: ')
		self.username = raw_input('Username: ')
		self.password = getpass.getpass('Password: ')

	def fetch(self):
		url = '%s:%s@%s/goform/updateIptAccount' % (self.username, self.password, self.raddress)
		return urllib.urlopen('http://' + url).read()
		

def main():
	r = Requester()
	r.auth()
	curses.wrapper(cmain, r)

def status(statusbar, message):
	statusbar.clear()
	statusbar.bkgd(' ', curses.A_BOLD)
	statusbar.addstr('  ' + message, curses.A_BOLD)
	statusbar.move(0,0)
	statusbar.refresh()

def parse(text):
	reader = csv.reader(StringIO.StringIO(text), delimiter=';')
	records = []
	for row in reader:
		record = {}
		record['ip'] = row[0]
		record['hostname'] = resolveip(row[0])
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

def resolveip(ip):
	global smbcache
	
	if smbcache.has_key(ip):
		return smbcache[ip]
		
	status(curses.sb, "Resolving {0}".format(ip))
	try:
		host = subprocess.check_output(["smbutil", "status", ip]).split('\n')[1].split(':')[1].strip()
		smbcache[ip] = host
	except Exception:
		smbcache[ip] = ip
		return ip
	return host

def window(mainwin, text, r):
	mainwin.clear()
	mainwin.move(0,0)
	maxlines = mainwin.getmaxyx()[0] - 3
	
	(records, sumup, sumdown) = parse(text)
	
	mainwin.addstr("Culprit.py 0.1 listening to {0.raddress} - Total up: {1} Total down: {2} \n".format(r, sumup, sumdown))
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

def cmain(stdscr, r):
	(maxy, maxx) = stdscr.getmaxyx()
	curses.sb = curses.newwin(1, maxx, maxy-1, 0)	
	mainwin = curses.newwin(maxy-1, maxx, 0, 0)
	
	while True:
		status(curses.sb, "Fetching...")
		dat = r.fetch()
		status(curses.sb, "Parsing...")
		window(mainwin, dat, r)
		status(curses.sb, "Fetched %d records" % len(dat.split('\n')))
		time.sleep(5)

if __name__ == '__main__':
	main()
