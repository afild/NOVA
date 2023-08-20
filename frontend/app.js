// NOVA — Dashboard Controller

let chartReturnsInstance = null;
let chartMonteCarloInstance = null;
let globalAssets = [];
let marketRates = { risk_free_rate: 0.0525, inflation_rate: 0.0300 };

document.addEventListener("DOMContentLoaded", () => {
    initDynamicFields();
    fetchMarketRates();
    fetchAssets();
    
    // Listeners
    document.getElementById("asset-type").addEventListener("change", initDynamicFields);
    document.getElementById("asset-form").addEventListener("submit", createAsset);
    document.getElementById("btn-compare").addEventListener("click", runComparison);
});

// 1. Renderiza campos dinâmicos no formulário de cadastro
function initDynamicFields() {
    const assetType = document.getElementById("asset-type").value;
    const wrapper = document.getElementById("dynamic-fields");
    
    let html = "";
    if (assetType === "real_estate") {
        html = `
            <div class="form-group">
                <label for="monthly_rent">Aluguel Mensal Bruto ($)</label>
                <input type="number" id="monthly_rent" class="form-control" placeholder="Ex: 2500" required min="0">
            </div>
            <div class="form-group">
                <label for="vacancy_rate">Taxa de Vacância Anual (%)</label>
                <input type="number" id="vacancy_rate" class="form-control" placeholder="Ex: 8" value="8" min="0" max="100" step="any">
            </div>
            <div class="form-group">
                <label for="appreciation_rate">Taxa de Valorização Anual (%)</label>
                <input type="number" id="appreciation_rate" class="form-control" placeholder="Ex: 4" value="4" min="0" max="100" step="any">
            </div>
            <div class="form-group">
                <label for="opex_rate">Taxa de Despesas Operacionais OPEX (%)</label>
                <input type="number" id="opex_rate" class="form-control" placeholder="Ex: 35" value="35" min="0" max="100" step="any">
            </div>
            <div class="form-group">
                <label for="noi">NOI Anual ($ - Opcional)</label>
                <input type="number" id="noi" class="form-control" placeholder="Deixe em branco para estimar 65%">
            </div>
            <div class="form-group">
                <label for="down_payment">Capital Próprio (Down Payment) ($)</label>
                <input type="number" id="down_payment" class="form-control" placeholder="Deixe vazio para assumir investimento total">
            </div>
            <div class="form-group">
                <label for="mortgage_payment">Mortgage Mensal ($ - se houver)</label>
                <input type="number" id="mortgage_payment" class="form-control" placeholder="Ex: 900" value="0">
            </div>
        `;
    } else if (assetType === "fixed_income") {
        html = `
            <div class="form-group">
                <label for="nominal_rate">Taxa Nominal de Rendimento Anual (%)</label>
                <input type="number" id="nominal_rate" class="form-control" placeholder="Ex: 11.5" required min="0" step="any">
            </div>
            <div class="form-group">
                <label for="term_days">Prazo do Título (Dias)</label>
                <input type="number" id="term_days" class="form-control" placeholder="Ex: 730" value="730" required min="1">
            </div>
            <div class="form-group" style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
                <input type="checkbox" id="is_exempt" style="width: 18px; height: 18px; cursor: pointer;">
                <label for="is_exempt" style="margin-bottom: 0; cursor: pointer;">Isento de Imposto de Renda? (Ex: LCI/LCA)</label>
            </div>
        `;
    } else if (assetType === "equity") {
        html = `
            <div class="form-group">
                <label for="ticker">Ticker do Ativo (yfinance)</label>
                <input type="text" id="ticker" class="form-control" placeholder="Ex: SPY, IVV, PETR4.SA" required>
            </div>
        `;
    } else if (assetType === "project") {
        html = `
            <div class="form-group">
                <label for="wacc">Taxa de Desconto / WACC (%)</label>
                <input type="number" id="wacc" class="form-control" placeholder="Ex: 12.0" required min="0" step="any">
            </div>
            <div class="form-group">
                <label for="cashflows">Fluxos de Caixa Anuais ($ - Separados por vírgula)</label>
                <input type="text" id="cashflows" class="form-control" placeholder="Ex: 40000, 50000, 60000, 45000" required>
            </div>
        `;
    }
    wrapper.innerHTML = html;
}

