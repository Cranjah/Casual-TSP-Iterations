#!/usr/bin/env python3


### PyQt6 application for simulating elastic circles / ellipses with a suction point & anchor points ###

### Requirements: pip install PyQt6 ###

### Created and vibecoded completely with Microsoft Copilot via:  https://copilot.microsoft.com/ ###


from __future__ import annotations
import math
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, QSizeF

from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QTransform, QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
    QToolBar,
    QFileDialog,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtGui import QAction
from PyQt6.QtSvg import QSvgGenerator
from PyQt6.QtGui import QPainterPath


# ---- Constants (UI colors and dimensions) ----
SCENE_SIZE = 1000
BACKGROUND_COLOR = QColor("#FFFFFF")
AXIS_COLOR = QColor("#333333")
FIXED_POINT_COLOR = QColor("#000000")
SUCTION_COLOR = QColor("#FFFF00")
ELASTIC_STROKE_COLOR = QColor("#FF0000")
ELASTIC_STROKE_WIDTH = 3

# ---- Physics defaults ----
DEFAULT_NODE_COUNT = 256
SPRING_K = 20.0
SHEAR_K = 5.0
DAMPING = 0.02
MASS = 2.0
SUCTION_STRENGTH = 5e4
EPS = 1e-6


# ---- Tool modes ----
class ToolMode:
    SELECT = "select"
    ADD_FIXED_POINT = "add_fixed_point"
    DRAW_CIRCLE = "draw_circle"
    DRAW_ELLIPSE = "draw_ellipse"
    SET_SUCTION = "set_suction"


# ---- Utility functions ----
def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def to_scene_point(view: QGraphicsView, pos) -> QPointF:
    return view.mapToScene(pos)


# ---- Graphics helpers ----
class CrossItem(QGraphicsItem):
    def __init__(
        self, center: QPointF, size: float = 10.0, color: QColor = FIXED_POINT_COLOR
    ):
        super().__init__()
        self.center = center
        self.size = size
        self.pen = QPen(color, 2)
        self.setZValue(10)

    def boundingRect(self) -> QRectF:
        s = self.size
        return QRectF(self.center.x() - s, self.center.y() - s, 2 * s, 2 * s)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(self.pen)
        cx, cy = self.center.x(), self.center.y()
        s = self.size
        painter.drawLine(QPointF(cx - s, cy - s), QPointF(cx + s, cy + s))
        painter.drawLine(QPointF(cx - s, cy + s), QPointF(cx + s, cy - s))


class SuctionItem(QGraphicsEllipseItem):
    def __init__(self, center: QPointF, radius: float = 6.0, parent_view=None):
        super().__init__(
            center.x() - radius, center.y() - radius, radius * 2, radius * 2
        )
        self.setBrush(QBrush(QColor("#FFFF00")))
        self.setPen(QPen(QColor("#888888"), 0.5))
        self.setZValue(12)
        self.parent_view = parent_view

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.parent_view and self.parent_view.elastic_body:
                self.parent_view.elastic_body.set_suction(self.pos())
        return super().itemChange(change, value)


class AxesItem(QGraphicsItem):
    def __init__(self, size: int = SCENE_SIZE, tick_step: int = 100):
        super().__init__()
        self.size = size
        self.tick_step = tick_step
        self.axis_pen = QPen(AXIS_COLOR, 1)
        self.tick_pen = QPen(AXIS_COLOR, 1)
        self.font = QFont("Arial", 9)
        self.setZValue(0)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.size, self.size)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(self.axis_pen)
        painter.setFont(self.font)
        w = self.size
        h = self.size
        cx = w / 2
        cy = h / 2

        # Draw axes
        painter.drawLine(QPointF(0, cy), QPointF(w, cy))  # X-axis
        painter.drawLine(QPointF(cx, 0), QPointF(cx, h))  # Y-axis

        # Arrowheads
        painter.drawLine(QPointF(w - 10, cy - 5), QPointF(w, cy))
        painter.drawLine(QPointF(w - 10, cy + 5), QPointF(w, cy))
        painter.drawLine(QPointF(cx - 5, 10), QPointF(cx, 0))
        painter.drawLine(QPointF(cx + 5, 10), QPointF(cx, 0))

        # Labels
        painter.drawText(QPointF(w - 20, cy - 10), "X")
        painter.drawText(QPointF(cx + 10, 15), "Y")
        painter.drawText(QPointF(cx + 5, cy - 5), "(0,0)")

        # Ticks
        painter.setPen(self.tick_pen)
        for x in range(0, w + 1, self.tick_step):
            painter.drawLine(QPointF(x, cy - 5), QPointF(x, cy + 5))
            if x != cx:
                painter.drawText(QPointF(x + 2, cy + 14), f"{x - cx:.0f}")
        for y in range(0, h + 1, self.tick_step):
            painter.drawLine(QPointF(cx - 5, y), QPointF(cx + 5, y))
            if y != cy:
                painter.drawText(QPointF(cx + 8, y - 4), f"{cy - y:.0f}")


