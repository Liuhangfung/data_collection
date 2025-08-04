package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/joho/godotenv"
)

// Asset represents a financial asset from FMP API
type Asset struct {
	Symbol        string  `json:"symbol"`
	Name          string  `json:"name"`
	Price         float64 `json:"price"`
	MarketCap     float64 `json:"marketCap"`
	Exchange      string  `json:"exchange"`
	Type          string  `json:"type"` // stock, etf, commodity
	Currency      string  `json:"currency"`
	Country       string  `json:"country"`
	Sector        string  `json:"sector"`
	Industry      string  `json:"industry"`
	Volume        int64   `json:"volume"`
	AvgVolume     float64 `json:"avgVolume"`
	Beta          float64 `json:"beta"`
	PE            float64 `json:"pe"`
	EPS           float64 `json:"eps"`
	DividendYield float64 `json:"dividendYield"`
	PreviousClose float64 `json:"previousClose,omitempty"` // Add previous close if available
	Image         string  `json:"image,omitempty"`         // Company logo/image URL
}

// SupabaseUSAsset represents the Supabase-compatible format for US assets
type SupabaseUSAsset struct {
	Symbol           string  `json:"symbol"`
	Ticker           string  `json:"ticker"`
	Name             string  `json:"name"`
	CurrentPrice     float64 `json:"current_price"`
	PreviousClose    float64 `json:"previous_close,omitempty"`
	PercentageChange float64 `json:"percentage_change,omitempty"`
	MarketCap        int64   `json:"market_cap"`
	Volume           int64   `json:"volume"`
	PrimaryExchange  string  `json:"primary_exchange"`
	Country          string  `json:"country"`
	Sector           string  `json:"sector"`
	Industry         string  `json:"industry"`
	AssetType        string  `json:"asset_type"`
	Rank             int     `json:"rank"`
	SnapshotDate     string  `json:"snapshot_date"`
	DataSource       string  `json:"data_source"`
	PriceRaw         float64 `json:"price_raw,omitempty"`
	MarketCapRaw     int64   `json:"market_cap_raw,omitempty"`
	Category         string  `json:"category,omitempty"`
	Image            string  `json:"image,omitempty"` // Add Image field
}

// FMPClient handles API calls to Financial Modeling Prep
type FMPClient struct {
	APIKey     string
	BaseURL    string
	HTTPClient *http.Client
}

// Response structures for different FMP endpoints
type StockListResponse struct {
	Symbol   string  `json:"symbol"`
	Name     string  `json:"name"`
	Price    float64 `json:"price"`
	Exchange string  `json:"exchange"`
	Type     string  `json:"type"`
}

type QuoteResponse struct {
	Symbol        string  `json:"symbol"`
	Name          string  `json:"name"`
	Price         float64 `json:"price"`
	PreviousClose float64 `json:"previousClose"`
	MarketCap     float64 `json:"marketCap"`
	Volume        int64   `json:"volume"`
	AvgVolume     float64 `json:"avgVolume"`
	PE            float64 `json:"pe"`
	EPS           float64 `json:"eps"`
	Beta          float64 `json:"beta"`
	DividendYield float64 `json:"dividendYield"`
	Exchange      string  `json:"exchange"`
}

type ProfileResponse struct {
	Symbol      string `json:"symbol"`
	CompanyName string `json:"companyName"`
	Currency    string `json:"currency"`
	Country     string `json:"country"`
	Sector      string `json:"sector"`
	Industry    string `json:"industry"`
	Exchange    string `json:"exchange"`
	Image       string `json:"image"`
}

// NewFMPClient creates a new FMP API client
func NewFMPClient(apiKey string) *FMPClient {
	return &FMPClient{
		APIKey:  apiKey,
		BaseURL: "https://financialmodelingprep.com",
		HTTPClient: &http.Client{
			Timeout: 120 * time.Second, // Increased timeout for large datasets
		},
	}
}

// makeRequest performs HTTP request with error handling and rate limiting
func (c *FMPClient) makeRequest(url string) ([]byte, error) {
	resp, err := c.HTTPClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("HTTP request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == 429 {
		// Rate limit hit, wait and retry
		time.Sleep(1 * time.Second)
		return c.makeRequest(url)
	}

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	return body, nil
}

