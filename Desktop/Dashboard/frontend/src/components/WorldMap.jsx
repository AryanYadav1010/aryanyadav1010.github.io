import React, { useState, useCallback, useEffect } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from "react-simple-maps";
import { getAlpha2Code, getCountryName } from "../lib/countries";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Color gradient: Darkest (low) -> Lightest (high) - Red to Pale Yellow
const COLOR_STOPS = [
  "#dc2626", // Red (lighter than very dark red)
  "#ea580c", // Orange-Red
  "#f97316", // Orange
  "#facc15", // Yellow
  "#fef08a"  // Pale Yellow
];

const NO_DATA_COLOR = "#475569";

function interpolateColor(color1, color2, factor) {
  const hex = (c) => parseInt(c, 16);
  const r1 = hex(color1.slice(1, 3));
  const g1 = hex(color1.slice(3, 5));
  const b1 = hex(color1.slice(5, 7));
  const r2 = hex(color2.slice(1, 3));
  const g2 = hex(color2.slice(3, 5));
  const b2 = hex(color2.slice(5, 7));

  const r = Math.round(r1 + (r2 - r1) * factor);
  const g = Math.round(g1 + (g2 - g1) * factor);
  const b = Math.round(b1 + (b2 - b1) * factor);

  return `rgb(${r}, ${g}, ${b})`;
}

function getColorForValue(value, invert = false) {
  if (value === null || value === undefined) return NO_DATA_COLOR;
  
  // If lower is better, we invert the value for coloring
  // So a low value (e.g. 0.1) becomes a high value (0.9) in the color scale (Yellow)
  const effectiveValue = invert ? 1 - value : value;
  
  const clampedValue = Math.max(0, Math.min(1, effectiveValue));
  const index = clampedValue * (COLOR_STOPS.length - 1);
  const lowerIndex = Math.floor(index);
  const upperIndex = Math.ceil(index);
  if (lowerIndex === upperIndex) return COLOR_STOPS[lowerIndex];
  return interpolateColor(COLOR_STOPS[lowerIndex], COLOR_STOPS[upperIndex], index - lowerIndex);
}

