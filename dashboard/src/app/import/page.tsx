'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Upload, FileJson, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8765'

interface ImportResult {
  skill_type: string
  prospects_created: number
  prospects_updated: number
  contacts_created: number
  contacts_updated: number
  imported_ids: string[]
  errors: string[]
  warnings: string[]
}

interface PreviewData {
  skill_type: string
  file_name: string
  prospect_count: number
  prospects: Array<{
    name?: string
    institution?: string
    type?: string
    state?: string
    tier?: string
    icp_score?: number
    total_score?: number
    has_decision_maker?: boolean
    secondary_contacts_count?: number
    contacts_count?: number
  }>
}

export default function ImportPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<PreviewData | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileSelect = useCallback(async (selectedFile: File) => {
    setFile(selectedFile)
    setPreview(null)
    setResult(null)
    setError(null)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const res = await fetch(`${API_BASE}/api/v1/import/preview`, {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Preview failed')
      }

      setPreview(data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to preview file')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile?.name.endsWith('.json')) {
        handleFileSelect(droppedFile)
      } else {
        setError('Please drop a JSON file')
      }
    },
    [handleFileSelect]
  )

  const handleImport = async () => {
    if (!file) return

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch(`${API_BASE}/api/v1/import/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || data.error || 'Import failed')
      }

      setResult(data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-navy-900">Import Prospects</h1>
      </div>

      {/* Instructions */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h2 className="font-semibold text-blue-800 mb-2">Supported Import Formats</h2>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>
            <strong>athletic-director-prospecting</strong> - Full prospect discovery with
            institution, facility, scoring, and contacts
          </li>
          <li>
            <strong>contact-finder-enrichment</strong> - Contact enrichment data for existing
            prospects
          </li>
        </ul>
      </Card>

      {/* Upload area */}
      {!result && (
        <Card
          className={`p-8 border-2 border-dashed transition-colors ${
            loading ? 'border-primary-300 bg-primary-50' : 'border-slate-300 hover:border-primary-400'
          }`}
          onDrop={handleDrop}
          onDragOver={(e: React.DragEvent) => e.preventDefault()}
        >
          <div className="text-center">
            {loading ? (
              <Loader2 className="w-12 h-12 mx-auto text-primary-500 animate-spin" />
            ) : (
              <Upload className="w-12 h-12 mx-auto text-slate-400" />
            )}
            <p className="mt-4 text-lg font-medium text-slate-700">
              {loading ? 'Processing...' : 'Drop JSON file here or click to browse'}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Supports athletic-director-prospecting and contact-finder-enrichment skills
            </p>
            <input
              type="file"
              accept=".json"
              onChange={(e) => {
                const selectedFile = e.target.files?.[0]
                if (selectedFile) handleFileSelect(selectedFile)
              }}
              className="hidden"
              id="file-input"
              disabled={loading}
            />
            <label htmlFor="file-input">
              <Button
                variant="secondary"
                className="mt-4"
                disabled={loading}
                onClick={() => document.getElementById('file-input')?.click()}
              >
                Select File
              </Button>
            </label>
          </div>
        </Card>
      )}

      {/* Error display */}
      {error && (
        <Card className="p-4 bg-red-50 border-red-200">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="w-5 h-5" />
            <p>{error}</p>
          </div>
        </Card>
      )}

      {/* Preview */}
      {preview && !result && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <FileJson className="w-6 h-6 text-primary-500" />
            <div>
              <h2 className="font-semibold text-navy-900">{preview.file_name}</h2>
              <p className="text-sm text-slate-500">
                Type: {preview.skill_type} • {preview.prospect_count} prospect(s)
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left">Name</th>
                  <th className="px-3 py-2 text-left">Type/State</th>
                  <th className="px-3 py-2 text-left">Tier</th>
                  <th className="px-3 py-2 text-left">Score</th>
                  <th className="px-3 py-2 text-left">Contacts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {preview.prospects.map((p, i) => (
                  <tr key={i}>
                    <td className="px-3 py-2 font-medium">{p.name || p.institution}</td>
                    <td className="px-3 py-2 text-slate-600">
                      {p.type || ''} {p.state ? `• ${p.state}` : ''}
                    </td>
                    <td className="px-3 py-2">
                      {p.tier && (
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            p.tier === 'A1'
                              ? 'bg-green-100 text-green-800'
                              : p.tier === 'A2'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {p.tier}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2">{p.icp_score || p.total_score || '-'}</td>
                    <td className="px-3 py-2">
                      {p.contacts_count ||
                        (p.has_decision_maker ? 1 : 0) + (p.secondary_contacts_count || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex gap-3 mt-6">
            <Button onClick={handleImport} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Importing...
                </>
              ) : (
                'Import Now'
              )}
            </Button>
            <Button variant="secondary" onClick={resetForm} disabled={loading}>
              Cancel
            </Button>
          </div>
        </Card>
      )}

      {/* Result */}
      {result && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle className="w-8 h-8 text-green-500" />
            <div>
              <h2 className="text-lg font-semibold text-navy-900">Import Complete</h2>
              <p className="text-sm text-slate-500">Skill type: {result.skill_type}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-green-700">{result.prospects_created}</p>
              <p className="text-sm text-green-600">Prospects Created</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">{result.prospects_updated}</p>
              <p className="text-sm text-blue-600">Prospects Updated</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-green-700">{result.contacts_created}</p>
              <p className="text-sm text-green-600">Contacts Created</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">{result.contacts_updated}</p>
              <p className="text-sm text-blue-600">Contacts Updated</p>
            </div>
          </div>

          {result.warnings.length > 0 && (
            <div className="mb-4 p-3 bg-yellow-50 rounded-lg">
              <p className="font-medium text-yellow-800 mb-1">Warnings:</p>
              <ul className="text-sm text-yellow-700 list-disc list-inside">
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {result.errors.length > 0 && (
            <div className="mb-4 p-3 bg-red-50 rounded-lg">
              <p className="font-medium text-red-800 mb-1">Errors:</p>
              <ul className="text-sm text-red-700 list-disc list-inside">
                {result.errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex gap-3">
            <Button onClick={() => router.push('/prospects')}>View Prospects</Button>
            <Button variant="secondary" onClick={resetForm}>
              Import Another
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
