from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "065c8017dbe0"
down_revision: str | Sequence[str] | None = "54afa5929fc9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("descrtiption", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "descrtiption")
