
# 使用前要先启动zookeeper和kafka服务
# 启动zookeeper要cd /home/lp/soft/kafka_2.11-1.1.0,然后 bin/zookeeper-server-start.sh config/zookeeper.properties
# 启动kafka要cd /home/lp/soft/kafka_2.11-1.1.0,然后bin/kafka-server-start.sh config/server.properties


# 消费者demo
# from kafka import KafkaConsumer
#
# consumer = KafkaConsumer('test',bootstrap_servers=['127.0.0.1:9092'])  #参数为接收主题和kafka服务器地址
#
# # 这是一个永久堵塞的过程，生产者消息会缓存在消息队列中,并且不删除,所以每个消息在消息队列中都有偏移
# for message in consumer:  # consumer是一个消息队列，当后台有消息时，这个消息队列就会自动增加．所以遍历也总是会有数据，当消息队列中没有数据时，就会堵塞等待消息带来
#     print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,message.offset, message.key,message.value))
#



# ======消费者分组==========
# from kafka import KafkaConsumer
# # 使用group,对于同一个group的成员只有一个消费者实例可以读取数据
# consumer = KafkaConsumer('test',group_id='my-group',bootstrap_servers=['127.0.0.1:9092'])
# for message in consumer:
#     print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,message.offset, message.key,message.value))



# =====读取消息队列最早或最新的消息========
# from kafka import KafkaConsumer
# consumer = KafkaConsumer('test',auto_offset_reset='earliest',bootstrap_servers=['127.0.0.1:9092'])
# for message in consumer:
#     print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,message.offset, message.key,message.value))
#


# # ==========读取指定位置消息===============
# from kafka import KafkaConsumer
# from kafka.structs import TopicPartition
#
# consumer = KafkaConsumer('test',bootstrap_servers=['127.0.0.1:9092'])
#
# print(consumer.partitions_for_topic("test"))  #获取test主题的分区信息
# print(consumer.topics())  #获取主题列表
# print(consumer.subscription())  #获取当前消费者订阅的主题
# print(consumer.assignment())  #获取当前消费者topic、分区信息
# print(consumer.beginning_offsets(consumer.assignment())) #获取当前消费者可消费的偏移量
# consumer.seek(TopicPartition(topic='test', partition=0), 5)  #重置偏移量，从第5个偏移量消费
# for message in consumer:
#     print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,message.offset, message.key,message.value))



# =======订阅多个消费者==========

# from kafka import KafkaConsumer
# from kafka.structs import TopicPartition
#
# consumer = KafkaConsumer(bootstrap_servers=['127.0.0.1:9092'])
# consumer.subscribe(topics=('test','test0'))  #订阅要消费的主题
# print(consumer.topics())
# print(consumer.position(TopicPartition(topic='test', partition=0))) #获取当前主题的最新偏移量
# for message in consumer:
#     print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,message.offset, message.key,message.value))


# ==========消费者(手动拉取消息)============
#
# from kafka import KafkaConsumer
# import time
#
# consumer = KafkaConsumer(bootstrap_servers=['127.0.0.1:9092'])
# consumer.subscribe(topics=('test','test0'))
# while True:
#     msg = consumer.poll(timeout_ms=5)   #从kafka获取消息
#     print(msg)
#     time.sleep(2)


# ==============消息恢复和挂起===========

from kafka import KafkaConsumer
from kafka.structs import TopicPartition
import time

consumer = KafkaConsumer(bootstrap_servers=['127.0.0.1:9092'])
consumer.subscribe(topics=('test'))
consumer.topics()
consumer.pause(TopicPartition(topic=u'test', partition=0))  # pause执行后，consumer不能读取，直到调用resume后恢复。
num = 0
while True:
    print(num)
    print(consumer.paused())   #获取当前挂起的消费者
    msg = consumer.poll(timeout_ms=5)
    print(msg)
    time.sleep(2)
    num = num + 1
    if num == 10:
        print("resume...")
        consumer.resume(TopicPartition(topic='test', partition=0))
        print("resume......")