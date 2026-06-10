
Briefcase prints this out when trying to build the iOS project

`Installing application resources...`
`Unable to find developer/gitissue2todoist-20.png for 20px application icon; using default`
`Unable to find developer/gitissue2todoist-29.png for 29px application icon; using default`
`...`
`Unable to find developer/gitissue2todoist-1024.png for 1024px application icon; using default`



Even though we gave Briefcase the master `1024x1024` PNG file, this specific version of Briefcase 
is not automatically resizing it down for iOS. When it cannot find the exact sizes explicitly 
named (like `-20.png`, `-60.png`, `-1024.png`), it just threw its hands up and injects the default BeeWare icon!



 I just sliced the master `gitissue2todoist.png` into every single size Apple demands 
 (from 20px all the way up to 1920px) and placed them all neatly into the `developer/` folder with 
 the exact naming convention Briefcase expects.
