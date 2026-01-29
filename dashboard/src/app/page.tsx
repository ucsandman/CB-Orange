'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { api, PipelineStats, AgentHealth, Activity } from '@/lib/api'
import { Users, Zap, AlertTriangle, Activity as ActivityIcon, WifiOff } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function DashboardPage() {
  const [stats, setStats] = useState<PipelineStats | null>(null)
  const [health, setHealth] = useState<AgentHealth[]>([])
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      setError(null)
      try {
        const [statsData, healthData, activitiesData] = await Promise.all([
          api.getProspectStats(),
          api.getAgentHealth(),
          api.getRecentActivities(10),
        ])
        setStats(statsData)
        setHealth(healthData)
        setActivities(activitiesData)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
        setError(err instanceof Error ? err.message : 'Failed to connect to API')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <WifiOff className="w-12 h-12 text-slate-400 mb-4" />
        <h2 className="text-lg font-semibold text-slate-700 mb-2">Cannot connect to API</h2>
        <p className="text-slate-500 mb-4">Make sure the API server is running on port 8765</p>
        <code className="bg-slate-100 px-3 py-2 rounded text-sm text-slate-600">
          python -m uvicorn api.server:app --port 8765
        </code>
      </div>
    )
  }

  const a1a2Count = (stats?.by_tier?.A1 || 0) + (stats?.by_tier?.A2 || 0)
  const pendingFlags = 0 // TODO: Fetch from API

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-navy-900">Dashboard</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Total Prospects</p>
              <p className="text-2xl font-bold text-navy-900">{stats?.total_prospects || 0}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">A1/A2 Prospects</p>
              <p className="text-2xl font-bold text-navy-900">{a1a2Count}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Pending Flags</p>
              <p className="text-2xl font-bold text-navy-900">{pendingFlags}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline funnel */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-navy-900 mb-4">Pipeline Funnel</h2>
          <div className="space-y-3">
            {[
              { label: 'Identified', key: 'identified' },
              { label: 'Needs Scoring', key: 'needs_scoring' },
              { label: 'Scored', key: 'scored' },
              { label: 'Needs Research', key: 'needs_research' },
              { label: 'Research Complete', key: 'research_complete' },
              { label: 'Outreach Active', key: 'outreach_active' },
              { label: 'Engaged', key: 'engaged' },
            ].map(({ label, key }) => (
              <div key={key} className="flex items-center gap-3">
                <div className="w-32 text-sm text-slate-600">{label}</div>
                <div className="flex-1 bg-slate-100 rounded-full h-6 overflow-hidden">
                  <div
                    className="bg-primary-500 h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, ((stats?.by_status?.[key] || 0) / (stats?.total_prospects || 1)) * 100)}%`,
                    }}
                  />
                </div>
                <div className="w-12 text-right text-sm font-medium text-navy-900">
                  {stats?.by_status?.[key] || 0}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Agent health */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-navy-900 mb-4">Agent Status</h2>
          <div className="space-y-3">
            {health.map((agent) => (
              <div key={agent.agent_name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      agent.status === 'healthy'
                        ? 'bg-green-500'
                        : agent.status === 'degraded'
                        ? 'bg-yellow-500'
                        : 'bg-slate-300'
                    }`}
                  />
                  <span className="capitalize text-slate-700">{agent.agent_name}</span>
                </div>
                <span className="text-sm text-slate-500">
                  {agent.last_run_at
                    ? `Last run ${formatDistanceToNow(new Date(agent.last_run_at))} ago`
                    : 'Never run'}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent activity */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-navy-900 mb-4">Recent Activity</h2>
        {activities.length === 0 ? (
          <p className="text-slate-500 text-center py-4">No recent activity</p>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 pb-3 border-b border-slate-100 last:border-0"
              >
                <div className="p-2 bg-slate-100 rounded-lg">
                  <ActivityIcon className="w-4 h-4 text-slate-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-slate-700">{activity.description || activity.type}</p>
                  <p className="text-xs text-slate-400">
                    {formatDistanceToNow(new Date(activity.created_at))} ago
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
