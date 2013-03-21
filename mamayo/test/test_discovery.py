from mamayo.test import fakefile as ff
from mamayo.discovery import Explorer
from mamayo.errors import NoSuchApplicationError

import pytest

def basic_mamayo_app_directory():
    "The most basic mamayo app discoverable is an empty directory with mamayo.conf."
    return ff.Directory({'application.wsgi': ff.File('')})

def test_root_as_application():
    "The document root is a possible place for a mamayo app."
    root = basic_mamayo_app_directory()
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {root}
    assert e.application_from_segments([]).path == root

def test_basic_application():
    "A mamayo app can be one directory in the document root."
    app = basic_mamayo_app_directory()
    root = ff.Directory(dict(app=app))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app}
    assert e.application_from_segments(['app']).path == app

def test_nested_application():
    "A mamayo app can be one directory nested deeply in the document root."
    app = basic_mamayo_app_directory()
    eggs = ff.Directory(dict(app=app))
    spam = ff.Directory(dict(eggs=eggs))
    root = ff.Directory(dict(spam=spam))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app}
    assert e.application_from_segments(['spam', 'eggs', 'app']).path == app

def test_basic_applications():
    "Multiple mamayo apps can live in the same directory."
    app1 = basic_mamayo_app_directory()
    app2 = basic_mamayo_app_directory()
    app3 = basic_mamayo_app_directory()
    root = ff.Directory(dict(foo=app1, bar=app2, baz=app3))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app1, app2, app3}
    assert e.application_from_segments(['foo']).path == app1
    assert e.application_from_segments(['bar']).path == app2
    assert e.application_from_segments(['baz']).path == app3

def test_basic_applications_with_cruft():
    "The presence of other files and directories doesn't hinder app discovery."
    app1 = basic_mamayo_app_directory()
    app2 = basic_mamayo_app_directory()
    app2.contents['cruft'] = ff.Directory(dict(spam=ff.File(''), eggs=ff.File('')))
    app3 = basic_mamayo_app_directory()
    app3.contents['cruft'] = ff.File('')
    root = ff.Directory(dict(foo=app1, bar=app2, baz=app3))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app1, app2, app3}
    assert e.application_from_segments(['foo']).path == app1
    assert e.application_from_segments(['bar']).path == app2
    assert e.application_from_segments(['baz']).path == app3

def test_nested_applications_fails():
    "App directories can _not_ be contained in other app directories."
    app1 = basic_mamayo_app_directory()
    app2 = basic_mamayo_app_directory()
    app1.contents['bar'] = app2
    app3 = basic_mamayo_app_directory()
    app2.contents['baz'] = app3
    root = ff.Directory(dict(foo=app1))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app1}
    assert e.application_from_segments(['foo']).path == app1
    assert e.application_from_segments(['foo', 'bar']).path == app1
    assert e.application_from_segments(['foo', 'bar', 'baz']).path == app1

def test_fetching_nonextant_applications():
    "application_from_segments raises NoSuchApplicationError on failure."
    app = basic_mamayo_app_directory()
    root = ff.Directory(dict(app=app))
    e = Explorer(root)
    e.explore()
    with pytest.raises(NoSuchApplicationError):
        e.application_from_segments([])
    with pytest.raises(NoSuchApplicationError):
        e.application_from_segments(['not-app'])

def test_providing_extra_segments():
    "application_from_segments allows extra segments after the application."
    app = basic_mamayo_app_directory()
    root = ff.Directory(dict(app=app))
    e = Explorer(root)
    e.explore()
    assert e.application_from_segments(['app', 'more']).path == app
    assert e.application_from_segments(['app', 'more', 'stuff']).path == app
