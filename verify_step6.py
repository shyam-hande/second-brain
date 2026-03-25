# verify_step6.py
import asyncio


async def verify():
    print("=" * 50)
    print("STEP 6 VERIFICATION - PII GUARDRAILS")
    print("=" * 50)

    all_good = True

    # Test 1: Imports
    print("\n📦 Import Check:")
    try:
        from src.guardrails.pii_detector import (
            detect_pii, redact_pii, has_pii, get_pii_report
        )
        print("  ✅ pii_detector imported")

        from src.guardrails.guardrail import PIIGuardrail, pii_guardrail
        print("  ✅ guardrail imported")
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return

    # Test 2: PII detection
    print("\n🔍 PII Detection Check:")
    try:
        from src.guardrails.pii_detector import detect_pii, has_pii

        test_cases = [
            ("john@gmail.com", "EMAIL", True),
            ("123-45-6789", "SSN", True),
            ("Call me at 555-123-4567", "PHONE_US", True),
            ("192.168.1.1", "IP_ADDRESS", True),
            ("Hello how are you", None, False),
        ]

        for text, expected_type, should_find in test_cases:
            found = has_pii(text)
            status = "✅" if found == should_find else "❌"
            print(f"  {status} '{text[:30]}' → PII found: {found}")
            if found != should_find:
                all_good = False

    except Exception as e:
        print(f"  ❌ Detection failed: {e}")
        all_good = False

    # Test 3: PII redaction
    print("\n✂️  PII Redaction Check:")
    try:
        from src.guardrails.pii_detector import redact_pii

        test_texts = [
            "Email me at john@example.com please",
            "My SSN is 123-45-6789",
            "Call 555-123-4567 or email test@test.com",
            "No sensitive data here",
        ]

        for text in test_texts:
            redacted, matches = redact_pii(text)
            was_changed = redacted != text
            print(f"  ✅ Input:   {text}")
            print(f"     Output:  {redacted}")
            print(f"     Changed: {was_changed} | Items: {len(matches)}")
            print()

    except Exception as e:
        print(f"  ❌ Redaction failed: {e}")
        all_good = False

    # Test 4: Guardrail processing
    print("\n🛡️  Guardrail Processing Check:")
    try:
        from src.guardrails.guardrail import PIIGuardrail

        guardrail = PIIGuardrail(strict_mode=False)

        # Test redact mode
        msg = "My email is secret@private.com and I need help"
        cleaned, modified = guardrail.process_input(msg)
        print(f"  ✅ Redact mode:")
        print(f"     Input:    {msg}")
        print(f"     Output:   {cleaned}")
        print(f"     Modified: {modified}")

        # Test strict mode
        strict = PIIGuardrail(strict_mode=True)
        blocked, modified = strict.process_input(msg)
        print(f"\n  ✅ Strict mode:")
        print(f"     Blocked: {modified}")
        print(f"     Message: {blocked[:60]}...")

    except Exception as e:
        print(f"  ❌ Guardrail processing failed: {e}")
        all_good = False

    # Test 5: Memory store PII protection
    print("\n💾 Memory PII Protection Check:")
    try:
        from src.memory.memory_store import memory_store
        from src.memory.models import MemoryType

        # Save memory with PII in it
        dirty_content = "User email is sensitive@email.com and SSN 987-65-4321"
        memory = memory_store.save_memory(
            content=dirty_content,
            memory_type=MemoryType.FACT,
            importance=3,
        )

        # Retrieve and check it was cleaned
        all_mem = memory_store.get_all_memories()
        saved = next((m for m in all_mem if m.id == memory.id), None)

        if saved:
            has_email = "sensitive@email.com" in saved.content
            has_ssn = "987-65-4321" in saved.content
            is_clean = not has_email and not has_ssn

            print(f"  ✅ Memory saved with ID: {memory.id[:8]}...")
            print(f"  {'✅' if is_clean else '❌'} PII removed from storage")
            print(f"  ✅ Stored content: {saved.content}")

            if not is_clean:
                all_good = False
        else:
            print("  ❌ Could not retrieve saved memory")
            all_good = False

    except Exception as e:
        print(f"  ❌ Memory PII protection failed: {e}")
        all_good = False

    # Test 6: PII report
    print("\n📊 PII Report Check:")
    try:
        from src.guardrails.pii_detector import get_pii_report

        text = "Contact john@test.com or call 555-987-6543"
        report = get_pii_report(text)

        print(f"  ✅ Has PII: {report['has_pii']}")
        print(f"  ✅ Total found: {report['total_found']}")
        print(f"  ✅ Types: {report['types_found']}")
        print(f"  ✅ Details: {report['details']}")

    except Exception as e:
        print(f"  ❌ PII report failed: {e}")
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 6 Complete! Ready for Step 7 (Multi-Agent System)")
    else:
        print("❌ Fix errors above before Step 7")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())