"use client";
import React from 'react';
import ChatPage from '@/components/ChatPage';
import Navbar from '@/components/Navbar';

export default function AppPage({ searchParams }) {
  // Determine the initial mode from URL search parameters. 
  // Defaults to "chat" if the 'mode' param is not "upload".
  const params = React.use(searchParams);
  const initialMode = params?.mode === "upload" ? "upload" : "chat";

  return (
    <div className="relative min-h-screen bg-slate-900" style={{ fontFamily: "'Poppins', sans-serif" }}>
       <Navbar hideLaunchButton={true} />
    
      <main >
        {/* Pass the determined mode to the ChatPage component */}
        <ChatPage initialMode={initialMode} />
      </main>
    </div>
  );
}

