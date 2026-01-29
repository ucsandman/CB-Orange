'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { api, AgentHealth } from '@/lib/api'
import { Bot, Play, RefreshCw, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const AGENT_DESCRIPTIONS: Record<string, string> = {
  prospector: 'Discovers new prospects from data sources',
  hygiene: 'Scores prospects and assigns tiers',
  researcher: 'Develops constraint hypotheses',
  outreach: 'Manages email sequences',
  orchestrator: 'Monitors health and coordinates handoffs',
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentHealth[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState<string | null>(null)

  async function fetchAgents() {
    try {
      const data = await api.getAgentHealth()
      setAgents(data)
    } catch (error) {
      console.error('Failed to fetch agent health:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
    // Refresh every 30 seconds
    const interval = setInterval(fetchAgents, 30000)
    return () => clearInterval(interval)
  }, [])

  async function handleTrigger(agentName: string) {
    setTriggering(agentName)
    try {
      await api.triggerAgent(agentName)
      // Refresh after triggering
      setTimeout(fetchAgents, 1000)
    } catch (error) {
      console.error(`Failed to trigger ${agentName}:`, error)
    } finally {
      setTriggering(null)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'down':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <div className="w-5 h-5 rounded-full bg-slate-300" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-navy-900">Agent Status</h1>
        <Button variant="secondary" onClick={fetchAgents}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <Card key={agent.agent_name} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-100 rounded-lg">
                  <Bot className="w-6 h-6 text-slate-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-navy-900 capitalize">{agent.agent_name}</h3>
                  <p className="text-xs text-slate-500">
                    {AGENT_DESCRIPTIONS[agent.agent_name]}
                  </p>
                </div>
              </div>
              {getStatusIcon(agent.status)}
            </div>

            <div className="space-y-2 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-slate-500">Last Run</span>
                <span className="text-slate-700">
                  {agent.last_run_at
                    ? formatDistanceToNow(new Date(agent.last_run_at)) + ' ago'
                    : 'Never'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Status</span>
                <span
                  className={`capitalize ${
                    agent.last_run_status === 'completed'
                      ? 'text-green-600'
                      : agent.last_run_status === 'failed'
                      ? 'text-red-600'
                      : 'text-slate-600'
                  }`}
                >
                  {agent.last_run_status || '-'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Runs (24h)</span>
                <span className="text-slate-700">{agent.runs_last_24h}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Errors (24h)</span>
                <span className={agent.errors_last_24h > 0 ? 'text-red-600' : 'text-slate-700'}>
                  {agent.errors_last_24h}
                </span>
              </div>
            </div>

            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => handleTrigger(agent.agent_name)}
              disabled={triggering === agent.agent_name}
            >
              {triggering === agent.agent_name ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Triggering...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Trigger Run
                </>
              )}
            </Button>
          </Card>
        ))}
      </div>
    </div>
  )
}