// GetAllStocks fetches all stock symbols
func (c *FMPClient) GetAllStocks() ([]StockListResponse, error) {
	url := fmt.Sprintf("%s/api/v3/stock/list?apikey=%s", c.BaseURL, c.APIKey)

	body, err := c.makeRequest(url)
	if err != nil {
		return nil, err
	}

	var stocks []StockListResponse
	if err := json.Unmarshal(body, &stocks); err != nil {
		return nil, fmt.Errorf("failed to parse stocks response: %w", err)
	}

	return stocks, nil
}

// GetAllETFs fetches all ETF symbols
func (c *FMPClient) GetAllETFs() ([]StockListResponse, error) {
	url := fmt.Sprintf("%s/api/v3/etf/list?apikey=%s", c.BaseURL, c.APIKey)

	body, err := c.makeRequest(url)
	if err != nil {
		return nil, err
	}

	var etfs []StockListResponse
	if err := json.Unmarshal(body, &etfs); err != nil {
		return nil, fmt.Errorf("failed to parse ETFs response: %w", err)
	}

	return etfs, nil
}

// GetAllCommodities fetches all commodity symbols
func (c *FMPClient) GetAllCommodities() ([]StockListResponse, error) {
	url := fmt.Sprintf("%s/api/v3/symbol/available-commodities?apikey=%s", c.BaseURL, c.APIKey)

	body, err := c.makeRequest(url)
	if err != nil {
		return nil, err
	}

	var commodities []StockListResponse
	if err := json.Unmarshal(body, &commodities); err != nil {
		return nil, fmt.Errorf("failed to parse commodities response: %w", err)
	}

	return commodities, nil
}

// ConvertToUSD converts market cap from local currency to USD
func ConvertToUSD(marketCap float64, currency string) float64 {
	// Exchange rates (approximate - in production, use real-time rates)
	rates := map[string]float64{
		"USD": 1.0,
		"JPY": 0.0067,  // Japanese Yen
		"EUR": 1.08,    // Euro
		"GBP": 1.27,    // British Pound
		"CAD": 0.73,    // Canadian Dollar
		"CHF": 1.11,    // Swiss Franc
		"CNY": 0.138,   // Chinese Yuan
		"KRW": 0.00075, // Korean Won
		"ARS": 0.001,   // Argentine Peso
		"INR": 0.012,   // Indian Rupee
		"BRL": 0.18,    // Brazilian Real
		"HKD": 0.128,   // Hong Kong Dollar
		"SGD": 0.74,    // Singapore Dollar
		"AUD": 0.66,    // Australian Dollar
		"MXN": 0.058,   // Mexican Peso
		"ZAR": 0.055,   // South African Rand
		"SEK": 0.092,   // Swedish Krona
		"NOK": 0.092,   // Norwegian Krone
		"DKK": 0.145,   // Danish Krone
		"PLN": 0.247,   // Polish Zloty
		"CZK": 0.043,   // Czech Koruna
		"HUF": 0.0026,  // Hungarian Forint
		"RUB": 0.010,   // Russian Ruble
		"TRY": 0.029,   // Turkish Lira
	}

	if rate, exists := rates[currency]; exists {
		return marketCap * rate
	}

	// If currency not found, assume it's already in USD
	return marketCap
}

