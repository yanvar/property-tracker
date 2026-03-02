# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real Estate Property Tracking System - a web-based application to track, manage, and drive action on single-family house listings. Users import Redfin CSV exports and manage properties through a workflow pipeline.

See `brainstorm.md` for detailed product requirements and specifications.

## Project Status

Pre-development phase. Tech stack and architecture to be determined.

## Target Deployment

- Ubuntu server with Docker
- Single user for v1
- Web-based access

## Key Concepts

### Data Flow
1. User exports search results from Redfin as CSV
2. System imports CSV, matching/adding/flagging properties
3. User manages properties through workflow states

### Property States
- **Market Status** (from Redfin): Active, Pending, Sold
- **User Workflow**: New → Call → Follow up → Skip (Pending/Sold override user state)
- Follow-up state requires a date

### Core Views
1. **Dashboard** - Action-driven home with priority cards and nudges
2. **Kanban Board** - Visual workflow pipeline with drag-and-drop
3. **List View** - Filterable table for analysis
4. **CSV Import** - Upload flow with change detection summary

## Open Design Questions

1. Tech stack selection (frontend, backend, database)
2. CSV parsing specifics (Redfin format handling)
3. Data model design
4. Authentication approach
5. Backup/data persistence strategy
