# AlgoTrader - Trading Analysis Project

A comprehensive trading analysis project that scrapes and analyzes various financial data sources including cryptocurrency markets, company holdings, economic calendars, and market dominance metrics.

## 🚀 Features

- **Aave Markets Data** - Scrape lending/borrowing rates and market data
- **Asset Market Cap Analysis** - Track largest companies and assets by market capitalization
- **Company Holdings Tracker** - Monitor Bitcoin treasury holdings by public companies
- **Government Holdings** - Track government/country Bitcoin holdings
- **Economic Calendar** - Fetch important economic events and indicators
- **Market Dominance** - Calculate altcoin season index and Bitcoin dominance
- **Algo724 Integration** - Connect to ClickHouse database for whale signal analysis
- **News Aggregation** - AI-powered cryptocurrency news processing

## 📋 Requirements

- Python 3.8+
- Chrome browser (for Selenium automation)
- API Keys for:
  - Supabase
  - OpenAI
  - Perplexity (for news)
  - ClickHouse (for algo724)

## 🛠️ Installation

1. Clone this repository:
```bash
git clone https://github.com/Liuhangfung/data_collection.git
cd data_collection
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API credentials:
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_USER_EMAIL=your_email
SUPABASE_USER_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Perplexity
PERPLEXITY_API_KEY=your_perplexity_api_key

# ClickHouse
CLICKHOUSE_HOST=your_clickhouse_host
CLICKHOUSE_PORT=your_clickhouse_port
CLICKHOUSE_USERNAME=your_clickhouse_username
CLICKHOUSE_PASSWORD=your_clickhouse_password
```

## 📁 Project Structure

```
algotradar/
├── get_aave.py              # Aave markets data scraper
├── get_algo724.py           # ClickHouse whale signals processor
├── get_allassetcap.py       # All assets market cap scraper
├── get_calendar.py          # Economic calendar scraper
├── get_company_holding.py   # Company Bitcoin holdings tracker
├── get_companycap.py        # Company market cap scraper
├── get_dominance.py         # Market dominance calculator
├── get_government_holding.py # Government Bitcoin holdings
├── get_news.py              # AI-powered news processor
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🏃‍♂️ Usage

Run individual scripts:

```bash
# Scrape Aave markets data
python get_aave.py

# Get market dominance data
python get_dominance.py

# Process economic calendar
python get_calendar.py

# Scrape company holdings
python get_company_holding.py

# Generate AI-powered news
python get_news.py
```

## 🔧 Configuration

Make sure to set up your `.env` file with all required API keys and database credentials. The scripts will automatically load these environment variables.

## 📊 Data Storage

All data is stored in Supabase tables:
- `aave_assets` - Aave market data
- `whale_signals` - Trading signals from ClickHouse
- `largest_companies` - Company market cap data
- `calendar` - Economic events
- `coin_season` - Market dominance metrics
- `news` - Processed news articles

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚠️ Important Notes

- This project uses web scraping - ensure compliance with website terms of service
- API rate limits may apply - implement appropriate delays if needed
- Some scripts require a display (use headless mode on servers)
- Keep your API keys secure and never commit them to version control

## 📝 License

This project is for educational and personal use. Please respect API terms of service and website robots.txt files.

## 🆘 Support

If you encounter any issues:
1. Check that all dependencies are installed correctly
2. Verify your `.env` file has all required credentials
3. Ensure Chrome browser is installed for Selenium scripts
4. Check API key permissions and quotas 