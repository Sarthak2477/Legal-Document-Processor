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

    // Mock data for presentation
    const mockRisks = [
        {
            title: "High Liability Exposure",
            explanation: "The indemnification clause places unlimited liability on the Company, which could result in significant financial exposure.",
            quote: "The Company shall indemnify and hold harmless the Client from any liability, damages, or costs arising from breach.",
            severity: "High"
        },
        {
            title: "Broad Confidentiality Definition", 
            explanation: "The definition of 'Confidential Information' is very broad and may restrict normal business operations.",
            quote: "any data, document, specification and other information or material, that is delivered or disclosed by UNHCR",
            severity: "Medium"
        },
        {
            title: "Mandatory Arbitration Clause",
            explanation: "Disputes must be resolved through arbitration, limiting legal recourse options and potentially favoring one party.",
            quote: "Any disputes shall be subject to binding arbitration in accordance with UNCITRAL Arbitration Rules",
            severity: "Medium"
        }
    ];

    const displayResults = analysisResults && analysisResults.length > 0 ? analysisResults : mockRisks;

    if (!analysisResults || analysisResults.length === 0) {
        // Show mock data for presentation
    }

    return (
        <div className="space-y-4">
            <div className="text-center mb-6">
                 <h2 className="text-2xl font-bold text-white">Riskometer Analysis</h2>
                 <p className="text-slate-400">Found {displayResults.length} potential item(s) to review.</p>
            </div>
            {displayResults.map((risk, index) => (
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
