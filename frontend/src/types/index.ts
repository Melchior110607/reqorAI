export interface User {
  id: number;
  email: string;
  company_name: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface Client {
  id: number;
  name: string;
  email: string;
  company: string;
  phone?: string;
  address?: string;
  notes?: string;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export enum RequestStatus {
  PENDING = "pending",
  COMPLETED = "completed",
  OVERDUE = "overdue"
}

export enum RequestType {
  OUTGOING = "outgoing",
  INCOMING = "incoming"
}

export enum RequestPriority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  URGENT = "urgent"
}

export enum ReminderFrequency {
  NEVER = "never",
  DAILY = "daily",
  WEEKLY = "weekly",
  MONTHLY = "monthly"
}

export interface Request {
  id: number;
  title: string;
  description: string;
  status: RequestStatus;
  priority: RequestPriority;
  type: RequestType;
  due_date?: string;
  reminder_frequency: ReminderFrequency;
  email_recipients?: string[];
  attachments?: string[];
  is_priority: boolean;
  client_id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface RequestWithClient extends Request {
  client_name: string;
  client_company: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  company_name: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
