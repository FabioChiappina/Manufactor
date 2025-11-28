# Gradio Navigation Implementation Guide

This document explains what we learned about implementing clickable navigation in Gradio and documents the implementation of deck card navigation using the Gallery component.

## ⚠️ Implementation Status: PARTIAL / CHALLENGING

As of November 28, 2025, the Gallery component approach has been partially implemented but faces significant challenges with Gradio's rendering behavior. While the technical implementation appears correct, the actual user experience does not work as expected.

## What We Learned

### Gradio's Capabilities and Limitations

**What Gradio DOES Support:**
- ✅ Clickable buttons that execute Python code
- ✅ Page/view navigation using `gr.Column(visible=True/False)` or `gr.Tab()`
- ✅ Interactive components (buttons, dropdowns, galleries, etc.)
- ✅ Event handlers that trigger Python functions
- ✅ State management with `gr.State()`

**What Gradio Does NOT Support:**
- ❌ JavaScript execution in `gr.HTML()` components
- ❌ Making HTML elements clickable with custom JavaScript
- ❌ HTML onclick events that trigger Gradio Python functions
- ❌ Custom JavaScript that interacts with Gradio components

### The Problem with HTML-based Cards

The current implementation uses `gr.HTML()` to display beautiful deck cards with:
- Card artwork backgrounds
- Gradient overlays
- Hover effects
- Rich formatting

**However:** `gr.HTML()` is a **display-only component**. For security reasons, Gradio sanitizes or doesn't execute JavaScript in HTML components, making them non-interactive.

**Key Insight:** If you render something as HTML in Gradio, it's purely visual and cannot trigger Python functions.

## Implementation Options

### Option 1: Dropdown + Button (Currently Not Implemented)

**Approach:**
```python
deck_dropdown = gr.Dropdown(choices=deck_names, label="Select Deck")
view_btn = gr.Button("View Details")
view_btn.click(fn=navigate_to_details, inputs=[deck_dropdown], outputs=[...])
```

**Pros:**
- Simple and guaranteed to work
- Uses pure Gradio components
- No JavaScript complications

**Cons:**
- Not visually appealing
- Loses the beautiful card grid aesthetic
- Poor UX compared to clicking cards

### Option 2: Gallery Component (RECOMMENDED)

**Approach:** Use `gr.Gallery()` with `.select()` event handler to make deck cards clickable.

**Pros:**
- Visual grid layout similar to current cards
- Natively clickable in Gradio
- Good balance of aesthetics and functionality
- Supports image previews

**Cons:**
- Requires generating preview images for each deck
- May need custom CSS for styling
- Less customizable than pure HTML

### Option 3: HTML Display + Separate Navigation

**Approach:** Keep beautiful HTML cards for visual display, add a dropdown/button below for actual navigation.

**Pros:**
- Keeps current visual design
- Reliable navigation with native components
- Separates aesthetics from functionality

**Cons:**
- Redundant UI elements
- Users might be confused why cards aren't clickable
- Not as clean UX

---

## Recommended Implementation: Gallery Component Approach

### Step 1: Generate Deck Preview Images

Create a function to generate a preview image for each deck that mirrors the current HTML card design:

```python
def generate_deck_preview_image(deck_name, deck_folder_path, json_path):
    """
    Generate a preview image for a deck card.

    Args:
        deck_name: Display name of the deck
        deck_folder_path: Path to deck folder
        json_path: Path to deck JSON file

    Returns:
        Path to generated preview image
    """
    from PIL import Image, ImageDraw, ImageFont

    # Load deck data
    with open(json_path, 'r') as f:
        deck_data = json.load(f)

    # Get background artwork (same logic as current HTML implementation)
    background_image = get_deck_background_image(deck_folder_path, deck_data)

    # Create preview image (800x600 or similar)
    preview = Image.new('RGB', (800, 600))

    if background_image:
        # Resize and darken background
        bg = background_image.resize((800, 600), Image.Resampling.LANCZOS)
        # Apply purple gradient overlay
        overlay = create_gradient_overlay((800, 600))
        preview = Image.alpha_composite(bg.convert('RGBA'), overlay).convert('RGB')
    else:
        # Use solid purple gradient if no artwork
        preview = create_gradient_background((800, 600))

    # Draw deck information on top
    draw = ImageDraw.Draw(preview)
    font_large = ImageFont.truetype("Arial.ttf", 48)
    font_small = ImageFont.truetype("Arial.ttf", 24)

    # Draw deck name
    draw.text((40, 40), deck_name, font=font_large, fill='white')

    # Draw deck stats (card count, format, etc.)
    metadata = deck_data.get('metadata', {})
    stats = f"📦 {len(deck_data.get('cards', {}))} cards • 🎮 {metadata.get('format', 'Unknown')}"
    draw.text((40, 120), stats, font=font_small, fill='white')

    # Save preview image
    preview_dir = Path(PROJECT_ROOT) / "temp" / "deck_previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{deck_name}.png"
    preview.save(preview_path)

    return str(preview_path)
```

