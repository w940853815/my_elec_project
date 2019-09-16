"""chat restful."""
import json
import time
import uuid

import redis
from flask_restful import reqparse

from common import BaseResource, rest_resource

# redis 读出来的字符串会转为bytes,加encoding='utf8', decode_responses=True按传入的编码方式转换,详情见https://huangzhw.github.io/2019/02/01/python3-redis-encoding/
conn = redis.Redis(host='localhost',
                   port=6379,
                   db=6,
                   encoding='utf8',
                   decode_responses=True)


@rest_resource
class ChatSession(BaseResource):
    """聊天会话."""

    endpoints = ['chat/session']

    def post(self):
        """创建聊天会话（创建一个群组）."""
        parser = reqparse.RequestParser()
        parser.add_argument('sender', type=str, required=True)
        parser.add_argument('recipients', type=str, required=True)
        parser.add_argument('message', type=str, required=True)
        args = parser.parse_args()
        sender = args.sender
        recipients = json.loads(args.recipients)
        message = args.message
        chat_id = create_chat(conn, sender, recipients, message, chat_id=None)
        return {'chat_id': chat_id}


@rest_resource
class GroupAdd(BaseResource):
    """加入群组."""

    endpoints = ['group/add']

    def post(self):
        """加入群组."""
        parser = reqparse.RequestParser()
        parser.add_argument('chat_id', type=str, required=True)
        parser.add_argument('user', type=str, required=True)
        args = parser.parse_args()
        chat_id = args.chat_id
        user = args.user
        try:
            join_chat(conn, chat_id, user)
            return {'msg': 'success'}
        except Exception as e:
            return {'msg': e}


@rest_resource
class GroupLeave(BaseResource):
    """离开群组."""

    endpoints = ['group/leave']

    def post(self):
        """离开群组."""
        parser = reqparse.RequestParser()
        parser.add_argument('chat_id', type=str, required=True)
        parser.add_argument('user', type=str, required=True)
        args = parser.parse_args()
        chat_id = args.chat_id
        user = args.user
        try:
            leave_chat(conn, chat_id, user)
            return {'msg': 'success'}
        except Exception as e:
            return {'msg': e}


@rest_resource
class Message(BaseResource):
    """消息."""

    endpoints = ['message']

    def get(self):
        """获取消息."""
        parser = reqparse.RequestParser()
        parser.add_argument('recipient', type=str, required=True)
        args = parser.parse_args()
        recipient = args.recipient
        chat_info = fetch_pending_messages(conn, recipient)
        return {'chat_info': chat_info}

    def post(self):
        """发送消息."""
        pass


def acquire_lock(conn, lockname, acquire_timeout=10):
    """获得锁.

    :param conn: redis连接
    :param lockname: 锁名称
    :param acquire_timeout: 超时时间, defaults to 10
    :return: bool
    """
    identifier = str(uuid.uuid4())

    end = time.time() + acquire_timeout
    while time.time() < end:
        if conn.setnx('lock:' + lockname, identifier):
            return identifier

        time.sleep(.001)

    return False


def release_lock(conn, lockname, identifier):
    """释放锁.

    :param conn: redis连接
    :param lockname: 锁名称
    :param identifier: 标示符
    :return: bool
    """
    pipe = conn.pipeline(True)
    lockname = 'lock:' + lockname

    while True:
        try:
            pipe.watch(lockname)
            if pipe.get(lockname) == identifier:
                pipe.multi()
                pipe.delete(lockname)
                pipe.execute()
                return True

            pipe.unwatch()
            break

        except redis.exceptions.WatchError:
            pass

    return False


def create_chat(conn, sender, recipients, message, chat_id=None):
    """创建聊天会话.

    :param conn: redis连接
    :param sender: 发送者
    :param recipients: 收件人
    :param message: 消息
    :param chat_id: [description], defaults to None
    :return: chat_id
    """
    chat_id = chat_id or str(conn.incr('ids:chat:'))

    recipients.append(sender)
    recipientsd = dict((r, 0) for r in recipients)

    pipeline = conn.pipeline(True)
    pipeline.zadd('chat:' + chat_id, **recipientsd)
    for rec in recipients:
        pipeline.zadd('seen:' + rec, chat_id, 0)
    pipeline.execute()

    return send_message(conn, chat_id, sender, message)


def send_message(conn, chat_id, sender, message):
    """发送消息.

    :param conn: redis连接
    :param chat_id: chat_id
    :param sender: 发送者
    :param message: 消息
    :return: chat_id
    """
    identifier = acquire_lock(conn, 'chat:' + chat_id)
    if not identifier:
        raise Exception("Couldn't get the lock")
    try:
        mid = conn.incr('ids:' + chat_id)
        ts = time.time()
        packed = json.dumps({
            'id': mid,
            'ts': ts,
            'sender': sender,
            'message': message,
        })

        conn.zadd('msgs:' + chat_id, packed, mid)
    finally:
        release_lock(conn, 'chat:' + chat_id, identifier)
    return chat_id


def fetch_pending_messages(conn, recipient):
    """拉取待读信息.

    :param conn: redis连接
    :param recipient: 收件人
    :return: 聊天信息
    """
    seen = conn.zrange('seen:' + recipient, 0, -1, withscores=True)

    pipeline = conn.pipeline(True)

    for chat_id, seen_id in seen:
        pipeline.zrangebyscore('msgs:' + chat_id, seen_id + 1, 'inf')
    chat_info = zip(seen, pipeline.execute())
    print(chat_info)
    chat_data = []
    for i, ((chat_id, seen_id), messages) in enumerate(chat_info):
        if not messages:
            continue
        messages[:] = map(json.loads, messages)
        seen_id = messages[-1]['id']
        conn.zadd('chat:' + chat_id, recipient, seen_id)

        min_id = conn.zrange('chat:' + chat_id, 0, 0, withscores=True)

        pipeline.zadd('seen:' + recipient, chat_id, seen_id)
        if min_id:
            pipeline.zremrangebyscore('msgs:' + chat_id, 0, min_id[0][1])
        # chat_info[i] = (chat_id, messages)
        chat_data.append((chat_id, messages))
    pipeline.execute()
    return chat_data


def join_chat(conn, chat_id, user):
    """加入群聊.

    :param conn: redis连接
    :param chat_id: chat_id
    :param user: 用户id
    """
    message_id = int(conn.get('ids:' + chat_id))

    pipeline = conn.pipeline(True)
    pipeline.zadd('chat:' + chat_id, user, message_id)
    pipeline.zadd('seen:' + user, chat_id, message_id)
    pipeline.execute()


def leave_chat(conn, chat_id, user):
    """离开群聊.

    :param conn: redis连接
    :param chat_id: chat_id
    :param user: 用户id
    """
    pipeline = conn.pipeline(True)
    pipeline.zrem('chat:' + chat_id, user)
    pipeline.zrem('seen:' + user, chat_id)
    pipeline.zcard('chat:' + chat_id)

    if not pipeline.execute()[-1]:
        pipeline.delete('msgs:' + chat_id)
        pipeline.delete('ids:' + chat_id)
        pipeline.execute()
    else:
        oldest = conn.zrange('chat:' + chat_id, 0, 0, withscores=True)
        conn.zremrangebyscore('msgs:' + chat_id, 0, oldest[0][1])
