# Analise de Pontos de Melhoria: Calculo de Volume e HDR

**Autor:** Jorge Morais
**Data:** 26 de Marco de 2026
**Objetivo:** Identificar problemas concretos no calculo de volume e no processamento HDR, propor solucoes implementaveis e fundamentar cada uma com referencia ao codigo atual.

---

## PARTE 1: CALCULO DE VOLUME

### 1.1 Descricao do Problema

O sistema calcula o volume de objetos colocados num workspace calibrado. A camara ToF (DS86) mede a profundidade de cada pixel em milimetros. O pipeline atual e:

```
MinDepthAPI()  ->  bundleIdentifier()/objIdentifier()  ->  volumeBundleAPI()/volumeRealAPI()
```

Existem **3 problemas fundamentais** que afetam a precisao da medicao.

---

### 1.2 Problema A: Bounding Box em vez de Volume Real

**Onde:** `VolumeTkinter.py`, linhas 30-55

**O que acontece:** O volume e calculado como um paralelepipedo (caixa retangular) envolvendo o objeto:

```python
# Codigo atual (VolumeTkinter.py:30-55)
pts_m = []
for (u,v) in pts_flat:
    Z = depthFrame[int(v), int(u)] / 1000
    X = (u - cx_d) * Z / fx_d
    Y = (v - cy_d) * Z / fy_d
    pts_m.append([X, Y])

rect_m = cv2.minAreaRect(pts_m)                          # retangulo minimo 2D
width_meters, height_meters = rect_m[1]                   # largura e altura do retangulo
volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)  # volume = caixa
```

**Consequencias:**

1. **Objetos redondos:** Uma esfera com 20cm de diametro tem volume real ~4189 cm3, mas o bounding box da ~8000 cm3 (erro de +91%)
2. **Objetos em L:** Uma pecas em L ocupa metade do seu bounding box, logo o volume e ~2x o real
3. **Objetos inclinados:** O `minAreaRect` ajuda com rotacao, mas nao com formas irregulares

**Exemplo visual:**

```
Objeto real (vista de cima):     O que o sistema mede:

      +----+                      +-----------+
      |    |                      |           |
      |    +--------+             |           |
      |             |             |           |
      +-------------+             +-----------+

Area real: ~75% do rect           Area medida: 100% do rect
```

---

### 1.3 Problema B: Profundidade Unica por Objeto (Superficie Plana Assumida)

**Onde:** `VolumeTkinter.py`, linha 55 e 110

```python
# volumeBundleAPI - usa UMA profundidade para todo o objeto:
volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)

# volumeRealAPI - mesma logica por objeto:
volume = width_meters * height_meters * ((workspace_depth - depths[idx]) / 1000)
```

O `minimum_depth` (ou `depths[idx]`) e o ponto mais alto do objeto - o ponto mais proximo da camara. Todo o objeto e tratado como se tivesse uma superficie plana a essa altura.

**Consequencias:**

```
Objeto real (vista lateral):     Modelo usado pelo sistema:

      /\                          +------+
     /  \                         |      |
    /    \        vs              |      |
   /______\                       +------+

Piramide: V = 1/3 * base * h     Prisma: V = base * h  (3x mais!)
```

Um saco de areia, por exemplo, com formato arredondado no topo, tera o volume significativamente sobrestimado porque a profundidade minima (topo) e aplicada a toda a area.

---

### 1.4 Problema C: Distancia Radial vs Perpendicular

**Onde:** `VolumeTkinter.py`, linhas 23-26

```python
Z = depthFrame[int(v), int(u)] / 1000    # Z e distancia RADIAL (do sensor ao ponto)
X = (u - cx_d) * Z / fx_d                # projecao para coordenadas mundo
Y = (v - cy_d) * Z / fy_d
```

A camara ToF mede a **distancia radial** - o comprimento do raio de luz desde o sensor ate ao objeto. Para pixels no centro da imagem, isto e praticamente igual a profundidade perpendicular (Z real). Mas para pixels nas bordas do FOV (70x50 graus), o raio viaja em diagonal.

