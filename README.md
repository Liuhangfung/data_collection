# 🌟 Global Asset Ranking System

A comprehensive system to fetch and rank the **top 500 individual assets globally** by market capitalization, including stocks, cryptocurrencies, and essential commodities.

## 📊 What This System Does

- **🌍 Global Stock Coverage**: Individual stocks from 70+ countries (US, Europe, Asia, etc.)
- **₿ Cryptocurrency Data**: Real-time crypto prices with accurate market caps
- **🥇 Essential Commodities**: Gold, Silver, Platinum, Palladium, Copper with realistic market caps
- **🚫 Excludes**: ETFs, Index Funds, Mutual Funds, Agricultural Futures
- **🎯 Output**: Daily ranking of top 500 individual assets by market cap

## 🏆 Expected Top Rankings

1. **Gold** (~$21.4T) - Usually #1 globally
2. **Silver** (~$1.6T) - Top 10
3. **NVIDIA, Microsoft, Apple** - Top individual stocks
4. **Bitcoin, Ethereum** - Top cryptocurrencies
5. **Copper** (~$700B+) - Large cap range
6. **Platinum, Palladium** (~$200B) - Mid-large cap range

## 🛠️ System Architecture

### Multi-Language Approach
- **Go + FMP API**: Global stocks and commodities (fast, efficient)
- **Python + CCXT**: Cryptocurrencies (best crypto library)
- **Python Combiner**: Merge, deduplicate, and rank all assets
- **Supabase Integration**: Store daily rankings in database

### Core Files
```
📁 algotradar/
├── 🔧 stock_fmp_global.go      # Go program for stocks & commodities
├── 🐍 get_crypto_ccxt.py       # Python crypto fetcher
├── 🔗 combine_all_assets.py    # Combiner & Supabase integration
├── 📊 [timestamp]_data.json    # Daily output files
└── 📖 README.md                # This file
```

## 🚀 Quick Start

