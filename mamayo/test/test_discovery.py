from mamayo.test import fakefile as ff
from mamayo.discovery import Explorer

def basic_mamayo_app_directory():
    "The most basic mamayo app discoverable is an empty directory with mamayo.conf."
    return ff.Directory({'mamayo.conf': ff.File('')})

def test_root_as_application():
    "The document root is a possible place for a mamayo app."
    root = basic_mamayo_app_directory()
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {root}

def test_basic_application():
    "A mamayo app can be one directory in the document root."
    app = basic_mamayo_app_directory()
    root = ff.Directory(dict(app=app))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app}

def test_nested_application():
    "A mamayo app can be one directory nested deeply in the document root."
    app = basic_mamayo_app_directory()
    eggs = ff.Directory(dict(app=app))
    spam = ff.Directory(dict(eggs=eggs))
    root = ff.Directory(dict(spam=spam))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app}

def test_basic_applications():
    "Multiple mamayo apps can live in the same directory."
    app1 = basic_mamayo_app_directory()
    app2 = basic_mamayo_app_directory()
    app3 = basic_mamayo_app_directory()
    root = ff.Directory(dict(foo=app1, bar=app2, baz=app3))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app1, app2, app3}

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

def test_nested_applications():
    "App directories can be contained in other app directories."
    app1 = basic_mamayo_app_directory()
    app2 = basic_mamayo_app_directory()
    app1.contents['bar'] = app2
    app3 = basic_mamayo_app_directory()
    app2.contents['baz'] = app3
    root = ff.Directory(dict(foo=app1))
    e = Explorer(root)
    e.explore()
    assert {app.path for app in e.applications} == {app1, app2, app3}
