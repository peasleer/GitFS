#!/usr/bin/python

import os
import subprocess
import signal
import socket

class GitServer:

  def __init__(self, port=9418, path=os.getcwd()):
    self.port = port
    self.path = path
    self.pid = 0
    return

  def start(self):

    if self.isBound(self.port):
      print "Git daemon already running"
      return 

    # Start the git server, listens on port 9418 by default.
    # the preexec_fn field stores the process group's id. "git daemon"
    # spawns a child process "git-daemon", if we don't set a process
    # group id for it, we can't kill the child, and thus can't kill
    # kill the git daemon.
    p = subprocess.Popen(["git", 
                          "daemon", 
                          "--reuseaddr", 
                          "--base-path=" + self.path,
                          "--enable=receive-pack",
                          "--export-all"
                         ], 
                         #stdout=subprocess.PIPE,
                         #stderr=subprocess.STDOUT,
                         preexec_fn=os.setsid
                        )
    self.pid = p.pid
    print "Git daemon started"

    return


  def stop(self):

    if self.pid == 0:
      print "Git daemon wasn't running, not stopping"
      return

    # Kill all members of the process group under the pid of the "git daemon"
    # sub-process
    os.killpg(self.pid, signal.SIGINT)
    print "Git daemon stopped"

    return

  
  def isBound(self, port):
    sock = None
    err = None
    try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.bind(("0.0.0.0", port))
    except socket.error as msg:
      err = msg

    sock.close()

    if err is None:
      return False
    else:
      return True

