let ratioChart = null;
let useLogScale = false;
let marketFilter = "ALL";
let currentWindow = 20;

async function fetchJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }
  return await resp.json();
}

function formatPct(x) {
  const v = Number.isFinite(x) ? x : 0;
  return v.toFixed(2);
}

function formatNumber(x) {
  const v = Number.isFinite(x) ? x : 0;
  return v.toLocaleString();
}

// ========== Stock Chart ==========

async function loadStock(code) {
  const status = document.getElementById("statusText");
  const title = document.getElementById("chartTitle");
  const btn = document.getElementById("loadBtn");

  code = (code || "").trim();
  if (!code) return;

  btn.disabled = true;
  status.textContent = `載入 ${code}...`;

  const showForeign = document.getElementById("showForeign").checked;
  const showTrust = document.getElementById("showTrust").checked;
  const showDealer = document.getElementById("showDealer").checked;
  const showTotal = document.getElementById("showTotal").checked;

  try {
    const data = await fetchJson(`data/timeseries/${code}.json`);
    if (!data.length) {
      status.textContent = `找不到 ${code} 資料`;
      btn.disabled = false;
      return;
    }

    const name = data[0].name || "";
    const market = data[0].market || "";
    title.textContent = `${code} ${name}（${market}）`;

    const labels = data.map((d) => d.date);
    const foreignRatio = data.map((d) => d.foreign_ratio);
    const trustRatio = data.map((d) => d.trust_ratio);
    const dealerRatio = data.map((d) => d.dealer_ratio);
    const totalRatio = data.map((d) => d.three_inst_ratio);

    const datasets = [];
    if (showForeign) {
      datasets.push({
        label: "外資%",
        data: foreignRatio,
        borderColor: "#ff6b6b",
        backgroundColor: "rgba(255, 107, 107, 0.1)",
        borderWidth: 2,
        tension: 0.3,
        fill: true,
      });
    }
    if (showTrust) {
      datasets.push({
        label: "投信%",
        data: trustRatio,
        borderColor: "#4ecdc4",
        borderWidth: 2,
        borderDash: [5, 3],
        tension: 0.3,
      });
    }
    if (showDealer) {
      datasets.push({
        label: "自營商%",
        data: dealerRatio,
        borderColor: "#ffe66d",
        borderWidth: 2,
        borderDash: [2, 2],
        tension: 0.3,
      });
    }
    if (showTotal) {
      datasets.push({
        label: "三法人合計%",
        data: totalRatio,
        borderColor: "#a55eea",
        borderWidth: 3,
        pointRadius: 0,
        tension: 0.3,
      });
    }

    const ctx = document.getElementById("ratioChart").getContext("2d");
    if (ratioChart) {
      ratioChart.destroy();
    }

    ratioChart = new Chart(ctx, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        interaction: { mode: "index", intersect: false },
        scales: {
          x: {
            ticks: { maxTicksLimit: 8, color: "#8b8b9e" },
            grid: { color: "rgba(255,255,255,0.05)" },
          },
          y: {
            type: useLogScale ? "logarithmic" : "linear",
            title: { display: true, text: "持股比重 (%)", color: "#8b8b9e" },
            ticks: { color: "#8b8b9e" },
            grid: { color: "rgba(255,255,255,0.05)" },
            min: 0,
          },
        },
        plugins: {
          legend: { position: "bottom", labels: { color: "#eaeaea" } },
        },
      },
    });

    const last = data[data.length - 1];
    status.textContent = `${last.date} | 三大法人 ${formatPct(last.three_inst_ratio)}%`;
  } catch (err) {
    console.error(err);
    status.textContent = `載入失敗：${err.message}`;
  } finally {
    btn.disabled = false;
  }
}

// ========== Institutional Ranking ==========