// GetQuotes fetches detailed quotes for multiple symbols in parallel
func (c *FMPClient) GetQuotes(symbols []string) ([]QuoteResponse, error) {
	// Split symbols into batches for batch API calls (FMP supports comma-separated symbols)
	batchSize := 30 // Reduced for larger responses with PreviousClose data
	var allQuotes []QuoteResponse
	var mu sync.Mutex
	var wg sync.WaitGroup

	// Channel to limit concurrent requests
	semaphore := make(chan struct{}, 25) // Max 25 concurrent requests (within 3000/min limit)

	for i := 0; i < len(symbols); i += batchSize {
		end := i + batchSize
		if end > len(symbols) {
			end = len(symbols)
		}

		batch := symbols[i:end]

		wg.Add(1)
		go func(batch []string) {
			defer wg.Done()

			// Acquire semaphore
			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			// Join symbols with comma for batch request
			symbolsStr := ""
			for j, symbol := range batch {
				if j > 0 {
					symbolsStr += ","
				}
				symbolsStr += symbol
			}

			url := fmt.Sprintf("%s/api/v3/quote/%s?apikey=%s", c.BaseURL, symbolsStr, c.APIKey)

			body, err := c.makeRequest(url)
			if err != nil {
				log.Printf("Error fetching quotes for batch: %v", err)
				return
			}

			var quotes []QuoteResponse
			if err := json.Unmarshal(body, &quotes); err != nil {
				log.Printf("Error parsing quotes for batch: %v", err)
				return
			}

			mu.Lock()
			allQuotes = append(allQuotes, quotes...)
			mu.Unlock()
		}(batch)
	}

	wg.Wait()
	return allQuotes, nil
}

// GetProfiles fetches company profiles for symbols in parallel
func (c *FMPClient) GetProfiles(symbols []string) (map[string]ProfileResponse, error) {
	profiles := make(map[string]ProfileResponse)
	var mu sync.Mutex
	var wg sync.WaitGroup

	// Channel to limit concurrent requests (3,000/min = 50/sec rate limit)
	semaphore := make(chan struct{}, 15) // Increased for better performance

	for _, symbol := range symbols {
		wg.Add(1)
		go func(symbol string) {
			defer wg.Done()

			// Acquire semaphore
			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			url := fmt.Sprintf("%s/api/v3/profile/%s?apikey=%s", c.BaseURL, symbol, c.APIKey)

			body, err := c.makeRequest(url)
			if err != nil {
				log.Printf("Error fetching profile for %s: %v", symbol, err)
				return
			}

			var profileList []ProfileResponse
			if err := json.Unmarshal(body, &profileList); err != nil {
				log.Printf("Error parsing profile for %s: %v", symbol, err)
				return
			}

			if len(profileList) > 0 {
				mu.Lock()
				profiles[symbol] = profileList[0]
				mu.Unlock()
			}
		}(symbol)
	}

	wg.Wait()
	return profiles, nil
}

// FilterSymbolsByCountry filters symbols based on their profiles to only include target countries
func FilterSymbolsByCountry(symbols []string, profiles map[string]ProfileResponse, targetCountries map[string]bool) []string {
	var filteredSymbols []string

	for _, symbol := range symbols {
		if profile, exists := profiles[symbol]; exists {
			if targetCountries[profile.Country] {
				filteredSymbols = append(filteredSymbols, symbol)
			}
		} else {
			// If no profile data, include major US exchanges by symbol pattern
			if isLikelyUSStock(symbol) && targetCountries["US"] {
				filteredSymbols = append(filteredSymbols, symbol)
			}
		}
	}

	return filteredSymbols
}

// isUSExchange checks if an exchange is NYSE or NASDAQ only
func isUSExchange(exchange string) bool {
	usExchanges := map[string]bool{
		"NASDAQ": true,
		"NYSE":   true,
	}
	return usExchanges[exchange]
}

// isETFOrFund checks if a symbol/name indicates an ETF or mutual fund
func isETFOrFund(symbol, name string) bool {
	// Check symbol patterns (ETFs/funds often have 4-5+ characters)
	if len(symbol) >= 4 {
		// Common ETF/fund suffixes
		etfSuffixes := []string{"ETF", "FUND", "IDX", "INDEX"}
		symbolUpper := strings.ToUpper(symbol)
		for _, suffix := range etfSuffixes {
			if strings.Contains(symbolUpper, suffix) {
				return true
			}
		}
	}

	// Check name for fund/ETF keywords - use word boundaries to avoid false positives
	nameUpper := strings.ToUpper(name)

	// Check for exact word matches or specific patterns
	if strings.Contains(nameUpper, " ETF") || strings.Contains(nameUpper, "ETF ") || strings.HasSuffix(nameUpper, " ETF") {
		return true
	}

	fundKeywords := []string{
		"FUND", "INDEX", "TRUST", "PORTFOLIO",
		"VANGUARD", "ISHARES", "SPDR", "FIDELITY",
		"ADMIRAL", "INSTITUTIONAL", "INVESTOR",
	}

	for _, keyword := range fundKeywords {
		if strings.Contains(nameUpper, keyword) {
			return true
		}
	}

	return false
}

