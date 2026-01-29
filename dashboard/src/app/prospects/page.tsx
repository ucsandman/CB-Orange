'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { TierBadge, StatusBadge } from '@/components/ui/Badge'
import { api, Prospect } from '@/lib/api'
import { formatVenueType } from '@/lib/utils'
import { Search, Filter, ChevronRight } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function ProspectsPage() {
  const [prospects, setProspects] = useState<Prospect[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState({
    status: '',
    tier: '',
    state: '',
  })

  useEffect(() => {
    async function fetchProspects() {
      setLoading(true)
      try {
        const params: Record<string, string> = {}
        if (search) params.search = search
        if (filters.status) params.status = filters.status
        if (filters.tier) params.tier = filters.tier
        if (filters.state) params.state = filters.state

        const data = await api.getProspects(params)
        setProspects(data.prospects)
        setTotal(data.total)
      } catch (error) {
        console.error('Failed to fetch prospects:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchProspects()
  }, [search, filters])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-navy-900">Prospects</h1>
        <Button>Add Prospect</Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search prospects..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Status filter */}
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Statuses</option>
            <option value="identified">Identified</option>
            <option value="needs_scoring">Needs Scoring</option>
            <option value="scored">Scored</option>
            <option value="needs_research">Needs Research</option>
            <option value="research_complete">Research Complete</option>
            <option value="outreach_active">Outreach Active</option>
          </select>

          {/* Tier filter */}
          <select
            value={filters.tier}
            onChange={(e) => setFilters({ ...filters, tier: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Tiers</option>
            <option value="A1">A1</option>
            <option value="A2">A2</option>
            <option value="B">B</option>
            <option value="C">C</option>
            <option value="D">D</option>
          </select>

          {/* State filter */}
          <select
            value={filters.state}
            onChange={(e) => setFilters({ ...filters, state: e.target.value })}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All States</option>
            <option value="OH">Ohio</option>
            <option value="IN">Indiana</option>
            <option value="PA">Pennsylvania</option>
            <option value="KY">Kentucky</option>
            <option value="IL">Illinois</option>
          </select>
        </div>
      </Card>

      {/* Results */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          </div>
        ) : prospects.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-slate-500">No prospects found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    State
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Tier
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Updated
                  </th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {prospects.map((prospect) => (
                  <tr key={prospect.id} className="hover:bg-slate-50">
                    <td className="px-4 py-4">
                      <Link
                        href={`/prospects/${prospect.id}`}
                        className="font-medium text-navy-900 hover:text-primary-600"
                      >
                        {prospect.name}
                      </Link>
                      {prospect.city && (
                        <p className="text-xs text-slate-500">{prospect.city}</p>
                      )}
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-600">
                      {formatVenueType(prospect.venue_type)}
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-600">{prospect.state}</td>
                    <td className="px-4 py-4 text-sm font-medium text-navy-900">
                      {prospect.icp_score ?? '-'}
                    </td>
                    <td className="px-4 py-4">
                      <TierBadge tier={prospect.tier} />
                    </td>
                    <td className="px-4 py-4">
                      <StatusBadge status={prospect.status} />
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-500">
                      {formatDistanceToNow(new Date(prospect.updated_at))} ago
                    </td>
                    <td className="px-4 py-4">
                      <Link
                        href={`/prospects/${prospect.id}`}
                        className="text-slate-400 hover:text-slate-600"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination info */}
        {!loading && prospects.length > 0 && (
          <div className="px-4 py-3 border-t border-slate-200 text-sm text-slate-500">
            Showing {prospects.length} of {total} prospects
          </div>
        )}
      </Card>
    </div>
  )
}