async function loadRanking() {
  const tbody = document.querySelector("#rankTable tbody");
  tbody.innerHTML = "<tr><td colspan='5'>載入中...</td></tr>";

  try {
    const up = await fetchJson(`data/top_three_inst_change_${currentWindow}_up.json`);
    tbody.innerHTML = "";

    const filtered = up.filter((row) => {
      if (marketFilter === "ALL") return true;
      return row.market === marketFilter;
    });

    filtered.slice(0, 50).forEach((row, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td><span class="badge">${row.code}</span>${row.name || ""}</td>
        <td>${row.market || ""}</td>
        <td>${formatPct(row.three_inst_ratio)}</td>
        <td class="${row.change >= 0 ? 'net-positive' : 'net-negative'}">${row.change >= 0 ? '+' : ''}${formatPct(row.change)}</td>
      `;
      tr.addEventListener("click", () => {
        document.getElementById("stockInput").value = row.code;
        loadStock(row.code);
      });
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
    tbody.innerHTML = `<tr><td colspan='5'>載入失敗：${err.message}</td></tr>`;
  }
}

// ========== Broker Functions ==========

async function loadBrokerRanking() {
  const tbody = document.querySelector("#brokerRankTable tbody");
  const updateTime = document.getElementById("brokerUpdateTime");

  if (!tbody) return;
  tbody.innerHTML = "<tr><td colspan='6'>載入中...</td></tr>";

  try {
    const data = await fetchJson("data/broker_ranking.json");
    tbody.innerHTML = "";

    if (updateTime && data.updated) {
      updateTime.textContent = `更新：${new Date(data.updated).toLocaleString("zh-TW")}`;
    }

    if (!data.data || data.data.length === 0) {
      tbody.innerHTML = "<tr><td colspan='6'>尚無券商數據</td></tr>";
      return;
    }

    data.data.slice(0, 50).forEach((row, idx) => {
      const netVol = row.total_net_vol || 0;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td>${row.broker_name || ""}</td>
        <td class="${netVol > 0 ? 'net-positive' : 'net-negative'}">${formatNumber(netVol)}</td>
        <td>${row.buy_count || 0}</td>
        <td>${row.sell_count || 0}</td>
        <td>${row.stocks_traded || 0}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
    tbody.innerHTML = `<tr><td colspan='6'>載入失敗：${err.message}</td></tr>`;
  }
}

async function loadBrokerTrades() {
  const tbody = document.querySelector("#brokerTradesTable tbody");
  const status = document.getElementById("brokerTradesStatus");

  if (!tbody) return;
  tbody.innerHTML = "";
  status.textContent = "載入中...";

  try {
    const data = await fetchJson("data/broker_trades_latest.json");

    if (!data.data || data.data.length === 0) {
      status.textContent = "尚無交易數據";
      return;
    }

    status.textContent = `共 ${data.count || 0} 筆交易`;

    data.data.slice(0, 100).forEach((row) => {
      const netVol = row.net_vol || 0;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.date || ""}</td>
        <td><span class="badge">${row.stock_code}</span></td>
        <td>${row.broker_name || ""}</td>
        <td>${formatNumber(row.buy_vol || 0)}</td>
        <td>${formatNumber(row.sell_vol || 0)}</td>
        <td class="${netVol > 0 ? 'net-positive' : 'net-negative'}">${formatNumber(netVol)}</td>
        <td>${formatPct(row.pct || 0)}%</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
    status.textContent = `載入失敗：${err.message}`;
  }
}

async function loadTargetBrokers() {
  const container = document.getElementById("targetBrokersContent");
  if (!container) return;

  container.innerHTML = "<p>載入中...</p>";

  try {
    const data = await fetchJson("data/target_broker_trades.json");

    if (!data.brokers || Object.keys(data.brokers).length === 0) {
      container.innerHTML = "<p>尚無目標券商數據</p>";
      return;
    }

    container.innerHTML = "";

    Object.entries(data.brokers).forEach(([brokerName, trades]) => {
      const totalNet = trades.reduce((sum, t) => sum + (t.net_vol || 0), 0);
      const netClass = totalNet > 0 ? "net-positive" : "net-negative";

      const card = document.createElement("div");
      card.className = "broker-card";
      card.innerHTML = `
        <h4>
          ${brokerName}
          <span class="${netClass}">${formatNumber(totalNet)} 張</span>
        </h4>
        <div class="trades-list">
          ${trades.slice(0, 8).map(t => {
        const sideClass = t.net_vol > 0 ? "buy-text" : "sell-text";
        return `<span class="badge">${t.stock_code}</span><span class="${sideClass}">${formatNumber(t.net_vol)}</span> `;
      }).join("")}
          ${trades.length > 8 ? `<br><small style="color:#8b8b9e">+${trades.length - 8} 筆</small>` : ""}
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error(err);
    container.innerHTML = `<p>載入失敗：${err.message}</p>`;
  }
}

// ========== Broker Trend Chart ==========

let brokerTrendChart = null;
let brokerTrendsData = null;

async function loadBrokerTrends() {
  const select = document.getElementById("brokerSelect");
  if (!select) return;

  try {
    brokerTrendsData = await fetchJson("data/broker_trends.json");

    if (!brokerTrendsData.brokers || Object.keys(brokerTrendsData.brokers).length === 0) {
      return;
    }

    // Populate broker select
    select.innerHTML = '<option value="ALL">全部目標券商</option>';
    Object.keys(brokerTrendsData.brokers).forEach(broker => {
      const option = document.createElement("option");
      option.value = broker;
      option.textContent = broker;
      select.appendChild(option);
    });

    // Add event listener
    select.addEventListener("change", () => {
      renderBrokerTrendChart(select.value);
    });

    // Initial render
    renderBrokerTrendChart("ALL");
  } catch (err) {
    console.error("Failed to load broker trends:", err);
  }
}

function renderBrokerTrendChart(selectedBroker) {
  const ctx = document.getElementById("brokerTrendChart");
  if (!ctx || !brokerTrendsData) return;

  // Destroy existing chart
  if (brokerTrendChart) {
    brokerTrendChart.destroy();
  }

  const brokers = brokerTrendsData.brokers;
  const datasets = [];

  // Define colors for different brokers
  const colors = [
    "#ff6b6b", "#4ecdc4", "#ffe66d", "#a55eea", "#45aaf2",
    "#fed330", "#26de81", "#fd9644", "#eb3b5a", "#2bcbba"
  ];

  let colorIndex = 0;
  let allDates = new Set();

  // Collect all dates
  Object.values(brokers).forEach(data => {
    data.forEach(d => allDates.add(d.date));
  });
  const sortedDates = Array.from(allDates).sort();

  // Build datasets
  Object.entries(brokers).forEach(([brokerName, data]) => {
    if (selectedBroker !== "ALL" && brokerName !== selectedBroker) {
      return;
    }

    // Create date -> cumulative map
    const dateMap = {};
    data.forEach(d => {
      dateMap[d.date] = d.cumulative;
    });

    // Fill in missing dates with last known value
    const values = [];
    let lastValue = 0;
    sortedDates.forEach(date => {
      if (dateMap[date] !== undefined) {
        lastValue = dateMap[date];
      }
      values.push(lastValue);
    });

    datasets.push({
      label: brokerName,
      data: values,
      borderColor: colors[colorIndex % colors.length],
      backgroundColor: "transparent",
      borderWidth: 2,
      tension: 0.3,
      pointRadius: selectedBroker === "ALL" ? 0 : 3,
    });

    colorIndex++;
  });

  brokerTrendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: sortedDates,
      datasets: datasets,
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          ticks: { maxTicksLimit: 10, color: "#8b8b9e" },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        y: {
          title: { display: true, text: "累計買賣超 (張)", color: "#8b8b9e" },
          ticks: { color: "#8b8b9e" },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#eaeaea", boxWidth: 12 },
        },
      },
    },
  });
}

// ========== Navigation ==========


function initNavigation() {
  const navBtns = document.querySelectorAll(".nav-btn");
  const sections = document.querySelectorAll(".section");

  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetSection = btn.dataset.section;

      // Update nav buttons
      navBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      // Update sections
      sections.forEach(section => {
        section.classList.remove("active");
        if (section.id === targetSection) {
          section.classList.add("active");
        }
      });

      // Load data for broker section on first click
      if (targetSection === "broker") {
        loadBrokerSummaryStats();
        createBrokerRankingChart();
        createBrokerHeatmap();
        loadBrokerTrends();
        loadBrokerTrades();
        loadTargetBrokers();
      }

      // Load AI analysis data on first click
      if (targetSection === "ai-analysis") {
        loadAIAnalysis();
      }
    });
  });
}

