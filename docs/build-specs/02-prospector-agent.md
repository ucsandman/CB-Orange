# Prospector Agent Build Specification

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Specification for the agent that discovers new prospects from various data sources

---

## Overview

The Prospector Agent is responsible for identifying potential customers (colleges and high schools with athletic venues) from multiple data sources and adding them to the pipeline. It runs on a scheduled basis and can also be triggered manually.

### Responsibilities

1. **Source Scanning** - Query configured data sources for potential prospects
2. **Deduplication** - Prevent duplicate prospect records
3. **Initial Data Capture** - Store basic information for later enrichment
4. **Source Tracking** - Record where each prospect was found

### Non-Responsibilities

- ICP scoring (handled by Hygiene Agent)
- Contact finding (handled by Contact Finder, separate utility)
- Research and enrichment (handled by Researcher Agent)

---

## Data Sources

### Priority 1 (Implement First)

#### 1. Manual CSV Import

Allow bulk import from spreadsheets.

```python
class CSVImportSource:
    """
    Import prospects from CSV file.
    
    Expected columns:
    - name (required)
    - venue_type (required): college_d1, college_d2, high_school_6a, etc.
    - state (required): OH, IN, PA, KY, IL
    - city
    - stadium_name
    - classification (for high schools)
    - conference
    - enrollment
    - primary_sport
    - notes
    """
    
    def import_file(self, filepath: str) -> ImportResult:
        # Validate required columns
        # Check for duplicates against existing prospects
        # Create prospect records with status='identified'
        # Return count of created, skipped (duplicate), failed
        pass
```

#### 2. State Athletic Association Directories

Scrape or import from state high school athletic associations.

| State | Association | Data Available |
|-------|-------------|----------------|
| Ohio | OHSAA | School list, classification, sports offered |
| Indiana | IHSAA | School list, classification, enrollment |
| Pennsylvania | PIAA | School list, district, classification |
| Kentucky | KHSAA | School list, classification, region |
| Illinois | IHSA | School list, classification, conference |

```python
class StateDirectorySource:
    """
    Import from state athletic association directories.
    
    Implementation approach:
    1. Download/scrape school lists (often available as PDF or HTML)
    2. Parse into structured data
    3. Filter to target classifications (5A, 6A, or equivalent)
    4. Deduplicate against existing prospects
    """
    
    SOURCES = {
        'OH': {
            'url': 'https://www.ohsaa.org/School-Directory',
            'classifications': ['Division I', 'Division II'],
        },
        'IN': {
            'url': 'https://www.ihsaa.org/Schools',
            'classifications': ['6A', '5A'],
        },
        # ... etc
    }
    
    def scan(self, state: str) -> List[ProspectData]:
        pass
```

#### 3. Bid Portal Monitoring

Monitor public bid portals for athletic facility RFPs.

```python
class BidPortalSource:
    """
    Monitor bid portals for relevant RFPs.
    
    Search terms:
    - "athletic lighting"
    - "LED sports lighting"
    - "stadium lighting"
    - "field lighting"
    - "gymnasium lighting"
    
    Filter by:
    - States: OH, IN, PA, KY, IL
    - Categories: Construction, Electrical, Athletic Facilities
    """
    
    PORTALS = {
        'bidnet': {
            'base_url': 'https://www.bidnet.com',
            'requires_auth': True,
        },
        'onvia': {
            'base_url': 'https://www.onvia.com',
            'requires_auth': True,
        },
        'public_purchase': {
            'base_url': 'https://www.publicpurchase.com',
            'requires_auth': False,
        }
    }
    
    def scan(self) -> List[BidAlert]:
        # Search each portal
        # Parse results
        # Match to existing prospects or flag as new
        # Store in bid_alerts table
        pass
```

### Priority 2 (Implement Later)

#### 4. Bond Election Tracker

Monitor for passed school bond measures that indicate capital funding.

```python
class BondElectionSource:
    """
    Track school bond elections.
    
    Data sources:
    - Ballotpedia (local elections)
    - State education department bond registrations
    - Local news searches
    
    Trigger: Bond measure passed in last 12 months
    """
    
    def scan(self) -> List[BondSignal]:
        pass
```

#### 5. LinkedIn Job Changes

Track Athletic Director job changes (new AD = new opportunity).

