import pytest
from csvcubeddevtools.helpers.file import get_test_cases_dir
from csvcubedpmd.urireplacement.urireplacement import _file_in_line
from csvcubedpmd.urireplacement.urireplacement import _line_replace
from csvcubedpmd.urireplacement.urireplacement import _chardet
_test_cases_dir_urireplace = get_test_cases_dir()


def test_file_in_line():
    assert _file_in_line("http://uri.org/example file://temp/example.csv")
    assert not _file_in_line("http://wwe.com/")


def test_line_replace():
    line = "example line from a ttl file"
    values = (("finduri1","replaceuri1"))
    assert _line_replace(line ,values)
    values = (("finduri1","replaceuri1"),("finduri2","replaceuri2"),("finduri3","replaceuri3"))
    assert _line_replace(line ,values)


def test_chardet():
    assert _chardet("/workspaces/csvwlib/csvcubed-pmd/tests/TurtleTestFile.ttl")


if __name__ == "__main__":
    pytest.main()
