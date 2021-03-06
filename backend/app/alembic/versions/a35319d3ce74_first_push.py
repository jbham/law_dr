"""first push

Revision ID: a35319d3ce74
Revises: 5ef2999165f0
Create Date: 2020-03-30 23:30:17.836307

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a35319d3ce74'
down_revision = '5ef2999165f0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('business', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('business', sa.Column('created_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('business', sa.Column('modified_by', sa.Integer(), nullable=True))
    op.add_column('business', sa.Column('modified_date', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, 'business', 'user', ['created_by'], ['id'])
    op.create_foreign_key(None, 'business', 'user', ['modified_by'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'business', type_='foreignkey')
    op.drop_constraint(None, 'business', type_='foreignkey')
    op.drop_column('business', 'modified_date')
    op.drop_column('business', 'modified_by')
    op.drop_column('business', 'created_date')
    op.drop_column('business', 'created_by')
    # ### end Alembic commands ###
