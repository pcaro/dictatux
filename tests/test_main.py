from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch


from dictatux import dictatux
from PySide6.QtCore import QFile


def test_resources_are_loaded():
    """Verify that the compiled Qt resources are available."""
    # This check ensures that dictatux_rc was imported and registered correctly
    assert QFile.exists(":/icons/dictatux/scalable/dictatux.svg")
    assert QFile.exists(":/icons/dictatux/24/micro.png")
    assert QFile.exists(":/icons/dictatux/24/nomicro.png")


@patch("dictatux.dictatux.choose_ipc_command")
@patch("dictatux.dictatux.handle_model_commands")
def test_already_running_no_command(mock_handle_model, mock_choose_ipc):
    """Verify app exits if it's already running and no command is given."""
    # Arrange
    mock_ipc = MagicMock()
    mock_ipc.is_running.return_value = True
    mock_choose_ipc.return_value = None
    mock_handle_model.return_value = None  # No model command

    args = MagicMock()

    # Act & Assert
    with patch("builtins.print") as mock_print, patch("sys.exit") as mock_exit:
        dictatux.handle_cli_commands_and_exit_if_needed(args, mock_ipc)
        mock_print.assert_any_call("Dictatux is already running", file=sys.stderr)
        mock_exit.assert_called_with(1)


@patch("dictatux.dictatux.choose_ipc_command")
@patch("dictatux.dictatux.handle_model_commands")
def test_send_command_to_running_instance_success(mock_handle_model, mock_choose_ipc):
    """Verify a command is sent successfully to a running instance."""
    # Arrange
    mock_ipc = MagicMock()
    mock_ipc.is_running.return_value = True
    mock_ipc.send_command.return_value = True
    mock_choose_ipc.return_value = "begin"
    mock_handle_model.return_value = None

    args = MagicMock()

    # Act & Assert
    with patch("builtins.print") as mock_print, patch("sys.exit") as mock_exit:
        dictatux.handle_cli_commands_and_exit_if_needed(args, mock_ipc)
        mock_ipc.send_command.assert_called_with("begin")
        mock_print.assert_called_with("✓ Command 'begin' sent successfully")
        mock_exit.assert_called_with(0)


@patch("dictatux.dictatux.choose_ipc_command")
@patch("dictatux.dictatux.handle_model_commands")
def test_send_command_to_running_instance_failure(mock_handle_model, mock_choose_ipc):
    """Verify app exits with error if sending a command fails."""
    # Arrange
    mock_ipc = MagicMock()
    mock_ipc.is_running.return_value = True
    mock_ipc.send_command.return_value = False
    mock_choose_ipc.return_value = "begin"
    mock_handle_model.return_value = None

    args = MagicMock()

    # Act & Assert
    with patch("builtins.print") as mock_print, patch("sys.exit") as mock_exit:
        dictatux.handle_cli_commands_and_exit_if_needed(args, mock_ipc)
        mock_ipc.send_command.assert_called_with("begin")
        mock_print.assert_called_with(
            "✗ Failed to send 'begin' command", file=sys.stderr
        )
        mock_exit.assert_called_with(1)


@patch("dictatux.dictatux.choose_ipc_command")
@patch("dictatux.dictatux.handle_model_commands")
def test_command_with_no_running_instance(mock_handle_model, mock_choose_ipc):
    """Verify app exits if 'exit' or 'end' is used with no running instance."""
    # Arrange
    mock_ipc = MagicMock()
    mock_ipc.is_running.return_value = False
    mock_handle_model.return_value = None
    args = MagicMock()

    # Test "exit" command
    mock_choose_ipc.return_value = "exit"
    with patch("builtins.print") as mock_print, patch("sys.exit") as mock_exit:
        dictatux.handle_cli_commands_and_exit_if_needed(args, mock_ipc)
        mock_print.assert_called_with("No running instance to exit")
        mock_exit.assert_called_with(1)

    # Test "end" command
    mock_choose_ipc.return_value = "end"
    with patch("builtins.print") as mock_print, patch("sys.exit") as mock_exit:
        dictatux.handle_cli_commands_and_exit_if_needed(args, mock_ipc)
        mock_print.assert_called_with("No running instance to end")
        mock_exit.assert_called_with(1)


@patch("dictatux.dictatux.choose_ipc_command")
@patch("dictatux.dictatux.handle_model_commands")
def test_begin_command_with_no_running_instance_continues(
    mock_handle_model, mock_choose_ipc
):
    """Verify that the 'begin' command does not exit if no instance is running."""
    # Arrange
    mock_ipc = MagicMock()
    mock_ipc.is_running.return_value = False
    mock_choose_ipc.return_value = "begin"
    mock_handle_model.return_value = None
    args = MagicMock()

    # Act & Assert
    with patch("sys.exit") as mock_exit:
        dictatux.handle_cli_commands_and_exit_if_needed(args, mock_ipc)
        mock_exit.assert_not_called()
