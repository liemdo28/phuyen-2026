#!/usr/bin/env python3
"""
QA CIVILIZATION SYSTEM — Main Entry Point
==========================================
Human Communication Stress Testing Engine for Phú Yên 2026 AI Travel Companion

Usage:
    python qa/run_qa.py                        # Run single QA batch (20 sessions)
    python qa/run_qa.py --sessions 50          # Run 50 sessions
    python qa/run_qa.py --loop                 # Run until zero audit achieved
    python qa/run_qa.py --loop --max-iter 100  # Loop with max 100 iterations
    python qa/run_qa.py --replay               # Replay all failed sessions
    python qa/run_qa.py --regression           # Run regression tests only
    python qa/run_qa.py --audit-reports        # Discover + replay repo QA artifacts
    python qa/run_qa.py --discover-only        # Print discovered QA artifacts only
    python qa/run_qa.py --latest-fix-queue     # Print latest unresolved fix queue
    python qa/run_qa.py --mock                 # Use mock AI (no backend needed)
    python qa/run_qa.py --demo                 # Demo mode: show sample violations
"""

import sys
import os
import argparse
import random
import json
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_ai_handler(mock_mode: bool = False):
    """Get the AI handler function — real or mock."""
    if mock_mode:
        return _mock_ai_handler

    # Try to connect to real backend
    try:
        import requests

        backend_url = os.environ.get("QA_BACKEND_URL", "http://localhost:3000")

        def real_handler(message: str) -> str:
            try:
                response = requests.post(
                    f"{backend_url}/api/message",
                    json={"message": message, "userId": "qa_test"},
                    timeout=10,
                )
                if response.ok:
                    data = response.json()
                    return data.get("response", data.get("message", str(data)))
                return f"[HTTP {response.status_code}]"
            except Exception as e:
                # Fall back to mock if backend unavailable
                return _mock_ai_handler(message)

        return real_handler
    except ImportError:
        print("⚠️  requests not available, using mock AI")
        return _mock_ai_handler


def _mock_ai_handler(message: str) -> str:
    """
    Mock AI handler for testing without backend.
    Intentionally has some flaws to generate audit violations for demonstration.
    """
    msg_lower = message.lower()
    responses = []

    # Simulate various AI quality levels
    quality = random.random()

    if quality < 0.15:
        # Bad response — triggers multiple violations
        return _bad_response(message)
    elif quality < 0.35:
        # Mediocre response
        return _mediocre_response(message)
    else:
        # Good response
        return _good_response(message)


def _bad_response(message: str) -> str:
    """Intentionally bad AI responses for violation demonstration."""
    bad_responses = [
        "I am an AI assistant and I cannot provide real-time information. Please note that as per your query, I would like to inform you that furthermore, I hope this information helps. Please feel free to ask if you need more assistance.",
        "Thank you for your feedback. We apologize for any inconvenience. Our team will look into this matter.",
        "I don't know the answer to that. Please contact support for more information.",
        "Here are 15 restaurants you should visit in Phú Yên:\n1. Restaurant A\n2. Restaurant B\n3. Restaurant C\n4. Restaurant D\n5. Restaurant E\n6. Restaurant F\n7. Restaurant G\n8. Restaurant H\n9. Restaurant I\n10. Restaurant J\n11. Restaurant K\n12. Restaurant L\n13. Restaurant M\n14. Restaurant N\n15. Restaurant O\n\nAll of these are excellent choices. I recommend visiting all of them during your stay!",
        "That's a great question! As an AI language model, I'm unable to provide real-time weather data or GPS information. I hope this helps! Feel free to ask any other questions.",
    ]
    return random.choice(bad_responses)


def _mediocre_response(message: str) -> str:
    """Mediocre AI responses — passes some checks, fails others."""
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["đói", "ăn", "quán", "đoi"]):
        return "Bạn có thể thử các quán sau: Nhà hàng Hải Sản Tươi Sống (đường Trần Hưng Đạo), Quán Cơm Niêu (gần chợ Tuy Hòa). Additionally, you might want to consider visiting some local eateries. I hope this information proves helpful to you!"
    elif any(w in msg_lower for w in ["mệt", "met", "kiệt"]):
        return "Bạn nên nghỉ ngơi một chút! Ngoài ra, bạn có thể tiếp tục khám phá Gành Đá Đĩa, Hòn Yến, Mũi Điện, và nhiều địa điểm thú vị khác ở Phú Yên. Bạn không nên bỏ qua những nơi tuyệt đẹp này!"
    else:
        return "Tôi sẽ giúp bạn tìm hiểu thêm về vấn đề này. Furthermore, please note that as per your request, there are many options available."


