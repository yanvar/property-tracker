from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models import Property, PriceHistory, StatusHistory, Note, MarketStatus, WorkflowStatus


def normalize_address(address: str) -> str:
    """Normalize address for matching."""
    return address.lower().strip().replace("  ", " ")


class PropertyService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        workflow_status: Optional[WorkflowStatus] = None,
        market_status: Optional[MarketStatus] = None,
        zip_code: Optional[str] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> List[Property]:
        """Get all properties with optional filtering."""
        query = self.db.query(Property)

        if workflow_status:
            query = query.filter(Property.workflow_status == workflow_status)
        if market_status:
            query = query.filter(Property.market_status == market_status)
        if zip_code:
            query = query.filter(Property.zip_code == zip_code)

        # Sorting
        sort_column = getattr(Property, sort_by, Property.created_at)
        if sort_dir == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        return query.all()

    def get_by_id(self, property_id: int) -> Optional[Property]:
        """Get a single property by ID."""
        return self.db.query(Property).filter(Property.id == property_id).first()

    def get_by_address(self, address: str) -> Optional[Property]:
        """Find property by normalized address."""
        normalized = normalize_address(address)
        return self.db.query(Property).filter(
            func.lower(Property.address) == normalized
        ).first()

    def create(self, data: Dict[str, Any]) -> Property:
        """Create a new property."""
        property_obj = Property(**data)
        self.db.add(property_obj)
        self.db.commit()
        self.db.refresh(property_obj)

        # Record initial price in history
        if property_obj.price:
            self.add_price_history(property_obj.id, property_obj.price)

        return property_obj

    def update(self, property_id: int, data: Dict[str, Any]) -> Optional[Property]:
        """Update a property."""
        property_obj = self.get_by_id(property_id)
        if not property_obj:
            return None

        for key, value in data.items():
            if hasattr(property_obj, key):
                setattr(property_obj, key, value)

        property_obj.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj

    def update_workflow_status(
        self,
        property_id: int,
        new_status: WorkflowStatus,
        follow_up_date: Optional[str] = None,
        skip_reason: Optional[str] = None,
        source: str = "user"
    ) -> Optional[Property]:
        """Update workflow status with history tracking."""
        property_obj = self.get_by_id(property_id)
        if not property_obj:
            return None

        old_status = property_obj.workflow_status

        # Record status change
        if old_status != new_status:
            history = StatusHistory(
                property_id=property_id,
                from_status=old_status.value if old_status else None,
                to_status=new_status.value,
                source=source
            )
            self.db.add(history)

        property_obj.workflow_status = new_status

        # Handle follow-up date
        if new_status == WorkflowStatus.FOLLOW_UP and follow_up_date:
            property_obj.follow_up_date = datetime.strptime(follow_up_date, "%Y-%m-%d").date()
        elif new_status != WorkflowStatus.FOLLOW_UP:
            property_obj.follow_up_date = None

        # Handle skip reason
        if new_status == WorkflowStatus.SKIP and skip_reason:
            property_obj.skip_reason = skip_reason
        elif new_status != WorkflowStatus.SKIP:
            property_obj.skip_reason = None

        property_obj.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj

    def update_market_status(
        self,
        property_id: int,
        new_status: MarketStatus,
        source: str = "user"
    ) -> Optional[Property]:
        """Update market status with history tracking."""
        property_obj = self.get_by_id(property_id)
        if not property_obj:
            return None

        old_status = property_obj.market_status

        if old_status != new_status:
            history = StatusHistory(
                property_id=property_id,
                from_status=f"market:{old_status.value}" if old_status else None,
                to_status=f"market:{new_status.value}",
                source=source
            )
            self.db.add(history)

        property_obj.market_status = new_status
        property_obj.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj

    def add_price_history(self, property_id: int, price: int) -> PriceHistory:
        """Add a price history entry."""
        history = PriceHistory(property_id=property_id, price=price)
        self.db.add(history)
        self.db.commit()
        return history

    def get_price_history(self, property_id: int) -> List[PriceHistory]:
        """Get price history for a property."""
        return self.db.query(PriceHistory).filter(
            PriceHistory.property_id == property_id
        ).order_by(PriceHistory.recorded_at.desc()).all()

    def add_note(self, property_id: int, content: str) -> Note:
        """Add a note to a property."""
        note = Note(property_id=property_id, content=content)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_notes(self, property_id: int) -> List[Note]:
        """Get all notes for a property."""
        return self.db.query(Note).filter(
            Note.property_id == property_id
        ).order_by(Note.created_at.desc()).all()

    def delete_note(self, note_id: int) -> bool:
        """Delete a note."""
        note = self.db.query(Note).filter(Note.id == note_id).first()
        if note:
            self.db.delete(note)
            self.db.commit()
            return True
        return False

    def import_properties(self, properties_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Import properties from parsed CSV data.
        Returns summary of changes.
        """
        summary = {
            "added": 0,
            "updated": 0,
            "price_changes": [],
            "unchanged": 0,
            "errors": []
        }

        now = datetime.utcnow()

        for data in properties_data:
            try:
                existing = self.get_by_address(data["address"])

                if existing:
                    # Update existing property
                    changes = []

                    # Check for price change
                    if data["price"] and existing.price != data["price"]:
                        old_price = existing.price
                        self.add_price_history(existing.id, data["price"])
                        changes.append(f"price: ${old_price/100:.0f} -> ${data['price']/100:.0f}")
                        summary["price_changes"].append({
                            "address": existing.address,
                            "old_price": old_price,
                            "new_price": data["price"]
                        })

                    # Update fields
                    update_fields = ["price", "beds", "baths", "sqft", "price_per_sqft",
                                   "days_on_market", "neighborhood", "redfin_url", "state"]
                    for field in update_fields:
                        if data.get(field) is not None:
                            setattr(existing, field, data[field])

                    existing.last_seen = now
                    existing.updated_at = now

                    if changes:
                        summary["updated"] += 1
                    else:
                        summary["unchanged"] += 1
                else:
                    # Create new property
                    data["first_seen"] = now
                    data["last_seen"] = now
                    data["market_status"] = MarketStatus.ACTIVE
                    data["workflow_status"] = WorkflowStatus.NEW
                    self.create(data)
                    summary["added"] += 1

            except Exception as e:
                summary["errors"].append(f"Error with {data.get('address', 'unknown')}: {str(e)}")

        self.db.commit()
        return summary

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get statistics for dashboard."""
        total = self.db.query(Property).count()

        by_workflow = {}
        for status in WorkflowStatus:
            count = self.db.query(Property).filter(
                Property.workflow_status == status
            ).count()
            by_workflow[status.value] = count

        by_market = {}
        for status in MarketStatus:
            count = self.db.query(Property).filter(
                Property.market_status == status
            ).count()
            by_market[status.value] = count

        return {
            "total": total,
            "by_workflow": by_workflow,
            "by_market": by_market
        }

    def get_properties_needing_followup(self) -> List[Property]:
        """Get properties with follow-up dates that have passed."""
        from datetime import date
        return self.db.query(Property).filter(
            Property.workflow_status == WorkflowStatus.FOLLOW_UP,
            Property.follow_up_date <= date.today()
        ).order_by(Property.follow_up_date.asc()).all()

    def get_new_properties(self, limit: int = 10) -> List[Property]:
        """Get newest properties."""
        return self.db.query(Property).filter(
            Property.workflow_status == WorkflowStatus.NEW
        ).order_by(Property.first_seen.desc()).limit(limit).all()

    def has_price_change(self, property_id: int) -> bool:
        """Check if a property has had price changes (more than 1 price history entry)."""
        count = self.db.query(PriceHistory).filter(
            PriceHistory.property_id == property_id
        ).count()
        return count > 1

    def get_properties_with_price_changes(self) -> set:
        """Get set of property IDs that have price changes."""
        from sqlalchemy import func
        results = self.db.query(PriceHistory.property_id).group_by(
            PriceHistory.property_id
        ).having(func.count(PriceHistory.id) > 1).all()
        return {r[0] for r in results}

    def delete_property(self, property_id: int) -> bool:
        """Delete a property and all related data."""
        property_obj = self.get_by_id(property_id)
        if not property_obj:
            return False

        # Cascade delete will handle related records (price_history, status_history, notes)
        self.db.delete(property_obj)
        self.db.commit()
        return True
