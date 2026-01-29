# Dashboard Build Specification

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Specification for the Mission Control dashboard for Sportsbeams pipeline

---

## Overview

The dashboard provides visibility into the pipeline, allows human review and approval, and surfaces actionable insights. It's built with Next.js and communicates with the API via REST and WebSocket.

### Key Features

1. **Pipeline Overview** - See prospects by stage and tier
2. **Prospect Management** - View, edit, and manually advance prospects
3. **Agent Status** - Real-time health monitoring
4. **Approval Workflow** - Review and approve A1 tier outreach
5. **Activity Feed** - Recent actions and events
6. **Reports** - Daily/weekly pipeline metrics

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State | Zustand |
| Real-time | WebSocket |
| Charts | Recharts |
| Icons | Lucide React |

---

## Page Structure

```
dashboard/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout with nav
│   │   ├── page.tsx             # Dashboard home (overview)
│   │   ├── prospects/
│   │   │   ├── page.tsx         # Prospect list
│   │   │   └── [id]/
│   │   │       └── page.tsx     # Prospect detail
│   │   ├── agents/
│   │   │   └── page.tsx         # Agent status
│   │   ├── outreach/
│   │   │   ├── page.tsx         # Sequence list
│   │   │   └── approvals/
│   │   │       └── page.tsx     # Pending approvals
│   │   ├── reports/
│   │   │   └── page.tsx         # Pipeline reports
│   │   └── settings/
│   │       └── page.tsx         # Configuration
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Nav.tsx
│   │   ├── prospects/
│   │   │   ├── ProspectCard.tsx
│   │   │   ├── ProspectTable.tsx
│   │   │   ├── ProspectDetail.tsx
│   │   │   ├── TierBadge.tsx
│   │   │   └── StatusBadge.tsx
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx
│   │   │   └── HealthIndicator.tsx
│   │   ├── outreach/
│   │   │   ├── SequenceCard.tsx
│   │   │   ├── ApprovalCard.tsx
│   │   │   └── EmailPreview.tsx
│   │   ├── activity/
│   │   │   └── ActivityFeed.tsx
│   │   ├── charts/
│   │   │   ├── PipelineFunnel.tsx
│   │   │   └── TierDistribution.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Badge.tsx
│   │       └── ...
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   ├── websocket.ts         # WebSocket client
│   │   └── utils.ts
│   └── stores/
│       ├── prospects.ts         # Prospect state
│       ├── agents.ts            # Agent health state
│       └── activity.ts          # Activity feed state
└── package.json
```

---

## Pages

### 1. Dashboard Home (`/`)

**Purpose:** High-level pipeline overview

**Components:**
- Pipeline funnel chart (prospects by stage)
- Tier distribution chart
- Key metrics cards (total prospects, A1/A2 count, emails sent today)
- Agent health summary
- Recent activity feed (last 10 items)
- Pending approvals alert

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────┐
│  SPORTSBEAMS PIPELINE                        [Alerts] [Profile] │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐ │
│ │   PROSPECTS     │ │    A1/A2        │ │   EMAILS TODAY      │ │
│ │      247        │ │     34          │ │       12            │ │
│ │   +12 today     │ │   3 pending     │ │   2 responses       │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────────┘ │
│                                                                  │
│ ┌──────────────────────────────┐  ┌────────────────────────────┐│
│ │     PIPELINE FUNNEL          │  │      AGENT STATUS          ││
│ │ ┌────────────────────────┐   │  │ Prospector    ● Healthy    ││
│ │ │ Identified         89  │   │  │ Hygiene       ● Healthy    ││
│ │ │ Scored            102  │   │  │ Researcher    ● Healthy    ││
│ │ │ Research Complete  34  │   │  │ Outreach      ○ Degraded   ││
│ │ │ Outreach Active    22  │   │  │ Orchestrator  ● Healthy    ││
│ │ └────────────────────────┘   │  └────────────────────────────┘│
│ └──────────────────────────────┘                                 │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────── │
│ │  RECENT ACTIVITY                                              ││
│ │  ─────────────────────────────────────────────────────────── ││
│ │  2 min ago   Prospect scored: Mason HS → A2 (67)             ││
│ │  5 min ago   Email sent: Ohio State (step 2 of 4)            ││
│ │  12 min ago  Research completed: Cincinnati                   ││
│ │  ...                                                          ││
│ └────────────────────────────────────────────────────────────── │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Prospects List (`/prospects`)