// ========== Initialization ==========

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("stockInput");
  const btn = document.getElementById("loadBtn");
  const marketSel = document.getElementById("marketFilter");
  const windowSel = document.getElementById("windowFilter");
  const logCb = document.getElementById("logScaleCheckbox");
  const showForeign = document.getElementById("showForeign");
  const showTrust = document.getElementById("showTrust");
  const showDealer = document.getElementById("showDealer");
  const showTotal = document.getElementById("showTotal");

  btn.addEventListener("click", () => loadStock(input.value));
  input.addEventListener("keyup", (e) => {
    if (e.key === "Enter") loadStock(input.value);
  });

  marketSel.addEventListener("change", () => {
    marketFilter = marketSel.value;
    loadRanking();
  });

  windowSel.addEventListener("change", () => {
    currentWindow = parseInt(windowSel.value, 10);
    loadRanking();
  });

  logCb.addEventListener("change", () => {
    useLogScale = logCb.checked;
    loadStock(input.value || "2330");
  });

  [showForeign, showTrust, showDealer, showTotal].forEach((cb) => {
    cb.addEventListener("change", () => loadStock(input.value || "2330"));
  });

  // Initialize navigation
  initNavigation();

  // Add report selector handler
  const reportSelect = document.getElementById("reportSelect");
  if (reportSelect) {
    reportSelect.addEventListener("change", () => {
      loadFullReport(reportSelect.value);
    });
  }

  // Load initial data
  input.value = "2330";
  loadStock("2330");
  loadRanking();
});

// ========== AI Analysis Functions ==========

let institutionalTrendChart = null;
let sentimentGaugeChart = null;
let recommendationRadarChart = null;

async function loadAIAnalysis() {
  try {
    await Promise.all([
      createInstitutionalTrendChart(),
      createSentimentGauge(),
      createRecommendationRadarChart(),
      createHoldingHeatmap(),
      loadTrendAnalysis(),
      loadSentimentAnalysis(), 
      loadRecommendations(),
      loadWatchlists(),
      loadIndividualAnalysis()
    ]);
  } catch (error) {
    console.error("Failed to load AI analysis:", error);
  }
}

async function loadTrendAnalysis() {
  const container = document.getElementById("trendAnalysisContent");
  try {
    const data = await fetchJson("data/ai_analysis/trend_analysis_20d.json");
    
    let html = `<h4>20日法人持股趨勢分析</h4>`;
    
    // AI 分析摘要
    if (data.ai_insights?.summary) {
      html += `<div class="analysis-summary">${data.ai_insights.summary}</div>`;
    }
    
    // 增持股票
    if (data.top_gainers && data.top_gainers.length > 0) {
      html += `<h4>📈 法人增持前三名</h4><ul>`;
      data.top_gainers.slice(0, 3).forEach(stock => {
        const change = stock.change || 0;
        const currentRatio = stock.three_inst_ratio || 0;
        html += `<li><strong>${stock.code} ${stock.name}</strong> (${stock.market}) <br>
                 增持 <span class="net-negative">+${change.toFixed(2)}%</span> | 
                 目前持股 ${currentRatio.toFixed(1)}%</li>`;
      });
      html += `</ul>`;
    }
    
    // 減持股票
    if (data.top_decliners && data.top_decliners.length > 0) {
      html += `<h4>📉 法人減持前三名</h4><ul>`;
      data.top_decliners.slice(0, 3).forEach(stock => {
        const change = stock.change || 0;
        const currentRatio = stock.three_inst_ratio || 0;
        html += `<li><strong>${stock.code} ${stock.name}</strong> (${stock.market}) <br>
                 減持 <span class="net-positive">${change.toFixed(2)}%</span> | 
                 目前持股 ${currentRatio.toFixed(1)}%</li>`;
      });
      html += `</ul>`;
    }
    
    // 趨勢統計
    if (data.ai_insights?.key_trends) {
      const trends = data.ai_insights.key_trends;
      html += `<div class="metric-grid">
        <div class="metric-item">
          <div class="metric-label">增持股數量</div>
          <div class="metric-value">${trends.gainer_count || 'N/A'}檔</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">平均增持幅度</div>
          <div class="metric-value">+${(trends.avg_gainer_change || 0).toFixed(1)}%</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">減持股數量</div>
          <div class="metric-value">${trends.decliner_count || 'N/A'}檔</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">平均減持幅度</div>
          <div class="metric-value">${(trends.avg_decliner_change || 0).toFixed(1)}%</div>
        </div>
      </div>`;
    }

    container.innerHTML = html;
  } catch (error) {
    console.error("Trend analysis error:", error);
    container.innerHTML = "趨勢分析數據載入失敗";
  }
}

async function loadSentimentAnalysis() {
  const container = document.getElementById("sentimentAnalysisContent");
  try {
    const data = await fetchJson("data/ai_analysis/market_sentiment_analysis.json");
    
    let html = `<h4>市場情緒指標</h4>`;
    html += `<div class="analysis-summary">整體情緒：<strong>${data.overall_sentiment || "中性"}</strong></div>`;
    
    if (data.sentiment_summary) {
      html += `<p>${data.sentiment_summary}</p>`;
    }

    container.innerHTML = html;
  } catch (error) {
    container.innerHTML = "情緒分析數據載入失敗";
  }
}

async function loadRecommendations() {
  const container = document.getElementById("recommendationsContent");
  try {
    const data = await fetchJson("data/ai_analysis/stock_recommendations.json");
    
    let html = "";
    
    if (data.recommendations && data.recommendations.length > 0) {
      data.recommendations.forEach(stock => {
        html += `
          <div class="stock-recommendation">
            <h4>
              ${stock.stock_code} ${stock.stock_name}
              <span class="recommendation-strength">${stock.recommendation_strength}</span>
            </h4>
            <div class="metric-grid">
              <div class="metric-item">
                <div class="metric-label">法人持股</div>
                <div class="metric-value">${stock.key_metrics?.current_inst_ratio?.toFixed(1) || 'N/A'}%</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">動能評分</div>
                <div class="metric-value">${stock.key_metrics?.momentum_score?.toFixed(2) || 'N/A'}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">品質評分</div>
                <div class="metric-value">${stock.key_metrics?.quality_score?.toFixed(2) || 'N/A'}</div>
              </div>
            </div>
            <div class="analysis-summary">
              ${stock.investment_thesis || "投資論述載入中..."}
            </div>
          </div>
        `;
      });
    } else {
      html = "目前無推薦股票";
    }

    container.innerHTML = html;
  } catch (error) {
    container.innerHTML = "推薦數據載入失敗";
  }
}