### Step 2: Create Gallery with Deck Previews

Replace the HTML-based deck display with a Gallery component:

```python
def get_deck_gallery_data():
    """
    Get list of deck preview images and names for Gallery component.

    Returns:
        Tuple of (list of image paths, list of deck names)
    """
    decks = get_available_decks()
    preview_images = []
    deck_names = []

    for folder_name, deck_folder_path, json_path in decks:
        # Generate or load cached preview image
        preview_path = generate_deck_preview_image(folder_name, deck_folder_path, json_path)
        preview_images.append(preview_path)

        # Get display name from metadata
        with open(json_path, 'r') as f:
            deck_data = json.load(f)
            display_name = deck_data.get('metadata', {}).get('deck_name', folder_name)
            deck_names.append(display_name)

    return preview_images, deck_names
```

### Step 3: Implement Gallery in UI

Update the UI creation code:

```python
def create_ui():
    with gr.Blocks(title="Manufactor") as app:
        gr.Markdown("# Manufactor")

        with gr.Tab("My Decks"):
            # State to track selected deck
            selected_deck_state = gr.State("")

            # Deck list view (visible by default)
            with gr.Column(visible=True) as deck_list_view:
                gr.Markdown("## My Decks")
                gr.Markdown("Click on a deck to view details")

                # Filter and refresh controls
                with gr.Row():
                    filter_all_btn = gr.Button("📚 All Decks", size="sm", variant="primary")
                    filter_complete_btn = gr.Button("✅ Complete", size="sm")
                    filter_incomplete_btn = gr.Button("⏳ Incomplete", size="sm")
                    refresh_btn = gr.Button("🔄 Refresh", size="sm")

                # Deck gallery
                preview_images, deck_names = get_deck_gallery_data()
                deck_gallery = gr.Gallery(
                    value=preview_images,
                    label="",
                    show_label=False,
                    columns=3,  # 3 columns grid
                    rows=None,  # Auto rows
                    height="auto",
                    object_fit="cover",
                    allow_preview=False  # Don't allow full-screen preview
                )

            # Deck details view (hidden by default)
            with gr.Column(visible=False) as deck_details_view:
                with gr.Row():
                    back_btn = gr.Button("← Back to My Decks", size="sm")
                deck_name_header = gr.Markdown("## Deck Details")
                gr.Markdown("*More details coming soon...*")

            # Handle gallery selection
            def on_deck_selected(evt: gr.SelectData):
                """Called when user clicks a deck in the gallery."""
                deck_index = evt.index
                deck_name = deck_names[deck_index]

                return (
                    gr.update(visible=False),  # Hide deck list
                    gr.update(visible=True),   # Show details
                    deck_name,                 # Update selected deck state
                    f"## {deck_name}"          # Update header
                )

            deck_gallery.select(
                fn=on_deck_selected,
                outputs=[deck_list_view, deck_details_view, selected_deck_state, deck_name_header]
            )

            # Handle back button
            def on_back_clicked():
                return (
                    gr.update(visible=True),   # Show deck list
                    gr.update(visible=False),  # Hide details
                    ""                         # Clear selected deck
                )

            back_btn.click(
                fn=on_back_clicked,
                outputs=[deck_list_view, deck_details_view, selected_deck_state]
            )

            # Handle refresh button
            def on_refresh_clicked():
                preview_images, deck_names = get_deck_gallery_data()
                return preview_images

            refresh_btn.click(
                fn=on_refresh_clicked,
                outputs=[deck_gallery]
            )

    return app
```

### Step 4: Add Filtering Support

Implement filtering for complete/incomplete decks:

