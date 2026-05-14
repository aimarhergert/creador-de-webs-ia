const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_AROS_API_KEY || "";

export type AssetStatus =
  | "pending" | "generating" | "created" | "deploying"
  | "live" | "optimizing" | "scaling" | "killed" | "error";
export type AssetType = "landing_page" | "blog" | "ecommerce" | "lead_gen";
export type MonetizationModel = "affiliates" | "ads" | "ecommerce" | "leads" | "none";

export interface Asset {
  id: number;
  keyword: string;
  type: AssetType;
  url: string | null;
  revenue: number;
  cost: number;
  roi: number;
  status: AssetStatus;
  monetization_model: MonetizationModel;
  market_score: number;
  cpc_estimate: number;
  created_at: string;
  updated_at: string;
}

export interface AssetListOut { total: number; items: Asset[] }

export interface PipelineResponse {
  asset_id?: number;
  task_id?: string;
  status: string;
  message: string;
}

export interface TaskStatus {
  status: "queued" | "running" | "done" | "error";
  pct: number;
  msg?: string;
  step?: string;
  asset_id?: number;
  url?: string;
  result?: { asset_id: number; url: string; status: string; keyword: string };
}

export interface PortfolioSummary {
  total_assets: number;
  total_revenue: number;
  total_cost: number;
  portfolio_roi: number;
}

export interface AssetMetrics {
  asset_id: number;
  total_visits: number;
  total_conversions: number;
  total_revenue: number;
  total_cost: number;
  roi: number;
  days_tracked: number;
}

export interface BillingPlan {
  name: string;
  price_eur: number;
  price_id: string;
}

export interface AuthUser {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  wallet_balance: number;
}

export interface WalletOut {
  id: number;
  balance: number;
  total_deposited: number;
  total_invested: number;
  total_returned: number;
  currency: string;
  roi: number;
  pnl: number;
}

export interface WalletTransaction {
  id: number;
  type: string;
  amount: number;
  balance_after: number;
  description: string | null;
  asset_id: number | null;
  created_at: string;
}

export interface Strategy {
  id: number;
  name: string;
  type: string;
  description: string | null;
  is_preset: boolean;
  is_active: boolean;
  user_id: number | null;
  visits_min: number;
  visits_max: number;
  conversion_rate_min: number;
  conversion_rate_max: number;
  revenue_per_conversion_min: number;
  revenue_per_conversion_max: number;
  scaling_multiplier: number;
  kill_threshold_roi: number;
  scale_threshold_roi: number;
  monthly_budget: number;
  capital_allocation_pct: number;
  color: string | null;
  icon: string | null;
  created_at: string;
}

export interface Sector {
  id: number;
  type: string;
  name: string;
  icon: string;
  description: string | null;
  color: string;
  visits_multiplier: number;
  conversion_multiplier: number;
  avg_cpc: number;
  revenue_multiplier: number;
  is_active: boolean;
}

export interface ScanResult {
  id: number;
  url: string;
  domain: string;
  status_code: number;
  seo_score: number;
  content_score: number;
  word_count: number;
  title: string | null;
  meta_description: string | null;
  title_length: number;
  meta_length: number;
  h1_count: number;
  h2_count: number;
  internal_links: number;
  external_links: number;
  image_count: number;
  images_with_alt: number;
  has_schema: boolean;
  has_og_tags: boolean;
  has_mobile_viewport: boolean;
  load_time_ms: number;
  readability_score: number;
  sentiment: string;
  top_keywords: string | null;
  estimated_traffic: number;
  estimated_cpc: number;
  content_type: string | null;
  ai_insights: string | null;
  recommendations: string | null;
  raw_data?: string | null;
  error: string | null;
  created_at: string;
}

