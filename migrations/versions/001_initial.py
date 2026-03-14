"""
Initial database migration - creates all tables.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""

    # ==========================================================================
    # articles table
    # ==========================================================================
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("meta_description", sa.String(200), nullable=True),
        sa.Column("keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("primary_keyword", sa.String(200), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "generating", "generated", "optimizing", "optimized",
                "publishing", "published", "failed", "archived",
                name="articlestatus",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "article_type",
            sa.Enum(
                "standard", "comparison", "tutorial", "listicle", "case_study", "news",
                name="articletype",
            ),
            nullable=False,
            server_default="standard",
        ),
        sa.Column("seo_score", sa.Float(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("readability_score", sa.Float(), nullable=True),
        sa.Column("keyword_density", sa.Float(), nullable=True),
        sa.Column("competitor_target", sa.String(200), nullable=True),
        sa.Column("published_url", sa.String(1000), nullable=True),
        sa.Column("github_sha", sa.String(100), nullable=True),
        sa.Column("schema_markup", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("internal_links", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("headings", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("organic_clicks", sa.Integer(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("average_position", sa.Float(), nullable=True),
        sa.Column("ctr", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generation_model", sa.String(100), nullable=True),
        sa.Column("generation_prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("generation_completion_tokens", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_articles_id", "articles", ["id"])
    op.create_index("ix_articles_title", "articles", ["title"])
    op.create_unique_constraint("uq_articles_slug", "articles", ["slug"])
    op.create_index("ix_articles_slug", "articles", ["slug"])
    op.create_index("ix_articles_status", "articles", ["status"])

    # ==========================================================================
    # keywords table
    # ==========================================================================
    op.create_table(
        "keywords",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("term", sa.String(500), nullable=False),
        sa.Column("search_volume", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("cpc", sa.Float(), nullable=True),
        sa.Column("opportunity_score", sa.Float(), nullable=True),
        sa.Column("competitor", sa.String(200), nullable=True),
        sa.Column("competitor_domain", sa.String(200), nullable=True),
        sa.Column("trend", sa.String(50), nullable=True),
        sa.Column("trend_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("current_position", sa.Integer(), nullable=True),
        sa.Column("previous_position", sa.Integer(), nullable=True),
        sa.Column("best_position", sa.Integer(), nullable=True),
        sa.Column("has_featured_snippet", sa.Boolean(), server_default="false"),
        sa.Column("has_local_pack", sa.Boolean(), server_default="false"),
        sa.Column("has_knowledge_panel", sa.Boolean(), server_default="false"),
        sa.Column("has_video_results", sa.Boolean(), server_default="false"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("tags", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("has_article", sa.Boolean(), server_default="false"),
        sa.Column("is_seed", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_keywords_id", "keywords", ["id"])
    op.create_unique_constraint("uq_keywords_term", "keywords", ["term"])
    op.create_index("ix_keywords_term", "keywords", ["term"])

    # ==========================================================================
    # competitors table
    # ==========================================================================
    op.create_table(
        "competitors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("domain", sa.String(200), nullable=False),
        sa.Column("keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("gap_keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("traffic_estimate", sa.Integer(), nullable=True),
        sa.Column("domain_authority", sa.Integer(), nullable=True),
        sa.Column("backlinks_count", sa.Integer(), nullable=True),
        sa.Column("content_gaps", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("article_ideas", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("their_strengths", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("their_weaknesses", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("recommended_strategy", sa.String(2000), nullable=True),
        sa.Column("serp_overlap_percentage", sa.Float(), nullable=True),
        sa.Column("shared_keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("has_comparison_article", sa.Boolean(), server_default="false"),
        sa.Column("comparison_article_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("analysis_status", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_analyzed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitors_id", "competitors", ["id"])
    op.create_unique_constraint("uq_competitors_name", "competitors", ["name"])
    op.create_unique_constraint("uq_competitors_domain", "competitors", ["domain"])
    op.create_index("ix_competitors_name", "competitors", ["name"])
    op.create_index("ix_competitors_domain", "competitors", ["domain"])

    # ==========================================================================
    # seo_reports table
    # ==========================================================================
    op.create_table(
        "seo_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("total_impressions", sa.Integer(), nullable=True),
        sa.Column("total_clicks", sa.Integer(), nullable=True),
        sa.Column("average_ctr", sa.Float(), nullable=True),
        sa.Column("keywords_in_top_10", sa.Integer(), nullable=True),
        sa.Column("articles_published", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_reports_id", "seo_reports", ["id"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("seo_reports")
    op.drop_table("competitors")
    op.drop_table("keywords")
    op.drop_table("articles")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS articlestatus")
    op.execute("DROP TYPE IF EXISTS articletype")