```python
class LinkedInTriggerSource:
    """
    Monitor LinkedIn for relevant job changes.
    
    Triggers:
    - New Athletic Director hired
    - New Facilities Director hired
    - Job posting for AD at target school
    
    Requires: LinkedIn Sales Navigator API or scraping
    """
    
    def scan(self) -> List[JobChangeSignal]:
        pass
```

#### 6. Construction News

Monitor regional construction news for facility announcements.

```python
class ConstructionNewsSource:
    """
    Monitor construction and business news.
    
    Sources:
    - ENR (Engineering News-Record)
    - Regional business journals
    - School district press releases
    
    Keywords:
    - "stadium renovation"
    - "athletic facility"
    - "field upgrade"
    - "lighting project"
    """
    
    def scan(self) -> List[NewsSignal]:
        pass
```

---

## Agent Implementation

### File Structure

```
agents/prospector/
├── __init__.py
├── agent.py              # Main ProspectorAgent class
├── sources/
│   ├── __init__.py
│   ├── base.py           # BaseSource abstract class
│   ├── csv_import.py
│   ├── state_directory.py
│   ├── bid_portal.py
│   ├── bond_election.py
│   ├── linkedin.py
│   └── construction_news.py
├── deduplication.py      # Duplicate detection logic
└── config.py             # Source configuration
```

### Base Source Class

```python
# agents/prospector/sources/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ProspectData:
    """Raw prospect data from a source."""
    name: str
    venue_type: str
    state: str
    city: Optional[str] = None
    address: Optional[str] = None
    classification: Optional[str] = None
    conference: Optional[str] = None
    enrollment: Optional[int] = None
    primary_sport: Optional[str] = None
    stadium_name: Optional[str] = None
    seating_capacity: Optional[int] = None
    source: str = ""
    source_url: Optional[str] = None
    source_date: Optional[datetime] = None
    raw_data: Optional[dict] = None  # Original data for reference

@dataclass
class ScanResult:
    """Result of a source scan."""
    source_name: str
    prospects_found: int
    prospects_created: int
    prospects_skipped_duplicate: int
    prospects_skipped_error: int
    errors: List[str]
    scan_duration_seconds: float

class BaseSource(ABC):
    """Abstract base class for prospect sources."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this source."""
        pass
    
    @property
    @abstractmethod
    def scan_frequency(self) -> str:
        """How often to scan: 'hourly', 'daily', 'weekly', 'manual'"""
        pass
    
    @abstractmethod
    def scan(self) -> List[ProspectData]:
        """
        Scan the source and return found prospects.
        
        Returns:
            List of ProspectData objects
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if this source is enabled in configuration."""
        # Check config
        return True
```

### Main Agent Class