### Prerequisites
1. **Go 1.20+** - Download from [golang.org](https://golang.org/dl/)
2. **Python 3.10+** - Download from [python.org](https://www.python.org/downloads/)
3. **FMP Ultimate API Key** - Get from [financialmodelingprep.com](https://financialmodelingprep.com/)
4. **Supabase Project** - Create at [supabase.com](https://supabase.com)

### Installation

1. **Clone/Download** this repository
2. **Install Python dependencies**:
   ```bash
   pip install ccxt requests python-dotenv supabase
   ```

3. **Set up environment variables** (create `.env` file):
   ```env
   FMP_API_KEY=your_fmp_ultimate_api_key_here
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

4. **Set up Supabase database** (run this SQL in your Supabase SQL editor):
   ```sql
   -- Create the assets table
   CREATE TABLE public.assets (
       id BIGSERIAL PRIMARY KEY,
       ticker VARCHAR(20) NOT NULL,
       name VARCHAR(255) NOT NULL,
       market_cap BIGINT NOT NULL,
       current_price DECIMAL(20, 8) NOT NULL,
       previous_close DECIMAL(20, 8),
       percentage_change DECIMAL(10, 4),
       volume BIGINT DEFAULT 0,
       primary_exchange VARCHAR(100),
       country VARCHAR(100),
       sector VARCHAR(100),
       industry VARCHAR(100),
       asset_type VARCHAR(50) NOT NULL,
       rank_position INTEGER NOT NULL,
       date_updated DATE NOT NULL DEFAULT CURRENT_DATE,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
   );

   -- Create indexes for better performance
   CREATE INDEX idx_assets_date_rank ON public.assets(date_updated, rank_position);
   CREATE INDEX idx_assets_ticker ON public.assets(ticker);
   CREATE INDEX idx_assets_asset_type ON public.assets(asset_type);
   CREATE INDEX idx_assets_market_cap ON public.assets(market_cap DESC);

   -- Enable Row Level Security (optional but recommended)
   ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;

   -- Create a policy to allow public read access (adjust as needed)
   CREATE POLICY "Enable read access for all users" ON public.assets
       FOR SELECT USING (true);

   -- Create a policy for insert/update (adjust as needed for your use case)
   CREATE POLICY "Enable insert for authenticated users only" ON public.assets
       FOR INSERT WITH CHECK (auth.role() = 'authenticated');

   CREATE POLICY "Enable update for authenticated users only" ON public.assets
       FOR UPDATE USING (auth.role() = 'authenticated');
   ```

## 📈 Daily Usage

### Simple One-Command Execution
```powershell
# Windows PowerShell
$env:PATH += ";C:\Program Files\Go\bin"
python combine_all_assets.py
```

```bash
# Linux/Mac
export PATH=$PATH:/usr/local/go/bin
python3 combine_all_assets.py
```

### Manual Step-by-Step
```bash
# Step 1: Fetch global stocks & commodities
go run stock_fmp_global.go

# Step 2: Fetch cryptocurrencies  
python get_crypto_ccxt.py

# Step 3: Combine, rank & upload to Supabase
python combine_all_assets.py
```

## 📁 Output Files (Generated Daily)

- `global_assets_fmp_YYYY-MM-DD.json` - Stocks & commodities from FMP
- `crypto_data_YYYY-MM-DD.json` - Cryptocurrencies from CCXT
- `all_assets_combined_YYYY-MM-DD.json` - **Final top 500 ranking**

## 🗃️ Database Schema

The system stores data in the `public.assets` table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `ticker` | VARCHAR(20) | Asset symbol (e.g., AAPL, BTC, GCUSD) |
| `name` | VARCHAR(255) | Full asset name |
| `market_cap` | BIGINT | Market capitalization in USD |
| `current_price` | DECIMAL(20,8) | Current price |
| `previous_close` | DECIMAL(20,8) | Previous close price |
| `percentage_change` | DECIMAL(10,4) | 24h percentage change |
| `volume` | BIGINT | Trading volume |
| `primary_exchange` | VARCHAR(100) | Exchange/platform |
| `country` | VARCHAR(100) | Country of origin |
| `sector` | VARCHAR(100) | Business sector |
| `industry` | VARCHAR(100) | Industry classification |
| `asset_type` | VARCHAR(50) | Type: stock, crypto, commodity |
| `rank_position` | INTEGER | Ranking by market cap (1-500) |
| `date_updated` | DATE | Date of data |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

## 🔍 Query Examples

```sql
-- Get today's top 10 assets
SELECT rank_position, ticker, name, market_cap, asset_type
FROM public.assets 
WHERE date_updated = CURRENT_DATE 
ORDER BY rank_position 
LIMIT 10;

-- Get all cryptocurrencies in today's top 100
SELECT rank_position, ticker, name, market_cap
FROM public.assets 
WHERE date_updated = CURRENT_DATE 
  AND asset_type = 'crypto'
  AND rank_position <= 100
ORDER BY rank_position;

-- Compare market caps of different asset types
SELECT 
    asset_type,
    COUNT(*) as count,
    AVG(market_cap) as avg_market_cap,
    MAX(market_cap) as max_market_cap
FROM public.assets 
WHERE date_updated = CURRENT_DATE
GROUP BY asset_type;
```

## ⚙️ Configuration

### Market Cap Calculations

**Stocks**: Real market cap from FMP API
**Cryptocurrencies**: Price × Circulating Supply (from CoinGecko/CCXT)
**Commodities**: Price × Estimated Total Mined Supply
- Gold: Price × 6.4B ounces mined
- Silver: Price × 54.6B ounces mined  
- Copper: Price × 700M tonnes mined
- Platinum: Price × 257M ounces mined
- Palladium: Price × 175M ounces mined

### API Rate Limits
- **FMP**: 300 requests/minute (Ultimate plan)
- **CoinGecko**: 10-30 requests/minute (free tier)
- **CCXT**: Varies by exchange

## 🔧 Troubleshooting

### Common Issues

**"Go not found"**: Add Go to your PATH
```powershell
# Windows
$env:PATH += ";C:\Program Files\Go\bin"
```

**"FMP API error"**: Check your API key and plan limits
**"Supabase connection error"**: Verify your Supabase URL and key
**"Encoding error"**: Use UTF-8 compatible terminal

### Debug Mode
Set environment variable for verbose output:
```bash
export DEBUG=true
python combine_all_assets.py
```

## 📊 Data Sources

- **Stocks**: Financial Modeling Prep (FMP) Ultimate API
- **Cryptocurrencies**: CoinGecko API + CCXT library
- **Commodities**: FMP commodities endpoint
- **Database**: Supabase PostgreSQL

## 🎯 System Benefits

1. **Comprehensive Coverage**: Truly global asset ranking
2. **Real Market Caps**: Accurate calculations for all asset types
3. **Individual Assets Only**: No funds, ETFs, or indices
4. **Daily Updates**: Fresh data every day
5. **Database Storage**: Historical tracking and analysis
6. **Fast Execution**: Multi-language optimization
7. **Easy to Use**: Single command execution

## 📝 License

This project is for educational and personal use. Please respect API terms of service and rate limits.

---

**🌟 Run daily to get the most accurate global asset rankings!** 