```python
def get_deck_gallery_data(filter_status="all"):
    """
    Get list of deck preview images and names, with optional filtering.

    Args:
        filter_status: "all", "complete", or "incomplete"

    Returns:
        Tuple of (list of image paths, list of deck names)
    """
    decks = get_available_decks()
    preview_images = []
    deck_names = []

    for folder_name, deck_folder_path, json_path in decks:
        # Load deck data to check completion status
        with open(json_path, 'r') as f:
            deck_data = json.load(f)

        metadata = deck_data.get('metadata', {})
        deck_complete = metadata.get('complete', 0)

        # Apply filter
        if filter_status == "complete" and not deck_complete:
            continue
        elif filter_status == "incomplete" and deck_complete:
            continue

        # Generate preview
        preview_path = generate_deck_preview_image(folder_name, deck_folder_path, json_path)
        preview_images.append(preview_path)

        display_name = metadata.get('deck_name', folder_name)
        deck_names.append(display_name)

    return preview_images, deck_names

# Update filter button handlers
filter_all_btn.click(
    fn=lambda: get_deck_gallery_data("all"),
    outputs=[deck_gallery]
)
filter_complete_btn.click(
    fn=lambda: get_deck_gallery_data("complete"),
    outputs=[deck_gallery]
)
filter_incomplete_btn.click(
    fn=lambda: get_deck_gallery_data("incomplete"),
    outputs=[deck_gallery]
)
```

### Step 5: Optimize with Caching

Cache preview images to avoid regenerating them every time:

```python
import hashlib
from pathlib import Path

def get_cached_preview_path(deck_name, json_path):
    """Get path to cached preview, generating if needed."""
    preview_dir = Path(PROJECT_ROOT) / "temp" / "deck_previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Create hash of JSON file modification time for cache invalidation
    mtime = os.path.getmtime(json_path)
    cache_key = hashlib.md5(f"{deck_name}_{mtime}".encode()).hexdigest()
    preview_path = preview_dir / f"{cache_key}.png"

    if not preview_path.exists():
        # Generate new preview
        generate_deck_preview_image(deck_name, json_path, preview_path)

    return str(preview_path)
```

---

## Styling Considerations

### Custom CSS for Gallery

You can add custom CSS to style the gallery grid:

```python
css = """
.gradio-gallery {
    grid-gap: 20px !important;
}
.gradio-gallery .thumbnail-item {
    border-radius: 12px !important;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}
.gradio-gallery .thumbnail-item:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
}
"""

with gr.Blocks(title="Manufactor", css=css) as app:
    # ... rest of UI
```

---

## Benefits of This Approach

1. **Purely Native Gradio** - No JavaScript hacks or workarounds
2. **Guaranteed to Work** - Uses official Gradio components and events
3. **Maintains Visual Appeal** - Preview images can look identical to current HTML cards
4. **Good Performance** - Image caching prevents redundant generation
5. **Clean Architecture** - Separates image generation from UI logic
6. **Easy to Maintain** - Standard Gradio patterns, well-documented

---

## Migration Checklist

When implementing this approach:

- [ ] Create `generate_deck_preview_image()` function
- [ ] Implement image caching system
- [ ] Create `get_deck_gallery_data()` function with filtering
- [ ] Replace `gr.HTML()` with `gr.Gallery()` in UI
- [ ] Implement `.select()` event handler for navigation
- [ ] Update filter buttons to refresh gallery
- [ ] Add custom CSS for gallery styling
- [ ] Test with decks that have various metadata configurations
- [ ] Test partner commander diagonal split previews
- [ ] Update documentation to reflect new navigation method

---

## Alternative: Hybrid Approach

If you want to keep the HTML cards for display AND have working navigation:

1. Keep the HTML gallery as-is (visual only)
2. Add a small dropdown below: "Or select from list:"
3. Use a native Gradio dropdown + button for actual navigation

This preserves your beautiful cards while adding reliable navigation.

---

## Conclusion

The Gallery component approach (Option 2) is the recommended solution because it:
- Provides clickable deck cards (as requested)
- Uses pure Gradio without JavaScript hacks
- Maintains visual appeal through generated preview images
- Is reliable, maintainable, and future-proof

The key insight is: **Don't fight Gradio's design - use its native components for interactivity, and generate images that match your desired visual style**.

---

## Implementation Summary

### What Was Implemented

The Gallery component approach has been fully implemented in [src/ui/app.py](../src/ui/app.py) with the following features:

