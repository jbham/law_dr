"""first push

Revision ID: 8a85b07d8c1e
Revises: 64488353f71a
Create Date: 2020-05-08 16:14:56.666369

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8a85b07d8c1e'
down_revision = '64488353f71a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cui_to_body_region_mapping')
    op.add_column('annotation_relationships', sa.Column('id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_annotation_relationships_id'), 'annotation_relationships', ['id'], unique=False)
    op.drop_constraint('unique_annot_relationship', 'annotation_relationships', type_='unique')
    op.create_unique_constraint('unique_annot_relationship', 'annotation_relationships', ['annotation_1_id', 'annotation_2_id', 'id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_annot_relationship', 'annotation_relationships', type_='unique')
    op.create_unique_constraint('unique_annot_relationship', 'annotation_relationships', ['annotation_1_id', 'annotation_2_id'])
    op.drop_index(op.f('ix_annotation_relationships_id'), table_name='annotation_relationships')
    op.drop_column('annotation_relationships', 'id')
    op.create_table('cui_to_body_region_mapping',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('cui', sa.VARCHAR(length=15), autoincrement=False, nullable=True),
    sa.Column('body_region', postgresql.ARRAY(sa.TEXT()), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='cui_to_body_region_mapping_pkey')
    )
    # ### end Alembic commands ###
