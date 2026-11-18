import { supabase } from "./supabase";

export async function createConversation(title = "New conversation") {
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError) throw authError;
  if (!user) throw new Error("You must sign in to save conversations.");

  const { data, error } = await supabase
    .from("conversations")
    .insert({
      user_id: user.id,
      title,
    })
    .select("id, title, created_at, updated_at")
    .single();

  if (error) throw error;

  return data;
}

export async function saveMessage(conversationId, role, content, sources = []) {
  if (!conversationId) {
    throw new Error("A conversation ID is required.");
  }

  if (!["user", "assistant"].includes(role)) {
    throw new Error("Invalid message role.");
  }

  if (typeof content !== "string" || !content.trim()) {
    throw new Error("Message content cannot be empty.");
  }

  const { data, error } = await supabase
    .from("messages")
    .insert({
      conversation_id: conversationId,
      role,
      content,
      sources: Array.isArray(sources) ? sources : [],
    })
    .select("id, conversation_id, role, content, sources, created_at")
    .single();

  if (error) throw error;

  return data;
}

export async function getConversations() {
  const { data, error } = await supabase
    .from("conversations")
    .select("id, title, created_at, updated_at")
    .order("updated_at", { ascending: false });

  if (error) throw error;

  return data ?? [];
}

export async function getMessages(conversationId) {
  if (!conversationId) {
    throw new Error("A conversation ID is required.");
  }

  const { data, error } = await supabase
    .from("messages")
    .select("id, conversation_id, role, content, sources, created_at")
    .eq("conversation_id", conversationId)
    .order("created_at", { ascending: true })
    .order("id", { ascending: true });

  if (error) throw error;

  return data ?? [];
}
