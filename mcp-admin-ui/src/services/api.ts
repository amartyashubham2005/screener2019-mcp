const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// const API_BASE_URL = "http://localhost:8000";
// const API_BASE_URL = "https://skylark-climbing-hermit.ngrok-free.app";
// const API_BASE_URL = "https://screener2019-mcp-server.centralus.cloudapp.azure.com";
// const API_BASE_URL = "https://mcp-gw1.jesterbot.com";

console.log("API_BASE_URL", API_BASE_URL);
interface ApiResponse<T = any> {
  data: T;
  status: number;
  ok: boolean;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    return {
      data,
      status: response.status,
      ok: response.ok,
    };
  }

  async get<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  async post<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }
}

export const api = new ApiService(API_BASE_URL);