# PDF Master
#### Video Demo: https://youtu.be/9w85Yua9D3s
#### Description:

PDF Master is a feature-rich PDF manipulation application built with Python, showcasing advanced GUI programming and PDF processing capabilities. The project consists of several key components working together:

1. **Main Application Class (`PDFApp`):**
   - Implements the core application logic in `project.py`
   - Manages three main modes: viewing, merging, and splitting PDFs
   - Handles file operations, user interactions, and state management
   - Uses Qt's signal-slot mechanism for event handling

2. **Thumbnail Widget (`ThumbnailWidget`):**
   - Custom widget implementation for PDF page previews
   - Provides interactive page management and reordering
   - Maintains its own state and communicates with main application
   - Implements efficient thumbnail generation and caching

3. **Configuration System (`Config` class):**
   - Centralizes application settings and constants
   - Defines window dimensions, zoom limits, and UI parameters
   - Ensures consistent behavior across the application
   - Makes the application easily configurable

4. **PDF Processing Layer:**
   - Utilizes PyMuPDF (fitz) for core PDF operations
   - Implements safe file handling and validation
   - Manages memory efficiently for large PDF files
   - Provides robust error handling and recovery

5. **Testing Framework:**
   - Comprehensive test suite in `test_project.py`
   - Covers UI interactions, PDF operations, and edge cases
   - Uses pytest fixtures for consistent test environments
   - Ensures reliability through automated testing

### Implementation Details:

1. **Viewer Page Features**
   - Navigation buttons (`←`, `→`) for page browsing
   - Zoom controls (`+`, `-`) and Ctrl + Mouse wheel
   - Interactive thumbnail sidebar
   - Undo/Redo buttons (`↶`, `↷`) for page movements
   - `Open PDF` and `Close PDF` operations
   - Page movement input format: `source,target` (e.g., `2,3`)
   - Keyboard shortcuts (`←`, `→` arrows)

2. **Split Page Features**
   - Navigation buttons (`←`, `→`) for page browsing
   - Zoom controls (`+`, `-`) and Ctrl + Mouse wheel
   - Page range input format: `1,4;2-3;5-6`
   - `Open PDF`, `Close PDF` operations
   - `Split PDF` button for processing
   - Live preview of split sections
   - Validation feedback via message boxes

3. **Merge Page Features**
   - `Add PDF` button for file selection
   - `Merge PDFs` button for combining files
   - `Remove` buttons for each file in list
   - File list with drag-drop support
   - Progress indicators during merging
   - File validation feedback
   - File order management in table
   - Automatic output handling

### Technical Architecture:

The application is built usder these approaches:  

- **Framework**: PyQt5 serves as the backbone for the graphical user interface, chosen for its mature ecosystem and cross-platform compatibility. The framework's signal-slot mechanism enables responsive user interactions and real-time updates.

- **PDF Processing**: PyMuPDF (fitz) handles all PDF operations, selected for its comprehensive feature set and excellent performance. It provides low-level access to PDF structures while maintaining high processing speed.

- **Testing**: A comprehensive pytest suite ensures reliability through:
  - Unit tests for core functionality
  - Integration tests for PDF operations
  - UI interaction tests
  - Edge case handling verification

- **Configuration**: The Config class provides a centralized configuration system that:
  - Manages application-wide settings
  - Enables easy customization of UI elements
  - Controls performance parameters
  - Defines system constants

### Installation:

1. Ensure Python >= 3.13.x is installed
2. Install required packages:
```
pip install -r requirements.txt
```

### Usage:

1. Run the application:
```
python project.py
```

2. Use the mode buttons to switch between:
   - PDF Viewer
   - PDF Merger
   - PDF Splitter

3. Navigation:
   - Use arrow buttons or keyboard arrows to change pages
   - Ctrl + Mouse Wheel to zoom
   - Click thumbnails for quick navigation

### Project Structure:

- `project.py`: Main application code
- `test_project.py`: Test suite
- `requirements.txt`: Package dependencies
- `Config` class: Configuration settings

### Testing:

The project includes comprehensive tests covering:
- Navigation functionality
- Zoom operations
- PDF manipulation
- UI interactions
- Keyboard shortcuts

Run tests with:
```
pytest test_project.py
```


### Future Enhancements:

- PDF annotation support
- Text extraction capabilities
- Bookmark management
- PDF form filling
- Document encryption/decryption
- Add eitor page

### acknowledgement

- CS50's online learning platform

### Author

CHAN Shing Hau, Anthony
CS50 Final Project
30-7-2025
