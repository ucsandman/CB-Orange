# Researcher Agent Build Specification

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Specification for the agent that develops constraint hypotheses and value propositions for qualified prospects

---

## Overview

The Researcher Agent performs deep research on A1/A2 tier prospects to develop personalized outreach. It identifies pain points, quantifies potential value, and crafts tailored messaging.

### Responsibilities

1. **Constraint Hypothesis Development** - Identify the primary pain point or need
2. **Value Quantification** - Estimate dollar impact of solving the constraint
3. **Competitive Intelligence** - Understand competitive landscape
4. **Personalization Hooks** - Find specific angles for outreach
5. **Research Documentation** - Store findings for sales team reference

### Non-Responsibilities

- Initial prospect identification (Prospector Agent)
- ICP scoring (Hygiene Agent)
- Sending outreach (Outreach Agent)

---

## Constraint Categories

The Researcher looks for evidence of constraints in these categories:

### 1. Energy Cost Burden

**Signals:**
- Metal halide fixtures (10-15kW per pole vs 3-4kW LED)
- High utility rates in region
- Published sustainability commitments
- Energy audit mentions

**Research Prompts:**
- Search for "{school_name} energy costs"
- Search for "{school_name} sustainability initiative"
- Look up regional utility rates

**Value Quantification:**
```python
def calculate_energy_savings(
    current_fixtures: int,
    current_wattage_per_fixture: int,  # e.g., 1500W for metal halide
    led_wattage_per_fixture: int,       # e.g., 500W for LED
    hours_per_year: int,                 # e.g., 500 hours
    utility_rate: float                  # e.g., $0.12/kWh
) -> dict:
    """Calculate annual energy savings from LED upgrade."""
    current_kwh = current_fixtures * current_wattage_per_fixture * hours_per_year / 1000
    led_kwh = current_fixtures * led_wattage_per_fixture * hours_per_year / 1000
    
    savings_kwh = current_kwh - led_kwh
    savings_dollars = savings_kwh * utility_rate
    
    return {
        'current_annual_kwh': current_kwh,
        'led_annual_kwh': led_kwh,
        'savings_kwh': savings_kwh,
        'savings_dollars': savings_dollars,
        'savings_percent': (savings_kwh / current_kwh) * 100,
    }
```

### 2. Maintenance and Reliability

**Signals:**
- Fixture failures mentioned in news/social media
- Crane rental for lamp replacement
- Game delays or cancellations due to lighting
- Old fixtures (15+ years)

**Research Prompts:**
- Search for "{stadium_name} lighting problems"
- Search for "{school_name} stadium repairs"

### 3. Night Game Capacity

**Signals:**
- Limited night scheduling
- Conference requires certain games at night
- Revenue opportunities from additional events
- Community use requests

**Research Prompts:**
- Search for "{school_name} night games schedule"
- Search for "{school_name} stadium events"

### 4. Broadcast Quality

**Signals:**
- Inadequate foot-candles for TV (need 100+ fc for HD)
- Flickering on camera (metal halide issue)
- Conference broadcast requirements
- Streaming quality complaints

**Research Prompts:**
- Search for "{school_name} broadcast" + conference name
- Check conference media guides for lighting requirements

### 5. Recruiting Disadvantage

**Signals:**
- Competitors with modern facilities
- Facility rankings/comparisons
- Recruiting visit experience discussions

**Research Prompts:**
- Search for "{school_name} facilities recruiting"
- Compare to conference rival facilities

### 6. Community/Neighbor Complaints

**Signals:**
- Light spill/trespass issues
- Dark sky ordinances
- Glare complaints from fans or neighbors

**Research Prompts:**
- Search for "{school_name} stadium light complaints"
- Check local ordinances

### 7. RGB/Entertainment Gap

**Signals:**
- Desire for light shows
- School color displays at events
- Event differentiation from competitors
- Multi-use venue needs

