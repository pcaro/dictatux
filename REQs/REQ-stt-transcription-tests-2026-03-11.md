# REQ: Tests de Regresión de Transcripción STT

**Fecha:** 2026-03-11
**Estado:** Borrador v2
**Autor:** Pablo Caro

---

## 1. Resumen Ejecutivo

Ampliar la cobertura de tests del proyecto extendiendo el patrón probado en `tests/engines/test_google_cloud_integration.py` a los demás motores STT. Cada motor tiene un método central de procesamiento de respuestas que actualmente carece de tests. El objetivo es cubrir esos métodos con datos reales capturados de logs o sesiones de dictado, verificando que el texto que llega al `input_simulator` es correcto.

No se propone un framework abstracto. Se proponen tests concretos por motor, siguiendo el mismo estilo que ya funciona para Google Cloud Speech.

---

## 2. Motivación

### Lo que ya existe y funciona

`test_google_cloud_integration.py` demuestra un patrón eficaz:

1. **Dataclasses que replican la API** — `MockStreamingResponse`, `MockRecognitionResult`, etc.
2. **Datos reales capturados de logs** — `REAL_API_RESPONSES` con timestamps exactos.
3. **`MockInputSimulator`** de `tests/helpers.py` — acumula texto y gestiona backspaces.
4. **Helper `create_runner()`** — instancia el runner real con dependencias mockeadas.
5. **Invocación directa del método de procesamiento** — llama a `_response_loop()` sin levantar hilos ni conexiones reales.
6. **Asserts sobre `mock.text` y `mock.calls`** — verifica el texto final y la secuencia de llamadas.

### Gaps en la cobertura actual

| Motor | Método central | ¿Testeado? | Gap |
|-------|---------------|------------|-----|
| Google Cloud | `_response_loop()` | ✅ Sí | — |
| OpenAI Realtime | `_on_message()` | ❌ No | Sin tests de procesamiento de mensajes WebSocket |
| Whisper Docker | `_process_audio_chunk()` / `_transcribe_audio()` | ❌ No | Sin tests de procesamiento de respuestas REST |
| Vosk Local | `VoskInferenceBackend.transcribe()` | ❌ No | Sin tests de transcripción con datos reales |
| Whisper Local | `WhisperInferenceBackend.transcribe()` | ❌ No | Sin tests de transcripción con datos reales |

---

## 3. Historias de Usuario

### HU-1: Detectar Regresiones en el Procesamiento de Respuestas
> **Como** desarrollador de Dictatux
> **Quiero** tests que verifiquen que el procesamiento de respuestas de cada motor produce el texto correcto
> **Para** detectar regresiones cuando modifico la lógica de transcripción, partials o formateo

### HU-2: Tests Rápidos y Sin Dependencias Externas
> **Como** mantenedor del proyecto
> **Quiero** tests que se ejecuten sin internet, credenciales, Docker ni modelos pesados
> **Para** poder ejecutarlos en CI en menos de 10 segundos

### HU-3: Documentar el Comportamiento Esperado
> **Como** contribuidor nuevo
> **Quiero** ver datos reales de cada API en los tests
> **Para** entender el formato exacto de las respuestas de cada motor

---

## 4. Estrategia por Tipo de Motor

### 4.1 Motores remotos (Google, OpenAI, Whisper Docker)

**Estrategia:** Mockear el transporte (gRPC / WebSocket / HTTP), inyectar respuestas reales capturadas de logs, invocar directamente el método de procesamiento, verificar `input_simulator`.

**Justificación:** Estos motores requieren credenciales, red o Docker para funcionar. Pero su lógica de procesamiento de respuestas es pura transformación de datos y se puede testear aisladamente.

### 4.2 Motores locales (Vosk, Whisper Local)

**Estrategia:** Testear a nivel de `InferenceBackend.transcribe()` con el modelo Vosk pequeño que ya existe en `tests/fixtures/vosk-model-small-en-us-0.15/`. Para Whisper Local, mockear `faster_whisper.WhisperModel` y verificar el post-procesamiento (filtrado de alucinaciones, contexto).