function WorldMap({
  onCountrySelect,
  selectedCountry,
  highlightedCountry,
  selectedIndicator,
  indicatorName,
  lowerIsBetter = false
}) {
  const [tooltip, setTooltip] = useState(null);
  const [position, setPosition] = useState({ coordinates: [0, 20], zoom: 1 });
  const [indicatorData, setIndicatorData] = useState({});
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    const fetchIndicatorData = async () => {
      setDataLoaded(false);
      try {
        const response = await axios.get(`${API}/indicators/${selectedIndicator}`);
        setIndicatorData(response.data.data || {});
      } catch (err) {
        console.error("Error fetching indicator data:", err);
        try {
          const fallbackResponse = await axios.get(`${API}/liberal-index`);
          setIndicatorData(fallbackResponse.data.data || {});
        } catch (e) {
          setIndicatorData({});
        }
      } finally {
        setDataLoaded(true);
      }
    };
    fetchIndicatorData();
  }, [selectedIndicator]);

  const handleCountryClick = useCallback((geo) => {
    const alpha3 = geo.properties?.["ISO_A3"] || geo.id;
    const alpha2 = getAlpha2Code(alpha3);
    const countryName = getCountryName(geo);
    const countryData = indicatorData[alpha2];

    if (alpha2 && onCountrySelect) {
      onCountrySelect({
        code: alpha2,
        name: countryName,
        alpha3: alpha3,
        indicatorValue: countryData?.value,
        indicatorYear: countryData?.year,
      });
    }
  }, [onCountrySelect, indicatorData]);

  const handleMouseEnter = useCallback((geo, event) => {
    const alpha3 = geo.properties?.["ISO_A3"] || geo.id;
    const alpha2 = getAlpha2Code(alpha3);
    const countryName = getCountryName(geo);
    const countryData = indicatorData[alpha2];

    setTooltip({
      name: countryName,
      value: countryData?.value,
      year: countryData?.year,
      x: event.clientX,
      y: event.clientY,
    });
  }, [indicatorData]);

  const handleMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  const handleMouseMove = useCallback((event) => {
    if (tooltip) {
      setTooltip(prev => ({ ...prev, x: event.clientX, y: event.clientY }));
    }
  }, [tooltip]);

  const handleMoveEnd = useCallback((position) => {
    setPosition(position);
  }, []);

  const getCountryFill = useCallback((alpha2) => {
    if (!dataLoaded) return NO_DATA_COLOR;
    const countryData = indicatorData[alpha2];
    return getColorForValue(countryData?.value, lowerIsBetter);
  }, [indicatorData, dataLoaded, lowerIsBetter]);

  return (
    <div
      className="world-map-container"
      data-testid="world-map-container"
      onMouseMove={handleMouseMove}
    >
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ scale: 130, center: [0, 30] }}
        style={{ width: "100%", height: "100%", background: "transparent" }}
      >
        <ZoomableGroup
          zoom={position.zoom}
          center={position.coordinates}
          onMoveEnd={handleMoveEnd}
          minZoom={1}
          maxZoom={8}
        >
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const alpha3 = geo.properties?.["ISO_A3"] || geo.id;
                const alpha2 = getAlpha2Code(alpha3);
                const fillColor = getCountryFill(alpha2);
                const isSelected = selectedCountry && alpha2 === selectedCountry.toLowerCase();
                const isHighlighted = highlightedCountry && alpha2 === highlightedCountry.toLowerCase();

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    data-testid={`country-${alpha2 || alpha3}`}
                    onClick={() => handleCountryClick(geo)}
                    onMouseEnter={(e) => handleMouseEnter(geo, e)}
                    onMouseLeave={handleMouseLeave}
                    style={{
                      default: {
                        fill: fillColor,
                        stroke: isSelected ? "#ffffff" : isHighlighted ? "#3b82f6" : "#334155",
                        strokeWidth: isSelected ? 2 : isHighlighted ? 1.5 : 0.5,
                        outline: "none",
                      },
                      hover: {
                        fill: fillColor,
                        stroke: "#ffffff",
                        strokeWidth: 1,
                        outline: "none",
                        filter: "brightness(1.1)",
                        cursor: "pointer",
                      },
                      pressed: {
                        fill: fillColor,
                        stroke: "#ffffff",
                        strokeWidth: 1.5,
                        outline: "none",
                        filter: "brightness(0.95)",
                      },
                    }}
                  />
                );
              })
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>

      {tooltip && (
        <div className="country-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
          <span className="country-tooltip-name">{tooltip.name}</span>
          {tooltip.value !== undefined && (
            <div className="country-tooltip-value">
              {indicatorName || "Value"}: <strong>{tooltip.value.toFixed(3)}</strong>
              <span className="text-xs text-slate-400 ml-1">({tooltip.year})</span>
            </div>
          )}
        </div>
      )}

      <div className="map-legend" data-testid="map-legend">
        <div className="legend-title">{indicatorName || "Index"}</div>
        <div className="legend-scale">
          <div className="legend-item">
            <span className="legend-color" style={{ background: "#dc2626" }}></span>
            <span className="legend-label">
              {lowerIsBetter ? "0.75 - 1.0" : "0 - 0.25"} ({lowerIsBetter ? "High/Worse" : "Low/Worse"})
            </span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: "#ea580c" }}></span>
            <span className="legend-label">
              {lowerIsBetter ? "0.5 - 0.75" : "0.25 - 0.5"}
            </span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: "#f97316" }}></span>
            <span className="legend-label">
              {"0.5"}
            </span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: "#facc15" }}></span>
            <span className="legend-label">
              {lowerIsBetter ? "0.1 - 0.25" : "0.75 - 0.9"}
            </span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: "#fef08a" }}></span>
            <span className="legend-label">
              {lowerIsBetter ? "0 - 0.1" : "0.9 - 1.0"} ({lowerIsBetter ? "Low/Better" : "High/Better"})
            </span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: NO_DATA_COLOR }}></span>
            <span className="legend-label">No Data</span>
          </div>
        </div>
        <div className="legend-source">Source: V-Dem v15 (2024)</div>
      </div>
    </div>
  );
}

export default WorldMap;
