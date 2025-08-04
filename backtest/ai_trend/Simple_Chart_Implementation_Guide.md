# Simple Chart Implementation Guide

## 🎯 Quick Overview

You have 3 Supabase tables with Bitcoin trading data. Here's how to use them for charts:

## 📊 Main Data Table: `ai_trend_data`

### Key Columns for Charts:
```sql
SELECT 
  timestamp,           -- X-axis (time)
  open_price,         -- Candlestick open
  high_price,         -- Candlestick high  
  low_price,          -- Candlestick low
  close_price,        -- Candlestick close
  signal,             -- KNN MA (raw AI trend line) 
  smoothed_signal,    -- KNN MA Smoothed (main AI trend line)
  ma_signal,          -- MA of KNN MA (trend confirmation)
  buy_signal,         -- Buy signal (boolean)
  sell_signal,        -- Sell signal (boolean)
  timeframe           -- 4H, 8H, 1D, 1W, 1M
FROM ai_trend_data
WHERE timeframe = '4H'
ORDER BY timestamp;
```

## 📈 Chart 1: Price Chart with AI Trend Lines & Buy/Sell Signals

### AI Trend Lines Explained:
- **🟠 KNN MA (Raw)**: Orange line - Raw KNN moving average calculation
- **🟣 KNN MA Smoothed**: Purple line - **Main AI trend line** (most important!)
- **🔵 KNN MA Trend**: Blue line - Moving average of KNN MA for trend confirmation
- **🟢 Buy Signals**: Green triangles - When AI detects uptrend start
- **🔴 Sell Signals**: Red triangles - When AI detects downtrend start

### Data Query:
```javascript
// Fetch price data with AI trend lines for chart
const { data: priceData } = await supabase
  .from('ai_trend_data')
  .select('timestamp, open_price, high_price, low_price, close_price, signal, smoothed_signal, ma_signal, buy_signal, sell_signal')
  .eq('timeframe', '4H')
  .order('timestamp', { ascending: true })
  .limit(1000);
```

### Chart Implementation (Chart.js example):
```javascript
// Prepare candlestick data
const candlestickData = priceData.map(item => ({
  x: new Date(item.timestamp),
  o: item.open_price,
  h: item.high_price,
  l: item.low_price,
  c: item.close_price
}));

// Prepare AI trend lines
const knnMA = priceData.map(item => ({
  x: new Date(item.timestamp),
  y: item.signal  // Raw KNN MA
}));

const knnMASmoothed = priceData.map(item => ({
  x: new Date(item.timestamp),
  y: item.smoothed_signal  // Main AI trend line
}));

const knnMATrend = priceData.map(item => ({
  x: new Date(item.timestamp),
  y: item.ma_signal  // Trend confirmation line
}));

// Prepare buy/sell signals (use boolean fields)
const buySignals = priceData
  .filter(item => item.buy_signal === true)
  .map(item => ({
    x: new Date(item.timestamp),
    y: item.close_price
  }));

const sellSignals = priceData
  .filter(item => item.sell_signal === true)
  .map(item => ({
    x: new Date(item.timestamp),
    y: item.close_price
  }));

// Chart configuration
const chartConfig = {
  type: 'candlestick',
  data: {
    datasets: [
      {
        label: 'BTC Price',
        data: candlestickData,
        color: {
          up: '#00C851',    // Green for price up
          down: '#ff4444',  // Red for price down
          unchanged: '#999'
        }
      },
      {
        label: 'KNN MA (Raw)',
        data: knnMA,
        type: 'line',
        borderColor: '#FFA500',  // Orange
        backgroundColor: 'transparent',
        borderWidth: 1,
        pointRadius: 0
      },
      {
        label: 'KNN MA Smoothed (Main AI Line)',
        data: knnMASmoothed,
        type: 'line',
        borderColor: '#8A2BE2',  // Purple - main AI trend
        backgroundColor: 'transparent',
        borderWidth: 3,
        pointRadius: 0
      },
      {
        label: 'KNN MA Trend',
        data: knnMATrend,
        type: 'line',
        borderColor: '#1E90FF',  // Blue - trend confirmation
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0
      },
      {
        label: 'Buy Signals',
        data: buySignals,
        type: 'scatter',
        backgroundColor: '#00C851',
        pointStyle: 'triangle',
        pointRadius: 8
      },
      {
        label: 'Sell Signals',
        data: sellSignals,
        type: 'scatter',
        backgroundColor: '#ff4444',
        pointStyle: 'triangle',
        pointRadius: 8,
        rotation: 180
      }
    ]
  },
  options: {
    responsive: true,
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Price (USD)'
        }
      }
    }
  }
};
```

