import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_get_activities_contains_activity_details(self):
        """Test that each activity contains required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_for_nonexistent_activity(self):
        """Test signup for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_duplicate_student(self):
        """Test that duplicate signup returns 400 error"""
        # Sign up once
        client.post("/activities/Chess Club/signup?email=duplicate@mergington.edu")
        
        # Try to sign up again
        response = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_updates_participant_list(self):
        """Test that signup actually adds participant to the list"""
        email = "participant@mergington.edu"
        
        # Get initial state
        response = client.get("/activities")
        initial_participants = response.json()["Tennis Club"]["participants"].copy()
        
        # Sign up
        client.post(f"/activities/Tennis Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        updated_participants = response.json()["Tennis Club"]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "student@mergington.edu"
        activity = "Art Studio"
        
        # First sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_not_signed_up_student(self):
        """Test unregister of student not signed up returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=nosignup@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes participant from list"""
        email = "remove_me@mergington.edu"
        activity = "Basketball Team"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