# ---- Elastic body model ----
@dataclass
class Node:
    p: QPointF
    v: QPointF


class ElasticBody(QGraphicsPathItem):
    def __init__(self, rect: QRectF, node_count: int = DEFAULT_NODE_COUNT):
        super().__init__()
        self.rect = rect.normalized()
        self.node_count = node_count
        self.nodes: List[Node] = []
        self.mass = MASS
        self.k = SPRING_K
        self.k_shear = SHEAR_K
        self.damping = DAMPING
        self.suction_strength = SUCTION_STRENGTH
        self.suction_point: Optional[QPointF] = None

        # Appearance
        self.setPen(QPen(ELASTIC_STROKE_COLOR, ELASTIC_STROKE_WIDTH))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setZValue(8)

        # Build nodes along ellipse perimeter
        self._initialize_nodes()
        self._update_path()

    def _initialize_nodes(self):
        cx = self.rect.center().x()
        cy = self.rect.center().y()
        rx = self.rect.width() / 2.0
        ry = self.rect.height() / 2.0

        self.nodes.clear()
        for i in range(self.node_count):
            t = 2.0 * math.pi * (i / self.node_count)
            x = cx + rx * math.cos(t)
            y = cy + ry * math.sin(t)
            self.nodes.append(Node(p=QPointF(x, y), v=QPointF(0.0, 0.0)))

    def set_suction(self, pt: QPointF):
        self.suction_point = pt

    def clear_suction(self):
        self.suction_point = None

    def step(self, dt: float, fixed_points: List[QPointF] = []):
        if fixed_points:
            for fp in fixed_points:
                for node in self.nodes:
                    if dist(node.p, fp) < 12.0:
                        node.p = QPointF(fp.x(), fp.y())
                        node.v = QPointF(0.0, 0.0)
                        break

        if not self.nodes:
            return

        forces: List[QPointF] = [QPointF(0.0, 0.0) for _ in self.nodes]

        # Spring forces (neighbors on ring)
        n = len(self.nodes)
        for i in range(n):
            i_prev = (i - 1) % n
            i_next = (i + 1) % n
            pi = self.nodes[i].p
            pprev = self.nodes[i_prev].p
            pnext = self.nodes[i_next].p

        # To store fixed rest lengths, precompute once:
        if not hasattr(self, "_rest_lengths"):
            self._rest_lengths = []
            for i in range(n):
                i_next = (i + 1) % n
                d = dist(self.nodes[i].p, self.nodes[i_next].p)
                self._rest_lengths.append(d)

        # Now calculate spring forces using fixed rest length
        for i in range(n):
            i_next = (i + 1) % n
            pi = self.nodes[i].p
            pj = self.nodes[i_next].p
            rl = self._rest_lengths[i]
            dx = pj.x() - pi.x()
            dy = pj.y() - pi.y()
            L = math.sqrt(dx * dx + dy * dy) + EPS
            ux = dx / L
            uy = dy / L
            fmag = self.k * (L - rl)
            fi = QPointF(fmag * ux, fmag * uy)
            forces[i] = QPointF(forces[i].x() + fi.x(), forces[i].y() + fi.y())
            forces[i_next] = QPointF(
                forces[i_next].x() - fi.x(), forces[i_next].y() - fi.y()
            )

        # Shear springs: second neighbors
        for i in range(n):
            i2 = (i + 2) % n
            pi = self.nodes[i].p
            pj = self.nodes[i2].p
            dx = pj.x() - pi.x()
            dy = pj.y() - pi.y()
            L = math.sqrt(dx * dx + dy * dy) + EPS
            ux = dx / L
            uy = dy / L
            # Rest length for two-step segment from init
            if not hasattr(self, "_rest_lengths2"):
                self._rest_lengths2 = []
                for k in range(n):
                    k2 = (k + 2) % n
                    d2 = dist(self.nodes[k].p, self.nodes[k2].p)
                    self._rest_lengths2.append(d2)
            rl2 = self._rest_lengths2[i]
            fmag = self.k_shear * (L - rl2)
            fi = QPointF(fmag * ux, fmag * uy)
            forces[i] = QPointF(forces[i].x() + fi.x(), forces[i].y() + fi.y())
            forces[i2] = QPointF(forces[i2].x() - fi.x(), forces[i2].y() - fi.y())

        # Suction force: attraction toward suction point
        if self.suction_point is not None:
            sx = self.suction_point.x()
            sy = self.suction_point.y()
            for i in range(n):
                pi = self.nodes[i].p
                dx = sx - pi.x()
                dy = sy - pi.y()
                L = math.sqrt(dx * dx + dy * dy) + EPS
                ux = dx / L
                uy = dy / L
                # Inverse-square like pull (attenuated), scaled
                fmag = self.suction_strength / L
                fi = QPointF(fmag * ux, fmag * uy)
                forces[i] = QPointF(forces[i].x() + fi.x(), forces[i].y() + fi.y())

        # Integrate with damping
        for i in range(n):
            a = QPointF(forces[i].x() / self.mass, forces[i].y() / self.mass)
            vi = self.nodes[i].v
            vi = QPointF(
                (vi.x() + a.x() * dt) * (1.0 - self.damping),
                (vi.y() + a.y() * dt) * (1.0 - self.damping),
            )
            pi = self.nodes[i].p
            pi = QPointF(pi.x() + vi.x() * dt, pi.y() + vi.y() * dt)
            self.nodes[i].v = vi
            self.nodes[i].p = pi

        self._update_path()

    def _update_path(self):
        path = QPainterPath()
        if not self.nodes:
            self.setPath(path)
            return
        path.moveTo(self.nodes[0].p)
        for i in range(1, len(self.nodes)):
            path.lineTo(self.nodes[i].p)
        path.closeSubpath()
        self.setPath(path)

    def stretch_to_points(self, fixed_points: List[QPointF]):
        if not fixed_points:
            return

        cx = SCENE_SIZE / 2
        cy = SCENE_SIZE / 2

        def angle(fp: QPointF):
            dx = fp.x() - cx
            dy = fp.y() - cy
            return math.atan2(dy, dx)

        sorted_points = sorted(fixed_points, key=angle)

        path = QPainterPath()
        path.moveTo(sorted_points[0])
        for fp in sorted_points[1:]:
            path.lineTo(fp)
        path.closeSubpath()

        self.setPath(path)


