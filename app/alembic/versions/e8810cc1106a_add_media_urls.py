from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8810cc1106a"
down_revision: str | Sequence[str] | None = "74d7d3e828e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chat_messages", sa.Column("attachment_url", sa.String(length=500), nullable=True))
    op.add_column("products", sa.Column("image_url", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
    op.drop_column("products", "image_url")
    op.drop_column("chat_messages", "attachment_url")
