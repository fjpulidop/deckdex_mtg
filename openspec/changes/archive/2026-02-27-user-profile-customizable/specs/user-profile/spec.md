## ADDED Requirements

### Requirement: Profile modal is accessible from the user dropdown
The frontend SHALL provide a profile editor modal opened from the navbar user dropdown.

#### Scenario: Open profile modal from dropdown
- **WHEN** an authenticated user clicks their avatar in the navbar
- **THEN** a dropdown appears with "Profile", "Settings", and "Logout" options
- **WHEN** the user clicks "Profile"
- **THEN** the `ProfileModal` SHALL open as an overlay without navigating away from the current page

### Requirement: Profile modal displays current user data
The `ProfileModal` SHALL display the user's current `display_name` and avatar.

#### Scenario: Modal shows current display name
- **WHEN** the `ProfileModal` opens
- **THEN** the display name input SHALL be pre-filled with the user's current `display_name`

#### Scenario: Modal shows current avatar
- **WHEN** the `ProfileModal` opens and the user has an `avatar_url`
- **THEN** the avatar SHALL be rendered as a circular image filling the avatar area

#### Scenario: Modal shows fallback when no avatar
- **WHEN** the `ProfileModal` opens and the user has no `avatar_url`
- **THEN** a generic user icon placeholder SHALL be shown in the avatar area

### Requirement: User can change display name
The `ProfileModal` SHALL allow the user to edit their `display_name`.

#### Scenario: Display name field is editable
- **WHEN** the `ProfileModal` is open
- **THEN** the display name field SHALL be an editable text input
- **THEN** changes to the field SHALL be reflected in the input immediately

#### Scenario: Empty display name is rejected
- **WHEN** the user clears the display name field and clicks Save
- **THEN** the modal SHALL display a validation error and SHALL NOT call the API

### Requirement: User can upload a profile photo with interactive crop
The `ProfileModal` SHALL allow the user to upload a photo and interactively position it in a circular crop.

#### Scenario: Avatar area triggers file picker
- **WHEN** the user clicks the avatar area or the "Change photo" button in the `ProfileModal`
- **THEN** a file picker SHALL open with `accept="image/*"`

#### Scenario: Photo crop modal appears after file selection
- **WHEN** the user selects an image file
- **THEN** a crop sub-modal SHALL appear over the `ProfileModal`
- **THEN** the crop sub-modal SHALL show the image with a circular crop overlay
- **THEN** the user SHALL be able to drag the image to reposition it within the circle
- **THEN** a zoom slider SHALL allow the user to scale the image in or out

#### Scenario: Confirming crop returns to profile modal
- **WHEN** the user clicks "Apply" in the crop sub-modal
- **THEN** the crop sub-modal SHALL close
- **THEN** the `ProfileModal` avatar preview SHALL update to show the cropped circular image
- **THEN** the crop result SHALL be stored as a JPEG base64 data URI (max 256×256px, quality 0.85)

#### Scenario: Cancelling crop discards changes
- **WHEN** the user clicks "Cancel" in the crop sub-modal
- **THEN** the crop sub-modal SHALL close without changing the avatar preview

### Requirement: User can save profile changes
The `ProfileModal` SHALL persist changes to `display_name` and `avatar_url` via the API.

#### Scenario: Save calls PATCH /api/auth/profile
- **WHEN** the user clicks "Save" in the `ProfileModal`
- **THEN** the frontend SHALL call `PATCH /api/auth/profile` with `{ display_name, avatar_url }` (either or both may be included)
- **THEN** a loading indicator SHALL be shown on the Save button during the request

#### Scenario: Successful save updates navbar
- **WHEN** `PATCH /api/auth/profile` returns 200
- **THEN** `AuthContext.refreshUser()` SHALL be called
- **THEN** the navbar SHALL immediately reflect the new display name and avatar
- **THEN** the `ProfileModal` SHALL close

#### Scenario: Save error is shown
- **WHEN** `PATCH /api/auth/profile` returns an error
- **THEN** the `ProfileModal` SHALL display an error message
- **THEN** the modal SHALL remain open

### Requirement: Profile modal can be dismissed
The `ProfileModal` SHALL be dismissible without saving.

#### Scenario: Cancel button closes modal
- **WHEN** the user clicks "Cancel" in the `ProfileModal`
- **THEN** the modal SHALL close without calling the API

#### Scenario: ESC key closes modal
- **WHEN** the user presses ESC while the `ProfileModal` is open
- **THEN** the modal SHALL close without calling the API
