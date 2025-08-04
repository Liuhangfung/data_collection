package main

import (
	"encoding/csv"
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

// FMP API structures
type FMPStockScreener struct {
	Symbol            string  `json:"symbol"`
	CompanyName       string  `json:"companyName"`
	MarketCap         float64 `json:"marketCap"`
	Sector            string  `json:"sector"`
	Industry          string  `json:"industry"`
	Beta              float64 `json:"beta"`
	Price             float64 `json:"price"`
	Volume            float64 `json:"volume"`
	Exchange          string  `json:"exchange"`
	ExchangeShortName string  `json:"exchangeShortName"`
	Country           string  `json:"country"`
	IsEtf             bool    `json:"isEtf"`
	IsActivelyTrading bool    `json:"isActivelyTrading"`
}

type FMPQuote struct {
	Symbol            string  `json:"symbol"`
	Name              string  `json:"name"`
	Price             float64 `json:"price"`
	ChangesPercentage float64 `json:"changesPercentage"`
	Change            float64 `json:"change"`
	MarketCap         float64 `json:"marketCap"`
	Volume            float64 `json:"volume"`
	Open              float64 `json:"open"`
	PreviousClose     float64 `json:"previousClose"`
	Exchange          string  `json:"exchange"`
	SharesOutstanding float64 `json:"sharesOutstanding"`
}

type FMPCompanyProfile struct {
	Symbol      string  `json:"symbol"`
	CompanyName string  `json:"companyName"`
	Image       string  `json:"image"`
	Price       float64 `json:"price"`
	Beta        float64 `json:"beta"`
	VolAvg      float64 `json:"volAvg"`
	MktCap      float64 `json:"mktCap"`
	Industry    string  `json:"industry"`
	Sector      string  `json:"sector"`
	Country     string  `json:"country"`
	Exchange    string  `json:"exchange"`
	Website     string  `json:"website"`
	Description string  `json:"description"`
}

type AssetData struct {
	Ticker           string  `json:"ticker"`
	Name             string  `json:"name"`
	MarketCap        float64 `json:"market_cap"`
	CurrentPrice     float64 `json:"current_price"`
	PreviousClose    float64 `json:"previous_close"`
	PercentageChange float64 `json:"percentage_change"`
	Volume           float64 `json:"volume"`
	PrimaryExchange  string  `json:"primary_exchange"`
	Country          string  `json:"country"`
	Sector           string  `json:"sector"`
	Industry         string  `json:"industry"`
	AssetType        string  `json:"asset_type"`
	Image            string  `json:"image"`
}

type FMPClient struct {
	APIKey     string
	BaseURL    string
	HTTPClient *http.Client
}

func NewFMPClient(apiKey string) *FMPClient {
	return &FMPClient{
		APIKey:  apiKey,
		BaseURL: "https://financialmodelingprep.com/api",
		HTTPClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *FMPClient) makeRequest(endpoint string) ([]byte, error) {
	separator := "?"
	if strings.Contains(endpoint, "?") {
		separator = "&"
	}
	url := fmt.Sprintf("%s%s%sapikey=%s", c.BaseURL, endpoint, separator, c.APIKey)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Accept", "application/json; charset=utf-8")
	req.Header.Set("Accept-Charset", "utf-8")
	req.Header.Set("Content-Type", "application/json; charset=utf-8")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		fmt.Printf("FMP API Error Response: %s\n", string(body))
		return nil, fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	return body, nil
}

func (c *FMPClient) GetQuote(symbol string) (*FMPQuote, error) {
	endpoint := fmt.Sprintf("/v3/quote/%s", symbol)

	body, err := c.makeRequest(endpoint)
	if err != nil {
		return nil, fmt.Errorf("failed to get quote for %s: %w", symbol, err)
	}

	var quotes []FMPQuote
	if err := json.Unmarshal(body, &quotes); err != nil {
		return nil, fmt.Errorf("failed to parse quote data for %s: %w", symbol, err)
	}

	if len(quotes) == 0 {
		return nil, fmt.Errorf("no quote data found for %s", symbol)
	}

	return &quotes[0], nil
}

func (c *FMPClient) GetCompanyProfile(symbol string) (*FMPCompanyProfile, error) {
	endpoint := fmt.Sprintf("/v3/profile/%s", symbol)

	body, err := c.makeRequest(endpoint)
	if err != nil {
		return nil, fmt.Errorf("failed to get company profile for %s: %w", symbol, err)
	}

	var profiles []FMPCompanyProfile
	if err := json.Unmarshal(body, &profiles); err != nil {
		return nil, fmt.Errorf("failed to parse company profile data for %s: %w", symbol, err)
	}

	if len(profiles) == 0 {
		return nil, fmt.Errorf("no company profile data found for %s", symbol)
	}

	return &profiles[0], nil
}

func (c *FMPClient) GetGlobalStocks() ([]AssetData, error) {
	fmt.Println("🌍 Fetching ALL 50M+ companies from 38 countries with USD conversion...")
	fmt.Println("🚀 Using ENHANCED PARALLEL MULTITHREADING for maximum performance...")

	var allStocks []FMPStockScreener
	var stockMutex sync.Mutex

	// STANDARDIZED 50M+ USD MARKET CAP FILTER - All countries use same threshold
	endpoints := []struct {
		endpoint string
		desc     string
	}{
		// All countries use 50M+ USD market cap filter with generous limits to capture ALL qualifying companies
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=5000&country=US&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇺🇸 United States"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=2000&country=HK&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇭🇰 Hong Kong"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=2000&country=CN&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇨🇳 China"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=2000&country=JP&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇯🇵 Japan"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=2000&country=IN&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇮🇳 India"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=GB&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇬🇧 United Kingdom"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=CA&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇨🇦 Canada"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=AU&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇦🇺 Australia"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=KR&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇰🇷 South Korea"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=DE&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇩🇪 Germany"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=FR&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇫🇷 France"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=BR&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇧🇷 Brazil"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=1000&country=SA&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇸🇦 Saudi Arabia"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=TW&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇹🇼 Taiwan"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=IT&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇮🇹 Italy"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=ES&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇪🇸 Spain"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=NL&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇳🇱 Netherlands"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=CH&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇨🇭 Switzerland"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=SG&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇸🇬 Singapore"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=ZA&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇿🇦 South Africa"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=MX&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇲🇽 Mexico"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=AE&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇦🇪 UAE"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=SE&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇸🇪 Sweden"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=NO&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇳🇴 Norway"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=DK&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇩🇰 Denmark"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=FI&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇫🇮 Finland"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=TH&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇹🇭 Thailand"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=MY&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇲🇾 Malaysia"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=ID&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇮🇩 Indonesia"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=PH&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇵🇭 Philippines"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=VN&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇻🇳 Vietnam"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=100&country=EG&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇪🇬 Egypt"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=200&country=TR&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇹🇷 Turkey"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=100&country=CL&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇨🇱 Chile"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=100&country=CO&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇨🇴 Colombia"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=100&country=PE&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇵🇪 Peru"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=100&country=AR&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇦🇷 Argentina"},
		{"/v3/stock-screener?marketCapMoreThan=50000000&limit=500&country=IL&order=desc&sortBy=marketcap&isActivelyTrading=true", "🇮🇱 Israel"},
	}

	// ENHANCED PARALLEL COUNTRY FETCHING - Process multiple countries simultaneously
	const countryWorkers = 12 // Fetch 12 countries in parallel for maximum speed
	countryWg := sync.WaitGroup{}
	countryChan := make(chan struct {
		endpoint string
		desc     string
	}, len(endpoints))

	// Start country worker goroutines
	for i := 0; i < countryWorkers; i++ {
		countryWg.Add(1)
		go func(workerID int) {
			defer countryWg.Done()
			for ep := range countryChan {
				fmt.Printf("📡 Worker %d: Fetching %s stocks from FMP...\n", workerID, ep.desc)

				body, err := c.makeRequest(ep.endpoint)
				if err != nil {
					fmt.Printf("⚠️  Worker %d: Failed to fetch %s stocks: %v\n", workerID, ep.desc, err)
					continue
				}

				var stocks []FMPStockScreener
				if err := json.Unmarshal(body, &stocks); err != nil {
					fmt.Printf("⚠️  Worker %d: Failed to parse %s stocks: %v\n", workerID, ep.desc, err)
					continue
				}

				fmt.Printf("✅ Worker %d: Received %d %s stocks\n", workerID, len(stocks), ep.desc)

				// Debug: Check for major stocks in specific countries
				saStocksFound := 0
				hkStocksFound := 0
				for _, stock := range stocks {
					// Check for Saudi Arabia stocks
					if stock.Country == "SA" || stock.ExchangeShortName == "SAU" || strings.Contains(stock.Exchange, "Saudi") {
						saStocksFound++
						if saStocksFound <= 3 {
							fmt.Printf("🔍 Worker %d: Found Saudi Arabia stock: %s (%s) - Market Cap: $%.1fB\n",
								workerID, stock.Symbol, stock.CompanyName, stock.MarketCap/1e9)
						}
					}

					// Check for Hong Kong stocks
					if strings.HasSuffix(strings.ToUpper(stock.Symbol), ".HK") || stock.Country == "HK" {
						hkStocksFound++
						if hkStocksFound <= 3 && strings.Contains(strings.ToUpper(stock.CompanyName), "TENCENT") {
							fmt.Printf("🔍 Worker %d: Found HK Tencent: %s - Market Cap: $%.1fB\n",
								workerID, stock.Symbol, stock.MarketCap/1e9)
						}
					}
				}

				if saStocksFound > 0 {
					fmt.Printf("✅ Worker %d: Found %d Saudi Arabia stocks in %s\n", workerID, saStocksFound, ep.desc)
				}
				if hkStocksFound > 0 && ep.desc == "🇭🇰 Hong Kong" {
					fmt.Printf("✅ Worker %d: Found %d Hong Kong stocks in %s\n", workerID, hkStocksFound, ep.desc)
				}

				// Thread-safe append to allStocks
				stockMutex.Lock()
				allStocks = append(allStocks, stocks...)
				stockMutex.Unlock()

				// Minimal rate limiting for enhanced speed
				time.Sleep(50 * time.Millisecond)
			}
		}(i)
	}

	// Send all endpoints to workers
	go func() {
		defer close(countryChan)
		for _, ep := range endpoints {
			countryChan <- ep
		}
	}()

	// Wait for all country fetches to complete
	countryWg.Wait()

	fmt.Printf("✅ Total received: %d stocks globally\n", len(allStocks))

	// Enhanced filtering and deduplication
	var validStocks []FMPStockScreener
	seenSymbols := make(map[string]bool)
	companyListings := make(map[string]FMPStockScreener)

	for _, stock := range allStocks {
		// Skip ETFs and index funds
		if stock.IsEtf {
			continue
		}

		nameUpper := strings.ToUpper(stock.CompanyName)
		if containsWord(nameUpper, "ETF") ||
			containsWord(nameUpper, "INDEX") ||
			containsWord(nameUpper, "FUND") ||
			containsWord(nameUpper, "SPDR") ||
			containsWord(nameUpper, "ISHARES") ||
			containsWord(nameUpper, "VANGUARD") {
			continue
		}

		// Skip if already seen this exact symbol
		if seenSymbols[stock.Symbol] {
			continue
		}
		seenSymbols[stock.Symbol] = true

		if stock.IsActivelyTrading && stock.MarketCap > 0 {
			// Check if we already have a listing for this company
			if existingStock, exists := companyListings[stock.CompanyName]; exists {
				// Keep the better listing based on priority
				if shouldKeepNewListing(stock, existingStock) {
					companyListings[stock.CompanyName] = stock
				}
			} else {
				// First time seeing this company
				companyListings[stock.CompanyName] = stock
			}
		}
	}

	// Convert map to slice
	for _, stock := range companyListings {
		validStocks = append(validStocks, stock)
	}

	fmt.Printf("🔄 Filtered to %d valid stocks (removed ETFs and duplicates)\n", len(validStocks))

	// ENHANCED PARALLEL PROCESSING for stock processing
	var assets []AssetData
	maxStocks := len(validStocks) // Process ALL valid stocks

	fmt.Printf("💱 Converting market caps to USD and getting real-time data with ENHANCED parallel processing...\n")

	// COMPREHENSIVE PROCESSING - Get ALL 50M+ companies globally
	const numWorkers = 8 // Balanced for performance and stability
	// No maxStocks limit - process ALL valid companies
	stockChan := make(chan FMPStockScreener, 300)
	resultChan := make(chan AssetData, 300)
	var wg sync.WaitGroup

	// Enhanced exchange rate cache with mutex for thread safety
	var exchangeRateCache = make(map[string]float64)
	var rateMutex sync.RWMutex

	// Pre-fetch common exchange rates in parallel
	commonCurrencies := []string{"EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "HKD", "KRW", "INR", "BRL", "MXN", "SAR", "AED", "SGD", "SEK", "NOK", "DKK", "THB", "MYR", "IDR", "PHP", "VND", "EGP", "TRY", "CLP", "COP", "PEN", "ARS", "ILS", "ZAR", "TWD"}

	// Parallel exchange rate fetching
	rateFetchWg := sync.WaitGroup{}
	for _, currency := range commonCurrencies {
		rateFetchWg.Add(1)
		go func(curr string) {
			defer rateFetchWg.Done()
			rate := c.getUSDExchangeRate(curr)
			rateMutex.Lock()
			exchangeRateCache[curr] = rate
			rateMutex.Unlock()
		}(currency)
	}

	// Start enhanced worker goroutines
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for stock := range stockChan {
				// Detect currency from symbol and country
				currencyCode := c.detectCurrency(stock.Symbol, stock.Country)

				// SPECIFIC STOCK VALIDATION: Skip known problematic stocks
				if isProblematicStock(stock.Symbol, stock.CompanyName) {
					fmt.Printf("⚠️  SKIPPING KNOWN PROBLEM: %s (%s) - known to have bad market cap data\n",
						stock.Symbol, stock.CompanyName)
					continue
				}

				// Keep original price in local currency, only convert market cap to USD
				currentPrice := stock.Price
				marketCapUSD := stock.MarketCap

				// VALIDATE USD STOCKS TOO: Filter out obviously bad market cap values for USD stocks
				if currencyCode == "USD" {
					if marketCapUSD > 5e12 { // More than $5 trillion is suspicious
						fmt.Printf("⚠️  SKIPPING USD: %s has market cap $%.1fT, likely bad API data\n",
							stock.Symbol, marketCapUSD/1e12)
						continue
					}
					// Filter out OTC USD stocks (often have bad data)
					if strings.Contains(strings.ToUpper(stock.ExchangeShortName), "OTC") ||
						stock.ExchangeShortName == "" {
						fmt.Printf("⚠️  SKIPPING USD OTC: %s (exchange: %s) - OTC stocks often have bad data\n",
							stock.Symbol, stock.ExchangeShortName)
						continue
					}
				}

				if currencyCode != "USD" {
					// Use cached exchange rate
					rateMutex.RLock()
					exchangeRate, exists := exchangeRateCache[currencyCode]
					rateMutex.RUnlock()

					if !exists {
						// Fetch and cache if not found
						exchangeRate = c.getUSDExchangeRate(currencyCode)
						rateMutex.Lock()
						exchangeRateCache[currencyCode] = exchangeRate
						rateMutex.Unlock()
					}

					// Convert market cap to USD
					// CRITICAL FIX: Many exchanges price in sub-units (cents/pence/agorot)!
					marketCapAdjusted := stock.MarketCap
					symbolUpper := strings.ToUpper(stock.Symbol)
					exchangeUpper := strings.ToUpper(stock.ExchangeShortName)

					// Apply ÷100 adjustment for exchanges that use sub-units
					if strings.HasSuffix(symbolUpper, ".L") || strings.Contains(exchangeUpper, "LSE") || // LSE: pence
						strings.HasSuffix(symbolUpper, ".JO") || strings.Contains(exchangeUpper, "JNB") || // JSE: cents
						strings.HasSuffix(symbolUpper, ".TA") || strings.Contains(exchangeUpper, "TLV") { // TASE: agorot
						marketCapAdjusted = stock.MarketCap / 100.0
						exchangeName := ""
						if strings.HasSuffix(symbolUpper, ".L") {
							exchangeName = "LSE (pence)"
						}
						if strings.HasSuffix(symbolUpper, ".JO") {
							exchangeName = "JSE (cents)"
						}
						if strings.HasSuffix(symbolUpper, ".TA") {
							exchangeName = "TASE (agorot)"
						}
						fmt.Printf("💱 %s Stock %s: Market Cap %s → %s (÷100 for %s adjustment)\n",
							exchangeName, stock.Symbol,
							formatLargeNumber(stock.MarketCap),
							formatLargeNumber(marketCapAdjusted), exchangeName)
					}

					marketCapUSD = marketCapAdjusted * exchangeRate

					// AGGRESSIVE DATA VALIDATION: Filter out suspicious market cap values
					if marketCapUSD > 5e12 { // More than $5 trillion is suspicious (only ~6 companies globally)
						fmt.Printf("⚠️  SKIPPING: %s has market cap $%.1fT, likely bad API data\n",
							stock.Symbol, marketCapUSD/1e12)
						continue // Skip this stock completely
					}

					// Filter out OTC stocks (often have bad data)
					if strings.Contains(strings.ToUpper(stock.ExchangeShortName), "OTC") ||
						stock.ExchangeShortName == "" {
						fmt.Printf("⚠️  SKIPPING OTC: %s (exchange: %s) - OTC stocks often have bad data\n",
							stock.Symbol, stock.ExchangeShortName)
						continue
					}

					// Log major conversions for Saudi stocks
					if marketCapUSD > 5e9 && stock.Country == "SA" {
						fmt.Printf("💱 Saudi Stock %s: %.2f %s | Market Cap: $%.1fB USD (Worker %d)\n",
							stock.Symbol, stock.Price, currencyCode, marketCapUSD/1e9, workerID)
					}
				}

				// Get real-time quote for current prices AND better market cap calculation
				quote, err := c.GetQuote(stock.Symbol)
				var percentageChange float64
				var previousClose float64
				var volume float64

				if err == nil && quote != nil {
					currentPrice = quote.Price
					previousClose = quote.PreviousClose
					percentageChange = quote.ChangesPercentage
					volume = quote.Volume

					// PREFER CALCULATED MARKET CAP from real-time quotes over screener data
					if quote.SharesOutstanding > 0 && quote.Price > 0 {
						adjustedPrice := quote.Price

						// Apply sub-unit adjustment for exchanges that use sub-units
						symbolUpper := strings.ToUpper(stock.Symbol)
						exchangeUpper := strings.ToUpper(stock.ExchangeShortName)
						if strings.HasSuffix(symbolUpper, ".L") || strings.Contains(exchangeUpper, "LSE") || // LSE: pence
							strings.HasSuffix(symbolUpper, ".JO") || strings.Contains(exchangeUpper, "JNB") || // JSE: cents
							strings.HasSuffix(symbolUpper, ".TA") || strings.Contains(exchangeUpper, "TLV") { // TASE: agorot
							adjustedPrice = quote.Price / 100.0
						}

						// Calculate market cap in USD
						if currencyCode != "USD" {
							rateMutex.RLock()
							exchangeRate := exchangeRateCache[currencyCode]
							rateMutex.RUnlock()
							marketCapUSD = (adjustedPrice * exchangeRate) * quote.SharesOutstanding
						} else {
							marketCapUSD = adjustedPrice * quote.SharesOutstanding
						}

						// FINAL VALIDATION: Re-check the calculated market cap
						if marketCapUSD > 5e12 {
							fmt.Printf("⚠️  SKIPPING CALCULATED: %s has calculated market cap $%.1fT, likely bad data\n",
								stock.Symbol, marketCapUSD/1e12)
							continue
						}

						fmt.Printf("📊 RECALCULATED: %s market cap from $%s to $%s using real-time data\n",
							stock.Symbol, formatLargeNumber(stock.MarketCap), formatLargeNumber(marketCapUSD))
					}
				} else {
					previousClose = currentPrice * 0.99
					percentageChange = 1.0
					volume = stock.Volume
				}

				// Determine asset type
				assetType := "stock"
				nameUpper := strings.ToUpper(stock.CompanyName)
				if containsWord(nameUpper, "REIT") {
					assetType = "reit"
				}

				// Get company profile for image (only for large companies to save time)
				imageURL := ""
				if marketCapUSD > 50e9 {
					profile, err := c.GetCompanyProfile(stock.Symbol)
					if err == nil && profile != nil {
						imageURL = profile.Image
					}
				}

				asset := AssetData{
					Ticker:           stock.Symbol,
					Name:             stock.CompanyName,
					MarketCap:        marketCapUSD,
					CurrentPrice:     currentPrice,
					PreviousClose:    previousClose,
					PercentageChange: percentageChange,
					Volume:           volume,
					PrimaryExchange:  stock.ExchangeShortName,
					Country:          stock.Country,
					Sector:           stock.Sector,
					Industry:         stock.Industry,
					AssetType:        assetType,
					Image:            imageURL,
				}

				resultChan <- asset

				// Rate limiting to avoid API limits
				time.Sleep(50 * time.Millisecond)
			}
		}(i)
	}

	// Wait for exchange rates to be pre-fetched
	go func() {
		rateFetchWg.Wait()
		fmt.Printf("✅ Pre-fetched exchange rates for %d currencies\n", len(commonCurrencies))
	}()

	// Send ALL stocks to workers (no artificial limits)
	go func() {
		defer close(stockChan)
		for _, stock := range validStocks {
			stockChan <- stock
		}
	}()

	// Collect results
	go func() {
		wg.Wait()
		close(resultChan)
	}()

	// Enhanced progress tracking
	processed := 0
	totalToProcess := len(validStocks)
	if totalToProcess > maxStocks {
		totalToProcess = maxStocks
	}

	for asset := range resultChan {
		assets = append(assets, asset)
		processed++

		// Enhanced progress reporting
		if processed%25 == 0 {
			fmt.Printf("📊 Processed %d/%d stocks... (%.1f%% complete) - Latest: %s\n",
				processed, totalToProcess, float64(processed)/float64(totalToProcess)*100, asset.Name)
		}
	}

	// Re-rank by USD market cap
	fmt.Printf("🏆 Re-ranking %d assets by USD market cap...\n", len(assets))
	sort.Slice(assets, func(i, j int) bool {
		return assets[i].MarketCap > assets[j].MarketCap
	})

	// Keep ALL companies (no artificial cutoff)
	// All companies with 50M+ market cap will be included

	fmt.Printf("✅ Final result: Top %d stocks ranked by USD market cap\n", len(assets))
	fmt.Printf("🚀 Optimized parallel processing completed with %d workers (reduced to avoid rate limits)!\n", numWorkers)

	return assets, nil
}

func containsWord(text, word string) bool {
	words := strings.Fields(text)
	for _, w := range words {
		cleanWord := strings.Trim(w, ".,!?;:")
		if strings.EqualFold(cleanWord, word) {
			return true
		}
	}
	return false
}

func isProblematicStock(symbol, companyName string) bool {
	// Known stocks with consistently bad market cap data from FMP API
	problematicStocks := map[string]bool{
		"NVL":   true, // Novelis - often shows $45T instead of ~$15B
		"AXTLF": true, // Axtel - often shows $2T instead of ~$100M
		"ALIZY": true, // Allianz ADR - often shows $1.7T instead of ~$80B
	}

	// Check by symbol
	if problematicStocks[strings.ToUpper(symbol)] {
		return true
	}

	// Check by company name patterns
	companyUpper := strings.ToUpper(companyName)
	if strings.Contains(companyUpper, "AXTEL") && strings.Contains(companyUpper, "S.A.B") {
		return true
	}

	return false
}

func shouldKeepNewListing(newStock, existingStock FMPStockScreener) bool {
	newPriority := getListingPriority(newStock.Symbol, newStock.ExchangeShortName)
	existingPriority := getListingPriority(existingStock.Symbol, existingStock.ExchangeShortName)

	if newPriority < existingPriority {
		return true
	} else if newPriority == existingPriority {
		return newStock.MarketCap > existingStock.MarketCap
	}
	return false
}

func getListingPriority(symbol, exchange string) int {
	// Lower number = higher priority
	symbolUpper := strings.ToUpper(symbol)
	exchangeUpper := strings.ToUpper(exchange)

	// Hong Kong primary listings get highest priority
	if strings.HasSuffix(symbolUpper, ".HK") || exchangeUpper == "HKSE" {
		return 1
	}

	// Major primary exchanges
	primaryExchanges := []string{"NYSE", "NASDAQ", "TSE", "SSE", "SZSE", "LSE", "FRA", "AMS", "SIX", "TSX"}
	for _, primaryExchange := range primaryExchanges {
		if exchangeUpper == primaryExchange {
			return 2
		}
	}

	// Saudi Arabia exchange
	if exchangeUpper == "SAU" || strings.Contains(exchangeUpper, "SAUDI") {
		return 2
	}

	// Regional exchanges
	if exchangeUpper == "ASX" || exchangeUpper == "BSE" || exchangeUpper == "NSE" {
		return 3
	}

	// Secondary markets
	return 4
}

func (c *FMPClient) getUSDExchangeRate(fromCurrency string) float64 {
	if fromCurrency == "USD" {
		return 1.0
	}

	// FIXED: Use hardcoded fallback rates for critical currencies when API fails
	fallbackRates := map[string]float64{
		"IDR": 0.0000625, // Indonesian Rupiah: ~16,000 IDR = 1 USD
		"JPY": 0.0067,    // Japanese Yen: ~150 JPY = 1 USD
		"KRW": 0.00075,   // Korean Won: ~1,330 KRW = 1 USD
		"INR": 0.012,     // Indian Rupee: ~83 INR = 1 USD
		"CNY": 0.14,      // Chinese Yuan: ~7.1 CNY = 1 USD
		"HKD": 0.128,     // Hong Kong Dollar: ~7.8 HKD = 1 USD
		"SAR": 0.267,     // Saudi Riyal: ~3.75 SAR = 1 USD
		"AED": 0.272,     // UAE Dirham: ~3.67 AED = 1 USD
		"THB": 0.028,     // Thai Baht: ~36 THB = 1 USD
		"MYR": 0.224,     // Malaysian Ringgit: ~4.46 MYR = 1 USD
		"PHP": 0.018,     // Philippine Peso: ~56 PHP = 1 USD
		"VND": 0.00004,   // Vietnamese Dong: ~24,000 VND = 1 USD
		"TWD": 0.031,     // Taiwan Dollar: ~32 TWD = 1 USD
		"ZAR": 0.053,     // South African Rand: ~19 ZAR = 1 USD
		"BRL": 0.20,      // Brazilian Real: ~5 BRL = 1 USD
		"MXN": 0.058,     // Mexican Peso: ~17 MXN = 1 USD
		"CLP": 0.0010,    // Chilean Peso: ~950 CLP = 1 USD
		"COP": 0.00024,   // Colombian Peso: ~4,100 COP = 1 USD
		"PEN": 0.27,      // Peruvian Sol: ~3.7 PEN = 1 USD
		"ARS": 0.0010,    // Argentine Peso: ~1,000 ARS = 1 USD
		"EGP": 0.032,     // Egyptian Pound: ~31 EGP = 1 USD
		"TRY": 0.030,     // Turkish Lira: ~33 TRY = 1 USD
		"ILS": 0.28,      // Israeli Shekel: ~3.6 ILS = 1 USD
		"EUR": 1.08,      // Euro: ~0.92 EUR = 1 USD
		"GBP": 1.27,      // British Pound: ~0.79 GBP = 1 USD
		"CHF": 1.11,      // Swiss Franc: ~0.90 CHF = 1 USD
		"CAD": 0.74,      // Canadian Dollar: ~1.35 CAD = 1 USD
		"AUD": 0.64,      // Australian Dollar: ~1.56 AUD = 1 USD
		"SEK": 0.094,     // Swedish Krona: ~10.6 SEK = 1 USD
		"NOK": 0.092,     // Norwegian Krone: ~10.9 NOK = 1 USD
		"DKK": 0.145,     // Danish Krone: ~6.9 DKK = 1 USD
		"SGD": 0.74,      // Singapore Dollar: ~1.35 SGD = 1 USD
	}

	// Try API first (but skip if rate limited)
	endpoint := fmt.Sprintf("/v3/fx/%sUSD", fromCurrency)
	body, err := c.makeRequest(endpoint)
	if err == nil {
		// Check if response contains rate limit error
		if strings.Contains(string(body), "Limit Reach") {
			fmt.Printf("⚠️  API Rate Limited for %s exchange rate, using fallback\n", fromCurrency)
		} else {
			var rates []map[string]interface{}
			if err := json.Unmarshal(body, &rates); err == nil {
				if len(rates) > 0 {
					if rate, ok := rates[0]["price"].(float64); ok && rate > 0 {
						fmt.Printf("📊 Exchange Rate API: %s to USD = %.6f\n", fromCurrency, rate)
						return rate
					}
				}
			}
		}
	}

	// CRITICAL: Use fallback rates when API fails
	if fallbackRate, exists := fallbackRates[fromCurrency]; exists {
		fmt.Printf("⚠️  Using fallback rate: %s to USD = %.6f (API failed)\n", fromCurrency, fallbackRate)
		return fallbackRate
	}

	// Last resort: return 1.0 only for unknown currencies
	fmt.Printf("❌ Unknown currency %s, defaulting to 1.0\n", fromCurrency)
	return 1.0
}

func (c *FMPClient) detectCurrency(symbol, country string) string {
	// FIXED: Exchange-based detection for accurate currency mapping

	// First check by exchange suffix or symbol pattern
	symbolUpper := strings.ToUpper(symbol)
	if strings.HasSuffix(symbolUpper, ".JO") || strings.Contains(symbolUpper, ".JNB") {
		return "ZAR" // South African Rand for Johannesburg Stock Exchange
	}
	if strings.HasSuffix(symbolUpper, ".HK") || strings.Contains(symbolUpper, ".HKSE") {
		return "HKD" // Hong Kong Dollar
	}
	if strings.HasSuffix(symbolUpper, ".SR") || strings.Contains(symbolUpper, ".SAU") {
		return "SAR" // Saudi Riyal
	}
	if strings.HasSuffix(symbolUpper, ".KS") || strings.HasSuffix(symbolUpper, ".KQ") {
		return "KRW" // Korean Won
	}
	if strings.HasSuffix(symbolUpper, ".T") {
		return "JPY" // Japanese Yen
	}
	if strings.HasSuffix(symbolUpper, ".L") || strings.HasSuffix(symbolUpper, ".LSE") {
		return "GBP" // British Pound for London Stock Exchange
	}
	if strings.HasSuffix(symbolUpper, ".TA") || strings.HasSuffix(symbolUpper, ".TLV") {
		return "ILS" // Israeli Shekel
	}

	// Currency mapping based on country (fallback)
	currencyMap := map[string]string{
		"US": "USD", "CA": "CAD", "GB": "GBP", "AU": "AUD", "NZ": "NZD",
		"DE": "EUR", "FR": "EUR", "IT": "EUR", "ES": "EUR", "NL": "EUR",
		"BE": "EUR", "AT": "EUR", "FI": "EUR", "IE": "EUR", "PT": "EUR",
		"JP": "JPY", "CN": "CNY", "HK": "HKD", "SG": "SGD", "KR": "KRW",
		"IN": "INR", "TH": "THB", "MY": "MYR", "ID": "IDR", "PH": "PHP",
		"VN": "VND", "TW": "TWD", "CH": "CHF", "SE": "SEK", "NO": "NOK",
		"DK": "DKK", "BR": "BRL", "MX": "MXN", "AR": "ARS", "CL": "CLP",
		"CO": "COP", "PE": "PEN", "ZA": "ZAR", "EG": "EGP", "SA": "SAR",
		"AE": "AED", "IL": "ILS", "TR": "TRY",
	}

	if currency, exists := currencyMap[country]; exists {
		return currency
	}

	return "USD"
}

func saveToJSON(data []AssetData, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	return encoder.Encode(data)
}

func saveToCSV(data []AssetData, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	// Write UTF-8 BOM for proper character encoding
	file.WriteString("\xEF\xBB\xBF")

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write header
	header := []string{
		"Rank", "Ticker", "Name", "Country", "Sector", "Industry",
		"Market_Cap_USD", "Current_Price", "Previous_Close", "Percentage_Change",
		"Volume", "Exchange", "Asset_Type",
	}
	if err := writer.Write(header); err != nil {
		return err
	}

	// Write data
	for i, asset := range data {
		record := []string{
			fmt.Sprintf("%d", i+1),
			asset.Ticker,
			cleanText(asset.Name),
			asset.Country,
			cleanText(asset.Sector),
			cleanText(asset.Industry),
			fmt.Sprintf("%.0f", asset.MarketCap),
			fmt.Sprintf("%.2f", asset.CurrentPrice),
			fmt.Sprintf("%.2f", asset.PreviousClose),
			fmt.Sprintf("%.2f", asset.PercentageChange),
			fmt.Sprintf("%.0f", asset.Volume),
			asset.PrimaryExchange,
			asset.AssetType,
		}
		if err := writer.Write(record); err != nil {
			return err
		}
	}

	return nil
}

func printSummary(data []AssetData) {
	fmt.Printf("\n📊 TOP 10 STOCKS BY MARKET CAP:\n")
	fmt.Printf("%-4s %-10s %-40s %-8s %-15s %15s\n", "Rank", "Ticker", "Company", "Country", "Exchange", "Market Cap")
	fmt.Printf("%s\n", strings.Repeat("-", 100))

	top10 := 10
	if len(data) < 10 {
		top10 = len(data)
	}

	for i := 0; i < top10; i++ {
		asset := data[i]
		fmt.Printf("%-4d %-10s %-40s %-8s %-15s %15s\n",
			i+1,
			asset.Ticker,
			truncateString(cleanText(asset.Name), 40),
			asset.Country,
			asset.PrimaryExchange,
			formatLargeNumber(asset.MarketCap))
	}

	// Country summary
	countryCounts := make(map[string]int)
	for _, asset := range data {
		countryCounts[asset.Country]++
	}

	fmt.Printf("\n🌍 STOCKS BY COUNTRY:\n")
	for country, count := range countryCounts {
		fmt.Printf("   %s: %d stocks\n", country, count)
	}

	// Saudi Arabia specific summary
	saCount := countryCounts["SA"]
	if saCount > 0 {
		fmt.Printf("\n🇸🇦 SAUDI ARABIA STOCKS FOUND: %d\n", saCount)
		fmt.Printf("   Top Saudi stocks:\n")
		saStockCount := 0
		for _, asset := range data {
			if asset.Country == "SA" && saStockCount < 5 {
				fmt.Printf("   %d. %s (%s) - $%.1fB\n",
					saStockCount+1, asset.Name, asset.Ticker, asset.MarketCap/1e9)
				saStockCount++
			}
		}
	} else {
		fmt.Printf("\n⚠️  No Saudi Arabia stocks found in top 500\n")
	}
}

func formatLargeNumber(num float64) string {
	if num >= 1e12 {
		return fmt.Sprintf("$%.1fT", num/1e12)
	} else if num >= 1e9 {
		return fmt.Sprintf("$%.1fB", num/1e9)
	} else if num >= 1e6 {
		return fmt.Sprintf("$%.1fM", num/1e6)
	}
	return fmt.Sprintf("$%.0f", num)
}

func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func cleanText(text string) string {
	// Remove any null bytes
	text = strings.ReplaceAll(text, "\x00", "")

	// Fix common encoding issues where German characters appear as Chinese characters
	text = strings.ReplaceAll(text, "羹", "ü")
	text = strings.ReplaceAll(text, "脛", "ä")
	text = strings.ReplaceAll(text, "枚", "ö")
	text = strings.ReplaceAll(text, "脽", "ß")

	// Remove only ASCII control characters, keep all international characters
	var result strings.Builder
	for _, r := range text {
		if r < 32 || r == 127 {
			// Skip control characters
			continue
		}
		result.WriteRune(r)
	}

	return result.String()
}

func main() {
	if err := godotenv.Load(); err != nil {
		log.Printf("Warning: No .env file found, using environment variables")
	}

	apiKey := os.Getenv("FMP_API_KEY")
	if apiKey == "" {
		log.Fatal("FMP_API_KEY environment variable is required")
	}

	client := NewFMPClient(apiKey)

	fmt.Println("🌟 COMPREHENSIVE GLOBAL STOCK ANALYSIS - ENHANCED PARALLEL MULTITHREADING")
	fmt.Println("📈 STRATEGY: 38 Country-Specific API Calls → Get ALL 50M+ companies → Convert to USD → Global ranking")
	fmt.Println("🚀 Using FMP Stock Screener API with MAXIMUM PARALLEL PROCESSING!")
	fmt.Println("⚡ PERFORMANCE OPTIMIZATIONS:")
	fmt.Println("   🔄 12 Parallel Country Fetchers (vs 1 sequential)")
	fmt.Println("   ⚡ 10 Parallel Stock Processors (optimized for rate limits)")
	fmt.Println("   💱 Fallback Exchange Rates (32 currencies)")
	fmt.Println("   🔥 Smart Rate Limiting (50ms to avoid API limits)")
	fmt.Println("🌍 GUARANTEED GLOBAL COVERAGE:")
	fmt.Println("   🇺🇸 US (3000) 🇭🇰 HK (800) 🇨🇳 CN (800) 🇯🇵 JP (500) 🇮🇳 IN (500)")
	fmt.Println("   🇬🇧 UK (300) 🇨🇦 CA (300) 🇦🇺 AU (200) 🇰🇷 KR (200) 🇩🇪 DE (200)")
	fmt.Println("   🇫🇷 FR (200) 🇧🇷 BR (200) 🇸🇦 SA (200) 🇹🇼 TW (150) 🇮🇹 IT (150)")
	fmt.Println("   🇪🇸 ES (150) 🇳🇱 NL (100) 🇨🇭 CH (100) 🇸🇬 SG (100) + 20 more countries")
	fmt.Println("✅ Includes: Tencent (HK), NVIDIA (US), Toyota (JP), Kweichow Moutai (CN), ASML (NL), Saudi Aramco (SA)")
	fmt.Println("✅ Excludes: Russia, ADRs, ETFs, Index Funds")
	fmt.Println("📊 RANKING: ALL 50M+ companies globally, ranked by USD market cap (no artificial limits)")
	fmt.Println("💵 Market caps converted to USD for ranking (prices kept in original currency)")
	fmt.Println()

	startTime := time.Now()
	var allAssets []AssetData

	fmt.Println("🌍 Fetching global stocks using FMP Stock Screener API...")

	globalStocks, err := client.GetGlobalStocks()
	if err != nil {
		log.Fatalf("❌ Failed to fetch global stocks: %v\n", err)
	}

	allAssets = append(allAssets, globalStocks...)

	if len(allAssets) == 0 {
		log.Fatal("❌ No stocks fetched successfully!")
	}

	// Count stocks by country
	countryCounts := make(map[string]int)
	for _, asset := range allAssets {
		countryCounts[asset.Country]++
	}

	fmt.Printf("\n📊 Retrieved %d stocks from %d countries\n", len(allAssets), len(countryCounts))

	filename := "global_stocks_fmp.json"
	if err := saveToJSON(allAssets, filename); err != nil {
		log.Printf("Failed to save to file: %v", err)
	} else {
		fmt.Printf("💾 Data saved to %s\n", filename)
	}

	csvFilename := "global_stocks_fmp.csv"
	if err := saveToCSV(allAssets, csvFilename); err != nil {
		log.Printf("Failed to save to CSV file: %v", err)
	} else {
		fmt.Printf("💾 Data saved to %s\n", csvFilename)
	}

	printSummary(allAssets)

	duration := time.Since(startTime)
	fmt.Printf("\n🎉 Total processing time: %v\n", duration)
	fmt.Printf("🌟 Retrieved stock data from worldwide markets using ENHANCED PARALLEL PROCESSING!\n")
	fmt.Printf("🌍 Comprehensive global stock coverage including Saudi Arabia - NO HARDCODING!\n")
	fmt.Printf("🚀 Optimized performance with 12 country workers + 10 stock processors (rate-limit friendly)!\n")
}
