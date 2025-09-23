"use client";
import React from 'react';

const ProcessingComponent = ({ fileName }) => {
    
    
    return (
        <div className="flex-grow flex flex-col items-center justify-center text-center transition-opacity duration-500">
            <div className="w-16 h-16 border-4 border-dashed border-blue-500 rounded-full animate-spin mb-6"></div>
            <h2 className="text-3xl font-bold text-white mb-2">Analyzing Your Document...</h2>
            <p className="text-gray-400 mb-4">{fileName}</p>
            
            
            <div className="mt-4 text-xs text-slate-500 max-w-sm">
                Using advanced AI to extract insights while maintaining privacy and security.
            </div>
        </div>
    );
};

export default ProcessingComponent;