```python
# agents/prospector/agent.py

from agents.base import BaseAgent
from agents.prospector.sources import (
    CSVImportSource,
    StateDirectorySource,
    BidPortalSource,
)
from agents.prospector.deduplication import DeduplicationEngine
from database.models import Prospect, BidAlert, AgentAuditLog
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ProspectorAgent(BaseAgent):
    """
    Agent that discovers new prospects from configured sources.
    
    Run modes:
    - scheduled: Run all enabled sources on their configured frequency
    - manual: Run specific source(s) on demand
    - import: Import from a specific file
    """
    
    name = "prospector"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.dedup = DeduplicationEngine(db_session)
        self.sources = self._init_sources()
    
    def _init_sources(self) -> dict:
        """Initialize all configured sources."""
        return {
            'csv_import': CSVImportSource(),
            'state_directory': StateDirectorySource(),
            'bid_portal': BidPortalSource(),
        }
    
    def run_cycle(self, source_filter: Optional[List[str]] = None) -> dict:
        """
        Run a prospecting cycle.
        
        Args:
            source_filter: Optional list of source names to run.
                          If None, runs all sources due for scanning.
        
        Returns:
            Summary of results by source
        """
        results = {}
        
        sources_to_run = self._get_sources_to_run(source_filter)
        
        for source_name, source in sources_to_run.items():
            try:
                result = self._run_source(source)
                results[source_name] = result
                
                self.log_action(
                    action="source_scanned",
                    details={
                        "source": source_name,
                        "found": result.prospects_found,
                        "created": result.prospects_created,
                        "duplicates": result.prospects_skipped_duplicate,
                    }
                )
                
            except Exception as e:
                logger.error(f"Error scanning source {source_name}: {e}")
                results[source_name] = {
                    "error": str(e)
                }
        
        return results
    
    def _run_source(self, source) -> ScanResult:
        """Run a single source scan."""
        import time
        start_time = time.time()
        
        # Scan source
        prospects_data = source.scan()
        
        created = 0
        duplicates = 0
        errors = []
        
        for data in prospects_data:
            try:
                # Check for duplicate
                existing = self.dedup.find_duplicate(data)
                
                if existing:
                    duplicates += 1
                    continue
                
                # Create prospect
                prospect = self._create_prospect(data)
                created += 1
                
                self.log_action(
                    action="prospect_created",
                    prospect_id=prospect.id,
                    details={
                        "name": prospect.name,
                        "source": source.name,
                    }
                )
                
            except Exception as e:
                errors.append(f"{data.name}: {str(e)}")
        
        return ScanResult(
            source_name=source.name,
            prospects_found=len(prospects_data),
            prospects_created=created,
            prospects_skipped_duplicate=duplicates,
            prospects_skipped_error=len(errors),
            errors=errors,
            scan_duration_seconds=time.time() - start_time,
        )
    
    def _create_prospect(self, data: ProspectData) -> Prospect:
        """Create a new prospect from source data."""
        prospect = Prospect(
            name=data.name,
            venue_type=data.venue_type,
            state=data.state,
            city=data.city,
            address=data.address,
            classification=data.classification,
            conference=data.conference,
            enrollment=data.enrollment,
            primary_sport=data.primary_sport,
            stadium_name=data.stadium_name,
            seating_capacity=data.seating_capacity,
            status='identified',
            source=data.source,
            source_url=data.source_url,
            source_date=data.source_date,
        )
        
        self.db.add(prospect)
        self.db.commit()
        
        return prospect
    
    def import_csv(self, filepath: str) -> ScanResult:
        """Import prospects from a CSV file."""
        source = self.sources['csv_import']
        source.set_filepath(filepath)
        return self._run_source(source)
    
    def _get_sources_to_run(self, source_filter: Optional[List[str]]) -> dict:
        """Determine which sources should run."""
        if source_filter:
            return {k: v for k, v in self.sources.items() if k in source_filter}
        
        # Check which sources are due based on their frequency
        # For now, return all enabled sources
        return {k: v for k, v in self.sources.items() if v.is_enabled()}
```

### Deduplication Engine

```python
# agents/prospector/deduplication.py

from database.models import Prospect
from typing import Optional
import re

class DeduplicationEngine:
    """
    Detect duplicate prospects.
    
    Matching strategies:
    1. Exact name match (case-insensitive)
    2. Fuzzy name match (for variations like "Ohio State" vs "Ohio State University")
    3. Location match (same city + state + similar name)
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def find_duplicate(self, data) -> Optional[Prospect]:
        """
        Check if a prospect already exists.
        
        Returns:
            Existing Prospect if duplicate found, None otherwise
        """
        # Strategy 1: Exact name match
        normalized_name = self._normalize_name(data.name)
        
        existing = self.db.query(Prospect).filter(
            Prospect.deleted_at.is_(None)
        ).all()
        
        for prospect in existing:
            if self._normalize_name(prospect.name) == normalized_name:
                return prospect
            
            # Strategy 2: Fuzzy match on similar names
            if self._is_fuzzy_match(data.name, prospect.name):
                return prospect
            
            # Strategy 3: Same city/state with similar stadium
            if (data.city and prospect.city and 
                data.city.lower() == prospect.city.lower() and
                data.state == prospect.state and
                data.stadium_name and prospect.stadium_name and
                self._is_fuzzy_match(data.stadium_name, prospect.stadium_name)):
                return prospect
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison."""
        # Lowercase
        name = name.lower()
        
        # Remove common suffixes
        suffixes = ['university', 'college', 'high school', 'hs', 'school district', 'isd']
        for suffix in suffixes:
            name = name.replace(suffix, '')
        
        # Remove punctuation and extra whitespace
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())
        
        return name.strip()
    
    def _is_fuzzy_match(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """Check if two names are a fuzzy match."""
        from difflib import SequenceMatcher
        
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)
        
        ratio = SequenceMatcher(None, n1, n2).ratio()
        return ratio >= threshold
```

