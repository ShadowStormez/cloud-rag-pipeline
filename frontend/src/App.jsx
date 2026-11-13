
import { useCallback, useEffect, useState } from "react";
import { signInWithGoogle, signOut } from "./lib/auth";
import { supabase } from "./lib/supabase";
import {
  createConversation,
  saveMessage,
  getConversations,
  getMessages,
} from "./lib/conversations";
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
const [user, setUser] = useState(null);
const [authLoading, setAuthLoading] = useState(true);

useEffect(() => {
  let active = true;

  supabase.auth.getUser().then(({ data, error }) => {
    if (!active) return;

    setUser(error ? null : data.user);
    setAuthLoading(false);
  });

  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((event, session) => {
  if (!active) return;

  if (event === "SIGNED_OUT") {
    requestIdRef.current += 1;
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    setMessages([]);
    setConversations([]);
    setActiveConversationId(null);
    setQuestion("");
    setError("");
    setIsLoading(false);
  }

  setUser(session?.user ?? null);
  setAuthLoading(false);
});

  return () => {
    active = false;
    subscription.unsubscribe();
  };
}, []);

useEffect(() => {
  let active = true;

  if (!user) {
    setConversations([]);
    setActiveConversationId(null);
    return;
  }

  async function loadConversations() {
    try {
      const savedConversations = await getConversations();

      if (active) {
        setConversations(savedConversations);
      }
    } catch (err) {
      if (active) {
        setError(err.message || "Failed to load conversations.");
      }
    }
  }

  loadConversations();

  return () => {
    active = false;
  };
}, [user?.id]);


  const [question, setQuestion] = useState("");
  const [engine, setEngine] = useState("auto");
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
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

  async function handleSelectConversation(conversationId) {
  requestIdRef.current += 1;
  abortControllerRef.current?.abort();
  abortControllerRef.current = null;

  setIsLoading(false);
  setError("");
  setQuestion("");
  setMessages([]);
  setActiveConversationId(conversationId);
  setMobileSidebarOpen(false);

  const requestId = requestIdRef.current;

  try {
    const savedMessages = await getMessages(conversationId);

    if (requestId !== requestIdRef.current) return;

    setMessages(savedMessages);
  } catch (err) {
    if (requestId !== requestIdRef.current) return;

    setError(err.message || "Failed to load conversation.");
  }
}

  function handleNewChat() {
  setActiveConversationId(null);
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

  let conversationId = activeConversationId;

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
    if (!user) {
      throw new Error("Please sign in to save your conversations.");
    }

    if (!conversationId) {
      const newConversation = await createConversation(
        trimmedQuestion.slice(0, 80)
      );

      conversationId = newConversation.id;

      if (requestId !== requestIdRef.current) return;

      setActiveConversationId(conversationId);
      setConversations((previous) => [
        newConversation,
        ...previous,
      ]);
    }
    if (requestId !== requestIdRef.current) return;

      await saveMessage(
        conversationId,
        "user",
        trimmedQuestion
      );

      if (requestId !== requestIdRef.current) return;
    const result = await askLudex(
      trimmedQuestion,
      selectedEngine,
      controller.signal
    );

    if (requestId !== requestIdRef.current) return;

    const assistantMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: result.answer,
      sources: result.sources,
    };

    // Display the answer immediately.
    setMessages((previous) => [
      ...previous,
      assistantMessage,
    ]);

    // Persist the answer and its documentation citations.
try {
  await saveMessage(
    conversationId,
    "assistant",
    result.answer,
    result.sources
  );
} catch (saveError) {
  if (requestId !== requestIdRef.current) return;

  setError(
    "The AI response was generated, but it could not be saved. " +
    "Copy the answer before refreshing or leaving this conversation."
  );

  console.error("Failed to save assistant response:", saveError);
}
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

async function handleGoogleSignIn() {
  try {
    setError("");
    await signInWithGoogle();
  } catch (err) {
    setError(err.message || "Google sign-in failed.");
  }
}

async function handleSignOut() {
  try {
    setError("");
    await signOut();
    handleNewChat();
  } catch (err) {
    setError(err.message || "Sign-out failed.");
  }
}
  return (
    <>
      {showSplash && <SplashScreen onComplete={finishSplash} />}

      <div className="app-layout">
        <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
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
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              {authLoading ? (
                <span>Checking session...</span>
              ) : user ? (
                <>
                  <span style={{ fontSize: "13px" }}>
                    {user.email}
                  </span>
                  <button
                    type="button"
                    onClick={handleSignOut}
                    style={{
                      padding: "9px 16px",
                      borderRadius: "12px",
                      border: "1px solid #D9541E",
                      background: "transparent",
                      color: "#D9541E",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  style={{
                    padding: "9px 16px",
                    borderRadius: "12px",
                    border: "1px solid #D9541E",
                    background: "#D9541E",
                    color: "#fff",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Sign in with Google
                </button>
              )}
            </div>
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
