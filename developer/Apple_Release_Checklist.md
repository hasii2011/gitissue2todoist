# GitIssue2Todoist - Apple Release Checklist

Because we are compiling a Python app into a native iOS/macOS app using BeeWare, there are a few "quirks" with Apple's strict App Store requirements. 

If you need to release a new version, just follow these exact steps:

### 1. Bump the Version
Never manually change the version in Xcode. Use the custom command we created:
1. Open your terminal.
2. Type `/bump`
*(This script automatically updates your Python version, increments the build number in `../pyproject.toml`, and forcefully injects them into Xcode's `project.pbxproj` and `Info.plist` files, bypassing Briefcase bugs).*

### 2. Prepare the Xcode Project
1. Open the project in Xcode: `open build/gitissue2todoist/ios/xcode/GitIssue2Todoist.xcodeproj`
2. **iPad Only Check:** Go to the GitIssue2Todoist target -> General tab. If **iPhone** is listed under Supported Destinations, click the minus (`-`) to remove it.
3. **Privacy Manifest Check:** If you completely rebuilt the project using `briefcase create`, you MUST re-add the Privacy Manifest to prevent App Store rejection (ITMS-91061). 
   * Go to **File > New > File...**
   * Search for **Privacy** and select **App Privacy**.
   * Save it exactly as `PrivacyInfo.xcprivacy` and ensure the app target is checked.

### 3. Archive and Upload
1. Set the target device at the top of Xcode to **Any iOS Device (arm64)**.
2. Go to **Product > Archive**.
3. When the Organizer pops up, click **Distribute App** -> **App Store Connect** -> **Upload**.

### 4. App Store Connect
1. Wait 5-15 minutes for Apple to process the uploaded archive.
2. Go to App Store Connect -> Your App -> Prepare for Submission.
3. Remove the old build (if attached) and select the new one.
4. Click **Save** and **Submit for Review**.
