import logging

def generate_pitch_deck_html(asset_data: dict, ai_narrative: str) -> str:
    """
    Gera um relatório HTML simulando um 'Pitch Deck' exportável para investidores.
    """
    logging.info("[Export Engine] Gerando documento de Pitch Deck...")
    
    asset_name = asset_data.get("name", "Ativo Desconhecido")
    current_value = asset_data.get("current_value", 0.0)
    
    html_content = f"""
    <html>
        <head>
            <title>Pitch Deck - {asset_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
                h1 {{ color: #2C3E50; }}
                .highlight {{ background: #E8F8F5; padding: 15px; border-left: 5px solid #1ABC9C; }}
                .narrative {{ margin-top: 20px; font-size: 1.1em; line-height: 1.6; }}
            </style>
        </head>
        <body>
            <h1>Executive Summary: {asset_name}</h1>
            <div class="highlight">
                <h2>Valuation Atual: $ {current_value:,.2f}</h2>
            </div>
            <div class="narrative">
                <h3>Análise e Parecer (AI Advisory):</h3>
                <p>{ai_narrative.replace(chr(10), '<br>')}</p>
            </div>
            <hr>
            <p><small>Gerado automaticamente por NOVA Framework</small></p>
        </body>
    </html>
    """
    
    return html_content
