from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import logging

router = APIRouter()

@router.websocket("/ws/scenario")
async def websocket_scenario_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("[WebSocket] Conexão de cenário aberta.")
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            
            # Simulando processamento interativo do Monte Carlo
            # Envia vários updates para mostrar a curva se ajustando
            for i in range(1, 6):
                await asyncio.sleep(0.5)
                response = {
                    "progress": i * 20,
                    "npv_mean": 1000000 + (i * 10000),
                    "npv_std": 50000 - (i * 1000),
                    "message": f"Simulando iteração {i * 2000} de 10000..."
                }
                await websocket.send_text(json.dumps(response))
                
            await websocket.send_text(json.dumps({
                "progress": 100,
                "status": "complete",
                "message": "Simulação finalizada."
            }))
    except WebSocketDisconnect:
        logging.info("[WebSocket] Cliente desconectado.")
    except Exception as e:
        logging.error(f"[WebSocket] Erro: {e}")
