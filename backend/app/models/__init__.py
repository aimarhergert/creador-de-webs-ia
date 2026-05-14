from app.database import Base

# Core models (no cross-deps beyond Base)
from app.models.user import User, UserRole
from app.models.asset import Asset, AssetType, AssetStatus, MonetizationModel
from app.models.deployment import Deployment, DeploymentPlatform, DeploymentStatus
from app.models.metrics import Metrics
from app.models.wallet import Wallet, WalletTransaction, TransactionType
from app.models.activity import ActivityEvent, EventType

# Sprint-1 models
from app.models.strategy import Strategy, StrategyType, STRATEGY_PRESETS
from app.models.project import Project, ProjectStatus
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus, PLAN_CONFIG
from app.models.optimization_log import OptimizationLog, OptimizationDecision
from app.models.traffic_simulation import TrafficSimulation
from app.models.investment import Investment, InvestmentStatus
from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog

# Sprint-2 models (scanner, blog, sectors)
from app.models.sector import Sector, SectorEnum, SECTOR_PRESETS
from app.models.scan import WebScan
from app.models.blog import BlogPost, BlogStatus

__all__ = [
    "Base",
    # existing
    "Asset", "AssetType", "AssetStatus", "MonetizationModel",
    "Deployment", "DeploymentPlatform", "DeploymentStatus",
    "Metrics",
    "User", "UserRole",
    "Wallet", "WalletTransaction", "TransactionType",
    "ActivityEvent", "EventType",
    # sprint-1
    "Strategy", "StrategyType", "STRATEGY_PRESETS",
    "Project", "ProjectStatus",
    "Subscription", "SubscriptionPlan", "SubscriptionStatus", "PLAN_CONFIG",
    "OptimizationLog", "OptimizationDecision",
    "TrafficSimulation",
    "Investment", "InvestmentStatus",
    "ApiKey",
    "AuditLog",
    # sprint-2
    "Sector", "SectorEnum", "SECTOR_PRESETS",
    "WebScan",
    "BlogPost", "BlogStatus",
]
