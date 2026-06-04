# ============================================================
# models.py — Database table definitions
# Add a new column here = add it everywhere automatically
# ============================================================

from sqlalchemy import Column, Integer, Text, DateTime, func
from database import Base


class Paper(Base):
    """
    Represents one past paper entry.
    Maps directly to the 'papers' table in Neon.
    """
    __tablename__ = "papers"

    id           = Column(Integer, primary_key=True, index=True)
    subject      = Column(Text,    nullable=False)
    semester     = Column(Integer, nullable=False)
    year         = Column(Integer, nullable=False)
    type         = Column(Text,    nullable=False)   # Mid Term / Final Term
    department   = Column(Text,    nullable=False)   # BSCS / BSSE / BSIT
    pdf_url      = Column(Text,    nullable=False)   # GitHub raw URL
    uploaded_by  = Column(Text,    nullable=True)    # Google user email
    status       = Column(Text,    default="approved")  # auto-approved
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert to plain dict for JSON response."""
        return {
            "id":          self.id,
            "subject":     self.subject,
            "semester":    self.semester,
            "year":        self.year,
            "type":        self.type,
            "department":  self.department,
            "pdf":         self.pdf_url,
            "uploaded_by": self.uploaded_by,
            "created_at":  str(self.created_at),
        }