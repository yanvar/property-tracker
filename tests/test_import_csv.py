"""Tests for multi-file CSV import endpoint."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./data/test_properties.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

VALID_CSV = (
    "address,address href,location,column,column 2,column 3,column 4,column 5,column 6\n"
    "123 Main St,https://www.redfin.com/OH/Cleveland/123-Main-St-44101/home/12345,Downtown,$200000,3,2,1500,$133,10 days\n"
)

VALID_CSV_2 = (
    "address,address href,location,column,column 2,column 3,column 4,column 5,column 6\n"
    "456 Oak Ave,https://www.redfin.com/OH/Akron/456-Oak-Ave-44301/home/67890,Westside,$150000,2,1,1000,$150,5 days\n"
)

INVALID_CSV = "this is not,a valid,csv\nwith no,proper,columns\n"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_single_file_import():
    """Single file import should work as before."""
    response = client.post(
        "/import/",
        files=[("files", ("test.csv", VALID_CSV, "text/csv"))],
    )
    assert response.status_code == 200
    assert "Import Complete" in response.text
    assert "Added: 1 new properties" in response.text
    # Per-file breakdown should NOT appear for single file
    assert "Per-File Breakdown" not in response.text


def test_multiple_file_import():
    """Multiple files should show combined totals and per-file breakdown."""
    response = client.post(
        "/import/",
        files=[
            ("files", ("file1.csv", VALID_CSV, "text/csv")),
            ("files", ("file2.csv", VALID_CSV_2, "text/csv")),
        ],
    )
    assert response.status_code == 200
    assert "Import Complete" in response.text
    assert "Added: 2 new properties" in response.text
    assert "Per-File Breakdown" in response.text
    assert "file1.csv" in response.text
    assert "file2.csv" in response.text


def test_invalid_file_doesnt_block_valid():
    """One bad file should not prevent other files from importing."""
    response = client.post(
        "/import/",
        files=[
            ("files", ("good.csv", VALID_CSV, "text/csv")),
            ("files", ("bad.csv", INVALID_CSV, "text/csv")),
        ],
    )
    assert response.status_code == 200
    assert "Import Complete" in response.text
    # The valid file should still have imported
    assert "Added: 1 new properties" in response.text
    # Per-file breakdown should show the error for the bad file
    assert "Per-File Breakdown" in response.text
    assert "bad.csv" in response.text


def test_duplicate_across_files():
    """Same property in two files: first adds, second updates/unchanged."""
    response = client.post(
        "/import/",
        files=[
            ("files", ("first.csv", VALID_CSV, "text/csv")),
            ("files", ("second.csv", VALID_CSV, "text/csv")),
        ],
    )
    assert response.status_code == 200
    assert "Import Complete" in response.text
    # First file adds 1, second file finds it already exists
    assert "Added: 1 new properties" in response.text


def test_get_import_page():
    """GET /import/ should show the upload form."""
    response = client.get("/import/")
    assert response.status_code == 200
    assert "Redfin CSV Files" in response.text
    assert 'multiple' in response.text
    assert "You can select multiple files at once" in response.text
