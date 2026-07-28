from fastapi import Depends, HTTPException, status
from fast_api.dependencies.auth import get_current_user
from fast_api.models.user import User
from typing import List

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role: {current_user.role}. Requires one of: {self.allowed_roles}"
            )
        return current_user

# Common shorthand checkers
allow_super_admin = RoleChecker(["super_admin"])
allow_agent = RoleChecker(["super_admin", "agent"])
allow_customer = RoleChecker(["super_admin", "customer"])