async function loadWatchlists() {
  const container = document.getElementById("watchlistContent");
  try {
    const [momentum, quality, activity] = await Promise.all([
      fetchJson("data/ai_analysis/watchlist_momentum.json"),
      fetchJson("data/ai_analysis/watchlist_quality.json"), 
      fetchJson("data/ai_analysis/watchlist_activity.json")
    ]);

    let html = `
      <h4>動能觀察清單</h4>
      <p>標準：${momentum.criteria?.focus || "動能分析"}</p>
      <p>篩選結果：${momentum.metadata?.final_selection || 0} 檔股票</p>
      
      <h4>品質觀察清單</h4>
      <p>標準：${quality.criteria?.focus || "品質分析"}</p>
      <p>篩選結果：${quality.metadata?.final_selection || 0} 檔股票</p>
      
      <h4>活躍度觀察清單</h4>
      <p>標準：${activity.criteria?.focus || "活躍度分析"}</p>
      <p>篩選結果：${activity.metadata?.final_selection || 0} 檔股票</p>
    `;

    container.innerHTML = html;
  } catch (error) {
    container.innerHTML = "觀察清單載入失敗";
  }
}

async function loadIndividualAnalysis() {
  const container = document.getElementById("individualAnalysisContent");
  try {
    const stockCodes = ["1560", "6944", "6139"];
    const analysisPromises = stockCodes.map(code => 
      fetchJson(`data/ai_analysis/individual_analysis_${code}.json`)
    );
    
    const analyses = await Promise.all(analysisPromises);
    
    let html = "";
    analyses.forEach(data => {
      if (data) {
        const totalHolding = data.current_holdings?.total_ratio || 0;
        const foreignTrend = data.ai_insights?.trend_metrics?.foreign_trend_direction || "持平";
        const trustTrend = data.ai_insights?.trend_metrics?.trust_trend_direction || "持平";
        const dealerTrend = data.ai_insights?.trend_metrics?.dealer_trend_direction || "持平";
        
        html += `
          <div class="individual-stock-card">
            <h4>
              ${data.stock_name || "N/A"}
              <span class="stock-code">${data.stock_code}</span>
            </h4>
            <div class="metric-grid">
              <div class="metric-item">
                <div class="metric-label">法人合計持股</div>
                <div class="metric-value">${totalHolding.toFixed(1)}%</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">外資持股</div>
                <div class="metric-value">${(data.current_holdings?.foreign_ratio || 0).toFixed(1)}%</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">投信持股</div>
                <div class="metric-value">${(data.current_holdings?.trust_ratio || 0).toFixed(1)}%</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">自營商持股</div>
                <div class="metric-value">${(data.current_holdings?.dealer_ratio || 0).toFixed(1)}%</div>
              </div>
            </div>
            <div class="metric-grid">
              <div class="metric-item">
                <div class="metric-label">外資趨勢</div>
                <div class="metric-value ${foreignTrend === '上升' ? 'net-negative' : foreignTrend === '下降' ? 'net-positive' : ''}">${foreignTrend}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">投信趨勢</div>
                <div class="metric-value ${trustTrend === '上升' ? 'net-negative' : trustTrend === '下降' ? 'net-positive' : ''}">${trustTrend}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">自營趨勢</div>
                <div class="metric-value ${dealerTrend === '上升' ? 'net-negative' : dealerTrend === '下降' ? 'net-positive' : ''}">${dealerTrend}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">分析天數</div>
                <div class="metric-value">${data.analysis_period_days || 'N/A'}天</div>
              </div>
            </div>
            <div class="analysis-summary">
              <h4>AI 投資洞察</h4>
              <p><strong>摘要：</strong>${data.ai_insights?.summary || "分析摘要載入中..."}</p>
              <div class="risk-factors">
                <strong>詳細分析：</strong>
                <div style="white-space: pre-line; margin-top: 0.5rem; line-height: 1.5;">
                  ${data.ai_insights?.detailed_analysis || "詳細分析載入中..."}
                </div>
              </div>
            </div>
          </div>
        `;
      }
    });

    if (html === "") {
      html = "個股分析數據載入中...";
    }

    container.innerHTML = html;
  } catch (error) {
    console.error("Individual analysis error:", error);
    container.innerHTML = "個股分析載入失敗：" + error.message;
  }
}

async function loadFullReport(reportType) {
  const container = document.getElementById("fullReportContent");
  
  if (!reportType) {
    container.innerHTML = "請選擇一個報告查看詳細內容";
    return;
  }

  try {
    const data = await fetchJson(`data/ai_analysis/${reportType}.json`);
    let html = "";
    
    switch (reportType) {
      case 'trend_analysis_5d':
      case 'trend_analysis_20d':
      case 'trend_analysis_60d':
        html = formatTrendAnalysisReport(data, reportType);
        break;
      case 'market_sentiment_analysis':
        html = formatSentimentAnalysisReport(data);
        break;
      case 'stock_recommendations':
        html = formatRecommendationsReport(data);
        break;
      default:
        html = formatGenericReport(data);
    }
    
    container.innerHTML = html;
  } catch (error) {
    container.innerHTML = "報告載入失敗：" + error.message;
  }
}

function formatTrendAnalysisReport(data, reportType) {
  const period = reportType.includes('5d') ? '5日' : reportType.includes('20d') ? '20日' : '60日';
  
  let html = `
    <div class="report-header">
      <h3>📊 ${period}法人持股趨勢分析報告</h3>
      <p class="report-meta">分析日期：${new Date(data.analysis_date).toLocaleString('zh-TW')}</p>
    </div>
  `;
  
  // AI 洞察分析
  if (data.ai_insights?.summary) {
    html += `
      <div class="report-section">
        <h4>🎯 核心洞察</h4>
        <div class="insight-content">${data.ai_insights.summary}</div>
      </div>
    `;
  }
  
  if (data.ai_insights?.detailed_analysis) {
    html += `
      <div class="report-section">
        <h4>📋 詳細分析</h4>
        <div class="detailed-analysis">${data.ai_insights.detailed_analysis.replace(/\n/g, '<br>')}</div>
      </div>
    `;
  }
  
  // 增持股票排名
  if (data.top_gainers && data.top_gainers.length > 0) {
    html += `
      <div class="report-section">
        <h4>📈 法人增持股票排名（前10名）</h4>
        <div class="stock-ranking">
    `;
    
    data.top_gainers.slice(0, 10).forEach((stock, index) => {
      html += `
        <div class="rank-item">
          <span class="rank-number">${index + 1}</span>
          <div class="stock-info">
            <strong>${stock.code} ${stock.name}</strong> (${stock.market})
            <div class="stock-metrics">
              增持幅度：<span class="net-negative">+${stock.change.toFixed(2)}%</span> | 
              目前法人持股：${stock.three_inst_ratio.toFixed(1)}%
            </div>
          </div>
        </div>
      `;
    });
    
    html += '</div></div>';
  }
  
  // 減持股票排名
  if (data.top_decliners && data.top_decliners.length > 0) {
    html += `
      <div class="report-section">
        <h4>📉 法人減持股票排名（前10名）</h4>
        <div class="stock-ranking">
    `;
    
    data.top_decliners.slice(0, 10).forEach((stock, index) => {
      html += `
        <div class="rank-item">
          <span class="rank-number">${index + 1}</span>
          <div class="stock-info">
            <strong>${stock.code} ${stock.name}</strong> (${stock.market})
            <div class="stock-metrics">
              減持幅度：<span class="net-positive">${stock.change.toFixed(2)}%</span> | 
              目前法人持股：${stock.three_inst_ratio.toFixed(1)}%
            </div>
          </div>
        </div>
      `;
    });
    
    html += '</div></div>';
  }
  
  // 統計數據
  if (data.ai_insights?.key_trends) {
    const trends = data.ai_insights.key_trends;
    html += `
      <div class="report-section">
        <h4>📊 統計數據摘要</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">增持股票數量</div>
            <div class="stat-value">${trends.gainer_count}檔</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">平均增持幅度</div>
            <div class="stat-value">+${trends.avg_gainer_change.toFixed(2)}%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">最大增持幅度</div>
            <div class="stat-value">+${trends.max_gain.toFixed(2)}%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">減持股票數量</div>
            <div class="stat-value">${trends.decliner_count}檔</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">平均減持幅度</div>
            <div class="stat-value">${trends.avg_decliner_change.toFixed(2)}%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">最大減持幅度</div>
            <div class="stat-value">${trends.max_decline.toFixed(2)}%</div>
          </div>
        </div>
      </div>
    `;
  }
  
  return html;
}

