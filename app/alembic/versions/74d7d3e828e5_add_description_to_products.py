from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "74d7d3e828e5"
down_revision: str | Sequence[str] | None = "065c8017dbe0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("description", sa.Text(), nullable=True))
    op.drop_column("products", "descrtiption")


def downgrade() -> None:
    op.add_column("products", sa.Column("descrtiption", sa.TEXT(), nullable=True))
    op.drop_column("products", "description")
