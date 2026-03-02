# Real Estate Property Tracking System - Brainstorm

## Project Overview

A web-based system for tracking, managing, and taking action on single-family houses on the market. The system helps users proactively pursue property purchases by organizing listings, tracking changes, and driving user action.

---

## Core Goals

1. **Track** properties currently on the market
2. **Monitor** changes (price drops, status changes, days on market)
3. **Manage** a personal workflow for pursuing properties
4. **Drive action** - push the user to proactively engage with opportunities
5. **Maintain history** of all properties and interactions

---

## Data Source

### Redfin CSV Export
- User runs a search query by zip code on Redfin
- Exports results to CSV
- Uploads CSV to the system
- **Frequency**: Daily to weekly imports

### On Import, System Will:
- **Match** existing properties and detect changes
- **Add** new listings
- **Flag** removed listings (sold/delisted)
- **Track** price history and status changes

---

## Property States (User Workflow)

Properties have two status layers:

### Market Status (from Redfin)
- Active
- Pending / Under Contract
- Sold

### User Workflow Status
| State | Description |
|-------|-------------|
| **New** | Just appeared on market, needs review |
| **Call** | User needs to call the agent |
| **Follow up** | User called, awaiting response (requires a follow-up date) |
| **Skip** | User decided to pass on this property |
| **Pending** | Market status - house under contract |
| **Sold** | Market status - house sold |

### State Rules
- Market status (Pending, Sold) from Redfin **auto-updates** and overrides user workflow state
- Follow-up state **requires** a date to be set
- Full history of state changes is retained

---

## User Experience

### Design Philosophy
**Action-driven** - The system should push the user into action, not just display data. The UX should drive proactive engagement with new opportunities.

---

## Three Views + Import Flow

### 1. Dashboard (Home)

The action-driving home screen.

**Priority Action Cards:**
- 🔥 New listings needing review (with count and CTA)
- 📞 Follow-ups due today (with property list and notes preview)
- 💰 Price drops / opportunities (highlighting motivated sellers)

**Pipeline Summary:**
- Visual count of properties in each state
- Warning indicators for stale items (e.g., "8 in New for 5+ days")
- Quick action buttons: [Review New] [Make Calls]

**Stale Alerts:**
- Properties sitting too long in New or Call states
- Nudges user to act or skip

**Smart Nudges (examples):**
- "You haven't reviewed new listings in 2 days"
- "123 Main St has been in Call for a week - still interested?"
- "Price dropped again on 456 Oak - 3rd reduction, motivated seller?"

---

### 2. Kanban Board

Visual pipeline management.

**Columns:**
```
| New | Call | Follow up | Skip | Pending | Sold |
```

**Property Card:**
```
┌─────────────────────────┐
│ 📍 123 Main St      🔗  │  ← link to Redfin
│    Anytown, 12345       │
├─────────────────────────┤
│ $425,000  ↓ $15K drop   │
│ 3 bd | 2 ba | 1,850 sqft│
│ 📅 14 days on market    │
├─────────────────────────┤
│ 🔔 Follow up: Mar 5     │  ← only in Follow up column
│ 📝 "Agent responsive"   │  ← note preview
└─────────────────────────┘
```

**Visual Indicators:**
- 🔴 Price drop badge (with amount)
- 🟢 New listing (< 24-48 hrs)
- ⚠️ Follow-up overdue
- 🕐 Long time on market

**Interactions:**
- Drag & drop cards between columns
- Click card → opens detail panel
- Moving to "Follow up" prompts for required date
- Column headers show count (e.g., "New (12)")
- No card limit per column - columns scroll

**Filtering:**
- Top filter bar: Zip code, price range, beds/baths, days on market
- Sort within column: By price, DOM, follow-up date
- Search by address

---

### 3. List View

Detailed, filterable table for analysis.

**Table Columns:**
| Column | Description |
|--------|-------------|
| Address | Street address |
| Price | Current asking price |
| Δ (Delta) | Price change indicator (↓ $15K) |
| Beds | Bedroom count |
| Sqft | Square footage |
| DOM | Days on market |
| State | User workflow state (inline dropdown) |
| 🔗 | Link to Redfin listing |

**Filters:**
- Zip code (single or multi-select)
- Price range (min/max)
- Market status (Active, Pending, Sold)
- User workflow state
- Days on market range
- Price change (show only drops)
- Text search by address

**Row Interactions:**
- Click row → opens detail side panel
- Change state via inline dropdown
- Sort by clicking column headers
- Multi-select with checkboxes for bulk actions

**Bulk Actions:**
- Move selected to [State]
- Export selected to CSV

**Detail Side Panel:**
- Full property info (address, price, beds/baths/sqft, DOM)
- Price history (all changes with dates)
- Current state with dropdown to change
- Follow-up date (if applicable)
- Notes section (chronological, add new)
- Activity history (state changes, system updates)
- Link to Redfin listing

---

### 4. CSV Import Flow

**Upload Interface:**
- Drag & drop zone for CSV file
- Or browse files button

**Import Summary (after upload):**
```
✅ IMPORT COMPLETE

📊 Summary:
• 8 new properties added
• 12 existing properties updated
   - 3 price changes
   - 2 status changes (→ Pending)
• 5 properties no longer in feed (removed/sold)

[View New]  [View Changes]  [Go to Dashboard]
```

---

## Property Features

### Core Data (from Redfin CSV)
- Address
- Price
- Beds / Baths / Sqft
- Days on market
- Market status
- Listing URL

### System-Tracked Data
- Price history (all changes with dates)
- Status history
- Date added to system
- Date last seen in CSV

### User-Added Data
- Workflow state
- Follow-up date
- Notes (timestamped, multiple entries)

### History Retention
- All properties kept forever (even after sold/removed)
- Full price change history
- Full status change history
- All notes preserved

---

## Technical Requirements

### Deployment
- **Platform**: Ubuntu server
- **Container**: Docker environment
- **Access**: Web-based (browser)

### Users
- Single user (for v1)

### Tech Stack
- To be determined in design phase
- Recommendations welcome

---

## Future Enhancements (Not in v1)

- Insights & analytics dashboard
- Trend analysis (inventory levels, price trends, DOM trends)
- Multi-user support
- Email/push notifications
- Property comparison tools
- Investment calculators (ROI, rental estimates)

---

## Open Questions for Design Phase

1. Tech stack selection (frontend, backend, database)
2. CSV parsing specifics (Redfin format handling)
3. Data model design
4. Authentication approach (single user, but still need login?)
5. Backup/data persistence strategy

---

## Summary

A proactive, action-driven real estate tracking system that:
- Ingests Redfin CSV exports
- Tracks properties through a user-defined workflow
- Maintains complete history
- Pushes users toward action through smart UX
- Provides multiple views: Dashboard (action), Kanban (workflow), List (analysis)
