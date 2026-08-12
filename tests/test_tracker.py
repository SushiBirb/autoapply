import pytest
from autoapply.tracker.db import Application, ApplicationDB


def test_add_and_get_application(test_db: ApplicationDB):
    app = Application(
        company="CrowdStrike",
        title="Security Operations Intern",
        platform="linkedin_easyapply",
        channel="linkedin",
        url="https://linkedin.com/jobs/view/12345",
    )
    app_id = test_db.add(app)
    assert app_id == 1

    fetched = test_db.get(app_id)
    assert fetched is not None
    assert fetched.company == "CrowdStrike"
    assert fetched.title == "Security Operations Intern"
    assert fetched.status == "submitted"


def test_set_status_event(test_db: ApplicationDB):
    app = Application(company="Cloudflare", title="Network Engineering Intern")
    app_id = test_db.add(app)

    test_db.set_status(app_id, "interview", note="Scheduled technical interview")
    updated = test_db.get(app_id)
    assert updated.status == "interview"

    with pytest.raises(ValueError):
        test_db.set_status(app_id, "invalid_status_name")


def test_list_and_search_applications(test_db: ApplicationDB):
    test_db.add(Application(company="Cisco", title="Security Analyst", status="submitted"))
    test_db.add(Application(company="Palo Alto Networks", title="Cloud Security Intern", status="phone_screen"))
    test_db.add(Application(company="Cisco Systems", title="Network Systems Intern", status="interview"))

    all_apps = test_db.list()
    assert len(all_apps) == 3

    cisco_apps = test_db.list(company="cisco")
    assert len(cisco_apps) == 2

    phone_screen_apps = test_db.list(status="phone_screen")
    assert len(phone_screen_apps) == 1
    assert phone_screen_apps[0].company == "Palo Alto Networks"

    search_res = test_db.search("analyst")
    assert len(search_res) == 1
    assert search_res[0].company == "Cisco"


def test_stats_metrics(test_db: ApplicationDB):
    assert test_db.stats()["total"] == 0

    test_db.add(Application(company="CompA", title="RoleA", status="submitted"))
    test_db.add(Application(company="CompB", title="RoleB", status="phone_screen"))
    test_db.add(Application(company="CompC", title="RoleC", status="interview"))
    test_db.add(Application(company="CompD", title="RoleD", status="offer"))

    stats = test_db.stats()
    assert stats["total"] == 4
    assert stats["responses"] == 3
    assert stats["offers"] == 1
    assert stats["response_rate"] == 0.75
    assert stats["offer_rate"] == 0.25


def test_portal_credentials_creation_and_export(test_db: ApplicationDB, tmp_path):
    cred1 = test_db.get_or_create_credential(company="Workday / Workday Jobs", domain="workday.com", email="jmattingly@proitserv.com")
    assert cred1["email"] == "jmattingly@proitserv.com"
    assert cred1["password"].startswith("App!")

    # Same domain should return same password
    cred2 = test_db.get_or_create_credential(company="Workday Jobs", domain="workday.com", email="jmattingly@proitserv.com")
    assert cred2["password"] == cred1["password"]

    all_creds = test_db.list_credentials()
    assert len(all_creds) == 1
    assert all_creds[0]["company"] == "Workday / Workday Jobs"

    txt_file = test_db.export_credentials_file()
    assert txt_file.exists()
    assert "workday.com" in txt_file.read_text()
