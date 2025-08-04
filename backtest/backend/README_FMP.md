# FMP API Asset Fetcher

This Go application fetches all stocks and ETFs from the Financial Modeling Prep (FMP) API and ranks them by market capitalization using parallel processing for maximum performance.

## What is FMP API?

**Financial Modeling Prep (FMP)** is a comprehensive financial data API that provides:
- Real-time and historical stock market data
- Company profiles and financial statements
- Market capitalization data
- ETF information
- Financial ratios and metrics

## Features

✅ **Parallel Processing**: Uses Go goroutines for ultra-fast data collection  
✅ **Market Cap Ranking**: Automatically sorts assets by market capitalization  
✅ **Comprehensive Data**: Fetches price, volume, fundamentals, and company profiles  
✅ **Rate Limiting**: Built-in protection against API rate limits  
✅ **Batch Requests**: Optimized API calls using FMP's batch endpoints  
✅ **JSON Export**: Saves ranked data to timestamped JSON files  

## Setup Instructions

### 1. Get Your FMP API Key
1. Sign up at [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs)
2. Get your free API key (500 requests/month free tier)

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```bash
# Financial Modeling Prep API Key
fmp_api=your_actual_api_key_here
```

### 3. Install Dependencies
```bash
cd /path/to/your/project
go mod tidy
```

### 4. Run the Application
```bash
go run fmp.go
```

## How It Works

The application uses **parallel processing** to maximize speed:

1. **Parallel Asset Collection**: 
   - Stocks and ETFs are fetched simultaneously using goroutines
   - Each asset type runs in its own goroutine

2. **Batch API Calls**:
   - Symbols are processed in batches of 50 (FMP's limit)
   - Multiple batches run concurrently with rate limiting

3. **Data Enrichment**:
   - Basic quotes are enhanced with company profiles
   - All data is combined into comprehensive asset records

4. **Market Cap Ranking**:
   - Assets are sorted by market capitalization (highest first)
   - Invalid/zero market cap assets are filtered out

## Output

The program generates:
- **Console output**: Real-time progress and top 10 ranked assets
- **JSON file**: Complete ranked dataset saved as `all_assets_ranked_YYYY-MM-DD.json`

Example output:
```
🚀 Starting parallel asset collection (stocks and ETFs)...
📈 Fetching stocks...
🏢 Fetching ETFs...
✅ Found 8,524 stocks
✅ Found 2,831 ETFs
🎯 Total assets collected: 1,700
⚡ Data collection completed in 45.2s
📊 Assets ranked by market cap. Top 10:
1. AAPL (Apple Inc.) - $2.89T - stock
2. MSFT (Microsoft Corporation) - $2.78T - stock
3. NVDA (NVIDIA Corporation) - $1.73T - stock
...
```

## Performance Benefits of Go

Compared to Python, this Go implementation is:
- **10-100x faster** for I/O operations
- **Highly concurrent** with lightweight goroutines  
- **Memory efficient** with better garbage collection
- **Built-in parallelism** without complex threading

## API Endpoints Used

- `/api/v3/stock/list` - Get all stock symbols
- `/api/v3/etf/list` - Get all ETF symbols  
- `/api/v3/quote/{symbols}` - Get detailed quotes (batch)
- `/api/v3/profile/{symbol}` - Get company profiles

## Rate Limiting

The application includes:
- Automatic retry on 429 (rate limit) responses
- Configurable concurrent request limits (default: 10)
- Built-in delays to respect API limits

## Customization

You can modify the limits in `fmp.go`:
```go
// Adjust these values based on your FMP plan
quotes, err := c.GetQuotes(symbols[:min(len(symbols), 1000)]) // Stock limit
quotes, err := c.GetQuotes(symbols[:min(len(symbols), 500)])  // ETF limit
```

For higher FMP plan tiers, you can increase these limits and concurrent requests. 