import os
import pytest

from pymdtools.common import path_depth


def test_path_depth_absolute_dir():
    assert path_depth("/a/b/c") == 3


def test_path_depth_absolute_file():
    assert path_depth("/a/b/c/file.txt") == 3


def test_path_depth_relative_path():
    assert path_depth("a/b/c") == 3


def test_path_depth_single_level():
    assert path_depth("a") == 1


def test_path_depth_current_dir():
    assert path_depth(".") == 0


def test_path_depth_root():
    # platform-dependent, but root has depth 0
    assert path_depth(os.path.abspath(os.sep)) == 0

