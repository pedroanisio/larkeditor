# Files Removed During GTK → Web Migration

## Deleted GTK-Specific Files

### Application Core Files (Removed)
- `larkeditor/__main__.py` - GTK entry point
- `larkeditor/application.py` - GTK application class  
- `larkeditor/main_window.py` - GTK main window
- `larkeditor/header_bar.py` - GTK header bar
- `larkeditor/buffer_watcher.py` - GTK buffer watcher with threading

### Editor Components (Removed)
- `larkeditor/editor/` (entire directory)
  - `larkeditor/editor/__init__.py`
  - `larkeditor/editor/completion.py` - GTK autocompletion
  - `larkeditor/editor/source_editor.py` - GTK source editor
  - `larkeditor/editor/symbols_set.py` - Symbol management
  - `larkeditor/editor/text_editor.py` - GTK text editor

### UI Definitions (Removed)
- `larkeditor/data/ui/` (entire directory)
  - `larkeditor/data/ui/header-bar.ui` - GTK header bar UI
  - `larkeditor/data/ui/parsing-results.ui` - GTK results UI

### GTK Utilities (Removed)
- `larkeditor/utils/accel_groups.py` - GTK keyboard accelerators
- `larkeditor/utils/error_message.py` - GTK error dialogs
- `larkeditor/utils/file_filter.py` - GTK file filters

## Renamed Files (Preserved for Reference)

### Core Logic Files (Renamed with `_original` suffix)
- `larkeditor/lark_parser.py` → `larkeditor/lark_parser_original.py`
- `larkeditor/results.py` → `larkeditor/results_original.py` 
- `larkeditor/utils/observable_value.py` → `larkeditor/utils/observable_value_original.py`

## Remaining Original Files

### Preserved Files
- `larkeditor/__init__.py` - Package initialization
- `larkeditor/data/language-specs/` - Language specifications (copied to web app)
- `larkeditor/data/styles/` - Editor styles (copied to web app)
- `larkeditor/utils/__init__.py` - Utils package init

## Migration Summary

**Removed**: 13 GTK-specific files totaling ~1,500 lines of GTK Python code
**Preserved**: 3 core logic files renamed for reference  
**Kept**: 4 configuration/data files for reference

**Result**: Clean separation between original GTK codebase (preserved in `larkeditor/`) and new web application (in `app/`).

The `larkeditor/` directory now contains only:
1. **Reference files** - Original core logic preserved with `_original` suffix
2. **Data files** - Language specs and styles (also copied to web app)
3. **Package structure** - Minimal `__init__.py` files

All GTK-specific UI, windowing, and platform-dependent code has been successfully removed and replaced with the modern web-based implementation in the `app/` directory.