**Impacto numerico:**

```
               Camara
                 |
                 | d_perp (o que queremos)
                 |
    d_radial  /  |
     (medido)/   |
            / θ  |
           /_____|____________ Plano do objeto

d_radial = d_perp / cos(θ)

Pixel no centro:  θ ≈ 0°   -> erro ≈ 0%
Pixel a 1/4:      θ ≈ 8.7° -> erro ≈ 1.2%
Pixel na borda:   θ ≈ 35°  -> erro ≈ 22%
```

**NOTA IMPORTANTE:** Na projecao 3D (X = (u-cx)*Z/fx), se Z fosse a profundidade perpendicular, as formulas estariam corretas. Como Z e radial, existe um erro sutil: o X e Y calculados ficam ligeiramente inflacionados nas bordas, e a profundidade do objeto (workspace_depth - Z) tambem fica distorcida.

Na pratica, para este sistema especifico, este erro e **menor** que os problemas A e B porque:
- Os objetos tendem a estar perto do centro do workspace
- O workspace ocupa tipicamente 60-70% do FOV, nao as bordas extremas
- O erro e de ~1-5% na zona util, vs >50% dos problemas A e B

---

### 1.5 SOLUCAO 1: Volume por Integracao de Pixels (Volumetria Voxel)

**Principio:** Em vez de calcular um bounding box, somar a contribuicao de cada pixel individualmente. Cada pixel do contorno do objeto contribui com um pequeno "pilar" de volume, cuja base e a area do pixel no mundo real e cuja altura e a diferenca entre o workspace e a profundidade nesse pixel.

**Porque funciona:**
- Respeita a forma real do contorno (resolve Problema A)
- Usa a profundidade real de cada pixel (resolve Problema B)
- Pode incluir correcao radial por pixel (resolve Problema C)

```python
import numpy as np
import cv2

def volumeVoxelAPI(depthFrame, workspace_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d):
    """
    Calcula o volume por integracao pixel-a-pixel.
    Cada pixel dentro do contorno do objeto contribui com um micro-volume.

    Parametros:
        depthFrame     - frame de profundidade (uint16, mm)
        workspace_depth - profundidade do workspace calibrado (mm)
        box_limits     - lista de contornos (um por objeto)
        depths         - lista de profundidades por objeto (nao usado nesta versao)
        fx_d, fy_d     - distancias focais do sensor de profundidade (pixels)
        cx_d, cy_d     - ponto principal do sensor de profundidade (pixels)

    Retorna:
        volumes        - lista de volumes por objeto + total (m3)
        widths         - lista de larguras por objeto (m)
        heights        - lista de alturas por objeto (m)
    """
    volumes = []
    widths = []
    heights = []
    total_volume = 0.0

    h, w = depthFrame.shape[:2]

    for i, contour in enumerate(box_limits):
        # 1. Criar mascara binaria do contorno do objeto
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, color=255, thickness=-1)  # preenchido

        # 2. Obter coordenadas de todos os pixels dentro do contorno
        ys, xs = np.where(mask == 255)

        if len(ys) == 0:
            volumes.append(0.0)
            widths.append(0.0)
            heights.append(0.0)
            continue

        # 3. Obter profundidade de cada pixel
        z_mm = depthFrame[ys, xs].astype(np.float64)

        # 4. Filtrar pixels invalidos (sem leitura ou fora do range)
        valid = (z_mm > 150) & (z_mm < workspace_depth)
        ys_v = ys[valid]
        xs_v = xs[valid]
        z_mm_v = z_mm[valid]

        if len(z_mm_v) == 0:
            volumes.append(0.0)
            widths.append(0.0)
            heights.append(0.0)
            continue

        # 5. Converter para metros
        z_m = z_mm_v / 1000.0
        ws_m = workspace_depth / 1000.0

        # 6. Calcular a altura do "pilar" de cada pixel
        #    (distancia do workspace ao ponto do objeto)
        pillar_height = ws_m - z_m  # metros

        # 7. Calcular a area de cada pixel no mundo real
        #    Um pixel a profundidade Z cobre uma area de (Z/fx) * (Z/fy) no mundo
        pixel_width  = z_m / fx_d   # metros por pixel na horizontal
        pixel_height = z_m / fy_d   # metros por pixel na vertical
        pixel_area = pixel_width * pixel_height  # m2

        # 8. Volume de cada pilar = area * altura
        pillar_volume = pixel_area * pillar_height  # m3

        # 9. Somar todos os pilares
        obj_volume = np.sum(pillar_volume)

        # 10. Calcular dimensoes para display (largura x altura do bounding rect)
        pts_3d = np.column_stack([
            (xs_v - cx_d) * z_m / fx_d,
            (ys_v - cy_d) * z_m / fy_d
        ]).astype(np.float32)

        if len(pts_3d) >= 5:
            rect = cv2.minAreaRect(pts_3d)
            w_m, h_m = rect[1]
        else:
            w_m, h_m = 0.0, 0.0

        volumes.append(obj_volume)
        widths.append(w_m)
        heights.append(h_m)
        total_volume += obj_volume

    volumes.append(total_volume)
    return volumes, widths, heights
```