// 2. Busca taxas de juros no backend
async function fetchMarketRates() {
    try {
        const res = await fetch("/api/system/market-rates");
        const data = await res.json();
        if (data.status === "success") {
            marketRates = data.rates;
        }
    } catch (err) {
        console.error("Falha ao obter taxas de mercado:", err);
    }
}

// 3. Busca todos os ativos do banco e atualiza a interface
async function fetchAssets() {
    try {
        const res = await fetch("/api/assets");
        const assets = await res.json();
        globalAssets = assets;
        
        updateAssetsList(assets);
        updateKpis(assets);
    } catch (err) {
        console.error("Falha ao obter ativos:", err);
    }
}

// 4. Renderiza lista de ativos
function updateAssetsList(assets) {
    const container = document.getElementById("registered-assets-list");
    if (!assets || assets.length === 0) {
        container.innerHTML = `<p style="text-align: center; color: var(--color-text-muted); font-size: 0.85rem; padding: 10px;">Nenhum ativo cadastrado.</p>`;
        return;
    }
    
    const typeLabels = {
        real_estate: "Imóvel",
        fixed_income: "Renda Fixa",
        equity: "Ações/Equities",
        project: "Projeto"
    };
    
    container.innerHTML = assets.map(asset => `
        <div class="asset-item">
            <div class="asset-item-left">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" class="asset-item-checkbox" data-id="${asset.id}" checked>
                    <span class="asset-item-title">${asset.name}</span>
                </div>
                <span class="asset-item-subtitle">${typeLabels[asset.type]} • Investimento: $${asset.initial_investment.toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
            </div>
            <button class="btn-delete-asset" onclick="deleteAsset(${asset.id})">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
        </div>
    `).join("");
}

// 5. Atualiza KPI Cards superiores
function updateKpis(assets) {
    if (!assets || assets.length === 0) {
        document.getElementById("kpi-portfolio-value").innerText = "$0.00";
        document.getElementById("kpi-portfolio-yield").innerText = "0.00%";
        document.getElementById("kpi-portfolio-risk").innerText = "N/A";
        return;
    }
    
    // Valor total do portfólio
    const totalVal = assets.reduce((sum, a) => sum + a.initial_investment, 0);
    document.getElementById("kpi-portfolio-value").innerText = `$${totalVal.toLocaleString('en-US', {maximumFractionDigits: 0})}`;
    
    // Média de Retorno Estimada (ponderada pelo investimento inicial)
    let totalReturnWeighted = 0.0;
    assets.forEach(a => {
        let ret = 0.08; // fallback
        const m = a.metadata;
        if (a.type === "fixed_income") {
            ret = parseFloat(m.nominal_rate || 0.08) / 100.0;
        } else if (a.type === "real_estate") {
            const noi = parseFloat(m.noi || (m.annual_gross_rent * 0.65 || 0.0));
            ret = a.initial_investment > 0 ? (noi / a.initial_investment) + parseFloat(m.appreciation_rate || 0.04) / 100.0 : 0.08;
        } else if (a.type === "project") {
            ret = 0.12; // estimativa
        }
        totalReturnWeighted += ret * a.initial_investment;
    });
    
    const avgYield = totalReturnWeighted / totalVal;
    document.getElementById("kpi-portfolio-yield").innerText = `${(avgYield * 100).toFixed(2)}%`;
    
    // Score de risco consolidado
    const hasHighRisk = assets.some(a => a.risk_level === "high");
    const hasMedRisk = assets.some(a => a.risk_level === "medium");
    let riskLabel = "Baixo";
    let color = "var(--color-success)";
    if (hasHighRisk) {
        riskLabel = "Alto";
        color = "var(--color-danger)";
    } else if (hasMedRisk) {
        riskLabel = "Médio";
        color = "var(--color-warning)";
    }
    
    const riskEl = document.getElementById("kpi-portfolio-risk");
    riskEl.innerText = riskLabel;
    riskEl.style.background = "none";
    riskEl.style.color = color;
    riskEl.style.webkitTextFillColor = color;
}

