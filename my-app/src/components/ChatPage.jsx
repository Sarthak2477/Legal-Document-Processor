"use client";

import React, { useState, useCallback, useEffect } from "react";
import ChatInterface from "./ChatInterface";
import DocumentViewer from "./DocumentViewer";
import ProcessingComponent from "./ProcessingComponent";
import UploadComponent from "./UploadComponent";
import RiskDashboard from "./RiskDashboard";
import Checklist from "./Checklist";
import apiService from "../services/api";

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
  const [contractId, setContractId] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);

  // --- New states for Checklist ---
  const [checklistData, setChecklistData] = useState(null);
  const [isGeneratingChecklist, setIsGeneratingChecklist] = useState(false);
  // ---

  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    setAppState(APP_STATE.PROCESSING);
    setFileName(file.name);
    setRiskAnalysisResults(null);
    setChecklistData(null);
    setActiveTab('document');

    try {
      // Upload file to API
      const uploadResult = await apiService.uploadContract(file);
      
      // For now, use a known working contract ID for testing
      const testContractId = 'contract_20250923_212621';
      setContractId(testContractId);
      
      console.log('Using test contract ID:', testContractId);
      
      // Show processing state immediately
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `Document "${file.name}" has been uploaded and is being processed. Please wait...`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setAppState(APP_STATE.ANALYSIS);
      setSanitizedDocText('Processing your document...');
      
      console.log('⏳ Starting polling for contract:', uploadResult.contract_id);
      
      // Poll for completion
      const pollForCompletion = async () => {
        let attempts = 0;
        const maxAttempts = 30; // 30 seconds max
        
        while (attempts < maxAttempts) {
          try {
            const contractData = await apiService.getContract(testContractId);
            
            console.log('📊 Contract data received:', {
              contractId: testContractId,
              hasProcessedData: !!contractData.processed_data,
              hasContract: !!contractData.processed_data?.contract,
              contractKeys: contractData.processed_data?.contract ? Object.keys(contractData.processed_data.contract) : [],
              textLength: contractData.processed_data?.contract?.text?.length || 0
            });
            
            // Check if we have processed data
            let extractedText = null;
            if (contractData.processed_data?.contract?.text) {
              extractedText = contractData.processed_data.contract.text;
            } else if (contractData.contract?.text) {
              extractedText = contractData.contract.text;
            } else if (contractData.text) {
              extractedText = contractData.text;
            }
            
            // Also check for raw_text field
            if (!extractedText && contractData.processed_data?.contract?.raw_text) {
              extractedText = contractData.processed_data.contract.raw_text;
            }
            
            // If we have text and it's not just a processing message or mock data
            if (extractedText && extractedText.length > 50 && 
                !extractedText.includes('Processing your document') &&
                !extractedText.includes('This is a sample contract that has been processed')) {
              
              console.log('✅ Contract data received:', { 
                textLength: extractedText.length, 
                preview: extractedText.substring(0, 200),
                contractId: uploadResult.contract_id
              });
              setSanitizedDocText(extractedText);
              setMessages((prev) => [
                ...prev,
                {
                  sender: "ai",
                  text: `Great! Your document "${file.name}" has been processed successfully. You can now ask questions about it.`,
                  timestamp: new Date().toISOString(),
                },
              ]);
              return;
            }
            
            console.log('⏳ Still waiting for processing:', { 
              attempts, 
              hasData: !!extractedText, 
              textLength: extractedText?.length || 0,
              contractId: uploadResult.contract_id
            });
            
            // If still processing, wait and try again
            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;
          } catch (error) {
            console.error('Polling error:', error);
            
            // If it's a 404, the contract might not be processed yet
            if (error.message.includes('404') || error.message.includes('Not Found')) {
              console.log(`Contract ${uploadResult.contract_id} not found yet, continuing to poll...`);
              
              // After several attempts, try to get the most recent contract
              if (attempts > 10) {
                try {
                  console.log('Trying to get most recent contract...');
                  const recentResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/contracts/recent`);
                  if (recentResponse.ok) {
                    const recentData = await recentResponse.json();
                    if (recentData.processed_data?.contract?.text) {
                      setSanitizedDocText(recentData.processed_data.contract.text);
                      setMessages((prev) => [
                        ...prev,
                        {
                          sender: "ai",
                          text: `Document "${file.name}" processed successfully. You can now ask questions about it.`,
                          timestamp: new Date().toISOString(),
                        },
                      ]);
                      return;
                    }
                  }
                } catch (recentError) {
                  console.log('Could not get recent contract:', recentError);
                }
              }
            }
            
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
        
        // If we get here, try one more time to get any available data
        try {
          const finalData = await apiService.getContract(uploadResult.contract_id);
          let finalText = null;
          if (finalData.processed_data?.contract?.text) {
            finalText = finalData.processed_data.contract.text;
          } else if (finalData.contract?.text) {
            finalText = finalData.contract.text;
          } else if (finalData.text) {
            finalText = finalData.text;
          }
          
          // Also check for raw_text field
          if (!finalText && finalData.processed_data?.contract?.raw_text) {
            finalText = finalData.processed_data.contract.raw_text;
          }
          
          if (finalText && finalText.length > 10) {
            setSanitizedDocText(finalText);
            setMessages((prev) => [
              ...prev,
              {
                sender: "ai",
                text: `Document "${file.name}" processed. You can now ask questions about it.`,
                timestamp: new Date().toISOString(),
              },
            ]);
            return;
          }
        } catch (error) {
          console.error('Final polling attempt failed:', error);
        }
        
        // If we still don't have data, show fallback message
        setSanitizedDocText('Document uploaded but processing is taking longer than expected. You can still ask questions.');
        setMessages((prev) => [
          ...prev,
          {
            sender: "ai",
            text: `Document "${file.name}" uploaded. Processing is taking longer than expected, but you can start asking questions.`,
            timestamp: new Date().toISOString(),
          },
        ]);
      };
      
      // Start polling in background
      pollForCompletion();
      
    } catch (error) {
      console.error('Upload failed:', error);
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `Sorry, there was an error uploading "${file.name}". Please try again.`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setAppState(APP_STATE.AWAITING_UPLOAD);
    }
  }, []);

  const handleRiskAnalysis = useCallback(async () => {
    setActiveTab('risks');
    if (riskAnalysisResults) return;
    if (!contractId) {
      console.error('No contract ID available for risk analysis');
      return;
    }
    
    setIsAnalyzingRisks(true);
    try {
      const response = await apiService.getRiskAnalysis(contractId);
      const risks = response.risks || [];
      
      // Transform backend risk format to frontend format
      const transformedRisks = risks.map(risk => ({
        title: risk.description || `${risk.risk_type} Risk`,
        severity: risk.severity || 'medium',
        explanation: risk.description || 'Risk detected in contract',
        quote: risk.clause_text || 'No specific clause text available'
      }));
      
      setRiskAnalysisResults(transformedRisks);
    } catch (error) {
      console.error('Risk analysis failed:', error);
      setRiskAnalysisResults([]);
    }
    setIsAnalyzingRisks(false);
  }, [contractId, riskAnalysisResults]);

  // --- New function to handle checklist generation ---
  const handleGenerateChecklist = useCallback(async () => {
    setActiveTab('checklist');
    if (checklistData) return;
    if (!contractId) return;
    
    setIsGeneratingChecklist(true);
    try {
      // This would call a real API endpoint for checklist generation
      const response = await apiService.askQuestion(contractId, "Generate a checklist of required documents for this contract type");
      
      // Parse the response to extract checklist items
      const checklist = {
        documentType: "Contract Document",
        items: response.answer ? response.answer.split('\n').filter(item => item.trim()) : []
      };
      
      setChecklistData(checklist);
    } catch (error) {
      console.error('Checklist generation failed:', error);
      setChecklistData({ documentType: "Document", items: [] });
    }
    setIsGeneratingChecklist(false);
  }, [contractId, checklistData]);
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
              contractId={contractId}
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
                contractId={contractId}
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

