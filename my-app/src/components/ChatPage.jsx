"use client";

import React, { useState, useCallback } from "react";
import ChatInterface from "./ChatInterface";
import DocumentViewer from "./DocumentViewer";
import ProcessingComponent from "./ProcessingComponent";
import UploadComponent from "./UploadComponent";
import RiskDashboard from "./RiskDashboard"; // Import the new component

const APP_STATE = {
  AWAITING_UPLOAD: "AWAITING_UPLOAD",
  GENERAL_CHAT: "GENERAL_CHAT",
  PROCESSING: "PROCESSING",
  ANALYSIS: "ANALYSIS",
};

// I've renamed the component to ChatPage for clarity
export default function ChatPage({ initialMode }) {
  // Set initial state based on server-side query param
  const [appState, setAppState] = useState(
    initialMode === "upload" ? APP_STATE.AWAITING_UPLOAD : APP_STATE.GENERAL_CHAT
  );
  const [fileName, setFileName] = useState("");
  const [sanitizedDocText, setSanitizedDocText] = useState("");
  const [messages, setMessages] = useState([]);

  // --- States for the Riskometer ---
  const [activeTab, setActiveTab] = useState('document'); 
  const [riskAnalysisResults, setRiskAnalysisResults] = useState(null);
  const [isAnalyzingRisks, setIsAnalyzingRisks] = useState(false);
  // ---

  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    setAppState(APP_STATE.PROCESSING);
    setFileName(file.name);
    // Reset previous analysis when a new file is uploaded
    setRiskAnalysisResults(null);
    setActiveTab('document');

    // Simulate file upload and processing
    setTimeout(() => {
      const simulatedText = `This is the extracted text from "${file.name}".`;
      setSanitizedDocText(simulatedText);
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `Great! Your document "${file.name}" has been processed. You can now ask questions or run a risk analysis.`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setAppState(APP_STATE.ANALYSIS);
    }, 3000);
  }, []);

  // --- Function to trigger the risk analysis ---
  const handleRiskAnalysis = useCallback(async () => {
    setActiveTab('risks'); // Switch to the riskometer tab
    if (riskAnalysisResults) return; // Don't re-run if we already have results

    setIsAnalyzingRisks(true);

    // In a real app, this would call your /chat endpoint with the special "risk analysis" prompt
    await new Promise(resolve => setTimeout(resolve, 2500));

    // Mocked results based on the prompt's expected JSON output
    const mockResults = [
        { title: 'Ambiguous Termination Clause', severity: 'high', explanation: 'The conditions for termination are not clearly defined, which could lead to disputes.', quote: '...termination can occur following a material breach...' },
        { title: 'Unilateral Liability Limit', severity: 'high', explanation: 'This clause significantly limits the liability of one party, which may be unfair.', quote: '...total liability of the Service Provider shall not exceed the total fees paid...' },
        { title: 'Automatic Renewal', severity: 'medium', explanation: 'The contract will automatically renew unless you provide written notice 90 days in advance.', quote: '...this Agreement shall automatically renew for successive one-year terms...' },
        { title: 'Vague Confidentiality Terms', severity: 'low', explanation: 'The definition of "Confidential Information" is broad and could be interpreted widely.', quote: '...all non-public information, whether oral or written...' },
    ];
    setRiskAnalysisResults(mockResults);
    setIsAnalyzingRisks(false);
  }, [sanitizedDocText, riskAnalysisResults]);
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
            {/* Left Panel: Now with Tabs */}
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

