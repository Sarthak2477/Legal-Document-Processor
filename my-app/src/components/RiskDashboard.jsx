"use client";
import React from 'react';

// This is the component that will display the risk analysis results.
// It expects to receive an array of risk objects as a prop.
const RiskDashboard = ({ analysisResults, isLoading }) => {

    const getRiskLevelStyle = (index) => {
        // Simple logic to assign colors. Can be made more sophisticated.
        if (index === 0) return 'border-red-500 bg-red-500/10'; // First risk is highest
        if (index === 1) return 'border-orange-500 bg-orange-500/10'; // Second is medium
        return 'border-yellow-500 bg-yellow-500/10'; // Others are warnings
    };

    if (isLoading) {
        return (
            <div className="text-center p-8">
                <div className="w-12 h-12 border-4 border-dashed border-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-slate-300">Scanning for risks...</p>
            </div>
        );
    }

    if (!analysisResults || analysisResults.length === 0) {
        return (
            <div className="text-center p-8 bg-green-500/10 border border-green-500 rounded-lg">
                <h3 className="text-xl font-bold text-green-400 mb-2">No Significant Risks Found</h3>
                <p className="text-slate-300">Our AI analysis did not detect any high-risk clauses in your document. As always, consider consulting with a legal professional.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="text-center mb-6">
                 <h2 className="text-2xl font-bold text-white">Riskometer Analysis</h2>
                 <p className="text-slate-400">Found {analysisResults.length} potential item(s) to review.</p>
            </div>
            {analysisResults.map((risk, index) => (
                <div key={index} className={`p-4 rounded-lg border ${getRiskLevelStyle(index)}`}>
                    <h4 className="font-bold text-white mb-1">{risk.title}</h4>
                    <p className="text-slate-300 text-sm mb-3">{risk.explanation}</p>
                    <blockquote className="border-l-2 border-slate-600 pl-3 text-xs text-slate-400 italic">
                        "{risk.quote}"
                    </blockquote>
                </div>
            ))}
        </div>
    );
};

export default RiskDashboard;
