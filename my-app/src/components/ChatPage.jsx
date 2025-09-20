"use client";

import React, { useState, useCallback, useEffect } from "react";
import ChatInterface from "./ChatInterface";
import DocumentViewer from "./DocumentViewer";
import ProcessingComponent from "./ProcessingComponent";
import UploadComponent from "./UploadComponent";

const APP_STATE = {
  AWAITING_UPLOAD: "AWAITING_UPLOAD",
  GENERAL_CHAT: "GENERAL_CHAT",
  PROCESSING: "PROCESSING",
  ANALYSIS: "ANALYSIS",
};

export default function ChatPageContent({ initialMode }) {
  // set initial state based on server-side query param
  const [appState, setAppState] = useState(
    initialMode === "upload" ? APP_STATE.AWAITING_UPLOAD : APP_STATE.GENERAL_CHAT
  );
  const [fileName, setFileName] = useState("");
  const [sanitizedDocText, setSanitizedDocText] = useState("");
  const [messages, setMessages] = useState([]);

  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    setAppState(APP_STATE.PROCESSING);
    setFileName(file.name);

    setTimeout(() => {
      const simulatedText = `This is the extracted text from "${file.name}".`;
      setSanitizedDocText(simulatedText);
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `Great! Your document "${file.name}" has been processed.`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setAppState(APP_STATE.ANALYSIS);
    }, 3000);
  }, []);

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
          <div className="w-full max-w-4xl h-[90vh] flex flex-col">
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
          <div className="flex flex-col lg:flex-row gap-6 w-full max-w-7xl h-[90vh]">
            <div className="lg:w-2/5 w-full h-full">
              <DocumentViewer
                fileName={fileName}
                sanitizedDocText={sanitizedDocText}
              />
            </div>
            <div className="lg:w-3/5 w-full h-full">
              <ChatInterface
                messages={messages}
                setMessages={setMessages}
                documentLoaded={true}
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
