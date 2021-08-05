"""empty message

Revision ID: 5b75a733430a
Revises: 
Create Date: 2020-12-01 09:22:54.332621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b75a733430a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('model2',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('attr1', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('attr1')
    )
    op.create_table('logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=512), nullable=True),
    sa.Column('method', sa.String(length=50), nullable=True),
    sa.Column('path', sa.String(length=200), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.Column('json', sa.Text(), nullable=True),
    sa.Column('dttm', sa.DateTime(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('referrer', sa.String(length=1024), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['ab_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('model1',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('attr1', sa.String(length=150), nullable=False),
    sa.Column('attr2', sa.DateTime(), nullable=True),
    sa.Column('attr3', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['attr3'], ['model2.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('attr1')
    )
    op.create_table('user_attribute',
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('changed_on', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_by_fk', sa.Integer(), nullable=True),
    sa.Column('changed_by_fk', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by_fk'], ['ab_user.id'], ),
    sa.ForeignKeyConstraint(['created_by_fk'], ['ab_user.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['ab_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('model1_model2',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model1_id', sa.Integer(), nullable=True),
    sa.Column('model2_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['model1_id'], ['model1.id'], ),
    sa.ForeignKeyConstraint(['model2_id'], ['model2.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('model1_model2')
    op.drop_table('user_attribute')
    op.drop_table('model1')
    op.drop_table('logs')
    op.drop_table('model2')
    # ### end Alembic commands ###