// 6. Cadastra um ativo
async function createAsset(e) {
    e.preventDefault();
    
    const name = document.getElementById("asset-name").value.trim();
    const type = document.getElementById("asset-type").value;
    const initial_investment = parseFloat(document.getElementById("asset-investment").value);
    const valInput = document.getElementById("asset-current-value").value;
    const current_value = valInput ? parseFloat(valInput) : initial_investment;
    const liquidity_type = document.getElementById("asset-liquidity").value;
    
    // Coleta metadados com base no tipo
    const metadata = {};
    let risk_level = "medium";
    
    if (type === "real_estate") {
        const monthly_rent = parseFloat(document.getElementById("monthly_rent").value || 0.0);
        metadata.monthly_rent = monthly_rent;
        metadata.annual_gross_rent = monthly_rent * 12.0;
        metadata.vacancy_rate = parseFloat(document.getElementById("vacancy_rate").value || 8.0) / 100.0;
        metadata.appreciation_rate = parseFloat(document.getElementById("appreciation_rate").value || 4.0) / 100.0;
        metadata.opex_rate = parseFloat(document.getElementById("opex_rate").value || 35.0) / 100.0;
        
        const noiVal = document.getElementById("noi").value;
        if (noiVal) metadata.noi = parseFloat(noiVal);
        
        const downP = document.getElementById("down_payment").value;
        metadata.down_payment = downP ? parseFloat(downP) : initial_investment;
        metadata.mortgage_payment = parseFloat(document.getElementById("mortgage_payment").value || 0.0);
        risk_level = "medium";
        
    } else if (type === "fixed_income") {
        metadata.nominal_rate = parseFloat(document.getElementById("nominal_rate").value || 8.0) / 100.0;
        metadata.term_days = parseInt(document.getElementById("term_days").value || 730);
        metadata.is_exempt = document.getElementById("is_exempt").checked;
        risk_level = "low";
        
    } else if (type === "equity") {
        metadata.ticker = document.getElementById("ticker").value.trim().toUpperCase();
        risk_level = "high";
        
    } else if (type === "project") {
        metadata.wacc = parseFloat(document.getElementById("wacc").value || 10.0) / 100.0;
        const cfsStr = document.getElementById("cashflows").value;
        metadata.cashflows = cfsStr.split(",").map(val => parseFloat(val.trim()));
        risk_level = "high";
    }
    
    try {
        const res = await fetch("/api/assets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name,
                type,
                initial_investment,
                current_value,
                liquidity_type,
                risk_level,
                metadata
            })
        });
        
        if (!res.ok) {
            const errData = await res.json();
            alert(`Erro ao cadastrar ativo: ${errData.detail}`);
            return;
        }
        
        // Limpa formulário
        document.getElementById("asset-name").value = "";
        document.getElementById("asset-investment").value = "";
        document.getElementById("asset-current-value").value = "";
        initDynamicFields();
        
        // Recarrega
        fetchAssets();
        
    } catch (err) {
        console.error("Erro no cadastro:", err);
    }
}

// 7. Deleta um ativo
async function deleteAsset(id) {
    if (!confirm("Tem certeza que deseja remover este ativo do portfólio?")) return;
    
    try {
        await fetch(`/api/assets/${id}`, { method: "DELETE" });
        fetchAssets();
    } catch (err) {
        console.error("Erro ao deletar ativo:", err);
    }
}

