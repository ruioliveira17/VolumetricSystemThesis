# HDR em Streaming — Problemas e Solucao

## Resumo

O HDR foi implementado de forma que entra em conflito com o loop de captura (`captureLoop`) que corre numa thread separada. O resultado e que ambos competem pelo controlo da camara e pela escrita dos frames, causando race conditions, dados corrompidos e comportamento imprevisivel.

---

## Problemas Identificados

### 1. Race Condition entre `captureLoop` e `hdrAPI` (CRITICO)

O `captureLoop()` em `CameraOptions.py` corre numa thread em background, continuamente a:
- Chamar `VZ_GetFrame` para obter frames
- Escrever em `frameState.colorToDepthFrame`, `frameState.depthFrame`, `frameState.colorFrame`

Quando o HDR e chamado (`hdrAPI()` em `HDRDef.py`), este tambem:
- Chama `VZ_SetExposureTime` para mudar o exposure (200, 675, 1150, ...)
- Chama `getFrame()` que internamente faz `VZ_GetFrame`
- Le e escreve em `frameState`

**Resultado:** Ambas as threads competem pela API da camara e pelo estado partilhado sem qualquer sincronizacao. A API da camara provavelmente nao e thread-safe, e os dados em `frameState` podem ser sobrescritos a meio de uma operacao.

### 2. Lock existe mas nao e usado

Em `CameraState.py`, o `camState._lock` e criado:

```python
self._lock = threading.Lock()
```

Mas **nunca e utilizado** no `captureLoop` nem nas funcoes HDR para proteger o acesso a `frameState` ou a camara.

Alem disso, as funcoes `getRGB()` e `getDepth()` em `CameraOptions.py` usam o lock mas referenciam atributos que nao existem:

```python
def getRGB():
    with camState._lock:
        return frameState.colorFrame.copy() if camState._rgb_frame is not None else None
                                                # ^^^ _rgb_frame NAO EXISTE em CameraState!
```

Isto vai dar `AttributeError` quando chamado.

### 3. `hdrAPI()` ignora o retorno do `getFrame()`

Em `HDRDef.py`, linhas 264-267:

```python
getFrame(camState.camera)                          # retorno ignorado!
colorToDepthFrame = frameState.colorToDepthFrame   # le do state global
depthFrame = frameState.depthFrame
colorFrame = frameState.colorFrame
```

O `getFrame()` escreve em `frameState`, mas entre essa escrita e a leitura nas linhas seguintes, o `captureLoop` pode ter sobrescrito os valores com um frame capturado a um exposure diferente do pretendido para o HDR.

### 4. `captureLoop` nao para durante o HDR

Nao existe nenhum mecanismo para pausar a thread de captura. O HDR precisa de controlo exclusivo da camara para alterar o exposure e capturar frames a diferentes niveis, mas a thread de streaming continua a correr e a interferir.

### 5. Problemas menores

- **Import desnecessario:** `from pickle import FALSE, TRUE` — `False` e `True` sao built-ins do Python, nao precisam de import.
- **Codigo duplicado:** `openCamera()` e `startCamera()` sao ~90% identicos. `hdr()`, `hdrAPI()` e `hdrAPI2()` sao 3 versoes do mesmo codigo com diferencas minimas.
- **`getFrame()` nao retorna valores em `hdrAPI()`:** A funcao `getFrame()` escreve em `frameState` mas nao retorna nada (retorna `None` implicitamente). Em `hdrAPI()` isso funciona por acidente porque o codigo le de `frameState`, mas em `hdrAPI2()` tenta usar o retorno diretamente — comportamento inconsistente.

---

## Solucao Proposta

### Opcao A: Parar o streaming durante o HDR (mais simples)

A ideia e: antes de fazer HDR, parar o `captureLoop`, fazer o HDR com controlo exclusivo, e depois reiniciar o loop.

```python
# Em CameraOptions.py — adicionar funcao de pausa/retoma

def pauseCapture():
    """Para o captureLoop sem fechar a camara."""
    camState._running = False
    if camState._thread:
        camState._thread.join(timeout=3)
        camState._thread = None

def resumeCapture():
    """Reinicia o captureLoop."""
    if not camState._running:
        camState._running = True
        camState._thread = threading.Thread(target=captureLoop, daemon=True)
        camState._thread.start()
```