**Justificación:** Cargar un modelo Vosk de 40MB es aceptable en CI. Cargar un modelo Whisper es demasiado lento y pesado; lo que interesa testear es la lógica de post-procesamiento.

---

## 5. Requisitos Funcionales

### RF-1: Tests de Transcripción para OpenAI Realtime

**El sistema** debe incluir tests que alimenten mensajes WebSocket reales al método `_on_message()` de `OpenAIRealtimeProcessRunner` y verifiquen el texto producido.

**Método bajo test:**
```python
# dictatux/engines/openai/controller.py
def _on_message(self, ws, message) -> None:
```

**Tipos de mensaje a cubrir:**

| Tipo | Propósito |
|------|-----------|
| `conversation.item.input_audio_transcription.completed` | Transcripción final (camino principal) |
| `conversation.item.input_audio_transcription.delta` | Deltas parciales (cuando `use_partials=True`) |
| `response.output_text.delta` | Acumulación de texto durante una respuesta |
| `response.completed` | Flush del texto acumulado |
| `error` | Manejo de errores |

**Criterios de aceptación:**
- [ ] Test con secuencia de mensajes `completed` → verifica `mock.text` correcto
- [ ] Test con secuencia de `delta` + `completed` → verifica corrección con backspaces (partials)
- [ ] Test de mensaje `error` → verifica que no se escribe texto basura
- [ ] Test de `transcript` vacío → verifica que se ignora
- [ ] Test con acumulación `response.output_text.delta` → `response.completed` → verifica flush

### RF-2: Tests de Transcripción para Whisper Docker

**El sistema** debe incluir tests que alimenten respuestas HTTP reales al método `_process_audio_chunk()` de `WhisperDockerProcessRunner` y verifiquen el texto producido.

**Métodos bajo test:**
```python
# dictatux/engines/whisper/controller.py
def _process_audio_chunk(self, audio_data: bytes) -> None:
def _transcribe_audio(self, audio_data: bytes) -> str:
```

**Criterios de aceptación:**
- [ ] Test con respuesta JSON `{"text": "..."}` → verifica `input_simulator` recibe el texto
- [ ] Test con VAD activado + audio silencioso (nivel bajo) → verifica que se salta el chunk
- [ ] Test con VAD activado + audio con voz (nivel alto) → verifica que se procesa
- [ ] Test con respuesta vacía `{"text": ""}` → verifica que no se escribe
- [ ] Test de retry en fallo HTTP → verifica reintento y recuperación
- [ ] Test de transiciones de estado: `RECORDING → TRANSCRIBING → RECORDING`

### RF-3: Tests de Transcripción para Vosk Local (con modelo real)

**El sistema** debe incluir tests que usen el modelo real `vosk-model-small-en-us-0.15` ya presente en `tests/fixtures/` para verificar el backend de inferencia.

**Método bajo test:**
```python
# dictatux/engines/vosk_local/inference_backend.py
class VoskInferenceBackend(InferenceBackend):
    def transcribe(self, audio: bytes) -> str:
```

**Criterios de aceptación:**
- [ ] Test con audio WAV pre-grabado en inglés → verifica que el texto básico es correcto
- [ ] Test de `transcribe_streaming()` → verifica que produce resultados parciales
- [ ] Test con audio silencioso → verifica que retorna cadena vacía
- [ ] Test de `load_model()` / `unload_model()` → verifica ciclo de vida
- [ ] Marcar con `@pytest.mark.slow` para permitir exclusión en CI rápido

### RF-4: Tests de Post-procesamiento para Whisper Local

**El sistema** debe incluir tests que verifiquen la lógica de post-procesamiento de `WhisperInferenceBackend.transcribe()` con el modelo mockeado.

