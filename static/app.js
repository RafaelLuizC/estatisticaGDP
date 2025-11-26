(() => {
    const raw = window.DATA || {};
    const select = document.getElementById('continentSelect'); // Seleciona os continentes no dropdown.
    const resetBtn = document.getElementById('resetBtn'); // Botão
    function getCtx(id){ const el = document.getElementById(id); return el ? el.getContext('2d') : null; }
    const ctx = getCtx('energyChart'); // Contexto do gráfico.
    const ctx_total = getCtx('chart_total');
    const ctx_avg_elec = getCtx('chart_avg_elec');
    const ctx_avg_gdp = getCtx('chart_avg_gdp');
    const ctx_above90 = getCtx('chart_above90');
    const ctx_minmax = getCtx('chart_minmax');
    const ctx_scatter = getCtx('chart_scatter');
    const info = document.getElementById('info');


    // Lista de continentes disponíveis, ordenados alfabeticamente.
    const continents = Object.keys(raw).filter(k => k !== undefined).sort((a,b)=>{
        if(a === 'All') return -1; if(b==='All') return 1; return a.localeCompare(b);
    });


    // Pega os valores e adiciona ao dropdown.
    function populateSelect(){
        select.innerHTML = '';
        // Para cada continente, cria uma opção de select.
        continents.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c; opt.textContent = c;
            select.appendChild(opt);
        });
    }

    // Os valores da tabela não estão no padrão, essa função recebe o valor e trata ele.
    function fmtNumber(n){
        // Se for null ou undefined, retorna N/A.
        if(n===null || n===undefined) return 'N/A';
        return n.toLocaleString();
    }

    function prepareDataset(continent){
        const list = (raw[continent] || []).slice();
        
        // AQUI SE CONFIGURA DADOS DO GRÁFICO.  
        const MAX = 40; // MAXIMO DE PAÍSES A MOSTRAR NO GRÁFICO
        const limited = list.slice(0, MAX); // 
        const labels = limited.map(x => x.country); 
        const values = limited.map(x => x.electricity == null ? null : +x.electricity); 
        const pibs = limited.map(x => x.pib);
        return { labels, values, pibs }; // RETORNA OS DADOS PREPARADOS
    }

    // Agrega dados de todos os continentes para os gráficos adicionais
    function prepareAggregates(){
        const continents = Object.keys(raw).filter(k => k !== 'All');
        const out = {
            continents: [],
            counts: [],
            avgElec: [],
            avgGdp: [],
            pctAbove90: [],
            minVals: [],
            minCountries: [],
            maxVals: [],
            maxCountries: [],
            scatterPoints: []
        };


        // Adiciona os dados agregados por continente, , computando médias, min/max, etc.
        // Nessa função, faço os cálculos necessários para os gráficos.

        continents.forEach(c => {
            const list = raw[c] || [];

            // Cálculos estatísticos
            // Valores válidos de eletricidade
            const validElec = list.map(x => x.electricity).filter(v => v !== null && v !== undefined && !isNaN(v)); 
            // Filtra valores válidos de PIB
            const validGdp = list.map(x => x.pib).filter(v => v !== null && v !== undefined && !isNaN(v));

            // Contagem de países.
            const count = list.length;
            // Valores médios de eletricidade e PIB
            const avgElec = validElec.length ? (validElec.reduce((a,b)=>a+b,0)/validElec.length) : null;
            const avgGdp = validGdp.length ? (validGdp.reduce((a,b)=>a+b,0)/validGdp.length) : null;
            // Percentual acima de 90%
            const above90 = list.filter(x => x.electricity !== null && x.electricity !== undefined && x.electricity > 90).length;
            const pct = count ? Math.round((above90 / count)*100) : 0; // Percentual arredondado.

            // min / max
            let minVal = null, minCountry = null, maxVal = null, maxCountry = null;
            list.forEach(it => {
                const v = it.electricity;
                if(v === null || v === undefined || isNaN(v)) return;
                if(minVal === null || v < minVal){ minVal = v; minCountry = it.country; }
                if(maxVal === null || v > maxVal){ maxVal = v; maxCountry = it.country; }
            });

            out.continents.push(c); 
            out.counts.push(count);
            out.avgElec.push(avgElec === null ? null : +avgElec.toFixed(2));
            out.avgGdp.push(avgGdp === null ? null : +Math.round(avgGdp));
            out.pctAbove90.push(pct);
            out.minVals.push(minVal);
            out.minCountries.push(minCountry);
            out.maxVals.push(maxVal);
            out.maxCountries.push(maxCountry);

            // Gráfico de pontos (scatter): inclui todos os países com ambos os valores
            list.forEach(it => {
                try{
                    const pibNum = Number(it.pib);
                    const elecNum = Number(it.electricity);
                    // exigir PIB numérico e maior que zero (escala log), e eletricidade numérica
                    if(!isFinite(pibNum) || pibNum <= 0) return;
                    if(!isFinite(elecNum)) return;
                    // raio da bolha baseado no PIB (log) para evitar bolhas gigantes
                    const r = Math.max(3, Math.min(12, Math.round(Math.log10(pibNum + 1))));
                    out.scatterPoints.push({ x: pibNum, y: +elecNum, label: it.country, continent: c, r: r });
                }catch(e){
                    // ignore malformed entries
                }
            });
        });

        return out;
    }

    // palette simples por continente
    const continentColors = [ '#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc949','#b07aa1' ];

    function colorForContinent(idx){ return continentColors[idx % continentColors.length]; }

    function colorForValue(v){
        if(v === null || v === undefined) return 'rgba(200,200,200,0.6)';
        const pct = Math.max(0, Math.min(100, v));
        // Do azul para um cinza mais fraquinho
        const a = 0.6; // Configuração de transparencia da cor
        const r = Math.round(30 + (100 - pct) * 1.2); // Round para evitar bugs.
        const g = Math.round(120 + pct * 0.5);
        const b = Math.round(200 + pct * 0.5); // Isso serve para criar um gradiente de cor de acordo com a quantidade de eletricidade.
        return `rgba(${r},${g},${b},${a})`; // Retorna a cor baseada no valor
    }

    let chart = null;

    // Renderiza o grafico.
    function render(continent){
        // Recebe os dados preparados pela função prepareDataset, e cria o gráfico.
        const {labels, values, pibs} = prepareDataset(continent); 
        // Recebe as cores: se filtrado por continente, usa cor consistente por continente;
        // se 'All', usa gradiente por valor como fallback
        const contIndex = continents.indexOf(continent);
        let bg;
        if(continent && continent !== 'All' && contIndex >= 0){
            const ccolor = colorForContinent(contIndex);
            bg = labels.map(()=> ccolor);
        } else {
            bg = values.map(v => colorForValue(v));
        }
        // Monta o dataset para o "Chart.js" a.k.a Grafico
        const data = {
            labels,
            datasets: [{
                label: `${continent} — Percentual de eletrificação`,
                data: values,
                backgroundColor: bg,
                borderRadius: 6,
                barPercentage: 0.9,
                categoryPercentage: 0.85
            }]
        };

        // Legenda: v = eletrificação, pib = PIB, idx = índice do país.
        // Configurações do gráfico
        const options = {
            responsive: true, // Responsivo
            maintainAspectRatio: false, // Não mantém a proporção
            plugins: {
                legend: { display: true, position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(ctx){
                            const v = ctx.raw; // Valor de eletrificação 
                            const idx = ctx.dataIndex;
                            const pib = pibs[idx];
                            const pibStr = pib == null ? 'N/A' : fmtNumber(pib);
                            return [`Eletrificação: ${v === null ? 'N/A' : v}%`, `PIB: ${pibStr} Milhões`]; // Se for null, mostra N/A.
                        }
                    }
                }
            },
            scales: {
                x: { ticks: { maxRotation: 90, minRotation: 45 }, grid: { display: false } },
                y: { beginAtZero: true }
            }
        };

        // Final do grafico, apresentando o total de paises que estão sendo apresentados.
        if(!ctx){ console.warn('Canvas energyChart não encontrado — pulando render principal'); return; }
        if(chart){ chart.destroy(); }
        chart = new Chart(ctx, { type: 'bar', data, options });
        info.textContent = `Mostrando ${labels.length} países — continente: ${continent}`;
    }

    let chart_total=null, chart_avg_elec=null, chart_avg_gdp=null, chart_above90=null, chart_minmax=null, chart_scatter=null;
    // tipos de visualização controláveis pelo usuário
    let above90ChartType = 'bar';
    let avgGdpChartType = 'bar';

    // botões de toggle (puxados do DOM quando existentes)
    const above90BtnBar = document.getElementById('above90_btn_bar');
    const above90BtnPie = document.getElementById('above90_btn_pie');
    const avggdpBtnBar = document.getElementById('avggdp_btn_bar');
    const avggdpBtnPie = document.getElementById('avggdp_btn_pie');

    function setButtonActive(btn){
        if(!btn) return;
        const group = btn.parentElement;
        if(!group) return;
        group.querySelectorAll('button').forEach(b=>{
            b.classList.remove('btn-secondary');
            b.classList.add('btn-outline-secondary');
        });
        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('btn-secondary');
    }

    // liga eventos dos botões se existirem
    if(above90BtnBar && above90BtnPie){
        above90BtnBar.addEventListener('click', ()=>{ above90ChartType='bar'; setButtonActive(above90BtnBar); renderAggregates(); });
        above90BtnPie.addEventListener('click', ()=>{ above90ChartType='pie'; setButtonActive(above90BtnPie); renderAggregates(); });
        // estado inicial
        setButtonActive(above90BtnBar);
    }
    if(avggdpBtnBar && avggdpBtnPie){
        avggdpBtnBar.addEventListener('click', ()=>{ avgGdpChartType='bar'; setButtonActive(avggdpBtnBar); renderAggregates(); });
        avggdpBtnPie.addEventListener('click', ()=>{ avgGdpChartType='pie'; setButtonActive(avggdpBtnPie); renderAggregates(); });
        setButtonActive(avggdpBtnBar);
    }

    // Função para renderizar os gráficos
    function renderAggregates(){
        const agg = prepareAggregates();

        // Gráfico Pizza do total de países por continente.
        if(ctx_total){
            if(chart_total) chart_total.destroy();
            chart_total = new Chart(ctx_total, {
                type: 'pie',
                data: {
                    labels: agg.continents,
                    datasets: [{
                        label: 'Países',
                        data: agg.counts,
                        backgroundColor: agg.continents.map((_,i)=>colorForContinent(i)),
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: true, position: 'right' },
                        tooltip: {
                            callbacks: {
                                label: function(ctx){
                                    const v = ctx.raw || 0;
                                    const lbl = ctx.label || '';
                                    return (lbl || '') + ': ' + v + ' países';
                                }
                            }
                        }
                    }
                }
            });
        }

        // média de eletricidade
        if(ctx_avg_elec){ if(chart_avg_elec) chart_avg_elec.destroy(); chart_avg_elec = new Chart(ctx_avg_elec, { type: 'bar', data: { labels: agg.continents, datasets:[{ label:'Média Eletricidade', data: agg.avgElec, backgroundColor: agg.continents.map((_,i)=>colorForContinent(i)) }] }, options: { responsive:true, plugins:{legend:{display:false}}, scales:{ y:{ beginAtZero:true } } } }); }

        // média de PIB (troca bar/pie via toggle)
        if(ctx_avg_gdp){ if(chart_avg_gdp) chart_avg_gdp.destroy();
            if(avgGdpChartType === 'pie'){
                chart_avg_gdp = new Chart(ctx_avg_gdp, { type: 'pie', data: { labels: agg.continents, datasets:[{ label:'Média PIB', data: agg.avgGdp, backgroundColor: agg.continents.map((_,i)=>colorForContinent(i)), hoverOffset:6 }] }, options: { responsive:true, plugins:{ legend:{ display:true, position:'right' }, tooltip:{ callbacks:{ label:function(ctx){ const v = ctx.raw; return (ctx.label || '') + ': ' + (v==null? 'N/A' : v.toLocaleString()); }}} } } });
            } else {
                chart_avg_gdp = new Chart(ctx_avg_gdp, { type: 'bar', data: { labels: agg.continents, datasets:[{ label:'Média PIB', data: agg.avgGdp, backgroundColor: agg.continents.map((_,i)=>colorForContinent(i)) }] }, options: { responsive:true, plugins:{legend:{display:false}, tooltip:{callbacks:{label:function(ctx){ const v = ctx.raw; return 'PIB médio: ' + (v==null? 'N/A' : v.toLocaleString()); }}}}, scales:{ y:{ beginAtZero:true, ticks:{ callback: function(v){ return v===null? '' : v.toLocaleString(); } } } } } });
            }
        }

        // percentuais acima de 90% (toggle bar/pie)
        if(ctx_above90){ if(chart_above90) chart_above90.destroy();
            if(above90ChartType === 'pie'){
                chart_above90 = new Chart(ctx_above90, { type:'pie', data:{ labels: agg.continents, datasets:[{ label:'% acima de 90', data: agg.pctAbove90, backgroundColor: agg.continents.map((_,i)=>colorForContinent(i)), hoverOffset:6 }] }, options:{ responsive:true, plugins:{ legend:{ display:true, position:'right' }, tooltip:{ callbacks:{ label:function(ctx){ return (ctx.label || '') + ': ' + ctx.raw + '%'; } } } } } });
            } else {
                chart_above90 = new Chart(ctx_above90, { type: 'bar', data: { labels: agg.continents, datasets:[{ label:'% acima de 90', data: agg.pctAbove90, backgroundColor: agg.continents.map((_,i)=>colorForContinent(i)) }] }, options: { responsive:true, plugins:{legend:{display:false}, tooltip:{callbacks:{label:function(ctx){ return ctx.raw + '%'; }}}}, scales:{ y:{ beginAtZero:true, max:100, ticks:{ callback: v => v + '%' } } } } });
            }
        }

        // min / max por continente (dois datasets)
        if(ctx_minmax){ if(chart_minmax) chart_minmax.destroy(); chart_minmax = new Chart(ctx_minmax, { type: 'bar', data: { labels: agg.continents, datasets:[ { label:'Maior', data: agg.maxVals, backgroundColor: agg.continents.map((_,i)=>colorForContinent(i)), countries: agg.maxCountries }, { label:'Menor', data: agg.minVals, backgroundColor: agg.continents.map((_,i)=>'rgba(200,200,200,0.6)'), countries: agg.minCountries } ] }, options: { responsive:true, plugins:{ tooltip:{ callbacks:{ label:function(ctx){ const ds = ctx.dataset; const country = ds.countries && ds.countries[ctx.dataIndex] ? ds.countries[ctx.dataIndex] : ''; return `${ctx.dataset.label}: ${ctx.raw} (${country})`; } } }, legend:{ display:true } }, scales:{ y:{ beginAtZero:true } } } }); }

        // Gráfico de pontos (scatter) PIB x Eletricidade.
        if(ctx_scatter){ if(chart_scatter) chart_scatter.destroy();
            try{
                if(ctx_scatter){
                    if(chart_scatter) chart_scatter.destroy();
                    // group points per continent to color them
                    const byCont = {};
                    agg.scatterPoints.forEach(p => { byCont[p.continent] = byCont[p.continent]||[]; byCont[p.continent].push(p); });
                    const scatterDatasets = Object.keys(byCont).map((c,i)=>({ label: c, data: byCont[c].map(pt=>({x:pt.x,y:pt.y,r:pt.r, label: pt.label})), backgroundColor: colorForContinent(i) }));

                    chart_scatter = new Chart(ctx_scatter, { type: 'bubble', data: { datasets: scatterDatasets }, options: { responsive:true, plugins:{ tooltip:{ callbacks:{ label:function(ctx){ const p = ctx.raw; return `${p.label} — PIB: ${p.x.toLocaleString()} — Eletricidade: ${p.y}`; } } } }, scales:{ x:{ type:'logarithmic', title:{display:true, text:'PIB (log)'} , min: 1 }, y:{ title:{display:true, text:'Acesso à eletricidade (%)'}} } } });
                }
            }catch(err){
                console.error('Falha ao renderizar scatter chart:', err);
            }
        }
    }

    // Eventos.
    select.addEventListener('change', ()=> render(select.value));
    resetBtn.addEventListener('click', ()=>{ select.value = 'África'; render('África'); });

    // Inicializa o modelo.
    populateSelect();
    select.value = 'África';
    // Verifica se Chart está disponível antes de renderizar
    if (typeof Chart === 'undefined'){
        console.error('Chart.js não foi carregado. Verifique a referência ao CDN.');
    } else {
        render('África');
        renderAggregates();
    }

})();
