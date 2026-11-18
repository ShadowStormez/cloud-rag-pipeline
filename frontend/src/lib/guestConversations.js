// Temporary guest history: memory only, never persisted.
const guestConversations = new Map();

export function createGuestConversation(title) {
  const conversation = {
    id: crypto.randomUUID(),
    title,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    isGuest: true,
  };

  guestConversations.set(conversation.id, {
    conversation,
    messages: [],
  });

  return conversation;
}

export function saveGuestMessage(conversationId, role, content, sources = []) {
  const entry = guestConversations.get(conversationId);

  if (!entry) {
    throw new Error("Guest conversation not found.");
  }

  const message = {
    id: crypto.randomUUID(),
    conversation_id: conversationId,
    role,
    content,
    sources,
    created_at: new Date().toISOString(),
  };

  entry.messages.push(message);
  entry.conversation.updated_at = message.created_at;

  return message;
}

export function getGuestMessages(conversationId) {
  const entry = guestConversations.get(conversationId);
  return entry ? [...entry.messages] : [];
}

export function clearGuestConversations() {
  guestConversations.clear();
}
