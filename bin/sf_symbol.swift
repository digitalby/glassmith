#!/usr/bin/env xcrun swift
// Render an SF Symbol to a transparent PNG layer for the glassmith pipeline.
//
// PROTOTYPING ONLY. Apple's SF Symbols license prohibits using SF Symbols (or
// modified versions) as app icons or logos. Use this to mock up and iterate;
// ship original artwork for a real App Store icon. See docs/sf-symbols.md.
//
// Usage:
//   sf_symbol.swift <symbol-name> --out layer.png
//     [--color "#RRGGBB"] [--weight regular|medium|semibold|bold|heavy|black]
//     [--size 1024] [--scale 0.6]

import AppKit
import Foundation

func arg(_ name: String, _ def: String? = nil) -> String? {
    let a = CommandLine.arguments
    if let i = a.firstIndex(of: name), i + 1 < a.count { return a[i + 1] }
    return def
}

let positional = CommandLine.arguments.dropFirst().first { !$0.hasPrefix("--") }
guard let symbolName = positional else {
    FileHandle.standardError.write("error: missing <symbol-name>\n".data(using: .utf8)!)
    exit(2)
}
guard let outPath = arg("--out") else {
    FileHandle.standardError.write("error: --out <file.png> is required\n".data(using: .utf8)!)
    exit(2)
}
let size = Int(arg("--size", "1024")!) ?? 1024
let scale = Double(arg("--scale", "0.6")!) ?? 0.6
let weightName = arg("--weight", "regular")!

func color(_ hex: String) -> NSColor {
    var s = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
    if s.count == 3 { s = s.map { "\($0)\($0)" }.joined() }
    var v: UInt64 = 0; Scanner(string: s).scanHexInt64(&v)
    return NSColor(srgbRed: CGFloat((v >> 16) & 0xff) / 255,
                   green: CGFloat((v >> 8) & 0xff) / 255,
                   blue: CGFloat(v & 0xff) / 255, alpha: 1)
}
let fg = color(arg("--color", "#FFFFFF")!)

let weights: [String: NSFont.Weight] = [
    "regular": .regular, "medium": .medium, "semibold": .semibold,
    "bold": .bold, "heavy": .heavy, "black": .black,
]
let weight = weights[weightName] ?? .regular

guard let base = NSImage(systemSymbolName: symbolName, accessibilityDescription: nil) else {
    FileHandle.standardError.write("error: unknown SF Symbol '\(symbolName)' (check name in SF Symbols.app)\n".data(using: .utf8)!)
    exit(1)
}
let config = NSImage.SymbolConfiguration(pointSize: CGFloat(size) * CGFloat(scale), weight: weight)
guard let symbol = base.withSymbolConfiguration(config) else {
    FileHandle.standardError.write("error: could not configure symbol\n".data(using: .utf8)!)
    exit(1)
}

guard let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0) else {
    FileHandle.standardError.write("error: could not allocate bitmap\n".data(using: .utf8)!)
    exit(1)
}
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)

let s = symbol.size
let canvas = CGFloat(size)
let fit = min(canvas * CGFloat(scale) / s.width, canvas * CGFloat(scale) / s.height)
let w = s.width * fit, h = s.height * fit
let rect = NSRect(x: (canvas - w) / 2, y: (canvas - h) / 2, width: w, height: h)
symbol.draw(in: rect, from: .zero, operation: .sourceOver, fraction: 1.0)
fg.set()
NSRect(x: 0, y: 0, width: canvas, height: canvas).fill(using: .sourceAtop)

NSGraphicsContext.restoreGraphicsState()
guard let png = rep.representation(using: .png, properties: [:]) else {
    FileHandle.standardError.write("error: PNG encode failed\n".data(using: .utf8)!)
    exit(1)
}
try png.write(to: URL(fileURLWithPath: outPath))
print("Rendered '\(symbolName)' (\(weightName)) -> \(outPath) [\(size)x\(size)]")