function formatSentimentAnalysisReport(data) {
  let html = `
    <div class="report-header">
      <h3>💭 市場情緒分析報告</h3>
      <p class="report-meta">生成時間：${new Date(data.metadata?.generated_at).toLocaleString('zh-TW')}</p>
    </div>
  `;
  
  if (data.overall_sentiment) {
    html += `
      <div class="report-section">
        <h4>🎯 整體市場情緒</h4>
        <div class="sentiment-indicator ${data.overall_sentiment.toLowerCase()}">
          ${data.overall_sentiment}
        </div>
      </div>
    `;
  }
  
  if (data.sentiment_summary) {
    html += `
      <div class="report-section">
        <h4>📋 情緒分析摘要</h4>
        <div class="sentiment-content">${data.sentiment_summary}</div>
      </div>
    `;
  }
  
  if (data.detailed_analysis) {
    html += `
      <div class="report-section">
        <h4>🔍 詳細分析</h4>
        <div class="detailed-analysis">${data.detailed_analysis.replace(/\n/g, '<br>')}</div>
      </div>
    `;
  }
  
  return html;
}

function formatRecommendationsReport(data) {
  let html = `
    <div class="report-header">
      <h3>⭐ 股票推薦分析報告</h3>
      <p class="report-meta">生成時間：${new Date(data.metadata?.generated_at).toLocaleString('zh-TW')}</p>
      <p class="report-meta">候選股票篩選：${data.total_candidates_screened}檔 → 推薦${data.recommendations?.length || 0}檔</p>
    </div>
  `;
  
  // 市場環境
  if (data.market_context) {
    html += `
      <div class="report-section">
        <h4>🌍 市場環境分析</h4>
        <div class="market-context">
          <p><strong>市場環境：</strong>${data.market_context.market_environment}</p>
          <p><strong>法人趨勢：</strong>${data.market_context.institutional_trend}</p>
          <p><strong>分析基礎：</strong>${data.market_context.recommendation_basis}</p>
          <p><strong>投資期間：</strong>${data.market_context.time_horizon}</p>
        </div>
      </div>
    `;
  }
  
  // 篩選標準
  if (data.screening_criteria) {
    html += `
      <div class="report-section">
        <h4>🎯 篩選標準</h4>
        <ul class="criteria-list">
          <li><strong>最低法人持股：</strong>${data.screening_criteria.minimum_institutional_holding}</li>
          <li><strong>動能要求：</strong>${data.screening_criteria.momentum_requirement}</li>
          <li><strong>品質門檻：</strong>${data.screening_criteria.quality_threshold}</li>
          <li><strong>活躍度要求：</strong>${data.screening_criteria.activity_requirement}</li>
          <li><strong>數據要求：</strong>${data.screening_criteria.data_requirement}</li>
        </ul>
      </div>
    `;
  }
  
  // 推薦股票
  if (data.recommendations && data.recommendations.length > 0) {
    html += `<div class="report-section"><h4>📈 推薦股票分析</h4>`;
    
    data.recommendations.forEach((stock, index) => {
      html += `
        <div class="recommendation-detail">
          <div class="rec-header">
            <h5>${index + 1}. ${stock.stock_code} ${stock.stock_name}</h5>
            <span class="rec-strength">${stock.recommendation_strength}</span>
          </div>
          
          <div class="rec-metrics">
            <div class="metric-row">
              <span>市場：${stock.market} | 綜合評分：${stock.composite_score?.toFixed(3)}</span>
            </div>
            <div class="key-metrics-grid">
              <div>法人持股：${stock.key_metrics?.current_inst_ratio?.toFixed(1)}%</div>
              <div>動能評分：${stock.key_metrics?.momentum_score?.toFixed(2)}</div>
              <div>品質評分：${stock.key_metrics?.quality_score?.toFixed(2)}</div>
              <div>活躍評分：${stock.key_metrics?.activity_score?.toFixed(2)}</div>
              <div>5日趨勢：${stock.key_metrics?.['5d_trend']?.toFixed(2)}%</div>
            </div>
          </div>
          
          <div class="investment-thesis">
            <h6>💡 投資論述</h6>
            <p>${stock.investment_thesis}</p>
          </div>
          
          <div class="risk-analysis">
            <h6>⚠️ 風險提醒</h6>
            <ul>
              ${stock.risk_factors?.map(risk => `<li>${risk}</li>`).join('') || '<li>風險分析資料載入中...</li>'}
            </ul>
          </div>
        </div>
      `;
    });
    
    html += '</div>';
  }
  
  // 風險聲明
  if (data.market_context?.risk_disclaimer) {
    html += `
      <div class="report-section risk-disclaimer">
        <h4>⚠️ 風險聲明</h4>
        <p>${data.market_context.risk_disclaimer}</p>
      </div>
    `;
  }
  
  return html;
}

