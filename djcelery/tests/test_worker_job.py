# -*- coding: utf-8 -*-
import unittest2 as unittest

from celery.utils import gen_unique_id
from celery.decorators import task as task_dec

from celery.tests.test_worker_job import jail


@task_dec()
def mytask(i, **kwargs):
    return i ** i


@task_dec()
def get_db_connection(i, **kwargs):
    from django.db import connection
    return id(connection)
get_db_connection.ignore_result = True


class TestJail(unittest.TestCase):

    def test_django_db_connection_is_closed(self):
        from django.db import connection
        connection._was_closed = False
        old_connection_close = connection.close

        def monkeypatched_connection_close(*args, **kwargs):
            connection._was_closed = True
            return old_connection_close(*args, **kwargs)

        connection.close = monkeypatched_connection_close
        try:
            jail(gen_unique_id(), get_db_connection.name, [2], {})
            self.assertTrue(connection._was_closed)
        finally:
            connection.close = old_connection_close

    def test_django_cache_connection_is_closed(self):
        from django.core import cache
        old_cache_close = getattr(cache.cache, "close", None)
        cache._was_closed = False
        old_cache_parse_backend = getattr(cache, "parse_backend_uri", None)
        if old_cache_parse_backend: # checks to make sure attr exists
            delattr(cache, 'parse_backend_uri')

        def monkeypatched_cache_close(*args, **kwargs):
            cache._was_closed = True


        print("C: %s" % (cache.cache, ))
        cache.cache.close = monkeypatched_cache_close
        print("X: %s" % (cache.cache.close, ))

        jail(gen_unique_id(), mytask.name, [4], {})
        self.assertTrue(cache._was_closed)
        cache.cache.close = old_cache_close
        if old_cache_parse_backend:
            cache.parse_backend_uri = old_cache_parse_backend

    def test_django_cache_connection_is_closed_django_1_1(self):
        from django.core import cache
        old_cache_close = getattr(cache.cache, "close", None)
        cache._was_closed = False
        old_cache_parse_backend = getattr(cache, "parse_backend_uri", None)
        cache.parse_backend_uri = lambda uri: ["libmemcached", "1", "2"]

        def monkeypatched_cache_close(*args, **kwargs):
            cache._was_closed = True

        cache.cache.close = monkeypatched_cache_close

        jail(gen_unique_id(), mytask.name, [4], {})
        self.assertTrue(cache._was_closed)
        cache.cache.close = old_cache_close
        if old_cache_parse_backend:
            cache.parse_backend_uri = old_cache_parse_backend
        else:
            del(cache.parse_backend_uri)