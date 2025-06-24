# 🚀 Major Enhancements to Stratus GitHub Actions

This PR introduces significant improvements to two key components in our GitHub Actions toolkit:

## 🔍 1. Build Scope Analyzer v3.0.0 (Major Update)

The Build Scope Analyzer has been completely redesigned with enhanced features for more reliable and detailed CI/CD operations:

### Key Improvements

- **Enhanced Output Schema**: Completely restructured output format with separate matrices for apps vs containers
- **Deletion Tracking**: Improved tracking of deleted apps and containers with detailed metadata (including commit SHA)
- **Multi-Container Support**: Better handling of multi-container apps with proper naming and context detection
- **Custom Docker Build Context**: Support for custom Docker build contexts via `# @context: ...` comment in Dockerfiles
- **Explicit Container Properties**: Each container output now includes `container_name`, `image_name`, and detailed Dockerfile info
- **Test Coverage**: Comprehensive test suite with multiple test scenarios

### Compatibility Note

This is a breaking change from v2 - workflow files using the analyzer will need to be updated to use the new output structure. See the updated example-workflow.yml for guidance.

## 🏷️ 2. Release Action Enhancements

Added smart tag management capabilities to the Release action:

- **Major Version Tags**: Automatically updates major version tags (e.g., v1) to reference the latest release in that major version
- **Latest Tag Support**: Creates/updates a `latest` tag that always points to the most recent release
- **Force-Update Strategy**: Uses Git's force-update for tags to ensure consistent tag references
- **Robust Semantic Versioning**: Enhanced tag detection to properly identify the latest semantic version regardless of tag creation date
- **Improved Version Parsing**: Better handling of various version formats (v1, v1.2, v1.2.3) for more reliable version increments

## 📚 Other Changes

- 📝 Added documentation examples and updated READMEs
- 🔧 Added `.gitignore` update to ignore local `_temp` folders
- 🧪 Replaced setup script with improved test runner

## 🌟 Benefits

This update delivers several key benefits:

1. ✅ **More Reliable Builds**: Better detection of what needs to be built and cleaned up
2. ✅ **Smarter Tag Management**: Proper semantic version handling for better dependency references
3. ✅ **Improved Multi-Container Support**: Handles complex container scenarios with dedicated contexts and naming
4. ✅ **Enhanced Testing**: More comprehensive test coverage across both actions

These improvements make our GitHub Actions more robust for complex multi-container projects while providing a reliable tagging strategy that follows semantic versioning best practices.
