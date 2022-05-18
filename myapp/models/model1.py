from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey,Float
from sqlalchemy.orm import relationship

from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Enum,
    Text,
)


# 添加自定义model
from sqlalchemy import Column, Integer, String, ForeignKey ,Date,DateTime
from flask_appbuilder.models.decorators import renders
from flask import Markup
import datetime
metadata = Model.metadata


# 定义model
class Model1(Model):
    __tablename__ = 'model1'
    id = Column(Integer, primary_key=True)
    attr1 = Column(String(50), unique = True, nullable=False)

    def __repr__(self):
        return self.attr1


# 定义model
class Model2(Model):
    __tablename__='model2'
    id = Column(Integer, primary_key=True)
    attr1 = Column(String(150), unique = True, nullable=False)   # 字符串型字段
    attr2 = Column(Enum('select1','select2'),nullable=False,default='select2')   # 枚举型字段

    attr3_id = Column(Integer, ForeignKey('model1.id'))    # 定义外键id
    attr3_object = relationship('Model1',foreign_keys=[attr3_id])  # 一对多关系，不存储数据库。第一个参数可以是model或者或者model的名称

    attr4 = Column(Text,default='{}')   # 文本型字段
    attr5 = Column(Boolean, default=True)  # 布尔型字段


    def __repr__(self):
        return self.attr1

    # 自定义一个函数字段和渲染样式，供前端显示
    @renders('date')
    def my_date(self):
        return Markup('<b style="color:red">' + self.attr2 + '</b>')

    @property
    def aa(self):
        return 'attr1:'+self.attr1




