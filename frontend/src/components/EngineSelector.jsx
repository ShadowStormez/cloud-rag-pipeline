
import {
  siUnity,
  siUnrealengine,
  siGodotengine,
} from "simple-icons";
import { Zap } from "lucide-react";

const engines = [
  { id: "auto", label: "Auto" },
  { id: "unity", label: "Unity", icon: siUnity },
  { id: "unreal", label: "Unreal", icon: siUnrealengine },
  { id: "godot", label: "Godot", icon: siGodotengine },
];

function EngineIcon({ icon }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d={icon.path} />
    </svg>
  );
}

export default function EngineSelector({ value, onChange }) {
  return (
    <div className="engine-selector" role="group" aria-label="Game engine">
      {engines.map((engine) => (
        <button
          key={engine.id}
          type="button"
          className={`engine-option ${
            value === engine.id ? "engine-option--active" : ""
          }`}
          onClick={() => onChange(engine.id)}
          aria-pressed={value === engine.id}
        >
          {engine.icon ? (
            <EngineIcon icon={engine.icon} />
          ) : (
            <Zap size={16} />
          )}
          <span>{engine.label}</span>
        </button>
      ))}
    </div>
  );
}
