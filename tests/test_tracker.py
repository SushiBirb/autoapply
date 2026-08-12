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

    s = test_db.stats()
    assert s["total"] == 4
    assert s["responses"] == 3  # phone_screen, interview, offer
    assert s["offers"] == 1
    assert s["response_rate"] == 0.75
    assert s["offer_rate"] == 0.25
