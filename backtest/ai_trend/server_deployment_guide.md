# 🚀 Server Deployment Guide - AI Trend Navigator

## 📦 Files Needed on Server

You need to upload these files to your server:

### **Core Files**
- `daily_supabase_update.py` - Main update script
- `supabase_integration.py` - Database integration
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (create this)

### **Supporting Files**
- `run_daily_update.sh` - Shell script for cron execution
- `deploy_check.py` - Deployment verification script

## 🔧 Server Setup Steps

### **1. Create Environment File (.env)**
```bash
# Create .env file with your credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
FMP_API_KEY=your-fmp-api-key
```

### **2. Install Python Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Create Shell Script for Cron**
```bash
#!/bin/bash
# run_daily_update.sh
cd /path/to/your/ai_trend/
python3 daily_supabase_update.py >> /var/log/ai_trend_update.log 2>&1
```

### **4. Set Up Cron Job (Every 4 Hours)**
```bash
# Edit crontab
crontab -e

# Add this line to run every 4 hours
0 */4 * * * /path/to/your/run_daily_update.sh
```

## ⏰ Scheduling Options

### **Option 1: Every 4 Hours**
```bash
0 */4 * * * /path/to/your/run_daily_update.sh
```

### **Option 2: Specific Times (8AM, 12PM, 4PM, 8PM)**
```bash
0 8,12,16,20 * * * /path/to/your/run_daily_update.sh
```

### **Option 3: Market Hours Only (9AM-5PM every 4 hours)**
```bash
0 9,13,17 * * 1-5 /path/to/your/run_daily_update.sh
```

## 📁 Server Directory Structure
```
/home/your-user/ai_trend/
├── daily_supabase_update.py
├── supabase_integration.py
├── requirements.txt
├── .env
├── run_daily_update.sh
├── deploy_check.py
└── logs/
    └── ai_trend_update.log
```

## 🔍 Monitoring & Logging

### **Log File Location**
```bash
/var/log/ai_trend_update.log
```

### **Check Last Run**
```bash
tail -f /var/log/ai_trend_update.log
```

### **Monitor Cron Jobs**
```bash
crontab -l  # List current cron jobs
grep CRON /var/log/syslog  # Check cron execution logs
```

## 🛠️ Deployment Checklist

- [ ] Upload all required files to server
- [ ] Create `.env` file with correct credentials
- [ ] Install Python dependencies
- [ ] Test script manually: `python3 daily_supabase_update.py`
- [ ] Create shell script with correct paths
- [ ] Set up cron job with desired schedule
- [ ] Verify log file permissions
- [ ] Test cron job execution
- [ ] Monitor first few automatic runs

## 🚨 Troubleshooting

### **Common Issues:**

1. **Permission Denied**
   ```bash
   chmod +x run_daily_update.sh
   chmod 644 .env
   ```

2. **Python Path Issues**
   ```bash
   which python3  # Use full path in shell script
   ```

3. **Environment Variables Not Loading**
   ```bash
   # Add to shell script
   export $(cat /path/to/.env | xargs)
   ```

4. **Cron Job Not Running**
   ```bash
   # Check cron service
   sudo service cron status
   sudo service cron restart
   ```

## 📊 Monitoring Dashboard

You can monitor the script performance by checking:
- Supabase dashboard for new data
- Log files for execution status
- Database row counts for each timeframe

## 🔄 Alternative Deployment Options

### **Option A: Cloud Functions (AWS Lambda, Google Cloud)**
- Upload as serverless function
- Trigger with CloudWatch/Cloud Scheduler
- Automatic scaling and error handling

### **Option B: Docker Container**
- Package everything in Docker
- Run with docker-compose
- Easy deployment and updates

### **Option C: GitHub Actions (Free)**
- Use GitHub's free cron scheduling
- Runs in cloud automatically
- No server maintenance needed

Would you like me to create any of these alternative deployment setups? 