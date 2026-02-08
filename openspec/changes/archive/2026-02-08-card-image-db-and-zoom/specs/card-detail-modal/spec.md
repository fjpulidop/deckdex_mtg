# Card Detail Modal (delta: image zoom and cursor affordances)

The card image in the detail modal SHALL be clickable to open a larger view (lightbox) and SHALL use cursor affordances to indicate zoom-in and zoom-out.

## ADDED Requirements

### Requirement: Card image SHALL be clickable to open a larger view (lightbox)

The system SHALL make the card image in the card detail modal clickable. When the user clicks the image, the system SHALL open a lightbox overlay that displays the same image at a larger size (e.g. roughly twice the size of the image in the modal). The lightbox SHALL be dismissible by clicking the overlay (backdrop or the large image) or by pressing Escape. When dismissed, the lightbox SHALL close and the user SHALL return to the card detail modal (the modal SHALL remain open). The lightbox SHALL be rendered above the modal (e.g. higher z-index).

#### Scenario: Clicking the card image opens the lightbox
- **WHEN** the user clicks the card image in the card detail modal
- **THEN** the system opens a lightbox overlay showing the same image at a larger size

#### Scenario: Clicking the lightbox or pressing Escape closes the lightbox
- **WHEN** the lightbox is open and the user clicks the overlay (backdrop or large image) or presses Escape
- **THEN** the lightbox closes and the card detail modal remains visible

### Requirement: Cursor SHALL indicate zoom-in on the modal image and zoom-out on the lightbox

The system SHALL use cursor affordances so that (1) when the user hovers over the card image in the modal, the cursor SHALL indicate "zoom in" (e.g. a magnifying glass with plus, such as the CSS `zoom-in` cursor), and (2) when the user hovers over the large image or clickable area in the lightbox, the cursor SHALL indicate "zoom out" (e.g. a magnifying glass with minus, such as the CSS `zoom-out` cursor) to convey that clicking will return to the modal.

#### Scenario: Modal image shows zoom-in cursor on hover
- **WHEN** the user hovers over the card image in the card detail modal
- **THEN** the cursor displays a zoom-in affordance (e.g. magnifying glass with +)

#### Scenario: Lightbox shows zoom-out cursor on hover
- **WHEN** the lightbox is open and the user hovers over the large image or the overlay area that closes the lightbox on click
- **THEN** the cursor displays a zoom-out affordance (e.g. magnifying glass with -)
