# Nova Class

from keystoneauth1 import session
from novaclient import client
from datetime import datetime

class Nova:
    def __init__(self, credentials):
        sess = session.Session(auth=credentials.getAuth())
        self._client = client.Client(2, session=sess)

    def getServers(self):
        return self._client.servers.list(search_opts={'all_tenants': 1})

    def getServer(self, server_id):
        return self._client.servers.get(server_id)

    def validateServer(self, server):
        updated_server = self._client.servers.get(server.id)

        if getattr(updated_server, 'OS-EXT-STS:task_state') is None:
            return True

        return False

    def lockServer(self, server):
        return server.lock()

    def unlockServer(self, server):
        return server.unlock()

    def backupServer(self, server, backup_type, rotation):
        name = self.generateBackupName(server, backup_type)
        return server.backup(name, backup_type, rotation)

    def generateBackupName(self, server, backup_type):
        date = datetime.now()
        name = 'backup-' + date.strftime('%Y-%m-%d') + '-{}-{}'.format(backup_type, server.id)
        return name

    def stillBackingUp(self, server):
        updated_server = self._client.servers.get(server.id)

        task_state = getattr(updated_server, 'OS-EXT-STS:task_state')

        if (task_state in ['image_backup', 'image_uploading', 'image_pending_upload']):
            return True

        return False
