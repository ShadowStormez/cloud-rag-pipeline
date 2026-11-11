
import { useCallback, useState } from "react";
import SplashScreen from "./components/SplashScreen";
import Sidebar from "./components/Sidebar";
import WelcomeScreen from "./components/WelcomeScreen";
import ChatComposer from "./components/ChatComposer";

import "./components/Logo.css";
import "./components/Layout.css";
import "./components/ChatComposer.css";

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [question, setQuestion] = useState("");
  const [engine, setEngine] = useState("auto");

  const finishSplash = useCallback(() => {
    setShowSplash(false);
  }, []);

  function handleSuggestion(suggestion) {
    setQuestion(suggestion.question);
    setEngine(suggestion.engine);
  }

  function handleNewChat() {
    setQuestion("");
    setEngine("auto");
  }

  function handleSubmit() {
    if (!question.trim()) return;

    // We'll connect this to Azure FastAPI in the next stage.
    console.log("Question:", question);
    console.log("Engine:", engine);
  }

  return (
    <>
      {showSplash && <SplashScreen onComplete={finishSplash} />}

      <div className="app-layout">
        <Sidebar onNewChat={handleNewChat} />

        <div className="main-content">
          <header className="topbar">
            <span className="topbar__breadcrumb">
              Workspace &nbsp; / &nbsp;
              <strong>New conversation</strong>
            </span>
          </header>

          <main className="workspace">
            <WelcomeScreen onSuggestion={handleSuggestion} />

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
