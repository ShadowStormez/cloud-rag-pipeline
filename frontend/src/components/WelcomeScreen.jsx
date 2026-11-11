import { ArrowUpRight, Box, Layers, Gamepad2, Code2 } from "lucide-react";

const suggestions = [
  {
    engine: "unity",
    label: "Unity",
    icon: Box,
    question: "How does Rigidbody2D work in Unity?",
  },
  {
    engine: "unreal",
    label: "Unreal Engine",
    icon: Layers,
    question: "What are Actors and Components in Unreal Engine?",
  },
  {
    engine: "godot",
    label: "Godot",
    icon: Gamepad2,
    question: "What does Node2D do in Godot?",
  },
  {
    engine: "auto",
    label: "Architecture",
    icon: Code2,
    question: "How should I structure a game project?",
  },
];

export default function WelcomeScreen({ onSuggestion }) {
  return (
    <div className="welcome">
      <p className="welcome__eyebrow">
        <span>&gt;</span> YOUR NEXT BUILD STARTS HERE
      </p>

      <h1>What are we building today?</h1>

      <p className="welcome__subtitle">
        From the first prototype to the final frame.
        Let's build it together.
      </p>

      <div className="suggestion-grid">
        {suggestions.map((suggestion) => {
          const Icon = suggestion.icon;

          return (
            <button
              key={suggestion.question}
              className="suggestion-card"
              onClick={() => onSuggestion(suggestion)}
            >
              <div className="suggestion-card__engine">
                <Icon size={16} />
                <span>{suggestion.label}</span>
              </div>

              <div className="suggestion-card__bottom">
                <p>{suggestion.question}</p>
                <ArrowUpRight size={18} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}