"""001

Revision ID: 9567837bd78c
Revises:
Create Date: 2026-03-06 01:08:15.927590

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "9567837bd78c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
