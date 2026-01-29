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
  address?: string
  classification?: string
  conference?: string
  enrollment?: number
  primary_sport?: string
  stadium_name?: string
  seating_capacity?: number
  current_lighting_type?: string
  current_lighting_age_years?: number
  has_night_games?: boolean
  broadcast_requirements?: string
  status: string
  tier?: string
  icp_score?: number
  constraint_hypothesis?: string
  value_proposition?: string
  research_notes?: string
  estimated_project_timeline?: string
  budget_cycle_month?: number
  source?: string
  source_url?: string
  source_date?: string
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
  linkedin_url?: string
  is_primary: boolean
  last_contacted_at?: string
  last_response_at?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface Activity {
  id: string
  prospect_id: string
  type: string
  description?: string
  agent_id?: string
  metadata?: Record<string, unknown>
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

  async getProspect(id: string): Promise<Prospect & { contacts: Contact[]; scores: ProspectScore[]; recent_activities: Activity[] }> {
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
  async getContacts(prospectId?: string): Promise<Contact[]> {
    const params = prospectId ? `?prospect_id=${prospectId}` : ''
    return fetchAPI(`/api/v1/contacts${params}`)
  },

  async createContact(contact: Omit<Contact, 'id' | 'created_at' | 'updated_at'>): Promise<Contact> {
    return fetchAPI('/api/v1/contacts', {
      method: 'POST',
      body: JSON.stringify(contact),
    })
  },

  // Activities
  async getActivities(prospectId?: string, limit?: number): Promise<Activity[]> {
    const params = new URLSearchParams()
    if (prospectId) params.set('prospect_id', prospectId)
    if (limit) params.set('limit', String(limit))
    return fetchAPI(`/api/v1/activities?${params}`)
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

  // Activities (legacy)
  async getRecentActivities(limit = 20): Promise<Activity[]> {
    const data = await fetchAPI<Activity[]>(`/api/v1/activities/recent?limit=${limit}`)
    return data
  },

  // Import
  async importProspects(data: unknown): Promise<{
    success: boolean
    skill_type: string
    prospects_created: number
    prospects_updated: number
    contacts_created: number
    contacts_updated: number
    warnings: string[]
    errors: string[]
  }> {
    return fetchAPI('/api/v1/import', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async previewImport(data: unknown): Promise<{
    skill_type: string
    prospect_count: number
    prospects: Array<{
      name?: string
      institution?: string
      type?: string
      state?: string
      tier?: string
      score?: number
      primary_contact_count?: number
      secondary_contacts_count?: number
    }>
  }> {
    return fetchAPI('/api/v1/import/preview', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}
