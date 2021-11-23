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
    values = (("finduri1","replaceuri1"),("finduri2","replaceuri2"),("finduri3","replaceuri3"))
    assert _line_replace(line ,values)
    values = (("finduri1","replaceuri1"),("finduri2","replaceuri2"))
    assert _line_replace(line ,values)
    values = (("finduri1","replaceuri1"))
    assert _line_replace(line ,values)
    

def test_chardet():
    TurtleTestFile = _test_cases_dir_urireplace / "TurtleTestFile.ttl"
    assert _chardet(TurtleTestFile) == 'ascii'
    CP437file = _test_cases_dir_urireplace / "CP437.txt"
    #assert _chardet(CP437file) == 'cp437'
    CP1252file = _test_cases_dir_urireplace / "CP1252.txt"
    #assert _chardet(CP1252file) == 'Windows-1252'
    UTF_8file = _test_cases_dir_urireplace / "UTF-8.txt"
    assert _chardet(UTF_8file) == 'utf-8'


if __name__ == "__main__":
    pytest.main()
