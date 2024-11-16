# coding:utf-8

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
import sys
import os

from starlette.websockets import WebSocketState

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from AI.main import MockInterviewAgent

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        if websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                print("WebSocket connection closed before sending message")
        else:
            print("WebSocket connection is not in CONNECTED state")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

websocket_manager = ConnectionManager()

# WebSocket 端点
@app.websocket("/ws/interview")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)

    response = json.dumps({'status': 0, 'type': "connection", 'message': "connected"})
    await websocket_manager.send_message(response, websocket)

    mockInterviewAgent = MockInterviewAgent()
    mockInterviewAgent.initial_chat()

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)

            if data['type'] == "close":
                await websocket_manager.send_message(json.dumps({'status': 0, 'type': "close", 'message': "connection is closing" }), 
                                                     websocket)
                await websocket_manager.disconnect(websocket)
                break
            else:
                # 将content添加到message列表
                mockInterviewAgent.simulateGroupChat.append({'content': data['content'], 'role': 'user', 'name': 'interviewee'}, mockInterviewAgent.ragUserProxyAgent)
                next_speaker = mockInterviewAgent.next_speaker_selection_func(last_speaker=mockInterviewAgent.ragUserProxyAgent, 
                                                                            simulateGroupChat=mockInterviewAgent.simulateGroupChat)
                while next_speaker is not mockInterviewAgent.ragUserProxyAgent and next_speaker != "auto":
                    # 使用异步回复更新groupchat
                    reply = await next_speaker.a_generate_reply(mockInterviewAgent.simulateGroupChat.messages)
                    print(next_speaker.name, ': ', reply)
                    if next_speaker is not mockInterviewAgent.questionsSelectorAssistantAgent:
                        response = json.dumps({'content': reply, 'type': next_speaker.name})
                        await websocket_manager.send_message(response, websocket)
                    mockInterviewAgent.simulateGroupChat.append({'content':reply, 'role': 'user', 'name': next_speaker.name}, next_speaker)
                    # 通过原有next_speaker_selection_func获取next speaker直到需要用户输入
                    next_speaker = mockInterviewAgent.next_speaker_selection_func(last_speaker=next_speaker, simulateGroupChat=mockInterviewAgent.simulateGroupChat)

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# 启动 FastAPI 应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)