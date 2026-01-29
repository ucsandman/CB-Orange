/**
 * API client for Sportsbeams Pipeline backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8765'

export interface Prospect {
  id: string
  name: string
  venue_type: string
  state: string
  city?: string
  classification?: string
  conference?: string
  stadium_name?: string
  seating_capacity?: number
  current_lighting_type?: string
  current_lighting_age_years?: number
  status: string
  tier?: string
  icp_score?: number
  constraint_hypothesis?: string
  value_proposition?: string
  created_at: string
  updated_at: string
}

export interface Contact {
  id: string
  prospect_id: string
  name: string
  title?: string
  role?: string
  email?: string
  phone?: string
  is_primary: boolean
  created_at: string
  updated_at: string
}

export interface Activity {
  id: string
  prospect_id: string
  type: string
  description?: string
  agent_id?: string
  created_at: string
}

export interface AgentHealth {
  agent_name: string
  status: string
  last_run_at?: string
  last_run_status?: string
  runs_last_24h: number
  errors_last_24h: number
}

export interface PipelineStats {
  total_prospects: number
  by_status: Record<string, number>
  by_tier: Record<string, number>
}

export interface ProspectScore {
  id: string
  prospect_id: string
  dimension: string
  score: number
  weight: number
  notes?: string
  scored_at: string
}

interface APIResponse<T> {
  success: boolean
  data: T
  error?: string
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(error.detail || error.error || 'API request failed')
  }

  const json: APIResponse<T> = await res.json()
  return json.data
}

export const api = {
  // Prospects
  async getProspects(params?: {
    status?: string
    tier?: string
    state?: string
    search?: string
    limit?: number
    offset?: number
  }): Promise<{ prospects: Prospect[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.set(key, String(value))
      })
    }
    return fetchAPI(`/api/v1/prospects?${searchParams}`)
  },

  async getProspect(id: string): Promise<Prospect & { contacts: Contact[]; scores: ProspectScore[] }> {
    return fetchAPI(`/api/v1/prospects/${id}`)
  },

  async getProspectStats(): Promise<PipelineStats> {
    return fetchAPI('/api/v1/prospects/stats')
  },

  async updateProspect(id: string, updates: Partial<Prospect>): Promise<Prospect> {
    return fetchAPI(`/api/v1/prospects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  },

  // Contacts
  async getContacts(prospectId?: string): Promise<{ contacts: Contact[] }> {
    const params = prospectId ? `?prospect_id=${prospectId}` : ''
    return fetchAPI(`/api/v1/contacts${params}`)
  },

  // Activities
  async getRecentActivities(limit = 20): Promise<Activity[]> {
    const data = await fetchAPI<Activity[]>(`/api/v1/activities/recent?limit=${limit}`)
    return data
  },

  // Agents
  async getAgentHealth(): Promise<AgentHealth[]> {
    return fetchAPI('/api/v1/agents/health')
  },

  async triggerAgent(agentName: string): Promise<{ message: string; run_id: string }> {
    return fetchAPI(`/api/v1/agents/${agentName}/trigger`, {
      method: 'POST',
    })
  },

  // Outreach
  async getPendingApprovals(): Promise<any[]> {
    return fetchAPI('/api/v1/outreach/pending-approvals')
  },

  async approveSequence(sequenceId: string, approvedBy: string): Promise<void> {
    return fetchAPI(`/api/v1/outreach/sequences/${sequenceId}/approve?approved_by=${approvedBy}`, {
      method: 'POST',
    })
  },
}
