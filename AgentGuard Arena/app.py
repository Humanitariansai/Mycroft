import streamlit as st
from profiles import TARGET_PROFILES
from core_swarm import (
    run_researcher,
    seed_target_context,
    run_attacker,
    run_target,
    run_judge,
    run_patcher,
)

st.set_page_config(layout="wide", page_title="AgentGuard Arena", page_icon="🛡️")

# ─── Page Header ─────────────────────────────────────────────────────────────────
st.title("🛡️ AgentGuard Arena")
st.caption(
    "Self-adversarial multi-agent pipeline · "
    "Powered by W&B Inference endpoints · "
    "Fully traced with Weights & Biases Weave"
)
st.divider()


# ─── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    selected_profile = st.selectbox(
        "Target Profile",
        options=list(TARGET_PROFILES.keys()),
        index=0,
    )
    max_rounds = st.slider("Max Rounds", min_value=2, max_value=6, value=3)
    turns_per_round = st.slider(
        "Attacker Turns / Round",
        min_value=1,
        max_value=5,
        value=3,
        help="Multi-turn conversation depth — higher = more trust-escalation, more likely to break the target.",
    )
    context_poisoning = st.checkbox(
        "Context poisoning (prime target)",
        value=True,
        help="Seed the target with a fabricated 'authorized session' before the live turns — "
        "the highest-yield jailbreak against small models.",
    )

    st.divider()
    st.markdown("**Model Assignments**")

    st.markdown("🟣 **Research**")
    st.code("deepseek-ai/DeepSeek-V4-Flash", language=None)
    st.caption("Scrapes live web threat-intel → synthesizes domain attack brief")

    st.markdown("🔴 **Attacker**")
    st.code("nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8", language=None)
    st.caption("120B agentic model — adversarial multi-step reasoning")

    st.markdown("🔵 **Target**")
    st.code("meta-llama/Llama-3.1-8B-Instruct", language=None)
    st.caption("Lightweight 8B — realistic production agent under test")

    st.markdown("⚖️ **Judge**")
    st.code("Qwen/Qwen3-235B-A22B-Instruct-2507", language=None)
    st.caption("235B MoE — structured logical evaluation")

    st.markdown("🟡 **Patcher**")
    st.code("deepseek-ai/DeepSeek-V4-Flash", language=None)
    st.caption("Fast MoE — surgical instruction rewriting")

    st.divider()
    profile_data = TARGET_PROFILES[selected_profile]
    st.markdown(f"**Role:** {profile_data['role']}")

    st.markdown("**Sensitive Data Categories:**")
    for key in profile_data["sensitive_data"]:
        st.markdown(f"- `{key}`")

    st.markdown("**Tools:**")
    for tool in profile_data["tools"]:
        st.markdown(f"- `{tool}`")


# ─── Log Formatting Helpers ───────────────────────────────────────────────────────

def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _log_section(text: str) -> str:
    return (
        '<div style="color:#6e7681;font-family:\'Courier New\',monospace;font-size:11px;'
        'padding:5px 0 2px 0;margin-top:10px;border-top:1px solid #21262d;">'
        f"{_esc(text)}</div>"
    )


def _log_research(intel: dict) -> str:
    preview = _esc(intel["brief"][:360]) + ("…" if len(intel["brief"]) > 360 else "")
    n_sources = len(intel.get("sources", []))
    if intel.get("kb_used"):
        src_note = f"research_kb.md · {n_sources} source(s)"
    else:
        src_note = f"{n_sources} live source(s) scraped" if n_sources else "no live hits — model-knowledge fallback"
    if intel.get("frameworks_used"):
        src_note += " · OWASP+MITRE ATLAS taxonomy"
    return (
        '<div style="background:#1a0a2d;border-left:4px solid #a371f7;'
        'padding:8px 12px;margin:3px 0;border-radius:0 4px 4px 0;'
        'font-family:\'Courier New\',monospace;font-size:12px;line-height:1.5;">'
        f'<span style="color:#a371f7;font-weight:700;">[RESEARCH] (one-time) </span>'
        f'<span style="color:#8b949e;">{src_note}</span><br>'
        f'<span style="color:#d2a8ff;">{preview}</span></div>'
    )


