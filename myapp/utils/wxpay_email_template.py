# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import os


class EmailTable(list):
    """
    email内的表格
    """

    def __init__(self, column_headers = [], description = ""):
        """
        初始化
        :param column_headers:表头，list类型，例如["字段1", "字段2", "字段3"]
        """
        self.column_size = None
        self.description = description
        self.column_headers = column_headers


    def add_row(self, row):
        """
        添加一列数据
        :param row:列表或者tuple类型， 例如[1,2,3,4,4]
        :return:
        """
        if not (isinstance(row, list) or isinstance(row, tuple)):
            raise Exception("param row must be object type of list or tuple")
        if len(row) == 0:
            raise Exception("not data found in your row")
        if not self.column_size:
            self.column_size = len(row)
        if self.column_size and len(row) != self.column_size:
            raise Exception("current row size does not equal to last one")
        self.append(row)


    def render(self):
        """
        渲染为html格式
        :return:
        """
        if not self.column_headers:
            self.column_headers = ["字段%s" % (i + 1) for i in range(0, self.column_size)]
        return """
        {description}
        <table  width="98%" cellpadding="0" bordercolor="#e2e2e2" width="90%" cellspacing="0" border= "1px" style="background-color: white;border-collapse: collapse;font-size: 12px;line-height: 20px;" >
            {table_header}
            {rows}
        </table>
        """.format(
            table_header = """<tr>{headers}</tr>""".format(headers = "".join([
                """<td style="padding-left: 5px;text-align:left;padding-top: 5px;padding-bottom: 5px;background-color: #EFEFEF;" align = "left">%s</td>""" % column_name for column_name in self.column_headers
                                                                            ])),
            rows = "".join([
                """<tr>%s</tr>""" % "".join(["""<td style="padding-left: 5px;text-align:left;padding-top: 5px;padding-bottom: 5px" align = "left">
                        %s
                    </td>""" % item_column for item_column in row])
                for row in self
            ]),
            description = "" if not self.description else """            <table width="90%%"  cellpadding="0" cellspacing="0" style="font-size: 12px">
                <tr>
                    <td style="background-color: white;padding-left: 10px;text-align:left;padding-top: 0px;padding-bottom: 0px;line-height: 30px;" align = "left">
                        %s
                    </td>
                </tr>
            </table><br />""" % self.description
        )


