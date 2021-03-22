"""first push

Revision ID: 187e21bc129f
Revises: 9152fe635a2e
Create Date: 2020-05-05 23:23:37.633237

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '187e21bc129f'
down_revision = '9152fe635a2e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('annotation_relationships', sa.Column('id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_annotation_relationships_id'), 'annotation_relationships', ['id'], unique=False)
    op.drop_constraint('unique_annot_relationship', 'annotation_relationships', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('unique_annot_relationship', 'annotation_relationships', ['annotation_1_id', 'annotation_2_id'])
    op.drop_index(op.f('ix_annotation_relationships_id'), table_name='annotation_relationships')
    op.drop_column('annotation_relationships', 'id')
    # ### end Alembic commands ###