"""create schema v2

Revision ID: 0002_schema_v2
Revises: 0001_initial_schema
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_schema_v2"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Permissions table
    op.create_table(
        "permissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name")
    )
    op.create_index(op.f("ix_permissions_name"), "permissions", ["name"], unique=True)
    op.create_index(op.f("ix_permissions_created_at"), "permissions", ["created_at"], unique=False)

    # 2. Roles table
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name")
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)
    op.create_index(op.f("ix_roles_created_at"), "roles", ["created_at"], unique=False)

    # 3. role_permissions join table
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("permission_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id")
    )

    # 4. Users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email")
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)
    op.create_index(op.f("ix_users_created_at"), "users", ["created_at"], unique=False)

    # 5. Districts table
    op.create_table(
        "districts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("population", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("polygon_geometry", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code")
    )
    op.create_index(op.f("ix_districts_name"), "districts", ["name"], unique=True)
    op.create_index(op.f("ix_districts_code"), "districts", ["code"], unique=True)
    op.create_index(op.f("ix_districts_created_at"), "districts", ["created_at"], unique=False)

    # 6. Police Stations table
    op.create_table(
        "police_stations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("district_id", sa.UUID(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_police_stations_name"), "police_stations", ["name"], unique=False)
    op.create_index(op.f("ix_police_stations_district_id"), "police_stations", ["district_id"], unique=False)
    op.create_index(op.f("ix_police_stations_created_at"), "police_stations", ["created_at"], unique=False)

    # 7. Crime Categories table
    op.create_table(
        "crime_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("severity_weight", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name")
    )
    op.create_index(op.f("ix_crime_categories_name"), "crime_categories", ["name"], unique=True)
    op.create_index(op.f("ix_crime_categories_created_at"), "crime_categories", ["created_at"], unique=False)

    # 8. Cases table
    op.create_table(
        "cases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_number", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("assigned_to_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number")
    )
    op.create_index(op.f("ix_cases_case_number"), "cases", ["case_number"], unique=True)
    op.create_index(op.f("ix_cases_title"), "cases", ["title"], unique=False)
    op.create_index(op.f("ix_cases_status"), "cases", ["status"], unique=False)
    op.create_index(op.f("ix_cases_assigned_to_id"), "cases", ["assigned_to_id"], unique=False)
    op.create_index(op.f("ix_cases_created_at"), "cases", ["created_at"], unique=False)

    # 9. Crime Records table
    op.create_table(
        "crime_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("crime_id", sa.String(length=40), nullable=False),
        sa.Column("fir", sa.String(length=60), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("district_id", sa.UUID(), nullable=False),
        sa.Column("police_station_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("victim_name", sa.String(length=140), nullable=False),
        sa.Column("suspect_name", sa.String(length=140), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["crime_categories.id"]),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["police_station_id"], ["police_stations.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crime_id"),
        sa.UniqueConstraint("fir")
    )
    op.create_index(op.f("ix_crime_records_crime_id"), "crime_records", ["crime_id"], unique=True)
    op.create_index(op.f("ix_crime_records_fir"), "crime_records", ["fir"], unique=True)
    op.create_index(op.f("ix_crime_records_status"), "crime_records", ["status"], unique=False)
    op.create_index(op.f("ix_crime_records_severity"), "crime_records", ["severity"], unique=False)
    op.create_index(op.f("ix_crime_records_latitude"), "crime_records", ["latitude"], unique=False)
    op.create_index(op.f("ix_crime_records_longitude"), "crime_records", ["longitude"], unique=False)
    op.create_index(op.f("ix_crime_records_occurred_at"), "crime_records", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_crime_records_case_id"), "crime_records", ["case_id"], unique=False)
    op.create_index(op.f("ix_crime_records_created_at"), "crime_records", ["created_at"], unique=False)

    # 10. Victims table
    op.create_table(
        "victims",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("contact_info", sa.String(length=100), nullable=True),
        sa.Column("crime_record_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["crime_record_id"], ["crime_records.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_victims_name"), "victims", ["name"], unique=False)
    op.create_index(op.f("ix_victims_crime_record_id"), "victims", ["crime_record_id"], unique=False)

    # 11. Suspects table
    op.create_table(
        "suspects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("physical_description", sa.Text(), nullable=True),
        sa.Column("crime_record_id", sa.UUID(), nullable=True),
        sa.Column("case_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["crime_record_id"], ["crime_records.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_suspects_name"), "suspects", ["name"], unique=False)
    op.create_index(op.f("ix_suspects_crime_record_id"), "suspects", ["crime_record_id"], unique=False)
    op.create_index(op.f("ix_suspects_case_id"), "suspects", ["case_id"], unique=False)

    # 12. Gangs table
    op.create_table(
        "gangs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("district_id", sa.UUID(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name")
    )
    op.create_index(op.f("ix_gangs_name"), "gangs", ["name"], unique=True)
    op.create_index(op.f("ix_gangs_risk_score"), "gangs", ["risk_score"], unique=False)
    op.create_index(op.f("ix_gangs_created_at"), "gangs", ["created_at"], unique=False)

    # 13. Offenders table
    op.create_table(
        "offenders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("offender_id", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("gang_name", sa.String(length=120), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("arrests", sa.Integer(), nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False),
        sa.Column("area", sa.String(length=120), nullable=False),
        sa.Column("recidivism_probability", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("offender_id")
    )
    op.create_index(op.f("ix_offenders_offender_id"), "offenders", ["offender_id"], unique=True)
    op.create_index(op.f("ix_offenders_name"), "offenders", ["name"], unique=False)
    op.create_index(op.f("ix_offenders_gang_name"), "offenders", ["gang_name"], unique=False)
    op.create_index(op.f("ix_offenders_risk_score"), "offenders", ["risk_score"], unique=False)
    op.create_index(op.f("ix_offenders_last_activity"), "offenders", ["last_activity"], unique=False)
    op.create_index(op.f("ix_offenders_area"), "offenders", ["area"], unique=False)
    op.create_index(op.f("ix_offenders_created_at"), "offenders", ["created_at"], unique=False)

    # 14. Gang Members table
    op.create_table(
        "gang_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gang_id", sa.UUID(), nullable=False),
        sa.Column("offender_id", sa.UUID(), nullable=False),
        sa.Column("role_in_gang", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["gang_id"], ["gangs.id"]),
        sa.ForeignKeyConstraint(["offender_id"], ["offenders.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_gang_members_gang_id"), "gang_members", ["gang_id"], unique=False)
    op.create_index(op.f("ix_gang_members_offender_id"), "gang_members", ["offender_id"], unique=False)

    # 15. Vehicles table
    op.create_table(
        "vehicles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plate_number", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("color", sa.String(length=40), nullable=False),
        sa.Column("owner_name", sa.String(length=140), nullable=False),
        sa.Column("suspected_crime_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["suspected_crime_id"], ["crime_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plate_number")
    )
    op.create_index(op.f("ix_vehicles_plate_number"), "vehicles", ["plate_number"], unique=True)
    op.create_index(op.f("ix_vehicles_suspected_crime_id"), "vehicles", ["suspected_crime_id"], unique=False)

    # 16. Phones table
    op.create_table(
        "phones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("phone_number", sa.String(length=40), nullable=False),
        sa.Column("imei", sa.String(length=40), nullable=False),
        sa.Column("owner_name", sa.String(length=140), nullable=False),
        sa.Column("suspected_crime_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["suspected_crime_id"], ["crime_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
        sa.UniqueConstraint("imei")
    )
    op.create_index(op.f("ix_phones_phone_number"), "phones", ["phone_number"], unique=True)
    op.create_index(op.f("ix_phones_imei"), "phones", ["imei"], unique=True)
    op.create_index(op.f("ix_phones_suspected_crime_id"), "phones", ["suspected_crime_id"], unique=False)

    # 17. Evidence table
    op.create_table(
        "evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evidence_code", sa.String(length=40), nullable=False),
        sa.Column("crime_record_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=True),
        sa.Column("file_type", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["crime_record_id"], ["crime_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_code")
    )
    op.create_index(op.f("ix_evidence_evidence_code"), "evidence", ["evidence_code"], unique=True)
    op.create_index(op.f("ix_evidence_crime_record_id"), "evidence", ["crime_record_id"], unique=False)

    # 18. Case Notes table
    op.create_table(
        "case_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_case_notes_case_id"), "case_notes", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_notes_author_id"), "case_notes", ["author_id"], unique=False)

    # 19. Patrol Units table
    op.create_table(
        "patrol_units",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("unit_code", sa.String(length=40), nullable=False),
        sa.Column("area", sa.String(length=120), nullable=False),
        sa.Column("coverage_score", sa.Integer(), nullable=False),
        sa.Column("eta_minutes", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("unit_code")
    )
    op.create_index(op.f("ix_patrol_units_unit_code"), "patrol_units", ["unit_code"], unique=True)
    op.create_index(op.f("ix_patrol_units_area"), "patrol_units", ["area"], unique=False)

    # 20. Emergency Calls table
    op.create_table(
        "emergency_calls",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("call_id", sa.String(length=40), nullable=False),
        sa.Column("caller_number", sa.String(length=40), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("dispatch_unit_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dispatch_unit_id"], ["patrol_units.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_id")
    )
    op.create_index(op.f("ix_emergency_calls_call_id"), "emergency_calls", ["call_id"], unique=True)
    op.create_index(op.f("ix_emergency_calls_caller_number"), "emergency_calls", ["caller_number"], unique=False)
    op.create_index(op.f("ix_emergency_calls_status"), "emergency_calls", ["status"], unique=False)

    # 21. CCTV Events table
    op.create_table(
        "cctv_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=40), nullable=False),
        sa.Column("camera_code", sa.String(length=40), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id")
    )
    op.create_index(op.f("ix_cctv_events_event_id"), "cctv_events", ["event_id"], unique=True)
    op.create_index(op.f("ix_cctv_events_camera_code"), "cctv_events", ["camera_code"], unique=False)
    op.create_index(op.f("ix_cctv_events_event_type"), "cctv_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_cctv_events_occurred_at"), "cctv_events", ["occurred_at"], unique=False)

    # 22. Alerts table
    op.create_table(
        "alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("alert_id", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alert_id")
    )
    op.create_index(op.f("ix_alerts_alert_id"), "alerts", ["alert_id"], unique=True)
    op.create_index(op.f("ix_alerts_level"), "alerts", ["level"], unique=False)

    # 23. Risk Predictions table
    op.create_table(
        "risk_predictions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("district_id", sa.UUID(), nullable=False),
        sa.Column("horizon", sa.String(length=40), nullable=False),
        sa.Column("predicted_crime_count", sa.Integer(), nullable=False),
        sa.Column("low_confidence_boundary", sa.Integer(), nullable=False),
        sa.Column("high_confidence_boundary", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_risk_predictions_horizon"), "risk_predictions", ["horizon"], unique=False)

    # 24. Socioeconomic Data table
    op.create_table(
        "socioeconomic_data",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("district_id", sa.UUID(), nullable=False),
        sa.Column("literacy_rate", sa.Float(), nullable=False),
        sa.Column("poverty_rate", sa.Float(), nullable=False),
        sa.Column("unemployment_rate", sa.Float(), nullable=False),
        sa.Column("average_income", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.PrimaryKeyConstraint("id")
    )

    # 25. Criminal Relationships table
    op.create_table(
        "criminal_relationships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_offender_id", sa.UUID(), nullable=False),
        sa.Column("target_offender_id", sa.UUID(), nullable=False),
        sa.Column("relationship_type", sa.String(length=80), nullable=False),
        sa.Column("strength", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_offender_id"], ["offenders.id"]),
        sa.ForeignKeyConstraint(["target_offender_id"], ["offenders.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_criminal_relationships_source_offender_id"), "criminal_relationships", ["source_offender_id"], unique=False)
    op.create_index(op.f("ix_criminal_relationships_target_offender_id"), "criminal_relationships", ["target_offender_id"], unique=False)

    # 26. Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor", sa.String(length=160), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_audit_logs_actor"), "audit_logs", ["actor"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity"), "audit_logs", ["entity"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)

    # 27. Reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("report_type", sa.String(length=60), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("generated_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["generated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_reports_title"), "reports", ["title"], unique=False)
    op.create_index(op.f("ix_reports_report_type"), "reports", ["report_type"], unique=False)
    op.create_index(op.f("ix_reports_created_at"), "reports", ["created_at"], unique=False)

def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("audit_logs")
    op.drop_table("criminal_relationships")
    op.drop_table("socioeconomic_data")
    op.drop_table("risk_predictions")
    op.drop_table("alerts")
    op.drop_table("cctv_events")
    op.drop_table("emergency_calls")
    op.drop_table("patrol_units")
    op.drop_table("case_notes")
    op.drop_table("evidence")
    op.drop_table("phones")
    op.drop_table("vehicles")
    op.drop_table("gang_members")
    op.drop_table("offenders")
    op.drop_table("gangs")
    op.drop_table("suspects")
    op.drop_table("victims")
    op.drop_table("crime_records")
    op.drop_table("cases")
    op.drop_table("crime_categories")
    op.drop_table("police_stations")
    op.drop_table("districts")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
