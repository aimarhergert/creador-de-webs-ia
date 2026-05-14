"""Baseline — existing tables created via create_all

Revision ID: 001
Revises:
Create Date: 2026-05-13
"""
from typing import Sequence, Union
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing tables (users, wallets, wallet_transactions, assets, deployments,
    # metrics, activity_events) were created via SQLAlchemy create_all.
    # This migration just marks the baseline so future revisions can chain from it.
    pass


def downgrade() -> None:
    pass
