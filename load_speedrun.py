import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "startups.db"
TABLE_NAME = "startups"

companies = [
  {"name": "2weeks", "cohort": "003", "location": "New York, New York", "tags": ["GAMES STUDIO"], "description": "Making breakout hits on the open web for you and your friends."},
  {"name": "Acceler8", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI for Workforce Intelligence & Planning"},
  {"name": "Advocate", "cohort": "006", "location": "New York, New York", "tags": ["AI", "HEALTHCARE", "B2B"], "description": "The AI-native system for easy & reimbursable care coordination."},
  {"name": "Adzap", "cohort": "003", "location": "Los Angeles, California", "tags": ["DEVELOPER TOOLS", "AI", "ADVERTISING/MARKETING"], "description": "Mobile-grade performance and attribution solution for PC/Console games"},
  {"name": "Agent Astra", "cohort": "005", "location": "New York, New York", "tags": ["AI"], "description": "We are building the AI-native UPS"},
  {"name": "Aghanim", "cohort": "002", "location": "Los Angeles, California", "tags": ["AI", "FINTECH", "B2B"], "description": "Integrated commerce, live-ops automation, community engagement, and payments platform for mobile games."},
  {"name": "Alike", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "DEEP TECH", "B2B"], "description": "The Agent Collaboration Layer for Enterprises"},
  {"name": "Alpaka Games", "cohort": "004", "location": "Istanbul, Turkey", "tags": ["GAMES STUDIO"], "description": "Creating the next generation of hit Action mobile games"},
  {"name": "Ambiguous", "cohort": "005", "location": "Bellevue, Washington", "tags": ["AI", "B2B"], "description": "AI coworkers that work like teammates."},
  {"name": "Amdahl", "cohort": "006", "location": "San Francisco, California", "tags": ["ADVERTISING/MARKETING", "B2B", "AI"], "description": "AI Context layer for all Enterprise GTM work"},
  {"name": "Anchr", "cohort": "005", "location": "New York City, New York", "tags": ["AI", "B2B"], "description": "The AI Operating System For Food Distributors"},
  {"name": "AndThen", "cohort": "005", "location": "Los Angeles, California", "tags": ["AI", "MEDIA/ANIMATION"], "description": "Voice-first platform that makes conversations with AI characters something you do."},
  {"name": "Antihero Studios", "cohort": "006", "location": "Barcelona, Spain", "tags": ["GAMES STUDIO"], "description": "Creating Games Worth Sharing."},
  {"name": "Argu", "cohort": "005", "location": "Israel", "tags": ["AI", "DEFENSE TECH"], "description": "Create Vision Agents to monitor any scenario in real-time video from CCTV."},
  {"name": "Artifact", "cohort": "005", "location": "New York, New York", "tags": ["AI", "FINTECH"], "description": "System of intelligence for accounting"},
  {"name": "Atorie", "cohort": "004", "location": "Los Angeles, California", "tags": ["AI", "MARKETPLACE"], "description": "Luxury Without the Price Tag"},
  {"name": "August", "cohort": "006", "location": "Tel Aviv, Israel", "tags": ["AI", "FINTECH", "B2B"], "description": "AI autonomous bankers"},
  {"name": "Auto", "cohort": "006", "location": "Los Angeles, California", "tags": ["AI"], "description": "AI camera that turns photos into personal apps."},
  {"name": "Autonomous Investing", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "FINTECH"], "description": "Building a superhuman AI investor"},
  {"name": "Avenir AI", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "HEALTHCARE", "B2B"], "description": "AI Agents for Employee Benefits"},
  {"name": "Axon", "cohort": "005", "location": "London, United Kingdom", "tags": ["AI", "FINTECH"], "description": "DeepMind for Finance"},
  {"name": "Azimov", "cohort": "005", "location": "San Francisco, California", "tags": ["AI"], "description": "An engine to bring AI to life"},
  {"name": "Bead AI", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI agents for Internal Audit teams"},
  {"name": "Belong", "cohort": "006", "location": "New York, New York", "tags": ["SOCIAL NETWORKING", "FINTECH"], "description": "Financial infrastructure of fandom."},
  {"name": "Bilrost", "cohort": "006", "location": "Oakland, California", "tags": ["AI", "FINTECH", "B2B"], "description": "Bilrost automates the most complicated commercial loan processing."},
  {"name": "Bota", "cohort": "006", "location": "Mountain View, California", "tags": ["AI", "DEVELOPER TOOLS", "B2B"], "description": "Bridging AI agents and the real world"},
  {"name": "BotBot", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "Aligning AI to brand and outcomes"},
  {"name": "Brief", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "DEVELOPER TOOLS", "B2B"], "description": "The AI Chief Product Officer"},
  {"name": "Cascade", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI for construction wins."},
  {"name": "Cedar", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "SOCIAL NETWORKING", "B2B"], "description": "Killing LinkedIn with Agents"},
  {"name": "Checkmate", "cohort": "004", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "Building AI-native Vertical SaaS"},
  {"name": "Clair Health", "cohort": "006", "location": "Mountain View, California", "tags": ["HEALTHCARE", "DEEP TECH"], "description": "Building the first continuous hormone monitor."},
  {"name": "Coalition Systems", "cohort": "006", "location": "San Francisco, California", "tags": ["DEFENSE TECH", "AI"], "description": "AI coordination software for allied defense."},
  {"name": "Concorda", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI operating system for trial lawyers"},
  {"name": "Crebit", "cohort": "006", "location": "San Francisco, California", "tags": ["FINTECH"], "description": "Rate-locking for stablecoin FX."},
  {"name": "Dex", "cohort": "005", "location": "London, United Kingdom", "tags": ["AI", "MARKETPLACE", "B2B"], "description": "The AI tech recruiter that finds the most motivated candidates"},
  {"name": "Dispatcher", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "ROBOTICS"], "description": "Agentic Interface for Drones and Robotics"},
  {"name": "Doublespeed", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "ADVERTISING/MARKETING"], "description": "Automating Attention - Synthetic Creator Infrastructure"},
  {"name": "Emanate", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "The First AI Revenue Engine Built for the Physical Economy."},
  {"name": "Endo Health", "cohort": "003", "location": "San Francisco, California", "tags": ["HEALTHCARE", "AI"], "description": "Building the first AI clinic for weight loss"},
  {"name": "EverCurrent", "cohort": "005", "location": "Oakland, California", "tags": ["AI", "DEEP TECH", "B2B"], "description": "Making the miracles of hardware development repeatable"},
  {"name": "Ezra AI Labs", "cohort": "005", "location": "Lafayette, California", "tags": ["AI", "B2B"], "description": "Ezra supercharges talent teams with AI voice interviewer"},
  {"name": "Fearn", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "Secure patents for everyone."},
  {"name": "Figment", "cohort": "004", "location": "San Francisco, California", "tags": ["AI", "CREATIVE TOOLS"], "description": "End to end ecosystem for telling infinite generative stories."},
  {"name": "General Magic", "cohort": "005", "location": "Toronto, Canada", "tags": ["AI", "B2B", "FINTECH"], "description": "SMS based AI agents for insurance workflows"},
  {"name": "Genway AI", "cohort": "004", "location": "San Francisco, California", "tags": ["AI", "B2B", "DEVELOPER TOOLS"], "description": "Conversational AI Agents for User Interviews"},
  {"name": "Ghosted", "cohort": "004", "location": "London, United Kingdom", "tags": ["SOCIAL NETWORKING", "DATING", "AI"], "description": "A no-filter dating app for GenZ."},
  {"name": "Grove Tax", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "FINTECH", "B2B"], "description": "AI Workforce for Tax Firms"},
  {"name": "Hammock", "cohort": "006", "location": "Brooklyn, New York", "tags": ["AI", "FINTECH", "HEALTHCARE"], "description": "The only HSA/FSA agent that saves you money."},
  {"name": "Heavi", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "MARKETPLACE", "B2B"], "description": "AI workforce for heavy vehicle mechanics."},
  {"name": "Hedra", "cohort": "002", "location": "San Francisco, California", "tags": ["MEDIA/ANIMATION", "AI"], "description": "A generative media company building the AI-native creation platform."},
  {"name": "Hotbox", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "ADVERTISING/MARKETING"], "description": "Predictive intelligence for social commerce"},
  {"name": "Human Computer", "cohort": "003", "location": "Bay Area, California", "tags": ["GAMES STUDIO", "AI"], "description": "Building the world's greatest triple-I game studio."},
  {"name": "Idilio", "cohort": "006", "location": "Bogota, Colombia", "tags": ["MEDIA/ANIMATION"], "description": "The future of serialized storytelling."},
  {"name": "Jigsaw", "cohort": "005", "location": "Los Angeles, California", "tags": ["AI", "DEEP TECH", "B2B"], "description": "Applied research lab scaling RL environments to accelerate superintelligence."},
  {"name": "Jooba", "cohort": "005", "location": "Los Angeles, California", "tags": ["AI", "B2B", "MARKETPLACE"], "description": "The world's first autonomous recruiting firm"},
  {"name": "Kaaro", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI Agents for Railways."},
  {"name": "Kanu AI", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B", "DEVELOPER TOOLS"], "description": "Your AI Cloud Engineer"},
  {"name": "Kintow", "cohort": "005", "location": "New York, New York", "tags": ["AI", "B2B"], "description": "The AI copilot for modern restaurants."},
  {"name": "Layerpath", "cohort": "004", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI that closes the gap between product explanation and navigation."},
  {"name": "Limy AI", "cohort": "005", "location": "New York, New York", "tags": ["AI", "ADVERTISING/MARKETING", "B2B"], "description": "Limy puts brands in control of agent interactions in the agentic web."},
  {"name": "Loan Labs", "cohort": "005", "location": "Los Angeles, California", "tags": ["AI", "FINTECH", "B2B"], "description": "Agentic workers for mortgage companies."},
  {"name": "Logical Health", "cohort": "005", "location": "Palo Alto, California", "tags": ["HEALTHCARE", "AI", "B2B"], "description": "Bringing transparency to health insurance"},
  {"name": "Loops AI", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "Agentic AI for commerce"},
  {"name": "Maniac", "cohort": "005", "location": "San Francisco, California", "tags": ["DEVELOPER TOOLS", "DEEP TECH", "AI"], "description": "Pareto-Optimal AI at Scale, for Enterprise Intelligence."},
  {"name": "Manifest", "cohort": "003", "location": "New York, New York", "tags": ["AI", "HEALTHCARE"], "description": "Gen Z mental health platform."},
  {"name": "Mara", "cohort": "004", "location": "San Francisco, California", "tags": ["ROBOTICS", "AI", "DEFENSE TECH"], "description": "Building a horde of tactical robots. Starting with Spike: a swarming anti-drone system."},
  {"name": "Margin", "cohort": "005", "location": "New York, New York", "tags": ["AI", "FINTECH"], "description": "The world's first AI powered credit card."},
  {"name": "Mercury", "cohort": "006", "location": "New York, New York", "tags": ["CREATIVE TOOLS", "AI", "B2B"], "description": "Figma for AI Agents."},
  {"name": "Meridian", "cohort": "006", "location": "San Francisco, California", "tags": ["B2B", "AI"], "description": "AI operating system for consulting firms"},
  {"name": "Metal", "cohort": "005", "location": "Los Angeles, California", "tags": ["AI", "B2B"], "description": "Super intelligence for fundraising"},
  {"name": "Miraka", "cohort": "006", "location": "New York, New York", "tags": ["HEALTHCARE", "AI"], "description": "The AI-Powered Cardiac Care Team"},
  {"name": "Mirror Mirror AI", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "MARKETPLACE"], "description": "The marketplace for licensing likeness for content & usage."},
  {"name": "Modaic", "cohort": "006", "location": "San Francisco, California", "tags": ["AI"], "description": "Alignment for AI decisions."},
  {"name": "Modern Industrials", "cohort": "006", "location": "New York, New York", "tags": ["AI", "B2B"], "description": "The AI Workforce for Building Materials Distribution."},
  {"name": "Moona Health", "cohort": "005", "location": "San Francisco, California", "tags": ["HEALTHCARE", "AI", "MARKETPLACE"], "description": "AI-powered sleep care, covered by insurance."},
  {"name": "Nexad", "cohort": "004", "location": "San Francisco, California", "tags": ["AI", "ADVERTISING/MARKETING"], "description": "Native ads system for AI apps"},
  {"name": "Nexxa.ai", "cohort": "005", "location": "Sunnyvale, California", "tags": ["AI", "DEEP TECH"], "description": "Specialized AI for Heavy Industries"},
  {"name": "NoMi", "cohort": "003", "location": "London, United Kingdom", "tags": ["HEALTHCARE", "AI"], "description": "Gives you the end result of therapy through a game."},
  {"name": "Oasiz", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "SOCIAL NETWORKING"], "description": "TikTok for AI-native software."},
  {"name": "Ocoder", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI-powered dev environment for designers and PMs"},
  {"name": "Oleum", "cohort": "005", "location": "New York City, New York", "tags": ["AI", "FINTECH", "B2B"], "description": "An AI platform that helps companies utilize data faster"},
  {"name": "Omi Health", "cohort": "006", "location": "New York, New York", "tags": ["HEALTHCARE", "AI"], "description": "Function Health for Pets."},
  {"name": "Panorama", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "Enterprise AI workflow enablement"},
  {"name": "PartyHat", "cohort": "006", "location": "San Francisco, California", "tags": ["AI"], "description": "Disrupting consumer cybersecurity"},
  {"name": "PayPath", "cohort": "006", "location": "New York, New York", "tags": ["AI", "FINTECH", "B2B"], "description": "The AI Operating System Powering Modern Debt."},
  {"name": "Pelago", "cohort": "005", "location": "Los Angeles, California", "tags": ["AI", "FITNESS", "HEALTHCARE"], "description": "Voice-First AI apps that deliver real life wellness outcomes"},
  {"name": "PicPet", "cohort": "006", "location": "San Francisco, California", "tags": ["SOCIAL NETWORKING"], "description": "Social messaging platform where friendships feed virtual pets."},
  {"name": "Piper-ai", "cohort": "006", "location": "San Francisco, California", "tags": ["B2B", "AI"], "description": "The AI workforce for construction."},
  {"name": "Pluvo", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI Decision Engine for Modern Enterprise."},
  {"name": "Prepp", "cohort": "005", "location": "Chicago, Illinois", "tags": ["AI", "EDTECH"], "description": "Reimagining global EdTech."},
  {"name": "Presia", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI agents for management consulting."},
  {"name": "Prior Foundry", "cohort": "006", "location": "San Francisco, California", "tags": ["AI"], "description": "Simulate how entire populations respond to decisions before they're made."},
  {"name": "Quanto", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "FINTECH"], "description": "AI Workforce for Accounting Firms"},
  {"name": "Quinn", "cohort": "006", "location": "New York, New York", "tags": ["B2B", "AI"], "description": "Building for the 2.7B frontline workforce"},
  {"name": "Quo Labs", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "HEALTHCARE", "ROBOTICS"], "description": "AI caretaker for seniors"},
  {"name": "Rehearsals", "cohort": "004", "location": "New York, New York", "tags": ["AI", "B2B", "ADVERTISING/MARKETING"], "description": "AI digital twins reveal what your market wants in minutes."},
  {"name": "Rork", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "CREATIVE TOOLS", "DEVELOPER TOOLS"], "description": "Turn your ideas into real mobile apps in minutes"},
  {"name": "SafeWorld", "cohort": "006", "location": "Palo Alto, California", "tags": ["AI", "ROBOTICS"], "description": "Making robots safe"},
  {"name": "Schemata", "cohort": "003", "location": "San Francisco, California", "tags": ["AI", "DEFENSE TECH", "B2B"], "description": "Virtual Training and Simulation for Defense and Enterprise"},
  {"name": "Sellara", "cohort": "006", "location": "New York, New York", "tags": ["FINTECH", "AI", "B2B"], "description": "Applied AI For Institutional Trading & Operations"},
  {"name": "Sentra", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "The foundational memory for Enterprise General Intelligence."},
  {"name": "Simula", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "ADVERTISING/MARKETING", "B2B"], "description": "Living AI native ad infrastructure"},
  {"name": "Sirius Technology", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI Retention Platform for Subscription Companies."},
  {"name": "Smart Bricks", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "FINTECH"], "description": "Applied AI Lab for Real Estate."},
  {"name": "Snapp Stats", "cohort": "006", "location": "San Francisco, California", "tags": ["AI"], "description": "24/7 AI Agent for Sports."},
  {"name": "Sonatic", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "An interface for to-do to done in seconds!"},
  {"name": "Sourcerer", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "Building the autonomous supply chain"},
  {"name": "Sparta", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "DEEP TECH"], "description": "Adaptive data transfer optimization for high-performance infrastructure."},
  {"name": "Straia", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "EDTECH", "B2B"], "description": "The agentic AI platform for higher education"},
  {"name": "SUN", "cohort": "006", "location": "Palo Alto, California", "tags": ["AI"], "description": "Personalized AI audio."},
  {"name": "SuperGaming", "cohort": "001", "location": "Pune, India", "tags": ["GAMES STUDIO", "DEVELOPER TOOLS"], "description": "Building India's Gaming Revolution"},
  {"name": "Syncere", "cohort": "006", "location": "Palo Alto, California", "tags": ["ROBOTICS"], "description": "Robot lamps that do your chores."},
  {"name": "Taxnova", "cohort": "006", "location": "San Francisco, California", "tags": ["AI", "B2B"], "description": "AI infrastructure to streamline the R&D tax market"},
  {"name": "Taya", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "SOCIAL NETWORKING", "DEEP TECH"], "description": "AI you'll actually want to wear"},
  {"name": "Third Space", "cohort": "006", "location": "Brooklyn, New York", "tags": ["AI", "FINTECH", "B2B"], "description": "Verticalized AI-native insurance broker for IRL businesses."},
  {"name": "Thirdbrain Labs", "cohort": "006", "location": "San Francisco, California", "tags": ["ROBOTICS", "AI", "B2B"], "description": "Unlocking the next one billion specialized models"},
  {"name": "URSA Mining", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "DEEP TECH", "ROBOTICS"], "description": "Making autonomous mines a reality."},
  {"name": "VariantNow", "cohort": "006", "location": "Tel Aviv, Israel", "tags": ["AI", "B2B", "ADVERTISING/MARKETING"], "description": "AI Infrastructure for the Adaptive Web."},
  {"name": "Vereda", "cohort": "006", "location": "Rio Verde, Brazil", "tags": ["AI", "MARKETPLACE", "FINTECH"], "description": "The AI procurement agent for agriculture."},
  {"name": "Zingroll", "cohort": "005", "location": "San Francisco, California", "tags": ["AI", "MEDIA/ANIMATION"], "description": "World's largest Netflix-quality AI streaming platform"},
  {"name": "ZeroDrift", "cohort": "006", "location": "New York, New York", "tags": ["AI", "FINTECH"], "description": "ZeroDrift makes every message compliant before it's sent."},
]