---

## Configuration

```python
# agents/prospector/config.py

PROSPECTOR_CONFIG = {
    'sources': {
        'csv_import': {
            'enabled': True,
            'frequency': 'manual',
        },
        'state_directory': {
            'enabled': True,
            'frequency': 'weekly',
            'states': ['OH', 'IN', 'PA', 'KY', 'IL'],
            'min_classification': '4A',  # Skip smaller schools
        },
        'bid_portal': {
            'enabled': True,
            'frequency': 'daily',
            'search_terms': [
                'athletic lighting',
                'LED sports lighting',
                'stadium lighting',
                'field lighting',
                'gymnasium lighting',
            ],
            'states': ['OH', 'IN', 'PA', 'KY', 'IL'],
        },
        'bond_election': {
            'enabled': False,  # Phase 2
            'frequency': 'weekly',
        },
        'linkedin': {
            'enabled': False,  # Phase 2
            'frequency': 'daily',
        },
        'construction_news': {
            'enabled': False,  # Phase 2
            'frequency': 'daily',
        },
    },
    'deduplication': {
        'fuzzy_match_threshold': 0.85,
    },
}
```

---

## API Endpoints

```python
# api/routes/prospector.py

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from agents.prospector import ProspectorAgent

router = APIRouter(prefix="/api/v1/prospector", tags=["prospector"])

@router.post("/run")
async def run_prospector(
    background_tasks: BackgroundTasks,
    sources: Optional[List[str]] = None
):
    """
    Trigger a prospector run.
    
    Args:
        sources: Optional list of source names to run.
                If not provided, runs all due sources.
    """
    # Run in background
    background_tasks.add_task(run_prospector_task, sources)
    return {"status": "started", "sources": sources or "all"}

@router.post("/import")
async def import_csv(file: UploadFile = File(...)):
    """Import prospects from CSV file."""
    # Save file temporarily
    # Run import
    # Return results
    pass

@router.get("/sources")
async def list_sources():
    """List all configured sources and their status."""
    pass

@router.get("/runs")
async def list_runs(limit: int = 20):
    """List recent prospector runs."""
    pass
```

---

## Testing

### Test Cases

1. **CSV Import**
   - Valid file with all required columns
   - Missing required columns
   - Duplicate detection
   - Invalid venue_type values

2. **Deduplication**
   - Exact name match
   - Fuzzy match variations ("Ohio State" vs "The Ohio State University")
   - Same location different name
   - Similar names different locations (not duplicates)

3. **State Directory**
   - Parse school list correctly
   - Filter by classification
   - Handle missing data gracefully

4. **Bid Portal**
   - Search term matching
   - State filtering
   - Date parsing
   - Link to existing prospect vs create new

### Sample Test Data

```python
# tests/prospector/test_data.py

SAMPLE_PROSPECTS = [
    {
        "name": "Mason High School",
        "venue_type": "high_school_6a",
        "state": "OH",
        "city": "Mason",
        "classification": "Division I",
        "enrollment": 3200,
        "primary_sport": "football",
        "stadium_name": "Atrium Stadium",
    },
    {
        "name": "Ohio State University",
        "venue_type": "college_d1",
        "state": "OH",
        "city": "Columbus",
        "primary_sport": "football",
        "stadium_name": "Ohio Stadium",
        "seating_capacity": 102780,
    },
    # ... more test data
]

DUPLICATE_VARIATIONS = [
    ("Ohio State University", "The Ohio State University"),
    ("Mason High School", "Mason HS"),
    ("University of Cincinnati", "Cincinnati, University of"),
]
```

---

## Monitoring

### Metrics to Track

- Prospects found per source per run
- Duplicate rate by source
- Error rate by source
- Time since last successful scan per source
- New prospects added per day/week

### Alerts

- Source scan fails 3+ consecutive times
- No new prospects found in 7 days
- Duplicate rate exceeds 80% (source may be stale)

---

## Related Documents

- [Database Schema](01-database-schema.md) - Prospect and BidAlert tables
- [Hygiene Agent](03-hygiene-agent.md) - Scores prospects after creation
- [Orchestrator Agent](06-orchestrator-agent.md) - Triggers Hygiene after Prospector