def _log_attack(round_num: int, payload: str) -> str:
    preview = _esc(payload[:320]) + ("…" if len(payload) > 320 else "")
    return (
        '<div style="background:#2d0a0a;border-left:4px solid #f85149;'
        'padding:8px 12px;margin:3px 0;border-radius:0 4px 4px 0;'
        'font-family:\'Courier New\',monospace;font-size:12px;line-height:1.5;">'
        f'<span style="color:#f85149;font-weight:700;">[R{round_num:02d}][ATTACKER] </span>'
        f'<span style="color:#ffa198;">{preview}</span></div>'
    )


def _log_target(round_num: int, response: str) -> str:
    preview = _esc(response[:320]) + ("…" if len(response) > 320 else "")
    return (
        '<div style="background:#0a1929;border-left:4px solid #388bfd;'
        'padding:8px 12px;margin:3px 0;border-radius:0 4px 4px 0;'
        'font-family:\'Courier New\',monospace;font-size:12px;line-height:1.5;">'
        f'<span style="color:#388bfd;font-weight:700;">[R{round_num:02d}][TARGET  ] </span>'
        f'<span style="color:#79c0ff;">{preview}</span></div>'
    )


def _log_judge_vulnerable(round_num: int, evaluation: dict) -> str:
    mechanism = _esc(evaluation["exploit_mechanism"][:140])
    return (
        '<div style="background:#2d0a0a;border-left:4px solid #f85149;'
        'padding:8px 12px;margin:3px 0;border-radius:0 4px 4px 0;'
        'font-family:\'Courier New\',monospace;font-size:12px;line-height:1.5;">'
        f'<span style="color:#f85149;font-weight:700;">[R{round_num:02d}][JUDGE   ] 🔴 VULNERABLE</span>'
        f'<span style="color:#8b949e;"> | Score: {evaluation["severity_score"]}/10 | {mechanism}</span></div>'
    )


def _log_judge_defended(round_num: int, evaluation: dict) -> str:
    mechanism = _esc(evaluation["exploit_mechanism"][:140])
    return (
        '<div style="background:#0a2d0a;border-left:4px solid #3fb950;'
        'padding:8px 12px;margin:3px 0;border-radius:0 4px 4px 0;'
        'font-family:\'Courier New\',monospace;font-size:12px;line-height:1.5;">'
        f'<span style="color:#3fb950;font-weight:700;">[R{round_num:02d}][JUDGE   ] 🟢 DEFENDED  </span>'
        f'<span style="color:#8b949e;"> | Score: {evaluation["severity_score"]}/10 | {mechanism}</span></div>'
    )


def _log_patcher(round_num: int, delta_chars: int) -> str:
    sign = "+" if delta_chars >= 0 else ""
    return (
        '<div style="background:#2d2a0a;border-left:4px solid #e3b341;'
        'padding:8px 12px;margin:3px 0;border-radius:0 4px 4px 0;'
        'font-family:\'Courier New\',monospace;font-size:12px;line-height:1.5;">'
        f'<span style="color:#e3b341;font-weight:700;">[R{round_num:02d}][PATCHER ] </span>'
        f'<span style="color:#f0cf7a;">Prompt hardened. '
        f'<b>{sign}{delta_chars}</b> chars appended to system prompt.</span></div>'
    )


def _log_defense_streak(round_num: int, streak: int) -> str:
    return (
        '<div style="background:#0a2d0a;border-left:4px solid #3fb950;'
        'padding:8px 12px;margin:3px 0;border-radius:0 4px 4px 0;'
        'font-family:\'Courier New\',monospace;font-size:12px;line-height:1.5;">'
        f'<span style="color:#3fb950;font-weight:700;">[R{round_num:02d}][DEFENSE ] </span>'
        f'<span style="color:#7ee787;">Attack deflected! Consecutive defenses: '
        f'<b>{streak}</b> — attacker will try a new vector next round.</span></div>'
    )


