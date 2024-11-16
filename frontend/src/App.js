import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
    const [userInput, setUserInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [isWaitingForResponse, setIsWaitingForResponse] = useState(true);
    const chatWindowRef = useRef(null);
    const wsRef = useRef(null);
    const isConnectedRef = useRef(false);

    const handleSend = () => {
        if (!userInput.trim()) return;

        const message = {
            content: userInput,
            type: 'chat',
        };
        
        if (wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
            setMessages(prevMessages => [
                ...prevMessages,
                { sender: 'User', text: userInput},
            ]);
            setIsWaitingForResponse(true);
        } else {
            console.error('WebSocket is not open');
        }


        setUserInput('');
    };

    useEffect(() => {
        if (isConnectedRef.current) return;
        const ws = new WebSocket('ws://localhost:8000/ws/interview');

        ws.onopen = () => {
            console.log('WebSocket is connected');
            isConnectedRef.current = true;
            setIsWaitingForResponse(false);
        };

        ws.onmessage = (event) => {
            const response = JSON.parse(event.data);
            if(response.type === "connection") return;
            setMessages((prevMessages) => [
                ...prevMessages,
                { sender: 'AI Assitant', text: response.content }
            ]);
            setIsWaitingForResponse(false);
        };
        ws.onclose = () => {
            console.log('WebSocket is closed');
            setIsWaitingForResponse(true);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        wsRef.current = ws;
    }, []);

    useEffect(() => {
        chatWindowRef.current?.scrollTo(0, chatWindowRef.current.scrollHeight);
    }, [messages])

    return (
        <div className="App">
            <h1>Mock Interview Platform</h1>

            <div className="chat-window" ref={chatWindowRef}>
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender.toLowerCase()}`}>
                        <span><strong>{msg.sender}:</strong> {msg.text}</span>
                    </div>
                ))}
            </div>

            <div className="input-area">
                <input
                    type="text"
                    placeholder="Ask your question..."
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                />
                <button 
                    onClick={handleSend}
                    disabled={isWaitingForResponse}
                    style={{
                        backgroundColor: isWaitingForResponse ? 'gray' : '#007bff',
                        cursor: isWaitingForResponse ? 'not-allowed' : 'pointer'
                    }}>
                    {isWaitingForResponse ? 'Waiting...' : 'Send'}
                </button>
            </div>
        </div>
    );
}

export default App;
