# HDR — Melhorias Pendentes

## Contexto

A integracao do HDR dentro do `captureLoop` (Opcao B) foi implementada com sucesso. O streaming normal funciona bem e sem interferencia. No entanto, caso o HDR venha a ser ativado (via `/expositionMode/hdr`), existem alguns problemas que devem ser corrigidos.

---

## 1. Ultimo frame do HDR nunca e capturado (BUG)

**Ficheiro:** `CameraOptions.py`, funcao `processHDR()`

**Problema:** A logica atual faz isto:
- hdrIndex=0: define exposure=200, **nao guarda** o frame (correto, descarta o frame antigo)
- hdrIndex=1: define exposure=675, guarda o frame capturado a **200**
- hdrIndex=2: define exposure=1150, guarda o frame capturado a **675**
- ...
- hdrIndex=8: define exposure=4000, guarda o frame capturado a **3525**
- hdrIndex=9 (>= len): processa o HDR

O frame a **4000 de exposure nunca e capturado**. O HDR e processado sem o frame de maior exposicao.

**Solucao:** Separar o momento de "guardar frame" do momento de "avancar exposure". O frame deve ser guardado ANTES de mudar o exposure para o proximo valor.

```python
def processHDR(colorToDepthFrame, depthFrame, colorFrame):
    global colorArray, depthArray

    # Guardar o frame atual (exceto o primeiro, que foi capturado antes do HDR)
    if camState.hdrIndex > 0:
        colorArray.append(colorToDepthFrame)
        depthArray.append(depthFrame)
        frameState.colorFrameHDR = colorFrame

    # Verificar se ja temos todos os frames
    if camState.hdrIndex >= len(camState.hdrExposures):
        # HDR COLOR
        stacked = numpy.stack(colorArray, axis=0).astype(numpy.float32)
        mask = stacked > 0
        stacked[~mask] = 0
        count = mask.sum(axis=0).clip(min=1)
        hdrColor = (stacked.sum(axis=0) / count).astype(numpy.uint8)

        frameState.colorToDepthFrameHDR = hdrColor

        # HDR DEPTH
        stacked_d = numpy.stack(depthArray, axis=0).astype(numpy.float32)
        mask_d = (stacked_d > 150) & (stacked_d <= 5000)
        stacked_d[~mask_d] = numpy.nan
        hdrDepth = numpy.nanmedian(stacked_d, axis=0)
        hdrDepth = numpy.nan_to_num(hdrDepth, nan=0).astype(numpy.uint16)

        frameState.depthFrameHDR = hdrDepth

        print("HDR Processed")

        # Reset para proximo ciclo
        camState.hdrIndex = 0
        colorArray = []
        depthArray = []
        return

    # Definir exposure para o PROXIMO frame
    exposure = camState.hdrExposures[camState.hdrIndex]
    camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exposure))
    camState.hdrIndex += 1
```

Com esta logica:
- hdrIndex=0: define exposure=200, nao guarda (correto), incrementa para 1
- hdrIndex=1: guarda frame a 200, define exposure=675, incrementa para 2
- ...
- hdrIndex=8: guarda frame a 3525, define exposure=4000, incrementa para 9
- hdrIndex=9: guarda frame a **4000**, processa HDR, reset

Agora todos os 9 exposures sao capturados.

---

## 2. Lock nao esta a ser usado (THREAD SAFETY)

**Ficheiro:** `CameraState.py` (linha 27) e `CameraOptions.py`

**Problema:** O `camState._lock` e criado mas nunca utilizado. O `captureLoop` escreve em `frameState` e os endpoints da API leem `frameState` de threads diferentes (uvicorn). Em Python com GIL isto raramente causa crashes, mas pode servir frames parcialmente atualizados (ex: `colorFrame` de um instante e `depthFrame` de outro).

**Solucao:** Proteger a escrita e leitura dos frames com o lock.

No `captureLoop`:
```python
if hasColorToDepth == 1 and hasDepth == 1 and hasColor == 1:
    with camState._lock:
        frameState.colorToDepthFrame = colorToDepthFrame
        frameState.depthFrame = depthFrame
        frameState.colorFrame = colorFrame
```

Nos endpoints da API que leem frames, exemplo:
```python
with camState._lock:
    frame = frameState.depthFrame
if frame is None:
    return ...
```

---

## 3. Variaveis globais sem protecao (ROBUSTEZ)

**Ficheiro:** `CameraOptions.py` (linhas 14-15)

**Problema:** `colorArray` e `depthArray` sao globais de modulo. Se ocorrer uma excecao durante o `processHDR`, os arrays nunca sao limpos e o proximo ciclo HDR vai ter dados corrompidos.

**Solucao:** Mover para `CameraState` e limpar em caso de erro.

Em `CameraState.py`:
```python
self.hdrColorArray = []
self.hdrDepthArray = []
```

No `processHDR`, usar `camState.hdrColorArray` e `camState.hdrDepthArray` em vez de globais.

No `captureLoop`, envolver o processHDR num try:
```python
if camState.hdrEnabled:
    try:
        processHDR(colorToDepthFrame, depthFrame, colorFrame)
    except Exception as e:
        print(f"HDR error: {e}")
        camState.hdrIndex = 0
        camState.hdrColorArray = []
        camState.hdrDepthArray = []
```

---

## 4. Limpar dead code (LIMPEZA)

**Ficheiro:** `HDRDef.py` (329 linhas)

**Problema:** O ficheiro contem 3 funcoes antigas (`hdr`, `hdrAPI`, `hdrAPI2`) que ja nao sao usadas. O HDR agora corre dentro do `captureLoop` via `processHDR()`.

**Solucao:** Apagar o ficheiro `HDRDef.py` ou, se quiser manter como referencia, renomear para `HDRDef_old.py`.

---

## Resumo de prioridades

| # | Problema | Impacto | Dificuldade |
|---|----------|---------|-------------|
| 1 | Frame a 4000 nunca capturado | HDR incompleto, pior qualidade | Facil |
| 2 | Lock nao usado | Frames inconsistentes na API | Facil |
| 3 | Globais sem protecao | HDR pode ficar preso se houver erro | Facil |
| 4 | Dead code HDRDef.py | Confusao, manutencao mais dificil | Trivial |
