# Komunitas Anak Belajar— CLAUDE.md


## Development Approach
- **No commits.** Leave all git operations to the developer.
- **Do not use sudo.** If a task requires elevated privileges, output the command and ask the developer to run it manually.
- **No multi-line `{# … #}` template comments.** Django's `{# … #}` is single-line only; a comment whose `{#` and `#}` sit on different lines renders as literal text on the page. Use `{% comment %}…{% endcomment %}` for anything spanning more than one line.