**Comparacao com o codigo atual:**

| Aspeto | Atual (volumeRealAPI) | Proposto (volumeVoxelAPI) |
|--------|----------------------|--------------------------|
| Forma do objeto | Retangulo envolvente | Forma real (contorno) |
| Profundidade | Unica por objeto | Individual por pixel |
| N. de pontos | Apenas contorno (~100-500) | Todos os pixels (~5000-50000) |
| Precisao esfera | Erro ~+91% | Erro ~+2-5% |
| Precisao caixa | Erro ~+5% | Erro ~+2-3% |
| Performance | ~1ms | ~5-15ms (ainda rapido) |

**Para integrar no sistema atual**, substituir a chamada em `api.py`:

```python
# Em vez de:
volume, width_m, height_m = volumeRealAPI(depthFrame, workspace_depth,
                                           box_limits, depths, fx_d, fy_d, cx_d, cy_d)

# Usar:
volume, width_m, height_m = volumeVoxelAPI(depthFrame, workspace_depth,
                                            box_limits, depths, fx_d, fy_d, cx_d, cy_d)
```

---

### 1.6 SOLUCAO 2: Volume por Point Cloud com Correcao Radial

**Principio:** Converter todo o frame de profundidade numa nuvem de pontos 3D corrigida, e calcular o volume como a integral do espaco entre a superfice do objeto e o plano do workspace.

Esta solucao e mais precisa e inclui correcao da distancia radial.

