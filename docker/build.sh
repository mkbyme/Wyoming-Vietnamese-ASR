#!/usr/bin/env bash
# ══════════════════════════════════════════════
# build.sh — Multi-variant Docker build script
# Usage:
#   ./build.sh                         → build all, version=1.0.10, push
#   ./build.sh 1.2.0                   → build all, version=1.2.0, push
#   ./build.sh 1.2.0 cpu               → build cpu only, push
#   ./build.sh 1.2.0 cuda12            → build cuda12 only, push
#   ./build.sh 1.2.0 cpu load          → build cpu, load local (no push)
#   ./build.sh 1.2.0 cuda12 load       → build cuda12, load local (no push)
#   ./build.sh 1.2.0 all load          → build all, load local (no push)
# ══════════════════════════════════════════════
set -euo pipefail

REGISTRY="mkbyme/wyoming-vietnamese-asr"
VERSION="${1:-1.0.10}"
TARGET="${2:-all}"    # all | cpu | cuda12
MODE="${3:-push}"     # push | load

# ── Validate MODE ─────────────────────────────
if [[ "${MODE}" != "push" && "${MODE}" != "load" ]]; then
    echo "❌ Unknown mode: ${MODE}"
    echo "   Valid: push | load"
    exit 1
fi

# ── Resolve output flag ───────────────────────
# --load chỉ hỗ trợ single platform (không dùng được với multi-arch)
if [[ "${MODE}" == "load" ]]; then
    OUTPUT_FLAG="--load"
    CPU_PLATFORMS="linux/amd64"   # load chỉ hỗ trợ 1 platform
    echo "⚠️  Mode: load — CPU build sẽ chỉ build linux/amd64 (--load không hỗ trợ multi-arch)"
else
    OUTPUT_FLAG="--push"
    CPU_PLATFORMS="linux/amd64,linux/arm64"
fi

# ── Ensure buildx builder ─────────────────────
if ! docker buildx inspect multiarch-builder &>/dev/null; then
    echo "🔧 Creating buildx builder..."
    docker buildx create --name multiarch-builder --use
    docker buildx inspect --bootstrap
else
    docker buildx use multiarch-builder
fi

# ── Build CPU ─────────────────────────────────
build_cpu() {
    echo ""
    echo "🏗️  Building CPU variant → ${REGISTRY}:${VERSION}-cpu [${MODE}]"
    docker buildx build \
        --platform "${CPU_PLATFORMS}" \
        --build-arg VARIANT=cpu \
        --target runtime \
        -t "${REGISTRY}:${VERSION}-cpu" \
        -t "${REGISTRY}:${VERSION}" \
        -t "${REGISTRY}:latest" \
        ${OUTPUT_FLAG} \
        .
    echo "✅ CPU build done: ${REGISTRY}:${VERSION}-cpu"
}

# ── Build CUDA12 ──────────────────────────────
build_cuda12() {
    echo ""
    echo "🏗️  Building CUDA12 variant → ${REGISTRY}:${VERSION}-cuda12 [${MODE}]"
    docker buildx build \
        --platform linux/amd64 \
        --build-arg VARIANT=cuda12 \
        --target runtime \
        -t "${REGISTRY}:${VERSION}-cuda12" \
        ${OUTPUT_FLAG} \
        .
    echo "✅ CUDA12 build done: ${REGISTRY}:${VERSION}-cuda12"
}

# ── Main ──────────────────────────────────────
echo "══════════════════════════════════════"
echo "  Registry : ${REGISTRY}"
echo "  Version  : ${VERSION}"
echo "  Target   : ${TARGET}"
echo "  Mode     : ${MODE}"
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
echo "🎉 Build complete! [mode: ${MODE}]"
echo ""

if [[ "${MODE}" == "push" ]]; then
    echo "📦 Tags pushed:"
    if [[ "${TARGET}" == "all" || "${TARGET}" == "cpu" ]]; then
        echo "   ${REGISTRY}:${VERSION}-cpu"
        echo "   ${REGISTRY}:${VERSION}       ← default (cpu)"
        echo "   ${REGISTRY}:latest           ← latest (cpu)"
    fi
    if [[ "${TARGET}" == "all" || "${TARGET}" == "cuda12" ]]; then
        echo "   ${REGISTRY}:${VERSION}-cuda12"
    fi
else
    echo "📦 Tags loaded locally (dùng 'docker images' để kiểm tra):"
    if [[ "${TARGET}" == "all" || "${TARGET}" == "cpu" ]]; then
        echo "   ${REGISTRY}:${VERSION}-cpu    [linux/amd64 only]"
        echo "   ${REGISTRY}:${VERSION}"
        echo "   ${REGISTRY}:latest"
    fi
    if [[ "${TARGET}" == "all" || "${TARGET}" == "cuda12" ]]; then
        echo "   ${REGISTRY}:${VERSION}-cuda12"
    fi
    echo ""
    echo "💡 Để push sau:"
    if [[ "${TARGET}" == "all" || "${TARGET}" == "cpu" ]]; then
        echo "   docker push ${REGISTRY}:${VERSION}-cpu"
        echo "   docker push ${REGISTRY}:${VERSION}"
        echo "   docker push ${REGISTRY}:latest"
    fi
    if [[ "${TARGET}" == "all" || "${TARGET}" == "cuda12" ]]; then
        echo "   docker push ${REGISTRY}:${VERSION}-cuda12"
    fi
fi