def dist(a: QPointF, b: QPointF) -> float:
    dx = b.x() - a.x()
    dy = b.y() - a.y()
    return math.sqrt(dx * dx + dy * dy)


# ---- Main view and scene controller ----
class CanvasView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.scene = QGraphicsScene(0, 0, SCENE_SIZE, SCENE_SIZE, self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(BACKGROUND_COLOR))
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        # Center the view on scene center; disable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Axes
        self.axes = AxesItem(size=SCENE_SIZE, tick_step=100)
        self.scene.addItem(self.axes)

        # Items
        self.fixed_points: List[CrossItem] = []
        self.elastic_body: Optional[ElasticBody] = None
        self.suction_item: Optional[SuctionItem] = None

        # Tool and drawing state
        self.tool_mode = ToolMode.SELECT
        self.drag_start_scene: Optional[QPointF] = None
        self.drag_rect_preview: Optional[QGraphicsPathItem] = None

    def set_tool_mode(self, mode: str):
        self.tool_mode = mode
        self._clear_preview()

    def mousePressEvent(self, event):
        pos_scene = to_scene_point(self, event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton:
            if self.tool_mode == ToolMode.ADD_FIXED_POINT:
                self.add_fixed_point(pos_scene)
            elif self.tool_mode in (ToolMode.DRAW_CIRCLE, ToolMode.DRAW_ELLIPSE):
                self.drag_start_scene = pos_scene
                self._start_preview(pos_scene)
            elif self.tool_mode == ToolMode.SET_SUCTION:
                self.set_suction_point(pos_scene)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos_scene = to_scene_point(self, event.position().toPoint())
        if self.drag_start_scene and self.tool_mode in (
            ToolMode.DRAW_CIRCLE,
            ToolMode.DRAW_ELLIPSE,
        ):
            rect = QRectF(self.drag_start_scene, pos_scene).normalized()
            if self.tool_mode == ToolMode.DRAW_CIRCLE:
                s = min(rect.width(), rect.height())
                rect = QRectF(rect.topLeft(), QSizeF(s, s))
            self._update_preview(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        pos_scene = to_scene_point(self, event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and self.drag_start_scene:
            if self.tool_mode in (ToolMode.DRAW_CIRCLE, ToolMode.DRAW_ELLIPSE):
                rect = QRectF(self.drag_start_scene, pos_scene).normalized()
                if self.tool_mode == ToolMode.DRAW_CIRCLE:
                    s = min(rect.width(), rect.height())
                    rect = QRectF(rect.topLeft(), QSizeF(s, s))
                self.add_elastic_body(rect)
            self.drag_start_scene = None
            self._clear_preview()
        super().mouseReleaseEvent(event)

    def add_fixed_point(self, p: QPointF):
        cross = CrossItem(center=p, size=8.0, color=FIXED_POINT_COLOR)
        self.fixed_points.append(cross)
        self.scene.addItem(cross)

    def add_fixed_point_coords(self, x: float, y: float):
        self.add_fixed_point(QPointF(x, y))

    def add_elastic_body(self, rect: QRectF):
        if self.elastic_body:
            self.scene.removeItem(self.elastic_body)
        self.elastic_body = ElasticBody(rect=rect, node_count=DEFAULT_NODE_COUNT)
        self.scene.addItem(self.elastic_body)

    def set_suction_point(self, p: QPointF):
        if self.suction_item:
            self.scene.removeItem(self.suction_item)
            self.suction_item = None
        self.suction_item = SuctionItem(center=p, radius=6.0, parent_view=self)
        self.scene.addItem(self.suction_item)
        if self.elastic_body:
            self.elastic_body.set_suction(p)

    def clear_suction_point(self):
        if self.suction_item:
            self.scene.removeItem(self.suction_item)
            self.suction_item = None
        if self.elastic_body:
            self.elastic_body.clear_suction()

    def export_png(self, path: str):
        pixmap = QPixmap(SCENE_SIZE, SCENE_SIZE)
        pixmap.fill(BACKGROUND_COLOR)
        painter = QPainter(pixmap)
        self.scene.render(painter)
        painter.end()
        pixmap.save(path, "PNG")

    def export_svg(self, path: str):
        generator = QSvgGenerator()
        generator.setFileName(path)
        generator.setSize(self.scene.sceneRect().size().toSize())
        generator.setViewBox(self.scene.sceneRect())
        generator.setTitle("Elastic Vacuum Simulation")
        generator.setDescription("Scene export")
        painter = QPainter(generator)
        self.scene.render(painter)
        painter.end()

    # --- Preview rectangle helpers ---
    def _start_preview(self, start: QPointF):
        if self.drag_rect_preview:
            self.scene.removeItem(self.drag_rect_preview)
        self.drag_rect_preview = QGraphicsPathItem()
        self.drag_rect_preview.setPen(QPen(QColor("#8888FF"), 1, Qt.PenStyle.DashLine))
        self.drag_rect_preview.setZValue(5)
        self.scene.addItem(self.drag_rect_preview)

    def _update_preview(self, rect: QRectF):
        if not self.drag_rect_preview:
            return
        path = QPainterPath()
        path.addRect(rect)
        self.drag_rect_preview.setPath(path)

    def _clear_preview(self):
        if self.drag_rect_preview:
            self.scene.removeItem(self.drag_rect_preview)
            self.drag_rect_preview = None


# ---- Main window with controls ----
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elastic Vacuum Simulation")
        self.resize(SCENE_SIZE + 240, SCENE_SIZE + 60)

        # Canvas
        self.view = CanvasView()
        self.setCentralWidget(self.view)

        # Simulation timer
        self.timer = QTimer(self)
        self.timer.setInterval(35)  # ~60 FPS
        self.timer.timeout.connect(self.on_tick)
        self.simulating = False
        self.dt = 0.005

        # Toolbar
        self._build_toolbar()

        # Modern palette
        self._apply_modern_palette()

    def _build_toolbar(self):
        tb = QToolBar("Tools")
        tb.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tb)

        # Actions
        act_add_point = QAction("Add fixed point", self)
        act_add_point_coords = QAction("Add fixed point (coords)", self)
        act_draw_circle = QAction("Draw circle", self)
        act_standard_circle = QAction("Standard circle", self)
        act_draw_ellipse = QAction("Draw ellipse", self)
        act_set_suction = QAction("Set suction", self)
        act_add_suction_coords = QAction("Set suction (coords)", self)
        act_clear_suction = QAction("Clear suction", self)
        act_start = QAction("Start sim", self)
        act_stop = QAction("Stop sim", self)
        act_export_png = QAction("Export PNG", self)
        act_export_svg = QAction("Export SVG", self)
        act_clear = QAction("Clear canvas", self)

        # Connect
        act_add_point.triggered.connect(
            lambda: self.view.set_tool_mode(ToolMode.ADD_FIXED_POINT)
        )
        act_add_point_coords.triggered.connect(self.add_point_coords_dialog)
        act_draw_circle.triggered.connect(
            lambda: self.view.set_tool_mode(ToolMode.DRAW_CIRCLE)
        )
        act_standard_circle.triggered.connect(self.add_standard_circle)
        act_draw_ellipse.triggered.connect(
            lambda: self.view.set_tool_mode(ToolMode.DRAW_ELLIPSE)
        )
        act_set_suction.triggered.connect(
            lambda: self.view.set_tool_mode(ToolMode.SET_SUCTION)
        )
        act_add_suction_coords.triggered.connect(self.add_suction_coords_dialog)
        act_clear_suction.triggered.connect(self.view.clear_suction_point)
        act_start.triggered.connect(self.start_sim)
        act_stop.triggered.connect(self.stop_sim)
        act_export_png.triggered.connect(self.on_export_png)
        act_export_svg.triggered.connect(self.on_export_svg)
        act_clear.triggered.connect(self.clear_canvas)

        # Add to toolbar
        tb.addSeparator()
        tb.addAction(act_add_point)
        tb.addAction(act_add_point_coords)
        tb.addSeparator()
        tb.addAction(act_draw_circle)
        tb.addAction(act_standard_circle)
        tb.addAction(act_draw_ellipse)
        tb.addSeparator()
        tb.addAction(act_set_suction)
        tb.addAction(act_add_suction_coords)
        tb.addAction(act_clear_suction)
        tb.addSeparator()
        tb.addAction(act_start)
        tb.addAction(act_stop)
        tb.addSeparator()
        tb.addAction(act_export_png)
        tb.addAction(act_export_svg)
        tb.addSeparator()
        tb.addAction(act_clear)
        tb.addSeparator()

    def _apply_modern_palette(self):
        pal = self.palette()
        self.setPalette(pal)

    # ---- Simulation control ----
    def start_sim(self):
        if not self.view.elastic_body:
            QMessageBox.information(self, "Info", "Draw a circle/ellipse first.")
            return
        self.simulating = True
        self.timer.start()

    def stop_sim(self):
        self.simulating = False
        self.timer.stop()

    def on_tick(self):
        if self.simulating and self.view.elastic_body:
            fixed_pts = [cross.center for cross in self.view.fixed_points]
            self.view.elastic_body.step(self.dt, fixed_pts)

            if self._all_points_grabbed(self.view.elastic_body, fixed_pts, radius=12.0):
                self.stop_sim()
                self.view.elastic_body.stretch_to_points(fixed_pts)

    # ---- Export ----
    def on_export_png(self):
        if self.simulating:
            QMessageBox.information(
                self, "Info", "Stop the simulation before exporting."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "scene.png", "PNG Files (*.png)"
        )
        if path:
            self.view.export_png(path)

    def on_export_svg(self):
        if self.simulating:
            QMessageBox.information(
                self, "Info", "Stop the simulation before exporting."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export SVG", "scene.svg", "SVG Files (*.svg)"
        )
        if path:
            self.view.export_svg(path)

    # ---- Fixed point coordinate entry ----
    def add_point_coords_dialog(self):
        text, ok = QInputDialog.getText(
            self, "Add fixed point", "Enter x,y (scene coords, origin at center):"
        )
        if not ok:
            return
        try:
            xs, ys = text.split(",")
            x = float(xs.strip())
            y = float(ys.strip())
        except Exception:
            QMessageBox.warning(self, "Invalid", "Please enter coordinates as: x,y")
            return

        cx = SCENE_SIZE / 2
        cy = SCENE_SIZE / 2
        scene_x = cx + x
        scene_y = cy - y
        scene_x = clamp(scene_x, 0, SCENE_SIZE)
        scene_y = clamp(scene_y, 0, SCENE_SIZE)

        self.view.add_fixed_point_coords(scene_x, scene_y)

    # ---- Suction point coordinate entry ----
    def add_suction_coords_dialog(self):
        text, ok = QInputDialog.getText(
            self, "Add suction point", "Enter x,y (Koordinaten):"
        )
        if not ok:
            return
        try:
            xs, ys = text.split(",")
            x = float(xs.strip())
            y = float(ys.strip())
        except Exception:
            QMessageBox.warning(self, "Invalid", "Bitte Koordinaten als x,y eingeben")
            return

        cx = SCENE_SIZE / 2
        cy = SCENE_SIZE / 2
        scene_x = cx + x
        scene_y = cy - y
        self.view.set_suction_point(QPointF(scene_x, scene_y))

    # ---- Standard circle ----
    def add_standard_circle(self):
        cx = SCENE_SIZE / 2
        cy = SCENE_SIZE / 2
        radius = 500
        rect = QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
        self.view.add_elastic_body(rect)

    # ---- Clear canvas ----
    def clear_canvas(self):
        self.stop_sim()
        for item in list(self.view.scene.items()):
            if item is self.view.axes:
                continue
            self.view.scene.removeItem(item)

        self.view.fixed_points.clear()
        self.view.elastic_body = None
        self.view.suction_item = None
        self.view.drag_start_scene = None
        self.view._clear_preview()

    def _all_points_grabbed(
        self, body: ElasticBody, fixed_pts: list[QPointF], radius: float = 12.0
    ) -> bool:
        if not fixed_pts or not body.nodes:
            return False
        for fp in fixed_pts:
            grabbed = any(dist(node.p, fp) < radius for node in body.nodes)
            if not grabbed:
                return False
        return True


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


### Created and vibecoded completely with Microsoft Copilot via:  https://copilot.microsoft.com/ ###


# Prompted for the overall asymptotic runtime, Microsoft Copilot calculated this:

# Asymptotic runtime of naive implementation: O(t * f * n + f log f)
# Asymptotic runtime with simple dimensional index: O(t * (n + f) + f log f)
# Asymptotic runtime with k-d-tree: O(t * (n log n + f log n) + f log f)

# n = Number of nodes in circular element conture
# f = Number of fixed points
# t = Number of simulation ticks until termination

# Comment: GUI events and rendering are not implemented into runtime calculation.