def get_country(loc):
    us_states = ["California", "New York", "Texas", "Washington", "Massachusetts", "Illinois", "Colorado", "Florida", "Pennsylvania", "Tennessee", "Michigan", "North Carolina", "Rhode Island", "Delaware", "Ohio", "Kansas", "Connecticut"]
    for state in us_states:
        if state in loc:
            return "USA"
    country_map = {"United Kingdom": "UK", "Israel": "Israel", "Turkey": "Turkey", "Canada": "Canada", "Spain": "Spain", "Colombia": "Colombia", "Brazil": "Brazil", "India": "India", "Australia": "Australia", "Singapore": "Singapore", "Sweden": "Sweden", "Finland": "Finland"}
    for k, v in country_map.items():
        if k in loc:
            return v
    return "USA"

today = datetime.now().strftime('%Y-%m-%d')
records = []
for c in companies:
    records.append({
        'date': today,
        'company': c['name'],
        'sector': ', '.join(c['tags']) if c['tags'] else 'Technology',
        'tags': ', '.join(c['tags']) if c['tags'] else 'Technology',
        'description': c['description'],
        'location': c['location'],
        'stage': 'Pre-Seed/Seed',
        'amount': 'Up to $1M',
        'country': get_country(c['location']),
        'source': 'a16z Speedrun',
        'lead_notable_investors': f'a16z Speedrun Cohort {c["cohort"]}'
    })

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE source='a16z Speedrun'")
print(f"Cleared existing Speedrun entries.")
df = pd.DataFrame(records)
df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
conn.close()
print(f"Inserted {len(df)} Speedrun companies.")
