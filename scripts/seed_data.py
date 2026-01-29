"""Seed the database with test data and outreach templates.

Usage:
    python scripts/seed_data.py
"""
import sys
import os
from datetime import date, datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db, SessionLocal
from database.models import (
    Prospect, Contact, ProspectScore, Activity, OutreachTemplate,
    AgentRun, HygieneFlag
)


def seed_outreach_templates(db):
    """Insert the standard outreach templates."""
    templates = [
        # A1 Tier (High-touch, 4 steps)
        {
            "id": "a1-1",
            "name": "A1 Initial Outreach",
            "tier": "A1",
            "step_number": 1,
            "subject_template": "{{stadium_name}} Lighting - Quick Question",
            "body_template": """Hi {{first_name}},

I noticed {{school_name}} has been {{trigger_observation}}. Given the timing, I wanted to reach out about your field lighting.

{{constraint_hypothesis}}

Would a 15-minute call this week make sense to see if we can help?

Best,
{{sender_name}}""",
            "days_after_previous": 0,
        },
        {
            "id": "a1-2",
            "name": "A1 Case Study Follow-up",
            "tier": "A1",
            "step_number": 2,
            "subject_template": "How {{similar_school}} solved their lighting challenge",
            "body_template": """Hi {{first_name}},

Quick follow-up on my note about {{stadium_name}}.

I thought you might find this relevant - {{similar_school}} faced a similar situation with {{shared_challenge}}. Here's what they did: {{case_study_link}}

Worth a conversation?

Best,
{{sender_name}}""",
            "days_after_previous": 4,
        },
        {
            "id": "a1-3",
            "name": "A1 Value Add",
            "tier": "A1",
            "step_number": 3,
            "subject_template": "Complimentary photometric study for {{school_name}}",
            "body_template": """Hi {{first_name}},

I wanted to offer something concrete - we'd be happy to do a complimentary photometric study of {{stadium_name}} to show exactly what modern LED lighting could look like.

No commitment, just useful data for whenever your timeline makes sense.

Interested?

Best,
{{sender_name}}""",
            "days_after_previous": 5,
        },
        {
            "id": "a1-4",
            "name": "A1 Break-up",
            "tier": "A1",
            "step_number": 4,
            "subject_template": "Closing the loop on {{school_name}} lighting",
            "body_template": """Hi {{first_name}},

I've reached out a few times about lighting for {{stadium_name}} and haven't heard back - totally understand if the timing isn't right.

I'll step back for now, but if lighting comes up in the future, I'd welcome the chance to help. We've done great work with similar programs like {{similar_school}}.

Wishing you a great season ahead.

Best,
{{sender_name}}""",
            "days_after_previous": 7,
        },
        # A2 Tier (Standard, 3 steps)
        {
            "id": "a2-1",
            "name": "A2 Initial Outreach",
            "tier": "A2",
            "step_number": 1,
            "subject_template": "LED Lighting for {{school_name}} Athletics",
            "body_template": """Hi {{first_name}},

I'm reaching out to athletic directors at {{classification}} programs in {{state}} about field lighting upgrades.

{{value_proposition}}

Would it make sense to connect briefly about your facilities roadmap?

Best,
{{sender_name}}""",
            "days_after_previous": 0,
        },
        {
            "id": "a2-2",
            "name": "A2 Follow-up",
            "tier": "A2",
            "step_number": 2,
            "subject_template": "Following up - {{school_name}} lighting",
            "body_template": """Hi {{first_name}},

Quick follow-up on my note about lighting for {{school_name}}.

I've attached a case study from {{similar_school}} that might be relevant to your situation.

Worth a quick call?

Best,
{{sender_name}}""",
            "days_after_previous": 5,
        },
        {
            "id": "a2-3",
            "name": "A2 Break-up",
            "tier": "A2",
            "step_number": 3,
            "subject_template": "One more note on {{school_name}} lighting",
            "body_template": """Hi {{first_name}},

I'll keep this brief - I've reached out about lighting for {{stadium_name}} and understand if the timing isn't right.

If it ever comes up, we'd love to help. Feel free to reach out anytime.

Best,
{{sender_name}}""",
            "days_after_previous": 7,
        },
        # B Tier (Nurture, 2 steps)
        {
            "id": "b-1",
            "name": "B Initial Outreach",
            "tier": "B",
            "step_number": 1,
            "subject_template": "Resource: LED Lighting ROI Calculator",
            "body_template": """Hi {{first_name}},

I wanted to share a resource that might be useful when you're planning future facility upgrades - our LED Lighting ROI Calculator.

It helps estimate energy savings and payback period for athletic lighting projects: {{roi_calculator_link}}

No pitch - just a useful tool. Let me know if you have any questions.

Best,
{{sender_name}}""",
            "days_after_previous": 0,
        },
        {
            "id": "b-2",
            "name": "B Quarterly Check-in",
            "tier": "B",
            "step_number": 2,
            "subject_template": "Checking in - {{school_name}} facilities planning",
            "body_template": """Hi {{first_name}},

Hope the season is going well at {{school_name}}.

I wanted to check in on your facilities roadmap - any lighting projects on the horizon?

Either way, happy to be a resource if questions come up.

Best,
{{sender_name}}""",
            "days_after_previous": 90,
        },
    ]

    for template_data in templates:
        existing = db.query(OutreachTemplate).filter(
            OutreachTemplate.id == template_data["id"]
        ).first()

        if not existing:
            template = OutreachTemplate(**template_data)
            db.add(template)

    db.commit()
    print(f"Seeded {len(templates)} outreach templates")