**Research Prompts:**
- Search for "{school_name} game day experience"
- Look at competitor light shows

---

## Research Process

### Phase 1: Automated Data Gathering

```python
class ResearchGatherer:
    """
    Gather data from multiple sources for a prospect.
    """
    
    def gather(self, prospect: Prospect) -> ResearchData:
        data = ResearchData(prospect_id=prospect.id)
        
        # 1. Web search for recent news
        data.news_mentions = self._search_news(prospect)
        
        # 2. Check for RFPs/bids
        data.active_bids = self._check_bid_portals(prospect)
        
        # 3. Search for facility information
        data.facility_info = self._search_facility_info(prospect)
        
        # 4. Look up utility rates for region
        data.utility_rates = self._get_utility_rates(prospect.state, prospect.city)
        
        # 5. Check for bond/levy information
        data.funding_signals = self._search_funding_signals(prospect)
        
        # 6. Search social media for complaints/issues
        data.social_mentions = self._search_social(prospect)
        
        return data
    
    def _search_news(self, prospect: Prospect) -> List[NewsItem]:
        """Search Google News for relevant mentions."""
        queries = [
            f'"{prospect.name}" stadium lighting',
            f'"{prospect.name}" athletic facilities',
            f'"{prospect.stadium_name}" renovation' if prospect.stadium_name else None,
        ]
        # Use web search API
        pass
    
    def _search_facility_info(self, prospect: Prospect) -> FacilityInfo:
        """Search for facility specifications."""
        # Try to find:
        # - Number of light poles
        # - Fixture type (metal halide vs LED)
        # - Installation year
        # - Seating capacity
        pass
```

### Phase 2: LLM-Powered Analysis

```python
class ConstraintAnalyzer:
    """
    Use LLM to analyze gathered data and develop constraint hypothesis.
    """
    
    ANALYSIS_PROMPT = """
    You are a sales research analyst for Sportsbeams, a premium LED sports lighting company.
    
    Analyze the following information about {prospect_name} and identify their most likely
    primary constraint (pain point) related to athletic lighting.
    
    ## Prospect Information
    - Name: {prospect_name}
    - Type: {venue_type}
    - Location: {city}, {state}
    - Stadium: {stadium_name}
    - Current Lighting: {current_lighting_type} ({current_lighting_age_years} years old)
    - Primary Sport: {primary_sport}
    
    ## Research Data
    {research_data}
    
    ## Your Task
    1. Identify the PRIMARY constraint from these categories:
       - Energy Cost Burden
       - Maintenance/Reliability Issues
       - Night Game Capacity Limitations
       - Broadcast Quality Requirements
       - Recruiting Disadvantage
       - Community/Neighbor Concerns
       - RGB/Entertainment Capability Gap
    
    2. Provide specific evidence supporting this hypothesis
    
    3. Estimate the annual dollar impact (be conservative, show your math)
    
    4. Suggest 2-3 personalization hooks for outreach
    
    Respond in JSON format:
    {{
        "primary_constraint": "category name",
        "evidence": ["evidence point 1", "evidence point 2"],
        "estimated_annual_impact": 50000,
        "impact_calculation": "explanation of calculation",
        "personalization_hooks": ["hook 1", "hook 2"],
        "confidence": "high/medium/low",
        "secondary_constraints": ["other relevant constraints"]
    }}
    """
    
    def analyze(self, prospect: Prospect, research_data: ResearchData) -> ConstraintHypothesis:
        """Use Claude to analyze research and develop hypothesis."""
        prompt = self.ANALYSIS_PROMPT.format(
            prospect_name=prospect.name,
            venue_type=prospect.venue_type,
            city=prospect.city,
            state=prospect.state,
            stadium_name=prospect.stadium_name,
            current_lighting_type=prospect.current_lighting_type,
            current_lighting_age_years=prospect.current_lighting_age_years,
            primary_sport=prospect.primary_sport,
            research_data=research_data.to_text(),
        )
        
        response = self.llm.complete(prompt)
        return ConstraintHypothesis.from_json(response)
```