export interface BlogPost {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  content_html: string | null;
  cover_image: string | null;
  category: string | null;
  tags: string | null;
  sector: string | null;
  status: string;
  meta_title: string | null;
  meta_description: string | null;
  focus_keyword: string | null;
  views: number;
  seo_score: number | null;
  asset_id: number | null;
  is_standalone: boolean;
  generated_by: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MarketOpportunity {
  keyword: string;
  sector: string;
  source: string;
  search_volume_est: number;
  competition: string;
  cpc_estimate: number;
  trend_direction: string;
  opportunity_score: number;
  why: string;
  suggested_asset_type: string;
  suggested_monetization: string;
}

export interface MarketReport {
  searched_at: string;
  total_keywords_found: number;
  sectors_analyzed: string[];
  top_opportunities: MarketOpportunity[];
  ai_verdict: string;
  recommended_action: string;
}

export interface AgentRunResult {
  started_at: string;
  keywords_found: number;
  opportunities_analyzed: number;
  assets_created: number;
  blog_posts_created: number;
  errors: string[];
  created_asset_ids: number[];
  top_keyword: string;
  ai_verdict: string;
}

export interface ActivityEvent {
  id: number;
  user_id: number | null;
  asset_id: number | null;
  event_type: string;
  title: string;
  description: string | null;
  data: Record<string, unknown> | null;
  created_at: string;
}

// Token getter — injected from the auth store at call time
let _getToken: (() => string | null) | null = null;
export function setTokenGetter(fn: () => string | null) {
  _getToken = fn;
}

function buildHeaders(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json", ...extra };
  if (API_KEY) h["X-API-Key"] = API_KEY;
  const token = _getToken?.();
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: buildHeaders(),
    ...options,
    ...(options?.headers
      ? { headers: { ...buildHeaders(), ...(options.headers as Record<string, string>) } }
      : {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string; api_key_enabled: boolean }>("/health"),

  // Auth
  register: (email: string, username: string, password: string, full_name?: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, username, password, full_name }),
    }),
  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    return fetch(`${BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Login failed");
      }
      return res.json() as Promise<{ access_token: string; refresh_token: string; token_type: string }>;
    });
  },
  me: () => request<AuthUser>("/api/auth/me"),

  // Wallet
  getWallet: () => request<WalletOut>("/api/wallet"),
  deposit: (amount: number, description?: string) =>
    request<WalletOut>("/api/wallet/deposit", {
      method: "POST",
      body: JSON.stringify({ amount, description }),
    }),
  getTransactions: (limit = 50) =>
    request<WalletTransaction[]>(`/api/wallet/transactions?limit=${limit}`),

  // Activity
  getActivity: (limit = 50, event_type?: string) =>
    request<ActivityEvent[]>(`/api/activity?limit=${limit}${event_type ? `&event_type=${event_type}` : ""}`),

  // Assets
  getAssets: (params?: string) =>
    request<AssetListOut>(`/api/assets${params ? `?${params}` : ""}`),
  getAsset: (id: number) => request<Asset>(`/api/assets/${id}`),
  getAssetFiles: (id: number) =>
    request<Record<string, string>>(`/api/assets/${id}/files`),
  deleteAsset: (id: number) =>
    fetch(`${BASE}/api/assets/${id}`, {
      method: "DELETE",
      headers: buildHeaders(),
    }),

  // Pipeline
  triggerPipeline: (
    keyword: string,
    type: AssetType,
    monetization: MonetizationModel,
    asyncMode = true,
  ) =>
    request<PipelineResponse>("/api/orchestrate/pipeline", {
      method: "POST",
      body: JSON.stringify({ keyword, type, monetization_model: monetization, async_mode: asyncMode }),
    }),
  getTaskStatus: (taskId: string) =>
    request<TaskStatus>(`/api/orchestrate/tasks/${taskId}`),
  optimizePortfolio: () =>
    request("/api/orchestrate/optimize", { method: "POST" }),
  optimizeAsset: (id: number) =>
    request(`/api/orchestrate/optimize/${id}`, { method: "POST" }),

  // Analytics
  getPortfolioSummary: () =>
    request<PortfolioSummary>("/api/analytics/portfolio/summary"),
  getAssetSummary: (id: number) =>
    request<AssetMetrics>(`/api/analytics/${id}/summary`),

  // Strategies
  getStrategies: (includePresets = true, type?: string) =>
    request<{ total: number; items: Strategy[] }>(
      `/api/strategies?include_presets=${includePresets}${type ? `&type=${type}` : ""}`
    ),
  getStrategy: (id: number) => request<Strategy>(`/api/strategies/${id}`),
  createStrategy: (body: Record<string, unknown>) =>
    request<Strategy>("/api/strategies", { method: "POST", body: JSON.stringify(body) }),
  deleteStrategy: (id: number) =>
    fetch(`${BASE}/api/strategies/${id}`, { method: "DELETE", headers: buildHeaders() }),
  seedPresetStrategies: () =>
    request<Strategy[]>("/api/strategies/seed-presets", { method: "POST" }),

  // Sectors
  getSectors: () =>
    request<{ total: number; items: Sector[] }>("/api/sectors"),
  seedSectors: () => request<Sector[]>("/api/sectors/seed", { method: "POST" }),

  // Scanner
  scanUrl: (url: string, deepAnalysis = true) =>
    request<ScanResult>("/api/scanner/analyze", {
      method: "POST",
      body: JSON.stringify({ url, deep_analysis: deepAnalysis }),
    }),
  getScanHistory: (limit = 20) =>
    request<{ total: number; items: ScanResult[] }>(`/api/scanner/history?limit=${limit}`),
  getScan: (id: number) => request<ScanResult>(`/api/scanner/history/${id}`),

  // Blog
  getBlogPosts: (params?: string) =>
    request<{ total: number; items: BlogPost[] }>(`/api/blog${params ? `?${params}` : ""}`),
  getBlogPost: (id: number) => request<BlogPost>(`/api/blog/${id}`),
  createBlogPost: (body: Record<string, unknown>) =>
    request<BlogPost>("/api/blog", { method: "POST", body: JSON.stringify(body) }),
  updateBlogPost: (id: number, body: Record<string, unknown>) =>
    request<BlogPost>(`/api/blog/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteBlogPost: (id: number) =>
    fetch(`${BASE}/api/blog/${id}`, { method: "DELETE", headers: buildHeaders() }),

  // Agent — Autonomous Market Research & Creation
  agentResearch: (sectors?: string, deep = true) =>
    request<MarketReport>(`/api/agent/research?deep=${deep}${sectors ? `&sectors=${sectors}` : ""}`),
  agentRun: (body: { sectors?: string[]; max_assets?: number; dry_run?: boolean }) =>
    request<AgentRunResult>("/api/agent/run", { method: "POST", body: JSON.stringify(body) }),
  agentAnalyzeKeyword: (keyword: string) =>
    request<Record<string, unknown>>(`/api/agent/analyze-keyword?keyword=${encodeURIComponent(keyword)}`),

  // Billing
  getBillingPlans: () =>
    request<{ plans: BillingPlan[] }>("/api/billing/plans"),
  createCheckout: (plan: string, successUrl?: string, cancelUrl?: string) =>
    request<{ session_id: string; url: string }>("/api/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ plan, success_url: successUrl, cancel_url: cancelUrl }),
    }),
};