**Método bajo test:**
```python
# dictatux/engines/whisper_local/inference_backend.py
class WhisperInferenceBackend(InferenceBackend):
    def transcribe(self, audio: bytes) -> str:
```

**Criterios de aceptación:**
- [ ] Test de filtrado de alucinaciones (`no_speech_prob > 0.6`) → verifica que se descartan
- [ ] Test de concatenación de múltiples segmentos → verifica texto unido correcto
- [ ] Test de actualización de contexto (`ContextManager.add()`) → verifica que se llama
- [ ] Test con segmentos vacíos → verifica que retorna cadena vacía
- [ ] Test de `initial_prompt` → verifica que se pasa el contexto al modelo

### RF-5: Utilidad WER (Word Error Rate)

**El sistema** debe incluir una función de utilidad `calculate_wer()` en `tests/helpers.py` para uso opcional en asserts.

**Criterios de aceptación:**
- [ ] Función `calculate_wer(reference: str, hypothesis: str) -> float`
- [ ] Normalización de texto: minúsculas, eliminar puntuación
- [ ] Usar la librería `jiwer`
- [ ] No es obligatorio usarla en todos los tests — es un complemento a los asserts exactos
- [ ] Incluir tests unitarios para la propia función WER

---

## 6. Diseño por Motor

### 6.1 OpenAI Realtime — `test_openai_transcription.py`

**Patrón:** Replicar el formato de mensajes WebSocket con diccionarios JSON. Instanciar `OpenAIRealtimeProcessRunner` con dependencias mockeadas. Llamar a `_on_message(mock_ws, json.dumps(message))` directamente.

```python
# Ejemplo de datos reales a capturar
REAL_WEBSOCKET_MESSAGES = [
    # Transcripción final
    {
        "type": "conversation.item.input_audio_transcription.completed",
        "transcript": "Esto es una prueba de dictado."
    },
    # Delta parcial
    {
        "type": "conversation.item.input_audio_transcription.delta",
        "delta": "Esto es una"
    },
    # Acumulación de respuesta
    {
        "type": "response.output_text.delta",
        "delta": "fragmento de texto",
        "response_id": "resp_001"
    },
    # Fin de respuesta
    {
        "type": "response.completed",
        "response": {"id": "resp_001"}
    },
]
```

**Helper `create_runner()`:**
```python
def create_runner(input_simulator, **kwargs):
    from dictatux.engines.openai.controller import OpenAIRealtimeProcessRunner
    mock_controller = MagicMock()
    mock_controller._stop_event = MagicMock()

    runner = OpenAIRealtimeProcessRunner(
        controller=mock_controller,
        api_key="fake-key",
        model="gpt-4o-transcribe",
        language="es",
        sample_rate=24000,
        channels=1,
        use_partials=kwargs.get("use_partials", False),
        input_simulator=input_simulator,
    )

    runner._ws = MagicMock()
    runner._connected = True
    return runner
```

**Invocación:**
```python
import json
for msg in REAL_WEBSOCKET_MESSAGES:
    runner._on_message(runner._ws, json.dumps(msg))
assert mock.text == "Esto es una prueba de dictado."
```

### 6.2 Whisper Docker — `test_whisper_docker_transcription.py`

**Patrón:** Mockear `requests.post` para devolver respuestas JSON pre-grabadas. Instanciar `WhisperDockerProcessRunner` con dependencias mockeadas. Llamar a `_process_audio_chunk()` o `_transcribe_audio()` directamente.

```python
# Ejemplo de respuesta REST real
REAL_API_RESPONSE = {"text": "Esto es una prueba de dictado."}

# Audio simulado (bytes aleatorios con nivel configurable)
def make_audio_chunk(level=1000, duration_samples=16000):
    """Genera un chunk de audio con nivel RMS controlado."""
    import struct
    return struct.pack(f"<{duration_samples}h",
                       *[level] * duration_samples)
```

