"use client";
import React from 'react';

const ProcessingComponent = ({ fileName }) => {
    const [currentStep, setCurrentStep] = React.useState(0);
    
    const steps = [
        "📄 Extracting text from document...",
        "🔍 Analyzing contract structure...", 
        "🧠 Generating embeddings...",
        "⚖️ Identifying legal clauses...",
        "✅ Analysis complete!"
    ];
    
    React.useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep(prev => {
                if (prev < steps.length - 1) {
                    return prev + 1;
                }
                return prev;
            });
        }, 1500);
        
        return () => clearInterval(interval);
    }, []);
    
    return (
        <div className="flex-grow flex flex-col items-center justify-center text-center transition-opacity duration-500">
            <div className="w-16 h-16 border-4 border-dashed border-blue-500 rounded-full animate-spin mb-6"></div>
            <h2 className="text-3xl font-bold text-white mb-2">Analyzing Your Document...</h2>
            <p className="text-gray-400 mb-4">{fileName}</p>
            
            <div className="bg-slate-800/50 rounded-lg p-4 max-w-md">
                {steps.map((step, index) => (
                    <div key={index} className={`flex items-center mb-2 transition-all duration-500 ${
                        index <= currentStep ? 'text-green-400' : 'text-slate-500'
                    }`}>
                        <div className={`w-2 h-2 rounded-full mr-3 transition-colors ${
                            index < currentStep ? 'bg-green-400' : 
                            index === currentStep ? 'bg-blue-400 animate-pulse' : 'bg-slate-600'
                        }`}></div>
                        <span className="text-sm">{step}</span>
                    </div>
                ))}
            </div>
            
            <div className="mt-4 text-xs text-slate-500 max-w-sm">
                Using advanced AI to extract insights while maintaining privacy and security.
            </div>
        </div>
    );
};

export default ProcessingComponent;
