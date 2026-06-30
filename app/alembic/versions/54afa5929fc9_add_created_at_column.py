from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "54afa5929fc9"
down_revision: str | Sequence[str] | None = "5276055d77e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("chat_rooms") as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
            )
        )
    with op.batch_alter_table("order_items") as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
            )
        )
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_column("created_at")
    with op.batch_alter_table("order_items") as batch_op:
        batch_op.drop_column("created_at")
    with op.batch_alter_table("chat_rooms") as batch_op:
        batch_op.drop_column("created_at")
