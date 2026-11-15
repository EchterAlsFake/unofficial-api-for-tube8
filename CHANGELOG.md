# 2.0.0

Release 2.0.0

Update pagination handling, validation, and documentation.

Changes since 1.3.3:

```text
README.md        |  20 ++++++++++
 pyproject.toml   |   4 +-
 tube8_api/api.py | 110 ++++++++++++++++++++++++++++++++++++++++++++++++++-----
 3 files changed, 122 insertions(+), 12 deletions(-)
```

# Changelog

## 1.3.3 — 2026-10-27

- Stop mistaking subscriber totals for video counts, including on French channel pages.
- Reject empty User pages instead of accepting generic session metadata as a profile identity.
- Encode search queries correctly and preserve their literal special characters.
- Close CLI sessions and report failed downloads accurately.
- A working public User feed remains unverified; ordinary video, channel, pornstar and amateur routes were tested live.
- Use the published `eaf-base-api>=4.2.5` dependency.