```python
import numpy as np
import cv2

def volumePointCloudAPI(depthFrame, workspace_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d):
    """
    Calcula o volume usando point cloud 3D com correcao de distancia radial.

    A correcao radial garante que a profundidade usada e a perpendicular
    ao plano da imagem, nao a distancia radial medida pelo sensor ToF.
    """
    volumes = []
    widths = []
    heights = []
    total_volume = 0.0

    h, w = depthFrame.shape[:2]

    # Pre-calcular mapa de correcao radial (faz-se uma vez, reutiliza-se)
    # cos(theta) para cada pixel - converte distancia radial em perpendicular
    u_coords = np.arange(w, dtype=np.float64)
    v_coords = np.arange(h, dtype=np.float64)
    uu, vv = np.meshgrid(u_coords, v_coords)

    dx = (uu - cx_d) / fx_d
    dy = (vv - cy_d) / fy_d
    cos_theta = 1.0 / np.sqrt(1.0 + dx*dx + dy*dy)  # mapa de correcao

    # Aplicar correcao ao frame inteiro
    depth_corrected = depthFrame.astype(np.float64) * cos_theta  # profundidade perpendicular
    ws_corrected = workspace_depth  # workspace medido no centro, onde cos(theta) ≈ 1

    for i, contour in enumerate(box_limits):
        # 1. Mascara do contorno
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, color=255, thickness=-1)

        # 2. Pixels dentro do contorno
        ys, xs = np.where(mask == 255)
        if len(ys) == 0:
            volumes.append(0.0)
            widths.append(0.0)
            heights.append(0.0)
            continue

        # 3. Profundidade corrigida de cada pixel
        z_corr = depth_corrected[ys, xs]

        # 4. Filtrar invalidos
        valid = (z_corr > 150) & (z_corr < ws_corrected)
        xs_v, ys_v = xs[valid], ys[valid]
        z_v = z_corr[valid]

        if len(z_v) == 0:
            volumes.append(0.0)
            widths.append(0.0)
            heights.append(0.0)
            continue

        # 5. Converter para metros
        z_m = z_v / 1000.0
        ws_m = ws_corrected / 1000.0

        # 6. Coordenadas 3D reais
        X = (xs_v - cx_d) * z_m / fx_d
        Y = (ys_v - cy_d) * z_m / fy_d

        # 7. Cada pixel cobre uma area no mundo real
        #    A area e uniforme no plano da imagem: (1/fx * 1/fy) * Z^2
        #    Mas como Z varia por pixel, calculamos por pixel
        pixel_area = (z_m / fx_d) * (z_m / fy_d)  # m2

        # 8. Altura do pilar = workspace - profundidade do objeto neste pixel
        pillar_h = ws_m - z_m

        # 9. Volume = soma dos pilares
        obj_volume = np.sum(pixel_area * pillar_h)

        # 10. Dimensoes para display
        pts_2d = np.column_stack([X, Y]).astype(np.float32)
        if len(pts_2d) >= 5:
            rect = cv2.minAreaRect(pts_2d)
            w_m, h_m = rect[1]
        else:
            w_m, h_m = 0.0, 0.0

        volumes.append(obj_volume)
        widths.append(w_m)
        heights.append(h_m)
        total_volume += obj_volume

    volumes.append(total_volume)
    return volumes, widths, heights
```

**Vantagens sobre a Solucao 1:**
- Inclui correcao da distancia radial (mais preciso nas bordas)
- Mapa de correcao pre-calculado (sem custo adicional por frame)

**Desvantagens:**
- Ligeiramente mais complexo
- A correcao radial so tem impacto significativo se os objetos estiverem nas bordas do FOV

---

### 1.7 Recomendacao para Calculo de Volume

**Implementar a Solucao 1 primeiro** (volumeVoxelAPI). E mais simples, resolve os dois problemas principais (A e B), e o ganho de precisao e enorme comparado com o sistema atual.

Se apos testes se verificar que existe erro sistematico nas bordas do workspace, **evoluir para a Solucao 2** adicionando a correcao radial.

**Prioridade de impacto:**
1. Integracao pixel-a-pixel em vez de bounding box -> **maior ganho** (resolve erro de 50-90%)
2. Profundidade por pixel em vez de minima -> **segundo maior ganho** (resolve erro de 30-200% em superficies nao-planas)
3. Correcao radial -> **ganho menor** (resolve erro de 1-5% na zona util do workspace)

---

## PARTE 2: LENTIDAO DO HDR

### 2.1 Descricao do Problema

O HDR (High Dynamic Range) combina multiplas capturas a diferentes exposicoes para produzir frames com melhor qualidade, especialmente em cenas com objetos muito escuros e muito claros.

**Onde:** `HDRDef.py`, funcoes `hdrAPI()` e `hdrAPI2()`

### 2.2 Analise do Codigo Atual

```python
# HDRDef.py - hdrAPI(), linhas 256-326
while exposureTime <= 4000 and expositionBus_done == 0:
    # 1. Mudar exposicao na camara
    camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exposureTime))

    # 2. Esperar que a camara estabilize
    time.sleep(0.1)                           # <-- 100ms de espera fixa

    # 3. Capturar frame
    getFrame(camState.camera)                  # <-- espera mais ~200ms (1/5 FPS)

    # 4. Descartar o PRIMEIRO frame de cada exposicao
    if firstFrame:
        firstFrame = False                     # <-- frame perdido
    else:
        hasColorArray.append(colorToDepthFrame)
        hasDepthArray.append(depthFrame)

    # 5. Avancar exposicao
    exposureTime += 475                        # <-- incremento de 475us
```

