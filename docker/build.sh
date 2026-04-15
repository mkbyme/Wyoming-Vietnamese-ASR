#!/usr/bin/env bash
# ══════════════════════════════════════════════
# build.sh — Multi-variant Docker build script
# Usage:
#   ./build.sh                    → build all, version=1.0.10
#   ./build.sh 1.2.0              → build all, version=1.2.0
#   ./build.sh 1.2.0 cpu          → build cpu only
#   ./build.sh 1.2.0 cuda12       → build cuda12 only
# ══════════════════════════════════════════════
set -euo pipefail

REGISTRY="mkbyme/wyoming-vietnamese-asr"
VERSION="${1:-1.0.10}"
TARGET="${2:-all}"   # all | cpu | cuda12

# ── Ensure buildx builder ─────────────────────
if ! docker buildx inspect multiarch-builder &>/dev/null; then
    echo "🔧 Creating buildx builder..."
    docker buildx create --name multiarch-builder --use
    docker buildx inspect --bootstrap
else
    docker buildx use multiarch-builder
fi

# ── Build CPU (amd64 + arm64) ─────────────────
build_cpu() {
    echo ""
    echo "🏗️  Building CPU variant → ${REGISTRY}:${VERSION}-cpu"
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --build-arg VARIANT=cpu \
        -t "${REGISTRY}:${VERSION}-cpu" \
        -t "${REGISTRY}:${VERSION}" \
        -t "${REGISTRY}:latest" \
        --push \
        .
    echo "✅ CPU build done: ${REGISTRY}:${VERSION}-cpu"
}

# ── Build CUDA 12 (amd64 only) ────────────────
build_cuda12() {
    echo ""
    echo "🏗️  Building CUDA12 variant → ${REGISTRY}:${VERSION}-cuda12"
    docker buildx build \
        --platform linux/amd64 \
        --build-arg VARIANT=cuda12 \
        -t "${REGISTRY}:${VERSION}-cuda12" \
        --push \
        .
    echo "✅ CUDA12 build done: ${REGISTRY}:${VERSION}-cuda12"
}

# ── Main ──────────────────────────────────────
echo "══════════════════════════════════════"
echo "  Registry : ${REGISTRY}"
echo "  Version  : ${VERSION}"
echo "  Target   : ${TARGET}"
echo "══════════════════════════════════════"

case "${TARGET}" in
    cpu)    build_cpu ;;
    cuda12) build_cuda12 ;;
    all)
        build_cpu
        build_cuda12
        ;;
    *)
        echo "❌ Unknown target: ${TARGET}"
        echo "   Valid: all | cpu | cuda12"
        exit 1
        ;;
esac

echo ""
echo "🎉 Build complete!"
echo ""
echo "📦 Tags pushed:"
if [[ "${TARGET}" == "all" || "${TARGET}" == "cpu" ]]; then
    echo "   ${REGISTRY}:${VERSION}-cpu"
    echo "   ${REGISTRY}:${VERSION}       ← default (cpu)"
    echo "   ${REGISTRY}:latest           ← latest (cpu)"
fi
if [[ "${TARGET}" == "all" || "${TARGET}" == "cuda12" ]]; then
    echo "   ${REGISTRY}:${VERSION}-cuda12"
fi
