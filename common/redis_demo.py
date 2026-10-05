import  redis
# r = redis.Redis(host='192.168.56.200', port=6379, db=0)

# 使用连接池的方式连接，会对我们的连接进行一个管理
# 不使用decode_responses这个参数，下边会返回bytes，需要转化才能看到中文
pool = redis.ConnectionPool(host='192.168.56.200', port=6379, db=0,decode_responses=True)
redis_client = redis.Redis(connection_pool=pool)
# 字符串类型的处理
redis_client.set("name", "zhangsan")    #单独设置一个值
print(redis_client.get("name"))

redis_client.mset({"age": 18,"address":"昆明"})
print(redis_client.mget("name","age","address"))       #获取多这个值的时候，返回的是列表类型
print(redis_client.exists("name"))    #存在是 1，不存在是0
print(redis_client.get("myname"))

print(redis_client.get("myname"))
print(redis_client.dbsize())    #键的数量
print(redis_client.lastsave())


# ================================哈希类型操作======================
# 新增一个
redis_client.hset(name="userHash",key="username",value="xiaoyu")
# 新增多个
redis_client.hset(name="userHash2",mapping={"username":"xiaoyu",
                                            "password":"123456",
                                            "address":"昆明"})

print(redis_client.hget("userHash","username"))
print(redis_client.hgetall("userHash2"))


# ================================list、set类型操作======================
redis_client.rpush("numberRight",1,2,3,4,5,6)
redis_client.lpush("numberLeft",1,2,3,4,5,6)
# 遍历循环查看
for i in range(redis_client.llen("numberRight")):
    print(redis_client.lindex("numberRight",i))


redis_client.sadd("setNum",11,12,13,32,14)
set_number = redis_client.smembers("setNum")
print(set_number)
for i in set_number:
    print(i)

# ================================zset类型操作======================
redis_client.zadd("myzset",{"v1":10,"v2":20,"v3":30})
r = redis_client.zrangebyscore("myzset",20,30)
print(r)
r = redis_client.zrangebyscore("myzset",20,30,withscores=True)
print(r)
# 查具体成员的索引值，或者叫排名也行
print(redis_client.zrank("myzset","v1"))
