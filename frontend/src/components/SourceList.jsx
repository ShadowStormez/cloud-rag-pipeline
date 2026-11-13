
import { BookOpen, ExternalLink } from "lucide-react";
import { siUnity, siGodotengine, siUnrealengine } from "simple-icons";
import "./SourceList.css";

const OFFICIAL_HOSTS = {
  unity: "docs.unity.com",
  godot: "docs.godotengine.org",
  unreal: "dev.epicgames.com",
};

function getOfficialSource(source) {
  const metadata = source.metadata ?? {};
  const url = metadata.source_url;

  if (typeof url !== "string") return null;

  try {
    const parsed = new URL(url);

    if (parsed.protocol !== "https:") return null;

    const engine = metadata.source_type?.toLowerCase();

    if (!Object.hasOwn(OFFICIAL_HOSTS, engine)) return null;
    if (parsed.hostname !== OFFICIAL_HOSTS[engine]) return null;

    const path = parsed.pathname.split("/").filter(Boolean);
    const filename = path.at(-1) || "Documentation";

    const title = decodeURIComponent(filename)
      .replace(/\.(html|htm)$/i, "")
      .replace(/[-_]/g, " ");

    return {
      url: parsed.href,
      engine,
      title,
    };
  } catch {
    return null;
  }
}


const ENGINE_ICONS = {
  unity: siUnity,
  godot: siGodotengine,
  unreal: siUnrealengine,
};

function EngineIcon({ engine }) {
  const icon = ENGINE_ICONS[engine];

  if (!icon) return null;

  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d={icon.path} />
    </svg>
  );
}


export default function SourceList({ sources = [] }) {
  const uniqueSources = Array.from(
    new Map(
      sources
        .map(getOfficialSource)
        .filter(Boolean)
        .map((source) => [source.url, source])
    ).values()
  );

  if (!uniqueSources.length) return null;

  return (
    <section className="source-list">
      <div className="source-list__heading">
        <BookOpen size={15} />
        <span>Sources</span>
      </div>

      <div className="source-list__citations">
        {uniqueSources.map((source) => (
          <a
            key={source.url}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`source-list__citation source-list__citation--${source.engine}`}
            title={`Open ${source.engine} documentation: ${source.title}`}
          >
            <EngineIcon engine={source.engine} />
            <span>{source.title}</span>
            <ExternalLink size={12} />
          </a>
        ))}
      </div>
    </section>
  );
}
