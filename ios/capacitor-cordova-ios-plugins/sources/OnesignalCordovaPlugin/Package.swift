// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "OnesignalCordovaPlugin",
    platforms: [.iOS(.v15)],
    products: [
        .library(
            name: "OnesignalCordovaPlugin",
            targets: ["OnesignalCordovaPlugin"]
        )
    ],
    dependencies: [
        .package(url: "https://github.com/ionic-team/capacitor-swift-pm.git", from: "8.4.0")
    ],
    targets: [
        .target(
            name: "OnesignalCordovaPlugin",
            dependencies: [
                .product(name: "Cordova", package: "capacitor-swift-pm")
            ],
            path: ".",
            publicHeadersPath: "."
        )
    ]
)