// isPreferredShare checks if a symbol represents a preferred share or warrant
func isPreferredShare(symbol string) bool {
	// Preferred shares typically have suffixes like -PA, -PB, -PC, -PD, -PE, -PF, etc.
	// Warrants have suffixes like -WT, -WS
	// Units have suffixes like -U
	if strings.Contains(symbol, "-P") ||
		strings.Contains(symbol, "-W") ||
		strings.Contains(symbol, "-U") ||
		strings.Contains(symbol, ".P") ||
		strings.Contains(symbol, ".W") ||
		strings.Contains(symbol, ".U") {
		return true
	}

	// Check for common preferred share patterns
	if strings.Contains(symbol, "PR") && len(symbol) > 4 {
		return true
	}

	return false
}

// isLikelyUSStock checks if a symbol is likely from a major US exchange
func isLikelyUSStock(symbol string) bool {
	// US stocks typically don't have country suffixes and are 1-5 characters
	if len(symbol) >= 1 && len(symbol) <= 5 {
		// Check if it doesn't contain country suffixes
		if !containsCountrySuffix(symbol) {
			return true
		}
	}
	return false
}

// containsCountrySuffix checks if symbol contains common country suffixes
func containsCountrySuffix(symbol string) bool {
	suffixes := []string{".NS", ".BO", ".TO", ".L", ".PA", ".DE", ".SW", ".T", ".KS", ".KQ", ".HK", ".SS", ".SZ"}
	for _, suffix := range suffixes {
		if len(symbol) > len(suffix) && symbol[len(symbol)-len(suffix):] == suffix {
			return true
		}
	}
	return false
}

