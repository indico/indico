from indico.core.models.settings import Setting


def test_settings(db):
    Setting.set('test', 'foo', 'bar')
    db.session.flush()
    assert Setting.get('test', 'foo') == 'bar'


def test_settings2(db):
    assert Setting.get('test', 'foo') is None


def test_settings3(db):
    data = {'a': 123, 'b': 'xyz'}
    Setting.set_multi('test', data)
    db.session.commit()  # automatically converted to a flush
    assert Setting.get_all('test') == data


def test_settings4(db):
    assert Setting.get('test', 'foo') is None
