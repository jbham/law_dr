"""first push

Revision ID: 823148555f2c
Revises: 56f0eee69626
Create Date: 2020-05-08 19:36:33.702131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '823148555f2c'
down_revision = '56f0eee69626'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sf_ctakes_mentions', sa.Column('annotation_type', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sf_ctakes_mentions', 'annotation_type')
    # ### end Alembic commands ###
