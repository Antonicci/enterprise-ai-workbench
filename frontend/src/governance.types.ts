export type GovernanceReport = {
  framework: string;
  scope: string;
  identity: {
    mode: string;
    roles: string[];
    permissions: string[];
  };
  limits: {
    requests_per_minute: number;
    max_concurrent_requests: number;
    max_prompt_chars: number;
    max_output_tokens: number;
    ollama_num_ctx: number | null;
    request_timeout_seconds: number;
    scope: string;
  };
  pricing: {
    enabled: boolean;
    model: string | null;
    input_per_million: string | null;
    output_per_million: string | null;
    currency: string;
    scope: string;
  };
  pillars: Pillar[];
};

export type Pillar = {
  name: string;
  status: string;
  evidence: string;
  gap: string;
};

export type LocalModel = {
  name: string;
  download_bytes: number | null;
  parameters: string | null;
  quantization: string | null;
  loaded: boolean;
  loaded_bytes: number | null;
  loaded_vram_bytes: number | null;
  context_length: number | null;
};

export type RuntimeReport = {
  available: boolean;
  reason?: string;
  configured_model: string;
  declared_host: {ram_gb: number | null; vram_gb: number | null};
  models: LocalModel[];
  limitations: string[];
};

export type ApiRequest = (path: string) => Promise<unknown>;
