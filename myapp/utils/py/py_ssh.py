import paramiko
import scpclient
from .config import *
import logging,json,time,datetime

class SSH_Client(object):
    def __init__(self, user=SSH_USER, password=SSH_PASSWORD, port=SSH_PORT, ips=SSH_IP):
        self.user = user
        self.password = password
        self.port = port
        self.ip = ips

    def connect(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.ip, self.port, self.user, self.password,timeout=3)
            logging.info("ssh connect success")
        except Exception as e:
            logging.info("ssh connect error %s" % e)
    # 执行命令
    def cmd(self,command):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        return exit_status,stdout.read()
    # 发送文件
    def put(self,local_file_abs,remote_file_abs):
        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
        # sftp = self.ssh.open_sftp()
        sftp.put(local_file_abs,remote_file_abs)
    # 获取文件
    def get(self,remote_file_abs,local_file_abs):
        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
        # sftp = self.ssh.open_sftp()
        sftp.get(remote_file_abs,local_file_abs)

    # def scp(self,filepath,remote_path):
    #     with closing(scpclient.Write(self.ssh.get_transport(), "~")) as scp:
    #         scp.send_file(filepath, True, remote_filename=remote_path) # - -True意味着保持文件的日期

    def close(self):
        self.ssh.close()
        logging.info("ssh close success")



if __name__=="__main__":
    ssh = SSH_Client('intellif','introcks','22','192.168.11.32')
    ssh.connect()
    # ssh.cmd('mkdir /home/intellif/ftp1/20180928')
    # ssh.cmd('rm -rf /home/intellif/ftp1/20180929')
    statue,result = ssh.cmd('pwd')
    print(statue,result)





