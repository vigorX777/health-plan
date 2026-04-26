#!/usr/bin/env python3
"""Generate health-plan daily training posters with OpenAI gpt-image-2.

The script is intentionally dependency-free so missing OpenAI SDK installs do
not block the official API path. It reports a Codex imagegen fallback signal
when OPENAI_API_KEY is unavailable.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1536x1024"
DEFAULT_QUALITY = "medium"
FALLBACK_PROVIDER = "codex_builtin_imagegen"
OFFICIAL_PROVIDER = "openai_gpt_image_2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Day 1-Day 7 health-plan images with OpenAI gpt-image-2."
    )
    parser.add_argument("--jobs", required=True, help="JSON string or path containing jobs.")
    parser.add_argument("--out-dir", default="health-plan/generated_images", help="Output directory.")
    parser.add_argument("--size", default=DEFAULT_SIZE, help="Image size, default 1536x1024.")
    parser.add_argument("--quality", choices=["medium", "high"], default=DEFAULT_QUALITY)
    parser.add_argument("--concurrency", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--provider",
        choices=["auto", OFFICIAL_PROVIDER, FALLBACK_PROVIDER],
        default="auto",
    )
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--output-format", choices=["png", "jpeg", "webp"], default="png")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument(
        "--mock-success",
        action="store_true",
        help="Testing hook. Write placeholder files instead of calling the API.",
    )
    parser.add_argument(
        "--mock-delay",
        type=float,
        default=0.0,
        help="Testing hook. Sleep this many seconds per successful mock job.",
    )
    parser.add_argument(
        "--simulate-fail-day",
        action="append",
        type=int,
        default=[],
        help="Testing hook. May be repeated.",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow fewer than seven jobs for concurrency tests.",
    )
    return parser.parse_args()


def load_jobs(jobs_arg: str, allow_partial: bool) -> list[dict]:
    source = Path(jobs_arg)
    if source.exists():
        raw = source.read_text(encoding="utf-8")
    else:
        raw = jobs_arg

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid --jobs JSON: {exc}") from exc

    if isinstance(payload, dict):
        jobs = payload.get("jobs")
    else:
        jobs = payload

    if not isinstance(jobs, list):
        raise SystemExit("--jobs must be a list or an object with a jobs list.")
    if not allow_partial and len(jobs) != 7:
        raise SystemExit("Expected exactly 7 jobs. Use --allow-partial for test runs.")
    if allow_partial and not (1 <= len(jobs) <= 7):
        raise SystemExit("--allow-partial requires 1-7 jobs.")

    normalized: list[dict] = []
    seen_days: set[int] = set()
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            raise SystemExit(f"Job {index} must be an object.")
        day = int(job.get("day", index))
        if day in seen_days:
            raise SystemExit(f"Duplicate day: {day}")
        seen_days.add(day)
        prompt = str(job.get("prompt", "")).strip()
        if not prompt:
            raise SystemExit(f"Job day_{day} is missing prompt.")
        normalized.append(
            {
                "day": day,
                "job_id": str(job.get("job_id", f"day_{day}")),
                "prompt": prompt,
                "output_filename": str(job.get("output_filename", f"day_{day}.png")),
            }
        )
    return sorted(normalized, key=lambda item: item["day"])


def fallback_manifest(reason: str, jobs: list[dict]) -> dict:
    return {
        "provider": FALLBACK_PROVIDER,
        "fallback_required": FALLBACK_PROVIDER,
        "fallback_reason": reason,
        "jobs": [
            {
                "day": job["day"],
                "job_id": job["job_id"],
                "status": "queued",
                "image_reference": None,
                "retry_policy": f"retry only {job['job_id']} if failed",
            }
            for job in jobs
        ],
    }


def request_image(args: argparse.Namespace, api_key: str, job: dict, out_dir: Path) -> dict:
    attempts = 0
    last_error = None
    max_attempts = max(1, args.retries + 1)

    while attempts < max_attempts:
        attempts += 1
        try:
            if job["day"] in args.simulate_fail_day:
                raise RuntimeError(f"Simulated failure for day_{job['day']}")
            return generate_once(args, api_key, job, out_dir, attempts)
        except Exception as exc:  # noqa: BLE001 - final manifest needs readable errors.
            last_error = str(exc)
            if attempts < max_attempts:
                time.sleep(min(2**attempts, 8))

    return {
        "day": job["day"],
        "job_id": job["job_id"],
        "status": "failed",
        "image_reference": None,
        "attempts": attempts,
        "error": last_error,
        "retry_policy": f"retry only {job['job_id']}",
    }


def generate_once(
    args: argparse.Namespace, api_key: str, job: dict, out_dir: Path, attempts: int
) -> dict:
    if args.mock_success:
        if args.mock_delay > 0:
            time.sleep(args.mock_delay)
        output_path = out_dir / job["output_filename"]
        output_path.write_text(
            f"mock image for {job['job_id']} using {args.model}\n",
            encoding="utf-8",
        )
        return {
            "day": job["day"],
            "job_id": job["job_id"],
            "status": "succeeded",
            "image_reference": str(output_path),
            "attempts": attempts,
            "retry_policy": f"retry only {job['job_id']} if failed",
        }

    endpoint = args.base_url.rstrip("/") + "/images/generations"
    payload = {
        "model": args.model,
        "prompt": job["prompt"],
        "size": args.size,
        "quality": args.quality,
        "n": 1,
        "output_format": args.output_format,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {detail}") from exc

    image_items = data.get("data") or []
    if not image_items:
        raise RuntimeError("OpenAI API response contained no image data.")

    image_item = image_items[0]
    output_path = out_dir / job["output_filename"]
    if image_item.get("b64_json"):
        output_path.write_bytes(base64.b64decode(image_item["b64_json"]))
    elif image_item.get("url"):
        download_image(str(image_item["url"]), output_path, args.timeout)
    else:
        raise RuntimeError("OpenAI API image item contained neither b64_json nor url.")

    return {
        "day": job["day"],
        "job_id": job["job_id"],
        "status": "succeeded",
        "image_reference": str(output_path),
        "attempts": attempts,
        "retry_policy": f"retry only {job['job_id']} if failed",
    }


def download_image(url: str, output_path: Path, timeout: int) -> None:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        output_path.write_bytes(response.read())


def dry_run_manifest(args: argparse.Namespace, jobs: list[dict]) -> dict:
    return {
        "provider": OFFICIAL_PROVIDER,
        "dry_run": True,
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "concurrency": args.concurrency,
        "jobs": [
            {
                "day": job["day"],
                "job_id": job["job_id"],
                "status": "queued",
                "image_reference": None,
                "retry_policy": f"retry only {job['job_id']} if failed",
            }
            for job in jobs
        ],
    }


def write_manifest(out_dir: Path, manifest: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    jobs = load_jobs(args.jobs, args.allow_partial)
    out_dir = Path(args.out_dir)

    if args.provider == FALLBACK_PROVIDER:
        manifest = fallback_manifest("provider explicitly set to codex_builtin_imagegen", jobs)
        write_manifest(out_dir, manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        manifest = fallback_manifest("missing OPENAI_API_KEY", jobs)
        write_manifest(out_dir, manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    if args.dry_run:
        manifest = dry_run_manifest(args, jobs)
        write_manifest(out_dir, manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    worker_count = max(1, min(args.concurrency, len(jobs)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(request_image, args, api_key, job, out_dir) for job in jobs]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    manifest = {
        "provider": OFFICIAL_PROVIDER,
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "concurrency": worker_count,
        "jobs": sorted(results, key=lambda item: item["day"]),
    }
    write_manifest(out_dir, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
