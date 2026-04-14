export interface Paper {
  id: string;
  filename: string;
  title: string | null;
  authors: string[] | null;
  page_count: number | null;
  status: "processing" | "ready" | "error";
  created_at: string;
  chunk_count?: number;
}

export interface Citation {
  chunk_id: string;
  chunk_index: number;
  page_number: number;
  section_heading: string | null;
  snippet: string;
}

export interface QueryRequest {
  paper_id: string;
  question: string;
  conversation_id?: string;
  top_k?: number;
  rerank_top_n?: number;
  llm_provider?: "ollama" | "anthropic" | "openai";
}

export interface QueryResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: Citation[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  paper_id: string;
  created_at: string;
  messages: Message[];
}
