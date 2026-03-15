Context gathered successfully. I've mapped all the code review issues with exact line numbers:

**Summary of findings:**

| Issue | File | Line(s) | Fix Required |
|-------|------|---------|---------------|
| Command Injection | `tray_icon.py` | 229, 357-359 | Use `shlex.split()` instead of `.split()` |
| Credential Docs | `settings.py` | 12-18 | Add security docstring to Settings class |
| WAV Header | `streaming_runner_base.py` | 172 | Use wave module for proper parsing |
| WAV Header | `engines/google/controller.py` | 293-296 | Use wave module for proper parsing |
| WAV Header | `engines/openai/controller.py` | 397-398 | Use wave module for proper parsing |
| Stderr Leak | `audio_recorder.py` | 304 | Add `stderr=subprocess.DEVNULL` |
| URL Validation | `model_repository.py` | 68-73 | Add domain validation for alphacephei.com |

The context file has been written to `/home/pcaro/src/dictatux/context.md` and archived to `~/.pi/history/dictatux/scouts/`.