"""
Integration tests for reports functionality.
"""
import pytest
import json
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from decimal import Decimal

from app.main import app
from app.services.reports_service import ReportsService
from app.schemas.reports import (
    ReportType,
    ReportFormat,
    ProjectReportResponse,
    ProjectReportExportResponse
)
from app.models.project import Project
from app.models.user import User


class TestReportsIntegration:
    """Integration tests for reports functionality."""
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",
            role="Manager",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return user
    
    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test project description",
            status="active",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=Decimal("10000.00"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return project
    
    @pytest.mark.asyncio
    async def test_get_project_reports_list(self, sample_user, sample_project):
        """Test getting list of project reports."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service:
                    mock_project_service.return_value = sample_project
                    
                    # Add some test reports to the service
                    test_report = ProjectReportResponse(
                        report_id="test-report-1",
                        project={"id": str(sample_project.id), "name": sample_project.name},
                        report_type=ReportType.SUMMARY,
                        generated_at=datetime.now(timezone.utc),
                        summary=MagicMock(),
                        team_performance=[],
                        milestones=[],
                        metadata={}
                    )
                    ReportsService._generated_reports["test-report-1"] = test_report
                    
                    # Make request
                    from fastapi.testclient import TestClient
                    client = TestClient(app)
                    
                    response = client.get("/reports/projects")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "reports" in data
                    assert "total_count" in data
                    assert "page" in data
                    assert "page_size" in data
                    assert "has_next" in data
                    assert "has_previous" in data
    
    @pytest.mark.asyncio
    async def test_get_project_report(self, sample_user, sample_project):
        """Test getting a specific project report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access, \
                     patch('app.services.project_service.ProjectService.project_to_response') as mock_project_response:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    mock_project_response.return_value = {
                        "id": str(sample_project.id),
                        "name": sample_project.name,
                        "description": sample_project.description,
                        "status": sample_project.status
                    }
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
                        test_report = ProjectReportResponse(
                            report_id="test-report-1",
                            project={"id": str(sample_project.id), "name": sample_project.name},
                            report_type=ReportType.SUMMARY,
                            generated_at=datetime.now(timezone.utc),
                            summary=MagicMock(),
                            team_performance=[],
                            milestones=[],
                            metadata={}
                        )
                        mock_generate.return_value = test_report
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.get(f"/reports/projects/{sample_project.id}")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["report_id"] == "test-report-1"
                        assert data["report_type"] == "summary"
                        assert data["project"]["id"] == str(sample_project.id)
    
    @pytest.mark.asyncio
    async def test_get_project_report_not_found(self, sample_user):
        """Test getting report for non-existent project."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service:
                    mock_project_service.return_value = None
                    
                    # Make request
                    from fastapi.testclient import TestClient
                    client = TestClient(app)
                    
                    response = client.get(f"/reports/projects/{uuid4()}")
                    
                    assert response.status_code == 404
                    data = response.json()
                    assert "Project not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_project_report_unauthorized(self, sample_user, sample_project):
        """Test getting report without proper authorization."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = False  # No access
                    
                    # Make request
                    from fastapi.testclient import TestClient
                    client = TestClient(app)
                    
                    response = client.get(f"/reports/projects/{sample_project.id}")
                    
                    assert response.status_code == 403
                    data = response.json()
                    assert "Not authorized" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_project_summary_report(self, sample_user, sample_project):
        """Test getting project summary report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access, \
                     patch('app.services.project_service.ProjectService.project_to_response') as mock_project_response:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    mock_project_response.return_value = {
                        "id": str(sample_project.id),
                        "name": sample_project.name,
                        "description": sample_project.description,
                        "status": sample_project.status
                    }
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
                        test_report = ProjectReportResponse(
                            report_id="test-summary-report",
                            project={"id": str(sample_project.id), "name": sample_project.name},
                            report_type=ReportType.SUMMARY,
                            generated_at=datetime.now(timezone.utc),
                            summary=MagicMock(),
                            team_performance=[],
                            milestones=[],
                            metadata={}
                        )
                        mock_generate.return_value = test_report
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.get(f"/reports/projects/{sample_project.id}/summary")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["report_id"] == "test-summary-report"
                        assert data["report_type"] == "summary"
    
    @pytest.mark.asyncio
    async def test_get_project_financial_report(self, sample_user, sample_project):
        """Test getting project financial report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access, \
                     patch('app.services.project_service.ProjectService.project_to_response') as mock_project_response:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    mock_project_response.return_value = {
                        "id": str(sample_project.id),
                        "name": sample_project.name,
                        "description": sample_project.description,
                        "status": sample_project.status
                    }
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
                        test_report = ProjectReportResponse(
                            report_id="test-financial-report",
                            project={"id": str(sample_project.id), "name": sample_project.name},
                            report_type=ReportType.FINANCIAL,
                            generated_at=datetime.now(timezone.utc),
                            summary=MagicMock(),
                            financial_data=MagicMock(),
                            team_performance=[],
                            milestones=[],
                            metadata={}
                        )
                        mock_generate.return_value = test_report
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.get(f"/reports/projects/{sample_project.id}/financial")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["report_id"] == "test-financial-report"
                        assert data["report_type"] == "financial"
    
    @pytest.mark.asyncio
    async def test_get_project_team_performance_report(self, sample_user, sample_project):
        """Test getting project team performance report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access, \
                     patch('app.services.project_service.ProjectService.project_to_response') as mock_project_response:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    mock_project_response.return_value = {
                        "id": str(sample_project.id),
                        "name": sample_project.name,
                        "description": sample_project.description,
                        "status": sample_project.status
                    }
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
                        test_report = ProjectReportResponse(
                            report_id="test-team-report",
                            project={"id": str(sample_project.id), "name": sample_project.name},
                            report_type=ReportType.TEAM_PERFORMANCE,
                            generated_at=datetime.now(timezone.utc),
                            summary=MagicMock(),
                            team_performance=[MagicMock()],
                            milestones=[],
                            metadata={}
                        )
                        mock_generate.return_value = test_report
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.get(f"/reports/projects/{sample_project.id}/team-performance")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["report_id"] == "test-team-report"
                        assert data["report_type"] == "team_performance"
    
    @pytest.mark.asyncio
    async def test_get_project_milestones_report(self, sample_user, sample_project):
        """Test getting project milestones report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access, \
                     patch('app.services.project_service.ProjectService.project_to_response') as mock_project_response:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    mock_project_response.return_value = {
                        "id": str(sample_project.id),
                        "name": sample_project.name,
                        "description": sample_project.description,
                        "status": sample_project.status
                    }
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
                        test_report = ProjectReportResponse(
                            report_id="test-milestones-report",
                            project={"id": str(sample_project.id), "name": sample_project.name},
                            report_type=ReportType.MILESTONE,
                            generated_at=datetime.now(timezone.utc),
                            summary=MagicMock(),
                            team_performance=[],
                            milestones=[MagicMock()],
                            metadata={}
                        )
                        mock_generate.return_value = test_report
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.get(f"/reports/projects/{sample_project.id}/milestones")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["report_id"] == "test-milestones-report"
                        assert data["report_type"] == "milestone"
    
    @pytest.mark.asyncio
    async def test_get_project_task_analysis_report(self, sample_user, sample_project):
        """Test getting project task analysis report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access, \
                     patch('app.services.project_service.ProjectService.project_to_response') as mock_project_response:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    mock_project_response.return_value = {
                        "id": str(sample_project.id),
                        "name": sample_project.name,
                        "description": sample_project.description,
                        "status": sample_project.status
                    }
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
                        test_report = ProjectReportResponse(
                            report_id="test-task-analysis-report",
                            project={"id": str(sample_project.id), "name": sample_project.name},
                            report_type=ReportType.TASK_ANALYSIS,
                            generated_at=datetime.now(timezone.utc),
                            summary=MagicMock(),
                            team_performance=[],
                            milestones=[],
                            task_analysis=MagicMock(),
                            metadata={}
                        )
                        mock_generate.return_value = test_report
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.get(f"/reports/projects/{sample_project.id}/task-analysis")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["report_id"] == "test-task-analysis-report"
                        assert data["report_type"] == "task_analysis"
    
    @pytest.mark.asyncio
    async def test_export_project_report(self, sample_user, sample_project):
        """Test exporting a project report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.export_project_report') as mock_export:
                        test_export = ProjectReportExportResponse(
                            export_id="test-export",
                            filename="test_report.json",
                            format=ReportFormat.JSON,
                            download_url="/static/exports/test_report.json",
                            file_size=1024,
                            expires_at=datetime.now(timezone.utc),
                            metadata={}
                        )
                        mock_export.return_value = test_export
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        export_request = {
                            "project_id": str(sample_project.id),
                            "report_type": "summary",
                            "format": "json",
                            "include_charts": True,
                            "filename": "test_report"
                        }
                        
                        response = client.post("/reports/projects/export", json=export_request)
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["export_id"] == "test-export"
                        assert data["filename"] == "test_report.json"
                        assert data["format"] == "json"
                        assert data["download_url"] == "/static/exports/test_report.json"
    
    @pytest.mark.asyncio
    async def test_export_project_report_invalid_dates(self, sample_user, sample_project):
        """Test exporting report with invalid date range."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    
                    # Make request
                    from fastapi.testclient import TestClient
                    client = TestClient(app)
                    
                    export_request = {
                        "project_id": str(sample_project.id),
                        "report_type": "summary",
                        "format": "json",
                        "start_date": "2024-12-31",
                        "end_date": "2024-01-01",  # End date before start date
                        "include_charts": True
                    }
                    
                    response = client.post("/reports/projects/export", json=export_request)
                    
                    assert response.status_code == 400
                    data = response.json()
                    assert "Start date cannot be after end date" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_project_report(self, sample_user, sample_project):
        """Test deleting a project report."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    
                    # Add a test report
                    test_report = ProjectReportResponse(
                        report_id="test-report-to-delete",
                        project={"id": str(sample_project.id), "name": sample_project.name},
                        report_type=ReportType.SUMMARY,
                        generated_at=datetime.now(timezone.utc),
                        summary=MagicMock(),
                        team_performance=[],
                        milestones=[],
                        metadata={}
                    )
                    ReportsService._generated_reports["test-report-to-delete"] = test_report
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.get_report_by_id') as mock_get_report:
                        mock_get_report.return_value = test_report
                        
                        # Make request
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.delete(f"/reports/projects/{sample_project.id}/reports/test-report-to-delete")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["message"] == "Report deleted successfully"
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_reports(self, sample_user):
        """Test cleanup of expired reports."""
        # Mock authentication with admin role
        with patch('app.core.dependencies.require_roles') as mock_roles:
            mock_roles.return_value = lambda user: user.role in ["Admin", "Manager"]
            
            with patch('app.core.dependencies.get_current_user') as mock_auth:
                mock_auth.return_value = sample_user
                
                # Mock reports service
                with patch('app.services.reports_service.ReportsService.cleanup_expired_exports') as mock_cleanup:
                    
                    # Make request
                    from fastapi.testclient import TestClient
                    client = TestClient(app)
                    
                    response = client.post("/reports/cleanup")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["message"] == "Cleanup task scheduled successfully"
    
    @pytest.mark.asyncio
    async def test_reports_with_date_filters(self, sample_user, sample_project):
        """Test reports with date filters."""
        # Mock authentication
        with patch('app.core.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            # Mock database session
            with patch('app.db.database.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Mock project service
                with patch('app.services.project_service.ProjectService.get_project_by_id') as mock_project_service, \
                     patch('app.services.project_service.ProjectService.can_access_project') as mock_access, \
                     patch('app.services.project_service.ProjectService.project_to_response') as mock_project_response:
                    
                    mock_project_service.return_value = sample_project
                    mock_access.return_value = True
                    mock_project_response.return_value = {
                        "id": str(sample_project.id),
                        "name": sample_project.name,
                        "description": sample_project.description,
                        "status": sample_project.status
                    }
                    
                    # Mock reports service
                    with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
                        test_report = ProjectReportResponse(
                            report_id="test-date-filter-report",
                            project={"id": str(sample_project.id), "name": sample_project.name},
                            report_type=ReportType.SUMMARY,
                            generated_at=datetime.now(timezone.utc),
                            period_start=date(2024, 1, 1),
                            period_end=date(2024, 6, 30),
                            summary=MagicMock(),
                            team_performance=[],
                            milestones=[],
                            metadata={}
                        )
                        mock_generate.return_value = test_report
                        
                        # Make request with date filters
                        from fastapi.testclient import TestClient
                        client = TestClient(app)
                        
                        response = client.get(
                            f"/reports/projects/{sample_project.id}",
                            params={
                                "report_type": "summary",
                                "start_date": "2024-01-01",
                                "end_date": "2024-06-30"
                            }
                        )
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["report_id"] == "test-date-filter-report"
                        assert data["period_start"] == "2024-01-01"
                        assert data["period_end"] == "2024-06-30" 