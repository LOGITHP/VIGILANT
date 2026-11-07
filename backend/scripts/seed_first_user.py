"""
VIGILANT - Ephemeral Bootstrap Initial User Seeding Script
Seeds cctv@gmail.com / 123456789 on the first boot into the persistent PostgreSQL database volume.
Automatically scrubs and wipes itself out after execution.
"""
import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add parent directory to sys.path so app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, Role, Permission, user_roles, role_permissions
from app.models.audit import AuditLog


async def seed_database():
    print("[VIGILANT BOOTSTRAP] Checking database for initial administrator...")
    admin_email = settings.INITIAL_ADMIN_EMAIL.strip().lower()
    raw_password = settings.INITIAL_ADMIN_PASSWORD

    async with AsyncSessionLocal() as session:
        # Check if user already exists in the persistent volume
        query = select(User).where(User.email == admin_email).options(selectinload(User.roles))
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"[VIGILANT BOOTSTRAP] User '{admin_email}' already exists in persistent database volume. Skipping creation.")
            return

        print(f"[VIGILANT BOOTSTRAP] Initializing roles and permissions...")
        # 1. Setup Roles
        roles_config = [
            ("SUPERADMIN", "Full system access to CCTV feeds, AI models, and user administration"),
            ("OPERATOR", "Access to view and control PTZ cameras and acknowledge alerts"),
            ("VIEWER", "Read-only access to assigned CCTV surveillance streams")
        ]

        roles_map = {}
        for role_name, description in roles_config:
            r_query = select(Role).where(Role.name == role_name)
            role = (await session.execute(r_query)).scalar_one_or_none()
            if not role:
                role = Role(name=role_name, description=description)
                session.add(role)
                await session.flush()
            roles_map[role_name] = role

        # 2. Setup Permissions
        permissions_list = [
            ("camera:view", "camera", "view"),
            ("camera:ptz_control", "camera", "control"),
            ("camera:manage", "camera", "manage"),
            ("ai:detections", "ai_model", "view"),
            ("audit:read", "audit", "read"),
            ("user:manage", "user", "manage")
        ]
        created_permissions = []
        for perm_name, resource, action in permissions_list:
            p_query = select(Permission).where(Permission.name == perm_name)
            perm = (await session.execute(p_query)).scalar_one_or_none()
            if not perm:
                perm = Permission(name=perm_name, resource=resource, action=action)
                session.add(perm)
                await session.flush()
            created_permissions.append(perm)

        # Associate permissions with SUPERADMIN role using direct association insert
        superadmin_role = roles_map["SUPERADMIN"]
        for perm in created_permissions:
            perm_check = select(role_permissions).where(
                role_permissions.c.role_id == superadmin_role.id,
                role_permissions.c.permission_id == perm.id
            )
            exists = (await session.execute(perm_check)).first()
            if not exists:
                await session.execute(
                    role_permissions.insert().values(
                        role_id=superadmin_role.id,
                        permission_id=perm.id
                    )
                )

        # 3. Create Super Admin User
        print(f"[VIGILANT BOOTSTRAP] Creating superadmin account: '{admin_email}'...")
        hashed = hash_password(raw_password)
        admin_user = User(
            email=admin_email,
            hashed_password=hashed,
            full_name="VIGILANT System Administrator",
            is_active=True,
            is_superuser=True
        )
        session.add(admin_user)
        await session.flush()

        # Link user to SUPERADMIN role
        await session.execute(
            user_roles.insert().values(
                user_id=admin_user.id,
                role_id=superadmin_role.id
            )
        )

        # 4. Create Audit Log Entry
        audit = AuditLog(
            user_id=admin_user.id,
            event="SEED_INITIAL_SUPERADMIN",
            ip_address="127.0.0.1",
            user_agent="VIGILANT Bootstrap / Docker Entrypoint",
            details={
                "email": admin_email,
                "role": "SUPERADMIN",
                "notice": "Initial account provisioned automatically."
            }
        )
        session.add(audit)
        await session.commit()
        print(f"[VIGILANT BOOTSTRAP] Successfully provisioned '{admin_email}'.")


def wipeout_self():
    """Securely deletes this seed script from disk to prevent credential remnants."""
    try:
        current_file = os.path.abspath(__file__)
        if os.path.exists(current_file):
            # Overwrite with zeroes before deleting for extra hygiene
            file_len = os.path.getsize(current_file)
            with open(current_file, "wb") as f:
                f.write(b"\x00" * file_len)
            os.remove(current_file)
            print("[VIGILANT BOOTSTRAP] Self-destruction complete: Seed script wiped out.")
    except Exception as e:
        print(f"[VIGILANT BOOTSTRAP] Notice on self-wipe: {e}")


def main():
    try:
        asyncio.run(seed_database())
    finally:
        # Wipe out only if not running inside a pytest suite
        if "pytest" not in sys.modules:
            wipeout_self()


if __name__ == "__main__":
    main()