## 📊 Chart 2: Portfolio Performance

### Data Query:
```javascript
// Get transaction history for portfolio tracking
const { data: transactions } = await supabase
  .from('transaction_records')
  .select('timestamp, portfolio_value, timeframe')
  .eq('timeframe', '4H')
  .order('timestamp', { ascending: true });
```

### Chart Implementation:
```javascript
// Prepare portfolio data
const portfolioData = transactions.map(item => ({
  x: new Date(item.timestamp),
  y: item.portfolio_value
}));

// Chart config
const portfolioChart = {
  type: 'line',
  data: {
    datasets: [{
      label: 'Portfolio Value',
      data: portfolioData,
      borderColor: '#007bff',
      backgroundColor: 'rgba(0, 123, 255, 0.1)',
      fill: true
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        title: {
          display: true,
          text: 'Portfolio Value ($)'
        }
      }
    }
  }
};
```

## 📈 Chart 3: Performance Comparison

### Data Query:
```javascript
// Get latest performance for all timeframes
const { data: performance } = await supabase
  .from('performance_summary')
  .select('timeframe, total_return, win_rate, total_trades')
  .order('total_return', { ascending: false });
```

### Chart Implementation:
```javascript
// Prepare data for bar chart
const timeframes = performance.map(item => item.timeframe);
const returns = performance.map(item => item.total_return);
const winRates = performance.map(item => item.win_rate);

const comparisonChart = {
  type: 'bar',
  data: {
    labels: timeframes,
    datasets: [
      {
        label: 'Total Return (%)',
        data: returns,
        backgroundColor: '#28a745',
        yAxisID: 'y'
      },
      {
        label: 'Win Rate (%)',
        data: winRates,
        backgroundColor: '#17a2b8',
        type: 'line',
        yAxisID: 'y1'
      }
    ]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: 'Total Return (%)' }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: { display: true, text: 'Win Rate (%)' },
        grid: { drawOnChartArea: false }
      }
    }
  }
};
```

## 🔄 Real-time Updates

### Subscribe to data changes:
```javascript
// Listen for new data
const subscription = supabase
  .channel('ai_trend_updates')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'ai_trend_data' },
    (payload) => {
      // Update chart with new data
      updateChart(payload.new);
    }
  )
  .subscribe();

function updateChart(newData) {
  // Add new point to chart
  chart.data.datasets[0].data.push({
    x: new Date(newData.timestamp),
    o: newData.open_price,
    h: newData.high_price,
    l: newData.low_price,
    c: newData.close_price
  });
  
  // Update chart
  chart.update();
}
```

## 🎨 Simple Dashboard Layout

### HTML Structure:
```html
<!DOCTYPE html>
<html>
<head>
    <title>AI Trend Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <!-- Timeframe Selector -->
    <select id="timeframeSelect">
        <option value="4H">4 Hours</option>
        <option value="8H">8 Hours</option>
        <option value="1D">1 Day</option>
        <option value="1W">1 Week</option>
        <option value="1M">1 Month</option>
    </select>

    <!-- Charts Container -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
        <!-- Main Price Chart -->
        <canvas id="priceChart"></canvas>
        
        <!-- Portfolio Chart -->
        <canvas id="portfolioChart"></canvas>
    </div>

    <!-- Performance Table -->
    <div id="performanceTable"></div>
</body>
</html>
```