**Helper `create_runner()`:**
```python
def create_runner(input_simulator, **kwargs):
    from dictatux.engines.whisper.controller import WhisperDockerProcessRunner
    mock_controller = MagicMock()
    mock_controller._stop_event = MagicMock()

    runner = WhisperDockerProcessRunner(
        controller=mock_controller,
        container_name="test-whisper",
        api_port=9000,
        model="base",
        language="es",
        chunk_duration=5.0,
        sample_rate=16000,
        channels=1,
        vad_enabled=kwargs.get("vad_enabled", False),
        vad_threshold=kwargs.get("vad_threshold", 500.0),
        input_simulator=input_simulator,
    )
    return runner
```

**Invocación:**
```python
with patch("dictatux.engines.whisper.controller.requests") as mock_requests:
    mock_response = MagicMock()
    mock_response.json.return_value = REAL_API_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_requests.post.return_value = mock_response

    runner._process_audio_chunk(audio_chunk)
    assert mock.text == "Esto es una prueba de dictado."
```

### 6.3 Vosk Local — `test_vosk_transcription.py`

**Patrón:** Cargar el modelo real de `tests/fixtures/vosk-model-small-en-us-0.15/`. Leer audio WAV pre-grabado. Llamar a `backend.transcribe(audio_bytes)`. Comparar el resultado.

```python
@pytest.mark.slow
def test_vosk_transcribes_english_audio():
    backend = VoskInferenceBackend()
    model_path = "tests/fixtures/vosk-model-small-en-us-0.15"
    backend.load_model(model_path, sample_rate=16000)

    audio_bytes = load_wav_as_pcm("tests/fixtures/audio/hello_world.wav")
    result = backend.transcribe(audio_bytes)

    assert "hello" in result.lower()
    backend.unload_model()
```

### 6.4 Whisper Local — `test_whisper_local_transcription.py`

**Patrón:** Mockear `faster_whisper.WhisperModel.transcribe()` para devolver segmentos controlados. Verificar post-procesamiento.

```python
# Segmentos simulados con diferentes probabilidades de no-speech
MOCK_SEGMENTS = [
    FakeSegment(text=" Esto es real.", no_speech_prob=0.1, start=0.0, end=1.5),
    FakeSegment(text=" Gracias por ver.", no_speech_prob=0.9, start=1.5, end=3.0),  # alucinación
    FakeSegment(text=" Fin del dictado.", no_speech_prob=0.2, start=3.0, end=4.0),
]
# Esperado: "Esto es real. Fin del dictado." (segundo segmento filtrado)
```

---

## 7. Fixtures de Audio

### 7.1 Para motores remotos (Google, OpenAI, Whisper Docker)

**No se necesitan archivos de audio.** Los tests operan a nivel de respuestas de API: JSON, mensajes WebSocket o respuestas HTTP. El audio ya fue procesado por el servicio remoto; lo que testeamos es cómo nuestro código interpreta esas respuestas.

### 7.2 Para Vosk Local (modelo real)

Se necesitan archivos de audio WAV cortos (< 5 segundos, 16kHz, mono, PCM 16-bit):

| Fixture | Contenido | Propósito |
|---------|-----------|-----------|
| `hello_world.wav` | "hello world" en inglés | Test básico con modelo existente |
| `silence.wav` | Silencio (2 segundos) | Verificar cadena vacía |
| `numbers.wav` | "one two three four five" | Test de números |

**Ubicación:** `tests/fixtures/audio/`

**Generación:** Se pueden generar con `espeak-ng` + `ffmpeg` o grabar manualmente. Incluir un script helper:

```bash
# generate_fixtures.sh
espeak-ng "hello world" --stdout | \
    ffmpeg -i - -ar 16000 -ac 1 -f wav tests/fixtures/audio/hello_world.wav
```

### 7.3 Para Whisper Local (modelo mockeado)

**No se necesitan archivos de audio.** El modelo está mockeado; se pasan bytes arbitrarios. Lo que testeamos es el post-procesamiento de los segmentos que devuelve el modelo.

