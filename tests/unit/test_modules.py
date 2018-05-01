import sys
import os

import sequel
from sequel import sequence
from sequel.utils import lcm
from sequel.modules import make_ref, load_ref

import pytest


@pytest.mark.parametrize("obj, ref", [
    (sys, 'sys'),
    (sequence, 'sequel.sequence'),
    (lcm, 'sequel.utils:lcm')])
def test_make_ref(obj, ref):
    assert make_ref(obj) == ref


@pytest.mark.parametrize("ref, obj", [
    ('sys', sys),
    ('sys:path', sys.path),
    ('os.path', os.path),
    ('os.path:abspath', os.path.abspath),
    ('sequel.sequence', sequence),
    ('sequel.utils:lcm', lcm),
    (os.path.dirname(sequel.__file__) + '/sequel.utils:lcm', lcm),
])
def test_load_ref(ref, obj):
    assert load_ref(ref) is obj