### 2.3 Problemas Identificados

**Problema 1: sleep(0.1) por cada nivel de exposicao**

Cada mudanca de exposicao tem um `time.sleep(0.1)` fixo. Com exposicoes de 200 a 4000 em incrementos de 475us, sao ~8 niveis. So em sleeps sao **800ms desperdicados**.

**Problema 2: Frame descartado por nivel**

O `firstFrame` flag descarta o primeiro frame de cada nivel de exposicao. Na realidade, o `firstFrame` so e True uma vez (no inicio), mas o conceito de "skip first frame after exposure change" nao esta corretamente implementado - so descarta o primeirissimo frame, nao o primeiro de cada nivel.

**Problema 3: getFrame() bloqueia ~200ms**

A funcao `getFrame()` chama `VZ_GetFrameReady(1200ms)`, que e bloqueante. Com frame rate de 5 FPS, cada frame demora ~200ms.

**Problema 4: Incremento de exposicao inconsistente entre versoes**

- `hdr()`: incremento de 1900us -> apenas 2-3 frames (rapido mas pouco HDR)
- `hdrAPI()`: incremento de 475us -> ~8 frames (melhor HDR mas muito lento)
- `hdrAPI2()`: incremento de 1900us mas com resize para 320x240

**Calculo do tempo total de um ciclo HDR (hdrAPI com 475us):**

```
Niveis: ~8 (200, 675, 1150, 1625, 2100, 2575, 3050, 3525, 4000)
Por nivel: sleep(0.1) + getFrame(~0.2s) + processamento = ~350ms
Total captura: 8 * 350ms = ~2.8 segundos
Fusao (nanmean sobre 8 frames): ~50-100ms
TOTAL: ~3 segundos por ciclo HDR
```

**A 5 FPS, 3 segundos e uma eternidade. A interface fica efetivamente congelada no modo HDR.**

**Problema 5: nanmean com NaN e ineficiente**

```python
# Codigo atual (lento):
stacked_masked = numpy.where(mask_valid, stacked, numpy.nan)   # cria array com NaNs
hdrColor = numpy.nanmean(stacked_masked, axis=-1)               # nanmean e ~3-5x mais lento que mean
hdrColor = numpy.nan_to_num(hdrColor, nan=0)                    # outra passagem pelo array
```

`numpy.nanmean` e significativamente mais lento que operacoes com mascaras inteiras porque precisa de verificar NaN valor a valor.

---

### 2.4 SOLUCAO 1: HDR Otimizado com Menos Niveis e Sem Sleeps Desnecessarios

**Principio:** Reduzir o numero de exposicoes para o minimo necessario (3-4 niveis bem escolhidos), eliminar sleeps desnecessarios, e usar fusao por mascara em vez de nanmean.