### JavaScript Implementation:
```javascript
// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', async () => {
    // Load initial data
    await loadCharts('4H');
    
    // Handle timeframe changes
    document.getElementById('timeframeSelect').addEventListener('change', (e) => {
        loadCharts(e.target.value);
    });
});

async function loadCharts(timeframe) {
    // Fetch data from Supabase
    const priceData = await fetchPriceData(timeframe);
    const transactionData = await fetchTransactionData(timeframe);
    
    // Update charts
    updatePriceChart(priceData);
    updatePortfolioChart(transactionData);
}
```

## 🎯 Key Points for Implementation:

1. **Use `ai_trend_data` table** for price charts and AI trend lines
2. **Use `transaction_records` table** for portfolio tracking
3. **Use `performance_summary` table** for comparison charts
4. **Filter by `timeframe`** to show different periods
5. **Order by `timestamp`** for proper chart sequence
6. **Use real-time subscriptions** for live updates

## 🔥 Quick Blue Line Recreation:

```javascript
// Get ALL data points to recreate the exact blue line from your chart
const { data } = await supabase
  .from('ai_trend_data')
  .select('timestamp, close_price, smoothed_signal, buy_signal, sell_signal')
  .eq('timeframe', '1M')  // Or any timeframe you want
  .order('timestamp');

// Recreate the EXACT blue line from your chart image
const blueLine = data.map(item => ({
  x: new Date(item.timestamp),
  y: item.smoothed_signal  // This IS your blue line data!
}));

// Buy/sell signals (green/red triangles)
const buySignals = data.filter(item => item.buy_signal).map(item => ({
  x: new Date(item.timestamp), 
  y: item.close_price
}));

const sellSignals = data.filter(item => item.sell_signal).map(item => ({
  x: new Date(item.timestamp), 
  y: item.close_price
}));

// Chart configuration to match your image
const chart = {
  type: 'candlestick',  // For price candles
  data: {
    datasets: [
      {
        label: 'BTC Price',
        data: candlestickData,  // Your price data
        type: 'candlestick'
      },
      {
        label: 'AI Trend Navigator',  // The blue line from your chart
        data: blueLine,
        type: 'line',
        borderColor: '#0066FF',    // Blue color like in your image
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0,            // No dots on the line
        tension: 0.1               // Slight curve smoothing
      },
      {
        label: 'Buy Signals',
        data: buySignals,
        type: 'scatter',
        backgroundColor: '#00FF00',  // Green triangles
        pointStyle: 'triangle',
        pointRadius: 6,
        showLine: false
      },
      {
        label: 'Sell Signals', 
        data: sellSignals,
        type: 'scatter',
        backgroundColor: '#FF0000',  // Red triangles
        pointStyle: 'triangle',
        pointRadius: 6,
        rotation: 180,               // Point down
        showLine: false
      }
    ]
  }
};
```

## ✅ Database Confirmation:

Your blue line data is stored as:
- **Table**: `ai_trend_data`
- **Column**: `smoothed_signal` 
- **Contains**: Every single data point of the blue trend line
- **Coverage**: All timeframes (4H, 8H, 1D, 1W, 1M)

## 📊 Simple Blue Line Query:

```sql
-- Get all blue line data points for 1M timeframe
SELECT 
  timestamp,
  smoothed_signal as blue_line_value
FROM ai_trend_data 
WHERE timeframe = '1M'
ORDER BY timestamp;
```

```javascript
// Minimal code to get just the blue line
const { data: blueLineData } = await supabase
  .from('ai_trend_data')
  .select('timestamp, smoothed_signal')
  .eq('timeframe', '1M')
  .order('timestamp');

// Convert to chart format
const blueLinePoints = blueLineData.map(point => ({
  x: new Date(point.timestamp),
  y: point.smoothed_signal
}));
```

## 📱 Mobile-Friendly Tips:

- Use responsive chart options: `responsive: true`
- Make touch-friendly controls (larger buttons)
- Stack charts vertically on mobile
- Use horizontal scrolling for tables

This gives you everything needed to create interactive charts from your Supabase data! 🚀 