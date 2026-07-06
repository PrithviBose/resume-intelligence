export type TextChunk = {
  index: number;
  text: string;
  start_char: number;
  end_char: number;
};

export type EmbeddingInfo = {
  resume_id: string;
  model_name: string;
  embedding_dimension: number;
};

export type UserProfile = {
  id: number;
  user_name: string | null;
  email: string | null;
  current_company: string | null;
  years_of_experience: number | null;
};

export type ParseResult = {
  filename: string;
  file_type: string;
  text_length: number;
  full_text: string;
  chunk_count: number;
  chunks: TextChunk[];
  embedding: EmbeddingInfo;
  user: UserProfile;
};

export type SearchHit = {
  chunk_index: number;
  text: string;
  start_char: number;
  end_char: number;
  score: number;
};

export type SearchResult = {
  resume_id: string;
  query: string;
  results: SearchHit[];
};

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: Date;
  chain?: QueryChainTrace;
  sources?: SearchHit[];
};

export type QueryUnderstanding = {
  search_query: string;
  intent: "factual" | "jd_fit" | "summary" | "other";
};

export type QueryEvidence = {
  key_facts: string[];
  matches: string[];
  gaps: string[];
  jd_fit: "strong" | "partial" | "weak" | "unknown" | null;
  insufficient_context: boolean;
};

export type QueryChainTrace = {
  step1_understanding: QueryUnderstanding;
  retrieval_chunk_count: number;
  step2_evidence: QueryEvidence;
};

export type QueryResult = {
  resume_id: string;
  query: string;
  answer: string;
  sources: SearchHit[];
  chain: QueryChainTrace;
};

export type ChatCandidate = {
  resumeId: string;
  userName: string | null;
  email: string | null;
  currentCompany: string | null;
};

export type UserListItem = {
  user_name: string | null;
  email: string | null;
  current_company: string | null;
  resume_id: string;
};

export type UsersListResponse = {
  users: UserListItem[];
};