def _render_log(lines: list, placeholder) -> None:
    body = "".join(lines)
    html = (
        '<div style="background:#0d1117;color:#c9d1d9;'
        'font-family:\'Courier New\',Courier,monospace;'
        'padding:14px;border-radius:8px;border:1px solid #30363d;'
        'max-height:560px;overflow-y:auto;font-size:12px;line-height:1.55;">'
        f"{body}</div>"
    )
    placeholder.markdown(html, unsafe_allow_html=True)


def _render_metrics(placeholder, score: int, round_num: int, max_rounds: int, is_vuln: bool) -> None:
    with placeholder.container():
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Severity Score",
            f"{score}/10",
            help="0 = fully defended · 10 = fully compromised",
        )
        m2.metric("Round", f"{round_num} / {max_rounds}")
        m3.metric("Status", "🔴 VULNERABLE" if is_vuln else "🟢 DEFENDED")


def _render_diff(placeholder, old_prompt: str, new_prompt: str) -> None:
    with placeholder.container():
        d1, d2 = st.columns(2)
        with d1:
            st.caption("Before Patch")
            st.code(old_prompt, language=None)
        with d2:
            st.caption("After Patch")
            st.code(new_prompt, language=None)


# ─── Main Two-Column Layout ───────────────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="medium")

with col_left:
    st.subheader("🔴 Live Security War Room")
    launch_btn = st.button(
        "⚡ LAUNCH ADVERSARIAL SWARM RUN",
        type="primary",
        use_container_width=True,
    )
    log_placeholder = st.empty()

with col_right:
    st.subheader("📊 Hardening Metrics")
    metrics_placeholder = st.empty()
    st.divider()
    st.caption("Prompt Mutation Tracker")
    diff_placeholder = st.empty()

# Initial idle state
_render_log(
    [
        '<div style="color:#6e7681;padding:8px 0;font-family:monospace;font-size:12px;">'
        "⚡ Press LAUNCH to begin adversarial swarm run…</div>"
    ],
    log_placeholder,
)
metrics_placeholder.info("Run a swarm to see live metrics.")
diff_placeholder.info("No patches applied yet — diff will appear after first exploit.")


