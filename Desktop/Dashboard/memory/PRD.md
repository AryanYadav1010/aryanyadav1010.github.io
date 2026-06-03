# Rebalance Global Observatory - PRD

## Original Problem Statement
Create a fully responsive, production-ready dashboard web page inspired by https://rebalanceproject.org/. Features an interactive world map with clickable countries, news aggregation, and data visualization using V-Dem datasets.

## Core Requirements
- Dark, policy-oriented, minimal color palette
- Interactive choropleth world map (react-simple-maps)
- Country click -> side panel with flag + news headlines
- News aggregation from NewsAPI.org (LIVE)
- Search bar for countries
- Loading states, skeleton loaders, error handling

## Architecture
- **Frontend**: React + react-simple-maps + d3-scale + shadcn/ui
- **Backend**: FastAPI (serves JSON data files, news API proxy)
- **Data**: Pre-processed CSVs -> JSON files loaded at startup
- **News**: NewsAPI.org (free tier, 100 req/day)

## What's Implemented
- [x] Full-stack dashboard with FastAPI + React
- [x] Interactive choropleth map colored by indicator values
- [x] Four indicators: Liberal Democracy, Gender Inequality, Populism, Combined Index
- [x] Dropdown to switch indicators
- [x] Ranking panel (left side) with sort/filter
- [x] `lower_is_better` auto-sort (Gender Inequality sorts ascending)
- [x] Country detail panel (right side) with LIVE news from NewsAPI.org
- [x] Search bar for countries
- [x] Color scheme: brown-to-yellow gradient (no red)
- [x] Populism data from Global Party Survey (Type_Populism * Type_Partysize_vote)
- [x] Combined Index = avg(Liberal Democracy, 1-Gender Inequality, 1-Populism)

## Data Sources
- **Liberal Democracy**: V-Dem v2x_liberal (179 countries)
- **Gender Inequality**: UNDP GII 2023 (169 countries)
- **Populism**: Global Party Survey 2020 (121 countries)
- **Combined Index**: Computed at startup (171 countries)
- **News**: NewsAPI.org (live, key in .env)

## Known Issues
- `babel-metadata-plugin` disabled in craco.config.js as build workaround (P1)
- NewsAPI free tier: 100 req/day limit, dev-only

## Backlog
- P1: Fix babel-metadata-plugin
- P1: Add more data indicators
- P2: Side-by-side country comparison
