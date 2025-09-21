"use client";

import React, { useState, useCallback, useEffect } from "react";
import ChatInterface from "./ChatInterface";
import DocumentViewer from "./DocumentViewer";
import ProcessingComponent from "./ProcessingComponent";
import UploadComponent from "./UploadComponent";
import RiskDashboard from "./RiskDashboard";
import Checklist from "./Checklist"; // Import the new component

const APP_STATE = {
  AWAITING_UPLOAD: "AWAITING_UPLOAD",
  GENERAL_CHAT: "GENERAL_CHAT",
  PROCESSING: "PROCESSING",
  ANALYSIS: "ANALYSIS",
};

export default function ChatPage({ initialMode }) {
  const [appState, setAppState] = useState(
    initialMode === "upload" ? APP_STATE.AWAITING_UPLOAD : APP_STATE.GENERAL_CHAT
  );
  const [fileName, setFileName] = useState("");
  const [sanitizedDocText, setSanitizedDocText] = useState("");
  const [messages, setMessages] = useState([]);
  const [activeTab, setActiveTab] = useState('document'); 
  const [riskAnalysisResults, setRiskAnalysisResults] = useState(null);
  const [isAnalyzingRisks, setIsAnalyzingRisks] = useState(false);

  // --- New states for Checklist ---
  const [checklistData, setChecklistData] = useState(null);
  const [isGeneratingChecklist, setIsGeneratingChecklist] = useState(false);
  // ---

  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    setAppState(APP_STATE.PROCESSING);
    setFileName(file.name);
    // Reset all previous analysis when a new file is uploaded
    setRiskAnalysisResults(null);
    setChecklistData(null);
    setActiveTab('document');

    // Simulate file upload and processing
    setTimeout(() => {
      // Set mock document content
      const simulatedText = `NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT

This NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT ("Agreement") is made by and between:

(i) the Office of the United Nations High Commissioner for Refugees, having its headquarters located at 94 rue de Montbrillant, 1202 Geneva, Switzerland (hereinafter "UNHCR" or the "Discloser"); and

(ii) TechCorp Solutions Inc., a company established in accordance with the laws of Delaware and having its principal offices located at 123 Business Ave, San Francisco, CA 94105 (hereinafter the "Bidder" or the "Recipient").

6. INDEMNIFICATION
The Recipient agrees to indemnify UNHCR in respect of any expenses, losses, damages, costs, claims or liability UNHCR may suffer or incur as a result of an act or omission by the Recipient.

8. TERM AND TERMINATION
This Agreement shall enter into force on the date it is signed by both Parties. Either Party may terminate by providing written notice.

[AI EXTRACTED METADATA]
Document Type: Non-Disclosure Agreement
Parties: UNHCR, TechCorp Solutions Inc.
Jurisdiction: International/Delaware
Risk Level: Medium-High
Key Terms: Confidentiality, Indemnification, Termination`;
      setSanitizedDocText(simulatedText);
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `✅ Successfully processed "${file.name}"! I've extracted the text and identified key legal clauses. You can now view the document, analyze risks, or ask me questions about the contract.`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setAppState(APP_STATE.ANALYSIS);
    }, 3000);
  }, []);

  const handleRiskAnalysis = useCallback(async () => {
    setActiveTab('risks');
    if (riskAnalysisResults) return;
    setIsAnalyzingRisks(true);
    await new Promise(resolve => setTimeout(resolve, 2500));
    const mockResults = [
        { title: 'Ambiguous Termination Clause', severity: 'high', explanation: 'The conditions for termination are not clearly defined, which could lead to disputes.', quote: '...termination can occur following a material breach...' },
        { title: 'Unilateral Liability Limit', severity: 'high', explanation: 'This clause significantly limits the liability of one party, which may be unfair.', quote: '...total liability of the Service Provider shall not exceed the total fees paid...' },
        { title: 'Automatic Renewal', severity: 'medium', explanation: 'The contract will auto-renew unless you provide notice 90 days in advance.', quote: '...this Agreement shall automatically renew for successive one-year terms...' },
        { title: 'Vague Confidentiality Terms', severity: 'low', explanation: 'The definition of "Confidential Information" is broad and could be interpreted widely.', quote: '...all non-public information, whether oral or written...' },
    ];
    setRiskAnalysisResults(mockResults);
    setIsAnalyzingRisks(false);
  }, [sanitizedDocText, riskAnalysisResults]);

  // --- New function to handle checklist generation ---
  const handleGenerateChecklist = useCallback(async () => {
    setActiveTab('checklist');
    if (checklistData) return;
    setIsGeneratingChecklist(true);

    // In a real app, this would be a two-step AI call: 1. Classify doc, 2. Generate list
    await new Promise(resolve => setTimeout(resolve, 2000));

    const mockChecklist = {
        documentType: "Residential Lease Agreement",
        items: [
            "Copy of Tenant's Government-Issued ID (e.g., Aadhaar, Passport)",
            "Proof of Income (e.g., recent salary slips, bank statements)",
            "References from previous landlords",
            "Signed copy of the rental application form",
            "Security deposit payment confirmation",
        ]
    };
    setChecklistData(mockChecklist);
    setIsGeneratingChecklist(false);
  }, [sanitizedDocText, checklistData]);
  // ---

  const renderCurrentView = () => {
    switch (appState) {
      case APP_STATE.AWAITING_UPLOAD:
        return (
          <div className="w-full max-w-4xl h-[90vh] flex flex-col items-center justify-center">
            <UploadComponent onFileUpload={handleFileUpload} />
          </div>
        );

      case APP_STATE.GENERAL_CHAT:
        return (
          <div className="w-full max-w-4xl h-[85vh] flex flex-col">
            <ChatInterface
              messages={messages}
              setMessages={setMessages}
              documentLoaded={false}
              onFileUpload={handleFileUpload}
            />
          </div>
        );

      case APP_STATE.PROCESSING:
        return <ProcessingComponent fileName={fileName} />;

      case APP_STATE.ANALYSIS:
        return (
          <div className="flex flex-col lg:flex-row gap-6 w-full max-w-7xl h-[85vh] pt-5">
            {/* Left Panel: Now with all three Tabs */}
            <div className="lg:w-2/5 w-full h-full flex flex-col bg-slate-800/40 rounded-xl border border-slate-700/50 p-6">
                <div className="flex-shrink-0 mb-4 border-b border-slate-700">
                    <div className="flex space-x-4">
                        <button 
                            onClick={() => setActiveTab('document')}
                            className={`py-2 px-4 text-sm font-medium transition-colors ${activeTab === 'document' ? 'text-white border-b-2 border-blue-500' : 'text-slate-400 hover:text-white'}`}
                        >
                            Document
                        </button>
                        <button 
                            onClick={handleRiskAnalysis}
                            className={`py-2 px-4 text-sm font-medium transition-colors ${activeTab === 'risks' ? 'text-white border-b-2 border-blue-500' : 'text-slate-400 hover:text-white'}`}
                        >
                            Riskometer
                        </button>
                        <button 
                            onClick={handleGenerateChecklist}
                            className={`py-2 px-4 text-sm font-medium transition-colors ${activeTab === 'checklist' ? 'text-white border-b-2 border-blue-500' : 'text-slate-400 hover:text-white'}`}
                        >
                            Checklist
                        </button>
                    </div>
                </div>
                <div className="flex-grow overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
                    {activeTab === 'document' && (
                         <DocumentViewer
                            fileName={fileName}
                            sanitizedDocText={sanitizedDocText}
                        />
                    )}
                    {activeTab === 'risks' && (
                        <RiskDashboard 
                            analysisResults={riskAnalysisResults}
                            isLoading={isAnalyzingRisks}
                        />
                    )}
                    {activeTab === 'checklist' && (
                        <Checklist
                            checklistData={checklistData}
                            isLoading={isGeneratingChecklist}
                        />
                    )}
                </div>
            </div>
            
            {/* Right Panel: Chat Interface */}
            <div className="lg:w-3/5 w-full h-full">
              <ChatInterface
                messages={messages}
                setMessages={setMessages}
                documentLoaded={true}
                sanitizedDocText={sanitizedDocText}
                onFileUpload={handleFileUpload}
              />
            </div>
          </div>
        );

      default:
        return <div className="text-white">Loading...</div>;
    }
  };

  return (
    <div className="flex justify-center items-center w-full min-h-screen bg-slate-900 p-4">
      {renderCurrentView()}
    </div>
  );
}

