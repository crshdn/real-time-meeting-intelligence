# Build for Production

Build the application for distribution.

## Steps

1. Run tests to ensure everything works
2. Build the frontend
3. Package with Electron Builder
4. Create installers for target platforms

## Commands

```bash
# Run all tests first
pytest backend/tests/
cd ui && npm test

# Build frontend
cd ui
npm run build

# Package for current platform
npm run package

# Package for specific platform
npm run package:win
npm run package:mac
```

## Output

Built applications will be in `ui/dist/`:
- Windows: `.exe` installer
- macOS: `.dmg` installer
- Linux: `.AppImage`

## Pre-build Checklist

- [ ] All tests passing
- [ ] Environment variables documented
- [ ] Version number updated in package.json
- [ ] CHANGELOG updated
- [ ] API keys removed from any config files
