from pathlib import Path
from re import Match
from re import search
from re import sub


def main():
    print('Fetching current version and bumping build number...')

    projectRoot: Path = Path(__file__).resolve().parent.parent
    versionFile: Path = projectRoot / 'src' / 'gitissue2todoist' / '_version.py'
    versionMatch: Match[str] | None = search(r"__version__:\s*str\s*=\s*['\"]([^'\"]+)['\"]", versionFile.read_text())
    if not versionMatch:
        raise RuntimeError('Could not parse __version__ in _version.py')
    version: str = versionMatch.group(1)

    tomlFile: Path = projectRoot / 'pyproject.toml'
    content: str = tomlFile.read_text()
    buildMatch: Match[str] | None = search(r'build\s*=\s*["\']?(\d+)["\']?', content)

    if buildMatch:
        oldBuild: str = buildMatch.group(1)
        newBuild: str = str(int(oldBuild) + 1)
        content = content.replace(f'build = "{oldBuild}"', f"build = '{newBuild}'")
        content = content.replace(f"build = '{oldBuild}'", f"build = '{newBuild}'")
        content = content.replace(f'build = {oldBuild}', f"build = '{newBuild}'")
        tomlFile.write_text(content)
    else:
        newBuild: str = '1'
        print('Warning: build= not found, assuming 1')

    print(f'SUCCESS: Bumped pyproject.toml -> Version: {version} | Build: {newBuild}')

    # 1. Update Xcode project.pbxproj
    pbxFile: Path = projectRoot / 'build' / 'gitissue2todoist' / 'ios' / 'xcode' / 'GitIssue2Todoist.xcodeproj' / 'project.pbxproj'
    if pbxFile.exists():
        pbxContent: str = pbxFile.read_text()
        pbxContent = sub(r'CURRENT_PROJECT_VERSION = [^;]+;', f'CURRENT_PROJECT_VERSION = {newBuild};', pbxContent)
        pbxContent = sub(r'MARKETING_VERSION = [^;]+;', f'MARKETING_VERSION = {version};', pbxContent)
        pbxFile.write_text(pbxContent)
        print('Updated project.pbxproj!')

    # 2. Update Info.plist (This is what Xcode Organizer actually reads!)
    plistFile: Path = projectRoot / 'build' / 'gitissue2todoist' / 'ios' / 'xcode' / 'GitIssue2Todoist' / 'GitIssue2Todoist-Info.plist'
    if plistFile.exists():
        plistContent: str = plistFile.read_text()

        # Replace CFBundleShortVersionString (The 1.0.0 Version)
        plistContent = sub(
            r'(<key>CFBundleShortVersionString</key>\s*<string>)[^<]+(</string>)',
            rf'\g<1>{version}\g<2>',
            plistContent
        )

        # Replace CFBundleVersion (The Build Number)
        plistContent = sub(
            r'(<key>CFBundleVersion</key>\s*<string>)[^<]+(</string>)',
            rf'\g<1>{newBuild}\g<2>',
            plistContent
        )

        plistFile.write_text(plistContent)
        print('Updated GitIssue2Todoist-Info.plist!')

    # 3. Patch BeeWare's utils.sh to inject Privacy Manifests (ITMS-91061)
    utilsFile: Path = projectRoot / 'build' / 'gitissue2todoist' / 'ios' / 'xcode' / 'Support' / 'Python.xcframework' / 'build' / 'utils.sh'
    if utilsFile.exists():
        utilsContent: str = utilsFile.read_text()
        patchCode: str = '''
    # FORCE-INJECT the root PrivacyInfo.xcprivacy into this framework!
    if [ -e "$PROJECT_DIR/PrivacyInfo.xcprivacy" ]; then
        cp "$PROJECT_DIR/PrivacyInfo.xcprivacy" "$CODESIGNING_FOLDER_PATH/$FRAMEWORK_FOLDER/PrivacyInfo.xcprivacy"
    fi
'''
        # Only inject if it's not already there
        if 'FORCE-INJECT the root PrivacyInfo.xcprivacy' not in utilsContent:
            # We want to inject it right after the XCPrivacy check inside install_dylib
            searchStr: str = 'mv "$MODULE_PATH/$MODULE_NAME.xcprivacy" "$XCPRIVACY_FILE"\n    fi\n'
            if searchStr in utilsContent:
                utilsContent = utilsContent.replace(searchStr, searchStr + patchCode)
                utilsFile.write_text(utilsContent)
                print('Patched BeeWare utils.sh to fix ITMS-91061!')
            else:
                print('Warning: Could not find insertion point in utils.sh!')
        else:
            print('BeeWare utils.sh is already patched for ITMS-91061!')


if __name__ == '__main__':
    main()