### Phase 3: Value Proposition Generation

```python
class ValuePropositionGenerator:
    """
    Generate tailored value proposition based on constraint hypothesis.
    """
    
    VALUE_PROP_PROMPT = """
    Create a compelling value proposition for {prospect_name} based on their primary constraint.
    
    ## Constraint
    {constraint_hypothesis}
    
    ## Sportsbeams Differentiators
    - Active cooling (490,000 hour MTBF) - reduces maintenance
    - Zero plastics (all aluminum) - longer lifespan, no yellowing
    - Symmetrical lighting - eliminates dead zones
    - Single optic design - reduces glare by 3.7x
    - 48V on-fixture drivers - safer than 700V competitors
    - Chromabeams RGB - full-spectrum color + broadcast white in one fixture
    
    ## Notable Installations
    - Texas A&M Kyle Field (first fully color-changing college stadium)
    - Ford Amphitheater, Colorado Springs
    - Multiple high schools in Texas and beyond
    
    ## Your Task
    Write a 2-3 sentence value proposition that:
    1. Acknowledges their specific situation
    2. Connects to their primary pain point
    3. Positions Sportsbeams as the solution
    4. Includes a proof point or differentiator
    
    Keep it conversational, not salesy. This will be used in personalized outreach.
    """
    
    def generate(self, prospect: Prospect, hypothesis: ConstraintHypothesis) -> str:
        """Generate value proposition."""
        pass
```

---

## Agent Implementation

### File Structure

```
agents/researcher/
├── __init__.py
├── agent.py              # Main ResearcherAgent class
├── gatherer.py           # ResearchGatherer - data collection
├── analyzer.py           # ConstraintAnalyzer - LLM analysis
├── value_prop.py         # ValuePropositionGenerator
├── sources/
│   ├── __init__.py
│   ├── web_search.py     # Google/Bing search wrapper
│   ├── news_search.py    # News-specific search
│   └── utility_rates.py  # Utility rate lookup
└── config.py
```

### Main Agent Class

```python
# agents/researcher/agent.py

from agents.base import BaseAgent
from agents.researcher.gatherer import ResearchGatherer
from agents.researcher.analyzer import ConstraintAnalyzer
from agents.researcher.value_prop import ValuePropositionGenerator
from database.models import Prospect, Activity
import logging

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """
    Agent that researches prospects and develops constraint hypotheses.
    
    Runs on prospects in 'needs_research' status.
    """
    
    name = "researcher"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.gatherer = ResearchGatherer()
        self.analyzer = ConstraintAnalyzer()
        self.value_prop_generator = ValuePropositionGenerator()
    
    def run_cycle(self) -> dict:
        """
        Research all prospects in 'needs_research' status.
        """
        prospects = self.db.query(Prospect).filter(
            Prospect.status == 'needs_research',
            Prospect.deleted_at.is_(None)
        ).all()
        
        results = {
            'researched': 0,
            'errors': [],
        }
        
        for prospect in prospects:
            try:
                self._research_prospect(prospect)
                results['researched'] += 1
            except Exception as e:
                logger.error(f"Error researching {prospect.id}: {e}")
                results['errors'].append({
                    'prospect_id': prospect.id,
                    'error': str(e)
                })
        
        return results
    
    def _research_prospect(self, prospect: Prospect) -> None:
        """Perform full research on a single prospect."""
        
        # Phase 1: Gather data
        self.emit_event("research_started", prospect_id=prospect.id)
        research_data = self.gatherer.gather(prospect)
        
        # Phase 2: Analyze and develop hypothesis
        hypothesis = self.analyzer.analyze(prospect, research_data)
        
        # Phase 3: Generate value proposition
        value_prop = self.value_prop_generator.generate(prospect, hypothesis)
        
        # Update prospect
        prospect.constraint_hypothesis = hypothesis.primary_constraint
        prospect.value_proposition = value_prop
        prospect.research_notes = hypothesis.to_json()
        prospect.status = 'research_complete'
        
        # Create activity
        activity = Activity(
            prospect_id=prospect.id,
            type='research_completed',
            description=f"Constraint hypothesis: {hypothesis.primary_constraint}",
            agent_id=self.name,
        )
        self.db.add(activity)
        
        # Log action
        self.log_action(
            action="research_completed",
            prospect_id=prospect.id,
            details={
                "constraint": hypothesis.primary_constraint,
                "confidence": hypothesis.confidence,
                "estimated_impact": hypothesis.estimated_annual_impact,
            }
        )
        
        self.db.commit()
        self.emit_event("research_completed", prospect_id=prospect.id)
    
    def research_single(self, prospect_id: str) -> dict:
        """Research a single prospect by ID (manual trigger)."""
        prospect = self.db.query(Prospect).filter(
            Prospect.id == prospect_id
        ).first()
        
        if not prospect:
            raise ValueError(f"Prospect {prospect_id} not found")
        
        self._research_prospect(prospect)
        
        return {
            'prospect_id': prospect_id,
            'constraint': prospect.constraint_hypothesis,
            'value_proposition': prospect.value_proposition,
        }
```