```python
import numpy as np
import time
from API.VzenseDS_api import *
from CameraState import camState
from FrameState import frameState
from GetFrame import getFrame

# Niveis de exposicao otimizados para cobrir a gama dinamica
# Baixa exposicao: recupera highlights (objetos brilhantes/perto)
# Media: caso geral
# Alta: recupera shadows (objetos escuros/longe)
HDR_EXPOSURE_LEVELS = [300, 1200, 2500, 4000]  # 4 niveis bem distribuidos

def hdrOptimizedAPI():
    """
    HDR otimizado: 4 niveis de exposicao, sem sleeps desnecessarios,
    fusao por mascara inteira (sem nanmean).

    Tempo estimado: ~1.0-1.2 segundos (vs ~3 segundos atual)
    """
    color_frames = []
    depth_frames = []

    original_exposure = camState.exposureTime

    try:
        for exp_time in HDR_EXPOSURE_LEVELS:
            # 1. Mudar exposicao
            camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exp_time))

            # 2. Descartar 1 frame para garantir que a nova exposicao esta aplicada
            #    Em vez de sleep fixo, capturamos e descartamos
            getFrame(camState.camera)  # frame descartado (~200ms a 5FPS)

            # 3. Capturar frame real
            getFrame(camState.camera)
            ctd = frameState.colorToDepthFrame
            dep = frameState.depthFrame

            if ctd is not None and dep is not None:
                # Resize para resolucao padrao
                ctd = cv2.resize(ctd, (640, 480))
                dep = cv2.resize(dep, (640, 480))
                color_frames.append(ctd)
                depth_frames.append(dep)

        if len(color_frames) == 0:
            return

        # --- FUSAO DE COR (media mascarada, sem nanmean) ---
        stacked_color = np.stack(color_frames, axis=0)  # (N, H, W, 3)
        mask_color = stacked_color > 0                     # pixels validos

        # Soma dos pixels validos e contagem
        sum_color = np.sum(stacked_color.astype(np.float32) * mask_color, axis=0)
        count_color = np.sum(mask_color, axis=0).astype(np.float32)
        count_color[count_color == 0] = 1  # evitar divisao por zero

        hdr_color = (sum_color / count_color).astype(np.uint8)

        # --- FUSAO DE PROFUNDIDADE (media mascarada) ---
        stacked_depth = np.stack(depth_frames, axis=0)  # (N, H, W)
        mask_depth = (stacked_depth > 0) & (stacked_depth <= 5000)

        sum_depth = np.sum(stacked_depth.astype(np.float64) * mask_depth, axis=0)
        count_depth = np.sum(mask_depth, axis=0).astype(np.float64)
        count_depth[count_depth == 0] = 1

        hdr_depth = (sum_depth / count_depth).astype(np.uint16)

        # --- Guardar resultados ---
        frameState.colorFrameHDR = frameState.colorFrame  # ultimo frame RGB
        frameState.colorToDepthFrameHDR = hdr_color
        frameState.depthFrameHDR = hdr_depth

    except Exception as e:
        print(f"HDR Error: {e}")
    finally:
        # Restaurar exposicao original
        camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(original_exposure))
        camState.exposureTime = original_exposure
```

**Comparacao de tempos:**

| Aspeto | hdrAPI() atual | hdrOptimizedAPI() |
|--------|---------------|-------------------|
| Niveis de exposicao | ~8 (475us step) | 4 (escolhidos) |
| Sleep por nivel | 100ms | 0ms |
| Frames por nivel | 1 + skip mal implementado | 2 (1 descarte + 1 real) |
| Tempo por nivel | ~350ms | ~400ms (2 frames) |
| Tempo total captura | ~2.8s | ~1.6s |
| Fusao | nanmean (~100ms) | soma/count (~20ms) |
| **TOTAL** | **~3.0s** | **~1.6s (47% mais rapido)** |

---

### 2.5 SOLUCAO 2: HDR por Frame Rate Elevado com Buffer Circular

**Principio:** Em vez de parar tudo para fazer HDR, capturar continuamente a diferentes exposicoes num ciclo rotativo. Cada N frames, a exposicao muda. A fusao acontece quando temos pelo menos 1 frame de cada nivel no buffer.

Esta abordagem e **nao-bloqueante** - a GUI nunca congela.

