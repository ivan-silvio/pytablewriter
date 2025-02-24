import copy
from enum import Enum, unique
from typing import Any, Final, Union

import dataproperty as dp
import typepy
from dataproperty import ColumnDataProperty, DataProperty
from mbstrdecoder import MultiByteStrDecoder
from pathvalidate import replace_symbol

from ..._function import normalize_enum
from ...error import EmptyTableDataError
from ...style import Align, GFMarkdownStyler, MarkdownStyler, StylerInterface
from .._table_writer import AbstractTableWriter
from ._text_writer import IndentationTextTableWriter


@unique
class MarkdownFlavor(Enum):
    COMMON_MARK = "common_mark"
    GITHUB = "github"
    GFM = "gfm"
    JEKYLL = "jekyll"
    KRAMDOWN = "kramdown"


def normalize_md_flavor(flavor: Union[str, MarkdownFlavor, None]) -> MarkdownFlavor:
    if isinstance(flavor, str):
        flavor_str = replace_symbol(flavor.strip(), "_").upper()
        flavor_str = flavor_str.replace("COMMONMARK", "COMMON_MARK")
        flavor = flavor_str

    norm_flavor = normalize_enum(flavor, MarkdownFlavor, default=MarkdownFlavor.COMMON_MARK)

    if norm_flavor == MarkdownFlavor.GITHUB:
        return MarkdownFlavor.GFM

    if norm_flavor == MarkdownFlavor.JEKYLL:
        return MarkdownFlavor.KRAMDOWN

    return norm_flavor


class MarkdownTableWriter(IndentationTextTableWriter):
    """
    A table writer class for Markdown format.

    Example:
        :ref:`example-markdown-table-writer`
    """

    FORMAT_NAME = "markdown"
    DEFAULT_FLAVOR: Final = MarkdownFlavor.COMMON_MARK

    @property
    def format_name(self) -> str:
        return self.FORMAT_NAME

    @property
    def support_split_write(self) -> bool:
        return True

    def __init__(self, **kwargs: Any) -> None:
        self.__flavor = normalize_md_flavor(kwargs.pop("flavor", self.DEFAULT_FLAVOR))

        super().__init__(**kwargs)

        self.indent_string = ""
        self.column_delimiter = "|"
        self.char_left_side_row = "|"
        self.char_right_side_row = "|"
        self.char_cross_point = "|"
        self.char_header_row_cross_point = "|"
        self.char_header_row_left_cross_point = "|"
        self.char_header_row_right_cross_point = "|"

        self.is_write_opening_row = True
        self._use_default_header = True

        self._is_require_header = True
        self._quoting_flags = copy.deepcopy(dp.NOT_QUOTING_FLAGS)
        self._dp_extractor.min_column_width = 3

        self._init_cross_point_maps()

    def _to_header_item(self, col_dp: ColumnDataProperty, value_dp: DataProperty) -> str:
        return self.__escape_vertical_bar_char(super()._to_header_item(col_dp, value_dp))

    def _to_row_item(self, row_idx: int, col_dp: ColumnDataProperty, value_dp: DataProperty) -> str:
        return self.__escape_vertical_bar_char(super()._to_row_item(row_idx, col_dp, value_dp))

    def _get_opening_row_items(self) -> list[str]:
        return []

    def _get_header_row_separator_items(self) -> list[str]:
        header_separator_list = []
        margin = " " * self.margin

        for col_dp in self._column_dp_list:
            padding_len = self._get_padding_len(col_dp)
            align = self._get_align(col_dp.column_index, col_dp.align)

            if align == Align.RIGHT:
                separator_item = "-" * (padding_len - 1) + ":"
            elif align == Align.CENTER:
                separator_item = ":" + "-" * (padding_len - 2) + ":"
            else:
                separator_item = "-" * padding_len

            header_separator_list.append(
                "{margin}{item}{margin}".format(margin=margin, item=separator_item)
            )

        return header_separator_list

    def _get_value_row_separator_items(self) -> list[str]:
        return []

    def _get_closing_row_items(self) -> list[str]:
        return []

    def _write_header(self) -> None:
        super()._write_header()

        if self.__flavor == MarkdownFlavor.KRAMDOWN:
            self._write_line()

    def write_table(self, **kwargs: Any) -> None:
        """
        |write_table| with Markdown table format.

        Args:
            flavor (Optional[str]):
                possible flavors are as follows (case insensitive):

                    - ``"CommonMark"``
                    - ``"gfm"``
                    - ``"github"`` (alias of ``"gfm"``)
                    - ``kramdown``
                    - ``Jekyll`` (alias of ``"kramdown"``)

                Defaults to ``"CommonMark"``.

        Example:
            :ref:`example-markdown-table-writer`

        .. note::
            - |None| values are written as an empty string
            - Vertical bar characters (``'|'``) in table items are escaped
        """

        if "flavor" in kwargs:
            new_flavor = normalize_md_flavor(kwargs["flavor"])
            if new_flavor != self.__flavor:
                self._clear_preprocess()
                self.__flavor = new_flavor

        if self.__flavor:
            self._styler = self._create_styler(self)

        with self._logger:
            try:
                self._verify_property()
            except EmptyTableDataError:
                self._logger.logger.debug("no tabular data found")
                return

            self.__write_chapter()
            self._write_table(**kwargs)
            if self.is_write_null_line_after_table:
                self.write_null_line()

    def _write_table_iter(self, **kwargs: Any) -> None:
        self.__write_chapter()
        super()._write_table_iter()

    def __write_chapter(self) -> None:
        if typepy.is_null_string(self.table_name):
            return

        self._write_line(
            "{:s} {:s}".format(
                "#" * (self._indent_level + 1), MultiByteStrDecoder(self.table_name).unicode_str
            )
        )

        if self.__flavor == MarkdownFlavor.KRAMDOWN:
            self._write_line()

    def _create_styler(self, writer: AbstractTableWriter) -> StylerInterface:
        if self.__flavor == MarkdownFlavor.GFM:
            return GFMarkdownStyler(writer)

        return MarkdownStyler(writer)

    @staticmethod
    def __escape_vertical_bar_char(value: str) -> str:
        return value.replace("|", r"\|")
