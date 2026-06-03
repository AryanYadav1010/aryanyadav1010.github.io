import React, { useState, useEffect, useMemo } from "react";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { TrendingUp, TrendingDown, Filter } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Interpolate between two colors
const interpolateColor = (color1, color2, factor) => {
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
};

// Color gradient stops: Darkest (low) -> Lightest (high) - Warm amber/brown tones (no red)
const COLOR_STOPS = [
  "#5D4037", "#795548", "#8D6E63", "#A1887F", "#D7A86E",
  "#E8B960", "#F5CB5C", "#FFE082", "#FFF8E1"
];

const getColorForValue = (value, invert = false) => {
  if (value === null || value === undefined) return "#1e293b";
  
  // If lower is better, we invert the value for coloring
  const effectiveValue = invert ? 1 - value : value;
  
  const clampedValue = Math.max(0, Math.min(1, effectiveValue));
  const index = clampedValue * (COLOR_STOPS.length - 1);
  const lowerIndex = Math.floor(index);
  const upperIndex = Math.ceil(index);
  if (lowerIndex === upperIndex) return COLOR_STOPS[lowerIndex];
  return interpolateColor(COLOR_STOPS[lowerIndex], COLOR_STOPS[upperIndex], index - lowerIndex);
};

const RankingPanel = ({ onCountrySelect, selectedCountry, selectedIndicator, indicatorName, lowerIsBetter }) => {
  const [indicatorData, setIndicatorData] = useState({});
  const [sortOrder, setSortOrder] = useState("desc");
  const [filterBucket, setFilterBucket] = useState("all");
  const [loading, setLoading] = useState(true);

  // Auto-adjust sort order when indicator changes
  useEffect(() => {
    setSortOrder(lowerIsBetter ? "asc" : "desc");
  }, [lowerIsBetter, selectedIndicator]);

  // Fetch indicator data when indicator changes
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API}/indicators/${selectedIndicator}`);
        setIndicatorData(response.data.data || {});
      } catch (err) {
        console.error("Error fetching indicator data:", err);
        // Fallback to liberal-index endpoint
        try {
          const fallbackResponse = await axios.get(`${API}/liberal-index`);
          setIndicatorData(fallbackResponse.data.data || {});
        } catch (e) {
          setIndicatorData({});
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedIndicator]);

  const rankedCountries = useMemo(() => {
    const countries = Object.entries(indicatorData).map(([code, data]) => ({
      code,
      name: data.name,
      value: data.value,
      year: data.year,
    }));

    let filtered = countries;
    if (filterBucket !== "all") {
      const bucketRanges = {
        high: [0.75, 1.01],
        "medium-high": [0.5, 0.75],
        "medium-low": [0.25, 0.5],
        low: [0, 0.25],
      };
      const [min, max] = bucketRanges[filterBucket];
      filtered = countries.filter((c) => c.value >= min && c.value < max);
    }

    filtered.sort((a, b) => sortOrder === "desc" ? b.value - a.value : a.value - b.value);
    return filtered;
  }, [indicatorData, sortOrder, filterBucket]);

  const handleCountryClick = (country) => {
    if (onCountrySelect) {
      onCountrySelect({
        code: country.code,
        name: country.name,
        indicatorValue: country.value,
        indicatorYear: country.year,
      });
    }
  };

  return (
    <div className="ranking-panel" data-testid="ranking-panel">
      <div className="ranking-header">
        <h2 className="ranking-title">{indicatorName || "Ranking"}</h2>
        <p className="ranking-subtitle">{rankedCountries.length} countries</p>
      </div>

      {/* Filters */}
      <div className="ranking-filters">
        <div className="filter-group">
          <label className="filter-label">
            <Filter className="w-3 h-3" />
            Sort
          </label>
          <Select value={sortOrder} onValueChange={setSortOrder}>
            <SelectTrigger className="filter-select" data-testid="sort-order-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="desc">
                <span className="flex items-center gap-2">
                  <TrendingUp className="w-3 h-3" style={{ color: "#FFF8E1" }} />
                  {lowerIsBetter ? "Worst First (Highest)" : "Best First (Highest)"}
                </span>
              </SelectItem>
              <SelectItem value="asc">
                <span className="flex items-center gap-2">
                  <TrendingDown className="w-3 h-3" style={{ color: "#5D4037" }} />
                  {lowerIsBetter ? "Best First (Lowest)" : "Worst First (Lowest)"}
                </span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Category</label>
          <Select value={filterBucket} onValueChange={setFilterBucket}>
            <SelectTrigger className="filter-select" data-testid="filter-bucket-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Countries</SelectItem>
              <SelectItem value="high">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: "#FFF8E1" }} />
                  {lowerIsBetter ? "High/Worse (0.75-1.0)" : "High/Better (0.75-1.0)"}
                </span>
              </SelectItem>
              <SelectItem value="medium-high">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: "#D7A86E" }} />
                  Medium-High (0.5-0.75)
                </span>
              </SelectItem>
              <SelectItem value="medium-low">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: "#8D6E63" }} />
                  Medium-Low (0.25-0.5)
                </span>
              </SelectItem>
              <SelectItem value="low">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: "#5D4037" }} />
                  {lowerIsBetter ? "Low/Better (0-0.25)" : "Low/Worse (0-0.25)"}
                </span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Ranking List */}
      <ScrollArea className="ranking-list">
        {loading ? (
          <div className="ranking-loading">Loading rankings...</div>
        ) : rankedCountries.length === 0 ? (
          <div className="ranking-empty">No countries match the filter</div>
        ) : (
          <div className="ranking-items">
            {rankedCountries.map((country, index) => {
              const isSelected = selectedCountry === country.code;
              const rank = index + 1;
              const color = getColorForValue(country.value, lowerIsBetter);
              // For lowerIsBetter indicators (populism, gender), invert the bar fill
              // so the "best" country (lowest value) shows the fullest bar
              const barFill = lowerIsBetter
                ? (1 - country.value) * 100
                : country.value * 100;

              return (
                <div
                  key={country.code}
                  className={`ranking-item ${isSelected ? "selected" : ""}`}
                  onClick={() => handleCountryClick(country)}
                  data-testid={`ranking-item-${country.code}`}
                >
                  <div className="ranking-position">
                    <span className="rank-number" style={{ color }}>#{rank}</span>
                  </div>

                  <div className="ranking-info">
                    <span className="ranking-country-name">{country.name}</span>
                    <div className="ranking-bar-container">
                      <div
                        className="ranking-bar"
                        style={{ width: `${barFill}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>

                  <div className="ranking-value">
                    <Badge
                      variant="outline"
                      className="ranking-badge"
                      style={{ color, borderColor: color }}
                    >
                      {country.value.toFixed(2)}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ScrollArea>

      <div className="ranking-footer">
        <span className="ranking-source">Source: V-Dem v15 (2024)</span>
      </div>
    </div>
  );
};

export default RankingPanel;
