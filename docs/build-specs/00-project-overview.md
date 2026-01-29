# Project Overview

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Master specification for the Sportsbeams automated marketing pipeline

---

## Business Context

### Company Profile

**Sportsbeams Lighting, Inc.** is a technology company headquartered in Austin, Texas that designs, engineers, and manufactures premium LED sports lighting fixtures. Founded in 2007, the company has roots in studio lighting (Lite Panels) and earned two Emmy awards for LED lighting innovation.

**Key Products:**
- NOVA 1000 (131,000+ lumens, white light)
- Supernova Chromabeams 1500 (172,000+ lumens, full RGB + white)
- Orbit Series (smaller venues, 42,000-57,000 lumens)
- Court 500 (indoor applications)

**Technical Differentiators:**
1. **Active Cooling** - Patented fan-cooled system with 490,000 hour MTBF
2. **Zero Plastics** - All aluminum die-cast housing, tempered glass lenses
3. **Symmetrical Lighting** - Eliminates dead zones for 3D sports visibility
4. **Single Optic Design** - 346 lumens/sq.in. (vs. 1275 for competitors) reduces glare
5. **On-Fixture Drivers** - 48V DC (vs. 700V+ for competitors), safer and more reliable
6. **Chromabeams RGB** - Full-spectrum color + broadcast white in one fixture

**Notable Installations:**
- Texas A&M Kyle Field (first fully color-changing college stadium)
- Ford Amphitheater, Colorado Springs
- Cedar Crest Community Center, Dallas
- Multiple high school fields across Texas and other states

---

### Target Market

**Primary Geography:** Ohio, Indiana, Western Pennsylvania, Northern Kentucky, Illinois

**Primary Segments:**

| Segment | Description | Typical Deal Size |
|---------|-------------|-------------------|
| College D1/D2 | Major athletic programs, large stadiums | $200K - $500K+ |
| College D3/NAIA | Smaller programs, still significant facilities | $100K - $250K |
| Large High Schools (5A/6A) | 2000+ students, competitive athletic programs | $75K - $200K |
| Mid-Size High Schools (3A/4A) | 1000-2000 students, growing programs | $50K - $125K |

**Primary Decision Makers:**
1. Athletic Director (primary)
2. Facilities Director
3. School CFO / Business Manager
4. School Board / Board of Trustees (for capital approval)

**Buying Triggers:**
- Bond measure or levy passage
- Capital campaign completion
- Facility master plan adoption
- Current lighting failure / maintenance burden
- Conference broadcast requirements
- Competing school upgrades (keeping up)
- New construction / renovation projects

---

## System Purpose

This pipeline automates the following workflow:

```
1. DISCOVER → Find schools/colleges with potential lighting needs
2. QUALIFY → Score prospects against ICP criteria
3. RESEARCH → Develop constraint hypotheses and value propositions
4. ENGAGE → Execute tier-appropriate outreach sequences
5. NURTURE → Maintain relationships until timing aligns
```

### Goals

1. **Increase top-of-funnel volume** by systematically identifying prospects across target geography
2. **Prioritize high-value opportunities** through objective ICP scoring
3. **Personalize outreach at scale** using research-driven constraint hypotheses
4. **Reduce manual prospecting time** for sales team
5. **Maintain pipeline visibility** through real-time dashboard

### Non-Goals (for V1)

- Full CRM replacement (integrate with existing tools)
- Automated email sending without human approval for A1 tier
- Payment processing or quoting
- Project management post-sale

---

## Technical Approach

### Why Agent Architecture?

Long B2B sales cycles (6-18 months) with complex qualification require:

1. **Persistent monitoring** - Bid portals, bond elections, job changes
2. **Incremental enrichment** - Data gathered over time, not all at once
3. **Human-in-the-loop** - Approval gates for high-stakes outreach
4. **Audit trails** - Track what was done, when, and why

Agents handle these requirements better than simple automation scripts because they maintain state, coordinate handoffs, and support review workflows.

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Database | SQLite (dev) / PostgreSQL (prod) | Simple to start, scales when needed |
| Backend API | FastAPI + Python | Async support, type safety, rapid development |
| Agent Runtime | Python + APScheduler | Scheduled and event-driven execution |
| Frontend | Next.js + TypeScript + Tailwind | Modern React, good DX, easy deployment |
| Real-time | WebSockets | Live dashboard updates |
| AI/LLM | Anthropic Claude API | Research, constraint hypothesis, outreach drafting |

### Integration Points

| System | Purpose | Priority |
|--------|---------|----------|
| BidNet / Onvia | RFP monitoring | P1 |
| Hunter.io | Email finding | P1 |
| Apollo.io | Contact enrichment | P2 |
| LinkedIn Sales Navigator | Job changes, contact data | P2 |
| Existing CRM (TBD) | Sync opportunities | P2 |
| Email (SMTP) | Outreach sending | P1 |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Prospects identified per week | 20-30 | Prospector agent output |
| A1/A2 prospects per month | 10-15 | Hygiene agent tier assignment |
| Research completion rate | 90% within 48 hours | Researcher agent SLA |
| Outreach response rate | 15%+ for A1 tier | Reply tracking |
| Pipeline visibility | 100% of active prospects in dashboard | System coverage |

---

## Build Phases

### Phase 1: Foundation (Week 1-2)
- Database schema and models
- API scaffolding
- Basic dashboard shell
- Seed data for testing

### Phase 2: Prospector + Hygiene (Week 3-4)
- Prospect data import
- ICP scoring engine
- Tier assignment
- Dashboard: prospect list view

### Phase 3: Researcher + Outreach (Week 5-6)
- Constraint hypothesis generation
- Outreach sequence templates
- Human approval workflow
- Dashboard: research and outreach views

### Phase 4: Orchestrator + Polish (Week 7-8)
- Agent health monitoring
- Handoff coordination
- Dashboard: agent status, activity feed
- Testing and refinement

---

## Related Documents

- [Database Schema](01-database-schema.md)
- [Prospector Agent](02-prospector-agent.md)
- [Hygiene Agent](03-hygiene-agent.md)
- [Researcher Agent](04-researcher-agent.md)
- [Outreach Agent](05-outreach-agent.md)
- [Orchestrator Agent](06-orchestrator-agent.md)
- [Dashboard](07-dashboard.md)