def seed_sample_prospects(db):
    """Insert sample prospects for testing."""
    prospects_data = [
        # Ohio schools
        {
            "name": "Ohio State University",
            "venue_type": "college_d1",
            "state": "OH",
            "city": "Columbus",
            "conference": "Big Ten",
            "stadium_name": "Ohio Stadium",
            "seating_capacity": 102780,
            "primary_sport": "football",
            "current_lighting_type": "early_led",
            "current_lighting_age_years": 8,
            "broadcast_requirements": "espn",
            "status": "scored",
            "tier": "A1",
            "icp_score": 82,
            "source": "manual",
        },
        {
            "name": "University of Cincinnati",
            "venue_type": "college_d1",
            "state": "OH",
            "city": "Cincinnati",
            "conference": "Big 12",
            "stadium_name": "Nippert Stadium",
            "seating_capacity": 40000,
            "primary_sport": "football",
            "current_lighting_type": "metal_halide",
            "current_lighting_age_years": 12,
            "broadcast_requirements": "conference_network",
            "status": "needs_research",
            "tier": "A2",
            "icp_score": 68,
            "source": "manual",
        },
        {
            "name": "Mason High School",
            "venue_type": "high_school_6a",
            "state": "OH",
            "city": "Mason",
            "classification": "6A",
            "conference": "Greater Miami Conference",
            "enrollment": 3200,
            "stadium_name": "Atrium Stadium",
            "seating_capacity": 8500,
            "primary_sport": "football",
            "current_lighting_type": "metal_halide",
            "current_lighting_age_years": 15,
            "broadcast_requirements": "local_streaming",
            "status": "research_complete",
            "tier": "A2",
            "icp_score": 67,
            "constraint_hypothesis": "Aging metal halide system likely causing $45K+ annually in energy costs. Recent bond passage for facility upgrades.",
            "value_proposition": "Modern LED lighting could cut energy costs by 60% and eliminate maintenance headaches from failing metal halide bulbs.",
            "source": "directory_import",
        },
        {
            "name": "St. Xavier High School",
            "venue_type": "high_school_5a",
            "state": "OH",
            "city": "Cincinnati",
            "classification": "5A",
            "conference": "Greater Catholic League",
            "enrollment": 1550,
            "stadium_name": "RDI Stadium",
            "seating_capacity": 5000,
            "primary_sport": "football",
            "current_lighting_type": "early_led",
            "current_lighting_age_years": 5,
            "broadcast_requirements": "local_streaming",
            "status": "scored",
            "tier": "B",
            "icp_score": 45,
            "source": "manual",
        },
        # Indiana schools
        {
            "name": "Purdue University",
            "venue_type": "college_d1",
            "state": "IN",
            "city": "West Lafayette",
            "conference": "Big Ten",
            "stadium_name": "Ross-Ade Stadium",
            "seating_capacity": 57236,
            "primary_sport": "football",
            "current_lighting_type": "metal_halide",
            "current_lighting_age_years": 10,
            "broadcast_requirements": "espn",
            "status": "needs_scoring",
            "source": "manual",
        },
        {
            "name": "Carmel High School",
            "venue_type": "high_school_6a",
            "state": "IN",
            "city": "Carmel",
            "classification": "6A",
            "conference": "Metropolitan Interscholastic Conference",
            "enrollment": 5000,
            "stadium_name": "Carmel Stadium",
            "seating_capacity": 10000,
            "primary_sport": "football",
            "current_lighting_type": "metal_halide",
            "current_lighting_age_years": 18,
            "broadcast_requirements": "local_streaming",
            "status": "identified",
            "source": "directory_import",
        },
        # Pennsylvania schools
        {
            "name": "University of Pittsburgh",
            "venue_type": "college_d1",
            "state": "PA",
            "city": "Pittsburgh",
            "conference": "ACC",
            "stadium_name": "Acrisure Stadium",
            "seating_capacity": 68400,
            "primary_sport": "football",
            "current_lighting_type": "modern_led",
            "current_lighting_age_years": 2,
            "broadcast_requirements": "espn",
            "status": "deprioritized",
            "tier": "D",
            "icp_score": 22,
            "source": "manual",
        },
        # Kentucky schools
        {
            "name": "Northern Kentucky University",
            "venue_type": "college_d1",
            "state": "KY",
            "city": "Highland Heights",
            "conference": "Horizon League",
            "stadium_name": "NKU Soccer Stadium",
            "seating_capacity": 2500,
            "primary_sport": "multi_sport",
            "current_lighting_type": "metal_halide",
            "current_lighting_age_years": 14,
            "broadcast_requirements": "conference_network",
            "status": "scored",
            "tier": "A2",
            "icp_score": 63,
            "source": "manual",
        },
        # Illinois schools
        {
            "name": "University of Illinois",
            "venue_type": "college_d1",
            "state": "IL",
            "city": "Champaign",
            "conference": "Big Ten",
            "stadium_name": "Memorial Stadium",
            "seating_capacity": 60670,
            "primary_sport": "football",
            "current_lighting_type": "early_led",
            "current_lighting_age_years": 7,
            "broadcast_requirements": "espn",
            "status": "needs_scoring",
            "source": "manual",
        },
        {
            "name": "Naperville Central High School",
            "venue_type": "high_school_6a",
            "state": "IL",
            "city": "Naperville",
            "classification": "6A",
            "conference": "DuPage Valley Conference",
            "enrollment": 2800,
            "stadium_name": "North Central College Stadium",
            "seating_capacity": 5500,
            "primary_sport": "football",
            "current_lighting_type": "metal_halide",
            "current_lighting_age_years": 20,
            "broadcast_requirements": "none",
            "status": "identified",
            "source": "directory_import",
        },
    ]

    for prospect_data in prospects_data:
        existing = db.query(Prospect).filter(
            Prospect.name == prospect_data["name"]
        ).first()

        if not existing:
            prospect = Prospect(**prospect_data)
            db.add(prospect)
            db.flush()

    db.commit()
    print(f"Seeded {len(prospects_data)} sample prospects")


