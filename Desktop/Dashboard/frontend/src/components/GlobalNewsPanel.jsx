import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Newspaper,
  RefreshCw,
  ChevronUp,
  ChevronDown,
  ExternalLink,
  Clock,
  ChevronLeft,
  ChevronRight,
  MousePointerClick,
} from "lucide-react";
import axios from "axios";
import { formatDistanceToNow } from "date-fns";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// News card skeleton
const NewsCardSkeleton = () => (
  <div className="global-news-card skeleton-news-card">
    <div className="skeleton-news-image" />
    <div className="skeleton-news-body">
      <div className="skeleton-line" style={{ width: "40%" }} />
      <div className="skeleton-line" />
      <div className="skeleton-line" style={{ width: "70%" }} />
    </div>
  </div>
);

// Individual news card
const NewsCard = ({ article }) => {
  const formatDate = (dateString) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return "Recently";
    }
  };

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="global-news-card"
      data-testid="global-news-card"
    >
      {article.urlToImage && (
        <div className="global-news-image-wrapper">
          <img
            src={article.urlToImage}
            alt=""
            className="global-news-image"
            onError={(e) => {
              e.target.parentElement.style.display = "none";
            }}
          />
          <div className="global-news-image-overlay" />
        </div>
      )}
      <div className="global-news-body">
        <div className="global-news-source">
          {article.source?.name || "News"}
        </div>
        <h4 className="global-news-title">{article.title}</h4>
        <div className="global-news-meta">
          <Clock className="w-3 h-3" />
          <span>{formatDate(article.publishedAt)}</span>
        </div>
      </div>
      <ExternalLink className="global-news-link-icon" />
    </a>
  );
};

const GlobalNewsPanel = ({ selectedCountry }) => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const scrollRef = useRef(null);

  const fetchCountryNews = useCallback(async (countryCode) => {
    if (!countryCode) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API}/news/${countryCode}`, {
        params: { page_size: 12 },
      });
      setArticles(response.data.articles || []);
    } catch (err) {
      console.error("Error fetching country news:", err);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch news when selected country changes
  useEffect(() => {
    if (selectedCountry?.code) {
      fetchCountryNews(selectedCountry.code);
    } else {
      setArticles([]);
    }
  }, [selectedCountry?.code, fetchCountryNews]);

  const scrollCarousel = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = 320;
      scrollRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      });
    }
  };

  const hasCountry = !!selectedCountry?.code;
  const countryName = selectedCountry?.name || "";

  return (
    <div
      className={`global-news-panel ${isExpanded ? "expanded" : "collapsed"}`}
      data-testid="global-news-panel"
    >
      {/* Panel Header */}
      <div className="global-news-header">
        <div className="global-news-header-left">
          <Newspaper className="w-4 h-4 text-blue-400" />
          <h3 className="global-news-heading">
            {hasCountry ? `${countryName} — Latest News` : "Country News"}
          </h3>
        </div>

        <div className="global-news-header-right">
          {hasCountry && (
            <button
              className="global-news-refresh-btn"
              onClick={() => fetchCountryNews(selectedCountry.code)}
              disabled={loading}
              data-testid="global-news-refresh"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          )}
          <button
            className="global-news-toggle-btn"
            onClick={() => setIsExpanded(!isExpanded)}
            data-testid="global-news-toggle"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronUp className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="global-news-content">
          {!hasCountry ? (
            /* Placeholder when no country is selected */
            <div className="global-news-empty">
              <MousePointerClick className="w-8 h-8 text-slate-600" />
              <p>Click on a country to see its latest news</p>
            </div>
          ) : (
            /* News Carousel */
            <div className="global-news-carousel-wrapper">
              <button
                className="carousel-nav-btn carousel-nav-left"
                onClick={() => scrollCarousel("left")}
                aria-label="Scroll left"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <div className="global-news-carousel" ref={scrollRef}>
                {loading
                  ? Array.from({ length: 6 }).map((_, i) => (
                    <NewsCardSkeleton key={i} />
                  ))
                  : articles.map((article, index) => (
                    <NewsCard
                      key={`${article.url}-${index}`}
                      article={article}
                    />
                  ))}
                {!loading && articles.length === 0 && (
                  <div className="global-news-empty">
                    <Newspaper className="w-8 h-8 text-slate-600" />
                    <p>No headlines available for {countryName}</p>
                  </div>
                )}
              </div>

              <button
                className="carousel-nav-btn carousel-nav-right"
                onClick={() => scrollCarousel("right")}
                aria-label="Scroll right"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GlobalNewsPanel;
