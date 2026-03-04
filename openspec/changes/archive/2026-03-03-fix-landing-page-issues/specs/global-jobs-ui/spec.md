## ADDED Requirements

### Requirement: Jobs bar excluded from public pages
The `JobsBottomBar` component SHALL NOT render on public pages (landing `/` and login `/login`). It SHALL only render on authenticated application routes where job management is relevant.

#### Scenario: Landing page has no jobs bar
- **WHEN** a visitor navigates to the landing page (`/`)
- **THEN** the `JobsBottomBar` component is not present in the DOM

#### Scenario: Login page has no jobs bar
- **WHEN** a user navigates to the login page (`/login`)
- **THEN** the `JobsBottomBar` component is not present in the DOM

#### Scenario: Authenticated route shows jobs bar
- **WHEN** an authenticated user navigates to `/dashboard`
- **THEN** the `JobsBottomBar` component is rendered as usual
