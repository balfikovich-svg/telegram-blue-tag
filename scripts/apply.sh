#!/usr/bin/env bash
# Clones an official Telegram client at the commit the patch was made against and applies Blue Tag.
#   scripts/apply.sh web-a|web-k|android|ios|desktop [target-dir]
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
client="${1:?web-a | web-k | android | ios | desktop}"
case "$client" in
  web-a)   repo=https://github.com/Ajaxy/telegram-tt.git;                  commit=4566a14adb6287867f21ed6c51449292581c8653 ;;
  web-k)   repo=https://github.com/morethanwords/tweb.git;                 commit=2e4bbb52b6aec5e95ee32e5c2882c1f05de32200 ;;
  android) repo=https://github.com/DrKLO/Telegram.git;                     commit=21f7d109da6ab3506c9e9577f98c6a38771ab335 ;;
  ios)     repo=https://github.com/TelegramMessenger/Telegram-iOS.git;     commit=24638bc69bd083981b178dd1e7f921eebbf7fc46 ;;
  desktop) repo=https://github.com/telegramdesktop/tdesktop.git;           commit=c2d0ad92432f6cde7504e8571ac2fcac9bbc42c7 ;;
  *) echo "unknown client: $client" >&2; exit 1 ;;
esac
dir="${2:-$client}"
git init -q "$dir"
cd "$dir"
git remote add origin "$repo" 2>/dev/null || true
git fetch -q --depth 1 origin "$commit"
git checkout -q FETCH_HEAD
git apply --whitespace=nowarn "$here/clients/$client.patch"
git checkout -q -b blue-tag
git add -A
git -c user.name="Blue Tag" -c user.email="blue-tag@users.noreply.github.com" commit -q -m "Blue Tag: member tag with free messages and a personal slow mode"
echo "Blue Tag applied to $client in $dir (branch blue-tag)"
