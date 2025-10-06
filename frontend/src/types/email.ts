export enum EmailProvider {
  GMAIL = "gmail",
  OUTLOOK = "outlook"
}

export enum ConnectionStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  ERROR = "error",
  EXPIRED = "expired"
}

export enum EmailClassification {
  RESPONSE_TO_REQUEST = "response_to_request",
  NEW_REQUEST = "new_request",
  CONFIRMATION = "confirmation",
  CLIENT_REMINDER = "client_reminder",
  DISSATISFACTION = "dissatisfaction",
  MIXED = "mixed",
  UNCLASSIFIED = "unclassified"
}

export enum ProcessingStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface EmailConnection {
  id: number;
  user_id: number;
  provider: EmailProvider;
  email_address: string;
  status: ConnectionStatus;
  last_sync?: string;
  created_at: string;
  updated_at: string;
}

export interface InterceptedEmail {
  id: number;
  user_id: number;
  connection_id: number;
  client_id?: number;
  sender_email: string;
  sender_name?: string;
  subject: string;
  body: string;
  attachments?: string[];
  confidence_score: number;
  matched_rule_id?: number;
  rule_type?: string;
  rule_pattern?: string;
  ai_classification: EmailClassification;
  ai_confidence: number;
  ai_reasoning?: string;
  related_request_ids?: number[];
  processing_status: ProcessingStatus;
  processed_at?: string;
  email_received_at: string;
  created_at: string;
  client_name?: string;
  client_company?: string;
}

export interface AuthUrlResponse {
  auth_url: string;
  provider: EmailProvider;
}