function formatGenericReport(data) {
  let html = `
    <div class="report-header">
      <h3>📊 分析報告</h3>
      <p class="report-meta">生成時間：${data.metadata?.generated_at ? new Date(data.metadata.generated_at).toLocaleString('zh-TW') : '未知'}</p>
    </div>
    <div class="report-section">
      <h4>原始數據</h4>
      <pre class="json-data">${JSON.stringify(data, null, 2)}</pre>
    </div>
  `;
  
  return html;
}

// ========== AI Chart Functions ==========

async function createInstitutionalTrendChart() {
  const canvas = document.getElementById("institutionalTrendChart");
  if (!canvas) return;
  
  try {
    const data = await fetchJson("data/ai_analysis/trend_analysis_20d.json");
    
    if (institutionalTrendChart) {
      institutionalTrendChart.destroy();
    }
    
    const ctx = canvas.getContext("2d");
    
    // 創建趨勢數據
    const gainers = data.top_gainers?.slice(0, 5) || [];
    const decliners = data.top_decliners?.slice(0, 5) || [];
    
    const labels = [...gainers.map(s => s.name), ...decliners.map(s => s.name)];
    const values = [...gainers.map(s => s.change), ...decliners.map(s => s.change)];
    const colors = values.map(v => v >= 0 ? 'rgba(46, 213, 115, 0.8)' : 'rgba(255, 71, 87, 0.8)');
    
    institutionalTrendChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "法人持股變化 (%)",
          data: values,
          backgroundColor: colors,
          borderColor: colors.map(c => c.replace('0.8', '1')),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            labels: { color: "#eaeaea" }
          }
        },
        scales: {
          x: {
            ticks: { color: "#8b8b9e", maxRotation: 45 },
            grid: { color: "rgba(255,255,255,0.05)" }
          },
          y: {
            title: { display: true, text: "變化百分比 (%)", color: "#8b8b9e" },
            ticks: { color: "#8b8b9e" },
            grid: { color: "rgba(255,255,255,0.05)" }
          }
        }
      }
    });
    
  } catch (error) {
    console.error("Failed to create trend chart:", error);
  }
}

async function createSentimentGauge() {
  const canvas = document.getElementById("sentimentGauge");
  if (!canvas) return;
  
  try {
    const data = await fetchJson("data/ai_analysis/market_sentiment_analysis.json");
    
    if (sentimentGaugeChart) {
      sentimentGaugeChart.destroy();
    }
    
    const ctx = canvas.getContext("2d");
    
    // 情緒分數（-1到1之間）
    const sentimentMapping = { "悲觀": -0.6, "中性": 0, "樂觀": 0.6 };
    const sentimentValue = sentimentMapping[data.overall_sentiment] || 0;
    
    sentimentGaugeChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        datasets: [{
          data: [50 + sentimentValue * 50, 50 - sentimentValue * 50],
          backgroundColor: [
            sentimentValue >= 0 ? 'rgba(46, 213, 115, 0.8)' : 'rgba(255, 71, 87, 0.8)',
            'rgba(139, 139, 158, 0.2)'
          ],
          borderWidth: 0,
          circumference: 180,
          rotation: 270
        }]
      },
      options: {
        responsive: true,
        cutout: '70%',
        plugins: {
          legend: { display: false }
        }
      },
      plugins: [{
        id: 'sentimentText',
        beforeDraw: (chart) => {
          const { ctx, chartArea: { width, height } } = chart;
          ctx.save();
          ctx.fillStyle = '#eaeaea';
          ctx.textAlign = 'center';
          ctx.font = 'bold 16px Arial';
          ctx.fillText(data.overall_sentiment || "中性", width / 2, height - 20);
          ctx.restore();
        }
      }]
    });
    
  } catch (error) {
    console.error("Failed to create sentiment gauge:", error);
  }
}

async function createRecommendationRadarChart() {
  const canvas = document.getElementById("recommendationRadarChart");
  if (!canvas) return;
  
  try {
    const data = await fetchJson("data/ai_analysis/stock_recommendations.json");
    
    if (recommendationRadarChart) {
      recommendationRadarChart.destroy();
    }
    
    const ctx = canvas.getContext("2d");
    
    if (!data.recommendations || data.recommendations.length === 0) {
      ctx.fillStyle = '#8b8b9e';
      ctx.textAlign = 'center';
      ctx.font = '16px Arial';
      ctx.fillText('暫無推薦股票', canvas.width / 2, canvas.height / 2);
      return;
    }
    
    const stock1 = data.recommendations[0];
    const stock2 = data.recommendations[1];
    
    const datasets = [];
    
    if (stock1) {
      datasets.push({
        label: `${stock1.stock_code} ${stock1.stock_name}`,
        data: [
          (stock1.key_metrics?.momentum_score || 0) * 100,
          (stock1.key_metrics?.quality_score || 0) * 100,
          (stock1.key_metrics?.activity_score || 0) * 100,
          (stock1.key_metrics?.current_inst_ratio || 0),
          Math.abs(stock1.key_metrics?.['5d_trend'] || 0) * 10
        ],
        backgroundColor: 'rgba(46, 213, 115, 0.3)',
        borderColor: 'rgba(46, 213, 115, 0.8)',
        borderWidth: 2
      });
    }
    
    if (stock2) {
      datasets.push({
        label: `${stock2.stock_code} ${stock2.stock_name}`,
        data: [
          (stock2.key_metrics?.momentum_score || 0) * 100,
          (stock2.key_metrics?.quality_score || 0) * 100,
          (stock2.key_metrics?.activity_score || 0) * 100,
          (stock2.key_metrics?.current_inst_ratio || 0),
          Math.abs(stock2.key_metrics?.['5d_trend'] || 0) * 10
        ],
        backgroundColor: 'rgba(255, 71, 87, 0.3)',
        borderColor: 'rgba(255, 71, 87, 0.8)',
        borderWidth: 2
      });
    }
    
    recommendationRadarChart = new Chart(ctx, {
      type: "radar",
      data: {
        labels: ["動能評分", "品質評分", "活躍評分", "法人持股%", "趨勢強度"],
        datasets: datasets
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#eaeaea", boxWidth: 12 }
          }
        },
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: { color: "#8b8b9e" },
            grid: { color: "rgba(255,255,255,0.1)" },
            pointLabels: { color: "#eaeaea" }
          }
        }
      }
    });
    
  } catch (error) {
    console.error("Failed to create radar chart:", error);
  }
}

