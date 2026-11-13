import { PanelLeft, Plus, Settings } from "lucide-react";
import Logo from "./Logo";

export default function Sidebar({
  onNewChat,
  collapsed,
  onToggle,
  mobileOpen = false,
  conversations = [],
  activeConversationId = null,
  onSelectConversation,
}) {

  return (
    <aside
        className={`sidebar ${collapsed ? "sidebar--collapsed" : ""} ${
          mobileOpen ? "sidebar--mobile-open" : ""
        }`}
      >
      <div className="sidebar__top">
        {!collapsed && <Logo />}

        <button
          className="icon-button"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <PanelLeft size={20} />
        </button>
      </div>

      <button className="new-chat-button" onClick={onNewChat}>
        <Plus size={20} />
        {!collapsed && <span>New chat</span>}
      </button>
  {!collapsed && (
  <div className="sidebar__history">
    <div className="sidebar__history-heading">
      Recent chats
    </div>

    {conversations.length === 0 ? (
      <p className="sidebar__history-empty">
        No conversations yet
      </p>
    ) : (
      <div className="sidebar__history-list">
        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            type="button"
            className={`sidebar__history-item ${
              activeConversationId === conversation.id
                ? "sidebar__history-item--active"
                : ""
            }`}
            onClick={() => onSelectConversation?.(conversation.id)}
            title={conversation.title}
            aria-current={
              activeConversationId === conversation.id
                ? "page"
                : undefined
            }
          >
            <span>{conversation.title}</span>
          </button>
        ))}
      </div>
    )}
  </div>
)}
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