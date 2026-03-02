# Property Tracker

A web-based real estate property tracking system for managing single-family house listings from Redfin.

## Features

- **CSV Import**: Import property listings from Redfin CSV exports
- **Dashboard**: Overview of your property pipeline with stats and action items
- **Kanban Board**: Visual workflow management with drag-and-drop
- **List View**: Filterable table view with sorting
- **Property Details**: Track agent info, notes, and price history
- **Workflow States**: New, Call, Follow Up, Skip
- **Market Status**: Active, Pending, Sold

## Quick Start

### Using Docker (Recommended)

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings (change SECRET_KEY for production)

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Open http://localhost:8000 in your browser

### Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy and configure environment:
   ```bash
   cp .env.example .env
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Open http://localhost:8000

## Usage

### Importing Properties

1. Go to Redfin.com and search for properties
2. Click "Download All" to export as CSV
3. Navigate to Import in the app
4. Upload the CSV and enter the zip code
5. Properties will be matched by address for updates

### Workflow Management

Properties flow through these stages:
- **New**: Freshly imported properties
- **Call**: Properties to contact about
- **Follow Up**: Properties with scheduled follow-up dates
- **Skip**: Properties you've decided to pass on

Use the Kanban board to drag properties between stages, or use the dropdown in the detail panel.

### Market Status

Track property market status independently:
- **Active**: Currently on the market
- **Pending**: Under contract
- **Sold**: No longer available

## Backup

The SQLite database is stored in `./data/properties.db`. To backup:

```bash
cp ./data/properties.db ./backup/properties-$(date +%Y%m%d).db
```

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Jinja2 templates + htmx + TailwindCSS
- **Database**: SQLite with SQLAlchemy
- **Deployment**: Docker

## Project Structure

```
oh/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings
│   ├── database.py          # SQLAlchemy setup
│   ├── models/              # Database models
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS/JS assets
├── alembic/                 # Database migrations
├── data/                    # SQLite database
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