// 8. Executa a comparação de oportunidades via LangGraph
async function runComparison() {
    const checkboxes = document.querySelectorAll(".asset-item-checkbox:checked");
    const assetIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.id));
    
    if (assetIds.length < 2) {
        alert("Por favor, selecione ao menos 2 ativos para comparação.");
        return;
    }
    
    const queryInput = document.getElementById("compare-query").value.trim();
    const query = queryInput || "Comparar a rentabilidade e riscos sob o ponto de vista da liquidez.";
    
    // Altera exibições na Arena de Decisão
    document.getElementById("arena-welcome-view").style.display = "none";
    document.getElementById("arena-results-view").style.display = "none";
    document.getElementById("arena-loading-view").style.display = "flex";
    
    try {
        const res = await fetch("/api/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query,
                asset_ids: assetIds,
                temporary_assets: []
            })
        });
        
        if (!res.ok) {
            const errData = await res.json();
            alert(`Erro na análise: ${errData.detail}`);
            resetArenaView();
            return;
        }
        
        const results = await res.json();
        renderComparisonResults(results);
        
    } catch (err) {
        console.error("Erro ao rodar comparação:", err);
        alert("Erro de rede. Verifique se o servidor FastAPI está ativo na porta 8006.");
        resetArenaView();
    }
}

function resetArenaView() {
    document.getElementById("arena-loading-view").style.display = "none";
    document.getElementById("arena-welcome-view").style.display = "flex";
}

// 9. Renderiza os resultados quantitativos, qualitativos e gráficos da comparação
function renderComparisonResults(data) {
    document.getElementById("arena-loading-view").style.display = "none";
    document.getElementById("arena-results-view").style.display = "block";
    
    // A. Renderiza a tabela de ranking
    const tbody = document.getElementById("ranking-table-body");
    const typeNames = {
        real_estate: "Imóvel",
        fixed_income: "Renda Fixa",
        equity: "Ações/Equities",
        project: "Projeto"
    };
    
    tbody.innerHTML = data.ranking.map((row, idx) => {
        const rank = idx + 1;
        const isGold = rank === 1;
        return `
            <tr class="${isGold ? 'ranking-row-gold' : ''}">
                <td>${isGold ? '🥇' : rank}</td>
                <td><strong>${row.name}</strong></td>
                <td><span class="badge badge-${row.type}">${typeNames[row.type]}</span></td>
                <td>${row.score_return}/10</td>
                <td>${row.score_risk}/10</td>
                <td>${row.score_liquidity}/10</td>
                <td style="font-weight: 700; color: ${isGold ? 'var(--color-primary)' : '#fff'}">${row.final_score}/10</td>
            </tr>
        `;
    }).join("");
    
    // B. Renderiza a recomendação do Advisor no Terminal Dourado (Markdown parser simplificado)
    document.getElementById("advisor-narrative-content").innerHTML = parseMarkdown(data.recommendation);
    
    // C. Desenha Gráficos interativos via Chart.js
    const labels = data.ranking.map(r => r.name);
    const returnsData = data.ranking.map(r => r.estimated_annual_return * 100.0);
    const lossProbData = data.ranking.map(r => r.loss_probability * 100.0);
    
    drawReturnsChart(labels, returnsData, lossProbData);
    drawMonteCarloChart(data.simulations);
}

// 10. Desenha o gráfico de barras comparativas (Retorno vs Probabilidade de Perda)
function drawReturnsChart(labels, returns, lossProbs) {
    if (chartReturnsInstance) chartReturnsInstance.destroy();
    
    const ctx = document.getElementById("chart-returns").getContext("2d");
    chartReturnsInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Retorno Estimado Anual (%)',
                    data: returns,
                    backgroundColor: 'rgba(212, 175, 55, 0.75)',
                    borderColor: 'rgb(212, 175, 55)',
                    borderWidth: 1.5,
                    borderRadius: 6
                },
                {
                    label: 'Probabilidade de Perda (%)',
                    data: lossProbs,
                    backgroundColor: 'rgba(255, 128, 128, 0.65)',
                    borderColor: 'rgb(255, 128, 128)',
                    borderWidth: 1.5,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { family: 'Inter', size: 10 } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0', font: { family: 'Inter' } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0', font: { family: 'Inter' } }
                }
            }
        }
    });
}

