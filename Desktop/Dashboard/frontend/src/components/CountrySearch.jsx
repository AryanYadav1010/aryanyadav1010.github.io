import React, { useState, useEffect, useCallback } from "react";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "../components/ui/command";
import { Search, MapPin } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CountrySearch = ({ onCountrySelect, onCountryHighlight }) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch countries on mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const response = await axios.get(`${API}/countries`);
        setCountries(response.data.countries || []);
      } catch (err) {
        console.error("Error fetching countries:", err);
        setCountries([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCountries();
  }, []);

  // Filter countries based on search
  const filteredCountries = countries.filter((country) =>
    country.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelect = useCallback((country) => {
    if (onCountrySelect) {
      onCountrySelect({
        code: country.code,
        name: country.name,
      });
    }
    setSearch("");
    setOpen(false);
  }, [onCountrySelect]);

  const handleSearchChange = useCallback((value) => {
    setSearch(value);
    setOpen(value.length > 0);
    
    // Highlight first matching country on map
    if (value.length > 0 && onCountryHighlight) {
      const firstMatch = countries.find((c) =>
        c.name.toLowerCase().includes(value.toLowerCase())
      );
      onCountryHighlight(firstMatch?.code || null);
    } else if (onCountryHighlight) {
      onCountryHighlight(null);
    }
  }, [countries, onCountryHighlight]);

  const handleFocus = useCallback(() => {
    if (search.length > 0) {
      setOpen(true);
    }
  }, [search]);

  const handleBlur = useCallback(() => {
    // Delay closing to allow click on items
    setTimeout(() => setOpen(false), 200);
  }, []);

  return (
    <div className="search-overlay" data-testid="country-search">
      <Command 
        className="glass rounded-xl shadow-xl overflow-visible"
        shouldFilter={false}
      >
        <div className="flex items-center border-b border-slate-700/50 px-3">
          <Search className="mr-2 h-4 w-4 shrink-0 text-slate-400" />
          <input
            className="flex h-11 w-full bg-transparent py-3 text-sm text-slate-100 placeholder:text-slate-500 outline-none disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Search for a country..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            onFocus={handleFocus}
            onBlur={handleBlur}
            data-testid="country-search-input"
          />
        </div>
        
        {open && (
          <CommandList className="absolute top-full left-0 right-0 mt-2 glass rounded-xl shadow-xl max-h-[300px] overflow-auto z-50">
            {loading ? (
              <div className="py-6 text-center text-sm text-slate-400">
                Loading countries...
              </div>
            ) : filteredCountries.length === 0 ? (
              <CommandEmpty className="py-6 text-center text-sm text-slate-400">
                No countries found.
              </CommandEmpty>
            ) : (
              <CommandGroup heading="Countries" className="p-2">
                {filteredCountries.slice(0, 10).map((country) => (
                  <CommandItem
                    key={country.code}
                    value={country.name}
                    onSelect={() => handleSelect(country)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer text-slate-200 hover:bg-slate-800/80 data-[selected=true]:bg-slate-800/80"
                    data-testid={`search-result-${country.code}`}
                  >
                    <span className="text-xl">{country.flag}</span>
                    <div className="flex flex-col">
                      <span className="font-medium">{country.name}</span>
                      <span className="text-xs text-slate-500 uppercase">
                        {country.code}
                      </span>
                    </div>
                    <MapPin className="ml-auto h-4 w-4 text-slate-500" />
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        )}
      </Command>
    </div>
  );
};

export default CountrySearch;
