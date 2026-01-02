"""
Tests for admin CLI functionality.

Tests the administrative interface for beta user management.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from datetime import datetime

from llm_context_exporter.cli.admin import admin
from llm_context_exporter.models.payment import BetaUser, UsageStats, Feedback


class TestAdminCLI:
    """Test admin CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.test_email = "test@example.com"
        self.test_notes = "Test user for admin CLI"
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_add_user_success(self, mock_beta_manager):
        """Test successful user addition."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = False
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, [
            'add-user', 
            '--email', self.test_email,
            '--notes', self.test_notes
        ])
        
        assert result.exit_code == 0
        assert "Successfully added beta user" in result.output
        mock_manager.add_beta_user.assert_called_once_with(self.test_email, self.test_notes)
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_add_user_already_exists(self, mock_beta_manager):
        """Test adding user that already exists."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = True
        mock_beta_manager.return_value = mock_manager
        
        # Simulate user declining to update
        with patch('llm_context_exporter.cli.admin.Confirm.ask', return_value=False):
            result = self.runner.invoke(admin, [
                'add-user', 
                '--email', self.test_email,
                '--notes', self.test_notes
            ])
        
        assert result.exit_code == 0
        assert "already in the beta program" in result.output
        mock_manager.add_beta_user.assert_not_called()
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_remove_user_success(self, mock_beta_manager):
        """Test successful user removal."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = True
        mock_manager.get_usage_stats.return_value = UsageStats(
            total_exports=5,
            exports_by_target={'gemini': 3, 'ollama': 2},
            total_conversations_processed=100,
            average_export_size_mb=2.5,
            last_export_date=datetime.now()
        )
        mock_beta_manager.return_value = mock_manager
        
        # Simulate user confirming removal
        with patch('llm_context_exporter.cli.admin.Confirm.ask', return_value=True):
            result = self.runner.invoke(admin, [
                'remove-user', 
                '--email', self.test_email
            ])
        
        assert result.exit_code == 0
        assert "Successfully removed beta user" in result.output
        mock_manager.remove_beta_user.assert_called_once_with(self.test_email)
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_remove_user_not_exists(self, mock_beta_manager):
        """Test removing user that doesn't exist."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = False
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, [
            'remove-user', 
            '--email', self.test_email
        ])
        
        assert result.exit_code == 0
        assert "is not in the beta program" in result.output
        mock_manager.remove_beta_user.assert_not_called()
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_list_users(self, mock_beta_manager):
        """Test listing beta users."""
        mock_manager = MagicMock()
        test_users = [
            BetaUser(
                email="user1@example.com",
                added_date=datetime.now(),
                notes="First user",
                total_exports=3,
                last_export_date=datetime.now(),
                feedback_count=1
            ),
            BetaUser(
                email="user2@example.com",
                added_date=datetime.now(),
                notes="Second user",
                total_exports=1,
                last_export_date=None,
                feedback_count=0
            )
        ]
        mock_manager.get_beta_users.return_value = test_users
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, ['list-users'])
        
        assert result.exit_code == 0
        assert "user1@example.com" in result.output
        assert "user2@example.com" in result.output
        assert "Beta Users (2 total)" in result.output
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_list_users_with_csv_export(self, mock_beta_manager):
        """Test listing users with CSV export."""
        mock_manager = MagicMock()
        test_users = [
            BetaUser(
                email="user1@example.com",
                added_date=datetime.now(),
                notes="Test user",
                total_exports=2,
                last_export_date=datetime.now(),
                feedback_count=1
            )
        ]
        mock_manager.get_beta_users.return_value = test_users
        mock_beta_manager.return_value = mock_manager
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            csv_path = tmp.name
        
        try:
            result = self.runner.invoke(admin, [
                'list-users', 
                '--export-csv', csv_path
            ])
            
            assert result.exit_code == 0
            assert "Exported to CSV" in result.output
            assert os.path.exists(csv_path)
            
            # Check CSV content
            with open(csv_path, 'r') as f:
                content = f.read()
                assert "user1@example.com" in content
                assert "Email,Added Date" in content
        
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_user_stats(self, mock_beta_manager):
        """Test getting user statistics."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = True
        
        test_user = BetaUser(
            email=self.test_email,
            added_date=datetime.now(),
            notes="Test user",
            total_exports=5,
            last_export_date=datetime.now(),
            feedback_count=2
        )
        mock_manager.get_beta_users.return_value = [test_user]
        
        test_stats = UsageStats(
            total_exports=5,
            exports_by_target={'gemini': 3, 'ollama': 2},
            total_conversations_processed=150,
            average_export_size_mb=3.2,
            last_export_date=datetime.now()
        )
        mock_manager.get_usage_stats.return_value = test_stats
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, [
            'user-stats', 
            '--email', self.test_email
        ])
        
        assert result.exit_code == 0
        assert self.test_email in result.output
        assert "Total Exports" in result.output
        assert "5" in result.output
        assert "Gemini" in result.output
        assert "Ollama" in result.output
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_user_stats_not_found(self, mock_beta_manager):
        """Test getting stats for non-existent user."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = False
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, [
            'user-stats', 
            '--email', self.test_email
        ])
        
        assert result.exit_code == 0
        assert "is not in the beta program" in result.output
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_feedback_list(self, mock_beta_manager):
        """Test listing feedback."""
        mock_manager = MagicMock()
        test_feedback = [
            Feedback(
                email="user1@example.com",
                timestamp=datetime.now(),
                rating=5,
                feedback_text="Great tool!",
                export_id="export_123",
                target_platform="gemini"
            ),
            Feedback(
                email="user2@example.com",
                timestamp=datetime.now(),
                rating=4,
                feedback_text="Good but could be better",
                export_id="export_456",
                target_platform="ollama"
            )
        ]
        mock_manager.get_all_feedback.return_value = test_feedback
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, ['feedback'])
        
        assert result.exit_code == 0
        assert "Great tool!" in result.output
        assert "Good but could be better" in result.output
        assert "⭐⭐⭐⭐⭐" in result.output
        assert "⭐⭐⭐⭐" in result.output
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_feedback_filtered(self, mock_beta_manager):
        """Test listing feedback with filters."""
        mock_manager = MagicMock()
        test_feedback = [
            Feedback(
                email="user1@example.com",
                timestamp=datetime.now(),
                rating=5,
                feedback_text="Great tool!",
                export_id="export_123",
                target_platform="gemini"
            ),
            Feedback(
                email="user2@example.com",
                timestamp=datetime.now(),
                rating=3,
                feedback_text="Average experience",
                export_id="export_456",
                target_platform="ollama"
            )
        ]
        mock_manager.get_all_feedback.return_value = test_feedback
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, [
            'feedback', 
            '--rating', '5',
            '--platform', 'gemini'
        ])
        
        assert result.exit_code == 0
        assert "Great tool!" in result.output
        assert "Average experience" not in result.output
        assert "Filtered by rating: 5" in result.output
        assert "Filtered by platform: gemini" in result.output
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_report_generation(self, mock_beta_manager):
        """Test generating comprehensive report."""
        mock_manager = MagicMock()
        
        test_users = [
            BetaUser(
                email="user1@example.com",
                added_date=datetime.now(),
                notes="Active user",
                total_exports=5,
                last_export_date=datetime.now(),
                feedback_count=2
            ),
            BetaUser(
                email="user2@example.com",
                added_date=datetime.now(),
                notes="New user",
                total_exports=1,
                last_export_date=datetime.now(),
                feedback_count=0
            )
        ]
        mock_manager.get_beta_users.return_value = test_users
        
        test_feedback = [
            Feedback(
                email="user1@example.com",
                timestamp=datetime.now(),
                rating=5,
                feedback_text="Excellent!",
                export_id="export_123",
                target_platform="gemini"
            )
        ]
        mock_manager.get_all_feedback.return_value = test_feedback
        
        # Mock usage stats for each user
        def mock_get_usage_stats(email):
            if email == "user1@example.com":
                return UsageStats(
                    total_exports=5,
                    exports_by_target={'gemini': 3, 'ollama': 2},
                    total_conversations_processed=100,
                    average_export_size_mb=2.5,
                    last_export_date=datetime.now()
                )
            else:
                return UsageStats(
                    total_exports=1,
                    exports_by_target={'gemini': 1},
                    total_conversations_processed=20,
                    average_export_size_mb=1.5,
                    last_export_date=datetime.now()
                )
        
        mock_manager.get_usage_stats.side_effect = mock_get_usage_stats
        mock_beta_manager.return_value = mock_manager
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            report_path = tmp.name
        
        try:
            result = self.runner.invoke(admin, [
                'report', 
                '--output', report_path
            ])
            
            assert result.exit_code == 0
            assert "Report generated" in result.output
            assert "Total Beta Users" in result.output
            assert "2" in result.output  # 2 users
            assert "6" in result.output  # 6 total exports
            assert os.path.exists(report_path)
            
            # Check report content
            with open(report_path, 'r') as f:
                content = f.read()
                assert "Beta Program Report" in content
                assert "user1@example.com" in content
                assert "user2@example.com" in content
        
        finally:
            if os.path.exists(report_path):
                os.unlink(report_path)
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_update_notes(self, mock_beta_manager):
        """Test updating user notes."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = True
        mock_beta_manager.return_value = mock_manager
        
        new_notes = "Updated notes for user"
        
        result = self.runner.invoke(admin, [
            'update-notes', 
            '--email', self.test_email,
            '--notes', new_notes
        ])
        
        assert result.exit_code == 0
        assert "Updated notes" in result.output
        assert new_notes in result.output
        mock_manager.add_beta_user.assert_called_once_with(self.test_email, new_notes)
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_update_notes_user_not_found(self, mock_beta_manager):
        """Test updating notes for non-existent user."""
        mock_manager = MagicMock()
        mock_manager.is_beta_user.return_value = False
        mock_beta_manager.return_value = mock_manager
        
        result = self.runner.invoke(admin, [
            'update-notes', 
            '--email', self.test_email,
            '--notes', "New notes"
        ])
        
        assert result.exit_code == 0
        assert "is not in the beta program" in result.output
        mock_manager.add_beta_user.assert_not_called()


class TestAdminCLIIntegration:
    """Integration tests for admin CLI with real BetaManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('llm_context_exporter.cli.admin.BetaManager')
    def test_full_user_lifecycle(self, mock_beta_manager_class):
        """Test complete user lifecycle: add, list, stats, remove."""
        from llm_context_exporter.web.beta import BetaManager
        
        # Use real BetaManager with temp database
        real_manager = BetaManager(self.db_path)
        mock_beta_manager_class.return_value = real_manager
        
        test_email = "integration@example.com"
        test_notes = "Integration test user"
        
        # Add user
        result = self.runner.invoke(admin, [
            'add-user', 
            '--email', test_email,
            '--notes', test_notes
        ])
        assert result.exit_code == 0
        assert "Successfully added beta user" in result.output
        
        # List users
        result = self.runner.invoke(admin, ['list-users'])
        assert result.exit_code == 0
        assert test_email in result.output
        
        # Get user stats
        result = self.runner.invoke(admin, [
            'user-stats', 
            '--email', test_email
        ])
        assert result.exit_code == 0
        assert test_email in result.output
        assert "Total Exports" in result.output
        
        # Remove user (with confirmation)
        with patch('llm_context_exporter.cli.admin.Confirm.ask', return_value=True):
            result = self.runner.invoke(admin, [
                'remove-user', 
                '--email', test_email
            ])
        assert result.exit_code == 0
        assert "Successfully removed beta user" in result.output
        
        # Verify user is gone
        result = self.runner.invoke(admin, ['list-users'])
        assert result.exit_code == 0
        assert test_email not in result.output or "No beta users found" in result.output