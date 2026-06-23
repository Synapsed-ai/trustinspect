from __future__ import annotations

from typing import Any, Mapping, Optional

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.box import HEAVY


TI_THEME = Theme(
    {
        "ti.banner": "#39ff14 bold",
        "ti.title": "#39ff14 bold",
        "ti.subtitle": "#98FB98",
        "ti.label": "#7CFC00 bold",
        "ti.value": "#D7FFD7",
        "ti.dim": "#6B8E6B",
        "ti.safe": "#39ff14 bold",
        "ti.possible": "#FFD75F bold",
        "ti.vuln": "#FF5F5F bold",
        "ti.error": "#FF875F bold",
        "ti.prompt": "#98FB98",
        "ti.response": "#D7FFD7",
    }
)


def make_console() -> Console:
    return Console(theme=TI_THEME)


BANNER = r"""
████████╗██████╗ ██╗   ██╗███████╗████████╗██╗███╗   ██╗███████╗██████╗ ███████╗ ██████╗████████╗
╚══██╔══╝██╔══██╗██║   ██║██╔════╝╚══██╔══╝██║████╗  ██║██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝
   ██║   ██████╔╝██║   ██║███████╗   ██║   ██║██╔██╗ ██║███████╗██████╔╝█████╗  ██║        ██║
   ██║   ██╔══██╗██║   ██║╚════██║   ██║   ██║██║╚██╗██║╚════██║██╔═══╝ ██╔══╝  ██║        ██║
   ██║   ██║  ██║╚██████╔╝███████║   ██║   ██║██║ ╚████║███████║██║     ███████╗╚██████╗   ██║
   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝
"""


def trim_text(value: Optional[str], limit: int = 900) -> str:
    value = value or ""
    if limit is None or limit <= 0:
        return value
    if len(value) <= limit:
        return value
    return value[:limit] + "\n... [truncated] ..."


def _status_style(status: str) -> str:
    status = (status or "").upper()
    if status == "SAFE":
        return "ti.safe"
    if status in {"POSSIBLE", "POSSIBLE VULNERABILITY"}:
        return "ti.possible"
    if status == "VULNERABILITY":
        return "ti.vuln"
    if status == "ERROR":
        return "ti.error"
    return "ti.value"


def render_banner(console: Console, license_name: str = "Apache-2.0", version: str = "v0.2.0") -> None:
    console.print(Text(BANNER, style="ti.banner"))

    meta = Text()
    meta.append("Evidence-Based Trustworthy AI Testing for LLM and Agentic Applications\n", style="ti.subtitle")
    meta.append("by Synapsed AI Lab", style="ti.value")
    meta.append("  •  ", style="ti.dim")
    meta.append(f"Open Source License: {license_name}", style="ti.value")
    meta.append("  •  ", style="ti.dim")
    meta.append(version, style="ti.value")
    meta.append("\nBlackHat Arsenal build", style="ti.title")

    console.print(
        Panel(
            meta,
            title="[ti.title]TRUSTINSPECT[/ti.title]",
            border_style="ti.title",
            box=HEAVY,
            padding=(1, 2),
        )
    )


def render_target_panel(
    console: Console,
    target_name: str,
    url: str,
    mode: str,
    test_cases: str,
    started_at: str,
) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="ti.label", justify="left", width=14)
    table.add_column(style="ti.value", justify="left")

    table.add_row("Target", str(target_name))
    table.add_row("URL", str(url))
    table.add_row("Mode", str(mode))
    table.add_row("Test cases", str(test_cases))
    table.add_row("Started", str(started_at))

    console.print(
        Panel(
            table,
            title="[ti.title]Assessment Target[/ti.title]",
            border_style="ti.title",
            box=HEAVY,
            padding=(1, 2),
        )
    )