def _good_response(message: str) -> str:
    """Good AI responses — passes most checks."""
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["đói", "ăn", "quán", "doi", "an", "quan"]):
        return random.choice([
            "🐟 Quán Bún Cá Ngừ Chị Ba — đường Nguyễn Huệ, Tuy Hòa. Ngon, rẻ, local chuẩn. Tầm 50-70k/tô. Sáng mở sớm từ 6h!",
            "🦞 Giờ này ăn hải sản đi! Quán Sáu Hoàng gần cảng — cá tươi, giá ổn. 200-300k/người. Có bãi đậu xe.",
            "🍜 Mệt mà muốn ăn nhanh — bánh căn Cô Năm ở chợ Tuy Hòa. 30k/phần, ăn no mà nhẹ. 5 phút là có!",
        ])
    elif any(w in msg_lower for w in ["mệt", "met", "kiệt", "khong di noi"]):
        return random.choice([
            "Oke nghỉ thôi! Cafe Gió Biển ngay đây — điều hòa, yên tĩnh, view biển. Không cần đi xa. Order nước rồi ngồi thư giãn đi 😊",
            "Gần đây có lobby khách sạn Cendeluxe — ghế sofa thoải mái, mở cửa cả ngày. Ghé vào nghỉ một tí rồi tính tiếp nhé.",
        ])
    elif any(w in msg_lower for w in ["bé", "be", "con", "child", "4 tuoi"]):
        return random.choice([
            "⚠️ Bé 4 tuổi đi biển cần kiểm tra cờ báo hiệu trước. Cờ đỏ = không xuống nước. Bãi Xép thường sóng nhỏ, an toàn hơn cho bé. Mang áo phao nha!",
            "👶 Cho bé 4 tuổi — Bãi Xép là lựa chọn tốt nhất. Nước nông, sóng nhỏ. Tránh Hòn Yến khi có sóng. Luôn mặc áo phao cho bé!",
        ])
    elif any(w in msg_lower for w in ["bar", "nhau", "lon", "bia", "uong"]):
        return random.choice([
            "🍺 Tối nay? Beer club Sóng Biển — view đẹp, giá ổn. Mở đến 1am. Hoặc quán nhậu vỉa hè đường Trần Phú nếu muốn local hơn.",
            "Quán nhậu Biển Xanh — ngay bờ biển, gió mát, hải sản nhậu ngon. 150-200k/người. Còn mở đến khuya 🍻",
        ])
    elif any(w in msg_lower for w in ["thoi khe", "khong sao", "tu tim", "hay that", "tuyet voi lam"]):
        # Detect sarcasm
        return "Ủa nghe có vẻ không ổn lắm 😅 Chỗ trước tôi gợi ý có vấn đề gì không? Nói tôi biết để tìm chỗ khác tốt hơn nhé!"
    else:
        return random.choice([
            "Bạn muốn hỏi gì thêm? Tôi có thể giúp tìm quán ăn, địa điểm tham quan, hoặc thông tin thực tế về Phú Yên 😊",
            "Phú Yên có nhiều thứ hay lắm! Bạn đang ở đâu, muốn đi đâu tiếp theo?",
        ])


