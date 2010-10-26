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
		record['uprate'] = float(row[1])
		record['downrate'] = float(row[2])
		# Sent packages (3) is skipped
		record['sendmb'] = float(row[4])
		# Received packages (5) is skipped
		record['recvmb'] = float(row[6])
		records.append(record)
	return reversed(sorted(records, key=lambda k: k['uprate']))

def window(mainwin, text):
	mainwin.clear()
	mainwin.move(0,0)
	maxlines = mainwin.getmaxyx()[0] - 1
	
	mainwin.addstr("{:<15} {:>8} {:>8} {:>15} {:>15}\n".format("IP/HOST", "UPLOAD", "DOWNLOAD", "SENT MB", "RECV MB"))
	
	i = 0
	for record in parse(text):
		if i == maxlines:
			break
		try:
			mainwin.addstr("{0[ip]:<15} {0[uprate]:>8.2f} {0[downrate]:>8.2f} {0[sendmb]:>15.2f} {0[recvmb]:>15.2f}\n".format(record))
		except curses.error:
			pass
		i += 1
	mainwin.move(0,0)
	mainwin.refresh()

def cmain(stdscr, r):
	(maxy, maxx) = stdscr.getmaxyx()
	sb = curses.newwin(1, maxx, maxy-1, 0)	
	mainwin = curses.newwin(maxy-1, maxx, 0, 0)
	
	while True:
		status(sb, "Fetching...")
		dat = r.fetch()
		status(sb, "Parsing...")
		window(mainwin, dat)
		status(sb, "Fetched %d records" % len(dat.split('\n')))
		time.sleep(5)

if __name__ == '__main__':
	main()
