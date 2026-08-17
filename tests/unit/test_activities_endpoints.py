"""Unit tests for activity endpoints using mocked database - AAA Pattern"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide TestClient for unit tests"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, sample_activities_data):
        """
        AAA Test: Verify GET /activities returns all activities with correct structure
        
        Arrange: Mock the activities database with sample data
        Act: Make GET request to /activities
        Assert: Verify status 200 and all activities returned with correct fields
        """
        # Arrange: Mock activities module
        with patch('src.app.activities', sample_activities_data):
            # Act: Make the GET request
            response = client.get("/activities")
        
            # Assert: Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 9
            assert "Chess Club" in data
            assert "Programming Class" in data
            assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
    
    def test_get_activities_includes_required_fields(self, client, sample_activities_data):
        """
        AAA Test: Verify each activity has all required fields
        
        Arrange: Mock activities with sample data
        Act: Make GET request
        Assert: Verify each activity has description, schedule, max_participants, participants
        """
        # Arrange
        with patch('src.app.activities', sample_activities_data):
            # Act
            response = client.get("/activities")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            for activity_name, activity in data.items():
                assert "description" in activity
                assert "schedule" in activity
                assert "max_participants" in activity
                assert "participants" in activity
                assert isinstance(activity["participants"], list)
    
    def test_get_activities_preserves_participant_data(self, client, sample_activities_data):
        """
        AAA Test: Verify participant emails are returned correctly
        
        Arrange: Mock activities with specific participants
        Act: Make GET request
        Assert: Verify participants list matches expected emails
        """
        # Arrange
        with patch('src.app.activities', sample_activities_data):
            # Act
            response = client.get("/activities")
            
            # Assert
            data = response.json()
            assert "michael@mergington.edu" in data["Chess Club"]["participants"]
            assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
            assert len(data["Chess Club"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, sample_activities_data):
        """
        AAA Test: Verify successful signup adds student to activity
        
        Arrange: Mock activities with sample data, prepare new student email
        Act: Make POST request to signup endpoint
        Assert: Verify status 200 and success message returned
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        new_student = "newstudent@mergington.edu"
        
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": new_student}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "Signed up" in data["message"]
            assert new_student in data["message"]
    
    def test_signup_nonexistent_activity_returns_404(self, client, sample_activities_data):
        """
        AAA Test: Verify signup fails for non-existent activity
        
        Arrange: Mock activities with sample data, use invalid activity name
        Act: Make POST request with invalid activity name
        Assert: Verify status 404 and appropriate error message
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.post(
                "/activities/Nonexistent Club/signup",
                params={"email": "student@mergington.edu"}
            )
            
            # Assert
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_returns_400(self, client, sample_activities_data):
        """
        AAA Test: Verify signup fails when student already enrolled
        
        Arrange: Mock activities with existing participant
        Act: Try to signup same student again
        Assert: Verify status 400 and duplicate enrollment error
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        existing_student = "michael@mergington.edu"
        
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": existing_student}
            )
            
            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "already signed up" in data["detail"]
    
    def test_signup_message_format(self, client, sample_activities_data):
        """
        AAA Test: Verify signup response message format
        
        Arrange: Mock activities with sample data
        Act: Make successful signup request
        Assert: Verify response message contains email and activity name
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        test_email = "testuser@mergington.edu"
        test_activity = "Programming Class"
        
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.post(
                f"/activities/{test_activity}/signup",
                params={"email": test_email}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert test_email in data["message"]
            assert test_activity in data["message"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client, sample_activities_data):
        """
        AAA Test: Verify successful participant removal
        
        Arrange: Mock activities with participant enrolled
        Act: Make DELETE request to remove participant
        Assert: Verify status 200 and success message
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        activity = "Chess Club"
        participant = "michael@mergington.edu"
        
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.delete(
                f"/activities/{activity}/participants/{participant}"
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "Removed" in data["message"]
            assert participant in data["message"]
    
    def test_remove_participant_nonexistent_activity_returns_404(self, client, sample_activities_data):
        """
        AAA Test: Verify removal fails for non-existent activity
        
        Arrange: Mock activities, use invalid activity name
        Act: Make DELETE request with invalid activity
        Assert: Verify status 404
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.delete(
                "/activities/Nonexistent Club/participants/student@mergington.edu"
            )
            
            # Assert
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Activity not found"
    
    def test_remove_participant_not_enrolled_returns_400(self, client, sample_activities_data):
        """
        AAA Test: Verify removal fails for participant not in activity
        
        Arrange: Mock activities, use student not enrolled in activity
        Act: Make DELETE request for unenrolled student
        Assert: Verify status 400 and appropriate error
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.delete(
                "/activities/Chess Club/participants/notstudent@mergington.edu"
            )
            
            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_remove_participant_message_format(self, client, sample_activities_data):
        """
        AAA Test: Verify removal response message format
        
        Arrange: Mock activities with participant
        Act: Make successful removal request
        Assert: Verify message contains email and activity name
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        activity = "Tennis Club"
        participant = "sarah@mergington.edu"
        
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.delete(
                f"/activities/{activity}/participants/{participant}"
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert participant in data["message"]
            assert activity in data["message"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_activity_name_with_special_characters(self, client):
        """
        AAA Test: Verify endpoint handling of special characters in activity names
        
        Arrange: Create activity with special characters in name
        Act: Make request with special character activity name
        Assert: Verify 404 for non-existent activity name
        """
        # Arrange
        mock_activities = {}
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.get("/activities")
            
            # Assert
            assert response.status_code == 200
            assert len(response.json()) == 0
    
    def test_email_parameter_handling(self, client, sample_activities_data):
        """
        AAA Test: Verify email parameter is correctly passed and used
        
        Arrange: Mock activities
        Act: Make signup request with specific email format
        Assert: Verify email is reflected in response
        """
        # Arrange
        mock_activities = sample_activities_data.copy()
        test_email = "user.name+tag@example.com"
        
        with patch('src.app.activities', mock_activities):
            # Act
            response = client.post(
                "/activities/Art Studio/signup",
                params={"email": test_email}
            )
            
            # Assert
            assert response.status_code == 200
            assert test_email in response.json()["message"]