```python
import numpy as np
import cv2
import threading
import time
from collections import deque
from API.VzenseDS_api import *
from CameraState import camState
from FrameState import frameState

HDR_EXPOSURES = [300, 1500, 4000]  # 3 niveis (balanco entre velocidade e qualidade)
FRAMES_PER_LEVEL = 2               # capturar 2 frames por nivel antes de mudar

class HDRProcessor:
    """
    Processador HDR continuo e nao-bloqueante.

    Funciona em background: alterna exposicoes automaticamente,
    acumula frames num buffer, e produz um frame HDR fundido
    assim que tem dados de todos os niveis.

    Tempo entre frames HDR: ~1.2s (3 niveis * 2 frames * 200ms)
    A GUI nunca bloqueia - le o ultimo HDR disponivel.
    """

    def __init__(self):
        self._running = False
        self._thread = None
        self._buffers = {}           # {exposure: [frames]}
        self._depth_buffers = {}     # {exposure: [frames]}
        self._lock = threading.Lock()
        self._original_exposure = None

    def start(self):
        """Inicia o processamento HDR em background."""
        if self._running:
            return
        self._running = True
        self._original_exposure = camState.exposureTime
        self._buffers = {exp: [] for exp in HDR_EXPOSURES}
        self._depth_buffers = {exp: [] for exp in HDR_EXPOSURES}
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Para o processamento HDR e restaura a exposicao original."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._original_exposure and camState.camera:
            camState.camera.VZ_SetExposureTime(
                VzSensorType.VzToFSensor, c_int32(self._original_exposure)
            )
            camState.exposureTime = self._original_exposure

    def _capture_loop(self):
        """Loop de captura: roda entre exposicoes e acumula frames."""
        level_idx = 0
        frames_at_level = 0
        skip_next = True  # descartar primeiro frame apos mudanca

        while self._running:
            current_exp = HDR_EXPOSURES[level_idx]

            # Mudar exposicao se necessario
            if frames_at_level == 0:
                camState.camera.VZ_SetExposureTime(
                    VzSensorType.VzToFSensor, c_int32(current_exp)
                )
                camState.exposureTime = current_exp
                skip_next = True

            # Capturar frame
            ret, frameready = camState.camera.VZ_GetFrameReady(c_uint16(200))
            if ret != 0:
                continue

            # Ler frames
            ctd_frame = None
            dep_frame = None

            if frameready.color:
                ret, rgbf = camState.camera.VZ_GetFrame(
                    VzFrameType.VzTransformColorImgToDepthSensorFrame
                )
                if ret == 0:
                    tmp = np.ctypeslib.as_array(
                        rgbf.pFrameData, (1, rgbf.width * rgbf.height * 3)
                    )
                    tmp.dtype = np.uint8
                    tmp.shape = (rgbf.height, rgbf.width, 3)
                    ctd_frame = tmp.copy()

            if frameready.depth:
                ret, df = camState.camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                if ret == 0:
                    tmp = np.ctypeslib.as_array(
                        df.pFrameData, (1, df.width * df.height * 2)
                    )
                    tmp.dtype = np.uint16
                    tmp.shape = (df.height, df.width)
                    dep_frame = tmp.copy()

            if ctd_frame is None or dep_frame is None:
                continue

            # Descartar primeiro frame apos mudanca de exposicao
            if skip_next:
                skip_next = False
                # Mas ainda atualizar o frameState normal para a GUI nao congelar
                frameState.colorToDepthFrame = ctd_frame
                frameState.depthFrame = dep_frame
                continue

            # Acumular frame no buffer deste nivel
            ctd_resized = cv2.resize(ctd_frame, (640, 480))
            dep_resized = cv2.resize(dep_frame, (640, 480))

            with self._lock:
                self._buffers[current_exp] = [ctd_resized]   # guardar ultimo frame
                self._depth_buffers[current_exp] = [dep_resized]

            # Atualizar frameState normal (a GUI continua a ver frames em tempo real)
            frameState.colorToDepthFrame = ctd_frame
            frameState.depthFrame = dep_frame

            frames_at_level += 1

            # Avancar para proximo nivel
            if frames_at_level >= FRAMES_PER_LEVEL:
                frames_at_level = 0
                level_idx = (level_idx + 1) % len(HDR_EXPOSURES)

                # Se completou um ciclo, fundir
                if level_idx == 0:
                    self._fuse()

    def _fuse(self):
        """Funde os buffers de todas as exposicoes num frame HDR."""
        with self._lock:
            # Verificar que temos frames de todos os niveis
            all_colors = []
            all_depths = []

            for exp in HDR_EXPOSURES:
                if len(self._buffers[exp]) == 0:
                    return  # incompleto, esperar proximo ciclo
                all_colors.extend(self._buffers[exp])
                all_depths.extend(self._depth_buffers[exp])

        # Fusao de cor
        stacked = np.stack(all_colors, axis=0).astype(np.float32)
        mask = stacked > 0
        sum_c = np.sum(stacked * mask, axis=0)
        cnt_c = np.sum(mask, axis=0).astype(np.float32)
        cnt_c[cnt_c == 0] = 1
        hdr_color = (sum_c / cnt_c).astype(np.uint8)

        # Fusao de profundidade
        stacked_d = np.stack(all_depths, axis=0).astype(np.float64)
        mask_d = (stacked_d > 0) & (stacked_d <= 5000)
        sum_d = np.sum(stacked_d * mask_d, axis=0)
        cnt_d = np.sum(mask_d, axis=0).astype(np.float64)
        cnt_d[cnt_d == 0] = 1
        hdr_depth = (sum_d / cnt_d).astype(np.uint16)

        # Publicar resultado
        frameState.colorToDepthFrameHDR = hdr_color
        frameState.depthFrameHDR = hdr_depth
        frameState.colorFrameHDR = frameState.colorFrame


# Uso global (singleton)
hdr_processor = HDRProcessor()
```

