# Installation

Dictatux can be installed using various methods, with `uv` being the recommended approach for modern Python environments.

## Quick Start

```bash
# Install with uv (recommended)
uv tool install git+https://github.com/pcaro/dictatux

# Or run without installing
uv run --with dictatux dictatux
```

## Using `uv` (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package and project manager that handles dependencies automatically.

### Installation Options

Dictatux offers **optional dependencies** for different STT engines. You can install only what you need:

**Core only (no local STT engines):**
```bash
uv pip install -e .
```

**Vosk Local (lightweight, CPU-only):**
```bash
uv pip install -e ".[local_stt]"
```

**Vosk Local with CUDA (GPU support):**
```bash
uv pip install -e ".[local_stt_cuda]"
```

**Whisper Local (CPU-only):**
```bash
# Install torch CPU first (lightweight, ~200MB)
uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install whisper_local without torch
uv pip install -e ".[whisper_local]"
```

**Whisper Local with CUDA (GPU support):**
```bash
# Installs torch with CUDA automatically (~4GB)
uv pip install -e ".[whisper_local_cuda]"
```

**All engines with CUDA:**
```bash
uv pip install -e ".[all]"
```

### Global Installation

```bash
uv tool install git+https://github.com/pcaro/dictatux
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/pcaro/dictatux
cd dictatux

# Install with desired extras
uv pip install -e ".[whisper_local]"  # CPU version
```

## Requirements

**Core Dependencies** (always installed):
- Python 3.8+
- PyQt6 (includes D-Bus support for KDE global shortcuts)
- ujson
- vosk
- pyaudio
- requests
- google-cloud-speech
- websocket-client

**Engine-Specific Dependencies** (optional):

| Engine | Extra | Dependencies | Size |
|--------|-------|--------------|------|
| Vosk Local | `local_stt` | vosk, webrtcvad | ~50MB |
| Vosk Local + CUDA | `local_stt_cuda` | + torch, torchaudio | ~4GB |
| Whisper Local | `whisper_local` | faster-whisper, silero-vad* | ~100MB |
| Whisper Local + CUDA | `whisper_local_cuda` | + torch, torchaudio | ~4GB |

*Requires manual installation of torch CPU first

**System Dependencies:**
- **Audio**: parec (PulseAudio) or PyAudio
- **Input Simulation**: xdotool (X11) or dotool (Wayland)

## Wayland Support

For **Wayland** (including KDE Plasma Wayland), Dictatux uses **dotool** instead of xdotool for text input simulation.

### Installing dotool

**Arch/Manjaro:**
```bash
sudo pacman -S dotool
```

**Fedora:**
```bash
sudo dnf install dotool
```

**Ubuntu/Debian/KDE Neon:**
```bash
# Install dependencies
sudo apt install -y build-essential golang-go libevdev-dev scdoc libxkbcommon-dev

# Build from source
cd /tmp
git clone https://git.sr.ht/~geb/dotool
cd dotool
./build.sh
sudo ./build.sh install

# Reload udev rules (no reboot required)
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Verification:**
```bash
dotool <<< "type hello"
# Should type "hello" in your active window
```

### Configuration

1. Open Dictatux's **Advanced Settings**
2. Set **Input Tool** to `DOTOOL`
3. Set **Keyboard Layout** if needed (e.g., `us`, `es`, `fr`)

### Note on Permissions

dotool uses uinput to simulate keyboard input. The `sudo ./build.sh install` command automatically installs udev rules that grant necessary permissions. You may need to log out and back in for group changes to take effect.