#### 1. Preview Image Generation (`generate_deck_preview_image()`)
- Creates 800x600 preview images for each deck
- Supports card artwork backgrounds with purple gradient overlay
- Handles partner commanders with diagonal split composite images
- Falls back to solid purple gradient if no artwork available
- Displays deck name, card count, format, and completion status
- Caches preview images with MD5 hash based on JSON modification time

#### 2. Gallery Data Management (`get_deck_gallery_data()`)
- Loads all decks from configured deck path
- Supports filtering by completion status (all/complete/incomplete)
- Returns lists of preview images, deck names, and deck paths
- Handles errors gracefully for individual decks

#### 3. UI Components
- **Deck List View**: Shows deck gallery with filter buttons
- **Deck Details View**: Hidden by default, shown when deck is selected
- **Navigation**: Back button to return to deck list
- **Filter Buttons**: All Decks, Complete, Incomplete
- **Refresh Button**: Reloads deck gallery

#### 4. Event Handlers
- **`deck_gallery.select()`**: Handles deck selection, shows details view
- **`back_btn.click()`**: Returns to deck list view
- **Filter buttons**: Update gallery based on completion status
- **Refresh button**: Reloads gallery data

### Key Features

✅ **Clickable Deck Cards** - Gallery items are natively clickable in Gradio
✅ **Visual Appeal** - Generated preview images maintain the purple gradient aesthetic
✅ **Partner Commander Support** - Diagonal split display for 2-commander decks
✅ **Filtering** - Filter decks by completion status
✅ **Caching** - Preview images are cached for performance
✅ **Error Handling** - Graceful degradation when artwork is missing
✅ **Navigation** - Smooth transitions between list and detail views

### File Changes

- **Modified**: [src/ui/app.py](../src/ui/app.py)
  - Added imports for `hashlib` and `ImageFont`
  - Added `generate_deck_preview_image()` function
  - Added `get_cached_preview_path()` function
  - Added `get_deck_gallery_data()` function
  - Replaced `gr.HTML()` deck display with `gr.Gallery()`
  - Added deck details view with navigation
  - Implemented all event handlers for gallery interaction
  - Updated `save_settings()` to remove HTML output

### Testing Results

✅ Preview images generated successfully for all decks
✅ Purple gradient overlay applied correctly
❌ **Text rendering had sizing/wrapping issues** - Text spilled over gallery card boundaries
✅ Partner commander diagonal split working
✅ Image caching implemented and functional
✅ UI creation successful without errors
❌ **Navigation doesn't work as expected** - Details view appears below gallery instead of replacing it

### What Actually Works

1. Users can see a grid of deck preview images (with text sizing issues)
2. Clicking a deck card triggers the `.select()` event handler
3. The event handler correctly sets `visible=False` on deck list and `visible=True` on details
4. Filter buttons work to show complete/incomplete decks
5. Refresh button reloads the gallery
6. Preview images are cached for performance

### What Doesn't Work

1. **Text overflow**: Deck names and stats spill outside the gallery card boundaries and don't wrap properly
2. **Navigation behavior**: When clicking a deck, the details view appears at the bottom of the screen rather than replacing the gallery entirely
3. **Visibility toggling**: Despite correctly setting `gr.update(visible=False)` on the deck list Column, both views appear to be visible simultaneously or the hidden view still takes up space

---

## Challenges Discovered

### Issue 1: Text Rendering in Gallery Preview Images

**Problem**: Text overlaid on the 800x600 preview images doesn't respect the gallery card boundaries when displayed in Gradio's Gallery component.

**What We Tried**:
1. Reduced font sizes from 48/24/16 to 36/18/14
2. Implemented text wrapping function using PIL's `textbbox()` to calculate line widths
3. Added margins (30px) and limited deck names to 2 lines
4. Removed emoji icons to save space

**Why It Failed**: The Gallery component appears to scale/resize the preview images when displaying them in the grid, which causes text that fits perfectly in the 800x600 source image to overflow or wrap incorrectly when rendered at a different size. The Gallery component's internal resizing doesn't preserve text readability.

**Possible Solutions**:
- Use much larger preview images (e.g., 1600x1200) so text remains readable when scaled down
- Use simpler text with much smaller font sizes
- Accept that text may not be perfectly readable and rely more on visual card artwork
- Use a different approach entirely (e.g., Image + separate Text components)

### Issue 2: Column Visibility Toggling

**Problem**: Setting `gr.update(visible=False)` on a Column doesn't completely hide it or remove it from the layout as expected. The details view appears below the (supposedly hidden) gallery view instead of replacing it.

