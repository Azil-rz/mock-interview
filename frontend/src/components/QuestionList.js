import React from 'react';

function QuestionList({ questions, onQuestionClick }) {
    return (
        <div className="question-list">
            {questions.map((q, index) => (
                <div
                    key={index}
                    className="question-item"
                    onClick={() => onQuestionClick(q)}
                >
                    {q.question}
                </div>
            ))}
        </div>
    );
}

export default QuestionList;
