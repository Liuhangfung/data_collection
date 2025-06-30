# 🐳 Docker Guide for AlgoTrader

## Quick Start

### 1. Prerequisites
- Docker installed on your system
- `.env` file with your API keys
- Internet connection

### 2. Basic Usage

```bash
# Build and run with docker-compose (recommended)
docker-compose up --build scraper

# Or use the convenience script
chmod +x run-docker.sh
./run-docker.sh get_allassetcap.py
```

## 📋 Available Commands

### Docker Compose Commands
```bash
# Run main scraper
docker-compose up scraper

# Run specific scrapers
docker-compose run --rm scraper python get_aave.py
docker-compose run --rm scraper python get_dominance.py
docker-compose run --rm scraper python get_news.py
docker-compose run --rm scraper python get_calendar.py

# Run with rebuild
docker-compose up --build scraper

# View logs
docker-compose logs scraper
```

### Shell Script Commands
```bash
# Run different scrapers
./run-docker.sh get_allassetcap.py
./run-docker.sh get_aave.py
./run-docker.sh get_dominance.py
./run-docker.sh get_news.py
```

### Manual Docker Commands
```bash
# Build image
docker build -t algotradar-scraper .

# Run container
docker run --rm \
    -v "$(pwd)/.env:/app/.env:ro" \
    -v "$(pwd)/logs:/app/logs" \
    --name scraper-run \
    algotradar-scraper python get_allassetcap.py

# Interactive shell (for debugging)
docker run -it --rm \
    -v "$(pwd)/.env:/app/.env:ro" \
    --entrypoint /bin/bash \
    algotradar-scraper
```

## 🔧 Configuration

### Environment Variables
Your `.env` file should contain:
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
SUPABASE_USER_EMAIL=your_email
SUPABASE_USER_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=your_openai_key

# Perplexity
PERPLEXITY_API_KEY=your_perplexity_key

# ClickHouse
CLICKHOUSE_HOST=your_clickhouse_host
CLICKHOUSE_PORT=your_clickhouse_port
CLICKHOUSE_USERNAME=your_clickhouse_username
CLICKHOUSE_PASSWORD=your_clickhouse_password
```

### Resource Limits
Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 2G      # Adjust based on your needs
      cpus: '1.0'     # Adjust based on your CPU cores
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Permission Denied" on run-docker.sh
```bash
chmod +x run-docker.sh
```

#### 2. "No space left on device"
```bash
# Clean up old images
docker system prune -f

# Remove unused images
docker image prune -a -f
```

#### 3. ".env file not found"
```bash
# Create .env file in project root
cp .env.example .env  # If you have an example
# Then edit .env with your actual API keys
```

#### 4. Chrome crashes in container
```bash
# Increase shared memory size
docker run --rm --shm-size=2g \
    -v "$(pwd)/.env:/app/.env:ro" \
    algotradar-scraper python get_allassetcap.py
```

#### 5. Container exits immediately
```bash
# Check logs
docker-compose logs scraper

# Run with interactive shell to debug
docker run -it --rm \
    -v "$(pwd)/.env:/app/.env:ro" \
    --entrypoint /bin/bash \
    algotradar-scraper
```

## 🚀 Advanced Usage

### Scheduling with Cron
```bash
# Add to crontab
0 */6 * * * cd /path/to/project && ./run-docker.sh get_allassetcap.py >> logs/cron.log 2>&1
```

### Running Multiple Scrapers
```bash
# Run in parallel
docker-compose run -d scraper python get_aave.py
docker-compose run -d scraper python get_dominance.py
docker-compose run -d scraper python get_news.py
```

### Custom Chrome Options
Edit `docker-selenium-config.py` and import in your scrapers:
```python
from docker_selenium_config import setup_stealth_driver, human_like_page_load

# Replace your driver setup with:
driver = setup_stealth_driver()
human_like_page_load(driver, url)
```

## 📊 Monitoring

### View Container Stats
```bash
docker stats algotradar-scraper
```

### Check Logs
```bash
# Real-time logs
docker-compose logs -f scraper

# Last 100 lines
docker-compose logs --tail=100 scraper
```

### Debug Mode
```bash
# Run with debug output
docker-compose run --rm scraper python -u get_allassetcap.py
```

## 🔄 Updates

### Update Code
```bash
# Pull latest code
git pull

# Rebuild container
docker-compose build --no-cache scraper

# Run updated version
docker-compose up scraper
```

### Update Dependencies
```bash
# Update requirements.txt
# Then rebuild
docker-compose build --no-cache scraper
```

## 💡 Tips

1. **Use the shell script** for simplicity
2. **Check logs** if scraping fails
3. **Increase wait times** for slow websites
4. **Monitor resource usage** with `docker stats`
5. **Clean up regularly** with `docker system prune`

## 🆘 Getting Help

If you encounter issues:
1. Check the logs: `docker-compose logs scraper`
2. Try the debug shell: `docker run -it --rm --entrypoint /bin/bash algotradar-scraper`
3. Verify your `.env` file has all required keys
4. Check if the website structure has changed 