"""add matching tables

Revision ID: add_matching_001
Revises: c34e4fefa31d
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_matching_001'
down_revision: Union[str, None] = 'c34e4fefa31d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to tutors table
    op.add_column('tutors', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('tutors', sa.Column('sex', sa.String(length=10), nullable=True))
    op.add_column('tutors', sa.Column('experience_years', sa.Integer(), nullable=True))
    op.add_column('tutors', sa.Column('teaching_style', sa.String(length=50), nullable=True))
    op.add_column('tutors', sa.Column('preferred_pace', sa.Integer(), nullable=True))
    op.add_column('tutors', sa.Column('communication_style', sa.Integer(), nullable=True))
    op.add_column('tutors', sa.Column('confidence_level', sa.Integer(), nullable=True))
    op.add_column('tutors', sa.Column('preferred_student_level', sa.String(length=50), nullable=True))
    op.add_column('tutors', sa.Column('preferences_json', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Create students table
    op.create_table('students',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('sex', sa.String(length=10), nullable=True),
    sa.Column('preferred_pace', sa.Integer(), nullable=False),
    sa.Column('preferred_teaching_style', sa.String(length=50), nullable=False),
    sa.Column('communication_style_preference', sa.Integer(), nullable=False),
    sa.Column('urgency_level', sa.Integer(), nullable=False),
    sa.Column('learning_goals', sa.String(length=500), nullable=True),
    sa.Column('previous_tutoring_experience', sa.Integer(), server_default='0', nullable=False),
    sa.Column('previous_satisfaction', sa.Integer(), nullable=True),
    sa.Column('preferences_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_students_age', 'students', ['age'], unique=False)
    op.create_index('ix_students_created_at', 'students', ['created_at'], unique=False)
    op.create_index('ix_students_preferred_pace', 'students', ['preferred_pace'], unique=False)
    
    # Create match_predictions table
    op.create_table('match_predictions',
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('tutor_id', sa.UUID(), nullable=False),
    sa.Column('churn_probability', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('risk_level', sa.String(length=20), nullable=False),
    sa.Column('compatibility_score', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('pace_mismatch', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('style_mismatch', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('communication_mismatch', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('age_difference', sa.Integer(), nullable=False),
    sa.Column('ai_explanation', sa.Text(), nullable=True),
    sa.Column('model_version', sa.String(length=50), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
    sa.ForeignKeyConstraint(['tutor_id'], ['tutors.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'tutor_id', name='uq_match_predictions_student_tutor')
    )
    op.create_index('ix_match_predictions_student_id', 'match_predictions', ['student_id'], unique=False)
    op.create_index('ix_match_predictions_tutor_id', 'match_predictions', ['tutor_id'], unique=False)
    op.create_index('ix_match_predictions_risk_level', 'match_predictions', ['risk_level'], unique=False)
    op.create_index('ix_match_predictions_churn_probability', 'match_predictions', ['churn_probability'], unique=False)
    op.create_index('ix_match_predictions_compatibility_score', 'match_predictions', ['compatibility_score'], unique=False)


def downgrade() -> None:
    # Drop match_predictions table
    op.drop_index('ix_match_predictions_compatibility_score', table_name='match_predictions')
    op.drop_index('ix_match_predictions_churn_probability', table_name='match_predictions')
    op.drop_index('ix_match_predictions_risk_level', table_name='match_predictions')
    op.drop_index('ix_match_predictions_tutor_id', table_name='match_predictions')
    op.drop_index('ix_match_predictions_student_id', table_name='match_predictions')
    op.drop_table('match_predictions')
    
    # Drop students table
    op.drop_index('ix_students_preferred_pace', table_name='students')
    op.drop_index('ix_students_created_at', table_name='students')
    op.drop_index('ix_students_age', table_name='students')
    op.drop_table('students')
    
    # Remove columns from tutors table
    op.drop_column('tutors', 'preferences_json')
    op.drop_column('tutors', 'preferred_student_level')
    op.drop_column('tutors', 'confidence_level')
    op.drop_column('tutors', 'communication_style')
    op.drop_column('tutors', 'preferred_pace')
    op.drop_column('tutors', 'teaching_style')
    op.drop_column('tutors', 'experience_years')
    op.drop_column('tutors', 'sex')
    op.drop_column('tutors', 'age')

