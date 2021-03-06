"""first push

Revision ID: 5b452e7452d1
Revises: 823148555f2c
Create Date: 2020-05-08 19:39:14.299800

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b452e7452d1'
down_revision = '823148555f2c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('annotation_relationships', sa.Column('business_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'annotation_relationships', 'business', ['business_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'annotation_relationships', type_='foreignkey')
    op.drop_column('annotation_relationships', 'business_id')
    # ### end Alembic commands ###