**Purpose:** View and manage all prospects

**Features:**
- Filterable table (by status, tier, state)
- Search by name
- Sort by score, created date, last activity
- Quick actions (view, edit status, start sequence)
- Bulk operations (export, assign tier)

**Components:**
```tsx
// components/prospects/ProspectTable.tsx

interface ProspectTableProps {
  prospects: Prospect[];
  onSelect: (id: string) => void;
  onStatusChange: (id: string, status: string) => void;
}

const ProspectTable = ({ prospects, onSelect, onStatusChange }: ProspectTableProps) => {
  return (
    <table className="w-full">
      <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>State</th>
          <th>Score</th>
          <th>Tier</th>
          <th>Status</th>
          <th>Last Activity</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {prospects.map(prospect => (
          <tr key={prospect.id} onClick={() => onSelect(prospect.id)}>
            <td>{prospect.name}</td>
            <td>{formatVenueType(prospect.venue_type)}</td>
            <td>{prospect.state}</td>
            <td>{prospect.icp_score}</td>
            <td><TierBadge tier={prospect.tier} /></td>
            <td><StatusBadge status={prospect.status} /></td>
            <td>{formatDate(prospect.updated_at)}</td>
            <td>
              <Button size="sm" onClick={() => onSelect(prospect.id)}>View</Button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

### 3. Prospect Detail (`/prospects/[id]`)

**Purpose:** Full prospect profile with history

**Sections:**
- Header (name, tier badge, score, status)
- Contact information
- Research findings (constraint hypothesis, value prop)
- Scoring breakdown (8 dimensions)
- Activity timeline
- Outreach sequence status
- Edit controls

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Prospects                                            │
├─────────────────────────────────────────────────────────────────┤
│  MASON HIGH SCHOOL                                              │
│  ┌──────┐  Division I  •  Mason, OH  •  Football               │
│  │  A2  │  Score: 67/100                                        │
│  └──────┘  Status: Research Complete                            │
├─────────────────────────────────────────────────────────────────┤
│  CONTACTS                          │  RESEARCH                  │
│  ─────────────────────────────     │  ───────────────────────── │
│  👤 John Smith (Primary)           │  Constraint: Energy Cost   │
│     Athletic Director              │  Confidence: High          │
│     jsmith@mason.k12.oh.us         │  Est. Impact: $45,000/yr   │
│     📞 513-555-0123                │                            │
│                                    │  Value Proposition:        │
│  👤 Jane Doe                       │  "Your metal halide system │
│     Facilities Director            │  is likely costing $45K+   │
│     jdoe@mason.k12.oh.us           │  annually in energy..."    │
├─────────────────────────────────────────────────────────────────┤
│  ICP SCORING                                                    │
│  ─────────────────────────────────────────────────────────────  │
│  Venue Type      ████████░░  8/10  (3x weight)                 │
│  Geography       ██████████  10/10 (2x weight)                 │
│  Budget Signals  ██████░░░░  6/10  (3x weight)                 │
│  Lighting Age    ████████░░  8/10  (2x weight)                 │
│  Night Games     ██████████  10/10 (2x weight)                 │
│  Broadcast       ██░░░░░░░░  2/10  (2x weight)                 │
│  DM Access       ████████░░  8/10  (2x weight)                 │
│  Timeline        ██████░░░░  6/10  (3x weight)                 │
├─────────────────────────────────────────────────────────────────┤
│  ACTIVITY TIMELINE                                              │
│  ─────────────────────────────────────────────────────────────  │
│  Jan 29  Research completed by Researcher Agent                 │
│  Jan 28  Scored 67 (A2) by Hygiene Agent                       │
│  Jan 28  Created from state directory import                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Agent Status (`/agents`)

**Purpose:** Monitor agent health and performance

**Components:**
- Agent cards with health indicators
- Recent runs table
- Error log
- Manual trigger buttons

### 5. Outreach Approvals (`/outreach/approvals`)

**Purpose:** Review and approve A1 tier emails

**Features:**
- List of pending approvals
- Email preview with personalization
- Approve / Request Changes / Reject actions
- Edit before sending

**Components:**
```tsx
// components/outreach/ApprovalCard.tsx

