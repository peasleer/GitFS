#!/usr/bin/python

import os
import subprocess


class NotADirectoryException():
  
  def __init__(self, path):
    self.path = path
    self.message = "Given path " + path + " is not a directory"

  def __str__(self):
    return self.message



class Yagit():

  def __init__(self, path):
    print "Given path: " + path
    if not os.path.isdir(path):
      raise NotADirectoryException(path)

    self.path = path 
    # Absolute path to repository
    self.abspath = os.getcwd() + "/" + path
  
    self.autosync=False

    if not self.isRepo():
      self.createRepo()
   
    # URLs to remote repositories we should sync with
    self.remotes = {}

    # Get any changes that were made while we were off,
    # track them, and commit them as most current
    pipe = subprocess.Popen('git add .', shell=True, cwd=self.abspath)
    pipe.wait()
    self.commitChanges("Changes that occurred while we weren't monitoring")

    return


  # Populate our list of remote repositories from the existing remotes
  # configured for this repository
  def populateRemotes(self):
    pipe = subprocess.Popen('git remote --verbose show', 
                            shell=True, 
                            cwd=self.abspath, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    pipe.wait()
  
    for line in pipe.stdout:
      if len(line.strip()) == 0:
        continue
      
      self.remotes[line.split('\t')[0]] = line.split('\t')[1]

    return 


  # Given a path to a directory, creates a repository
  def createRepo(self):
    print "Creating repository at " + self.path
    
    if not os.path.exists(self.path):
      os.mkdir(self.path)
    
    pipe = subprocess.Popen('git init', shell=True, cwd=self.abspath)
    pipe.wait()
    # add all existing files to git repo
    pipe = subprocess.Popen('git add .', shell=True, cwd=self.abspath)
    pipe.wait()
 
    # --- The stuff above is essential for creating the repository ---
    # The stuff below is a workaround to allow remote repositories to update
    # our working repository
    #

    pipe = subprocess.Popen('git commit --allow-empty -m "created gitfs cache"',
                            shell=True, 
                            cwd=self.abspath)
    pipe.wait()

    pipe = subprocess.Popen("git branch incoming",
                          shell=True,
                          cwd=self.abspath)
    pipe.wait()

    pipe = subprocess.Popen('cp ../post-receive .git/hooks/post-receive', 
                            shell=True,
                            cwd=self.abspath)
    pipe.wait()

    pipe = subprocess.Popen('chmod u+x .git/hooks/post-receive',
                            shell=True,
                            cwd=self.abspath)

    return


  # Determine if a given path exists and is a repository
  def isRepo(self):
    
    try:
      if os.path.isdir( self.path + "/.git" ):
        return True
    except:
      return False
    
    return False 


  # If the path contains ".git", it belongs to git's repository
  # maintenance and should be ignored by our handlers
  def isGitRepoFile(self, path):
    if path.find(".git/") != -1:
      return True

    return False


  # Item at path was created, handle it
  def handle_create(self, path):

    if self.isGitRepoFile(path):
      return

    if os.path.isdir(path):
      if len(os.listdir(path)) == 0:
        # We have an emptry directory, which git doesn't like. Touch a 
        # useless .gitignore file so we can add it.
        open(path + "/.gitignore", 'a').close()

    print "Handling creation of new file at: " + path 
   
    # tell git to track the new file
    pipe = subprocess.Popen('git add "' + path + '"',
                            shell=True,
                            cwd=self.abspath)
    pipe.wait()

    self.commitChanges("added file " + os.path.basename(path))

    return


  # Item at path was modified, handle it
  def handle_modify(self, path):
    if self.isGitRepoFile(path):
      return

    print "Handling modification of existing file at: " + path 
    
    # Different hook, but 'git add' is used both for adding new files
    # and staging modifications to tracked files
    pipe = subprocess.Popen('git add "' + path +'"',
                            shell=True,
                            cwd=self.abspath)
    pipe.wait()

    self.commitChanges("storing modification of file " + os.path.basename(path))

    return


  # Item at path was deleted, handle it
  def handle_delete(self, path):
    if self.isGitRepoFile(path):
      return

    print "Handling deletion of file at: " + path 

    pipe = subprocess.Popen('git rm -rf --cached "' + path +'"',
                            shell=True,
                            cwd=self.abspath)
    pipe.wait()

    self.commitChanges("removed file " + os.path.basename(path))

    return
 
  
  # Item at path was moved, remove old, in with new
  def handle_move_self(self, path):
    pass


  def commitChanges(self, message):
    print "Committing changes with messsage " + message
    pipe = subprocess.Popen('git commit -a -m "' + message + '"',
                            shell=True,
                            cwd=self.abspath)
    pipe.wait()
   
    if self.autosync:
      self.sync()

    return


  def addRemote(self, shortname, gitUrl):

    if shortname in self.remotes:
      print "Already have entry for " + shortname + ", returning"
      return

    pipe = subprocess.Popen("git remote add \"" + shortname + "\" " + '"' + gitUrl + '"',
                            shell=True,
                            cwd=self.abspath,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    pipe.wait()

    # Add new remote to this object's store
    self.populateRemotes()

    return


  def sync(self):

    # First clean up the repository so we aren't pushing more than is necessary
    self.repoCleanup()

    for key in self.remotes:
      print "Pushing updates to " + self.remotes[key]

      # Push our updates to the remote repository's 'incoming' branch
      pipe = subprocess.Popen("git push " + key + " --force master:incoming",
                              shell=True,
                              cwd=self.abspath,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
      pipe.wait()

      if pipe.returncode != 0:
        print "Error pushing updates to " + key + " at " + self.remotes[key]
        for line in pipe.stderr:
          print line
        return
      
      
    return


  def toggleAutosync(self):
    if self.autosync:
      self.autosync = False
    else:
      self.autosync = True

    return


  def repoCleanup(self):
      pipe = subprocess.Popen("git gc --auto",
                              shell=True,
                              cwd=self.abspath,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
      pipe.wait()




