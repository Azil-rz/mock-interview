import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import categories from './data/categories';

function App() {
    const [userInput, setUserInput] = useState('');
    const [messages, setMessages] = useState([]);
    const chatWindowRef = useRef(null);

    const handleSend = () => {
        if (!userInput.trim()) return;

        const allQuestions = Object.values(categories).flat();
        const match = allQuestions.find(q => userInput.includes(q.question));

        const response = match ? match.answer : '未找到相关答案，请尝试询问其他问题。';

        setMessages(prevMessages => [
            ...prevMessages,
            { sender: 'User', text: userInput },
            { sender: 'AI', text: response }
        ]);

        setUserInput('');
    };

    useEffect(() => {
        chatWindowRef.current?.scrollTo(0, chatWindowRef.current.scrollHeight);
    }, [messages]);

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
                <button onClick={handleSend}>Send</button>
            </div>
        </div>
    );
}

export default App;
