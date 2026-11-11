import { useState } from "react";
import { PanelLeft, Plus, Settings } from "lucide-react";
import Logo from "./Logo";

export default function Sidebar({ onNewChat }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`}>
      <div className="sidebar__top">
        {!collapsed && <Logo />}

        <button
          className="icon-button"
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <PanelLeft size={20} />
        </button>
      </div>

      <button className="new-chat-button" onClick={onNewChat}>
        <Plus size={20} />
        {!collapsed && <span>New chat</span>}
      </button>

      <div className="sidebar__spacer" />

      <div className="sidebar__bottom">
        <div className="sidebar__tagline">
          {!collapsed && (
            <>
              <span>YOUR WORKSPACE</span>
              <p>From idea to playable.</p>
            </>
          )}
        </div>

        <button className="sidebar__settings" disabled title="Coming later">
          <Settings size={19} />
          {!collapsed && <span>Settings</span>}
        </button>
      </div>
    </aside>
  );
}