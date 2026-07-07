import logging
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.config import settings

class AdvisorResponse(BaseModel):
    """
    Corporate Standard Schema: AdvisorResponse
    Garante o parsing estruturado rigoroso da saída do LLM.
    """
    recommendation: str = Field(
        ..., 
        description="Narrativa detalhada e justificada em Markdown gerada pelo Advisor financeiro."
    )

def run_ai_advisor_agent(state: dict) -> dict:
    """
    Corporate Standard Docstring: run_ai_advisor_agent
    AI Investment Advisor Agent com mitigação de alucinação (Structured Parsing).
    Gera uma narrativa detalhada em linguagem natural (português do Brasil) explicando a decisão.
    Compara os ativos com base em liquidez, retorno e volatilidade.
    Se a chave ANTHROPIC_API_KEY estiver disponível, usa a API Claude com Pydantic;
    caso contrário, recorre a um gerador heurístico offline local altamente refinado.
    """
    logging.info("[AI Advisor Agent] Iniciando geração de recomendação estruturada.")
    
    ranking = state.get("ranking", [])
    simulations = state.get("simulations", {})
    query = state.get("query", "Como alocar meu capital?")
    
    if not ranking:
        state["recommendation"] = "Não há dados suficientes sobre ativos para formular uma recomendação."
        return state
        
    api_key = settings.ANTHROPIC_API_KEY
    
    if api_key:
        try:
            logging.info("[AI Advisor Agent] Utilizando Anthropic Claude para a narrativa.")
            from langchain_anthropic import ChatAnthropic
            from langchain_core.messages import SystemMessage, HumanMessage
            
            chat = ChatAnthropic(
                anthropic_api_key=api_key,
                model_name=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            ).with_structured_output(AdvisorResponse)
            
            system_prompt = (
                "Você é o NOVA (Net Asset & Opportunity Valuation Agent), um consultor financeiro de elite "
                "especializado em alocação estratégica de capital para pequenas e médias empresas (SMEs).\n"
                "Sua tarefa é analisar o ranking e os resultados de simulação de Monte Carlo dos ativos sob consideração "
                "e redigir uma recomendação e análise comparativa detalhada, profissional, com tom premium e construtiva, "
                "direcionada ao CFO/proprietário da empresa.\n\n"
                "Regras Obrigatórias:\n"
                "1. Responda estritamente em PORTUGUÊS DO BRASIL (PT-BR).\n"
                "2. Explique detalhadamente a racionalidade econômica de por que o vencedor do ranking foi escolhido em relação aos concorrentes.\n"
                "3. Destaque os trade-offs de liquidez, risco de perda simulado e volatilidade para cada ativo listado.\n"
                "4. Dê um alerta explícito sobre armadilhas de fluxo de caixa e a importância de manter um runway de caixa de segurança na empresa.\n"
                "5. NÃO invente métricas. Use exatamente as taxas, scores, VPLs, TIRs e probabilidades calculadas pelo backend.\n"
                "Responda formatando com markdown limpo, usando negrito, listas e alertas se conveniente para facilitar a leitura."
            )
            
            # Formata os dados quantitativos para o prompt
            formatted_data = {
                "pergunta_do_usuario": query,
                "ranking_MCDA": ranking,
                "detalhes_das_simulacoes_monte_carlo": {
                    str(k): {
                        "asset_name": v["asset_name"],
                        "asset_type": v["asset_type"],
                        "retorno_medio_simulado": f"{v['mean_return']*100:.2f}%",
                        "p10_pessimista": f"{v['p10_return']*100:.2f}%",
                        "p90_otimista": f"{v['p90_return']*100:.2f}%",
                        "probabilidade_de_perda": f"{v['loss_probability']*100:.2f}%",
                        "volatilidade": f"{v['std_dev']*100:.2f}%"
                    } for k, v in simulations.items()
                }
            }
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Aqui estão as métricas e o ranking calculados:\n\n{json.dumps(formatted_data, indent=2)}")
            ]
            
            response = chat.invoke(messages)
            state["recommendation"] = response.recommendation.strip()
            logging.info("[AI Advisor Agent] Narrativa estruturada gerada com sucesso via Claude e Pydantic.")
            return state
            
        except Exception as e:
            logging.error(f"[AI Advisor Agent] Falha ao chamar a API Claude: {e}. Iniciando fallback offline...")
            state["recommendation"] = generate_heuristic_recommendation(ranking, simulations, query)
    else:
        logging.info("[AI Advisor Agent] Chave ANTHROPIC_API_KEY vazia. Iniciando fallback heurístico offline.")
        state["recommendation"] = generate_heuristic_recommendation(ranking, simulations, query)
        
    return state