---

## 8. Estructura de Archivos

```
tests/
├── helpers.py                              # (existente) + añadir calculate_wer()
├── fixtures/
│   ├── vosk-model-small-en-us-0.15/        # (existente)
│   └── audio/                              # NUEVO — audio WAV para Vosk
│       ├── hello_world.wav
│       ├── silence.wav
│       └── numbers.wav
└── engines/
    ├── test_google_cloud_integration.py    # (existente) — ya cubre _response_loop()
    ├── test_openai_transcription.py        # NUEVO — cubre _on_message()
    ├── test_whisper_docker_transcription.py # NUEVO — cubre _process_audio_chunk()
    ├── test_vosk_transcription.py          # NUEVO — cubre VoskInferenceBackend
    └── test_whisper_local_transcription.py # NUEVO — cubre WhisperInferenceBackend
```

Total: **4 archivos de test nuevos** + ampliación de `helpers.py` + fixtures de audio.

---

## 9. Datos Reales a Capturar

Antes de implementar los tests de OpenAI y Whisper Docker, se necesita capturar datos reales de sesiones de dictado. El procedimiento:

1. **Activar logging DEBUG** en los controladores de cada motor
2. **Realizar una sesión de dictado** de ~15 segundos en español
3. **Extraer los mensajes/respuestas** del log
4. **Trasladarlos a constantes** en el archivo de test (como `REAL_API_RESPONSES` en el test de Google)

### Datos ya disponibles

| Motor | Datos reales | Fuente |
|-------|-------------|--------|
| Google Cloud | ✅ 5 respuestas (3 interim + 2 final) | `test_google_cloud_integration.py` |
| OpenAI Realtime | ❌ Por capturar | Sesión de dictado con logging |
| Whisper Docker | ❌ Por capturar | Sesión de dictado con logging |
| Vosk Local | ✅ Modelo real disponible | `tests/fixtures/vosk-model-small-en-us-0.15/` |
| Whisper Local | N/A (mock) | No aplica |

---

## 10. Dependencia Nueva

| Dependencia | Versión | Propósito | Cómo añadir |
|-------------|---------|-----------|-------------|
| `jiwer` | >= 3.0 | Cálculo opcional de WER | Añadir a `[dependency-groups] dev` en `pyproject.toml` |

```toml
[dependency-groups]
dev = [
    "pytest>=7.4.4",
    "pytest-qt>=4.2.0",
    "numpy",
    "jiwer>=3.0",
]
```

---

## 11. Plan de Implementación

### Fase 1: Utilidad WER + Fixtures de Audio

**Duración estimada:** 1 sesión

- [ ] Añadir `jiwer` a `pyproject.toml` en `[dependency-groups] dev`
- [ ] Añadir `calculate_wer()` y `normalize_text()` a `tests/helpers.py`
- [ ] Tests unitarios para `calculate_wer()`
- [ ] Generar fixtures de audio WAV para Vosk (`hello_world.wav`, `silence.wav`, `numbers.wav`)

### Fase 2: Tests OpenAI Realtime

**Duración estimada:** 1–2 sesiones

- [ ] Capturar datos reales de una sesión WebSocket con logging DEBUG
- [ ] Crear `tests/engines/test_openai_transcription.py`
- [ ] Implementar `create_runner()` helper
- [ ] Tests para cada tipo de mensaje (`completed`, `delta`, `error`)
- [ ] Tests de modo partials (`use_partials=True`)

### Fase 3: Tests Whisper Docker

**Duración estimada:** 1 sesión

- [ ] Capturar respuestas REST reales con logging DEBUG
- [ ] Crear `tests/engines/test_whisper_docker_transcription.py`
- [ ] Implementar `create_runner()` helper
- [ ] Tests de `_process_audio_chunk()` con mock de `requests.post`
- [ ] Tests de VAD client-side (audio silencioso vs. con voz)
- [ ] Tests de retry en fallo HTTP

