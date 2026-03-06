## ADDED Requirements

### Requirement: Import wizard includes Review step
The import wizard SHALL include 6 steps: upload → resolve → review → mode → progress → result. The resolve step replaces the previous preview step and includes format detection, card count, and per-card resolution status.

#### Scenario: Step indicator shows 6 steps
- **WHEN** the user opens the import page
- **THEN** the step indicator SHALL display 6 numbered steps

#### Scenario: Upload triggers resolve instead of preview
- **WHEN** the user uploads a file or submits pasted text
- **THEN** the wizard SHALL call the resolve endpoint and advance to the review step upon completion
