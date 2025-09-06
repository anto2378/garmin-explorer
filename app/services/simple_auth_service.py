"""
Simple Authentication Service - Uses .env credentials for 2-3 users
No JWT, no complex auth - just simple email/password matching
"""

import os
from typing import Optional, Dict, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.group import Group, GroupMembership, UserRole
from app.core.encryption import encrypt_credential


class UserCredentials(BaseModel):
    """User credentials from environment"""
    email: str
    password: str
    name: str
    garmin_email: str
    garmin_password: str
    role: str


class SimpleAuthService:
    """Simple authentication service using .env credentials"""
    
    def __init__(self):
        self.users = self._load_users_from_env()
    
    def _load_users_from_env(self) -> Dict[str, UserCredentials]:
        """Load user credentials from environment variables"""
        users = {}
        
        # Check for up to 5 users (expandable)
        for i in range(1, 6):
            email = os.getenv(f'USER{i}_EMAIL')
            password = os.getenv(f'USER{i}_PASSWORD')
            name = os.getenv(f'USER{i}_NAME')
            garmin_email = os.getenv(f'USER{i}_GARMIN_EMAIL')
            garmin_password = os.getenv(f'USER{i}_GARMIN_PASSWORD')
            role = os.getenv(f'USER{i}_ROLE', 'member')
            
            if email and password and name and garmin_email and garmin_password:
                users[email.lower()] = UserCredentials(
                    email=email,
                    password=password,
                    name=name,
                    garmin_email=garmin_email,
                    garmin_password=garmin_password,
                    role=role
                )
        
        return users
    
    def authenticate(self, email: str, password: str) -> Optional[UserCredentials]:
        """Authenticate user with email/password"""
        user_creds = self.users.get(email.lower())
        if user_creds and user_creds.password == password:
            return user_creds
        return None
    
    def get_all_users(self) -> List[UserCredentials]:
        """Get all configured users"""
        return list(self.users.values())
    
    def setup_database_users(self, db: Session) -> Dict[str, str]:
        """Setup users in database based on .env configuration"""
        created_users = {}
        
        for user_creds in self.users.values():
            # Check if user exists
            existing_user = db.query(User).filter(User.email == user_creds.email).first()
            
            if not existing_user:
                # Create new user
                user = User(
                    email=user_creds.email,
                    full_name=user_creds.name,
                    garmin_email=encrypt_credential(user_creds.garmin_email),
                    garmin_password=encrypt_credential(user_creds.garmin_password),
                    is_active=True
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                created_users[user_creds.email] = str(user.id)
                print(f"✅ Created user: {user_creds.name} ({user_creds.email})")
            else:
                created_users[user_creds.email] = str(existing_user.id)
                print(f"ℹ️  User exists: {user_creds.name} ({user_creds.email})")
        
        return created_users
    
    def setup_default_group(self, db: Session, user_ids: Dict[str, str]) -> Optional[str]:
        """Setup default group with all users"""
        group_name = os.getenv('DEFAULT_GROUP_NAME', 'Fitness Crew')
        group_description = os.getenv('DEFAULT_GROUP_DESCRIPTION', 'Weekly fitness tracking')
        whatsapp_group_id = os.getenv('DEFAULT_WHATSAPP_GROUP_ID', 'default-group@g.us')
        
        # Check if group exists
        existing_group = db.query(Group).filter(Group.name == group_name).first()
        if existing_group:
            print(f"ℹ️  Group exists: {group_name}")
            return str(existing_group.id)
        
        # Find admin user
        admin_user_email = None
        for email, user_creds in self.users.items():
            if user_creds.role == 'admin':
                admin_user_email = email
                break
        
        if not admin_user_email:
            admin_user_email = list(self.users.keys())[0]  # First user as admin
        
        admin_user_id = user_ids[admin_user_email]
        
        # Create group
        group = Group(
            name=group_name,
            description=group_description,
            whatsapp_group_id=whatsapp_group_id,
            admin_user_id=admin_user_id,
            digest_schedule=os.getenv('DIGEST_SCHEDULE', '0 8 * * 1'),
            is_active=True
        )
        
        db.add(group)
        db.commit()
        db.refresh(group)
        
        # Add all users to group
        for email, user_id in user_ids.items():
            user_creds = self.users[email]
            role = UserRole.ADMIN if user_creds.role == 'admin' else UserRole.MEMBER
            
            membership = GroupMembership(
                group_id=group.id,
                user_id=user_id,
                role=role
            )
            
            db.add(membership)
        
        db.commit()
        
        print(f"✅ Created group: {group_name} with {len(user_ids)} members")
        return str(group.id)


# Global instance
auth_service = SimpleAuthService()