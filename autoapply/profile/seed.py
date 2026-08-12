from __future__ import annotations

from .schema import empty_profile

RESUME_SEED = {
    "identity": {
        "legal_first": "Joshua",
        "legal_last": "Mattingly",
        "preferred_name": "Josh",
        "email": "jmattingly@proitserv.com",
        "phone": "(502) 309-1990",
        "address": {
            "city": "Louisville",
            "state": "KY",
            "country": "USA",
        },
        "linkedin_url": "https://linkedin.com/in/joshua-mattingly-39145721b",
        "github_url": "https://github.com/SushiBirb",
    },
    "work_authorization": {
        "security_clearance": "none",
        "willing_background_check": True,
        "willing_drug_test": True,
    },
    "education": [
        {
            "institution": "University of Louisville",
            "degree": "B.S. (in progress)",
            "major": "",
            "gpa": "",
            "start_date": "2025",
            "end_date": "Spring 2029",
            "location": "Louisville, KY",
        },
        {
            "institution": "Eastern High School",
            "degree": "High School Diploma (Nationally Accredited IT Security Program)",
            "major": "IT Security",
            "start_date": "",
            "end_date": "2025",
            "location": "Louisville, KY",
        },
    ],
    "experience": [
        {
            "company": "Self-employed",
            "title": "Java APCSA Tutor",
            "employment_type": "part-time",
            "location": "Louisville, KY",
            "start_date": "May 2026",
            "end_date": "Present",
            "bullets": [
                "Tutor students in AP Computer Science A (Java).",
            ],
        },
        {
            "company": "Freelance",
            "title": "IT Assistant",
            "employment_type": "contract",
            "location": "Louisville, KY",
            "start_date": "2020",
            "end_date": "2024",
            "bullets": [
                "Provided freelance IT support for local clients.",
            ],
        },
    ],
    "skills": [
        {"name": "TCP/IP networking", "years": "3", "proficiency": "intermediate"},
        {"name": "DNS/DHCP/VLANs", "years": "3", "proficiency": "intermediate"},
        {"name": "pfSense firewalls", "years": "2", "proficiency": "intermediate"},
        {"name": "Cisco IOS", "years": "2", "proficiency": "intermediate"},
        {"name": "Active Directory / GPO", "years": "2", "proficiency": "intermediate"},
        {"name": "VPNs", "years": "2", "proficiency": "intermediate"},
        {"name": "Wireshark", "years": "3", "proficiency": "intermediate"},
        {"name": "Nmap", "years": "3", "proficiency": "intermediate"},
        {"name": "TrueNAS", "years": "2", "proficiency": "intermediate"},
        {"name": "Hyper-V", "years": "2", "proficiency": "intermediate"},
        {"name": "VMware", "years": "2", "proficiency": "intermediate"},
        {"name": "Linux (Ubuntu, Arch)", "years": "4", "proficiency": "advanced"},
        {"name": "Python", "years": "4", "proficiency": "advanced"},
        {"name": "Java", "years": "4", "proficiency": "advanced"},
        {"name": "C++", "years": "2", "proficiency": "intermediate"},
        {"name": "Bash", "years": "4", "proficiency": "advanced"},
        {"name": "SQL", "years": "2", "proficiency": "intermediate"},
        {"name": "Git/GitHub", "years": "4", "proficiency": "advanced"},
    ],
    "projects": [
        {
            "name": "autoapply (Local-First Application Automation System)",
            "role": "Developer",
            "dates": "2026",
            "bullets": [
                "Architected a Python CLI tool using Playwright browser automation and Google Gemini AI for automated form filling with human-in-the-loop review.",
                "Integrated Google Gemini AI SDK via OAuth 2.0 / ADC to generate candidate screening responses based on resume context.",
                "Implemented embedded SQLite tracking database with conversion metrics and encrypted file permissions (0o600).",
            ],
        },
        {
            "name": "Enterprise Network Simulation (Home Lab)",
            "dates": "2024 - 2025",
            "bullets": [
                "Designed and deployed a physical server rack simulating a corporate network with Cisco switching and pfSense routing.",
                "Managed Windows Server 2019 AD Domain Controller enforcing GPOs for password complexity and network filtering.",
                "Administered a hypervisor with 10+ VMs for testing network isolation, plus a TrueNAS server for centralized storage.",
            ],
        },
        {
            "name": "FlyAway (Badge Tracking System) for JCPS",
            "role": "Co-Developer",
            "bullets": [
                "Built full-stack Java/MySQL badge scanning proof of concept for Jefferson County Public Schools.",
                "Maintained a security-patched fork resolving vulnerabilities (github.com/SushiBirb/FlyAway).",
                "Awarded 1st Place at KY Technology Student Association (TSA).",
            ],
        },
        {
            "name": "HyprWpE (Linux Wayland Wallpaper Engine)",
            "role": "Co-Developer",
            "bullets": [
                "Architected a GTK4 wallpaper management tool for Hyprland using native Wayland tools (mpvpaper, WebKitGTK).",
            ],
        },
    ],
    "preferences": {
        "target_roles": [
            "InfoSec Intern / Co-op / Associate",
            "Network Engineering Intern / Co-op / Associate",
            "Cybersecurity Intern / Co-op / Associate",
            "IT Security Specialist",
            "Security Operations Center (SOC) Analyst",
        ],
        "remote_preference": "open",
        "willing_relocate": True,
    },
    "screening_answers": {
        "tell_me_about_yourself_short": "",
        "notice_period": "immediate / open for Summer Co-op, Internship, or Full-Time positions",
    },
    "meta": {
        "version": 1,
        "target_season": "Summer Co-op / Internship / Full-Time Entry-Level",
    },
}

CERTIFICATIONS = [
    "CompTIA Security+",
    "CompTIA A+",
    "TestOut Network Pro",
    "TestOut Security Pro",
]

AWARDS = [
    "FBLA National Competitor (2024); 1st Place State Networking Infrastructures (2025); 3rd in MIS (2024).",
    "TSA Co-Founder; 1st Place State Software Development (2025).",
    "YMCA Student Y Club: active in KYA/KUNA civic discussions and parliamentary procedure.",
]


def seeded_profile():
    profile = empty_profile()

    def deep_merge(base, seed):
        for key, value in seed.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                deep_merge(base[key], value)
            else:
                base[key] = value

    deep_merge(profile, RESUME_SEED)
    profile["certifications"] = list(CERTIFICATIONS)
    profile["awards"] = list(AWARDS)
    return profile