async function createHoldingHeatmap() {
  const container = document.getElementById("holdingHeatmap");
  if (!container) return;
  
  try {
    const data = await fetchJson("data/ai_analysis/trend_analysis_20d.json");
    
    const allStocks = [
      ...(data.top_gainers?.slice(0, 6) || []),
      ...(data.top_decliners?.slice(0, 6) || [])
    ];
    
    if (allStocks.length === 0) {
      container.innerHTML = '<p style="text-align: center; color: #8b8b9e;">暫無持股變化數據</p>';
      return;
    }
    
    let html = `
      <h4>法人持股變化概覽</h4>
      <div class="chart-legend">
        <div class="legend-item">
          <div class="legend-color" style="background: rgba(46, 213, 115, 0.8);"></div>
          <span>增持</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background: rgba(255, 71, 87, 0.8);"></div>
          <span>減持</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background: rgba(139, 139, 158, 0.6);"></div>
          <span>持平</span>
        </div>
      </div>
      <div class="heatmap-grid">
    `;
    
    allStocks.forEach(stock => {
      const change = stock.change || 0;
      const intensity = Math.min(Math.abs(change) / 10, 1); // 歸一化到0-1
      let cellClass = 'neutral';
      
      if (change > 1) cellClass = 'positive';
      else if (change < -1) cellClass = 'negative';
      
      html += `
        <div class="heatmap-cell ${cellClass}" style="opacity: ${0.6 + intensity * 0.4}">
          <div class="heatmap-cell-code">${stock.code}</div>
          <div class="heatmap-cell-name">${stock.name}</div>
          <div class="heatmap-cell-value">${change >= 0 ? '+' : ''}${change.toFixed(1)}%</div>
        </div>
      `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    
  } catch (error) {
    console.error("Failed to create heatmap:", error);
    container.innerHTML = '<p style="text-align: center; color: #ff4757;">熱力圖載入失敗</p>';
  }
}

// ========== Enhanced Broker Functions ==========

let brokerRankingChart = null;

async function loadBrokerSummaryStats() {
  try {
    const [rankingResponse, tradesResponse] = await Promise.all([
      fetchJson("data/broker_ranking.json"),
      fetchJson("data/broker_trades_latest.json")
    ]);

    const rankingData = rankingResponse.data || [];
    const tradesData = tradesResponse.data || [];

    // 計算統計數據
    const totalBrokers = rankingData.length;
    const totalBuyVolume = rankingData.reduce((sum, b) => {
      const netVol = b.total_net_vol || 0;
      return sum + (netVol > 0 ? netVol : 0);
    }, 0);
    const totalSellVolume = rankingData.reduce((sum, b) => {
      const netVol = b.total_net_vol || 0;
      return sum + (netVol < 0 ? Math.abs(netVol) : 0);
    }, 0);
    const targetStocks = new Set(tradesData.map(t => t.stock_code)).size;

    // 更新統計卡片
    document.getElementById('totalBrokers').textContent = totalBrokers;
    document.getElementById('totalBuyVolume').textContent = formatNumber(totalBuyVolume);
    document.getElementById('totalSellVolume').textContent = formatNumber(totalSellVolume);
    document.getElementById('targetStocks').textContent = targetStocks + '檔';

  } catch (error) {
    console.error("Failed to load broker stats:", error);
  }
}

async function createBrokerRankingChart() {
  const canvas = document.getElementById("brokerRankingChart");
  if (!canvas) return;

  try {
    const response = await fetchJson("data/broker_ranking.json");
    const data = response.data || [];
    
    if (brokerRankingChart) {
      brokerRankingChart.destroy();
    }

    const ctx = canvas.getContext("2d");
    
    // 取前10名券商
    const topBrokers = data.slice(0, 10);
    const labels = topBrokers.map(b => (b.broker_name || '').replace(/證券.*/, ''));
    const netValues = topBrokers.map(b => b.total_net_vol || 0);
    const colors = netValues.map(v => v >= 0 ? 'rgba(46, 213, 115, 0.8)' : 'rgba(255, 71, 87, 0.8)');

    brokerRankingChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "淨買賣超 (張)",
          data: netValues,
          backgroundColor: colors,
          borderColor: colors.map(c => c.replace('0.8', '1')),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            labels: { color: "#eaeaea" }
          }
        },
        scales: {
          x: {
            ticks: { color: "#8b8b9e", maxRotation: 45 },
            grid: { color: "rgba(255,255,255,0.05)" }
          },
          y: {
            title: { display: true, text: "淨買賣超 (張)", color: "#8b8b9e" },
            ticks: { 
              color: "#8b8b9e",
              callback: function(value) {
                return formatNumber(value);
              }
            },
            grid: { color: "rgba(255,255,255,0.05)" }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                const value = context.raw;
                return `淨買賣超: ${formatNumber(value)}張`;
              }
            }
          }
        }
      }
    });

  } catch (error) {
    console.error("Failed to create broker ranking chart:", error);
  }
}

async function createBrokerHeatmap() {
  const container = document.getElementById("brokerHeatmap");
  if (!container) return;

  try {
    const response = await fetchJson("data/broker_ranking.json");
    const data = response.data || [];
    
    if (!data || data.length === 0) {
      container.innerHTML = '<p style="text-align: center; color: #8b8b9e;">暫無券商數據</p>';
      return;
    }

    // 取前20名券商創建熱力圖
    const topBrokers = data.slice(0, 20);
    
    let html = `
      <h4>券商交易活躍度分佈</h4>
      <div class="chart-legend">
        <div class="legend-item">
          <div class="legend-color" style="background: rgba(46, 213, 115, 0.8);"></div>
          <span>高活躍度</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background: rgba(255, 193, 7, 0.8);"></div>
          <span>中活躍度</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background: rgba(139, 139, 158, 0.6);"></div>
          <span>低活躍度</span>
        </div>
      </div>
      <div class="broker-heatmap-grid">
    `;

    topBrokers.forEach(broker => {
      const netVolume = broker.total_net_vol || 0;
      const stocksTraded = broker.stocks_traded || 0;
      
      // 根據淨交易量和股票數量決定活躍度
      let activityClass = 'low-activity';
      if (Math.abs(netVolume) > 20000 || stocksTraded > 15) activityClass = 'high-activity';
      else if (Math.abs(netVolume) > 10000 || stocksTraded > 10) activityClass = 'medium-activity';

      const brokerName = (broker.broker_name || '').replace(/證券.*/, '').replace(/台灣/, '');

      html += `
        <div class="broker-heatmap-cell ${activityClass}" title="${broker.broker_name}">
          <div class="broker-name">${brokerName}</div>
          <div class="broker-volume">${formatNumber(Math.abs(netVolume))}張</div>
          <div class="broker-trend">${netVolume >= 0 ? '買超' : '賣超'}</div>
        </div>
      `;
    });

    html += '</div>';
    container.innerHTML = html;

  } catch (error) {
    console.error("Failed to create broker heatmap:", error);
    container.innerHTML = '<p style="text-align: center; color: #ff4757;">券商熱力圖載入失敗</p>';
  }
}

