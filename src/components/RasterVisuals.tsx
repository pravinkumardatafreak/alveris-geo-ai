import React, { useEffect, useRef } from 'react';

function interpolateColor(
  t: number,
  stops: [number, [number, number, number]][]
): [number, number, number] {
  const clamped = Math.max(0, Math.min(1, t));
  for (let i = 0; i < stops.length - 1; i++) {
    const [t0, c0] = stops[i];
    const [t1, c1] = stops[i + 1];
    if (clamped >= t0 && clamped <= t1) {
      const f = (clamped - t0) / Math.max(1e-6, t1 - t0);
      return [
        Math.round(c0[0] + (c1[0] - c0[0]) * f),
        Math.round(c0[1] + (c1[1] - c0[1]) * f),
        Math.round(c0[2] + (c1[2] - c0[2]) * f),
      ];
    }
  }
  return stops[stops.length - 1][1];
}

const TERRAIN_STOPS: [number, [number, number, number]][] = [
  [0.0, [30, 64, 175]],
  [0.25, [16, 185, 129]],
  [0.55, [234, 179, 8]],
  [0.8, [161, 98, 7]],
  [1.0, [248, 250, 252]],
];

const SLOPE_STOPS: [number, [number, number, number]][] = [
  [0.0, [254, 249, 195]],
  [0.35, [253, 186, 116]],
  [0.7, [239, 68, 68]],
  [1.0, [127, 29, 29]],
];

const COOLWARM_STOPS: [number, [number, number, number]][] = [
  [0.0, [59, 130, 246]],
  [0.5, [226, 232, 240]],
  [1.0, [220, 38, 38]],
];

/**
 * Copernicus DEM Elevation Raster with SLR Breach Contour (`plot_dem_elevation_raster` in `rasters.py`)
 */
export const DemElevationRasterCanvas: React.FC<{
  elevGrid: number[][];
  waterLevelRiseM: number;
}> = ({ elevGrid, waterLevelRiseM }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !elevGrid.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const H = elevGrid.length;
    const W = elevGrid[0].length;
    const scale = 5;
    canvas.width = W * scale;
    canvas.height = H * scale;

    const flat = elevGrid.flat();
    const vmin = Math.min(...flat);
    const vmax = Math.max(vmin + 0.5, Math.max(...flat));

    for (let r = 0; r < H; r++) {
      for (let c = 0; c < W; c++) {
        const val = elevGrid[r][c];
        const norm = (val - vmin) / (vmax - vmin);
        const [R, G, B] = interpolateColor(norm, TERRAIN_STOPS);
        ctx.fillStyle = `rgb(${R},${G},${B})`;
        ctx.fillRect(c * scale, r * scale, scale, scale);

        // Highlight SLR breach contour line in cyan (#00e5ff)
        if (Math.abs(val - waterLevelRiseM) < (vmax - vmin) * 0.03) {
          ctx.fillStyle = '#00e5ff';
          ctx.fillRect(c * scale, r * scale, scale, scale);
        }
      }
    }
  }, [elevGrid, waterLevelRiseM]);

  return (
    <div className="bg-[#0b121e] border border-slate-800 rounded-lg p-3">
      <div className="text-xs font-bold text-slate-100 mb-2">
        Copernicus DEM (SLR Breach: {waterLevelRiseM >= 0 ? `+${waterLevelRiseM.toFixed(1)}` : waterLevelRiseM.toFixed(1)}m MSL)
      </div>
      <canvas ref={canvasRef} className="w-full h-48 rounded border border-slate-800" />
      <div className="flex justify-between text-[11px] text-slate-400 mt-1.5">
        <span>Low Elevation (Estuary)</span>
        <span className="text-cyan-400 font-semibold">-- Cyan: SLR Breach Contour</span>
        <span>High Elevation Ridge</span>
      </div>
    </div>
  );
};

/**
 * Horn's Surface Slope Gradient Raster (`plot_slope_gradient_raster` in `rasters.py`)
 */