def render_test_start(
    console: Console,
    index: int,
    total: int,
    test_id: str,
    test_name: str,
    category: Optional[str] = None,
    source: Optional[str] = None,
    parent: Optional[str] = None,
    layer: Optional[str] = None,
) -> None:
    console.print()
    console.print(
        Rule(
            f"[ti.title][{index}/{total}] {test_id} — {test_name}[/ti.title]",
            style="ti.title",
        )
    )

    table = Table.grid(padding=(0, 3))
    table.add_column(style="ti.label")
    table.add_column(style="ti.value")
    if source:
        table.add_row("Source", str(source).upper())
    if parent:
        table.add_row("Parent", str(parent))
    if layer:
        table.add_row("Layer", str(layer))
    if category:
        table.add_row("Category", str(category))
    table.add_row("Executed", str(max(index - 1, 0)))
    table.add_row("Remaining", str(max(total - index + 1, 0)))
    console.print(table)


def render_prompt_response(
    console: Console,
    prompt: str,
    response: str,
    prompt_chars: int = 700,
    response_chars: int = 900,
) -> None:
    console.print(
        Panel(
            trim_text(prompt, prompt_chars),
            title="[ti.label]PROMPT[/ti.label]",
            border_style="ti.label",
            box=HEAVY,
            padding=(1, 2),
            style="ti.prompt",
        )
    )

    console.print(
        Panel(
            trim_text(response, response_chars),
            title="[ti.title]RESPONSE[/ti.title]",
            border_style="ti.title",
            box=HEAVY,
            padding=(1, 2),
            style="ti.response",
        )
    )


def render_result(
    console: Console,
    status: str,
    confidence: float,
    rationale: str,
    index: int,
    total: int,
) -> None:
    status = status or "UNKNOWN"
    status_style = _status_style(status)

    table = Table.grid(padding=(0, 2))
    table.add_column(style="ti.label", width=14)
    table.add_column(style="ti.value")

    try:
        confidence_text = f"{float(confidence):.2f}"
    except Exception:
        confidence_text = "0.00"

    table.add_row("Status", f"[{status_style}]{status}[/{status_style}]")
    table.add_row("Confidence", confidence_text)
    table.add_row("Executed", str(index))
    table.add_row("Remaining", str(max(total - index, 0)))
    table.add_row("Rationale", rationale or "-")

    console.print(
        Panel(
            table,
            border_style=status_style,
            box=HEAVY,
            padding=(1, 2),
        )
    )


def render_final_summary(
    console: Console,
    total: int,
    effective: int,
    vulnerabilities: int,
    possible: int,
    safe: int,
    errors: int,
    output_path: str,
) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="ti.label", width=18)
    table.add_column(style="ti.value")

    table.add_row("Total tests", str(total))
    table.add_row("Effective tests", str(effective))
    table.add_row("Vulnerabilities", f"[ti.vuln]{vulnerabilities}[/ti.vuln]")
    table.add_row("Possible", f"[ti.possible]{possible}[/ti.possible]")
    table.add_row("Safe", f"[ti.safe]{safe}[/ti.safe]")
    table.add_row("Errors", f"[ti.error]{errors}[/ti.error]")
    table.add_row("Report", str(output_path))

    console.print()
    console.print(
        Panel(
            table,
            title="[ti.title]Assessment Completed[/ti.title]",
            border_style="ti.title",
            box=HEAVY,
            padding=(1, 2),
        )
    )


def render_progress_event(
    console: Console,
    event: Mapping[str, Any],
    prompt_chars: int = 700,
    response_chars: int = 900,
) -> None:
    event_type = str(event.get("type") or event.get("event") or "")
    index = int(event.get("index") or 0)
    total = int(event.get("total") or 0)

    if event_type in {"test_start", "start_test", "before_test"}:
        render_test_start(
            console=console,
            index=index,
            total=total,
            test_id=str(event.get("test_id") or event.get("id") or ""),
            test_name=str(event.get("test_name") or event.get("name") or ""),
            category=event.get("category"),
            source=event.get("source"),
            parent=event.get("parent_static_test_id") or event.get("parent"),
            layer=event.get("aitg_layer") or event.get("layer"),
        )

        prompt = event.get("prompt")
        if prompt:
            console.print(
                Panel(
                    trim_text(str(prompt), prompt_chars),
                    title="[ti.label]PROMPT[/ti.label]",
                    border_style="ti.label",
                    box=HEAVY,
                    padding=(1, 2),
                    style="ti.prompt",
                )
            )

    elif event_type in {"test_result", "test_complete", "after_test"}:
        prompt = str(event.get("prompt") or "")
        response = str(event.get("response") or event.get("error") or event.get("message") or "")
        render_prompt_response(
            console=console,
            prompt=prompt,
            response=response,
            prompt_chars=prompt_chars,
            response_chars=response_chars,
        )

        render_result(
            console=console,
            status=str(event.get("classification") or event.get("status") or "UNKNOWN"),
            confidence=float(event.get("confidence") or 0.0),
            rationale=str(event.get("rationale") or event.get("analysis") or event.get("message") or ""),
            index=index,
            total=total,
        )

    elif event_type in {"error", "test_error"}:
        console.print(
            Panel(
                str(event.get("error") or event.get("message") or "Unknown error"),
                title="[ti.error]ERROR[/ti.error]",
                border_style="ti.error",
                box=HEAVY,
                padding=(1, 2),
            )
        )