---

## Research Output Schema

```python
@dataclass
class ConstraintHypothesis:
    """Output of constraint analysis."""
    primary_constraint: str          # Category name
    evidence: List[str]              # Supporting evidence
    estimated_annual_impact: int     # Dollar estimate
    impact_calculation: str          # How we got the number
    personalization_hooks: List[str] # Outreach angles
    confidence: str                  # high/medium/low
    secondary_constraints: List[str] # Other relevant constraints
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ConstraintHypothesis':
        return cls(**json.loads(json_str))
```

---

## API Endpoints

```python
# api/routes/researcher.py

from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/api/v1/researcher", tags=["researcher"])

@router.post("/run")
async def run_researcher(background_tasks: BackgroundTasks):
    """Run researcher on all prospects needing research."""
    background_tasks.add_task(run_researcher_task)
    return {"status": "started"}

@router.post("/research/{prospect_id}")
async def research_prospect(prospect_id: str):
    """Research a single prospect."""
    pass

@router.get("/research/{prospect_id}")
async def get_research(prospect_id: str):
    """Get research results for a prospect."""
    pass
```

---

## Testing

### Test Cases

1. **Data Gathering**
   - News search returns relevant results
   - Empty results handled gracefully
   - Rate limiting respected

2. **Constraint Analysis**
   - Each constraint category can be identified
   - Confidence levels are appropriate
   - Impact estimates are reasonable

3. **Value Proposition**
   - Generated text is conversational
   - Includes proof points
   - Connects to constraint

### Mock Data

```python
MOCK_RESEARCH_DATA = {
    'news_mentions': [
        {
            'title': 'Mason High School announces facility master plan',
            'snippet': 'The plan includes upgrades to athletic lighting...',
            'date': '2025-09-15',
            'url': 'https://example.com/article1'
        }
    ],
    'active_bids': [],
    'facility_info': {
        'estimated_poles': 6,
        'estimated_fixtures_per_pole': 8,
        'lighting_type': 'metal_halide',
        'estimated_age': 18,
    },
    'utility_rates': {
        'state_avg_commercial': 0.11,
        'local_estimate': 0.12,
    },
}
```

---

## Related Documents

- [Database Schema](01-database-schema.md) - Research fields on Prospect
- [Hygiene Agent](03-hygiene-agent.md) - Sets status to 'needs_research'
- [Outreach Agent](05-outreach-agent.md) - Uses research for personalization
- [Orchestrator Agent](06-orchestrator-agent.md) - Triggers Outreach after Research
