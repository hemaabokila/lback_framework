"""
This file serves as the initialization point for the 'lback_framework/lback/auth' package.
It is designed to expose the core components necessary for handling various authentication
and authorization mechanisms within the Lback web framework. This package centralizes
the definition and management of security-related functionalities, including different
authentication schemes, password management, and permission enforcement.

---

**Key Components Exposed by this Package:**

1.  **SessionAuth (from .session_auth):**
    Manages session-based authentication for users. This component is typically responsible
    for creating and managing user sessions, storing session data (e.g., user ID) on the server
    and providing a session ID to the client (often via cookies). It handles login, logout,
    and session validation to maintain user state across requests.

2.  **PermissionRequired (from .permissions):**
    A decorator or utility class used to enforce permissions on views or specific actions.
    This component ensures that only users with the necessary permissions are allowed to
    access certain resources or perform specific operations. It integrates with the
    authentication system to check a user's assigned roles or permissions.

3.  **PasswordHasher (from .password_hashing):**
    Provides utilities for securely hashing and verifying user passwords. This component
    is critical for protecting sensitive user credentials by converting plain-text passwords
    into irreversible hash values before storage, and then securely comparing them during login
    attempts without exposing the original password. It typically supports various hashing algorithms.

4.  **OAuth2Auth (from .oauth):**
    Implements support for the OAuth 2.0 authorization framework. This component enables
    Lback applications to integrate with external identity providers (e.g., Google, Facebook)
    for user authentication and authorization, allowing users to grant limited access to their
    data without sharing their credentials directly with the application.

5.  **JWTAuth (from .jwt_auth):**
    Implements JSON Web Token (JWT) based authentication. This component handles the creation,
    signing, and validation of JWTs, which are commonly used for stateless authentication in APIs.
    It allows users to obtain a token upon successful login, which they then include in subsequent
    requests to prove their identity without needing to re-authenticate with each request.

6.  **AdminAuth (from .adminauth):**
    Specifically handles authentication logic for the administrative interface. This component
    might extend or specialize the general authentication mechanisms to cater to the unique
    requirements of admin users, potentially including stricter security policies or different
    login flows for administrative access.
"""
