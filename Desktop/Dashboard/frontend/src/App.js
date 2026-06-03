import React, { useState, useCallback, useEffect } from "react";
import "@/App.css";
import WorldMap from "./components/WorldMap";
import CountryPanel from "./components/CountryPanel";
import CountrySearch from "./components/CountrySearch";
import RankingPanel from "./components/RankingPanel";

import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { Globe2, Info, ChevronDown } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [highlightedCountry, setHighlightedCountry] = useState(null);
  const [selectedIndicator, setSelectedIndicator] = useState("liberal");
  const [indicators, setIndicators] = useState([]);

  // Fetch available indicators
  useEffect(() => {
    const fetchIndicators = async () => {
      try {
        const response = await axios.get(`${API}/indicators`);
        setIndicators(response.data.indicators || []);
      } catch (err) {
        console.error("Error fetching indicators:", err);
        // Fallback indicators
        setIndicators([
          { id: "liberal", name: "Liberal Democracy", lower_is_better: false },
          { id: "gender_inequality", name: "Gender Inequality", lower_is_better: true },
          { id: "populism", name: "Populism", lower_is_better: true },
          { id: "combined", name: "Combined Index", lower_is_better: false }
        ]);
      }
    };
    fetchIndicators();
  }, []);

  const handleCountrySelect = useCallback((country) => {
    setSelectedCountry(country);
    setIsPanelOpen(true);
    setHighlightedCountry(null);

    const indicatorName = indicators.find(i => i.id === selectedIndicator)?.name || selectedIndicator;

    toast.success(`Selected: ${country.name}`, {
      description: country.indicatorValue !== undefined
        ? `${indicatorName}: ${country.indicatorValue.toFixed(3)}`
        : "Loading data...",
      duration: 2000,
    });
  }, [indicators, selectedIndicator]);

  const handlePanelClose = useCallback((open) => {
    setIsPanelOpen(open);
    if (!open) {
      setSelectedCountry(null);
    }
  }, []);

  const handleCountryHighlight = useCallback((countryCode) => {
    setHighlightedCountry(countryCode);
  }, []);

  const handleIndicatorChange = useCallback((value) => {
    setSelectedIndicator(value);
    const indicatorName = indicators.find(i => i.id === value)?.name || value;
    toast.info(`Switched to: ${indicatorName}`, { duration: 1500 });
  }, [indicators]);

  const currentIndicator = indicators.find(i => i.id === selectedIndicator);

  return (
    <div className="app-container" data-testid="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <Globe2 className="w-8 h-8 text-blue-500" />
            <div>
              <h1 className="header-title" data-testid="app-title">
                Rebalance Global Observatory
              </h1>
              <p className="header-subtitle">
                Interactive geopolitical data dashboard
              </p>
            </div>
          </div>

          {/* Indicator Dropdown */}
          <div className="indicator-selector" data-testid="indicator-selector">
            <Select value={selectedIndicator} onValueChange={handleIndicatorChange}>
              <SelectTrigger className="indicator-select-trigger">
                <SelectValue placeholder="Select Indicator" />
              </SelectTrigger>
              <SelectContent>
                {indicators.map((indicator) => (
                  <SelectItem key={indicator.id} value={indicator.id}>
                    {indicator.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </header>

      {/* Ranking Panel - Left Side */}
      <RankingPanel
        onCountrySelect={handleCountrySelect}
        selectedCountry={selectedCountry?.code}
        selectedIndicator={selectedIndicator}
        indicatorName={currentIndicator?.name}
        lowerIsBetter={currentIndicator?.lower_is_better || false}
      />

      {/* Search Component */}
      <CountrySearch
        onCountrySelect={handleCountrySelect}
        onCountryHighlight={handleCountryHighlight}
      />

      {/* World Map */}
      <WorldMap
        onCountrySelect={handleCountrySelect}
        selectedCountry={selectedCountry?.code}
        highlightedCountry={highlightedCountry}
        selectedIndicator={selectedIndicator}
        indicatorName={currentIndicator?.name}
        lowerIsBetter={currentIndicator?.lower_is_better || false}
      />

      {/* Country News Panel */}
      <CountryPanel
        isOpen={isPanelOpen}
        onClose={handlePanelClose}
        country={selectedCountry}
        indicatorName={currentIndicator?.name}
        selectedIndicator={selectedIndicator}
      />



      {/* Instructions Overlay */}
      <div className="instructions-overlay" data-testid="instructions">
        <Info className="w-4 h-4 inline-block mr-2 text-slate-500" />
        Click on any country or use the ranking to view details
      </div>

      {/* Toast notifications */}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#0f172a",
            border: "1px solid #1e293b",
            color: "#f8fafc",
          },
        }}
      />
    </div>
  );
}

export default App;
