import React, { useEffect, useRef, useState } from 'react';
import { InundationScenarioResult, ParcelAsset } from '../engine/alverisEngine';

declare global {
  interface Window {
    L: any;
  }
}

interface GeospatialCockpitProps {
  parcel: ParcelAsset;
  inundation: InundationScenarioResult;
  isNetworkIsolated: boolean;
  subsidenceRateMmYr: number;
}

export const GeospatialCockpit: React.FC<GeospatialCockpitProps> = ({
  parcel,
  inundation,
  isNetworkIsolated,
  subsidenceRateMmYr,
}) => {
  const [activeTab, setActiveTab] = useState<'deck' | 'folium'>('deck');
  const [showFlood, setShowFlood] = useState(true);
  const [showRoads, setShowRoads] = useState(true);
  const [basemapStyle, setBasemapStyle] = useState<'dark' | 'satellite' | 'osm'>('dark');

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const leafletMapRef = useRef<any>(null);

  const [cenLon, cenLat] = parcel.centroid_lonlat;
  const ring = parcel.geometry_geojson.coordinates[0];

  // Initialize and update Leaflet GIS map
  useEffect(() => {
    if (!mapContainerRef.current || !window.L) return;
    const L = window.L;

    if (leafletMapRef.current) {
      leafletMapRef.current.remove();
      leafletMapRef.current = null;
    }

    const map = L.map(mapContainerRef.current, {
      center: [cenLat, cenLon],
      zoom: activeTab === 'deck' ? 14 : 15,
      zoomControl: true,
    });
    leafletMapRef.current = map;

    const tileUrls = {
      dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      satellite:
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      osm: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    };

    L.tileLayer(tileUrls[basemapStyle], {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap & CARTO / Esri',
    }).addTo(map);

    // 1. Cadastral Parcel Polygon
    const latLngs = ring.map((c) => [c[1], c[0]]);
    const parcelPoly = L.polygon(latLngs, {
      color: '#00ffcc',
      weight: 3,
      fillColor: '#00ffcc',
      fillOpacity: 0.22,
    }).addTo(map);

    parcelPoly.bindPopup(
      `<div style="color:#0f172a;font-family:sans-serif;font-size:12px;">
        <strong style="color:#0284c7;font-size:13px;">${parcel.name}</strong><br/>
        <b>Asset ID:</b> ${parcel.asset_id}<br/>
        <b>Land Use:</b> ${parcel.land_use_class}<br/>
        <b>Area:</b> ${parcel.area_hectares} ha (${Math.round(parcel.area_sqm).toLocaleString()} m²)<br/>
        <b>UTM CRS:</b> <code>${parcel.utm_epsg}</code><br/>
        <b>InSAR Rate:</b> ${subsidenceRateMmYr.toFixed(2)} mm/yr
      </div>`
    );

    // 2. 8-Way Flood Extent Overlay
    if (showFlood && inundation.flooded_percent > 0.5) {
      const frac = Math.min(1.0, inundation.connected_inundation_fraction * 1.15);
      const floodedLatLngs = ring.map(([lon, lat]) => [
        lat + (cenLat - lat) * (1.0 - frac),
        lon + (cenLon - lon) * (1.0 - frac),
      ]);
      L.polygon(floodedLatLngs, {
        color: activeTab === 'deck' ? '#00d2ff' : '#ef4444',
        weight: 2,
        fillColor: activeTab === 'deck' ? '#008cff' : '#ef4444',
        fillOpacity: 0.48,
      })
        .bindTooltip(
          `Connected Inundation: ${inundation.flooded_percent.toFixed(1)}% submerged (Mean Depth: ${inundation.flood_depth_mean_m.toFixed(2)}m)`
        )
        .addTo(map);
    }

    // 3. Road Network Links
    if (showRoads) {
      const roads = [
        {
          name: 'Arterial Highway East',
          coords: [
            [cenLat, cenLon],
            [cenLat + 0.006, cenLon + 0.008],
          ],
          severed: isNetworkIsolated || inundation.water_level_rise_m >= 1.0,
        },
        {
          name: 'Inland Access Road West',
          coords: [
            [cenLat, cenLon],
            [cenLat + 0.003, cenLon - 0.007],
          ],
          severed: false,
        },
        {
          name: 'Port Feeder Road South',
          coords: [
            [cenLat, cenLon],
            [cenLat - 0.008, cenLon + 0.002],
          ],
          severed: isNetworkIsolated || inundation.water_level_rise_m >= 1.0,
        },
      ];

      roads.forEach((r) => {
        L.polyline(r.coords, {
          color: r.severed ? '#ef4444' : '#10b981',
          weight: 4,
          opacity: 0.9,
          dashArray: r.severed ? '6, 6' : undefined,
        })
          .bindTooltip(
            `${r.name}: ${r.severed ? 'IMPASSABLE / SUBMERGED (>0.30m)' : 'PASSABLE / DRY'}`
          )
          .addTo(map);
      });
    }

    // 4. InSAR PS Stations (in Multi-Layer GIS mode)
    if (activeTab === 'folium') {
      const psOffsets: [number, number, number, string][] = [
        [0.0012, 0.001, subsidenceRateMmYr * 1.15, 'PS-01 (Building Roof)'],
        [-0.0015, -0.0008, subsidenceRateMmYr * 0.9, 'PS-02 (Foundation West)'],
        [0.002, -0.0012, subsidenceRateMmYr * 1.05, 'PS-03 (Loading Bay)'],
        [-0.0009, 0.0018, subsidenceRateMmYr * 0.8, 'PS-04 (Perimeter Dykes)'],
        [0.0, 0.0, subsidenceRateMmYr, 'PS-05 (Central Benchmark)'],
      ];

      psOffsets.forEach(([dLat, dLon, rate, label]) => {
        const clr = rate < -7.0 ? '#ef4444' : rate < -3.0 ? '#f59e0b' : '#10b981';
        L.circleMarker([cenLat + dLat, cenLon + dLon], {
          radius: 6,
          color: '#ffffff',
          weight: 1.5,
          fillColor: clr,
          fillOpacity: 0.9,
        })
          .bindTooltip(`${label}: ${rate.toFixed(2)} mm/yr`)
          .addTo(map);
      });
    }

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, [
    parcel,
    inundation,
    isNetworkIsolated,
    subsidenceRateMmYr,
    activeTab,
    showFlood,
    showRoads,
    basemapStyle,
    cenLat,
    cenLon,
    ring,
  ]);

  return (
    <div className="my-6">
      <h2 className="text-xl font-bold text-slate-100 mb-3">Interactive Geospatial Cockpit</h2>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 bg-[#0f172a] border border-slate-800 rounded-lg p-4">
          {/* Tabs matching Streamlit app.py */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-3">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setActiveTab('deck')}
                className={`px-3 py-1.5 rounded text-xs font-semibold transition ${
                  activeTab === 'deck'
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                🌐 WebGL PyDeck (3D Perspective)
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('folium')}
                className={`px-3 py-1.5 rounded text-xs font-semibold transition ${
                  activeTab === 'folium'
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                🗺️ Leaflet / Folium (Multi-Layer GIS)
              </button>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Basemap:</span>
              {(['dark', 'satellite', 'osm'] as const).map((bm) => (
                <button
                  key={bm}
                  type="button"
                  onClick={() => setBasemapStyle(bm)}
                  className={`px-2 py-1 rounded capitalize ${
                    basemapStyle === bm
                      ? 'bg-slate-700 text-white font-medium'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {bm}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-6 mb-3 text-xs text-slate-300">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showFlood}
                onChange={(e) => setShowFlood(e.target.checked)}
                className="accent-sky-400"
              />
              Overlay 8-Way Flood Extent
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showRoads}
                onChange={(e) => setShowRoads(e.target.checked)}
                className="accent-sky-400"
              />
              Overlay Road Network Links
            </label>
          </div>

          <div
            ref={mapContainerRef}
            className="w-full h-[380px] rounded-lg overflow-hidden border border-slate-800 z-0"
          />

          <div className="text-xs text-slate-400 mt-2.5">
            {activeTab === 'deck' ? (
              <span>
                <strong>Centroid:</strong> {cenLat.toFixed(4)}°N, {cenLon.toFixed(4)}°E |{' '}
                <strong>UTM:</strong> <code className="text-sky-400">{parcel.utm_epsg}</code> |{' '}
                <strong>Basemap:</strong> Carto DarkMatter WebGL
              </span>
            ) : (
              <span>
                <strong>Interactive GIS Layers:</strong> CartoDB DarkMatter · Esri Satellite ·
                Cadastral Boundary · InSAR PS Stations · Inundation Hazard · Road Arterials
              </span>
            )}
          </div>
        </div>

        <div className="lg:col-span-2 bg-[#0f172a] border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-100 mb-4">
              Hydrological Inundation Telemetry
            </h3>
            <div className="grid grid-cols-2 gap-4 mb-5">
              <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
                <div className="text-xs text-slate-400">Flooded Parcel Area</div>
                <div className="text-2xl font-bold text-slate-100 mt-1">
                  {Math.round(inundation.flooded_area_sqm).toLocaleString('en-IN')} m²
                </div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
                <div className="text-xs text-slate-400">Mean Flood Depth</div>
                <div className="text-2xl font-bold text-slate-100 mt-1">
                  {inundation.flood_depth_mean_m.toFixed(2)} m
                </div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
                <div className="text-xs text-slate-400">Usable Land Loss</div>
                <div className="text-2xl font-bold text-rose-400 mt-1">
                  {inundation.flooded_percent.toFixed(1)}%
                </div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
                <div className="text-xs text-slate-400">Dry Pockets (Protected)</div>
                <div className="text-2xl font-bold text-emerald-400 mt-1">
                  {inundation.unconnected_low_pocket_count}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-sky-950/40 border border-sky-800/60 text-sky-200 text-xs p-3.5 rounded-lg leading-relaxed">
            <strong>Physical Engine:</strong> 8-Way Morphological Connected Components seeded at
            coastline. Depression pockets below sea level without hydrologic path remain dry.
          </div>
        </div>
      </div>
    </div>
  );
};
