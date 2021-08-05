
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email
from smtplib import SMTP
import smtplib
import os.path
import mimetypes


class Email_Client():
    def __init__(self,host="smtp.exmail.qq.com",sender="luan.peng@intellif.com",password="1qaz2wsx#EDC",postfix="intellif.com",recips=["luan.peng@intellif.com"]):
        self.HOST=host            #使用的邮箱的smtp服务器地址，这里是163的smtp地址，经过测试网易和搜狐的邮箱可用
        self.SENDER=sender                           #用户名
        self.PASSWORD=password                             #密码
        self.POSTFIX=postfix                     #邮箱的后缀，网易就是163.com
        self.RECIPS= recips  #这里接收人也设置为自己




    # 一个包含文本和html的多部分邮件。多部分消息通常包含纯文本和html格式，客户端自行选择显示哪个。（web客户端显示html，命令行客户端显示纯文本）
    def make_text_msg(self,message):
        myemail = MIMEMultipart('alternative')
        text = MIMEText(message+'\r\n', 'plain',_charset="utf-8")  #纯文本的邮件消息正文
        myemail.attach(text)  #消息正文绑定到邮件对象
        return myemail

    def make_html_msg(self,html='<html><body><h1>Hello World!</h1></body></html>'):
        myemail = MIMEMultipart('alternative')
        html_msg = MIMEText(html, 'html')
        myemail.attach(html_msg)  # 消息正文绑定到邮件对象
        return myemail


    # 创建一个文本和图片的邮件
    def make_img_msg(self,imgfile):
        f = open(imgfile, 'rb')  #创建文件指针,这里要以rb的模式取读
        data = f.read()  #读取图片成字节流
        f.close()  #文件关闭
        ctype, encoding = mimetypes.guess_type(imgfile)   #ctype为根据文件获取的数据传输类型image/jpeg，encoding应该为None
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)   #maintype为文件所属类image，subtype为具体文件类型jpeg
        myemail = MIMEImage(data, name=subtype)  #生成图片邮件,name=文件类型jpeg
        basename = os.path.basename(imgfile)  #basename为文件名，不包含路径
        myemail.add_header('Content-Disposition','attachment; filename="%s"' % basename)  #添加邮件头
        return myemail

    # 创建一个文本和文件的邮件
    def make_file_msg(self,file_name):
        # 构造MIMEBase对象做为文件附件内容并附加到根容器
        ctype, encoding = mimetypes.guess_type(file_name)  # ctype为根据文件获取的数据传输类型image/jpeg，encoding应该为None
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)  # maintype为文件所属类image，subtype为具体文件类型jpeg
        print(maintype,subtype)
        ## 读入文件内容并格式化
        f = open(file_name, 'rb')  # 创建文件指针,这里要以rb的模式取读
        myemail = MIMEBase(maintype, subtype)
        myemail.set_payload(f.read())  #设置负载数据
        f.close()
        email.encoders.encode_base64(myemail)  #将邮件编码
        #设置附件头
        basename = os.path.basename(file_name) #basename为文件名，不包含路径
        myemail.add_header('Content-Disposition','attachment; filename="%s"' % basename)  #添加邮件头
        return myemail

    def sendMsg(self,subject, message):

        msg['From'] = self.SENDER
        msg['To'] = ', '.join(self.RECIPS)
        msg['Subject'] = subject
        print(msg)
        sendSvr = smtplib.SMTP()
        sendSvr.connect(self.HOST)  # 连接服务器
        sendSvr.login(self.SENDER, self.PASSWORD)  # 登录操作
        errs = sendSvr.sendmail(self.SENDER, self.RECIPS, message.as_string())  #参数：发件人，收件人，消息正文
        sendSvr.quit()


if __name__ == '__main__':

    email_client = Email_Client()
    msg = email_client.make_text_msg('出现了问题,检查一下吧')
    email_client.sendMsg('aicloud face-searh check', msg)

    # print('发送图片消息体')
    # msg = make_img_msg(r'D:/test.jpg')
    # msg['From'] = SENDER
    # msg['To'] = ', '.join(RECIPS)
    # msg['Subject'] = '图片消息邮件'
    # sendMsg(SENDER, RECIPS, msg.as_string())
    #
    # print('发送文件消息体')
    # msg = make_file_msg(r'D:/test.mp4')
    # msg['From'] = SENDER
    # msg['To'] = ', '.join(RECIPS)
    # msg['Subject'] = '文件消息邮件'
    # sendMsg(SENDER, RECIPS, msg.as_string())
