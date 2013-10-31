import os
from cStringIO import StringIO
from threading import Lock
import tempfile

from indico.util.redis import redis

from whoosh.filedb.structfile import StructFile
from whoosh.filedb.filestore import Storage, FileStorage
from whoosh.util import random_name


class RedisStorage(Storage):
    """
    Storage object that keeps the index in redis.
    """
    supports_mmap = False

    def __file(self, name):
        return self.client.hget("RedisStore:%s" % self.folder, name)

    def __init__(self, redis_url, namespace='whoosh'):
        self.folder = namespace
        self.client = redis.StrictRedis.from_url(redis_url)
        self.locks = {}

    def file_modified(self, name):
        return -1

    def list(self):
        return self.client.hkeys("RedisStore:%s" % self.folder)

    def clean(self):
        self.client.delete("RedisStore:%s" % self.folder)

    def total_size(self):
        return sum(self.file_length(f) for f in self.list())

    def file_exists(self, name):
        return self.client.hexists("RedisStore:%s" % self.folder, name)

    def file_length(self, name):
        if not self.file_exists(name):
            raise NameError
        return len(self.__file(name))

    def delete_file(self, name):
        if not self.file_exists(name):
            raise NameError
        self.client.hdel("RedisStore:%s" % self.folder, name)

    def rename_file(self, name, newname, safe=False):
        if not self.file_exists(name):
            raise NameError("File %r does not exist" % name)
        if safe and self.file_exists(newname):
            raise NameError("File %r exists" % newname)

        content = self.__file(name)
        pl = self.client.pipeline()
        pl.hdel("RedisStore:%s" % self.folder, name)
        pl.hset("RedisStore:%s" % self.folder, newname, content)
        pl.execute()

    def create_file(self, name, **kwargs):
        def onclose_fn(sfile):
            self.client.hset("RedisStore:%s" % self.folder, name, sfile.file.getvalue())
        f = StructFile(StringIO(), name=name, onclose=onclose_fn)
        return f

    def open_file(self, name, *args, **kwargs):
        if not self.file_exists(name):
            raise NameError("No such file %r" % name)

        def onclose_fn(sfile):
            self.client.hset("RedisStore:%s" % self.folder, name, sfile.file.getvalue())
        return StructFile(StringIO(self.__file(name)), name=name, onclose=onclose_fn, *args, **kwargs)

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = Lock()
        return self.locks[name]

    def temp_storage(self, name=None):
        tdir = tempfile.gettempdir()
        name = name or "%s.tmp" % random_name()
        path = os.path.join(tdir, name)
        tempstore = FileStorage(path)
        return tempstore.create()
