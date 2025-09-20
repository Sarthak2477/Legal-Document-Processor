import ChatPageContent from "@/components/ChatPage";

export default function AppPage({ searchParams }) {
  const initialMode = searchParams.mode === "upload" ? "upload" : "chat";
  return <ChatPageContent initialMode={initialMode} />;
}