class TerminalUI:
    """Terminal renderer used by CLI and scanner progress callbacks.

    This class intentionally exposes several aliases because the CLI evolved
    across patches.  The UI layer should never break an assessment run.
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        prompt_chars: int = 700,
        response_chars: int = 900,
        quiet: bool = False,
        quiet_ui: bool = False,
        no_banner: bool = False,
        license_name: str = "Apache-2.0",
        version: str = "v0.2.0",
        **_: Any,
    ) -> None:
        self.console = console or make_console()
        self.prompt_chars = prompt_chars
        self.response_chars = response_chars
        self.quiet = bool(quiet or quiet_ui)
        self.no_banner = no_banner
        self.license_name = license_name
        self.version = version

    def handle_event(self, event: Mapping[str, Any]) -> None:
        if self.quiet:
            return
        try:
            render_progress_event(
                self.console,
                event,
                prompt_chars=self.prompt_chars,
                response_chars=self.response_chars,
            )
        except Exception as exc:  # pragma: no cover - UI must never stop scans
            try:
                self.console.print(f"[ti.dim]UI event rendering skipped: {exc}[/ti.dim]")
            except Exception:
                pass


    def render_progress_event(self, event):
        """Backward-compatible alias for older tests/callers.

        The canonical scanner callback is handle_event(), but public tests and
        some older CLI code call render_progress_event(). Both should work.
        """
        return self.handle_event(event)

    # Newer CLI calls ui.banner(...); older code used render_banner(...).
    def banner(self, version: Optional[str] = None, license_name: Optional[str] = None, **_: Any) -> None:
        self.render_banner(license_name=license_name, version=version)

    def render_banner(self, license_name: Optional[str] = None, version: Optional[str] = None, **_: Any) -> None:
        if not self.no_banner and not self.quiet:
            render_banner(self.console, license_name or self.license_name, version or self.version)

    def target_panel(self, target_name: str, url: str, mode: str, test_cases: str, started_at: str, **_: Any) -> None:
        self.render_target_panel(target_name, url, mode, test_cases, started_at)

    def render_target_panel(self, target_name: str, url: str, mode: str, test_cases: str, started_at: str, **_: Any) -> None:
        if not self.quiet:
            render_target_panel(self.console, target_name, url, mode, test_cases, started_at)

    def final_summary(
        self,
        total: int,
        effective: int,
        vulnerabilities: int,
        possible: int,
        safe: int,
        errors: int,
        output_path: str,
        **_: Any,
    ) -> None:
        self.render_final_summary(total, effective, vulnerabilities, possible, safe, errors, output_path)

    def render_final_summary(
        self,
        total: int,
        effective: int,
        vulnerabilities: int,
        possible: int,
        safe: int,
        errors: int,
        output_path: str,
        **_: Any,
    ) -> None:
        if not self.quiet:
            render_final_summary(self.console, total, effective, vulnerabilities, possible, safe, errors, output_path)

    def info(self, message: str) -> None:
        if not self.quiet:
            self.console.print(str(message), style="ti.value")

    def warning(self, message: str) -> None:
        if not self.quiet:
            self.console.print(str(message), style="ti.possible")

    def error(self, message: str) -> None:
        if not self.quiet:
            self.console.print(str(message), style="ti.error")

# --- TrustInspect flexible TerminalUI.target_panel compatibility patch ---
def _ti_terminalui_target_panel_flexible(self, *args, **kwargs):
    """Render the assessment target panel.

    This compatibility wrapper supports both historical call styles used by
    TrustInspect during the v0.3-alpha refactor:

      target_panel(target_name, url, mode, test_cases, started_at=None)
      target_panel(url, target_name, test_cases, mode="adaptive-web-ui")

    The second form previously caused:
      TypeError: target_panel() got multiple values for argument 'mode'
    when the method signature had a positional `mode` parameter.
    """
    from datetime import datetime, timezone
    from rich.panel import Panel
    from rich.table import Table
    from rich.box import HEAVY

    def _is_url(value):
        value = str(value or "")
        return value.startswith("http://") or value.startswith("https://")

    mode = kwargs.pop("mode", None)
    started_at = kwargs.pop("started_at", None) or kwargs.pop("started", None)
    test_cases = kwargs.pop("test_cases", None)
    target_name = kwargs.pop("target_name", None) or kwargs.pop("target", None)
    url = kwargs.pop("url", None) or kwargs.pop("target_url", None)

    # New CLI call style:
    #   target_panel(args.target_url, target.name, str(generated_output), mode="adaptive-web-ui")
    if len(args) >= 3 and mode is not None:
        url = url or args[0]
        target_name = target_name or args[1]
        test_cases = test_cases or args[2]

    # Legacy style:
    #   target_panel(target_name, url, mode, test_cases, started_at)
    elif len(args) >= 4:
        target_name = target_name or args[0]
        url = url or args[1]
        mode = mode or args[2]
        test_cases = test_cases or args[3]
        if len(args) >= 5:
            started_at = started_at or args[4]

    # Ambiguous 3-argument style.
    elif len(args) == 3:
        if _is_url(args[0]):
            url = url or args[0]
            target_name = target_name or args[1]
            test_cases = test_cases or args[2]
        else:
            target_name = target_name or args[0]
            url = url or args[1]
            test_cases = test_cases or args[2]

    elif len(args) == 2:
        if _is_url(args[0]):
            url = url or args[0]
            target_name = target_name or args[1]
        else:
            target_name = target_name or args[0]
            url = url or args[1]

    mode = mode or "web-ui"
    target_name = str(target_name or "-")
    url = str(url or "-")
    test_cases = str(test_cases or "-")

    if started_at is None:
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    elif hasattr(started_at, "strftime"):
        started_at = started_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        started_at = str(started_at)

    console = getattr(self, "console", None)
    if console is None:
        try:
            console = make_console()
        except Exception:
            from rich.console import Console
            console = Console()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold #71ff5d", justify="left", width=14)
    table.add_column(style="#f8fbff", justify="left")
    table.add_row("Target", target_name)
    table.add_row("URL", url)
    table.add_row("Mode", mode)
    table.add_row("Test cases", test_cases)
    table.add_row("Started", started_at)

    console.print(
        Panel(
            table,
            title="[bold #71ff5d]Assessment Target[/bold #71ff5d]",
            border_style="#71ff5d",
            box=HEAVY,
            padding=(1, 2),
        )
    )

# Always assign the flexible implementation; this is safe and idempotent.
try:
    TerminalUI.target_panel = _ti_terminalui_target_panel_flexible
except NameError:
    pass
# --- end TrustInspect flexible TerminalUI.target_panel compatibility patch ---

# --- TrustInspect realtime progress compatibility patch ---
# This block is intentionally self-contained: it normalizes progress events coming
# from different scanner versions and renders them in the CLI without breaking scans.
def _ti_safe_trim(value, limit=900):
    value = "" if value is None else str(value)
    if len(value) <= limit:
        return value
    return value[:limit] + "\n... [truncated] ..."


def _ti_event_value(event, *names, default=None):
    if event is None:
        return default
    if isinstance(event, dict):
        for name in names:
            if name in event and event.get(name) is not None:
                return event.get(name)
        return default
    for name in names:
        if hasattr(event, name):
            value = getattr(event, name)
            if value is not None:
                return value
    return default


def _ti_status_style(status):
    status = (status or "").upper()
    if status == "VULNERABILITY":
        return "bold red"
    if "POSSIBLE" in status:
        return "bold yellow"
    if status == "SAFE":
        return "bold green"
    if status == "ERROR":
        return "bold orange1"
    return "bold white"


def _ti_render_live_event(self, event):
    try:
        from rich.panel import Panel
        from rich.table import Table
        from rich.rule import Rule
        from rich.box import ROUNDED
    except Exception:
        return

    console = getattr(self, "console", None)
    if console is None:
        return

    event_type = str(_ti_event_value(event, "type", "event", default="")).lower()
    idx = int(_ti_event_value(event, "index", "idx", default=0) or 0)
    total = int(_ti_event_value(event, "total", default=0) or 0)
    test_id = str(_ti_event_value(event, "test_id", "id", default=""))
    test_name = str(_ti_event_value(event, "test_name", "name", default=""))
    source = str(_ti_event_value(event, "source", default=""))
    parent = str(_ti_event_value(event, "parent", "parent_static_test_id", default=""))
    layer = str(_ti_event_value(event, "layer", "aitg_layer", default=""))
    category = str(_ti_event_value(event, "category", default=""))
    prompt = _ti_event_value(event, "prompt", "payload", default="")
    response = _ti_event_value(event, "response", default="")
    rationale = _ti_event_value(event, "rationale", "analysis", default="")
    status = str(_ti_event_value(event, "classification", "status", default=""))
    confidence = _ti_event_value(event, "confidence", default=None)

    prompt_chars = int(getattr(self, "prompt_chars", 700) or 700)
    response_chars = int(getattr(self, "response_chars", 900) or 900)

    if event_type in {"test_start", "start_test", "before_test"}:
        title = f"[{idx}/{total}] {test_id} — {test_name}" if total else f"{test_id} — {test_name}"
        console.print(Rule(title, style="bold green"))

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold green", width=12)
        table.add_column(style="white")
        table.add_row("Source", source or "static")
        if parent:
            table.add_row("Parent", parent)
        if layer:
            table.add_row("Layer", layer)
        if category:
            table.add_row("Category", category)
        if total:
            table.add_row("Executed", str(max(idx - 1, 0)))
            table.add_row("Remaining", str(max(total - idx + 1, 0)))
        console.print(Panel(table, title="Test Metadata", border_style="green", box=ROUNDED))

        if prompt:
            console.print(Panel(_ti_safe_trim(prompt, prompt_chars), title="PROMPT", border_style="green", box=ROUNDED))
        return

    if event_type in {"test_result", "test_complete", "after_test", "result"}:
        if response:
            console.print(Panel(_ti_safe_trim(response, response_chars), title="RESPONSE", border_style="green", box=ROUNDED))

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold green", width=12)
        table.add_column(style="white")
        table.add_row("Status", f"[{_ti_status_style(status)}]{status or 'UNKNOWN'}[/{_ti_status_style(status)}]")
        if confidence is not None:
            try:
                table.add_row("Confidence", f"{float(confidence):.2f}")
            except Exception:
                table.add_row("Confidence", str(confidence))
        if total:
            table.add_row("Executed", str(idx))
            table.add_row("Remaining", str(max(total - idx, 0)))
        if rationale:
            table.add_row("Rationale", _ti_safe_trim(rationale, 350))
        console.print(Panel(table, title="RESULT", border_style=_ti_status_style(status), box=ROUNDED))
        return

    if event_type in {"error", "test_error"}:
        message = _ti_event_value(event, "error", "message", "rationale", default="Unknown error")
        console.print(Panel(str(message), title="ERROR", border_style="red", box=ROUNDED))


# Attach / override aliases expected by different CLI versions.
try:
    TerminalUI.handle_event = _ti_render_live_event
    TerminalUI.render_progress_event = _ti_render_live_event
except NameError:
    pass
# --- end TrustInspect realtime progress compatibility patch ---

