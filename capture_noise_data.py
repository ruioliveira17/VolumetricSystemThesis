#!/usr/bin/env python3
"""
Captura frames com diferentes configuracoes HDR para analise de ruido
e metodo de calibracao. Plataforma deve estar VAZIA durante a captura.
"""

import sys
import os
import time
import numpy
import cv2
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "Python"))
sys.path.insert(0, os.path.join(BASE_DIR, "Python", "Samples", "DS86", "FrameViewer"))

from API.VzenseDS_api import *

OUTPUT_DIR = os.path.join(BASE_DIR, "noise_capture")
os.makedirs(OUTPUT_DIR, exist_ok=True)

N_FRAMES         = 10    # frames por configuracao
SETTLE           = 4     # frames descartadas apos mudar exposicao (estabilizacao)
FRAME_TIMEOUT_MS = 1200

# Exposicoes fixas individuais (microsegundos)
FIXED_EXPOSURES = [30, 195, 360, 525, 690, 855, 1020, 1185, 1350, 1515, 1750, 2000, 4000]

# Grupos HDR (identicos ao CameraState.py)
HDR_GROUPS = {
    "Low":    [30,   195,  360,  525],
    "Medium": [690,  855,  1020, 1185],
    "High":   [1350, 1515, 1750, 2000],
}


# ---------------------------------------------------------------------------
# Camera helpers
# ---------------------------------------------------------------------------

def connect_camera():
    cam = VzenseTofCam()
    count = cam.VZ_GetDeviceCount()
    retry = 30
    while count == 0 and retry > 0:
        count = cam.VZ_GetDeviceCount()
        time.sleep(1)
        retry -= 1
        print(f"  Procurando camera... {retry}")

    ret, info = cam.VZ_GetDeviceInfo()
    if ret != 0:
        raise RuntimeError(f"VZ_GetDeviceInfo falhou: {ret}")

    retry = 20
    while retry > 0:
        if info.status == VzConnectStatus.Connected.value:
            break
        retry -= 1
        time.sleep(1)
        ret, info = cam.VZ_GetDeviceInfo()

    ret = cam.VZ_OpenDeviceByIP(info.ip)
    if ret != 0:
        raise RuntimeError(f"VZ_OpenDeviceByIP falhou: {ret}")

    ret = cam.VZ_StartStream()
    if ret != 0:
        raise RuntimeError(f"VZ_StartStream falhou: {ret}")

    cam.VZ_SetExposureControlMode(
        VzSensorType.VzToFSensor,
        VzExposureControlMode.VzExposureControlMode_Manual
    )
    cam.VZ_SetFillHoleFilterEnabled(True)
    cam.VZ_SetSpatialFilterEnabled(True)

    ret, tf = cam.VZ_GetTimeFilterParams()
    tf.enable = True
    cam.VZ_SetTimeFilterParams(tf)

    cam.VZ_SetFrameRate(10)
    print("Camera pronta.")
    return cam


def grab_depth(cam):
    """Captura um frame de profundidade. Retorna array uint16 ou None."""
    for _ in range(30):
        ret, ready = cam.VZ_GetFrameReady(c_uint16(FRAME_TIMEOUT_MS))
        if ret != 0:
            continue
        if ready.depth:
            ret, df = cam.VZ_GetFrame(VzFrameType.VzDepthFrame)
            if ret == 0:
                tmp = numpy.ctypeslib.as_array(
                    df.pFrameData, (1, df.width * df.height * 2))
                tmp.dtype = numpy.uint16
                tmp.shape = (df.height, df.width)
                return tmp.copy()
    return None


def set_exposure(cam, us):
    cam.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(us))
    time.sleep(0.08)


# ---------------------------------------------------------------------------
# Capture helpers
# ---------------------------------------------------------------------------

def capture_n_frames(cam, exposure_us, n, label):
    """Define exposicao, descarta frames de estabilizacao, captura N frames depth."""
    set_exposure(cam, exposure_us)
    for _ in range(SETTLE):
        grab_depth(cam)

    frames = []
    for i in range(n):
        d = grab_depth(cam)
        if d is not None:
            frames.append(d)
        print(f"    [{label}] {i+1}/{n}", end="\r")
    print()
    return frames


