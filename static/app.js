(() => {
    const raw = window.DATA || {};
    const select = document.getElementById('continentSelect'); // Seleciona os continentes no dropdown.
    const resetBtn = document.getElementById('resetBtn'); // Botão
    const ctx = document.getElementById('energyChart').getContext('2d'); // Contexto do gráfico.
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
        // Recebe as cores de acordo com o valor
        const bg = values.map(v => colorForValue(v));
        // Monta o dataset para o "Chart.js" a.k.a Grafico
        const data = {
            labels,
            datasets: [{
                label: 'Percentual de eletrificação (índice)',
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
                legend: { display: false }, // Legenda desativada
                tooltip: {
                    callbacks: {
                        label: function(ctx){
                            const v = ctx.raw; // Valor de eletrificação 
                            const idx = ctx.dataIndex;
                            const pib = pibs[idx];
                            const pibStr = pib == null ? 'N/A' : fmtNumber(pib);
                            return [`Eletrificação: ${v === null ? 'N/A' : v}`, `PIB: ${pibStr}`]; // Se for null, mostra N/A.
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
        if(chart){ chart.destroy(); }
        chart = new Chart(ctx, { type: 'bar', data, options });
        info.textContent = `Mostrando ${labels.length} países — continente: ${continent}`;
    }

    // Eventos.
    select.addEventListener('change', ()=> render(select.value));
    resetBtn.addEventListener('click', ()=>{ select.value = 'All'; render('All'); });

    // Inicializa o modelo.
    populateSelect();
    select.value = 'All';
    render('All');

})();