def seed_sample_contacts(db):
    """Add contacts to sample prospects."""
    # Get prospects
    mason = db.query(Prospect).filter(Prospect.name == "Mason High School").first()
    osu = db.query(Prospect).filter(Prospect.name == "Ohio State University").first()
    uc = db.query(Prospect).filter(Prospect.name == "University of Cincinnati").first()

    contacts_data = []

    if mason:
        contacts_data.extend([
            {
                "prospect_id": mason.id,
                "name": "John Smith",
                "title": "Athletic Director",
                "role": "decision_maker",
                "email": "jsmith@masonschools.org",
                "phone": "513-555-0123",
                "is_primary": True,
            },
            {
                "prospect_id": mason.id,
                "name": "Jane Doe",
                "title": "Facilities Director",
                "role": "influencer",
                "email": "jdoe@masonschools.org",
                "phone": "513-555-0124",
                "is_primary": False,
            },
        ])

    if osu:
        contacts_data.extend([
            {
                "prospect_id": osu.id,
                "name": "Gene Smith",
                "title": "Athletic Director",
                "role": "decision_maker",
                "email": "smith.7@osu.edu",
                "is_primary": True,
            },
        ])

    if uc:
        contacts_data.extend([
            {
                "prospect_id": uc.id,
                "name": "John Cunningham",
                "title": "Athletic Director",
                "role": "decision_maker",
                "email": "john.cunningham@uc.edu",
                "is_primary": True,
            },
        ])

    for contact_data in contacts_data:
        existing = db.query(Contact).filter(
            Contact.prospect_id == contact_data["prospect_id"],
            Contact.email == contact_data["email"]
        ).first()

        if not existing:
            contact = Contact(**contact_data)
            db.add(contact)

    db.commit()
    print(f"Seeded {len(contacts_data)} sample contacts")


