import sublime
import sublime_plugin
import re
import fnmatch
import os

class QuickThemesCommand(sublime_plugin.WindowCommand):
    def theme_name(self, full_name):
        try:
            match = re.search("Packages/(.*)/(.*).tmTheme|.sublime-theme$", full_name)
            theme_group = match.group(1)
            theme_name = match.group(2)

            if theme_name:
                return (theme_name, theme_group)
        except:
            try:
                return (full_name.split("/")[-1])
            except:
                return full_name

    def theme_name_status_message(self, full_name):
        try:
            sublime.status_message("%s (%s)" % self.theme_name(full_name))
        except:
            pass

    def get_mismatch(self, a, b):
        """ Return the difference between two dicts. """
        try:
            diff = set(a).difference(set(b))
            return dict((key, value) for (key, value) in diff)
        except:
            return {}

    def run(self, action):
        qt_settings = sublime.load_settings('QuickThemes.sublime-settings')
        full_settings = sublime.load_settings("Base File.sublime-settings")
        relevant_settings = {}

        qt_defaults = qt_settings.get("quick_themes_defaults")  # dict
        qt_group_selection = int(qt_settings.get("quick_themes_group_selection", 0))  # int
        qt_selection = int(qt_settings.get("quick_themes_selection", 0))  # int
        qt_themes = qt_settings.get("quick_themes") # list

        for option in qt_defaults:
            relevant_settings[option] = full_settings.get(option)

        mismatch = self.get_mismatch(
            qt_themes[qt_group_selection][qt_selection], relevant_settings)

        if len(mismatch) > 0:
            """ There is a mismatch between the selected quicktheme
                and the current base theme settings. Check to see whether
                any of the other quickthemes match. """
            match = False
            for theme in qt_themes[qt_group_selection]:
                test = qt_defaults
                test.update(theme)
                if self.get_mismatch(test, relevant_settings).len == 0:
                    match = True
                    """ Found a match, so update the selection setting. """
                    qt_selection = qt_themes[qt_group_selection].index(theme)
                    break
            if match is False:
                """ No match found, so add a new quicktheme to preserve current
                    settings. """
                qt_themes[qt_group_selection].append(relevant_settings)
                qt_selection = len(qt_settings["quick_themes"]) - 1

        if action == "inc":
            qt_selection += 1
            if qt_selection > len(qt_themes[qt_group_selection]) - 1:
                qt_selection = 0
        elif action == "dec":
            qt_selection -= 1
            if qt_selection < 0:
                qt_selection = len(qt_themes[qt_group_selection]) - 1
        elif action == "group":
            qt_selection = 0
            qt_group_selection += 1
            if qt_group_selection > len(qt_themes) - 1:
                qt_group_selection = 0
        elif action == "reload":
            qt_themes = self.find_themes()

            try:
                test = qt_themes[qt_group_selection][qt_selection]
            except:
                qt_selection = 0
                qt_group_selection = 0

        writeable_settings = dict(qt_defaults, **qt_themes[qt_group_selection][qt_selection])

        for option in writeable_settings:
            full_settings.set(option, writeable_settings[option])

        qt_settings.set("quick_themes_group_selection", int(qt_group_selection))
        qt_settings.set("quick_themes_selection", int(qt_selection))
        qt_settings.set("quick_themes", qt_themes)

        sublime.save_settings('QuickThemes.sublime-settings')
        sublime.save_settings("Base File.sublime-settings")

        self.theme_name_status_message(writeable_settings["color_scheme"])

    def find_themes(self):
        groups = {}
        themes = []

        for root, dirnames, filenames in os.walk(sublime.packages_path()):
            matches = fnmatch.filter(filenames, "*.tmTheme")

            for filename in matches:
                theme_path = os.path.join(root, filename)
                theme_name = self.theme_name(theme_path)

                if theme_name is None:
                    continue

                if theme_name[1] not in groups:
                    groups[theme_name[1]] = []

                groups[theme_name[1]].append({"color_scheme": theme_path})

        for group in sorted(groups, lambda a, b: cmp(a.lower(), b.lower())):
            groups[group].append({})
            themes.append(groups[group])

        return themes