**What We Tried**:
1. Used `gr.Column(visible=True)` for deck list and `gr.Column(visible=False)` for details
2. Event handler returns `gr.update(visible=False)` for deck_list_view and `gr.update(visible=True)` for deck_details_view
3. Added `elem_id` attributes to the Columns to ensure they're distinct
4. Implemented proper state management to track which decks are currently displayed

**Why It Failed**: Despite the code being technically correct, Gradio's rendering behavior causes both columns to appear in the DOM or the hidden column to still take up space. This may be a Gradio bug, version-specific behavior, or a fundamental limitation of how Gradio handles dynamic visibility changes in complex layouts.

**Attempted Debugging**:
- Verified event handlers are firing correctly
- Confirmed `gr.update(visible=False/True)` is being returned from handlers
- Checked that outputs array matches the components being updated
- State management correctly tracks current filter and deck data

**Possible Root Causes**:
1. **Gradio Version**: The behavior of `visible` parameter may vary across Gradio versions
2. **Nesting Issues**: Having both Columns within a Tab may cause unexpected rendering
3. **CSS/Layout Conflicts**: Gradio's internal CSS may not properly handle hiding/showing Columns
4. **Browser Rendering**: The issue may be browser-specific or related to how Gradio's JavaScript handles visibility
5. **State Timing**: There may be a race condition or timing issue with when the visibility update is applied

### Issue 3: Gallery Component Text vs. Image Content

**Problem**: Gradio's Gallery component is fundamentally designed for displaying images, not images with overlaid text that needs to remain readable at different scales.

**Core Limitation**: The Gallery component:
- Automatically scales images to fit grid cells
- Doesn't preserve text readability during scaling
- Has no built-in support for text overlays or captions
- Treats all content as pure images

**What This Means**: Using generated preview images with text overlays is fighting against the Gallery component's intended use case. The component expects images like photos or artwork, not composite images with important text content.

---

## Recommendations

### For Text Rendering

**Option 1**: Accept Lower Text Quality
- Use very large fonts that remain somewhat readable when scaled
- Keep text extremely simple (deck name only)
- Rely primarily on visual card artwork for identification

**Option 2**: Separate Text from Images
- Use Gallery for card artwork only (no text overlays)
- Add a separate Text/Markdown component below each gallery item for deck info
- This requires a different UI structure than the current implementation

**Option 3**: Use Different Component Entirely
- Instead of Gallery, use a custom layout with individual Image + Text components
- More control over layout but loses Gallery's built-in grid and interaction

### For Navigation

**Option 1**: Use Tabs Instead of Column Visibility
- Create "Deck List" and "Deck Details" as separate tabs
- Switch between tabs programmatically instead of toggling Column visibility
- Tabs are more reliably supported in Gradio

**Option 2**: Simpler Single-View Approach
- Keep everything on one page
- Instead of navigation, expand details inline below clicked deck
- Use accordion or collapsible section

**Option 3**: Dropdown + Button (Original Fallback)
- Abandon clickable cards entirely
- Use dropdown to select deck + button to view details
- Less elegant but guaranteed to work

### For Future Implementation

1. **Test Gradio Version**: Upgrade to latest Gradio and test if Column visibility works better
2. **Simplify First**: Start with the simplest possible navigation (dropdown + button) and verify it works
3. **Add Complexity Gradually**: Only add Gallery/clickable cards after basic navigation is confirmed working
4. **Consider Alternatives**: Streamlit, Dash, or other frameworks may handle this use case better

---

## Conclusion

The Gallery component approach (Option 2) faces significant implementation challenges that make it unreliable for this use case:

❌ **Text rendering** - Gallery scaling breaks text readability
❌ **Navigation** - Column visibility toggling doesn't work as expected
✅ **Image generation** - Preview image creation works well
✅ **Caching** - Image caching is functional
✅ **State management** - Filter and deck tracking works correctly

**Key Insight**: **Gradio's Gallery component is designed for images, not composite images with text. The Column visibility system may have bugs or limitations that prevent reliable view switching. A simpler approach using dropdowns and buttons, or using Tabs for navigation, would be more reliable.**

### Next Steps (Future Enhancements)

If attempting this again, consider:
- Testing with latest Gradio version
- Using Tabs instead of Column visibility
- Separating text from images entirely
- Starting with dropdown navigation as a baseline
- Consulting Gradio community/docs for visibility best practices
