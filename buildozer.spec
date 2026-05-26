[app]
title = Frogger Kars4Kids
package.name = froggerk4kids
package.domain = org.kars4kids

source.dir = .
source.include_exts = py,png,jpg

version = 1.0

requirements = python3,pygame

orientation = portrait
fullscreen = 1

android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

p4a.branch = v2023.05.21

[buildozer]
log_level = 2
warn_on_root = 1