def build_hdr(frames, max_valid=5000):
    """Mediana + substituicao por minimo nos pixels instáveis (MAD > 15mm)."""
    stacked = numpy.stack(frames, axis=0).astype(numpy.float32)
    valid   = (stacked > 150) & (stacked <= max_valid)
    stacked[~valid] = numpy.nan

    med = numpy.nanmedian(stacked, axis=0)
    mad = numpy.nanmedian(numpy.abs(stacked - med), axis=0)
    unstable = mad > 15
    min_d = numpy.nanmin(stacked, axis=0)
    hdr = med.copy()
    hdr[unstable] = min_d[unstable]
    return numpy.nan_to_num(hdr, nan=0).astype(numpy.uint16)


def stats_in_roi(frames, roi_mask=None):
    """Devolve estatisticas na ROI (ou global se roi_mask=None)."""
    stacked = numpy.stack(frames, axis=0).astype(numpy.float32)
    valid   = (stacked > 150) & (stacked <= 5000)
    stacked[~valid] = numpy.nan

    mean_map   = numpy.nanmean(stacked, axis=0)
    std_map    = numpy.nanstd(stacked, axis=0)
    median_map = numpy.nanmedian(stacked, axis=0)
    zero_map   = numpy.sum(~valid, axis=0)

    sel = roi_mask if roi_mask is not None else numpy.ones(mean_map.shape, bool)
    return {
        "roi_mean_depth":      float(numpy.nanmean(mean_map[sel])),
        "roi_std_mean":        float(numpy.nanmean(std_map[sel])),
        "roi_std_max":         float(numpy.nanmax(std_map[sel])),
        "roi_std_p95":         float(numpy.nanpercentile(std_map[sel], 95)),
        "roi_zeros_per_frame": float(numpy.mean(zero_map[sel])),
        "n_frames":            len(frames),
    }, mean_map, std_map, median_map


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    run = os.path.join(OUTPUT_DIR, f"run_{ts}")
    os.makedirs(run, exist_ok=True)

    print("=" * 60)
    print("CAPTURA DE RUIDO - PLATAFORMA VAZIA")
    print(f"Output: {run}")
    print("=" * 60)
    input("Prima ENTER quando a plataforma estiver vazia e pronta...")

    cam = connect_camera()

    # Carregar mascara da workspace se existir
    roi_mask = None
    calib_path = os.path.join(BASE_DIR, "config", "workspace_calibration.json")
    if os.path.exists(calib_path):
        with open(calib_path) as f:
            calib = json.load(f)
        det = numpy.array(calib["detection_area"], dtype=numpy.int32)
        msk = numpy.zeros((480, 640), dtype=numpy.uint8)
        cv2.fillPoly(msk, [det], 255)
        roi_mask = msk > 0
        print(f"ROI carregada. workspace_depth={calib['workspace_depth']:.1f}mm")

    summary = {"timestamp": ts, "n_frames": N_FRAMES, "configs": {}}

    try:
        # ------------------------------------------------------------------
        # 1. Exposicoes fixas individuais
        # ------------------------------------------------------------------
        print("\n[FASE 1] Exposicoes fixas individuais")
        for exp in FIXED_EXPOSURES:
            label = f"fixed_{exp}us"
            print(f"  Exposicao {exp} us...")
            frames = capture_n_frames(cam, exp, N_FRAMES, label)
            if not frames:
                print("    ERRO: sem frames")
                continue

            d = os.path.join(run, label)
            os.makedirs(d, exist_ok=True)
            for i, fr in enumerate(frames):
                numpy.save(os.path.join(d, f"depth_{i:02d}.npy"), fr)

            st, mean_map, std_map, med_map = stats_in_roi(frames, roi_mask)
            numpy.save(os.path.join(d, "mean_map.npy"),   mean_map)
            numpy.save(os.path.join(d, "std_map.npy"),    std_map)
            numpy.save(os.path.join(d, "median_map.npy"), med_map)
            summary["configs"][label] = st
            print(f"    depth={st['roi_mean_depth']:.1f}mm  "
                  f"std_mean={st['roi_std_mean']:.2f}mm  "
                  f"std_p95={st['roi_std_p95']:.2f}mm  "
                  f"zeros={st['roi_zeros_per_frame']:.1f}")

        # ------------------------------------------------------------------
        # 2. Grupos HDR (frames brutas por exposicao + HDR combinado do grupo)
        # ------------------------------------------------------------------
        print("\n[FASE 2] Grupos HDR")
        all_hdr_group_depths = []

        for group_name, exposures in HDR_GROUPS.items():
            print(f"  Grupo {group_name} {exposures}")
            group_raw = []

            for exp in exposures:
                label = f"hdr_{group_name}_{exp}us"
                frames = capture_n_frames(cam, exp, N_FRAMES, label)
                if not frames:
                    continue
                d = os.path.join(run, label)
                os.makedirs(d, exist_ok=True)
                for i, fr in enumerate(frames):
                    numpy.save(os.path.join(d, f"depth_{i:02d}.npy"), fr)
                group_raw.extend(frames)

            if group_raw:
                hdr_d = build_hdr(group_raw)
                gdir  = os.path.join(run, f"hdr_{group_name}_combined")
                os.makedirs(gdir, exist_ok=True)
                numpy.save(os.path.join(gdir, "hdr_depth.npy"), hdr_d)
                all_hdr_group_depths.append(hdr_d)

                st, mean_map, std_map, med_map = stats_in_roi(group_raw, roi_mask)
                numpy.save(os.path.join(gdir, "mean_map.npy"),   mean_map)
                numpy.save(os.path.join(gdir, "std_map.npy"),    std_map)
                numpy.save(os.path.join(gdir, "median_map.npy"), med_map)
                summary["configs"][f"hdr_{group_name}"] = st
                print(f"    depth={st['roi_mean_depth']:.1f}mm  "
                      f"std_mean={st['roi_std_mean']:.2f}mm  "
                      f"std_p95={st['roi_std_p95']:.2f}mm  "
                      f"zeros={st['roi_zeros_per_frame']:.1f}")

        # ------------------------------------------------------------------
        # 3. HDR final (Low+Medium+High combinados) - simula pipeline actual
        # ------------------------------------------------------------------
        if all_hdr_group_depths:
            print("\n[FASE 3] HDR Final (Low+Medium+High combinados)")
            hdr_final = build_hdr(all_hdr_group_depths)
            fdir = os.path.join(run, "hdr_final_combined")
            os.makedirs(fdir, exist_ok=True)
            numpy.save(os.path.join(fdir, "hdr_depth.npy"), hdr_final)

            st, mean_map, std_map, med_map = stats_in_roi([hdr_final], roi_mask)
            numpy.save(os.path.join(fdir, "mean_map.npy"),   mean_map)
            numpy.save(os.path.join(fdir, "std_map.npy"),    std_map)
            numpy.save(os.path.join(fdir, "median_map.npy"), med_map)
            summary["configs"]["hdr_final"] = st
            print(f"  depth={st['roi_mean_depth']:.1f}mm  "
                  f"std_mean={st['roi_std_mean']:.2f}mm  "
                  f"std_p95={st['roi_std_p95']:.2f}mm")

        # ------------------------------------------------------------------
        # Gravar resumo
        # ------------------------------------------------------------------
        with open(os.path.join(run, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\nConcluido. Dados em: {run}")
        print("\n--- RESUMO FINAL ---")
        for cfg, st in summary["configs"].items():
            print(f"  {cfg:<40}  depth={st['roi_mean_depth']:7.1f}mm  "
                  f"std_mean={st['roi_std_mean']:5.2f}mm  "
                  f"std_p95={st['roi_std_p95']:5.2f}mm")

    finally:
        cam.VZ_StopStream()
        cam.VZ_CloseDevice()
        print("Camera fechada.")


if __name__ == "__main__":
    main()