```python
# Em HDRDef.py — modificar hdrAPI para usar pausa

from CameraOptions import pauseCapture, resumeCapture

def hdrAPI():
    print("HDR API Called!")

    # 1. Parar o streaming
    pauseCapture()

    exposureTime = 200
    hasDepthArray = []
    hasColorArray = []
    exposureTimeArray = []
    firstFrame = True

    try:
        while exposureTime <= 4000:
            # 2. Mudar exposure com controlo exclusivo
            camState.camera.VZ_SetExposureTime(
                VzSensorType.VzToFSensor, c_int32(exposureTime)
            )
            time.sleep(0.15)  # dar tempo a camara para aplicar

            # 3. Capturar frame diretamente (sem captureLoop a interferir)
            colorToDepthFrame, depthFrame, colorFrame = getFrameDirect(camState.camera)

            if colorToDepthFrame is None or depthFrame is None:
                continue

            ret_code, exposureStruct = camState.camera.VZ_GetExposureTime(
                VzSensorType.VzToFSensor
            )

            if exposureStruct.exposureTime == exposureTime:
                if firstFrame:
                    firstFrame = False
                else:
                    hasColorArray.append(cv2.resize(colorToDepthFrame, (640, 480)))
                    hasDepthArray.append(cv2.resize(depthFrame, (640, 480)))
                    exposureTimeArray.append(exposureTime / 1e6)

                exposureTime += 475

        # 4. Processar HDR
        if hasColorArray and hasDepthArray:
            # Color HDR
            stacked = numpy.stack(hasColorArray, axis=-1)
            mask_valid = stacked > 0
            hdrColor = numpy.sum(stacked * mask_valid, axis=-1) / numpy.maximum(
                numpy.sum(mask_valid, axis=-1), 1
            )
            hdrColor = hdrColor.astype(numpy.uint8)

            # Depth HDR
            mask_valid = [(f > 0) & (f <= 5000) for f in hasDepthArray]
            stacked = numpy.stack(hasDepthArray, axis=-1).astype(numpy.float32)
            stacked_mask = numpy.stack(mask_valid, axis=-1).astype(numpy.float32)
            count_valid = numpy.sum(stacked_mask, axis=-1)
            count_valid[count_valid == 0] = 1
            hdrDepth = (numpy.sum(stacked * stacked_mask, axis=-1) / count_valid)
            hdrDepth = hdrDepth.astype(numpy.uint16)

            # Guardar resultado
            frameState.colorToDepthFrameHDR = hdrColor
            frameState.depthFrameHDR = hdrDepth
            frameState.colorFrameHDR = colorFrame
            print("HDR Processed")

    except Exception as e:
        print(f"HDR error: {e}")
    finally:
        # 5. Restaurar exposure normal e reiniciar streaming
        camState.camera.VZ_SetExposureTime(
            VzSensorType.VzToFSensor, c_int32(camState.exposureTime)
        )
        resumeCapture()
        print("HDR end")
```

```python
# Em GetFrame.py — adicionar versao que retorna diretamente sem escrever no state

def getFrameDirect(camera):
    """Retorna (colorToDepth, depth, color) diretamente, sem tocar no frameState."""
    ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
    if ret != 0:
        return None, None, None

    colorToDepthFrame = None
    depthFrame = None
    colorFrame = None

    if frameready.color:
        ret, rgbframe = camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
        if ret == 0:
            frametmp = numpy.ctypeslib.as_array(
                rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3)
            )
            frametmp.dtype = numpy.uint8
            frametmp.shape = (rgbframe.height, rgbframe.width, 3)
            colorToDepthFrame = frametmp.copy()

    if frameready.depth:
        ret, depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
        if ret == 0:
            frametmp = numpy.ctypeslib.as_array(
                depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2)
            )
            frametmp.dtype = numpy.uint16
            frametmp.shape = (depthframe.height, depthframe.width)
            depthFrame = frametmp.copy()

    if frameready.color:
        ret, colorframe = camera.VZ_GetFrame(VzFrameType.VzColorFrame)
        if ret == 0:
            frametmp = numpy.ctypeslib.as_array(
                colorframe.pFrameData, (1, colorframe.width * colorframe.height * 3)
            )
            frametmp.dtype = numpy.uint8
            frametmp.shape = (colorframe.height, colorframe.width, 3)
            colorFrame = frametmp.copy()

    return colorToDepthFrame, depthFrame, colorFrame
```

### Opcao B: Integrar HDR dentro do `captureLoop` (mais robusto)

Em vez de ter uma funcao separada, o proprio `captureLoop` detecta quando o HDR e pedido e executa-o internamente. Assim nunca ha duas threads a aceder a camara.

```python
# Em CameraState.py — adicionar flags HDR

class CameraState:
    def __init__(self):
        # ... campos existentes ...
        self.hdr_requested = False
        self.hdr_in_progress = False
```

```python
# Em CameraOptions.py — modificar captureLoop

def captureLoop():
    while camState._running:
        if camState.hdr_requested:
            camState.hdr_requested = False
            camState.hdr_in_progress = True
            runHDRSequence()  # funcao HDR que corre na mesma thread
            camState.hdr_in_progress = False
            continue

        # ... captura normal existente ...
```

Esta opcao e melhor a longo prazo porque garante que so uma thread acede a camara, mas requer mais refactoring.

---

## Recomendacao

Comecar pela **Opcao A** porque e a mudanca minima para resolver o problema. Se no futuro houver necessidade de fazer HDR sem interromper visivelmente o streaming (ex: transicao mais suave), migrar para a **Opcao B**.

Em ambos os casos, corrigir tambem:
- Remover `from pickle import FALSE, TRUE`
- Corrigir `getRGB()` e `getDepth()` para referenciar os atributos corretos
- Consolidar as 3 versoes de HDR (`hdr`, `hdrAPI`, `hdrAPI2`) numa so
