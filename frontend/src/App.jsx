
import { useCallback, useState } from "react";
import { useRef } from "react";
import { askLudex } from "./api/rag";
import SplashScreen from "./components/SplashScreen";
import Sidebar from "./components/Sidebar";
import WelcomeScreen from "./components/WelcomeScreen";
import ChatComposer from "./components/ChatComposer";
import ChatMessage from "./components/ChatMessage";
import "./components/ChatMessage.css";

import "./components/Logo.css";
import "./components/Layout.css";
import "./components/ChatComposer.css";

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [question, setQuestion] = useState("");
  const [engine, setEngine] = useState("auto");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const abortControllerRef = useRef(null);
  const requestIdRef = useRef(0);

  const finishSplash = useCallback(() => {
    setShowSplash(false);
  }, []);

  function handleSuggestion(suggestion) {
    setQuestion(suggestion.question);
    setEngine(suggestion.engine);
  }

  function handleNewChat() {
  requestIdRef.current += 1;
  abortControllerRef.current?.abort();
  abortControllerRef.current = null;

  setQuestion("");
  setEngine("auto");
  setMessages([]);
  setError("");
  setIsLoading(false);
}


async function handleSubmit() {
  const trimmedQuestion = question.trim();

  if (!trimmedQuestion || isLoading) return;

  const selectedEngine = engine;
  const requestId = ++requestIdRef.current;
  const controller = new AbortController();

  abortControllerRef.current = controller;

  setMessages((previous) => [
    ...previous,
    {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmedQuestion,
    },
  ]);

  setQuestion("");
  setError("");
  setIsLoading(true);

  try {
    const result = await askLudex(
      trimmedQuestion,
      selectedEngine,
      controller.signal
    );

    if (requestId !== requestIdRef.current) return;

    setMessages((previous) => [
      ...previous,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.answer,
        sources: result.sources,
      },
    ]);
  } catch (err) {
    if (requestId !== requestIdRef.current) return;

    if (err.name !== "AbortError") {
      setError(err.message || "Something went wrong. Please try again.");
    }
  } finally {
    if (requestId === requestIdRef.current) {
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }
}


  return (
    <>
      {showSplash && <SplashScreen onComplete={finishSplash} />}

      <div className="app-layout">
        <Sidebar
          onNewChat={() => {
            handleNewChat();
            setMobileSidebarOpen(false);
          }}
          collapsed={sidebarCollapsed}
          onToggle={() => {
            if (window.matchMedia("(max-width: 768px)").matches) {
              setMobileSidebarOpen(false);
            } else {
              setSidebarCollapsed((previous) => !previous);
            }
          }}
          mobileOpen={mobileSidebarOpen}
        />
        {mobileSidebarOpen && (
          <button
            type="button"
            className="sidebar-backdrop"
            aria-label="Close sidebar"
            onClick={() => setMobileSidebarOpen(false)}
          />
        )}
        <div className="main-content">
          <header className="topbar">
            <nav className="topbar__breadcrumb" aria-label="Breadcrumb">
              <button
                type="button"
                className="topbar__workspace-button"
                onClick={() => {
                  if (window.matchMedia("(max-width: 768px)").matches) {
                    setMobileSidebarOpen(true);
                  } else {
                    setSidebarCollapsed(false);
                  }
                }}
                aria-label="Open workspace sidebar"
              >
                Workspace
              </button>
              <span aria-hidden="true"> / </span>
              <strong>New conversation</strong>
            </nav>
          </header>

          <main className="workspace">
            {messages.length === 0 ? (
              <WelcomeScreen onSuggestion={handleSuggestion} />
            ) : (
              <section className="conversation" aria-label="Conversation">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    sources={message.sources}
                  />
                ))}
                {isLoading && (
                  <div className="ludex-loading" role="status">
                    <span className="ludex-loading__dot" />
                    <span className="ludex-loading__dot" />
                    <span className="ludex-loading__dot" />
                    <span>Ludex is thinking...</span>
                  </div>
                )}
              </section>
            )}

            {error && (
              <div className="ludex-error" role="alert">
                {error}
              </div>
            )}
            <div className="composer-container">
              <ChatComposer
                question={question}
                onQuestionChange={setQuestion}
                engine={engine}
                onEngineChange={setEngine}
                onSubmit={handleSubmit}
              />

              <div className="composer-hint">
                <span>Enter to send · Shift + Enter for a new line</span>
                <span>AI can make mistakes. Verify what you ship.</span>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}
