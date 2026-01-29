'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { TierBadge, StatusBadge } from '@/components/ui/Badge'
import { api, Prospect, Contact, ProspectScore, Activity } from '@/lib/api'
import { formatVenueType, formatStatus } from '@/lib/utils'
import { ArrowLeft, User, Mail, Phone, MapPin, Building } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface ProspectDetail extends Prospect {
  contacts: Contact[]
  scores: ProspectScore[]
  recent_activities: Activity[]
}

const DIMENSION_LABELS: Record<string, string> = {
  venue_type: 'Venue Type',
  geography: 'Geography',
  budget_signals: 'Budget Signals',
  current_lighting_age: 'Lighting Age',
  night_game_frequency: 'Night Games',
  broadcast_requirements: 'Broadcast',
  decision_maker_access: 'DM Access',
  project_timeline: 'Timeline',
}

export default function ProspectDetailPage() {
  const params = useParams()
  const id = params.id as string

  const [prospect, setProspect] = useState<ProspectDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchProspect() {
      try {
        const data = await api.getProspect(id)
        setProspect(data as ProspectDetail)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch prospect')
      } finally {
        setLoading(false)
      }
    }
    fetchProspect()
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (error || !prospect) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">{error || 'Prospect not found'}</p>
        <Link href="/prospects" className="text-primary-500 hover:underline mt-4 inline-block">
          Back to prospects
        </Link>
      </div>
    )
  }

  const primaryContact = prospect.contacts?.find((c) => c.is_primary)

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/prospects"
        className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Prospects
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">{prospect.name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <TierBadge tier={prospect.tier} />
            <StatusBadge status={prospect.status} />
            <span className="text-slate-500">
              {formatVenueType(prospect.venue_type)} • {prospect.city}, {prospect.state}
            </span>
          </div>
          {prospect.icp_score !== undefined && (
            <p className="text-lg font-semibold text-navy-900 mt-2">
              Score: {prospect.icp_score}/100
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="secondary">Edit</Button>
          <Button>Start Outreach</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Facility info */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-navy-900 mb-4">Facility Information</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {prospect.stadium_name && (
                <div>
                  <p className="text-slate-500">Stadium</p>
                  <p className="font-medium">{prospect.stadium_name}</p>
                </div>
              )}
              {prospect.seating_capacity && (
                <div>
                  <p className="text-slate-500">Capacity</p>
                  <p className="font-medium">{prospect.seating_capacity.toLocaleString()}</p>
                </div>
              )}
              {prospect.current_lighting_type && (
                <div>
                  <p className="text-slate-500">Current Lighting</p>
                  <p className="font-medium capitalize">
                    {prospect.current_lighting_type.replace('_', ' ')}
                  </p>
                </div>
              )}
              {prospect.current_lighting_age_years && (
                <div>
                  <p className="text-slate-500">Lighting Age</p>
                  <p className="font-medium">{prospect.current_lighting_age_years} years</p>
                </div>
              )}
            </div>
          </Card>

          {/* Research */}
          {(prospect.constraint_hypothesis || prospect.value_proposition) && (
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-navy-900 mb-4">Research</h2>
              {prospect.constraint_hypothesis && (
                <div className="mb-4">
                  <p className="text-sm text-slate-500 mb-1">Constraint Hypothesis</p>
                  <p className="text-slate-700">{prospect.constraint_hypothesis}</p>
                </div>
              )}
              {prospect.value_proposition && (
                <div>
                  <p className="text-sm text-slate-500 mb-1">Value Proposition</p>
                  <p className="text-slate-700">{prospect.value_proposition}</p>
                </div>
              )}
            </Card>
          )}

          {/* ICP Scoring */}
          {prospect.scores && prospect.scores.length > 0 && (
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-navy-900 mb-4">ICP Scoring</h2>
              <div className="space-y-3">
                {prospect.scores.map((score) => (
                  <div key={score.id} className="flex items-center gap-3">
                    <div className="w-32 text-sm text-slate-600">
                      {DIMENSION_LABELS[score.dimension] || score.dimension}
                    </div>
                    <div className="flex-1">
                      <div className="bg-slate-100 rounded-full h-4 overflow-hidden">
                        <div
                          className="bg-primary-500 h-full rounded-full transition-all"
                          style={{ width: `${(score.score / 10) * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="w-20 text-right text-sm text-slate-600">
                      {score.score}/10 ({score.weight}x)
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Activity Timeline */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-navy-900 mb-4">Activity Timeline</h2>
            {prospect.recent_activities && prospect.recent_activities.length > 0 ? (
              <div className="space-y-4">
                {prospect.recent_activities.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex gap-3 pb-4 border-b border-slate-100 last:border-0"
                  >
                    <div className="w-2 h-2 mt-2 rounded-full bg-primary-500" />
                    <div>
                      <p className="text-sm text-slate-700">
                        {activity.description || formatStatus(activity.type)}
                      </p>
                      <p className="text-xs text-slate-400">
                        {formatDistanceToNow(new Date(activity.created_at))} ago
                        {activity.agent_id && ` • ${activity.agent_id}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-4">No activity yet</p>
            )}
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Contacts */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-navy-900 mb-4">Contacts</h2>
            {prospect.contacts && prospect.contacts.length > 0 ? (
              <div className="space-y-4">
                {prospect.contacts.map((contact) => (
                  <div
                    key={contact.id}
                    className="pb-4 border-b border-slate-100 last:border-0"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-slate-500" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-navy-900">
                          {contact.name}
                          {contact.is_primary && (
                            <span className="ml-2 text-xs text-primary-600">(Primary)</span>
                          )}
                        </p>
                        {contact.title && (
                          <p className="text-sm text-slate-500">{contact.title}</p>
                        )}
                        {contact.email && (
                          <a
                            href={`mailto:${contact.email}`}
                            className="flex items-center gap-1 text-sm text-primary-600 hover:underline mt-1"
                          >
                            <Mail className="w-3 h-3" />
                            {contact.email}
                          </a>
                        )}
                        {contact.phone && (
                          <p className="flex items-center gap-1 text-sm text-slate-500 mt-1">
                            <Phone className="w-3 h-3" />
                            {contact.phone}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-4">No contacts added</p>
            )}
            <Button variant="secondary" size="sm" className="w-full mt-4">
              Add Contact
            </Button>
          </Card>

          {/* Quick info */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-navy-900 mb-4">Details</h2>
            <div className="space-y-3 text-sm">
              {prospect.conference && (
                <div className="flex items-center gap-2">
                  <Building className="w-4 h-4 text-slate-400" />
                  <span>{prospect.conference}</span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-slate-400" />
                <span>
                  {prospect.city}, {prospect.state}
                </span>
              </div>
              {prospect.source && (
                <div>
                  <p className="text-slate-500">Source</p>
                  <p className="capitalize">{prospect.source.replace('_', ' ')}</p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
