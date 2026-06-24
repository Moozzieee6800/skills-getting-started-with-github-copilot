import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module

client = TestClient(app_module.app)
INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    app_module.activities = copy.deepcopy(INITIAL_ACTIVITIES)
    yield
    app_module.activities = copy.deepcopy(INITIAL_ACTIVITIES)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"].endswith("/static/index.html")


def test_get_activities_returns_all_activities():
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
    assert "participants" in data["Chess Club"]
    assert "michael@mergington.edu" in data["Chess Club"]["participants"]


def test_signup_creates_new_participant():
    activity_name = quote("Chess Club", safe="")
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={quote(email, safe='')}" )
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"

    activities_response = client.get("/activities").json()
    assert email in activities_response["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    activity_name = quote("Chess Club", safe="")
    email = "michael@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={quote(email, safe='')}" )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_delete_participant_removes_entry():
    activity_name = quote("Chess Club", safe="")
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants?email={quote(email, safe='')}" )
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Chess Club"

    activities_response = client.get("/activities").json()
    assert email not in activities_response["Chess Club"]["participants"]


def test_delete_missing_participant_returns_404():
    activity_name = quote("Chess Club", safe="")
    email = "doesnotexist@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants?email={quote(email, safe='')}" )
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
