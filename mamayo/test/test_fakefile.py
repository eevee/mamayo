from mamayo.test import fakefile as ff

import pytest

def test_basic_segmentsFrom():
    f = ff.File('')
    d = ff.Directory(dict(f=f))
    assert f.segmentsFrom(d) == ['f']

def test_nested_segmentsFrom():
    f = ff.File('')
    d1 = ff.Directory(dict(f=f))
    d2 = ff.Directory(dict(spam=d1))
    assert f.segmentsFrom(d2) == ['spam', 'f']

def test_multiple_nesting_levels_in_segmentsFrom():
    f = ff.File('')
    d1 = ff.Directory(dict(f=f))
    d2 = ff.Directory(dict(spam=d1))
    d3 = ff.Directory(dict(eggs=d2))
    assert f.segmentsFrom(d2) == ['spam', 'f']
    assert f.segmentsFrom(d3) == ['eggs', 'spam', 'f']
    assert d1.segmentsFrom(d3) == ['eggs', 'spam']

def test_non_ancestors_raise_in_segmentsFrom():
    f1 = ff.File('')
    d1 = ff.Directory(dict(f=f1))
    f2 = ff.File('')
    d2 = ff.Directory(dict(f=f2))
    with pytest.raises(ValueError):
        f2.segmentsFrom(d1)
    with pytest.raises(ValueError):
        f1.segmentsFrom(d2)
