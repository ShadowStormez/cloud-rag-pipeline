
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy } from "lucide-react";
import SourceList from "./SourceList";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Could not copy text:", error);
    }
  }

  return (
    <button
      type="button"
      className="message-copy"
      onClick={handleCopy}
      aria-label="Copy content"
      title="Copy content"
    >
      {copied ? <Check size={15} /> : <Copy size={15} />}
    </button>
  );
}

function CodeBlock({ children, className }) {
  const language = className?.replace("language-", "") || "code";
  const code = String(children).replace(/\n$/, "");

  return (
    <div className="message-code">
      <div className="message-code__header">
        <span>{language}</span>
        <CopyButton text={code} />
      </div>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}

export default function ChatMessage({ role, content, sources = [] }) {
  const isUser = role === "user";

  return (
    <article className={`chat-message chat-message--${role}`}>
      {!isUser && (
        <div className="chat-message__avatar">
          <span className="ludex-mark" aria-label="Ludex">
            <span className="ludex-mark__prompt">&gt;</span>
            <span className="ludex-mark__letter"> l</span>
          </span>
        </div>
      )}

      <div className="chat-message__body">
        {isUser ? (
          <p>{content}</p>
        ) : (
          <>
            <div className="chat-message__markdown">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const text = String(children);

                    if (
                      className?.startsWith("language-") ||
                      text.includes("\n")
                    ) {
                      return (
                        <CodeBlock className={className}>
                          {children}
                        </CodeBlock>
                      );
                    }

                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
            <SourceList sources={sources} />
          </>
        )}
      </div>
    </article>
  );
}
