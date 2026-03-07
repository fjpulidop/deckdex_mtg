## ADDED Requirements

### Requirement: Animation pauses when tab is hidden
Both background components SHALL pause their animation loops when the browser tab is not visible, and SHALL resume when the tab becomes visible again.

#### Scenario: Animation pauses on tab switch
- **WHEN** the user switches to a different browser tab or minimizes the window
- **THEN** the `requestAnimationFrame` loop in both `AetherParticles` and `CardMatrix` SHALL be cancelled within one frame
- **THEN** no further draw or update calls SHALL be made while the tab is hidden

#### Scenario: Animation resumes on tab return
- **WHEN** the user returns to the tab after it was hidden
- **THEN** the animation loop SHALL resume from its last state without reinitializing particles or drops
- **THEN** particle and drop positions SHALL be continuous with where they were when the tab was hidden

#### Scenario: Animation does not pause when tab remains visible
- **WHEN** the tab remains in the foreground
- **THEN** the animation loop SHALL run uninterrupted as before

### Requirement: CardMatrix glow rendering does not use real-time shadow blur
The `CardMatrix` component SHALL render mana symbol glow effects using pre-rendered off-screen canvases rather than setting `ctx.shadowBlur` on every draw call.

#### Scenario: Dark mode glow renders without shadowBlur on main context
- **WHEN** the theme is dark and `CardMatrix` is animating
- **THEN** `ctx.shadowBlur` SHALL NOT be set to a non-zero value on the main canvas context during the animation loop
- **THEN** each mana symbol SHALL still display a visible glow halo consistent with current appearance

#### Scenario: Glow cache is invalidated on theme change
- **WHEN** the user toggles between dark and light theme
- **THEN** the off-screen glow canvas cache SHALL be cleared
- **THEN** new cache entries SHALL be populated on the next draw frame using the correct colors for the new theme

#### Scenario: Light mode glow pass is skipped
- **WHEN** the theme is light
- **THEN** no glow pass SHALL be performed (consistent with existing behavior)
- **THEN** no shadow blur or off-screen canvas drawing SHALL occur

### Requirement: Theme changes do not restart the animation loop
Both background components SHALL update their rendering to reflect a theme change without cancelling and restarting the animation loop.

#### Scenario: Theme toggle does not cause canvas blank frame
- **WHEN** the user toggles between dark and light theme
- **THEN** the canvas SHALL NOT be blank or flicker during the theme transition
- **THEN** the animation loop SHALL continue running without interruption
- **THEN** particles and drops SHALL begin rendering in the new theme colors on the next animation frame

#### Scenario: Particle state is preserved across theme changes
- **WHEN** the user toggles the theme while the animation is running
- **THEN** particle and drop positions, velocities, and opacities SHALL be preserved
- **THEN** no reinitialization of the particle or drop arrays SHALL occur
