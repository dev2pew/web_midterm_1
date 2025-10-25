# LuckyForums Test Plan

## 1. User Roles (Points of View)

-   **Guest (Anonymous):** Unauthenticated visitor.
-   **User (Authenticated):** A standard, logged-in user.
-   **Admin (Staff/Superuser):** A logged-in user with `is_staff` or `is_superuser` privileges.

---

## 2. Test Cases by Feature

### 2.1. Authentication & Accounts

| Action                  | Guest (Anonymous)          | User (Authenticated)       | Admin (Authenticated)      |
| ----------------------- | -------------------------- | -------------------------- | -------------------------- |
| **View Register Page**  | Permit (200)               | Redirect to Home           | Redirect to Home           |
| **Submit Registration** | Permit (Success)           | Redirect to Home           | Redirect to Home           |
| **View Login Page**     | Permit (200)               | Redirect to Home           | Redirect to Home           |
| **Submit Login**        | Permit (Success)           | Redirect to Home           | Redirect to Home           |
| **Logout**              | Redirect to Login          | Permit (Success)           | Permit (Success)           |
| **View `/api/auth/me`** | Prohibit (401/403)         | Permit (200, own data)     | Permit (200, own data)     |

### 2.2. Page Visibility & Basic Content

| Page / View             | Guest (Anonymous)                                | User (Authenticated)                             | Admin (Authenticated)                            |
| ----------------------- | ------------------------------------------------ | ------------------------------------------------ | ------------------------------------------------ |
| **Home Page (`/`)**     | Permit (200). Can see threads, login button.     | Permit (200). Can see threads, profile link.     | Permit (200). Can see threads, profile link.     |
| **Thread Detail (`/t/`)** | Permit (200). Can see posts, no reply form.      | Permit (200). Can see posts, can see reply form. | Permit (200). Can see posts, can see reply form. |
| **Profile Page (`/u/`)** | Permit (200). Can see profile, no comment form.  | Permit (200). Can see profile and comment form.  | Permit (200). Can see profile and comment form.  |
| **About Page (`/about/`)** | Permit (200).                                    | Permit (200).                                    | Permit (200).                                    |

### 2.3. Forum: Threads

| Action                  | Guest (Anonymous)  | User (Authenticated)       | Admin (Authenticated)      |
| ----------------------- | ------------------ | -------------------------- | -------------------------- |
| **Create Thread**       | Prohibit (401/403) | Permit (201)               | Permit (201)               |
| **Edit Own Thread**     | Prohibit (401/403) | Permit (200)               | Permit (200)               |
| **Edit Other's Thread** | Prohibit (401/403) | Prohibit (403)             | Permit (200)               |
| **Delete Own Thread**   | Prohibit (401/403) | Permit (204)               | Permit (204)               |
| **Delete Other's Thread** | Prohibit (401/403) | Prohibit (403)             | Permit (204)               |

### 2.4. Forum: Posts (Comments on Threads)

| Action                | Guest (Anonymous)  | User (Authenticated)     | Admin (Authenticated)    |
| --------------------- | ------------------ | ------------------------ | ------------------------ |
| **Create Post**       | Prohibit (401/403) | Permit (201)             | Permit (201)             |
| **Edit Own Post**     | Prohibit (401/403) | Permit (200)             | Permit (200)             |
| **Edit Other's Post** | Prohibit (401/403) | Prohibit (403)           | Permit (200)             |
| **Delete Own Post**   | Prohibit (401/403) | Permit (204)             | Permit (204)             |
| **Delete Other's Post** | Prohibit (401/403) | Prohibit (403)           | Permit (204)             |
| **Vote on Post**      | Prohibit (401/403) | Permit (200)             | Permit (200)             |
| **View Post History** | Prohibit (401/403) | Prohibit (403)           | Permit (200)             |

### 2.5. User Profiles & Comments

| Action                           | Guest (Anonymous)  | User (Authenticated)                                | Admin (Authenticated)                               |
| -------------------------------- | ------------------ | --------------------------------------------------- | --------------------------------------------------- |
| **Edit Own Profile**             | Prohibit (401/403) | Permit (200)                                        | Permit (200)                                        |
| **Edit Other's Profile**         | Prohibit (401/403) | Prohibit (403)                                      | Permit (via Admin Panel, not API)                   |
| **Create Comment on Profile**    | Prohibit (401/403) | Permit (201)                                        | Permit (201)                                        |
| **Edit Own Profile Comment**     | Prohibit (401/403) | Permit (200)                                        | Permit (200)                                        |
| **Edit Other's Profile Comment** | Prohibit (401/403) | Prohibit (403)                                      | Permit (200)                                        |
| **Delete Own Profile Comment**   | Prohibit (401/403) | Permit (204)                                        | Permit (204)                                        |
| **Delete Other's Profile Comment** | Prohibit (401/403) | Prohibit (403)                                      | Permit (204)                                        |
| **Delete Comment on Own Profile**  | Prohibit (401/403) | Permit (204, if commenter is another user)          | Permit (204)                                        |
| **Vote on Profile Comment**      | Prohibit (401/403) | Permit (200)                                        | Permit (200)                                        |
| **View Profile Comment History** | Prohibit (401/403) | Prohibit (403)                                      | Permit (200)                                        |

### 2.6. Moderation

| Action                    | Guest (Anonymous)  | User (Authenticated) | Admin (Authenticated)                                    |
| ------------------------- | ------------------ | -------------------- | -------------------------------------------------------- |
| **Silence a User**        | Prohibit (401/403) | Prohibit (403)       | Permit (200, unless target is another admin/self)        |
| **Ban a User**            | Prohibit (401/403) | Prohibit (403)       | Permit (200, unless target is another admin/self)        |
| **Silence an Admin**      | Prohibit (401/403) | Prohibit (403)       | Prohibit (403, unless actor is Superuser)                |
| **Ban an Admin**          | Prohibit (401/403) | Prohibit (403)       | Prohibit (403, unless actor is Superuser)                |
| **(As Silenced User) Post** | N/A                | Prohibit (403)       | Prohibit (403, if an admin gets silenced by superuser) |
| **(As Banned User) View**   | N/A                | Prohibit (403)       | Prohibit (403, if an admin gets banned by superuser)   |

### 2.7. Notifications

| Action                       | Guest (Anonymous)  | User (Authenticated) | Admin (Authenticated) |
| ---------------------------- | ------------------ | -------------------- | --------------------- |
| **Receive on Thread Reply**  | N/A                | Yes                  | Yes                   |
| **Receive on Profile Comment** | N/A                | Yes                  | Yes                   |
| **Receive on @mention**      | N/A                | Yes                  | Yes                   |
| **List Notifications**       | Prohibit (401/403) | Permit (200)         | Permit (200)          |
| **Mark Notification as Read**  | Prohibit (401/403) | Permit (200)         | Permit (200)          |
