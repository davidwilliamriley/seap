# Railway Integration Roadmap - JSON Schema Setup

## 📋 What This Does

The JSON schema (`roadmap_schema.json`) provides:
- ✅ **Autocomplete** - Suggests valid field names as you type
- ✅ **Validation** - Shows errors for invalid dates, statuses, or structure
- ✅ **IntelliSense** - Hover tooltips explaining each field
- ✅ **Status suggestions** - Dropdown with valid values (completed, in_progress, planned, delayed)
- ✅ **Date format checking** - Ensures dates are in YYYY-MM-DD format

## 🔧 Setup Instructions

### Option 1: Automatic (Using .vscode folder)

1. Place these files in the same directory:
   - `roadmap_data.json` (your data)
   - `roadmap_schema.json` (the schema)
   - `.vscode/settings.json` (VS Code settings)

2. Open the folder in VS Code (File → Open Folder)

3. Open `roadmap_data.json` - autocomplete and validation will work automatically!

### Option 2: Manual (Add schema reference to data file)

Add this line at the top of your `roadmap_data.json`:

```json
{
  "$schema": "./roadmap_schema.json",
  "Station A": {
    ...
  }
}
```

### Option 3: Global VS Code Settings

1. Open VS Code Settings (Ctrl+, or Cmd+,)
2. Click "Open Settings (JSON)" icon in top-right
3. Add this configuration:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/roadmap_data.json"],
      "url": "/full/path/to/roadmap_schema.json"
    }
  ]
}
```

## 🎯 Using the Schema

### Autocomplete
- Type `"` and press Ctrl+Space to see available fields
- For status fields, you'll see a dropdown with valid options

### Validation
- Invalid dates (e.g., "2024-13-45") will show red underlines
- Misspelled status values (e.g., "compleeted") will be highlighted
- Missing required fields will be flagged

### Date Format
- All dates must be in `YYYY-MM-DD` format
- Examples: `"2024-01-15"`, `"2025-12-31"`

### Valid Status Values
- `"completed"` - Work is finished
- `"in_progress"` - Work is ongoing
- `"planned"` - Work is scheduled but not started
- `"delayed"` - Work is behind schedule

## 📊 Data Structure

```
{
  "Station Name": {                    ← Railway station
    "P1 - Portion Description": {      ← Work portion
      "stages": [                       ← Array of stages
        {
          "name": "Stage Name",         ← Required
          "start": "YYYY-MM-DD",        ← Required (date format)
          "end": "YYYY-MM-DD",          ← Required (date format)
          "status": "completed",        ← Required (enum)
          "milestones": [               ← Required (array)
            {
              "name": "Milestone",      ← Required
              "date": "YYYY-MM-DD",     ← Required (date format)
              "status": "completed"     ← Required (enum)
            }
          ]
        }
      ]
    }
  }
}
```

## 🚀 Quick Test

1. Open `roadmap_data.json` in VS Code
2. Try adding a new station:
   - Type `"Station D": {` and press Enter
   - Press Ctrl+Space to see autocomplete suggestions
3. Try an invalid status:
   - Type `"status": "done"` - you'll see an error (should be "completed")
4. Try an invalid date:
   - Type `"start": "2024-13-45"` - you'll see an error

## 💡 Tips

- Use Ctrl+Space frequently to trigger autocomplete
- Hover over field names to see descriptions
- Red squiggles indicate schema violations
- Format document with Shift+Alt+F (Windows/Linux) or Shift+Option+F (Mac)

## 🔍 Validation Rules

The schema enforces:
- ✅ Station names (any text)
- ✅ Portion format: "PX - Description" or any "X - Y" pattern
- ✅ Required fields: name, start, end, status, milestones
- ✅ Date format: YYYY-MM-DD (validated via regex)
- ✅ Status enum: completed, in_progress, planned, delayed
- ✅ At least one stage per portion
- ✅ Milestones array (can be empty)

## 📝 Example Entry

```json
{
  "Station D": {
    "P1 - Electrical Works": {
      "stages": [
        {
          "name": "Design",
          "start": "2024-01-01",
          "end": "2024-03-31",
          "status": "completed",
          "milestones": [
            {
              "name": "Design Review",
              "date": "2024-02-15",
              "status": "completed"
            }
          ]
        }
      ]
    }
  }
}
```

## 🆘 Troubleshooting

**Schema not working?**
- Make sure both files are in the same folder
- Reload VS Code window (Ctrl+Shift+P → "Reload Window")
- Check that file is named exactly `roadmap_data.json`

**No autocomplete?**
- Press Ctrl+Space to manually trigger
- Ensure JSON Language Features extension is enabled
- Check bottom-right corner shows "JSON" as language mode

**Validation errors?**
- Hover over red squiggles to see details
- Check date formats (must be YYYY-MM-DD)
- Verify status values match enum (completed, in_progress, planned, delayed)