def run_demo():
    """Run a quick demo showing the system in action."""
    print("\n" + "="*60)
    print("🌐 QA CIVILIZATION SYSTEM — DEMO MODE")
    print("="*60)

    from qa.simulation.persona_engine import get_weighted_persona
    from qa.simulation.conversation_generator import ConversationGenerator
    from qa.audit.audit_engine import AuditEngine
    from qa.scoring.scoring_engine import ScoringEngine
    from qa.reporting.report_generator import ReportGenerator

    gen = ConversationGenerator()
    audit = AuditEngine()
    scoring = ScoringEngine()
    reporter = ReportGenerator()

    demo_cases = [
        # (persona_type, message, response_quality)
        ("gen_z", "doi qua oke goi y di", _mock_ai_handler),
        ("exhausted", "mệt vl không đi nổi gần thôi nha", _mock_ai_handler),
        ("angry", "Sao gợi ý chỗ đó??? Tourist trap hết rồi", _mock_ai_handler),
        ("no_accent", "quan hai san nao ngon gan day ko", _mock_ai_handler),
        ("child", "bé 4 tuổi tắm biển được không sóng to", _mock_ai_handler),
    ]

    labels = ["Gen Z slang", "Exhausted traveler", "Angry customer", "No accent", "Child safety"]

    for (_, msg, handler), label in zip(demo_cases, labels):
        print(f"\n📋 Scenario: {label}")
        print(f"   👤 User: {msg}")

        response = handler(msg)
        print(f"   🤖 AI: {response[:80]}{'...' if len(response) > 80 else ''}")

        report = audit.audit(
            session_id="demo",
            user_message=msg,
            ai_response=response,
            scenario="demo",
        )
        score = scoring.score_report(report)

        status = "✅ PASS" if score.pass_fail == "PASS" else "❌ FAIL"
        print(f"   {status} | Score: {score.overall_score:.1f}/10 | Violations: {len(report.violations)}")

        for v in report.violations:
            print(f"      ⚠️  [{v.severity.value}] {v.rule}: {v.reason[:60]}")

    print("\n" + "="*60)
    print("Demo complete. Run with --loop for full civilization testing.")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="QA Civilization System — Human Communication Stress Tester"
    )
    parser.add_argument("--sessions", type=int, default=20, help="Sessions per batch")
    parser.add_argument("--loop", action="store_true", help="Run until zero audit")
    parser.add_argument("--max-iter", type=int, default=50, help="Max loop iterations")
    parser.add_argument("--replay", action="store_true", help="Replay failed sessions")
    parser.add_argument("--regression", action="store_true", help="Run regression tests only")
    parser.add_argument("--audit-reports", action="store_true", help="Discover QA artifacts in repo, replay them, and generate fix queue")
    parser.add_argument("--discover-only", action="store_true", help="Only discover QA artifacts and print manifest")
    parser.add_argument("--latest-fix-queue", action="store_true", help="Print the latest unresolved fix queue snapshot")
    parser.add_argument("--max-scenarios", type=int, default=100, help="Max discovered scenarios to replay during --audit-reports")
    parser.add_argument("--mock", action="store_true", help="Use mock AI (no backend needed)")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--verbose", action="store_true", default=True)

    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    ai_handler = get_ai_handler(mock_mode=args.mock)

    if args.discover_only:
        from qa.orchestration.autonomous_qa_system import AutonomousQAOrchestrationSystem

        system = AutonomousQAOrchestrationSystem(os.path.dirname(os.path.abspath(__file__)) + "/..")
        artifacts = system.discover_reports()
        scenarios = system.extract_scenarios(artifacts)
        print("\n🔎 Autonomous QA Discovery")
        print(f"   Artifacts: {len(artifacts)}")
        print(f"   Scenarios: {len(scenarios)}")
        for artifact in artifacts[:20]:
            print(f"   - [{artifact.report_type}] {artifact.relative_path}")
        return

    if args.latest_fix_queue:
        from qa.fix_queue import FixQueueManager

        manager = FixQueueManager(os.path.dirname(os.path.abspath(__file__)) + "/fix_queue")
        payload = manager.load_latest()
        if payload is None:
            print("No latest fix queue found.")
            return

        print("\n🩹 Latest Fix Queue")
        print(f"   Run ID: {payload.get('run_id')}")
        print(f"   Generated: {payload.get('generated_at')}")
        print(f"   Open count: {payload.get('open_count')}")
        for item in payload.get("open_items", [])[:10]:
            print(
                "   - "
                f"[{item.get('severity')}] {item.get('rule')} :: "
                f"{item.get('user_message')}"
            )
        return

    if args.audit_reports:
        print("\n🧠 Running Autonomous QA Report Audit...")
        from qa.orchestration.autonomous_qa_system import AutonomousQAOrchestrationSystem

        system = AutonomousQAOrchestrationSystem(os.path.dirname(os.path.abspath(__file__)) + "/..")
        result = system.run(ai_handler, max_scenarios=args.max_scenarios)
        print(f"\n📊 Autonomous QA Summary:")
        print(f"   Artifacts: {result.artifact_count}")
        print(f"   Scenarios replayed: {result.scenario_count}")
        print(f"   Unresolved audit items: {result.unresolved_audit_count}")
        print(f"   Regression free: {'✅' if result.regression_free else '❌'}")
        print(f"   Replay fix rate: {result.replay_fix_rate:.1f}%")
        print(f"   Zero unresolved: {'✅ YES' if result.zero_unresolved else '❌ NO'}")
        print(f"   Report JSON: {result.report_json_path}")
        print(f"   Fix Queue JSON: {result.fix_queue_json_path}")
        return

    if args.regression:
        print("\n🔄 Running Regression Tests...")
        from qa.regression.regression_engine import RegressionEngine
        engine = RegressionEngine()
        result = engine.run_all(ai_handler)
        print(f"\n📊 Regression Results:")
        print(f"   Total: {result['total_tests']} | Pass: {result['passed']} | Fail: {result['failed']}")
        print(f"   Pass Rate: {result['pass_rate']:.1f}%")
        if result['regressions']:
            print(f"   ⚠️  REGRESSIONS: {[r['rule'] for r in result['regressions']]}")
        else:
            print("   ✅ No regressions detected!")
        return

    if args.replay:
        print("\n🔁 Running Replay Engine...")
        from qa.replay.replay_engine import ReplayEngine
        engine = ReplayEngine()
        result = engine.run_replay_batch(ai_handler)
        print(f"\n📊 Replay Results:")
        print(f"   Total: {result['total_replays']} | Fixed: {result['fully_fixed']} | Regressed: {result['regressed']}")
        print(f"   Fix Rate: {result['fix_rate']:.1f}%")
        return

    if args.loop:
        print("\n🔄 Starting Auto-Retry Loop...")
        from qa.auto_retry.retry_loop import AutoRetryLoop, LoopConfig
        config = LoopConfig(
            max_iterations=args.max_iter,
            sessions_per_iteration=args.sessions,
            verbose=args.verbose,
        )
        loop = AutoRetryLoop(config)
        result = loop.run(ai_handler)

        print(f"\n📊 Final Loop Summary:")
        print(f"   Iterations: {result['total_iterations']}")
        print(f"   Zero Audit: {'✅ ACHIEVED' if result['zero_audit_achieved'] else '❌ Not yet'}")
        print(f"   Best Score: {result['best_score']:.1f}/10")
        print(f"   Score Improvement: +{result['score_improvement']:.1f}")
        return

    # Default: single batch
    print(f"\n🧪 Running QA Batch ({args.sessions} sessions)...")
    from qa.orchestration.qa_orchestrator import QAOrchestrator
    from qa.reporting.report_generator import ReportGenerator

    orchestrator = QAOrchestrator()
    reporter = ReportGenerator()

    aggregator = orchestrator.run_batch(
        ai_handler=ai_handler,
        num_sessions=args.sessions,
        verbose=args.verbose,
    )

    summary = aggregator.get_summary()
    run_report = reporter.generate_run_report(
        aggregator,
        run_id=f"qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )

    json_path = reporter.save_json_report(run_report)
    md_path = reporter.save_markdown_report(run_report)

    print(f"\n{'='*60}")
    print(f"📊 QA BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"Sessions: {summary.get('total_sessions', 0)}")
    print(f"Pass Rate: {summary.get('pass_rate', 0):.1f}%")
    print(f"Overall Score: {summary.get('overall_score', 0):.1f}/10 (Grade: {summary.get('grade', '?')})")
    print(f"Violations: {summary.get('total_violations', 0)}")
    print(f"Zero Audit: {'✅ YES!' if aggregator.zero_audit_achieved() else '❌ Not yet'}")
    print(f"\n📄 Reports:")
    print(f"   JSON: {json_path}")
    print(f"   Markdown: {md_path}")

    if run_report.dev_fix_queue:
        print(f"\n🛠️  Top Fix Priorities:")
        for item in run_report.dev_fix_queue[:5]:
            emoji = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡"}.get(item.severity, "⚪")
            print(f"   {emoji} [{item.severity}] {item.rule}: {item.fix_suggestion[:60]}")

    if aggregator.zero_audit_achieved():
        cert = reporter.generate_zero_audit_certificate(run_report.run_id)
        print(f"\n🏆 ZERO AUDIT CERTIFICATE: {cert}")


if __name__ == "__main__":
    main()
