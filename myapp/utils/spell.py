# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""


def to_spanish(class_name):
    """
    驼峰规则命名转换为西班牙命名法
    :param class_name:
    :return:
    """
    letters = []
    iIndex = 0
    for item_letter in class_name:
        if item_letter.isupper() is True:
            if iIndex > 0:
                letters.append("_%s" % item_letter.lower())
            else:
                letters.append("%s" % item_letter.lower())
        else:
            letters.append(item_letter)
        iIndex += 1
    return "".join(letters)