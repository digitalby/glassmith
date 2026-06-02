#!/usr/bin/env ruby
# frozen_string_literal: true

# Integrate a .icon bundle into an Xcode project, safely and reversibly.
#
# Uses the `xcodeproj` gem (ships with CocoaPods). It:
#   1. copies the .icon into the target's source group folder,
#   2. adds a file reference + resources build-file to the chosen target,
#   3. sets ASSETCATALOG_COMPILER_APPICON_NAME = <icon name> on that target.
#
# Default is a DRY RUN that prints the plan. Pass --write to apply. On --write
# the project.pbxproj is backed up to project.pbxproj.glassmith.bak first.
#
# Usage:
#   integrate.rb --project App.xcodeproj --target App --icon AppIcon.icon [--write]

require 'fileutils'
require 'optparse'

begin
  require 'xcodeproj'
rescue LoadError
  warn "error: the 'xcodeproj' gem is required.\n" \
       "  gem install xcodeproj   (or run inside a CocoaPods project's bundle)"
  exit 3
end

options = { write: false }
OptionParser.new do |o|
  o.banner = 'usage: integrate.rb --project PATH.xcodeproj --target NAME --icon PATH.icon [--write]'
  o.on('--project PATH') { |v| options[:project] = v }
  o.on('--target NAME')  { |v| options[:target] = v }
  o.on('--icon PATH')    { |v| options[:icon] = v }
  o.on('--app-icon-name NAME', 'Override the app icon name (default: .icon basename)') { |v| options[:name] = v }
  o.on('--write', 'Apply changes (default: dry run)') { options[:write] = true }
end.parse!

%i[project target icon].each do |k|
  next if options[k]

  warn "error: --#{k} is required"
  exit 2
end

proj_path = File.expand_path(options[:project])
icon_path = File.expand_path(options[:icon])
unless File.directory?(proj_path) && proj_path.end_with?('.xcodeproj')
  warn "error: not an .xcodeproj: #{proj_path}"
  exit 2
end
unless File.directory?(icon_path) && File.file?(File.join(icon_path, 'icon.json'))
  warn "error: not a .icon bundle: #{icon_path}"
  exit 2
end

icon_name = options[:name] || File.basename(icon_path, '.icon')
project = Xcodeproj::Project.open(proj_path)
target = project.targets.find { |t| t.name == options[:target] }
unless target
  warn "error: target '#{options[:target]}' not found. Available: #{project.targets.map(&:name).join(', ')}"
  exit 2
end

# Destination: alongside the project (project root group's real path).
project_dir = File.dirname(proj_path)
dest_icon = File.join(project_dir, File.basename(icon_path))
basename = File.basename(icon_path)

puts "Plan:"
puts "  project        : #{proj_path}"
puts "  target         : #{target.name}"
puts "  icon           : #{icon_path}"
puts "  copy to        : #{dest_icon}"
puts "  add to target  : #{basename} (resources build phase)"
puts "  set build flag : ASSETCATALOG_COMPILER_APPICON_NAME = #{icon_name}"

already_ref = project.files.any? { |f| f.path && File.basename(f.path) == basename }
puts "  note           : a file reference named #{basename} already exists; will reuse" if already_ref

unless options[:write]
  puts "\nDRY RUN. Re-run with --write to apply."
  exit 0
end

# 1. copy bundle in
FileUtils.cp_r(icon_path, dest_icon, remove_destination: true)

# 2. backup pbxproj
pbx = File.join(proj_path, 'project.pbxproj')
FileUtils.cp(pbx, "#{pbx}.glassmith.bak")

# 3. file reference + build file
ref = project.files.find { |f| f.path && File.basename(f.path) == basename }
ref ||= project.main_group.new_reference(dest_icon)
unless target.resources_build_phase.files_references.include?(ref)
  target.resources_build_phase.add_file_reference(ref)
end

# 4. build setting on every configuration of the target
target.build_configurations.each do |config|
  config.build_settings['ASSETCATALOG_COMPILER_APPICON_NAME'] = icon_name
end

project.save
puts "\nApplied. Backup at #{pbx}.glassmith.bak"
puts "Open the project in Xcode 26+ and build; the Liquid Glass icon is now the app icon."