// GetAllAssetsWithMarketCap fetches all assets and enriches them with market cap and profile data
func (c *FMPClient) GetAllAssetsWithMarketCap() ([]Asset, error) {
	log.Println("🚀 Starting US stock collection...")
	log.Println("🇺🇸 Focus: NYSE and NASDAQ stocks only - no ETFs/funds")
	log.Println("💰 USD market caps with $40B+ filter")
	log.Println("📊 Minimum market cap filter: $40 billion USD")

	var allAssets []Asset
	var wg sync.WaitGroup
	var mu sync.Mutex

	// Note: Country filtering removed - we filter by US exchanges instead for faster processing

	// Channel for collecting assets from different sources
	assetChan := make(chan []Asset, 1) // Only stocks for now

	// Fetch stocks in parallel
	wg.Add(1)
	go func() {
		defer wg.Done()
		log.Println("📈 Fetching stocks...")

		stocks, err := c.GetAllStocks()
		if err != nil {
			log.Printf("Error fetching stocks: %v", err)
			return
		}

		log.Printf("✅ Found %d stocks", len(stocks))

		// Convert to symbols and get quotes for ALL stocks (fast market cap filtering)
		allSymbols := make([]string, len(stocks))
		for i, stock := range stocks {
			allSymbols[i] = stock.Symbol
		}

		log.Printf("💰 Getting quotes for ALL %d stocks to filter by $40B+ market cap first...", len(allSymbols))
		quotes, err := c.GetQuotes(allSymbols)
		if err != nil {
			log.Printf("Error fetching stock quotes: %v", err)
			return
		}

		// FAST FILTER: Only keep stocks with $40B+ market cap and US exchanges (before expensive profile fetch)
		const minMarketCapUSD = 40e9 // $40 billion USD minimum
		var highValueSymbols []string
		var filteredQuotes []QuoteResponse

		for _, quote := range quotes {
			// Quick filters first: market cap, exchange, ETF/fund exclusion
			if quote.MarketCap >= minMarketCapUSD &&
				isUSExchange(quote.Exchange) &&
				!isETFOrFund(quote.Symbol, quote.Name) {
				highValueSymbols = append(highValueSymbols, quote.Symbol)
				filteredQuotes = append(filteredQuotes, quote)
			}
		}

		log.Printf("🎯 Fast filter: Found %d stocks with $40B+ market cap on US exchanges", len(highValueSymbols))

		// NOW get profiles only for high-value stocks (much faster - only ~500 instead of 15k!)
		log.Printf("📋 Getting profiles for %d high-value stocks only...", len(highValueSymbols))
		profiles, err := c.GetProfiles(highValueSymbols)
		if err != nil {
			log.Printf("Error fetching profiles: %v", err)
		}
		log.Printf("✅ Retrieved profiles for %d high-value symbols", len(profiles))

		// Combine data into final assets with profile data
		var stockAssets []Asset
		for _, quote := range filteredQuotes {
			// Basic data validation (already filtered for market cap, exchange, ETFs)
			if quote.Price <= 0 || quote.Price > 10000 { // Reasonable price range
				continue
			}

			// Get currency from profile or default to USD
			currency := "USD"
			if profile, exists := profiles[quote.Symbol]; exists {
				if profile.Currency != "" {
					currency = profile.Currency
				}
			}

			// Convert market cap to USD (should already be USD for US exchanges)
			marketCapUSD := ConvertToUSD(quote.MarketCap, currency)

			asset := Asset{
				Symbol:        quote.Symbol,
				Name:          quote.Name,
				Price:         quote.Price,
				PreviousClose: quote.PreviousClose,
				MarketCap:     marketCapUSD,
				Exchange:      quote.Exchange,
				Type:          "stock",
				Currency:      "USD", // All converted to USD
				Volume:        quote.Volume,
				AvgVolume:     quote.AvgVolume,
				Beta:          quote.Beta,
				PE:            quote.PE,
				EPS:           quote.EPS,
				DividendYield: quote.DividendYield,
			}

			// Add profile data if available
			if profile, exists := profiles[quote.Symbol]; exists {
				asset.Country = profile.Country
				asset.Sector = profile.Sector
				asset.Industry = profile.Industry
				asset.Image = profile.Image
			}

			stockAssets = append(stockAssets, asset)
		}

		assetChan <- stockAssets
	}()

	// Note: Commenting out ETFs and commodities for now - focusing on US stocks only
	// TODO: Add ETF and commodity processing later

	// Wait for all goroutines to complete
	go func() {
		wg.Wait()
		close(assetChan)
	}()

	// Collect all assets
	for assets := range assetChan {
		mu.Lock()
		allAssets = append(allAssets, assets...)
		mu.Unlock()
	}

	log.Printf("🎯 Total assets collected: %d", len(allAssets))
	return allAssets, nil
}

// RankByMarketCap sorts assets by market cap in descending order and filters for $40B+ USD
func RankByMarketCap(assets []Asset) []Asset {
	const minMarketCapUSD = 40e9 // $40 billion USD minimum

	// Filter for assets with market cap >= $40B USD
	validAssets := make([]Asset, 0, len(assets))
	for _, asset := range assets {
		if asset.MarketCap >= minMarketCapUSD {
			validAssets = append(validAssets, asset)
		}
	}

	// Sort by market cap descending
	sort.Slice(validAssets, func(i, j int) bool {
		return validAssets[i].MarketCap > validAssets[j].MarketCap
	})

	log.Printf("🎯 Filtered to %d assets with $40B+ USD market cap", len(validAssets))
	return validAssets
}

