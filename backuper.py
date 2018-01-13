#!/usr/bin/python
#
# Backuper for OpenStack Instances
#
# Copyright (C) 2018 Henry Spanka
#
# Authors:
#  Henry Spanka <henry@myvirtualserver.de>
#
# This work is licensed under the terms of the GNU GPL, version 2.  See
# the COPYING file in the root directory.

import argparse
import os
import sys
import dumper
from tendo import singleton
from classes.credentials import Credentials
from classes.nova import Nova
from datetime import datetime
import time

def checkEnvExists(name):
    if os.environ.get(name) is None:
        displayMessage('error', "Error: Environment variable %s not set." % name)
        sys.exit(1)

def displayMessage(level, message):
    date = datetime.now()
    print date.strftime('%Y-%m-%d %H:%M:%S - ') + level.upper() + ': ' + message

def main():
    parser = argparse.ArgumentParser(description='OpenStack Backuper')

    displayMessage('info', 'Starting OpenStack Backuper')

    for env in ['OS_AUTH_URL', 'OS_PROJECT_ID', 'OS_USERNAME',
    'OS_PASSWORD', 'OS_REGION_NAME', 'OS_USER_DOMAIN_NAME']:
        checkEnvExists(env)

    me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

    auth_url = os.environ.get('OS_AUTH_URL')
    project_id = os.environ.get('OS_PROJECT_ID')
    username = os.environ.get('OS_USERNAME')
    password = os.environ.get('OS_PASSWORD')
    user_domain_name = os.environ.get('OS_USER_DOMAIN_NAME')

    credentials = Credentials(auth_url=auth_url,
                              username=username,
                              password=password,
                              project_id=project_id,
                              user_domain_name=user_domain_name)

    nova = Nova(credentials)

    displayMessage('info', 'Getting server list')

    servers = nova.getServers()

    for server in servers:
        try:
            # server = nova.getServer('b1d7ec28-486b-4c58-aa78-e7f7e678449d')
            displayMessage('info', 'Processing Server %s' % server.id)
            if not nova.validateServer(server):
                displayMessage('error', 'Server %s can not be backuped' % server.id)
                continue

            displayMessage('info', 'Locking server %s for backup' % server.id)
            nova.lockServer(server)

            if not nova.validateServer(server):
                displayMessage('error', 'Server %s can not be backuped after lock' % server.id)
                nova.unlockServer(server)
                continue

            displayMessage('info', 'Backing up server %s' % server.id)
            nova.backupServer(server, 'weekly', 1)

            elapsed = 0

            while (nova.stillBackingUp(server)):
                time.sleep(60)
                elapsed = elapsed + 60

                if (elapsed > 60*10):
                    displayMessage('info', 'Server {} still backing up - state: {}'.format(server.id, getattr(nova.getServer(server.id), 'OS-EXT-STS:task_state')))
                    elapsed = 0

            displayMessage('info', 'Backup of server %s complete' % server.id)

            nova.unlockServer(server)

            displayMessage('info', 'Server %s unlocked' % server.id)
        except KeyboardInterrupt:
            nova.unlockServer(server)
            displayMessage('info', 'Server %s unlocked' % server.id)
            displayMessage('warning', 'Backup interrupted')
            exit(0)


    displayMessage('info', 'Processed all servers.')
    exit(0)

if __name__ == '__main__':
    main()