interface ApprovalCardProps {
  sequence: OutreachSequence;
  prospect: Prospect;
  contact: Contact;
  emailDraft: EmailDraft;
  onApprove: () => void;
  onReject: () => void;
  onEdit: () => void;
}

const ApprovalCard = ({ 
  sequence, prospect, contact, emailDraft, onApprove, onReject, onEdit 
}: ApprovalCardProps) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-semibold">{prospect.name}</h3>
            <p className="text-sm text-gray-500">
              To: {contact.name} ({contact.email})
            </p>
          </div>
          <TierBadge tier="A1" />
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="bg-gray-50 p-4 rounded">
          <p className="font-medium mb-2">Subject: {emailDraft.subject}</p>
          <div className="whitespace-pre-wrap text-sm">{emailDraft.body}</div>
        </div>
        
        <div className="mt-4 text-sm text-gray-500">
          <p>Constraint: {prospect.constraint_hypothesis}</p>
          <p>Score: {prospect.icp_score} ({prospect.tier})</p>
        </div>
      </CardContent>
      
      <CardFooter className="flex gap-2">
        <Button variant="primary" onClick={onApprove}>
          Approve & Send
        </Button>
        <Button variant="secondary" onClick={onEdit}>
          Edit
        </Button>
        <Button variant="ghost" onClick={onReject}>
          Skip
        </Button>
      </CardFooter>
    </Card>
  );
};
```

### 6. Reports (`/reports`)

**Purpose:** View pipeline analytics and reports

**Features:**
- Daily report summary
- Trend charts (prospects over time, response rates)
- Export to CSV/PDF

---

## Real-time Updates

### WebSocket Connection

```typescript
// lib/websocket.ts

class PipelineWebSocket {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Function[]> = new Map();
  
  connect() {
    this.ws = new WebSocket('ws://127.0.0.1:8765/ws');
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.emit(data.type, data.payload);
    };
    
    this.ws.onclose = () => {
      // Reconnect after delay
      setTimeout(() => this.connect(), 3000);
    };
  }
  
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }
  
  private emit(event: string, payload: any) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(cb => cb(payload));
  }
}

export const pipelineWS = new PipelineWebSocket();
```

### Event Types

```typescript
// Events from backend
type WSEvent = 
  | { type: 'prospect_created', payload: { id: string, name: string } }
  | { type: 'prospect_scored', payload: { id: string, score: number, tier: string } }
  | { type: 'research_completed', payload: { id: string, constraint: string } }
  | { type: 'email_sent', payload: { prospect_id: string, step: number } }
  | { type: 'approval_needed', payload: { sequence_id: string, prospect_id: string } }
  | { type: 'agent_health', payload: { agent: string, status: string } }
  | { type: 'report_generated', payload: { date: string, summary: string } };
```

---

## State Management

### Zustand Stores

```typescript
// stores/prospects.ts

import { create } from 'zustand';

interface ProspectState {
  prospects: Prospect[];
  loading: boolean;
  error: string | null;
  filters: {
    status?: string;
    tier?: string;
    state?: string;
    search?: string;
  };
  
  // Actions
  fetchProspects: () => Promise<void>;
  setFilters: (filters: Partial<ProspectState['filters']>) => void;
  updateProspect: (id: string, updates: Partial<Prospect>) => void;
}

