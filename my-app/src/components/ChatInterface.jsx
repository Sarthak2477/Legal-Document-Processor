"use client";
import React, { useState, useRef, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import apiService from '../services/api';

// 1. UploadComponent import is no longer needed.

const ChatInterface = ({ 
    messages = [], 
    setMessages, 
    documentLoaded = false, 
    sanitizedDocText = '',
    onFileUpload,
    isProcessing = false,
    maxMessageLength = 1000,
    contractId = null
}) => {
    const [userInput, setUserInput] = useState('');
    const [isAiResponding, setIsAiResponding] = useState(false);
    const [uploadError, setUploadError] = useState(null); // 2. State for upload-specific errors
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null); // 3. Ref for the hidden file input

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Clear upload error when user starts typing
    useEffect(() => {
        if (uploadError && userInput.trim()) {
            setUploadError(null);
        }
    }, [userInput, uploadError]);

    // 4. File validation and upload logic is now integrated here
    const handleFileSelected = useCallback((e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validation constants
        const maxFileSize = 10 * 1024 * 1024; // 10MB
        const acceptedTypes = ['.pdf', '.doc', '.docx', '.txt'];

        try {
            // Check file size
            if (file.size > maxFileSize) {
                const maxSizeMB = (maxFileSize / (1024 * 1024)).toFixed(1);
                throw new Error(`File exceeds ${maxSizeMB}MB limit.`);
            }

            // Check file type
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            if (!acceptedTypes.includes(fileExtension)) {
                throw new Error(`Invalid file type. Please use PDF, DOC, DOCX, or TXT.`);
            }

            // If validation passes
            setUploadError(null);
            
            if (onFileUpload) {
                onFileUpload(file);
            }

        } catch (err) {
            console.error('File validation error:', err);
            setUploadError(err.message);
        } finally {
            // Reset file input so the same file can be re-uploaded
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    }, [onFileUpload]);
    
    const handleUploadButtonClick = () => {
        setUploadError(null); // Clear previous errors
        fileInputRef.current.click();
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!userInput.trim() || isAiResponding || isProcessing) return;

        const newMessages = [...messages, { 
            sender: 'user', 
            text: userInput.trim(),
            timestamp: new Date().toISOString()
        }];
        setMessages(newMessages);
        
        const currentQuestion = userInput.trim();
        setUserInput('');
        setIsAiResponding(true);

        try {
            // Try to use the real API first
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rag/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: currentQuestion,
                    contract_id: contractId,
                }),
            });
            
            let aiResponse;
            if (response.ok) {
                const data = await response.json();
                aiResponse = data.answer || 'I received your question but couldn\'t generate a response.';
            } else {
                throw new Error('API request failed');
            }
            
            setMessages([...newMessages, { 
                sender: 'ai', 
                text: aiResponse,
                timestamp: new Date().toISOString()
            }]);
        } catch (error) {
            console.warn('API call failed, using fallback response:', error.message);
            
            // Generate fallback response based on question
            let fallbackResponse = "I'm having trouble connecting to the analysis service right now.";
            
            if (documentLoaded && contractId) {
                if (sanitizedDocText && sanitizedDocText.length > 0) {
                    fallbackResponse = `I can see your document is loaded with ${sanitizedDocText.length} characters of content. Please try asking specific questions about the contract terms, parties, or clauses.`;
                } else {
                    fallbackResponse += " I can see you have a document uploaded, but I'm having trouble accessing its content. Please try re-uploading or ask general questions.";
                }
            } else {
                fallbackResponse += " Please try uploading a document first, or ask general legal questions.";
            }
            
            setMessages([...newMessages, { 
                sender: 'ai', 
                text: fallbackResponse,
                timestamp: new Date().toISOString()
            }]);
        }
        setIsAiResponding(false);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    return (
        <div className="flex flex-col h-full bg-slate-800/40 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 shadow-2xl">
            {/* Messages Area */}
            <div className="flex-grow overflow-y-auto mb-4 pr-2 space-y-4">
                {/* Initial welcome message if chat is empty */}
                {messages.length === 0 && (
                     <div className="flex items-center justify-center h-full text-slate-400 text-center">
                        <div>
                            <div className="text-4xl mb-4">⚖️</div>
                            <p className="text-lg mb-2">Welcome to the Legal AI Assistant</p>
                            <p className="text-sm text-slate-500">Upload a contract to get started or ask general legal questions</p>
                            {!documentLoaded && (
                                <div className="mt-4 space-y-2">
                                    <p className="text-xs text-slate-600">Try asking:</p>
                                    <div className="flex flex-wrap gap-2 justify-center">
                                        <button 
                                            onClick={() => setUserInput('What should I look for in an NDA?')}
                                            className="bg-slate-700/30 hover:bg-slate-700/50 text-slate-400 text-xs px-2 py-1 rounded transition-colors"
                                        >
                                            NDA advice
                                        </button>
                                        <button 
                                            onClick={() => setUserInput('Explain contract liability clauses')}
                                            className="bg-slate-700/30 hover:bg-slate-700/50 text-slate-400 text-xs px-2 py-1 rounded transition-colors"
                                        >
                                            Liability clauses
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`p-3 rounded-lg max-w-lg ${msg.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'}`}>
                           {msg.text}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
            
            {/* Input Area */}
            <div className="flex-shrink-0">
                {/* 5. Upload error display area */}
                {uploadError && (
                    <div className="mb-2 p-2 bg-red-900/50 border border-red-700/50 rounded-lg text-red-300 text-sm text-center">
                        {uploadError}
                    </div>
                )}
                
                {/* Suggestion Chips */}
                {documentLoaded && (
                    <div className="mb-3 flex flex-wrap gap-2">
                        <button 
                            onClick={() => setUserInput('Summarize this contract')}
                            className="bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-sm px-3 py-1 rounded-full transition-colors"
                        >
                            📋 Summarize
                        </button>
                        <button 
                            onClick={() => setUserInput('What are the risks in this contract?')}
                            className="bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-sm px-3 py-1 rounded-full transition-colors"
                        >
                            ⚠️ Find Risks
                        </button>
                        <button 
                            onClick={() => setUserInput('Who are the parties in this contract?')}
                            className="bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-sm px-3 py-1 rounded-full transition-colors"
                        >
                            👥 Parties
                        </button>
                        <button 
                            onClick={() => setUserInput('What are the termination clauses?')}
                            className="bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-sm px-3 py-1 rounded-full transition-colors"
                        >
                            🚪 Termination
                        </button>
                    </div>
                )}

                <form onSubmit={handleSendMessage} className="flex items-end gap-3">
                    {/* 6. The new upload button is here */}
                    <button 
                        type="button"
                        onClick={handleUploadButtonClick}
                        className="flex-shrink-0 bg-slate-700/50 hover:bg-slate-600 text-white font-semibold rounded-lg p-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isAiResponding || isProcessing}
                        aria-label="Upload document"
                        title="Upload document"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                    </button>

                    <textarea
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={documentLoaded ? "Ask about your document..." : "Ask a general legal question..."}
                        className="w-full bg-slate-700/50 border border-slate-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        disabled={isAiResponding || isProcessing}
                        rows="1"
                    />
                    <button 
                        type="submit" 
                        className="bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg p-3 disabled:opacity-50"
                        disabled={isAiResponding || isProcessing || !userInput.trim()}
                        aria-label="Send message"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                    </button>
                </form>
            </div>
            
            {/* Hidden file input that the button triggers */}
            <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileSelected}
                className="hidden"
                accept=".pdf,.doc,.docx,.txt"
            />
        </div>
    );
};

// All prop types are still defined for robust component usage
ChatInterface.propTypes = {
    messages: PropTypes.array,
    setMessages: PropTypes.func.isRequired,
    documentLoaded: PropTypes.bool,
    sanitizedDocText: PropTypes.string,
    onFileUpload: PropTypes.func,
    isProcessing: PropTypes.bool,
    maxMessageLength: PropTypes.number,
    contractId: PropTypes.string
};

export default ChatInterface;