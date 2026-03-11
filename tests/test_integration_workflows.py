from __future__ import annotations

import os
from typing import List, Tuple

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from dictatux.settings import Settings
from dictatux.tray_icon import SystemTrayIcon
from tests.helpers import FakeController, FakeIPC, FakeRunner


@pytest.fixture(scope="module")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


@pytest.fixture
def fake_engine(monkeypatch) -> List[Tuple[FakeController, FakeRunner]]:
    created: List[Tuple[FakeController, FakeRunner]] = []

    def factory(engine_type: str = "vosk-local", **kwargs):
        controller = FakeController()
        runner = FakeRunner(controller)
        created.append((controller, runner))
        return controller, runner

    monkeypatch.setattr("dictatux.engine_manager.create_stt_engine", factory)
    return created


@pytest.fixture
def tray(fake_engine, qt_app):
    """Create a SystemTrayIcon with cleanup."""
    ipc = FakeIPC()
    icon = QIcon()
    tray = SystemTrayIcon(icon, False, ipc, temporary_engine="fake-engine")
    tray.settings.sttEngine = "fake-engine"
    tray.settings.models = [{"name": "fake", "location": "/tmp/fake-model"}]
    yield tray
    # Cleanup: cancel any pending timers
    tray._engine_manager._cancel_retry_timer()
    tray._engine_manager._cancel_refresh_timeout()


def test_full_engine_workflow(tray, fake_engine, qt_app):
    controller, runner = fake_engine[-1]

    tray.begin()
    assert runner.is_running() is True
    assert tray.dictating is True
    assert controller.states[-1] == "READY"

    tray.suspend()
    assert tray.suspended is True
    assert controller.states[-1] == "SUSPENDED"

    tray.resume()
    assert tray.suspended is False
    assert controller.states[-1] == "READY"

    tray.end()
    assert runner.is_running() is False
    assert tray.dictating is False
    assert controller.exit_codes[-1] == 0


def test_settings_persistence_roundtrip(qt_app):
    backend = QSettings(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        "DictatuxIntegration",
        "PersistenceTest",
    )
    backend.clear()

    settings = Settings(backend)
    settings.sttEngine = "openai-realtime"
    settings.openaiLanguage = "es"
    settings.deviceName = "test-device"
    settings.add_model("es", "fake-model", "1.0", "1GB", "vosk", "/tmp/fake-model")
    settings.save()

    reload_backend = QSettings(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        "DictatuxIntegration",
        "PersistenceTest",
    )
    reloaded = Settings(reload_backend)
    reloaded.load()

    assert reloaded.sttEngine == "openai-realtime"
    assert reloaded.openaiLanguage == "es"
    assert reloaded.deviceName == "test-device"
    assert reloaded.models == [
        {
            "name": "fake-model",
            "language": "es",
            "version": "1.0",
            "size": "1GB",
            "type": "vosk",
            "location": "/tmp/fake-model",
        }
    ]

    reload_backend.clear()


def test_error_recovery_triggers_retry(tray, fake_engine, qt_app):
    tray._engine_manager._retry_delay_ms = 1
    tray._engine_manager._max_retries = 3  # Limit retries for faster test

    initial_controller, initial_runner = fake_engine[-1]

    tray.begin()
    assert initial_runner.is_running() is True

    initial_runner.fail()
    qt_app.processEvents()
    assert tray.dictating is False
    assert initial_controller.exit_codes[-1] == 1

    QTest.qWait(50)
    qt_app.processEvents()

    assert len(fake_engine) >= 2
    _, new_runner = fake_engine[-1]
    assert tray.dictation_runner is new_runner
    assert new_runner.is_running() is False
