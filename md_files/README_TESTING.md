# Testing Guide

## Running Tests

### Prerequisites
1. Install dependencies: `pip install -r requirements.txt`
2. Ensure PostgreSQL is running (or use SQLite for tests)
3. Set DATABASE_URL environment variable (optional, defaults to SQLite)

### Run All Tests
```bash
cd backend
pytest tests/ -v
```

### Run with Coverage
```bash
# First install pytest-cov: pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Run Specific Test Files
```bash
# API tests
pytest tests/api/ -v

# Service tests
pytest tests/services/ -v

# Task tests
pytest tests/tasks/ -v

# Integration tests
pytest tests/integration/ -v
```

### Run Specific Tests
```bash
pytest tests/api/test_sessions.py::test_create_session_success -v
```

## Test Structure

- `tests/api/` - API endpoint tests
- `tests/services/` - Business logic service tests
- `tests/tasks/` - Celery task tests (with mocks)
- `tests/integration/` - End-to-end integration tests

## Test Fixtures

Available fixtures (from `conftest.py`):
- `db_session` - Database session for each test
- `sample_tutor` - Sample tutor record
- `sample_session` - Sample session record
- `sample_reschedule` - Sample reschedule record
- `sample_tutor_score` - Sample tutor score record
- `sample_email_report` - Sample email report record

## Notes

- Tests use PostgreSQL if DATABASE_URL is set, otherwise SQLite (in-memory)
- Celery tasks are mocked in tests to avoid requiring Redis
- Email service is mocked to avoid sending actual emails
- All tests clean up after themselves

