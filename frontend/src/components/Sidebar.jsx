import { PanelLeft, Plus, LogIn, LogOut, UserRound } from "lucide-react";
import Logo from "./Logo";

export default function Sidebar({
  onNewChat,
  collapsed,
  onToggle,
  mobileOpen = false,
  conversations = [],
  activeConversationId = null,
  onSelectConversation,
  user,
  authLoading,
  onSignIn,
  onSignOut,
}) {
  const displayName =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "Account";

  const initials = displayName
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("");


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
        <div className="sidebar__account">
          <div className="sidebar__account-avatar" aria-hidden="true">
            {user ? initials : <UserRound size={19} />}
          </div>

          {!collapsed && (
            <div className="sidebar__account-info">
              <span className="sidebar__account-name">
                {authLoading ? "Checking session..." : user ? displayName : "Guest"}
              </span>
              <span className="sidebar__account-detail">
                {user ? "Signed in" : "Temporary chats"}
              </span>
            </div>
          )}

          <button
            type="button"
            className="sidebar__account-action"
            onClick={user ? onSignOut : onSignIn}
            disabled={authLoading}
            title={user ? "Sign out" : "Sign in with Google"}
            aria-label={user ? "Sign out" : "Sign in with Google"}
          >
            {user ? <LogOut size={19} /> : <LogIn size={19} />}
          </button>
        </div>
      </div>
    </aside>
  );
}