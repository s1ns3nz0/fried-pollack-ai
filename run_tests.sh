#!/usr/bin/env bash
# 전체 테스트 실행 — 무슨 기능·어떤 시나리오를 테스트하는지 콘솔 출력 + 로그 저장.
#
#   ./run_tests.sh            # 전체 테스트
#   ./run_tests.sh realistic  # 실 상황 유사 레인지(loopback 실공격)만
#   ./run_tests.sh <경로>     # 특정 파일/키워드
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] && source .venv/bin/activate 2>/dev/null || true

case "${1:-all}" in
  all)        TARGET="tests" ;;
  realistic)  TARGET="tests/test_realistic_range.py" ;;
  *)          TARGET="$1" ;;
esac

echo "▶ 레드팀 에이전트 테스트 실행: ${TARGET}"
python -m pytest "${TARGET}"
echo ""
echo "📄 최신 로그: $(ls -t out/test_logs/*.log 2>/dev/null | head -1 || echo '(없음)')"
