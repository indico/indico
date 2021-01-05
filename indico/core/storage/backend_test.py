# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os
from io import BytesIO

import pytest

from indico.core.storage import (FileSystemStorage, ReadOnlyFileSystemStorage, Storage, StorageError,
                                 StorageReadOnlyError)


@pytest.fixture
def fs_storage(tmpdir):
    return FileSystemStorage(tmpdir.strpath)


@pytest.mark.parametrize('data', ('foo', 'foo=bar,', ','))
def test_parse_data_invalid(data):
    with pytest.raises(ValueError):
        Storage(None)._parse_data(data)


@pytest.mark.parametrize(('data', 'expected'), (
    ('foo=bar', {'foo': 'bar'}),
    ('foo = bar', {'foo': 'bar'}),
    ('foo = bar, hello= world   ', {'foo': 'bar', 'hello': 'world'}),
    ('test=123,test2=True', {'test': '123', 'test2': 'True'}),
))
def test_parse_data(data, expected):
    assert Storage(None)._parse_data(data) == expected


@pytest.mark.usefixtures('request_context')
def test_fs_errors(fs_storage):
    with pytest.raises(StorageError) as exc_info:
        fs_storage.open('xxx')
    assert 'Could not open' in unicode(exc_info.value)
    with pytest.raises(StorageError) as exc_info:
        fs_storage.send_file('xxx', 'unused/unused', 'unused')
    assert 'Could not send' in unicode(exc_info.value)
    with pytest.raises(StorageError) as exc_info:
        fs_storage.delete('xxx')
    assert 'Could not delete' in unicode(exc_info.value)
    with pytest.raises(StorageError) as exc_info:
        fs_storage.getsize('xxx')
    assert 'Could not get size' in unicode(exc_info.value)
    with pytest.raises(StorageError) as exc_info:
        fs_storage.open('../xxx')
    assert 'Invalid path' in unicode(exc_info.value)
    os.mkdir(fs_storage._resolve_path('secret'), 0o000)
    with pytest.raises(StorageError) as exc_info:
        fs_storage.save('secret/test.txt', 'unused/unused', 'unused', b'hello test')
    assert 'Could not save' in unicode(exc_info.value)
    os.rmdir(fs_storage._resolve_path('secret'))


def test_fs_save_bytes(fs_storage):
    f, __ = fs_storage.save('test.txt', 'unused/unused', 'unused', b'hello test')
    assert fs_storage.open(f).read() == b'hello test'


def test_fs_save_fileobj(fs_storage):
    f, __ = fs_storage.save('test.txt', 'unused/unused', 'unused', BytesIO(b'hello test'))
    assert fs_storage.open(f).read() == b'hello test'


def test_fs_overwrite(fs_storage):
    f, __ = fs_storage.save('test.txt', 'unused/unused', 'unused', b'hello test')
    with pytest.raises(StorageError) as exc_info:
        fs_storage.save('test.txt', 'unused/unused', 'unused', b'hello fail')
    assert 'already exists' in unicode(exc_info.value)
    with fs_storage.open(f) as fd:
        assert fd.read() == b'hello test'


def test_fs_dir(fs_storage):
    fs_storage.save('foo/test.txt', 'unused/unused', 'unused', b'hello test')
    # Cannot open directory
    with pytest.raises(StorageError) as exc_info:
        fs_storage.open('foo')
    assert 'Could not open' in unicode(exc_info.value)
    # Cannot create file colliding with the directory
    with pytest.raises(StorageError) as exc_info:
        fs_storage.save('foo', 'unused/unused', 'unused', b'hello test')
    assert 'Could not save' in unicode(exc_info.value)


def test_fs_operations(fs_storage):
    f1, h1 = fs_storage.save('foo/bar/test.txt', 'unused/unused', 'unused', b'hello world')
    f2, h2 = fs_storage.save('foo/bar/test2.txt', 'unused/unused', 'unused', b'hello there')
    f3, h3 = fs_storage.save('test.txt', 'unused/unused', 'unused', b'very very long file' * 1024 * 1024)

    # check md5 checksums
    assert h1 == u'5eb63bbbe01eeed093cb22bb8f5acdc3'
    assert h2 == u'161bc25962da8fed6d2f59922fb642aa'
    assert h3 == u'd35ddfd803cbe8915f5c3ecd1d0523b4'

    with fs_storage.open(f1) as fd:
        assert fd.read() == b'hello world'
    with fs_storage.open(f2) as fd:
        assert fd.read() == b'hello there'
    with fs_storage.open(f3) as fd:
        assert len(fd.read()) == 19922944
    assert fs_storage.getsize(f1) == 11
    fs_storage.delete(f1)
    # only f1 should have been deleted
    with pytest.raises(StorageError):
        fs_storage.open(f1)
    with fs_storage.open(f2) as fd:
        assert fd.read() == b'hello there'
    with fs_storage.open(f3) as fd:
        assert len(fd.read()) == 19922944


@pytest.mark.usefixtures('request_context')
def test_fs_send_file(fs_storage):
    f1, __ = fs_storage.save('foo/bar/test.txt', 'unused/unused', 'unused', b'hello world')
    response = fs_storage.send_file(f1, 'text/plain', 'filename.txt')
    assert 'text/plain' in response.headers['Content-type']
    assert 'filename.txt' in response.headers['Content-disposition']
    assert ''.join(response.response) == 'hello world'


@pytest.mark.usefixtures('request_context')
def test_fs_readonly(fs_storage):
    f, __ = fs_storage.save('test.txt', 'unused/unused', 'unused', b'hello world')
    readonly = ReadOnlyFileSystemStorage(fs_storage.path)
    assert readonly.open(f).read() == b'hello world'
    assert readonly.send_file(f, 'test/plain', 'test.txt')
    assert readonly.getsize(f) == 11
    with pytest.raises(StorageReadOnlyError):
        readonly.delete(f)
    with pytest.raises(StorageReadOnlyError):
        readonly.save('test2.txt', 'unused/unused', 'unused', b'hello fail')
    # just to make sure the file is still there
    assert readonly.open(f).read() == b'hello world'


def test_fs_get_local_path(fs_storage):
    f, __ = fs_storage.save('test.txt', 'unused/unused', 'unused', b'hello world')
    with fs_storage.get_local_path(f) as path:
        assert path == fs_storage._resolve_path(f)
        with open(path, 'rb') as fd:
            assert fd.read() == b'hello world'
    # fs storage returns the real path so it should still exist afterwards
    assert os.path.exists(path)


def test_storage_get_local_path(fs_storage):
    class CustomStorage(FileSystemStorage):
        def get_local_path(self, file_id):
            return Storage.get_local_path(self, file_id)

    storage = CustomStorage(fs_storage.path)
    f, __ = storage.save('test.txt', 'unused/unused', 'unused', b'hello world')
    with storage.get_local_path(f) as path:
        with open(path, 'rb') as fd:
            assert fd.read() == b'hello world'
    assert not os.path.exists(path)