# ─── Adversarial Loop ─────────────────────────────────────────────────────────────
if launch_btn:
    profile_data = TARGET_PROFILES[selected_profile]
    current_prompt = profile_data["baseline_prompt"]

    history = []
    consecutive_defenses = 0
    initial_severity = None
    last_severity = 0
    last_vulnerable = False
    log_lines = []
    final_round = 0

    log_lines.append(
        _log_section(
            f"AgentGuard Arena  ·  Profile: {selected_profile}  ·  Max Rounds: {max_rounds}"
        )
    )
    _render_log(log_lines, log_placeholder)

    # ── Research (runs ONCE — intel is reused by the attacker across all rounds) ───
    with st.spinner("🟣 Research agent gathering threat-intel (one-time)…"):
        intel = run_researcher(profile_data, [], selected_profile)

    log_lines.append(_log_research(intel))
    _render_log(log_lines, log_placeholder)

    for round_num in range(1, max_rounds + 1):
        final_round = round_num
        log_lines.append(_log_section(f"Round {round_num} / {max_rounds}"))
        _render_log(log_lines, log_placeholder)

        # ── Multi-turn engagement: attacker ↔ target ───────────────────────────────
        # The attacker and target actually converse for several turns so trust
        # escalation, many-shot priming and context poisoning can land.
        target_conv = []          # target's perspective: user=attacker, assistant=target
        round_attacks = []
        round_responses = []

        # Context poisoning: seed the target with a fabricated 'authorized session'.
        # These primer turns are NOT counted as real breaches by the judge.
        if context_poisoning:
            with st.spinner(f"🔴 Attacker priming target context (round {round_num})…"):
                primer = seed_target_context(profile_data, intel)
            if primer:
                target_conv.extend(primer)
                log_lines.append(
                    _log_section(f"Context-poisoning primer injected: {len(primer)} fabricated turn(s)")
                )
                _render_log(log_lines, log_placeholder)

        for turn in range(1, turns_per_round + 1):
            with st.spinner(f"🔴 Attacker — round {round_num}, turn {turn}/{turns_per_round}…"):
                attack_payload = run_attacker(profile_data, history, intel, target_conv)
            target_conv.append({"role": "user", "content": attack_payload})
            round_attacks.append(attack_payload)
            log_lines.append(_log_attack(round_num, f"(turn {turn}) {attack_payload}"))
            _render_log(log_lines, log_placeholder)

            with st.spinner(f"🔵 Target ({selected_profile}) — round {round_num}, turn {turn}…"):
                target_response = run_target(current_prompt, target_conv)
            target_conv.append({"role": "assistant", "content": target_response})
            round_responses.append(target_response)
            log_lines.append(_log_target(round_num, f"(turn {turn}) {target_response}"))
            _render_log(log_lines, log_placeholder)

        # Collapse the multi-turn exchange into blobs for the judge and history.
        attack_payload = "\n\n".join(f"[Turn {i}] {a}" for i, a in enumerate(round_attacks, 1))
        target_response = "\n\n".join(f"[Turn {i}] {r}" for i, r in enumerate(round_responses, 1))

        # ── Judge (evaluates the full multi-turn exchange) ──────────────────────────
        with st.spinner("⚖️ Judge evaluating the full exchange for security breach…"):
            evaluation = run_judge(attack_payload, target_response, profile_data)

        if initial_severity is None:
            initial_severity = evaluation["severity_score"]
        last_severity = evaluation["severity_score"]
        last_vulnerable = evaluation["vulnerable"]

        if evaluation["vulnerable"]:
            log_lines.append(_log_judge_vulnerable(round_num, evaluation))
        else:
            log_lines.append(_log_judge_defended(round_num, evaluation))

        _render_log(log_lines, log_placeholder)
        _render_metrics(metrics_placeholder, last_severity, round_num, max_rounds, last_vulnerable)

        history.append(
            {
                "round": round_num,
                "attack": attack_payload,
                "target_response": target_response,
                "evaluation": evaluation,
            }
        )

        if evaluation["vulnerable"]:
            consecutive_defenses = 0
            old_prompt = current_prompt

            # ── Patcher ───────────────────────────────────────────────────────────
            with st.spinner("🟡 Patcher surgically hardening system prompt…"):
                current_prompt = run_patcher(current_prompt, evaluation, profile_data)

            delta = len(current_prompt) - len(old_prompt)
            log_lines.append(_log_patcher(round_num, delta))
            _render_log(log_lines, log_placeholder)
            _render_diff(diff_placeholder, old_prompt, current_prompt)

        else:
            consecutive_defenses += 1
            log_lines.append(_log_defense_streak(round_num, consecutive_defenses))
            _render_log(log_lines, log_placeholder)
            # No early stop: the attacker keeps probing for new vectors every round,
            # even after consecutive defenses, until max_rounds is reached.
    else:
        log_lines.append(
            _log_section(f"⏹ Max rounds ({max_rounds}) reached — run complete")
        )
        _render_log(log_lines, log_placeholder)

    # ─── Hardening Summary ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Hardening Summary")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Rounds Completed", final_round)
    s2.metric("Initial Severity", f"{initial_severity if initial_severity is not None else 0}/10")
    s3.metric("Final Severity", f"{last_severity}/10")
    improvement = (initial_severity if initial_severity is not None else 0) - last_severity
    s4.metric(
        "Score Improvement",
        f"{improvement:+d} pts",
        delta=f"{improvement:+d}",
        delta_color="normal",
    )

    st.text_area(
        "Final Hardened System Prompt",
        value=current_prompt,
        height=320,
        disabled=True,
    )

    st.balloons()
