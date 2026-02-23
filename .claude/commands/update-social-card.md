Update the social card image (`social-card.png`) from its HTML source (`social-card.html`).

## Steps

### 1. Pick 3 themes

Read `RUNS.md` (the overview table and highlights sections). Choose the 3 most impressive/diverse themes across all runs. A theme can span multiple runs. For each column, pick:
- A short title (max 24 chars including spaces — must fit one line)
- 3 bullet points: the most concrete, specific outputs for that theme

Aim for variety — don't let one run dominate all 3 columns. Prefer outputs that sound surprising or impressive to a general audience (not just "wrote some Python scripts").

### 2. Find quotes

For each theme, search the actual run repos for a real quote to feature. Look in markdown files (essays, notes, READMEs) and code comments. Pick lines that are punchy, self-contained, and read well out of context. Prefer Claude's own words over editorial paraphrasing.

### 3. Update footer stats

Count the runs and files for the footer line (e.g. "4 runs · 60+ files · 0 prompts"):

- **Runs**: count directories matching `runs/run-*` using Glob.
- **Files**: for each run, count tracked files with `git -C runs/run-xxxx ls-files | wc -l`. Sum across all runs. Round down to the nearest 10 and use a `+` suffix (e.g. 67 → "60+").
- **Prompts**: always `0 prompts` (the whole point of the project).

### 4. Update HTML

Update the content in `social-card.html` with the chosen themes, bullets, quotes, and footer stats.

### 5. Render the image

1. Start a local HTTP server on port 8191 serving the project root:
   ```
   python -m http.server 8191 --directory . --bind 127.0.0.1
   ```
   Run this in the background.

2. Open `http://127.0.0.1:8191/social-card.html` in the Playwright browser.

3. Set viewport to **1200x630** (LinkedIn/Open Graph standard).

4. Take a PNG screenshot saved as `social-card.png` in the project root.

5. Stop the HTTP server.

6. Show the user the resulting image.

## Notes

- The HTML file uses JetBrains Mono from Google Fonts — make sure the font loads before screenshotting.
- The image dimensions must stay at 1200x630 for social media compatibility.
- Card titles must be max 24 characters (including spaces) to fit on one line.