// 11. Desenha o gráfico de probabilidade de Monte Carlo (Curva Bell aproximada)
function drawMonteCarloChart(simulations) {
    if (chartMonteCarloInstance) chartMonteCarloInstance.destroy();
    
    const ctx = document.getElementById("chart-montecarlo").getContext("2d");
    
    // Coleta as distribuições brutas para criar datasets de linha contínua
    const datasets = [];
    const colors = [
        'rgba(190, 90, 50, 1.0)', // ciano
        'rgba(212, 175, 55, 1.0)', // ouro
        'rgba(46, 139, 87, 1.0)',  // verde
        'rgba(255, 127, 80, 1.0)'  // coral
    ];
    
    let colorIdx = 0;
    for (const id in simulations) {
        const sim = simulations[id];
        const rawDist = sim.raw_distribution;
        
        if (!rawDist || rawDist.length === 0) continue;
        
        // Ordena os retornos para desenhar uma distribuição de densidade cumulativa simples ou uma curva de dispersão
        const sorted = [...rawDist].sort((a, b) => a - b);
        
        // Agrupa os valores em 15 intervalos para desenhar histograma em formato de linha
        const binsCount = 15;
        const minVal = sorted[0];
        const maxVal = sorted[sorted.length - 1];
        const step = (maxVal - minVal) / binsCount;
        
        const binLabels = [];
        const binCounts = Array(binsCount).fill(0);
        
        for (let i = 0; i < binsCount; i++) {
            const binStart = minVal + i * step;
            const binEnd = binStart + step;
            binLabels.push(((binStart + binEnd) / 2 * 100).toFixed(1) + "%");
            
            rawDist.forEach(v => {
                if (v >= binStart && v < binEnd) {
                    binCounts[i]++;
                }
            });
        }
        
        datasets.push({
            label: sim.asset_name,
            data: binCounts,
            borderColor: colors[colorIdx % colors.length],
            backgroundColor: colors[colorIdx % colors.length].replace("1.0", "0.08"),
            fill: true,
            tension: 0.4,
            borderWidth: 2
        });
        
        colorIdx++;
    }
    
    // Cria labels baseadas em índices de distribuição normativos
    const defaultLabels = Array(15).fill(0).map((_, i) => `${i + 1}`);
    
    chartMonteCarloInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: defaultLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { family: 'Inter', size: 10 } }
                },
                tooltip: {
                    enabled: false // desativa tooltip indexado para evitar ruídos de labels abstratos
                }
            },
            scales: {
                x: {
                    display: false, // oculta eixo X por ser binning abstrato
                    grid: { display: false }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0', display: false } // oculta escala por ser densidade relativa
                }
            }
        }
    });
}

// 12. Parser Markdown simples e robusto para o terminal dourado
function parseMarkdown(md) {
    if (!md) return "";
    let html = md;
    
    // Substitui títulos #
    html = html.replace(/^#\s+(.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.*?)$/gm, '<h4>$1</h4>');
    html = html.replace(/^###\s+(.*?)$/gm, '<h5 style="color: var(--color-primary); margin-top: 1rem; font-size: 1rem;">$1</h5>');
    
    // Substitui quebras de linha horizontais
    html = html.replace(/^---$/gm, '<hr style="border: 0; border-top: 1px solid rgba(212, 175, 55, 0.2); margin: 1.5rem 0;">');
    
    // Substitui alertas do github > [!WARNING] etc
    html = html.replace(/>\s+\[!WARNING\]\s+([\s\S]*?)(?=\n\n|\n$|$)/g, '<div class="alert-box alert-warning" style="border-left: 4px solid var(--color-warning); background: rgba(255, 224, 102, 0.04); padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 15px 0;"><strong>⚠️ ALERTA DE RISCO:</strong><br>$1</div>');
    
    // Substitui negritos
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/`(.*?)`/g, '<code style="background: rgba(255, 255, 255, 0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.85em; color: var(--color-accent);">$1</code>');
    
    // Substitui listas bullets simples
    html = html.replace(/^\*\s+(.*?)$/gm, '<li>$1</li>');
    html = html.replace(/^\-\s+(.*?)$/gm, '<li>$1</li>');
    // Envolve blocos de <li> em <ul> se não houver
    // Uma aproximação regex simples para formatar listas
    html = html.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
    
    // Converte parágrafos simples
    html = html.split('\n\n').map(p => {
        p = p.trim();
        if (!p) return "";
        if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<div') || p.startsWith('<hr')) return p;
        return `<p>${p}</p>`;
    }).join("");
    
    return html;
}
