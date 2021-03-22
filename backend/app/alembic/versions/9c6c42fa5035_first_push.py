"""first push

Revision ID: 9c6c42fa5035
Revises: 34ce1a21ab71
Create Date: 2020-04-17 17:35:30.377649

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9c6c42fa5035'
down_revision = '34ce1a21ab71'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sf_ctakes_mentions', sa.Column('body_side', sa.String(), nullable=True))
    op.add_column('sf_ctakes_mentions', sa.Column('relations', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sf_ctakes_mentions', 'relations')
    op.drop_column('sf_ctakes_mentions', 'body_side')
    # ### end Alembic commands ###
