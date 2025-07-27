import pytest
import json
import logging # Import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_self_ext_engine.goal_manager import Goal, GoalManager

# Define a temporary goals file path for testing
@pytest.fixture
def temp_goals_file(tmp_path):
    """Creates a temporary goals.json file for testing."""
    file_path = tmp_path / "goals.json"
    yield file_path
    if file_path.exists():
        file_path.unlink()

@pytest.fixture
def populated_goals_file(temp_goals_file):
    """Creates a temporary goals.json file with initial data."""
    initial_data = {
        "goals": [
            {"id": "goal1", "description": "Description for goal 1", "status": "pending"},
            {"id": "goal2", "description": "Description for goal 2", "status": "pending"},
            {"id": "goal3", "description": "Description for goal 3", "status": "completed"}
        ]
    }
    with open(temp_goals_file, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f)
    return temp_goals_file

def test_goal_creation():
    """Test that a Goal object is created correctly."""
    goal = Goal("test_id", "Test description")
    assert goal.goal_id == "test_id"
    assert goal.description == "Test description"
    assert goal.status == "pending"

def test_goal_to_dict():
    """Test that Goal.to_dict returns the correct dictionary representation."""
    goal = Goal("test_id", "Test description", "completed")
    expected_dict = {
        "id": "test_id", 
        "description": "Test description", 
        "status": "completed",
        "priority": "medium",  # Default value
        "metadata": {}  # Default value
    }
    assert goal.to_dict() == expected_dict

def test_goal_manager_init_no_file(temp_goals_file, caplog):
    """Test GoalManager initialization when goals file does not exist."""
    with caplog.at_level(logging.INFO, logger='ai_self_ext_engine.goal_manager'):
        manager = GoalManager(str(temp_goals_file))
        assert manager.goals == []
        assert "Goals file not found" in caplog.text

def test_goal_manager_init_with_file(populated_goals_file):
    """Test GoalManager initialization when goals file exists and is populated."""
    manager = GoalManager(str(populated_goals_file))
    assert len(manager.goals) == 3
    assert manager.goals[0].goal_id == "goal1"
    assert manager.goals[2].status == "completed"

def test_goal_manager_init_corrupted_json(temp_goals_file, caplog):
    """Test GoalManager initialization with corrupted JSON."""
    temp_goals_file.write_text("this is not json")
    manager = GoalManager(str(temp_goals_file))
    assert manager.goals == []
    assert "Error decoding goals JSON" in caplog.text

def test_save_goals(temp_goals_file):
    """Test saving goals to file."""
    manager = GoalManager(str(temp_goals_file))
    manager.add_goal(Goal("new_goal", "A new goal"))
    
    with open(temp_goals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data["goals"]) == 1
    assert data["goals"][0]["id"] == "new_goal"

def test_next_goal_pending(populated_goals_file):
    """Test next_goal returns pending goals."""
    manager = GoalManager(str(populated_goals_file))
    next_g = manager.next_goal()
    assert next_g.goal_id == "goal1"
    next_g = manager.next_goal() # Call again to get next pending
    assert next_g.goal_id == "goal2"
    manager.mark_done("goal1") # Mark goal1 done
    manager.mark_done("goal2") # Mark goal2 done
    next_g = manager.next_goal()
    assert next_g is None # No more pending goals

def test_mark_done(populated_goals_file, caplog):
    """Test marking a goal as done."""
    with caplog.at_level(logging.INFO, logger='ai_self_ext_engine.goal_manager'):
        manager = GoalManager(str(populated_goals_file))
        manager.mark_done("goal1")
        assert manager.goals[0].status == "completed"
        assert "Goal 'goal1' marked as completed." in caplog.text
    
    # Verify it's saved to file
    manager_reloaded = GoalManager(str(populated_goals_file))
    assert manager_reloaded.goals[0].status == "completed"

def test_mark_done_not_found(populated_goals_file, caplog):
    """Test marking a non-existent goal as done."""
    with caplog.at_level(logging.WARNING, logger='ai_self_ext_engine.goal_manager'):
        manager = GoalManager(str(populated_goals_file))
        manager.mark_done("non_existent_goal")
        assert "Goal 'non_existent_goal' not found when trying to mark as done." in caplog.text

def test_add_goal(temp_goals_file):
    """Test adding a new goal."""
    manager = GoalManager(str(temp_goals_file))
    new_goal = Goal("add_test", "Test adding goal")
    manager.add_goal(new_goal)
    assert len(manager.goals) == 1
    assert manager.goals[0].goal_id == "add_test"

def test_add_goal_from_dict(temp_goals_file):
    """Test adding a new goal from a dictionary."""
    manager = GoalManager(str(temp_goals_file))
    goal_data = {"id": "dict_test", "description": "Test adding goal from dict"}
    manager.add_goal_from_dict(goal_data)
    assert len(manager.goals) == 1
    assert manager.goals[0].goal_id == "dict_test"
