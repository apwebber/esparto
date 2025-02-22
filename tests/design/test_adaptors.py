from inspect import getmembers, isfunction, signature
from pathlib import Path, PosixPath

import pytest

import esparto.design.adaptors as ad
from esparto.design.content import Content, Markdown
from esparto.design.layout import Column
from tests.conftest import _EXTRAS, adaptor_list


def get_dispatch_type(fn):
    sig = signature(fn)
    if "content" in sig.parameters:
        return sig.parameters["content"].annotation


def test_all_adaptors_covered(adaptor_list_fn):
    test_classes = {type(item[0]) for item in adaptor_list_fn}
    module_functions = [x[1] for x in getmembers(ad, isfunction)]
    adaptor_types = {get_dispatch_type(fn) for fn in module_functions}
    adaptor_types.remove(Content)  # Can't use abstract base class in a test
    if _EXTRAS:
        adaptor_types.remove(ad.BokehObject)  # Can't use abstract base class in a test
    if PosixPath in test_classes:
        test_classes.remove(PosixPath)
        test_classes = adaptor_types | {Path}
    if None in adaptor_types:
        adaptor_types.remove(None)
    missing = adaptor_types.difference(test_classes)
    assert not missing, missing


@pytest.mark.parametrize("input_,expected", adaptor_list)
def test_adaptor_text(input_, expected):
    output = ad.content_adaptor(input_)
    assert isinstance(output, expected)


def test_adaptor_layout():
    input_col = Column(title="title", children=["a", "b"])
    output_col = ad.content_adaptor(input_col)
    assert input_col == output_col


def test_adapator_textfile(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.exe"
    CONTENT = "# This is some Markdown content"
    p.write_text(CONTENT)
    with pytest.raises(TypeError):
        ad.content_adaptor(Path(p))


def test_adapator_bad_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    CONTENT = "# This is some Markdown content"
    p.write_text(CONTENT)
    assert ad.content_adaptor(Path(p)) == Markdown(CONTENT)
    assert ad.content_adaptor(str(p)) == Markdown(CONTENT)


def test_incorrect_content_rejected():
    class FakeClass:
        def __call__(self):
            return "I'm not supported"

    fake = FakeClass()

    with pytest.raises(TypeError):
        ad.content_adaptor(fake)


def test_adaptor_dict_bad():
    bad_dict = {"key1": "val1", "key2": "val2"}
    with pytest.raises(ValueError):
        ad.content_adaptor(bad_dict)
