
import os
import paramiko

import tempfile
from smb.SMBConnection import SMBConnection

from smb.SMBHandler import SMBHandler

import socket

import urllib

import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p')

SAMBA_USERNAME = "ibmcam"
SAMBA_PASSWORD = "gc..1234"
SAMBA_PORT = 445
SAMBA_MYNAME = "anyname"
SAMBA_REMOTEIP = "192.168.224.8"
SAMBA_DOMAINNAME = ""
SAMBA_DIR = '/工程自动化/IBM项目组/0.计划/机器清单.xlsx'


class Smb(object):
    def __init__(self, username, password, server, share, port=445):
        # split username if it contains a domain (domain\username)
        domain, username = username.split('\\') if username.count('\\') == 1 else ('', username)
        # setup data
        self.domain    = str(domain)
        self.username  = str(username)
        self.password  = str(password)
        self.client    = socket.gethostname()
        self.server    = str(server)
        self.server_ip = socket.gethostbyname(server)
        self.share     = str(share)
        self.port      = port
        self.conn      = None
        self.connected = False
        # SMB.SMBConnection logs too much
        # smb_logger = logging.getLogger('SMB.SMBConnection')
        # smb_logger.setLevel(logging.WARNING)

    def connect(self):

        logging.info('self.username is %s, self.password  is %s, self.client is %s, self.server is %s ', self.username, self.password,
                                      self.client, self.server)
        try:
            self.conn = SMBConnection(self.username, self.password,
                                      self.client, self.server,
                                      use_ntlm_v2=True, domain=self.domain)

            logging.info('self.server_ip is %s, self.port  is %s', self.server_ip, self.port)

            self.connected = self.conn.connect(self.server_ip, self.port)
            logging.info('Connected to %s' % self.server)
            return self.connected
        except Exception as e:
            logging.exception('Connect failed. Reason: %s', e)
            return False



class ConnectSamba():

    def __init__(self):
        self.user_name = SAMBA_USERNAME
        self.pass_word = SAMBA_PASSWORD
        self.my_name = SAMBA_MYNAME
        self.domain_name = SAMBA_DOMAINNAME
        self.remote_smb_IP = SAMBA_REMOTEIP
        self.port = SAMBA_PORT
        self.dir = SAMBA_DIR

    def downloadFile(self, filename, download_filepath):
        '''
        下载文件
        :param filename: 保存到本地的文件名
        :param download_filepath: 保存到本地文件的路径
        :return:c
        '''

        print('downloadFile file_name is ' + filename)

        conn = SMBConnection(self.user_name, self.pass_word, self.my_name, self.domain_name, use_ntlm_v2=True)

        conn.connect(self.remote_smb_IP, self.port)
        file_obj = open(download_filepath + filename, 'wb')
        conn.retrieveFile(self.dir, filename, file_obj)

        print(type(file_obj))

        print(type(file_obj))

        file_obj.close()
        return True


    def uploadFile(self, filename, upload_path):
        '''
        上传文件
        :param filename: 上传文件的名称
        :param upload_path: 上传文件的路径
        :return:True or False
        '''
        try:
            conn = SMBConnection(self.user_name, self.pass_word, self.my_name, self.domain_name, use_ntlm_v2=True)
            conn.connect(self.remote_smb_IP, self.port)
            file_obj = open(upload_path + filename, 'rb')
            conn.storeFile(self.dir, filename, file_obj)
            file_obj.close()
            return True
        except:
            return False


def SMBScpFile2():

    opener = urllib.request.build_opener(SMBHandler)
    fh = opener.open('smb://192.168.224.8/工程自动化/IBM项目组/0.计划/test_data.txt')

    data = fh.read()

    print(data)

    fh.close()


def SMBScpFile(userID, password, client_machine_name, server_name,server_ip):

    # There will be some mechanism to capture userID, password, client_machine_name, server_name and server_ip
    # client_machine_name can be an arbitary ASCII string
    # server_name should match the remote machine name, or else the connection will be rejected
    conn = SMBConnection(userID, password, client_machine_name, server_name, use_ntlm_v2 = True)
    conn.connect(server_ip, 139)

    file_obj = tempfile.NamedTemporaryFile()
    file_attributes, filesize = conn.retrieveFile('smbtest', '/rfc1001.txt', file_obj)

    # Retrieved file contents are inside file_obj
    # Do what you need with the file_obj and then close it
    # Note that the file obj is positioned at the end-of-file,
    # so you might need to perform a file_obj.seek() if you need
    # to read from the beginning
    file_obj.close()



def RemoteScpFile(host_ip, host_port, host_username, host_password, remote_file, local_file):

  scp = paramiko.Transport((host_ip, host_port))

  scp.connect(username=host_username, password=host_password)
  sftp = paramiko.SFTPClient.from_transport(scp)

  sftp.get(remote_file, local_file)
  scp.close()
  return ("success")

def RemoteScpDir(host_ip, host_port, host_username, host_password, remote_path, local_path):

  scp = paramiko.Transport((host_ip, host_port))
  scp.connect(username=host_username, password=host_password)
  sftp = paramiko.SFTPClient.from_transport(scp)
  try:
    remote_files = sftp.listdir(remote_path)
    for file in remote_files:  #遍历读取远程目录里的所有文件
      local_file = local_path + file
      remote_file = remote_path + file
      sftp.get(remote_file, local_file)
  except IOError:  # 如果目录不存在则抛出异常
    return ("remote_path or local_path is not exist")
  scp.close()


if __name__ == '__main__':

    host_ip = '192.168.224.8'
    host_port = 445

    host_username = 'ibmcam'
    # host_username = 'chinafastprint\ibmcam'
    host_password = 'gc..1234'
    remote_path = '/工程自动化/IBM项目组/0.计划/机器清单.xlsx'
    local_path = '/Users/weilei/project/fastprint/05_test/02_remote_tmp_data/机器清单1.xlsx'
    RemoteScpFile(host_ip, host_port, host_username, host_password, remote_path, local_path)


    # SMBScpFile(host_username, host_password, 'weilei', remote_path, host_ip)

    # SMBScpFile2()
    #
    # smb =  ConnectSamba()
    # smb.downloadFile('机器清单.xlsx', '/Users/weilei/project/fastprint/05_test/02_remote_tmp_data/')

    # smb = Smb('ibmcam', 'gc..1234', '192.168.224.8', '工程自动化/IBM项目组/0.计划/')
    # smb.connect()
