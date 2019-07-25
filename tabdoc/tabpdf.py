#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 19-2-11 下午6:14
"""
from collections import MutableMapping, Sequence

from path import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

__all__ = ("PDFWriter",)

pdfmetrics.registerFont(
    TTFont('simhei', Path(__file__).dirname().joinpath("templates/SimHei.ttf").abspath()))


class PDFWriter(object):
    """
    pdf book writer
    """

    def __init__(self, pdf_name, pdf_path=None, water_mark=None, title=None):
        """
            excel book writer
        Args:
            pdf_name: pdf 名称
            title: 文件title
            pdf_path: pdf path
            water_mark: pdf 水印文字
        """
        self.story = []
        self.pdf_name = f"{pdf_name}.pdf"
        self.pdf_path = pdf_path
        self.document = SimpleDocTemplate(self.get_full_name(), pagesize=letter)
        self.styles = self.get_sample_style_sheet()
        self.water_mark = water_mark
        self.alignment_map = {"left": 0, "center": 1, "right": 2, "justify": 4}
        if title:
            self.add_heading(title, alignment="center")

    @staticmethod
    def get_sample_style_sheet():
        """
            获取样式，这里会更改样式的字体，以便于支持中文
        Args:
        """

        styles = getSampleStyleSheet()
        for key, value in styles.byName.items():
            value.fontName = "simhei"
            styles.byName[key] = value
        return styles

    def get_full_name(self, ):
        """
        获取全路径文件名
        Args:

        Returns:

        """
        if self.pdf_path is None:
            full_name = self.pdf_name
        else:
            full_name = Path(self.pdf_path).joinpath(self.pdf_name).abspath()
        return full_name

    def __enter__(self):
        """

        Args:

        Returns:

        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        Args:

        Returns:

        """
        self.save()

    @staticmethod
    def _reduce_datetimes(row):
        """Receives a row, converts datetimes to strings."""

        row = list(row)

        for i, val in enumerate(row):
            if hasattr(val, "strftime"):
                row[i] = val.strftime("%Y-%m-%d %H:%M:%S")
            elif hasattr(val, 'isoformat'):
                row[i] = val.isoformat()
        return tuple(row)

    def add_heading(self, head_text: str = None, *, level: int = 1, alignment="left"):
        """
        为PDF文档中添加标题
        Args:
            head_text: 标题的内容
            level: 标题的级别， 共一到六级别
            alignment: 标题的对其方式,left,center,right,justify
        Returns:

        """
        if alignment not in self.alignment_map:
            raise ValueError("alignment必须是left,center,right,justify")
        if level < 1 or level > 6:
            raise ValueError("level必须在1和6之间。")
        styles = self.styles.get(f'Heading{level}')
        styles.alignment = self.alignment_map[alignment]
        self.story.append(Paragraph(head_text, styles))
        self.story.append(Spacer(1, 0.25 * inch))

    def add_paragraph(self, paragraph_text, alignment="left"):
        """
        PDF文档中添加段落
        Args:
            paragraph_text: 段落内容
            alignment: 标题的对其方式,left,center,right,justify
        Returns:

        """

        if alignment not in self.alignment_map:
            raise ValueError("alignment必须是left,center,right,justify")
        styles = self.styles.get('Normal')
        styles.alignment = self.alignment_map[alignment]
        self.story.append(Paragraph(paragraph_text, styles))
        self.story.append(Spacer(1, 0.15 * inch))

    def add_table(self, table_data: list, table_name=None, data_align='CENTER', table_halign='CENTER'):
        """
        为pdf添加表格数据
        Args:
            table_name: 表格的名称
            table_data: 表格的数据， 必须是列表中嵌套元祖、列表或者字典（从records查询出来的数据库的数据）
            data_align: The alignment of the data inside the table (eg.
                'LEFT', 'CENTER', 'RIGHT')
            table_halign: Horizontal alignment of the table on the page
                (eg. 'LEFT', 'CENTER', 'RIGHT')

        Returns:

        """

        if table_name:
            styles = self.styles.get('Heading4')
            styles.alignment = self.alignment_map.get(table_halign.lower(), "center")
            self.story.append(Paragraph(table_name, styles))
            self.story.append(Spacer(1, 0.15 * inch))

        for row in table_data:
            if not isinstance(row, (MutableMapping, Sequence)):
                raise ValueError("table_data值数据类型错误,请检查")

        # 处理list或者tuple个别长度不一致的情况
        first = table_data[0]
        if isinstance(first, Sequence):
            for index, row in enumerate(table_data[1:], 1):
                diff = len(row) - len(first)
                if abs(diff) > 0:
                    if isinstance(row, list):
                        row.extend(["" for _ in range(diff)])
                    else:
                        table_data[index] = (*row, *["" for _ in range(diff)])
                table_data[index] = self._reduce_datetimes(row)

        else:
            for index, row in enumerate(table_data[1:], 1):
                diff = len(row) - len(first)
                if abs(diff) > 0:
                    row_ = [*list(row.values()), *["" for _ in range(diff)]]
                    table_data[index] = self._reduce_datetimes(row_)
                else:
                    table_data[index] = self._reduce_datetimes(row.values())

        table = Table(table_data, hAlign=table_halign)
        # (列,行) (0, 0)(-1, -1)代表0列0行到所有的单元格
        table.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'simhei'),  # 所有单元格设置雅黑字体
                                   ('ALIGN', (0, 0), (-1, 0), 'LEFT'),  # 第一列左对齐
                                   ('ALIGN', (0, 0), (0, 0), data_align),  # 第一个单元格
                                   ('ALIGN', (1, 0), (-1, -1), data_align),  # 第一列到剩下的所有数据
                                   ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.black),
                                   ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))

        self.story.append(table)

    def save(self, ):
        """
        保存PDF
        Args:
        Returns:

        """
        self.document.build(self.story)


if __name__ == '__main__':
    with PDFWriter("test", title="hahha") as pdf:
        pdf.add_heading("第一个标题", level=3)
        pdf.add_paragraph("这是一个测试文档")
        pdf.add_table([["很大", "很大", "很大", "很大fdsfa"],
                       ["很大1fdsafd", "很大", "很大", "很大"],
                       ["很大", "很大fdsfd", "很大", "很大"]],
                      table_name="test")