def generate_heuristic_recommendation(ranking: List[Dict[str, Any]], simulations: Dict[int, Dict[str, Any]], query: str) -> str:
    """
    Corporate Standard Docstring: generate_heuristic_recommendation
    Fallback Offline para o Advisor.
    Gera um relatório financeiro rico e estruturado em PT-BR a partir de lógica heurística,
    garantindo que o usuário receba uma análise profissional mesmo sem chaves de API externas.
    """
    vencedor = ranking[0]
    nome_vencedor = vencedor["name"]
    score_vencedor = vencedor["final_score"]
    tipo_vencedor = vencedor["type"]
    ret_vencedor = vencedor["estimated_annual_return"]
    loss_vencedor = vencedor["loss_probability"]
    
    # Mapeamento estético de tipos de ativos
    type_names = {
        "real_estate": "Imóvel de Aluguel (Real Estate)",
        "fixed_income": "Aplicação em Renda Fixa",
        "equity": "Investimento em Renda Variável (Equities)",
        "project": "Projeto de Expansão Corporativo"
    }
    
    markdown_report = f"""# Relatório de Avaliação e Alocação de Capital — NOVA

**Análise gerada em Modo Local / Fallback Offline**
*Consulta do Usuário:* "{query}"

---

### 🏆 Recomendação Principal

Com base no algoritmo de decisão multicritério (MCDA) e em 1.000 iterações de simulações estatísticas Monte Carlo, a oportunidade recomendada como prioritária para a alocação do seu capital é o ativo **{nome_vencedor}** (tipo: *{type_names.get(tipo_vencedor, tipo_vencedor)}*), obtendo uma pontuação final de **{score_vencedor}/10.00** na matriz de decisão.

---

### 📊 Detalhamento e Comparação do Portfólio

"""

    for idx, asset in enumerate(ranking):
        pos = idx + 1
        med_sim = simulations.get(asset["asset_id"], {})
        p10 = med_sim.get("p10_return", 0.0)
        p90 = med_sim.get("p90_return", 0.0)
        loss_p = med_sim.get("loss_probability", 0.0)
        std_d = med_sim.get("std_dev", 0.0)
        
        # Medalhas visuais
        medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else "▪️"
        
        markdown_report += f"""#### {medal} {pos}º Lugar: {asset['name']} ({type_names.get(asset['type'], asset['type'])})
*   **Pontuação Consolidada (MCDA):** `{asset['final_score']}/10.00`
*   **Retorno Anual Estimado:** `{asset['estimated_annual_return']*100:.2f}%`
*   **Simulação Monte Carlo (Distribuição de Probabilidades):**
    *   *Cenário Pessimista (P10):* `{p10*100:.2f}%`
    *   *Cenário Esperado (P50/Mediana):* `{med_sim.get('p50_return', 0.0)*100:.2f}%`
    *   *Cenário Otimista (P90):* `{p90*100:.2f}%`
    *   *Volatilidade Estimada (Std Dev):* `{std_d*100:.2f}%`
    *   *Probabilidade de Retorno Negativo:* **`{loss_p*100:.2f}%`**
*   **Breakdown de Critérios (0-10):** Retorno: `{asset['score_return']}` | Risco: `{asset['score_risk']}` | Liquidez: `{asset['score_liquidity']}` | Estabilidade: `{asset['score_stability']}`

"""

    # Seções de conselhos estratégicos e trade-offs
    markdown_report += f"""---

### ⚖️ Trade-offs e Fatores de Decisão Estratégica

1. **Liquidez vs. Retorno**: 
   Investimentos como *Imóveis* ou *Projetos Internos* demandam imobilização de caixa por longos períodos (baixa liquidez). Se a sua empresa necessita de capital operacional imediato para cobrir flutuações de mercado de curto prazo, o ativo vencedor pode expor o fluxo de caixa a riscos. Considere manter uma parcela do caixa alocada em Renda Fixa de alta liquidez para emergências.
   
2. **Mitigação do Risco de Perda**:
   As simulações de estresse indicam que o ativo com menor risco de perda na simulação Monte Carlo é aquele que oferece retornos garantidos ou taxas fixas de juros. No caso de projetos operacionais, desvios nos fluxos de caixa de mais de 15% ao ano podem empurrar o Valor Presente Líquido (VPL) para a faixa negativa, reduzindo o valor de mercado gerado pelo projeto.

> [!WARNING]
> **Aviso de Gestão de Risco**:
> Antes de efetuar qualquer aporte de capital de grande porte em ativos de liquidez média/baixa, certifique-se de que a empresa mantém no mínimo **6 a 12 meses** de custos operacionais fixos livres em caixa (runway de segurança), em conformidade com as diretrizes do ecossistema financeiro BP Now.
"""

    return markdown_report