export const useProspectStore = create<ProspectState>((set, get) => ({
  prospects: [],
  loading: false,
  error: null,
  filters: {},
  
  fetchProspects: async () => {
    set({ loading: true });
    try {
      const { filters } = get();
      const prospects = await api.getProspects(filters);
      set({ prospects, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
  
  setFilters: (filters) => {
    set((state) => ({ 
      filters: { ...state.filters, ...filters } 
    }));
    get().fetchProspects();
  },
  
  updateProspect: (id, updates) => {
    set((state) => ({
      prospects: state.prospects.map(p => 
        p.id === id ? { ...p, ...updates } : p
      )
    }));
  },
}));
```

---

## API Client

```typescript
// lib/api.ts

const API_BASE = 'http://127.0.0.1:8765/api/v1';

export const api = {
  // Prospects
  getProspects: async (filters?: ProspectFilters): Promise<Prospect[]> => {
    const params = new URLSearchParams(filters as any);
    const res = await fetch(`${API_BASE}/prospects?${params}`);
    const data = await res.json();
    return data.data;
  },
  
  getProspect: async (id: string): Promise<Prospect> => {
    const res = await fetch(`${API_BASE}/prospects/${id}`);
    const data = await res.json();
    return data.data;
  },
  
  updateProspect: async (id: string, updates: Partial<Prospect>): Promise<Prospect> => {
    const res = await fetch(`${API_BASE}/prospects/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    const data = await res.json();
    return data.data;
  },
  
  // Agents
  getAgentHealth: async (): Promise<AgentHealth[]> => {
    const res = await fetch(`${API_BASE}/orchestrator/health`);
    const data = await res.json();
    return data.data;
  },
  
  triggerAgent: async (agentName: string): Promise<void> => {
    await fetch(`${API_BASE}/${agentName}/run`, { method: 'POST' });
  },
  
  // Outreach
  getPendingApprovals: async (): Promise<PendingApproval[]> => {
    const res = await fetch(`${API_BASE}/outreach/pending-approvals`);
    const data = await res.json();
    return data.data;
  },
  
  approveSequence: async (sequenceId: string): Promise<void> => {
    await fetch(`${API_BASE}/outreach/sequences/${sequenceId}/approve`, {
      method: 'POST',
    });
  },
  
  // Reports
  getTodayReport: async (): Promise<PipelineReport> => {
    const res = await fetch(`${API_BASE}/orchestrator/report/today`);
    const data = await res.json();
    return data.data;
  },
};
```

---

## Styling (Tailwind)

### Brand Colors

```javascript
// tailwind.config.js

module.exports = {
  theme: {
    extend: {
      colors: {
        // Sportsbeams yellow/gold
        primary: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
        },
        // Navy/dark
        navy: {
          800: '#1E293B',
          900: '#0F172A',
        },
      },
    },
  },
};
```

### Tier Badge Colors

```tsx
const TIER_COLORS = {
  A1: 'bg-green-100 text-green-800 border-green-200',
  A2: 'bg-blue-100 text-blue-800 border-blue-200',
  B: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  C: 'bg-orange-100 text-orange-800 border-orange-200',
  D: 'bg-red-100 text-red-800 border-red-200',
};
```

---

## Development

### Setup

```bash
cd dashboard
npm install
npm run dev
```

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8765
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8765/ws
```

### Key Dependencies

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "zustand": "^4.4.0",
    "recharts": "^2.8.0",
    "lucide-react": "^0.263.1",
    "@tanstack/react-table": "^8.10.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "typescript": "^5.2.0",
    "tailwindcss": "^3.3.0",
    "@types/react": "^18.2.0"
  }
}
```

---

## Related Documents

- [Database Schema](01-database-schema.md) - Data models
- [Orchestrator Agent](06-orchestrator-agent.md) - Provides health/report data
- [Outreach Agent](05-outreach-agent.md) - Approval workflow integration
