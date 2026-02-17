"""
Tests for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test to ensure clean state"""
    # Reset to initial state
    activities.clear()
    activities.update({
        "Basketball": {
            "description": "Play competitive basketball and improve your skills",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Soccer": {
            "description": "Join the soccer team and compete in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
            "participants": ["alex@mergington.edu", "isabella@mergington.edu"]
        },
        "Debate Club": {
            "description": "Develop critical thinking and public speaking skills through debates",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["liam@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
    })
    yield
    activities.clear()


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball" in data
        assert "Soccer" in data
        assert "Debate Club" in data
        assert "Chess Club" in data

    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        basketball = data["Basketball"]
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball

    def test_get_activities_shows_participants(self, client):
        """Test that participants are included in activities"""
        response = client.get("/activities")
        data = response.json()
        assert "james@mergington.edu" in data["Basketball"]["participants"]
        assert len(data["Soccer"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """Test successful signup of a new participant"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        assert "newstudent@mergington.edu" in activities_response.json()["Basketball"]["participants"]

    def test_signup_duplicate_participant_rejected(self, client):
        """Test that duplicate signups are rejected"""
        # Try to signup someone already registered
        response = client.post(
            "/activities/Basketball/signup?email=james@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        # Sign up for Basketball
        response1 = client.post(
            "/activities/Basketball/signup?email=multijoiner@mergington.edu"
        )
        assert response1.status_code == 200

        # Sign up for Soccer
        response2 = client.post(
            "/activities/Soccer/signup?email=multijoiner@mergington.edu"
        )
        assert response2.status_code == 200

        # Verify both signups
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert "multijoiner@mergington.edu" in data["Basketball"]["participants"]
        assert "multijoiner@mergington.edu" in data["Soccer"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """Test successful unregistration of an existing participant"""
        response = client.delete(
            "/activities/Basketball/signup?email=james@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        assert "james@mergington.edu" not in activities_response.json()["Basketball"]["participants"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a non-existent participant fails"""
        response = client.delete(
            "/activities/Basketball/signup?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test that unregistering from a non-existent activity fails"""
        response = client.delete(
            "/activities/NonexistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_and_reregister(self, client):
        """Test that unregistered participants can sign up again"""
        email = "james@mergington.edu"
        
        # Verify they're already registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Basketball"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/Basketball/signup?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify they're unregistered
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Basketball"]["participants"]
        
        # Re-register
        signup_response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify they're registered again
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Basketball"]["participants"]
