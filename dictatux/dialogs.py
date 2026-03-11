#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Pablo Caro

ABOUTME: Dialog windows for Dictatux including model management and configuration
ABOUTME: Contains Advanced settings dialog with PulseAudio device selection
"""

from __future__ import annotations

import logging
import warnings
from typing import Dict, List, Optional, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QDialogButtonBox,
)

import dictatux.advanced as advanced  # type: ignore

from dictatux.ui_generator import (
    generate_settings_tab,
    read_settings_from_tab,
    format_tooltip,
)
from dictatux.engine_plugin import (
    get_all_engine_ids,
    get_engine_settings_class,
    get_engine_display_name,
)
from dictatux.model_ui.dialogs import launch_model_selection_dialog
from dictatux.audio_recorder import get_audio_devices

from dictatux.settings import Settings
from dictatux.utils import get_icon


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("About Dictatux"))
        self.setFixedSize(400, 350)

        layout = QVBoxLayout(self)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(":/icons/dictatux/scalable/dictatux.svg")
        logo_label.setPixmap(
            logo_pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # App Name and Version
        from importlib.metadata import version

        try:
            v = version("Dictatux")
        except Exception:
            v = "0.0.1"

        name_label = QLabel(f"<h2>Dictatux v{v}</h2>")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        # Description
        desc_label = QLabel(
            self.tr("Multi-engine voice recognition utility for Linux.")
        )
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)

        # License
        license_label = QLabel(self.tr("License: GPL v3.0"))
        license_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(license_label)

        # Authors
        authors_label = QLabel(self.tr("Author: Pablo Caro (pcaro)"))
        authors_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(authors_label)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class AdvancedUI(QDialog):
    def __init__(
        self,
        settings: Settings | None = None,
        reset_context_callback: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self.ui = advanced.Ui_Dialog()
        self.ui.setupUi(self)

        # Add About button to buttonBox
        self.about_button = self.ui.buttonBox.addButton(
            self.tr("About"), QDialogButtonBox.ButtonRole.HelpRole
        )
        self.about_button.clicked.connect(self.show_about)

        self.setWindowIcon(
            get_icon("dictatux", ":/icons/dictatux/scalable/dictatux.svg")
        )
        self._settings_ref = settings
        self._reset_context_callback = reset_context_callback
        self.engine_tabs: Dict[str, QWidget] = {}
        self.engine_settings_classes: Dict[str, type] = {}
        self._shortcut_rows: List[tuple[QLabel, str, str, QPushButton]] = []
        self._refresh_devices_button: Optional[QPushButton] = None
        self._add_shortcuts_config()
        self._populate_audio_devices()

        # Generate dynamic tabs for all engines
        self._generate_engine_tabs()

        # Update engine dropdown to include all registered engines
        self._populate_engine_dropdown()

        # Add info icons to General tab labels
        self._add_info_icons_to_general_tab()

        # Initialize Interface Language combobox data
        self.ui.interface_language_cb.setItemData(0, "en")
        self.ui.interface_language_cb.setItemData(1, "es")

        # Synchronize tabs with current selection
        self._on_stt_engine_changed(self.ui.stt_engine_cb.currentIndex())

        self.ui.stt_engine_cb.currentIndexChanged.connect(self._on_stt_engine_changed)
        self.ui.interface_language_cb.currentIndexChanged.connect(
            self._on_language_changed
        )
        self.language_changed_callback = None

    def show_about(self) -> None:
        """Show the About dialog."""
        AboutDialog(self).exec()

    def _on_language_changed(self, index: int) -> None:
        lang = self.ui.interface_language_cb.itemData(index)
        if lang:
            from dictatux.dictatux import load_translations
            from PySide6.QtWidgets import QApplication

            load_translations(QApplication.instance(), lang)
            self.retranslateUi()

            # Call callback to let tray icon update itself
            if (
                hasattr(self, "language_changed_callback")
                and self.language_changed_callback
            ):
                self.language_changed_callback()

    def retranslateUi(self) -> None:
        """Retranslate all UI components including dynamic ones."""
        # Block signals to avoid recursive or unwanted calls during re-population
        self.ui.stt_engine_cb.blockSignals(True)
        self.ui.interface_language_cb.blockSignals(True)

        try:
            # Save current selections
            current_engine = self.ui.stt_engine_cb.currentData()
            current_lang = self.ui.interface_language_cb.currentData()

            # Retranslate static UI from generated class
            self.ui.retranslateUi(self)

            # Rebuild dynamic engine tabs so labels/tooltips use new translator
            self._rebuild_engine_tabs_for_translation()

            # Re-populate engine dropdown (it was cleared or messed up by retranslateUi)
            self._populate_engine_dropdown()

            # Restore engine selection
            index = self.ui.stt_engine_cb.findData(current_engine)
            if index >= 0:
                self.ui.stt_engine_cb.setCurrentIndex(index)

            # Restore language selection and data
            self.ui.interface_language_cb.setItemData(0, "en")
            self.ui.interface_language_cb.setItemData(1, "es")
            index = self.ui.interface_language_cb.findData(current_lang)
            if index >= 0:
                self.ui.interface_language_cb.setCurrentIndex(index)

            # Re-apply info icons since layout/texts might have been reset
            self._add_info_icons_to_general_tab()
            self._retranslate_dynamic_general_widgets()

            # Ensure tab enabled state follows selected engine
            index = self.ui.stt_engine_cb.currentIndex()
            if index >= 0:
                self._on_stt_engine_changed(index)
        finally:
            self.ui.stt_engine_cb.blockSignals(False)
            self.ui.interface_language_cb.blockSignals(False)

    def _add_info_icons_to_general_tab(self) -> None:
        """Add info icons to labels in the General tab that have tooltips."""
        self._ensure_info_icons_in_layout(self.ui.general_grid_layout)
        self._ensure_label_has_info_icon(
            self.ui.label_stt_engine,
            self.ui.gridLayout_8,
            row=0,
            col=0,
        )

    def _ensure_info_icons_in_layout(self, layout) -> None:
        """Ensure labels with tooltips have one info icon container."""
        for i in range(layout.rowCount()):
            item = layout.itemAtPosition(i, 0)
            if not item:
                continue

            widget = item.widget()
            if widget is None:
                continue

            if isinstance(widget, QLabel):
                self._ensure_label_has_info_icon(widget, layout, i, 0)
                continue

            if isinstance(widget, QWidget) and getattr(
                widget, "_dictatux_info_container", False
            ):
                label = getattr(widget, "_dictatux_info_label", None)
                icon = getattr(widget, "_dictatux_info_icon", None)
                if isinstance(label, QLabel) and isinstance(icon, QLabel):
                    tooltip_text = label.toolTip()
                    if tooltip_text:
                        icon.setToolTip(format_tooltip(tooltip_text))
                        label.setToolTip("")

    def _ensure_label_has_info_icon(
        self, label: QLabel, layout, row: int, col: int
    ) -> None:
        """Wrap label with tooltip in a reusable label+info icon container."""
        tooltip_text = label.toolTip()
        if not tooltip_text:
            return

        current_item = layout.itemAtPosition(row, col)
        current_widget = current_item.widget() if current_item else None

        if isinstance(current_widget, QWidget) and getattr(
            current_widget, "_dictatux_info_container", False
        ):
            icon = getattr(current_widget, "_dictatux_info_icon", None)
            if isinstance(icon, QLabel):
                icon.setToolTip(format_tooltip(tooltip_text))
                label.setToolTip("")
            return

        container = QWidget()
        container._dictatux_info_container = True  # type: ignore[attr-defined]
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        layout.removeWidget(label)

        info_icon = QLabel("ⓘ")
        info_icon.setStyleSheet("color: #3498db; font-weight: bold;")
        info_icon.setToolTip(format_tooltip(tooltip_text))

        container._dictatux_info_label = label  # type: ignore[attr-defined]
        container._dictatux_info_icon = info_icon  # type: ignore[attr-defined]

        h_layout.addWidget(label)
        h_layout.addWidget(info_icon)
        h_layout.addStretch()
        layout.addWidget(container, row, col)
        label.setToolTip("")

    def _capture_engine_tab_values(self) -> Dict[str, object]:
        """Capture current engine dataclass values to preserve edits on retranslate."""
        captured: Dict[str, object] = {}
        for engine_id in list(self.engine_tabs.keys()):
            settings_obj = self.get_engine_settings_dataclass(engine_id)
            if settings_obj is not None:
                captured[engine_id] = settings_obj
        return captured

    def _rebuild_engine_tabs_for_translation(self) -> None:
        """Rebuild dynamic tabs so labels/tooltips are translated with current locale."""
        captured_values = self._capture_engine_tab_values()
        for tab in list(self.engine_tabs.values()):
            idx = self.ui.tabWidget.indexOf(tab)
            if idx >= 0:
                self.ui.tabWidget.removeTab(idx)
            tab.deleteLater()

        self.engine_tabs = {}
        self.engine_settings_classes = {}
        self._generate_engine_tabs(instances=captured_values)

    def _retranslate_dynamic_general_widgets(self) -> None:
        """Retranslate labels/tooltips for widgets added programmatically."""
        for label, label_text, tooltip_text, clear_button in self._shortcut_rows:
            label.setText(self.tr(label_text))
            label.setToolTip(self.tr(tooltip_text))
            clear_button.setToolTip(self.tr("Clear shortcut"))

        if self._refresh_devices_button is not None:
            self._refresh_devices_button.setToolTip(
                self.tr("Refresh audio device list")
            )

    def _generate_engine_tabs(
        self, instances: Optional[Dict[str, object]] = None
    ) -> None:
        """Generate tabs dynamically for all registered engines."""
        self.engine_tabs = {}
        instances = instances or {}

        for engine_id in get_all_engine_ids():
            settings_class = get_engine_settings_class(engine_id)
            if not settings_class:
                logging.warning(
                    f"Could not load settings class for engine: {engine_id}"
                )
                continue

            # Generate tab from settings metadata
            instance = instances.get(engine_id)
            if instance is None and self._settings_ref is not None:
                try:
                    instance = self._settings_ref.get_engine_settings(engine_id)
                except Exception as exc:  # pragma: no cover - defensive
                    logging.debug("Failed to load settings for %s: %s", engine_id, exc)

            tab_widget = generate_settings_tab(settings_class, instance)
            num_widgets = len(getattr(tab_widget, "widgets_map", {}))
            logging.debug(f"Generated tab for {engine_id} with {num_widgets} widgets")

            # Add tab to dialog
            display_name = get_engine_display_name(engine_id)
            idx = self.ui.tabWidget.addTab(tab_widget, display_name)

            # Initially disable all engine tabs (they'll be enabled when selected)
            self.ui.tabWidget.setTabEnabled(idx, False)

            # Store reference
            self.engine_tabs[engine_id] = tab_widget
            self.engine_settings_classes[engine_id] = settings_class

            self._wire_engine_tab_actions(engine_id, tab_widget)

    def _wire_engine_tab_actions(self, engine_id: str, tab_widget: QWidget) -> None:
        """Attach callbacks for engine-specific action buttons."""
        if engine_id == "vosk-local":
            button = tab_widget.widgets_map.get("manage_models_action")
            if isinstance(button, QPushButton):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", RuntimeWarning)
                        button.clicked.disconnect()
                except (TypeError, RuntimeError):
                    pass
                button.clicked.connect(
                    lambda _checked=False, tab=tab_widget: self._handle_model_selection(
                        tab
                    )
                )

        if engine_id == "whisper-local":
            button = tab_widget.widgets_map.get("reset_context_action")
            if isinstance(button, QPushButton) and self._reset_context_callback:
                button.clicked.connect(self._reset_context_callback)

    def _populate_engine_dropdown(self) -> None:
        """Populate the engine dropdown with all registered engines."""
        # Clear existing items
        self.ui.stt_engine_cb.clear()

        # Add all registered engines with display names
        for engine_id in get_all_engine_ids():
            display_name = get_engine_display_name(engine_id)
            self.ui.stt_engine_cb.addItem(display_name, engine_id)

    def get_engine_settings_dataclass(self, engine_id: str):
        """Return dataclass instance built from the current tab values."""
        tab = self.engine_tabs.get(engine_id)
        settings_class = self.engine_settings_classes.get(engine_id)
        if not tab or not settings_class:
            return None
        return read_settings_from_tab(tab, settings_class)

    def _handle_model_selection(self, tab: QWidget) -> None:
        launch_model_selection_dialog(self)
        settings_obj = self._settings_ref or Settings()
        try:
            settings_obj.load()
        except Exception:
            return
        _, location = settings_obj.current_model()
        path_widget = getattr(tab, "widgets_map", {}).get("model_path")
        if isinstance(path_widget, QLineEdit):
            path_widget.setText(location)

    def _on_stt_engine_changed(self, index: int):
        """Handle engine selection change."""
        if index < 0:
            return

        # Get engine ID from dropdown data (safer to use itemData with index)
        engine = self.ui.stt_engine_cb.itemData(index)
        if not engine:
            return

        logging.debug(f"STT Engine changed to: {engine} (at index {index})")

        # Enable/disable tabs based on selected engine
        # "General" tab (index 0) must always be enabled
        self.ui.tabWidget.setTabEnabled(0, True)

        target_tab = self.engine_tabs.get(engine)

        for engine_name, tab in self.engine_tabs.items():
            idx = self.ui.tabWidget.indexOf(tab)
            if idx >= 0:
                is_active = engine_name == engine
                self.ui.tabWidget.setTabEnabled(idx, is_active)

        # Switch to the appropriate tab if it exists
        if target_tab:
            self.ui.tabWidget.setCurrentWidget(target_tab)

    def _add_shortcuts_config(self) -> None:
        # This is a bit of a hack, but it's the easiest way to add the shortcuts
        # to the general tab without redoing the whole UI file.
        layout = self.ui.general_grid_layout
        row_count = layout.rowCount()

        # Helper to add shortcut with clear button
        def add_shortcut_row(
            row: int, label_text: str, tooltip: str
        ) -> QKeySequenceEdit:
            label = QLabel(self.tr(label_text))
            label.setToolTip(self.tr(tooltip))
            shortcut_edit = QKeySequenceEdit()

            clear_button = QPushButton("✕")
            clear_button.setMaximumWidth(30)
            clear_button.setToolTip(self.tr("Clear shortcut"))
            clear_button.clicked.connect(shortcut_edit.clear)

            layout.addWidget(label, row, 0)
            layout.addWidget(shortcut_edit, row, 1)
            layout.addWidget(clear_button, row, 2)
            self._shortcut_rows.append((label, label_text, tooltip, clear_button))
            return shortcut_edit

        self.beginShortcut = add_shortcut_row(
            row_count,
            "Global shortcut: Begin",
            "Global keyboard shortcut to begin dictation (KDE only)",
        )

        self.endShortcut = add_shortcut_row(
            row_count + 1,
            "Global shortcut: End",
            "Global keyboard shortcut to end dictation (KDE only)",
        )

        self.toggleShortcut = add_shortcut_row(
            row_count + 2,
            "Global shortcut: Toggle",
            "Global keyboard shortcut to toggle dictation (KDE only)",
        )

        self.suspendShortcut = add_shortcut_row(
            row_count + 3,
            "Global shortcut: Suspend",
            "Global keyboard shortcut to suspend dictation (KDE only)",
        )

        self.resumeShortcut = add_shortcut_row(
            row_count + 4,
            "Global shortcut: Resume",
            "Global keyboard shortcut to resume dictation (KDE only)",
        )

    def _populate_audio_devices(self) -> None:
        """Populate the device name combo box with available audio devices and add refresh button."""
        # Get the layout where deviceName is located
        layout = self.ui.general_grid_layout

        # Populate initial devices
        self._refresh_audio_devices()

        # Create refresh button
        refresh_button = QPushButton("🔄")
        refresh_button.setMaximumWidth(40)
        refresh_button.setToolTip(self.tr("Refresh audio device list"))
        refresh_button.clicked.connect(self._refresh_audio_devices)
        self._refresh_devices_button = refresh_button

        # Add refresh button next to the combobox (row 3, column 2)
        layout.addWidget(refresh_button, 3, 2, 1, 1)

    def _refresh_audio_devices(self) -> None:
        """Refresh the audio devices list in the dropdown."""
        devices = get_audio_devices(backend="parec")
        combo = self.ui.deviceName

        # Save current selection
        current_value = combo.currentData() or combo.currentText()

        # Repopulate
        combo.clear()
        for device_value, display_name in devices:
            combo.addItem(display_name, device_value)

        # Restore selection if it still exists
        index = combo.findData(current_value)
        if index >= 0:
            combo.setCurrentIndex(index)
        elif current_value:
            # Fallback to text matching
            index = combo.findText(current_value)
            if index >= 0:
                combo.setCurrentIndex(index)

    def show_validation_warnings_dialog(
        self,
        general_warnings: dict[str, str],
        engine_warnings: dict[str, str],
        engine_id: str,
    ) -> bool:
        """Show dialog with validation warnings and ask user to confirm.

        Args:
            general_warnings: Warnings from General tab
            engine_warnings: Warnings from engine tab
            engine_id: Current engine identifier

        Returns:
            True if user wants to save anyway, False to go back and fix
        """
        from PySide6.QtWidgets import QMessageBox

        warning_lines = []

        if general_warnings:
            warning_lines.append(self.tr("General Settings:"))
            for message in general_warnings.values():
                warning_lines.append(f"  - {message}")

        if engine_warnings:
            engine_name = get_engine_display_name(engine_id)
            warning_lines.append("")
            warning_lines.append(f"{engine_name}:")
            for message in engine_warnings.values():
                warning_lines.append(f"  - {message}")

        message = (
            self.tr("The following warnings were found:")
            + "\n\n"
            + "\n".join(warning_lines)
            + "\n\n"
            + self.tr("Do you want to save anyway?")
        )

        reply = QMessageBox.warning(
            self,
            self.tr("Validation Warnings"),
            message,
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        return reply == QMessageBox.StandardButton.Save

    def add_tab_warning_icon(self, tab_widget: QWidget, has_warnings: bool) -> None:
        """Add or remove warning icon from tab label.

        Args:
            tab_widget: The tab widget
            has_warnings: True to add icon, False to remove
        """
        tab_index = self.ui.tabWidget.indexOf(tab_widget)
        if tab_index < 0:
            return

        original_text = self.ui.tabWidget.tabText(tab_index)

        # Remove existing warning icon if present
        if original_text.startswith("⚠️ "):
            original_text = original_text[3:]

        # Add warning icon if needed
        if has_warnings:
            new_text = f"⚠️ {original_text}"
        else:
            new_text = original_text

        self.ui.tabWidget.setTabText(tab_index, new_text)