def seed_sample_scores(db):
    """Add ICP scores to scored prospects."""
    mason = db.query(Prospect).filter(Prospect.name == "Mason High School").first()

    if mason and mason.tier:
        # Dimension weights from spec
        dimensions = [
            ("venue_type", 8, 3),
            ("geography", 10, 2),
            ("budget_signals", 6, 3),
            ("current_lighting_age", 8, 2),
            ("night_game_frequency", 10, 2),
            ("broadcast_requirements", 2, 2),
            ("decision_maker_access", 8, 2),
            ("project_timeline", 6, 3),
        ]

        for dimension, score, weight in dimensions:
            existing = db.query(ProspectScore).filter(
                ProspectScore.prospect_id == mason.id,
                ProspectScore.dimension == dimension
            ).first()

            if not existing:
                score_record = ProspectScore(
                    prospect_id=mason.id,
                    dimension=dimension,
                    score=score,
                    weight=weight,
                    scored_by="agent:hygiene",
                )
                db.add(score_record)

        db.commit()
        print("Seeded ICP scores for Mason High School")


def seed_sample_activities(db):
    """Add sample activities."""
    mason = db.query(Prospect).filter(Prospect.name == "Mason High School").first()

    if mason:
        activities = [
            {
                "prospect_id": mason.id,
                "type": "status_change",
                "description": "Created from state directory import",
                "agent_id": "prospector",
            },
            {
                "prospect_id": mason.id,
                "type": "score_change",
                "description": "Scored 67 (A2) by Hygiene Agent",
                "agent_id": "hygiene",
            },
            {
                "prospect_id": mason.id,
                "type": "research_completed",
                "description": "Research completed - Energy cost constraint identified",
                "agent_id": "researcher",
            },
        ]

        for i, activity_data in enumerate(activities):
            existing = db.query(Activity).filter(
                Activity.prospect_id == mason.id,
                Activity.description == activity_data["description"]
            ).first()

            if not existing:
                activity = Activity(
                    **activity_data,
                    created_at=datetime.utcnow() - timedelta(days=len(activities) - i)
                )
                db.add(activity)

        db.commit()
        print("Seeded sample activities")


def seed_sample_agent_runs(db):
    """Add sample agent runs."""
    runs_data = [
        {"agent_name": "prospector", "status": "completed", "records_processed": 50, "records_created": 12},
        {"agent_name": "hygiene", "status": "completed", "records_processed": 12, "records_updated": 8},
        {"agent_name": "researcher", "status": "completed", "records_processed": 5, "records_updated": 5},
        {"agent_name": "outreach", "status": "completed", "records_processed": 3, "records_created": 3},
        {"agent_name": "orchestrator", "status": "completed", "records_processed": 0},
    ]

    for run_data in runs_data:
        run = AgentRun(
            **run_data,
            trigger="scheduled",
            started_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
            completed_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 60)),
        )
        db.add(run)

    db.commit()
    print("Seeded sample agent runs")


def main():
    """Run all seed functions."""
    print("Initializing database...")
    init_db()

    print("Creating database session...")
    db = SessionLocal()

    try:
        print("\n--- Seeding Data ---\n")
        seed_outreach_templates(db)
        seed_sample_prospects(db)
        seed_sample_contacts(db)
        seed_sample_scores(db)
        seed_sample_activities(db)
        seed_sample_agent_runs(db)
        print("\n--- Seeding Complete ---\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
