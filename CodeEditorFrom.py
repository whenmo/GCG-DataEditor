from PyQt6.QtWidgets import QWidget, QPlainTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSlot
from PyQt6.QtGui import QColor, QPainter


class LineNumberArea(QWidget):
    def __init__(self, editor, max_digits: int):
        super().__init__(editor)
        self.editor: CodeEditor = editor
        self.max_digits: int = max_digits

    def sizeHint(self):
        return QSize(self.lineNumberAreaWidth(), 0)

    def lineNumberAreaWidth(self):
        if (digits := self.max_digits) == 0:
            digits = len(str(max(1, self.editor.blockCount())))
        space = 10 + self.editor.fontMetrics().horizontalAdvance("9") * digits
        return space

    def paintEvent(self, event):
        painter = QPainter(self)
        block = self.editor.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(
            self.editor.blockBoundingGeometry(block)
            .translated(self.editor.contentOffset())
            .top()
        )
        bottom = top + int(self.editor.blockBoundingRect(block).height())
        height = self.editor.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.GlobalColor.white)  # 白色字體
                painter.drawText(
                    0,
                    top,
                    self.width() - 1,
                    height,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            blockNumber += 1

        # 畫分隔線
        painter.setPen(QColor(180, 180, 180))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


class CodeEditor(QPlainTextEdit):
    def __init__(self, default_txt: str = "", max_digits: int = 0):
        super().__init__()
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.lineNumberArea: LineNumberArea = LineNumberArea(self, max_digits)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth(0)
        font = self.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.setFont(font)

        if default_txt:
            self.setPlainText(default_txt)

    def lineNumberAreaWidth(self):
        return self.lineNumberArea.lineNumberAreaWidth()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    @pyqtSlot(int)
    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    @pyqtSlot(QRect, int)
    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0, rect.y(), self.lineNumberArea.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)