// ConvertToSupabaseFormatUS converts Asset to SupabaseUSAsset format
func ConvertToSupabaseFormatUS(assets []Asset) []SupabaseUSAsset {
	today := time.Now().Format("2006-01-02")
	supabaseAssets := make([]SupabaseUSAsset, len(assets))

	for i, asset := range assets {
		// Calculate percentage change if previous close is available
		var percentageChange float64
		if asset.PreviousClose > 0 {
			percentageChange = ((asset.Price - asset.PreviousClose) / asset.PreviousClose) * 100
		}

		// Truncate strings to match Supabase field limits
		symbol := truncateStringUS(asset.Symbol, 50)
		name := truncateStringUS(asset.Name, 200)
		exchange := truncateStringUS(asset.Exchange, 50)
		country := truncateStringUS(asset.Country, 50)
		sector := truncateStringUS(asset.Sector, 100)
		industry := truncateStringUS(asset.Industry, 100)

		supabaseAssets[i] = SupabaseUSAsset{
			Symbol:           symbol,
			Ticker:           symbol, // Same as symbol
			Name:             name,
			CurrentPrice:     asset.Price,
			PreviousClose:    asset.PreviousClose,
			PercentageChange: percentageChange,
			MarketCap:        int64(asset.MarketCap), // Already in USD
			Volume:           asset.Volume,
			PrimaryExchange:  exchange,
			Country:          country,
			Sector:           sector,
			Industry:         industry,
			AssetType:        "stock",
			Rank:             i + 1, // Ranking position
			SnapshotDate:     today,
			DataSource:       "FMP",
			PriceRaw:         asset.Price,
			MarketCapRaw:     int64(asset.MarketCap),
			Category:         "stocks",
			Image:            asset.Image, // Add Image field
		}
	}

	return supabaseAssets
}

// truncateStringUS truncates a string to specified length
func truncateStringUS(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen]
}

// SaveUSToSupabase saves the US assets in Supabase-compatible format
func SaveUSToSupabase(assets []Asset, filename string) error {
	supabaseAssets := ConvertToSupabaseFormatUS(assets)

	jsonData, err := json.MarshalIndent(supabaseAssets, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal Supabase assets: %v", err)
	}

	err = os.WriteFile(filename, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write file: %v", err)
	}

	log.Printf("💾 Saved %d US assets to %s (Supabase format)", len(supabaseAssets), filename)
	return nil
}

// SaveToJSON saves assets to a JSON file
func SaveToJSON(assets []Asset, filename string) error {
	data, err := json.MarshalIndent(assets, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	if err := os.WriteFile(filename, data, 0644); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}

// Helper function for min
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// FormatMarketCap formats market cap for display
func FormatMarketCap(marketCap float64) string {
	if marketCap >= 1e12 {
		return fmt.Sprintf("$%.2fT", marketCap/1e12)
	} else if marketCap >= 1e9 {
		return fmt.Sprintf("$%.2fB", marketCap/1e9)
	} else if marketCap >= 1e6 {
		return fmt.Sprintf("$%.2fM", marketCap/1e6)
	} else if marketCap >= 1e3 {
		return fmt.Sprintf("$%.2fK", marketCap/1e3)
	}
	return fmt.Sprintf("$%.2f", marketCap)
}

func main() {
	// Load environment variables
	if err := godotenv.Load(".env"); err != nil {
		log.Printf("Warning: Could not load .env file: %v", err)
	}

	apiKey := os.Getenv("FMP_API_KEY")
	if apiKey == "" {
		log.Fatal("❌ FMP_API_KEY key not found in environment variables")
	}

	log.Println("🔑 FMP API key loaded successfully")

	// Create FMP client
	client := NewFMPClient(apiKey)

	// Get all assets with market cap data
	startTime := time.Now()
	assets, err := client.GetAllAssetsWithMarketCap()
	if err != nil {
		log.Fatalf("❌ Error fetching assets: %v", err)
	}

	log.Printf("⚡ Data collection completed in %v", time.Since(startTime))

	// Rank by market cap
	rankedAssets := RankByMarketCap(assets)

	log.Printf("📊 NYSE/NASDAQ stocks only ($40B+ USD) ranked by market cap. Top 10:")
	for i, asset := range rankedAssets[:min(10, len(rankedAssets))] {
		log.Printf("%d. %s (%s) - %s - %s",
			i+1,
			asset.Symbol,
			asset.Name,
			FormatMarketCap(asset.MarketCap),
			asset.Type,
		)
	}

	// Save only in Supabase-compatible format (legacy JSON removed)
	filename := "assets/stocks/us_supabase.json"
	if err := SaveUSToSupabase(rankedAssets, filename); err != nil {
		log.Printf("❌ Failed to save Supabase results: %v", err)
	} else {
		log.Printf("💾 Supabase data saved to %s (temporary - will be cleaned up)", filename)
	}

	log.Printf("✅ Process completed successfully! Found and ranked %d NYSE/NASDAQ stocks only ($40B+ USD)", len(rankedAssets))
}
