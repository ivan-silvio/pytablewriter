from textwrap import dedent

import pytest

from pytablewriter import BorderlessTableWriter

from ..._common import print_test_result
from ...data import style_tabledata, styles


class Test_BorderlessTableWriter_write_new_line:
    @pytest.mark.parametrize(["table_writer_class"], [[BorderlessTableWriter]])
    def test_normal(self, capsys, table_writer_class):
        writer = table_writer_class()
        writer.write_null_line()

        out, _err = capsys.readouterr()
        assert out == "\n"


class Test_BorderlessTableWriter_write_table:
    def test_normal_styles(self, capsys):
        writer = BorderlessTableWriter()
        writer.from_tabledata(style_tabledata)
        writer.column_styles = styles
        writer.write_table()

        expected = dedent(
            """\
            noneemptytinysmallmediumlargenull w/ boldL boldS italicL bold italic
             111  111 111  111   111  111               111     111          111
            1234 12341234 1234 1,2341 234              1234    1234         1234
            """
        )

        out = writer.dumps()
        print_test_result(expected=expected, actual=out)
        assert out == expected
