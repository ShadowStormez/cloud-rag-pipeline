
import { ArrowUp } from "lucide-react";
import EngineSelector from "./EngineSelector";

export default function ChatComposer({
  question,
  onQuestionChange,
  engine,
  onEngineChange,
  onSubmit,
}) {
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <form
      className="chat-composer"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <textarea
        className="chat-composer__input"
        placeholder="Ask Ludex anything about game development..."
        value={question}
        onChange={(event) => onQuestionChange(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
        aria-label="Your question"
      />

      <div className="chat-composer__footer">
        <EngineSelector value={engine} onChange={onEngineChange} />

        <button
          className="chat-composer__send"
          type="submit"
          disabled={!question.trim()}
          aria-label="Send question"
        >
          <ArrowUp size={20} />
        </button>
      </div>
    </form>
  );
}