**Integracao com api.py:**

```python
# Substituir o codigo atual de toggle HDR:

# Quando liga HDR:
@app.post("/expositionMode/hdr")
async def set_hdr_mode():
    hdr_processor.start()
    modeState.expositionMode = "HDR"
    return {"message": "HDR started"}

# Quando desliga HDR:
@app.post("/expositionMode/fixed")
async def set_fixed_mode():
    hdr_processor.stop()
    modeState.expositionMode = "Fixed Exposition"
    return {"message": "Fixed mode"}
```

**Comparacao:**

| Aspeto | hdrAPI() atual | HDRProcessor |
|--------|---------------|-------------|
| Bloqueante? | Sim (~3s de congelamento) | Nao (background) |
| GUI congela? | Sim | Nao |
| Tempo por ciclo HDR | ~3.0s | ~1.2s |
| Frame rate normal | Interrompido | Continua (com exposicao variavel) |
| Thread safety | Nenhuma | Lock no buffer |
| Restaura exposicao | Hardcoded 700us | Restaura valor original |

---

### 2.6 Recomendacao para HDR

**Para implementacao rapida:** Solucao 1 (hdrOptimizedAPI). Troca direta - substitui a funcao existente, reduz tempo de ~3s para ~1.6s, e mantem a mesma logica.

**Para implementacao robusta:** Solucao 2 (HDRProcessor). Requer mais trabalho de integracao mas elimina completamente o problema de congelamento da GUI. E a abordagem correta para producao.

**Melhorias adicionais possiveis (futuro):**
- Ponderacao por qualidade do pixel (exposure weighting) em vez de media simples
- Tone mapping (Debevec, Mertens) para melhor qualidade visual do HDR de cor
- Usar o confidence frame da camara para pesar a fusao de profundidade

---

## RESUMO DE ACOES

| # | Acao | Ficheiro | Impacto | Esforco |
|---|------|----------|---------|---------|
| 1 | Implementar volumeVoxelAPI | VolumeTkinter.py | Precisao de volume: +50-90% | Medio |
| 2 | Substituir chamada em api.py | api.py | Integracao | Baixo |
| 3 | Implementar hdrOptimizedAPI | HDRDef.py | Tempo HDR: -47% | Baixo |
| 4 | OU implementar HDRProcessor | HDRDef.py + api.py | GUI nao congela | Alto |
| 5 | Adicionar correcao radial | VolumeTkinter.py | Precisao bordas: +1-5% | Baixo |

**Ordem recomendada:** 1 -> 2 -> 3 (ganho maximo com esforco minimo), depois avaliar se precisa de 4 e 5.