async function loadTargetBrokers() {
  const container = document.getElementById("targetBrokersContent");
  try {
    const response = await fetchJson("data/target_broker_trades.json");
    const data = response.brokers || {};
    
    if (!data || Object.keys(data).length === 0) {
      container.innerHTML = '<p style="text-align: center; color: #8b8b9e;">暫無目標券商數據</p>';
      return;
    }

    let html = "";
    
    Object.entries(data).forEach(([brokerName, trades]) => {
      if (!trades || trades.length === 0) return;
      
      const netVolume = trades.reduce((sum, t) => sum + (t.net_vol || 0), 0);
      const stockCount = new Set(trades.map(t => t.stock_code)).size;
      
      html += `
        <div class="target-broker-card">
          <div class="broker-header">
            <div class="broker-name-display">${brokerName}</div>
            <div class="broker-status ${stockCount > 0 ? 'active' : 'inactive'}">
              ${stockCount > 0 ? '活躍' : '無交易'}
            </div>
          </div>
          
          <div class="broker-metrics">
            <div class="broker-metric">
              <div class="broker-metric-value ${netVolume >= 0 ? 'net-negative' : 'net-positive'}">
                ${formatNumber(Math.abs(netVolume))}
              </div>
              <div class="broker-metric-label">${netVolume >= 0 ? '淨買超' : '淨賣超'}</div>
            </div>
            <div class="broker-metric">
              <div class="broker-metric-value">${stockCount}</div>
              <div class="broker-metric-label">交易股票</div>
            </div>
          </div>
          
          <div class="broker-activity">
            ${trades.slice(0, 3).map(t => 
              `${t.stock_code}: ${t.side === 'buy' ? '買' : '賣'}${formatNumber(Math.abs(t.net_vol || 0))}張`
            ).join(' | ')}
            ${trades.length > 3 ? '...' : ''}
          </div>
        </div>
      `;
    });

    container.innerHTML = html || '<p style="text-align: center; color: #8b8b9e;">暫無目標券商活動</p>';

  } catch (error) {
    console.error("Failed to load target brokers:", error);
    container.innerHTML = '<p style="text-align: center; color: #ff4757;">目標券商載入失敗</p>';
  }
}

async function loadBrokerTrades() {
  const table = document.getElementById("brokerTradesTable");
  const statusDiv = document.getElementById("brokerTradesStatus");
  
  try {
    const response = await fetchJson("data/broker_trades_latest.json");
    const data = response.data || [];
    
    if (!data || data.length === 0) {
      statusDiv.innerHTML = "今日暫無交易數據";
      return;
    }

    // 統計摘要
    const totalTrades = data.length;
    const buyTrades = data.filter(t => t.side === 'buy').length;
    const sellTrades = data.filter(t => t.side === 'sell').length;
    
    statusDiv.innerHTML = `
      今日共 <strong>${totalTrades}</strong> 筆交易 | 
      買超 <span class="net-negative">${buyTrades}</span> 筆 | 
      賣超 <span class="net-positive">${sellTrades}</span> 筆
    `;

    // 填充篩選器
    populateTradeFilters(data);

    // 顯示交易數據
    displayBrokerTradesData(data);

  } catch (error) {
    console.error("Failed to load broker trades:", error);
    statusDiv.innerHTML = "交易數據載入失敗";
  }
}

function populateTradeFilters(data) {
  const stockFilter = document.getElementById("stockFilter");
  const brokerFilter = document.getElementById("brokerFilter");
  
  // 股票選項
  const stocks = [...new Set(data.map(t => t.stock_code))].sort();
  stockFilter.innerHTML = '<option value="ALL">全部股票</option>' + 
    stocks.map(s => `<option value="${s}">${s}</option>`).join('');
  
  // 券商選項
  const brokers = [...new Set(data.map(t => t.broker_name))].sort();
  brokerFilter.innerHTML = '<option value="ALL">全部券商</option>' + 
    brokers.map(b => `<option value="${b}">${b}</option>`).join('');
  
  // 添加事件監聽
  [stockFilter, brokerFilter, document.getElementById("actionFilter")].forEach(filter => {
    filter.addEventListener("change", () => applyTradeFilters(data));
  });
}

function applyTradeFilters(allData) {
  const stockFilter = document.getElementById("stockFilter").value;
  const brokerFilter = document.getElementById("brokerFilter").value;
  const actionFilter = document.getElementById("actionFilter").value;
  
  let filteredData = allData;
  
  if (stockFilter !== "ALL") {
    filteredData = filteredData.filter(t => t.stock_code === stockFilter);
  }
  
  if (brokerFilter !== "ALL") {
    filteredData = filteredData.filter(t => t.broker_name === brokerFilter);
  }
  
  if (actionFilter === "BUY") {
    filteredData = filteredData.filter(t => t.side === 'buy');
  } else if (actionFilter === "SELL") {
    filteredData = filteredData.filter(t => t.side === 'sell');
  }
  
  displayBrokerTradesData(filteredData);
}

function displayBrokerTradesData(data) {
  const tbody = document.querySelector("#brokerTradesTable tbody");
  
  if (data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #8b8b9e;">無符合條件的交易資料</td></tr>';
    return;
  }
  
  tbody.innerHTML = data.map((trade, index) => {
    const netVolume = trade.net_vol || 0;
    const action = trade.side || 'neutral';
    const actionText = action === 'buy' ? '買超' : action === 'sell' ? '賣超' : '持平';
    
    return `
      <tr>
        <td>${index + 1}</td>
        <td><strong>${trade.stock_code}</strong></td>
        <td>${trade.broker_name}</td>
        <td>${formatNumber(trade.buy_vol || 0)}</td>
        <td>${formatNumber(trade.sell_vol || 0)}</td>
        <td class="${netVolume >= 0 ? 'net-negative' : 'net-positive'}">
          ${netVolume >= 0 ? '+' : ''}${formatNumber(netVolume)}
        </td>
        <td>${trade.pct?.toFixed(1) || 'N/A'}%</td>
        <td>
          <span class="broker-action-badge ${action}">${actionText}</span>
        </td>
      </tr>
    `;
  }).join('');
}
