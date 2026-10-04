from fleet_maintenance.persistence.database import SessionLocal, create_schema
from fleet_maintenance.services.records import seed_demo

if __name__ == "__main__":
    create_schema()
    with SessionLocal() as session:
        print("seeded" if seed_demo(session) else "already seeded")
