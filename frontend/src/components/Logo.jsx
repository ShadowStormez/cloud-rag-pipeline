export default function Logo({ text = "ludex", className = "" }) {
  return (
    <div className={`ludex-logo ${className}`} aria-label="Ludex">
      <span className="ludex-logo__prompt" aria-hidden="true">
        &gt;
      </span>
      <span className="ludex-logo__text">{text}</span>
    </div>
  );
}