class WxPayEmailTemplate(dict):
    """
    微信支付邮件模版
    """

    BASE_TEMPLATE = """
<table background="#e2e2e2" height="100%" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse;text-align: center;font-size: 12px;font-family: 'Microsoft Sans Serif';background:#e2e2e2">
    <tr>
        <td valign="top" align="center">
            
            <table  cellpadding="0" cellspacing="0"  width="90%" height="20px" style="height: 20px">
                <tr>
                
                <td background="https://pay-weizhi-image-1258344707.cos.ap-shanghai.myqcloud.com/xdata/xdata_email_header.jpg" bgcolor="#007F56" width="860" height="100" valign="top" style="background-color: #007F56;background-image:url(https://pay-weizhi-image-1258344707.cos.ap-shanghai.myqcloud.com/xdata/xdata_email_header.jpg);background-repeat: no-repeat;overflow: hidden">
                  <!--[if gte mso 9]>
                  <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:860px;height:100px;">
                    <v:fill type="frame" src="https://pay-weizhi-image-1258344707.cos.ap-shanghai.myqcloud.com/xdata/xdata_email_header.jpg" color="#007F56" />
                    <v:textbox inset="0,0,0,0">
                  <![endif]-->
                  <table height="100px"  cellpadding="0" cellspacing="0" style="padding-left: 120px;color: white">
                    <tr>
                        <td style="font-size: 30px;line-height: 55px;font-family: 'Microsoft Sans Serif'">
                            {title}
                        </td>
                    </tr>
                    <tr>
                        <td  style="font-size: 12px;color: lightgray;line-height:20px">
                            {slogan}
                        </td>
                    </tr>
                  </table>
                  <!--[if gte mso 9]>
                    </v:textbox>
                  </v:rect>
                  <![endif]-->
                </td>
                </tr>
            </table>
        
            <table  cellpadding="0" cellspacing="0" width="90%">
                <tr >
                    <td style="background-color: white;padding: 5px;line-height: 30px;padding-top: 15px;padding-bottom: 15px;font-size: 12px" height="100px" width="90%">
                    Hi {receiver},<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;{quotation}
                    </td>
                </tr>
                <tr>
                <td>
                    <table  cellpadding="0" cellspacing="0"  width="90%" height="1px" style="height: 1px">
                        <tr><td height="1px" style="color: white;height: 1px;"></td></tr>
                    </table>
                </td>
                </tr>
            </table>

            {content}
            <table  cellpadding="0" cellspacing="0"  width="90%" height="20px" style="height: 20px">
                <tr><td height="20px" style="color: white;height: 20px;"></td></tr>
            </table>
            <table  cellpadding="0" cellspacing="0" width="90%">
                <tr>
                    <td height="30px" style="background-color: #007F56;color: white;text-align: center;font-size:12px" width="90%">
                        微信支付-数据中心
                    </td>
                </tr>
                <tr>
                <td>
                    <table  cellpadding="0" cellspacing="0"  width="90%" height="1px" style="height: 1px">
                        <tr><td height="1px" style="color: white;height: 1px;"></td></tr>
                    </table>
                </td>
                </tr>
            </table>
                
        </td>
    </tr>
</table>
"""

    def __init__(self, title, quotation, receiver = "", slogan = "", backgroup_image = None):
        """
        初始化
        :param title:邮件内容的标题
        :param slogan:title下面一段用于放置标语等信息的占位符
        :param quotation:引语，就是开头一段陈述的内容
        :param receiver:邮件接收人，主要用于替换Hi 后面的名字
        :param backgroup_image:背景图片，要求高度是100px，长度不能超过1024px
        """
        dict.__init__(self, title = title, quotation = quotation, receiver = receiver, slogan = slogan, sections = [])


    def add_section(self, content, titile = None):
        """
        添加一个分节块内容
        :param titile:块标题
        :param content:内容，可以是text、html、或者
        :return:
        """
        self["sections"].append({
            "title"   :   titile,
            "content" :   content if not isinstance(content, EmailTable) else content.render(),
            "index"   :   len(self["sections"]) + 1
        })


    def render(self):
        """
        渲染html
        :param content:
        :return:
        """
        return WxPayEmailTemplate.BASE_TEMPLATE.format(
            title = self["title"],
            slogan = self["slogan"],
            quotation = self["quotation"],
            receiver = self["receiver"],
            content = "".join([self.__make_section(item["title"], item["content"], item["index"]) for item in self["sections"]])
        )

    def __make_section(self, title, content, index):
        """
        生成section的html
        :param title:section的标题
        :param content:内容
        :param index:编号
        :return:
        """
        if not title:
            title_html = """"""
        else:
            title_html = """<table  cellpadding="0" cellspacing="0" width="90%">
                <tr>
                    <td width="30px" style="width:30px;background-color: #007F56;color: white;text-align: center;font-style: italic" >
                        {index}
                    </td>
                    <td style="background-color: white;padding-left: 10px;font-size: 14px;border-bottom: 1px solid #e2e2e2">
                        {title}
                    </td>
                </tr>
                <tr>
                <td>
                    <table  cellpadding="0" cellspacing="0"  width="90%" height="1px" style="height: 1px">
                        <tr><td height="1px" style="color: white;height: 1px;"></td></tr>
                    </table>
                </td>
                </tr>
            </table>""".format(index = index, title = title)
        return """
            <table  cellpadding="0" cellspacing="0"  width="90%" height="20px" style="height: 20px">
                <tr><td height="20px" style="color: white;height: 20px;"></td></tr>
            </table>
            {title_html}
            <table  cellpadding="0" cellspacing="0"  style="font-size: 12px" width="90%">
                <tr>
                    <td style="background-color: white;padding-left: 10px;text-align:left;padding-top: 10px;padding-bottom: 10px;line-height: 30px;" align = "left" width="90%">
                        {content}
                    </td>
                </tr>
                <tr>
                <td>
                    <table  cellpadding="0" cellspacing="0"  width="90%" height="1px" style="height: 1px">
                        <tr><td height="1px" style="color: white;height: 1px;"></td></tr>
                    </table>
                </td>
                </tr>
            </table>
            """.format(
            title_html = title_html,
            content = content
        )