### Fase 4: Tests Vosk Local con Modelo Real

**Duración estimada:** 1 sesión

- [ ] Crear `tests/engines/test_vosk_transcription.py`
- [ ] Tests con `VoskInferenceBackend` + modelo real + audio WAV
- [ ] Tests de streaming con resultados parciales
- [ ] Tests de ciclo de vida (`load_model` / `unload_model`)
- [ ] Marcar con `@pytest.mark.slow`

### Fase 5: Tests Whisper Local Post-procesamiento

**Duración estimada:** 1 sesión

- [ ] Crear `tests/engines/test_whisper_local_transcription.py`
- [ ] Definir `FakeSegment` dataclass para simular segmentos de `faster-whisper`
- [ ] Tests de filtrado de alucinaciones
- [ ] Tests de concatenación de segmentos
- [ ] Tests de gestión de contexto (`ContextManager`)

---

## 12. Criterios de Aceptación Final

- [ ] Los 4 motores sin tests de transcripción ahora tienen cobertura
- [ ] Todos los tests pasan con `uv run python -m pytest tests/engines/`
- [ ] Los tests de motores remotos (OpenAI, Whisper Docker) usan datos capturados de sesiones reales
- [ ] Los tests se ejecutan en < 10 segundos (excluyendo los marcados `@pytest.mark.slow`)
- [ ] Ningún test requiere internet, credenciales, Docker ni modelos adicionales
- [ ] `calculate_wer()` disponible en `tests/helpers.py` para uso futuro
- [ ] El patrón de cada test file es coherente con `test_google_cloud_integration.py`

---

## 13. Qué NO incluye esta iteración

| Elemento | Razón de exclusión | Cuándo considerarlo |
|----------|-------------------|---------------------|
| Clase base abstracta `IntegrationTestBase` | Los motores son demasiado diferentes; abstraer ahora sería prematuro | Cuando haya ≥ 3 tests por motor con patrones claros a extraer |
| `FixtureProvider` por motor | Over-engineering para la cantidad actual de fixtures | Cuando haya > 10 fixtures por motor |
| Fixtures de repositorios públicos externos | Las fuentes identificadas no encajan bien con nuestros formatos | Cuando se necesiten datasets de evaluación masivos |
| Tests con modelos Whisper reales | Modelos demasiado pesados (75MB–3GB) para CI | Como tests manuales opcionales en el futuro |
| Directorio `tests/integration/` separado | Rompe la convención actual de `tests/engines/` | Si la cantidad de tests justifica la separación |
| `conftest.py` | El proyecto no usa `conftest.py`; los helpers están en `tests/helpers.py` | Migración global del proyecto a `conftest.py` |
| Tests de audio en español | Requiere modelo Vosk en español (no incluido) | Cuando se añada un modelo español a fixtures |

---

## 14. Riesgos y Mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|--------|-------|---------|------------|
| Datos WebSocket de OpenAI cambian de formato entre versiones | Media | Alto | Fijar versión de API en los datos de test; documentar la versión usada |
| El modelo Vosk small produce resultados inestables | Baja | Medio | Usar asserts flexibles (`"hello" in result.lower()`) en lugar de texto exacto |
| `_on_message` y `_process_audio_chunk` tienen dependencias internas difíciles de mockear | Media | Medio | Inspeccionar cada método antes de implementar; ajustar helpers según sea necesario |
| `jiwer` introduce conflictos de dependencias | Baja | Bajo | Es una dependencia solo de dev, sin dependencias transitivas pesadas |

---

## 15. Referencias

- **Patrón de referencia:** `tests/engines/test_google_cloud_integration.py`
- **Helpers compartidos:** `tests/helpers.py` — `MockInputSimulator`
- **jiwer:** https://github.com/jitsi/jiwer
- **OpenAI Realtime API Events:** https://platform.openai.com/docs/api-reference/realtime
- **Whisper ASR Webservice API:** https://github.com/ahmetoner/whisper-asr-webservice