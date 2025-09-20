"use client";
import React from 'react';

const ProcessingComponent = ({ fileName }) => {
    return (
        <div className="flex-grow flex flex-col items-center justify-center text-center transition-opacity duration-500">
            <div className="w-16 h-16 border-4 border-dashed border-blue-500 rounded-full animate-spin mb-6"></div>
            <h2 className="text-3xl font-bold text-white mb-2">Analyzing Your Document...</h2>
            <p className="text-gray-400">{fileName}</p>
            <div className="mt-4 text-sm text-slate-500 max-w-sm">
                Please wait while our AI extracts text, sanitizes it for privacy, and prepares for your questions.
            </div>
        </div>
    );
};

export default ProcessingComponent;
