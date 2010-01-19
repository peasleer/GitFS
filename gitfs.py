#!/usr/bin/python

import os
import pyinotify
import time
import yagit
import gitserver

_git = None


# Subclass ProcessEvent with our own handlers
class EventHandler(pyinotify.ProcessEvent):
  def process_IN_CREATE(self, event):
    _git.handle_create(event.pathname)
    
  def process_IN_DELETE(self, event):
    _git.handle_delete(event.pathname)

  def process_IN_MODIFY(self, event):
    _git.handle_modify(event.pathname)

  def process_IN_MOVE_SELF(self, event):
    #_git.handle_move_self(event.pathname)
    pass

  def process_IN_MOVED_TO(self, event):
    #_git.handle_create(event.pathname)
    pass

  def process_IN_MOVED_FROM(self, event):
    #_git.handle_delete(event.pathname)
    pass


class GitFS():

  def __init__(self):
    
    self.gitRepos = { 'rep1': 'gitfs.cache1', 
                     'rep2': 'git://127.0.0.1/gitfs.cache2' }
    self.git = yagit.Yagit(self.gitRepos['rep1'])
    self.git.addRemote('rep2', self.gitRepos['rep2'])

    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE 
    mask = mask | pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF
    mask = mask | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
    wm.add_watch(self.gitRepos["rep1"], mask, rec=True, auto_add=True)
    self.notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
    self.gitserver = gitserver.GitServer()


  def start(self):
    
    self.notifier.start()
    self.gitserver.start()
    return


  def stop(self):
    self.notifier.stop()
    self.gitserver.stop()
    return



# Entrypoint
if "__main__" == __name__:
 
  gitfs = GitFS()
  gitfs.start()
  _git = gitfs.git

  try:
    while True:
      print "'stop' to quit, 'sync' to synchronize with other gitfs systems"
      input = raw_input( "$ " )
      if input == "stop":
        break
      elif input == "sync":
        _git.sync( )
        continue
      elif input == "autosync":
        _git.toggleAutosync()
      else:
        print "Invalid input, ctrl+c will quit cleanly if you are having trouble"
        continue

    print "Stopping"
    gitfs.stop()

  except Exception as detail:

    print "Runtime exception: " + str(detail)
    gitfs.stop()

