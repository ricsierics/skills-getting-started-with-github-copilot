"""Integration tests for activity endpoints against live app - AAA Pattern"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide TestClient for integration tests"""
    return TestClient(app)


class TestGetActivitiesIntegration:
    """Integration tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_nine_activities(self, client, clean_activities):
        """
        AAA Test: Verify GET /activities returns all 9 activities from live database
        
        Arrange: Use clean app state with 9 pre-populated activities
        Act: Make GET request to /activities
        Assert: Verify 200 status and exactly 9 activities returned
        """
        # Arrange: clean_activities fixture resets state
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Art Studio", "Drama Club", "Robotics Club", "Debate Team"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_returns_complete_activity_data(self, client, clean_activities, sample_activities_data):
        """
        AAA Test: Verify activity data structure and content matches expected format
        
        Arrange: Use clean app state
        Act: Make GET request
        Assert: Verify each activity has correct structure and initial participants
        """
        # Arrange: clean_activities ensures reset state
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify Chess Club details
        chess = data["Chess Club"]
        assert chess["description"] == sample_activities_data["Chess Club"]["description"]
        assert chess["schedule"] == sample_activities_data["Chess Club"]["schedule"]
        assert chess["max_participants"] == 12
        assert len(chess["participants"]) == 2
        assert "michael@mergington.edu" in chess["participants"]
    
    def test_get_activities_participant_counts_accurate(self, client, clean_activities):
        """
        AAA Test: Verify participant counts match pre-populated data
        
        Arrange: Use clean app state with known participant counts
        Act: Make GET request
        Assert: Verify each activity has expected number of participants
        """
        # Arrange
        expected_counts = {
            "Chess Club": 2,
            "Programming Class": 2,
            "Gym Class": 2,
            "Basketball Team": 1,
            "Tennis Club": 2,
            "Art Studio": 1,
            "Drama Club": 2,
            "Robotics Club": 1,
            "Debate Team": 2
        }
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity_name, expected_count in expected_counts.items():
            actual_count = len(data[activity_name]["participants"])
            assert actual_count == expected_count


class TestSignupIntegration:
    """Integration tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_adds_participant_to_activity(self, client, clean_activities):
        """
        AAA Test: Verify signup successfully adds new participant to activity
        
        Arrange: Use clean app state, get initial participant count
        Act: Make signup request for new student
        Assert: Verify 200 status and participant added to activity
        """
        # Arrange
        new_student = "newsignup@mergington.edu"
        activity_name = "Chess Club"
        
        # Act: Sign up student
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_student}
        )
        
        # Assert: Verify signup response
        assert response.status_code == 200
        assert new_student in response.json()["message"]
        
        # Assert: Verify student appears in activity
        get_response = client.get("/activities")
        assert new_student in get_response.json()[activity_name]["participants"]
    
    def test_signup_persists_across_requests(self, client, clean_activities):
        """
        AAA Test: Verify signup state persists across multiple GET requests
        
        Arrange: Use clean app state
        Act: Sign up student, make multiple GET requests
        Assert: Verify student remains enrolled across all requests
        """
        # Arrange
        new_student = "persistent@mergington.edu"
        activity_name = "Programming Class"
        
        # Act: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_student}
        )
        
        # Assert: First GET
        get_response1 = client.get("/activities")
        assert new_student in get_response1.json()[activity_name]["participants"]
        
        # Assert: Second GET - verify persistence
        get_response2 = client.get("/activities")
        assert new_student in get_response2.json()[activity_name]["participants"]
    
    def test_signup_multiple_students_to_same_activity(self, client, clean_activities):
        """
        AAA Test: Verify multiple students can signup to same activity
        
        Arrange: Use clean app state, prepare multiple students
        Act: Sign up two students to same activity
        Assert: Verify both students appear in activity participants
        """
        # Arrange
        student1 = "multi1@mergington.edu"
        student2 = "multi2@mergington.edu"
        activity_name = "Drama Club"
        
        # Act: Sign up first student
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student1}
        )
        assert response1.status_code == 200
        
        # Act: Sign up second student
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student2}
        )
        assert response2.status_code == 200
        
        # Assert: Both in activity
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        assert student1 in participants
        assert student2 in participants
    
    def test_signup_fails_with_duplicate_enrollment(self, client, clean_activities):
        """
        AAA Test: Verify duplicate signup attempt fails appropriately
        
        Arrange: Sign up a student, attempt duplicate signup
        Act: Make duplicate signup request
        Assert: Verify 400 status and error message
        """
        # Arrange
        student = "duplicate@mergington.edu"
        activity_name = "Gym Class"
        
        # Act: First signup (should succeed)
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student}
        )
        assert response1.status_code == 200
        
        # Act: Duplicate signup (should fail)
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student}
        )
        
        # Assert
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_invalid_activity_fails(self, client, clean_activities):
        """
        AAA Test: Verify signup to non-existent activity fails with 404
        
        Arrange: Use clean app state with invalid activity name
        Act: Make signup request with non-existent activity
        Assert: Verify 404 status
        """
        # Arrange & Act
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestRemoveParticipantIntegration:
    """Integration tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_deletes_from_activity(self, client, clean_activities):
        """
        AAA Test: Verify participant removal actually deletes from activity
        
        Arrange: Sign up new student, verify enrollment
        Act: Remove the student
        Assert: Verify student no longer in activity participants
        """
        # Arrange: Sign up student first
        student = "removal@mergington.edu"
        activity_name = "Tennis Club"
        
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student}
        )
        
        # Verify enrolled
        get_before = client.get("/activities")
        assert student in get_before.json()[activity_name]["participants"]
        
        # Act: Remove participant
        response = client.delete(
            f"/activities/{activity_name}/participants/{student}"
        )
        
        # Assert: Verify deletion
        assert response.status_code == 200
        assert student in response.json()["message"]
        
        # Assert: Verify student no longer in activity
        get_after = client.get("/activities")
        assert student not in get_after.json()[activity_name]["participants"]
    
    def test_remove_existing_participant_succeeds(self, client, clean_activities):
        """
        AAA Test: Verify removal of pre-populated participant succeeds
        
        Arrange: Use clean state with pre-populated participants
        Act: Remove an existing participant
        Assert: Verify 200 status and participant removed
        """
        # Arrange
        activity_name = "Chess Club"
        participant = "michael@mergington.edu"
        
        # Verify participant exists before removal
        get_before = client.get("/activities")
        assert participant in get_before.json()[activity_name]["participants"]
        initial_count = len(get_before.json()[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{participant}"
        )
        
        # Assert: Response successful
        assert response.status_code == 200
        
        # Assert: Participant count decreased
        get_after = client.get("/activities")
        final_count = len(get_after.json()[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert participant not in get_after.json()[activity_name]["participants"]
    
    def test_remove_participant_fails_not_enrolled(self, client, clean_activities):
        """
        AAA Test: Verify removal of unenrolled participant fails appropriately
        
        Arrange: Use clean state, attempt to remove non-participant
        Act: Make DELETE request for unenrolled student
        Assert: Verify 400 status
        """
        # Arrange & Act
        response = client.delete(
            "/activities/Chess Club/participants/notinclubed@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
    
    def test_remove_participant_invalid_activity_fails(self, client, clean_activities):
        """
        AAA Test: Verify removal from non-existent activity fails with 404
        
        Arrange: Use clean state, specify non-existent activity
        Act: Make DELETE request to non-existent activity
        Assert: Verify 404 status
        """
        # Arrange & Act
        response = client.delete(
            "/activities/Fake Club/participants/student@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestCrossEndpointWorkflows:
    """Integration tests verifying workflows across multiple endpoints"""
    
    def test_signup_get_remove_workflow(self, client, clean_activities):
        """
        AAA Test: Complete workflow - signup, verify via GET, remove
        
        Arrange: Use clean app state
        Act: Sign up student → GET activities → Remove student
        Assert: Verify state changes persist correctly at each step
        """
        # Arrange
        student = "workflow@mergington.edu"
        activity = "Robotics Club"
        
        # Act 1: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": student}
        )
        
        # Assert 1: Signup successful
        assert signup_response.status_code == 200
        
        # Act 2: GET to verify enrollment
        get_response = client.get("/activities")
        
        # Assert 2: Verify enrolled
        assert student in get_response.json()[activity]["participants"]
        count_with_student = len(get_response.json()[activity]["participants"])
        
        # Act 3: Remove participant
        delete_response = client.delete(
            f"/activities/{activity}/participants/{student}"
        )
        
        # Assert 3: Removal successful
        assert delete_response.status_code == 200
        
        # Act 4: GET to verify removal
        get_response_after = client.get("/activities")
        
        # Assert 4: Verify no longer enrolled
        assert student not in get_response_after.json()[activity]["participants"]
        count_after_removal = len(get_response_after.json()[activity]["participants"])
        assert count_after_removal == count_with_student - 1
    
    def test_multiple_students_workflow(self, client, clean_activities):
        """
        AAA Test: Multiple concurrent signups and removals maintain consistency
        
        Arrange: Use clean state
        Act: Sign up 3 students, remove 1, verify state
        Assert: Verify remaining students correctly enrolled
        """
        # Arrange
        students = ["multi_a@mergington.edu", "multi_b@mergington.edu", "multi_c@mergington.edu"]
        activity = "Debate Team"
        
        # Act: Sign up all students
        for student in students:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        # Assert: All enrolled
        get_response = client.get("/activities")
        participants = get_response.json()[activity]["participants"]
        for student in students:
            assert student in participants
        
        # Act: Remove one student
        remove_response = client.delete(
            f"/activities/{activity}/participants/{students[1]}"
        )
        assert remove_response.status_code == 200
        
        # Assert: Correct students remain
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity]["participants"]
        assert students[0] in final_participants
        assert students[1] not in final_participants  # Removed
        assert students[2] in final_participants
    
    def test_signup_to_multiple_activities(self, client, clean_activities):
        """
        AAA Test: Student can signup to multiple different activities
        
        Arrange: Use clean state
        Act: Sign up same student to 2 different activities
        Assert: Verify student enrolled in both
        """
        # Arrange
        student = "multi_club@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act: Sign up to first activity
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": student}
        )
        assert response1.status_code == 200
        
        # Act: Sign up to second activity
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": student}
        )
        assert response2.status_code == 200
        
        # Assert: Student in both activities
        get_response = client.get("/activities")
        assert student in get_response.json()[activity1]["participants"]
        assert student in get_response.json()[activity2]["participants"]