export const SlopeGradientRasterCanvas: React.FC<{ slopeGrid: number[][] }> = ({ slopeGrid }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !slopeGrid.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const H = slopeGrid.length;
    const W = slopeGrid[0].length;
    const scale = 5;
    canvas.width = W * scale;
    canvas.height = H * scale;

    const flat = slopeGrid.flat();
    const vmax = Math.max(5.0, ...flat);

    for (let r = 0; r < H; r++) {
      for (let c = 0; c < W; c++) {
        const norm = slopeGrid[r][c] / vmax;
        const [R, G, B] = interpolateColor(norm, SLOPE_STOPS);
        ctx.fillStyle = `rgb(${R},${G},${B})`;
        ctx.fillRect(c * scale, r * scale, scale, scale);
      }
    }
  }, [slopeGrid]);

  return (
    <div className="bg-[#0b121e] border border-slate-800 rounded-lg p-3 mt-3">
      <div className="text-xs font-bold text-slate-100 mb-2">
        Horn&apos;s Surface Slope Gradient (Topographic Drainage)
      </div>
      <canvas ref={canvasRef} className="w-full h-44 rounded border border-slate-800" />
      <div className="flex justify-between text-[11px] text-slate-400 mt-1.5">
        <span>0.0° Flat Basin</span>
        <span>Steep Slope Gradient (°)</span>
      </div>
    </div>
  );
};

/**
 * Sentinel-2 False-Color Infrared (CIR) Raster (`plot_sentinel2_false_color_cir` in `rasters.py`)
 */
export const Sentinel2CirRasterCanvas: React.FC<{ spectralTensor: number[][][] }> = ({
  spectralTensor,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || spectralTensor.length < 4) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const b4 = spectralTensor[0];
    const b5 = spectralTensor[1];
    const b8 = spectralTensor[2];
    const H = b8.length;
    const W = b8[0].length;
    const scale = 5;
    canvas.width = W * scale;
    canvas.height = H * scale;

    for (let r = 0; r < H; r++) {
      for (let c = 0; c < W; c++) {
        const R = Math.min(255, Math.max(0, Math.round(b8[r][c] * 420)));
        const G = Math.min(255, Math.max(0, Math.round(b4[r][c] * 550)));
        const B = Math.min(255, Math.max(0, Math.round(b5[r][c] * 480)));
        ctx.fillStyle = `rgb(${R},${G},${B})`;
        ctx.fillRect(c * scale, r * scale, scale, scale);
      }
    }
  }, [spectralTensor]);

  return (
    <div className="bg-[#0b121e] border border-slate-800 rounded-lg p-3 mt-3">
      <div className="text-xs font-bold text-slate-100 mb-2">
        Sentinel-2 CIR (Red=Healthy Canopy, Cyan=Water/Pavement)
      </div>
      <canvas ref={canvasRef} className="w-full h-48 rounded border border-slate-800" />
      <div className="flex justify-between text-[11px] text-slate-400 mt-1.5">
        <span>B08 Near-Infrared (Canopy Vigor)</span>
        <span>B04 Red / B05 Red-Edge</span>
      </div>
    </div>
  );
};

/**
 * InSAR Subsidence Velocity Surface (`plot_insar_subsidence_surface` in `rasters.py`)
 */
export const InsarSubsidenceRasterCanvas: React.FC<{
  meanRateMm: number;
  diffGradient: number;
}> = ({ meanRateMm, diffGradient }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rows = 30;
    const cols = 30;
    const scale = 7;
    canvas.width = cols * scale;
    canvas.height = rows * scale;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const norm = (r / rows) * 0.55 + (c / cols) * 0.45;
        const [R, G, B] = interpolateColor(norm, COOLWARM_STOPS);
        ctx.fillStyle = `rgb(${R},${G},${B})`;
        ctx.fillRect(c * scale, r * scale, scale, scale);
      }
    }
  }, [meanRateMm, diffGradient]);

  return (
    <div className="bg-[#0b121e] border border-slate-800 rounded-lg p-3 mt-3">
      <div className="text-xs font-bold text-slate-100 mb-2">
        InSAR Deformation Surface ({meanRateMm.toFixed(1)} mm/yr ± {diffGradient.toFixed(4)})
      </div>
      <canvas ref={canvasRef} className="w-full h-48 rounded border border-slate-800" />
      <div className="flex justify-between text-[11px] text-slate-400 mt-1.5">
        <span>Stable Uplift / Low Velocity</span>
        <span>High Subsidence Velocity (mm/yr)</span>
      </div>
    </div>
  );
};
