"""Store the interview question guide alongside its confirmed outline."""

from alembic import op

revision = "0001_question_guide"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Fresh installations may already have the column from metadata.create_all.
    op.execute("ALTER TABLE interview_preps ADD COLUMN IF NOT EXISTS question_guide JSONB")


def downgrade():
    op.drop_column("interview_preps", "question_guide")
