'''
Created on Mar 27, 2017

@author: Tyler Thompson
'''

from git import *
from Drivers import Config
import time

class Git(object):
    '''
    classdocs
    '''

    def __init__(self):
        configDriver = Config.Config()
        self.repoRoot = configDriver.getConfigRoot().replace('/configs', '')
        self.repo = Repo(self.repoRoot, odbt=GitDB)
        self.branch = self.repo.active_branch
        self.remote = self.repo.remotes.origin.url
        self.author = self.repo.head.commit.author
        self.authorContact = self.repo.head.commit.committer.email
        self.description = self.repo.description
        self.commit = self.repo.heads.master.commit
        self.lastCommittedDate = time.asctime(time.gmtime(self.repo.heads.master.commit.committed_date))

