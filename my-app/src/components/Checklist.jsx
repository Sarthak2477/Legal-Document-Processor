"use client";
import React from 'react';

const Checklist = ({ checklistData, isLoading }) => {

    if (isLoading) {
        return (
            <div className="text-center p-8 flex flex-col items-center justify-center h-full">
                <div className="w-12 h-12 border-4 border-dashed border-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-slate-300 font-medium">Generating Checklist...</p>
                <p className="text-slate-500 text-sm mt-1">Our AI is identifying your document type.</p>
            </div>
        );
    }

    if (!checklistData) {
        return (
            <div className="text-center p-8 flex flex-col items-center justify-center h-full">
                 <h3 className="text-xl font-bold text-slate-300 mb-2">Generate Your Checklist</h3>
                <p className="text-slate-400 max-w-sm">Click the "Checklist" tab to have our AI create a list of required supporting documents for your specific legal process.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 h-full flex flex-col">
            <div className="text-center flex-shrink-0">
                 <h2 className="text-2xl font-bold text-white">Actionable Checklist</h2>
                 <p className="text-slate-400 text-sm">
                    Based on our analysis, your document appears to be a: 
                    <span className="font-semibold text-blue-400"> {checklistData.documentType}</span>
                 </p>
            </div>

            <div className="flex-grow overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
                <ul className="space-y-3">
                    {checklistData.items.map((item, index) => (
                        <li key={index} className="bg-slate-800/50 p-3 rounded-lg flex items-center transition-all hover:bg-slate-800">
                           <input id={`item-${index}`} type="checkbox" className="h-4 w-4 rounded border-gray-600 text-blue-500 focus:ring-blue-500 cursor-pointer" />
                           <label htmlFor={`item-${index}`} className="ml-3 block text-sm font-medium text-slate-300 cursor-pointer">
                                {item}
                           </label>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};


export default Checklist;

