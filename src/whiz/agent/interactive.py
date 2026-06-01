"""Interactive mode: async I/O event loop with mid-session steering."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from whiz.models.base import BaseModel
from whiz.agent.loop import SessionResult, SessionEvent, SYSTEM_PROMPT
from whiz.agent.loop_base import SubLLMManager
from whiz.agent.code_extraction import extract_code
from whiz.agent.tools import inject_tools
from whiz.logging.trajectory import TrajectoryLogger
from whiz.context.indexer import CodebaseIndex
from whiz.repl.core import LocalREPL
from whiz.agent.compaction import CompactionTrigger, Compactor


console = Console()


class InteractiveSession:
    """An interactive session with a REPL-like user interface.

    Presents the agent's work in real-time and allows mid-session steering.
    """

    def __init__(
        self,
        model: BaseModel,
        project_root: Path,
        max_rounds: int = 100,
        max_recursion_depth: int = 5,
        compaction_threshold: int = 4000,
        verbose: bool = False,
        log_dir: Path | None = None,
    ):
        self.model = model
        self.project_root = Path(project_root).resolve()
        self.max_rounds = max_rounds
        self.max_recursion_depth = max_recursion_depth
        self.compaction_threshold = compaction_threshold
        self.verbose = verbose
        self.log_dir = log_dir
        self._steering_queue: asyncio.Queue[str] = asyncio.Queue()
        self._running = False
        self._trajectory: list[SessionEvent] = []

    async def run(self, initial_prompt: str) -> SessionResult:
        """Run an interactive session with the given initial prompt."""
        self._running = True
        self._trajectory = []

        logger = TrajectoryLogger(log_dir=self.log_dir, verbose=self.verbose)

        index = CodebaseIndex.from_root(self.project_root)
        repl = LocalREPL(max_output_lines=100)

        variables = index.to_repl_variables()
        variables["user_prompt"] = initial_prompt
        for name, value in variables.items():
            repl._namespace[name] = value

        recursion_mgr = SubLLMManager(max_depth=self.max_recursion_depth)
        inject_tools(
            repl=repl,
            model=self.model,
            project_root=self.project_root,
            recursion_mgr=recursion_mgr,
            max_rounds=self.max_rounds,
        )

        compaction_trigger = CompactionTrigger(threshold=self.compaction_threshold)
        compactor = Compactor(model=self.model)

        console.print(Panel(
            f"[bold]Whiz[/bold] v0.1.0 | Project: [cyan]{self.project_root.name}[/cyan] | "
            f"Project: [cyan]{self.project_root}[/cyan]",
            title="Interactive Session",
            border_style="blue",
        ))
        console.print(f"[dim]Type your prompt below. Use 'stop' to cancel. Use 'steer <msg>' to redirect.[/dim]\n")

        # Show the initial prompt
        console.print(f"[bold green]>[/bold green] {initial_prompt}\n")

        input_task = asyncio.create_task(self._input_listener())

        try:
            for round_num in range(1, self.max_rounds + 1):
                if not self._running:
                    break

                # Check for steering messages
                steer_msg = self._check_steering()
                if steer_msg:
                    repl._namespace["_user_steer"] = steer_msg
                    console.print(f"[bold yellow]↳ Steering:[/bold yellow] {steer_msg}\n")

                if compaction_trigger.should_compact(repl):
                    compactor.compact(repl)
                    console.print("[dim]⚡ Context compacted[/dim]\n")

                # Build messages and call LLM
                messages = self._build_messages(repl)
                try:
                    response = self.model.chat_completion(messages, model="")
                except Exception as e:
                    console.print(f"[bold red]Error:[/bold red] {e}")
                    return SessionResult(
                        success=False, value=None, rounds=round_num,
                        trajectory=list(self._trajectory), error=f"LLM error: {e}",
                    )

                code = extract_code(response.content)
                if code is None:
                    continue

                # Show the agent's code
                console.print(Panel(
                    f"[dim]{code}[/dim]",
                    title=f"[bold]Round {round_num}[/bold]",
                    border_style="green",
                ))

                raw_output = repl.exec_code(code)

                has_error = False
                error_msg = None
                try:
                    entry = repl.history[-1]
                    if entry.has_error:
                        has_error = True
                        error_msg = entry.error
                except IndexError:
                    pass

                event = SessionEvent(
                    round_num=round_num, code=code,
                    output=raw_output, error=error_msg,
                )
                self._trajectory.append(event)

                if has_error:
                    console.print(f"[bold red]✗ Error:[/bold red] {error_msg}\n")
                else:
                    output = raw_output.strip()
                    if output:
                        console.print(f"[bold]Output:[/bold] {output}\n")

                # Check for completion
                ns = repl.get_namespace()
                if "_done" in ns:
                    value = ns.get("_done_value")
                    console.print(Panel(
                        f"[bold green]{value}[/bold green]",
                        title="✓ Complete",
                        border_style="green",
                    ))
                    logger.save()
                    return SessionResult(
                        success=True, value=value, rounds=round_num,
                        trajectory=list(self._trajectory),
                    )

                # Prompt for user input between rounds
                console.print("[dim]Press Enter to continue, type a message to steer, or 'stop' to cancel...[/dim]")

            logger.save()
            console.print("[bold yellow]⚠ Max rounds reached[/bold yellow]")
            return SessionResult(
                success=False, value=None, rounds=self.max_rounds,
                trajectory=list(self._trajectory),
                error=f"Max rounds ({self.max_rounds}) exceeded",
            )

        except asyncio.CancelledError:
            logger.save()
            return SessionResult(
                success=False, value=None, rounds=0,
                trajectory=list(self._trajectory),
                error="Session cancelled by user",
            )
        finally:
            self._running = False
            input_task.cancel()

    async def _input_listener(self):
        """Background task that reads user input from stdin."""
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                stripped = line.strip()
                if stripped:
                    if stripped.lower() == "stop":
                        self._running = False
                        break
                    elif stripped.lower().startswith("steer "):
                        await self._steering_queue.put(stripped[6:])
                    else:
                        await self._steering_queue.put(stripped)
            except (EOFError, asyncio.CancelledError):
                break

    def _check_steering(self) -> str | None:
        try:
            return self._steering_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def steer(self, message: str) -> None:
        try:
            self._steering_queue.put_nowait(message)
        except asyncio.QueueFull:
            pass

    def cancel(self) -> None:
        self._running = False

    def _build_messages(self, repl) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for entry in repl.history:
            if entry.code.strip():
                messages.append({"role": "assistant", "content": entry.code})
            output = entry.output
            if entry.has_error:
                output = f"Error: {entry.error}"
            if output.strip():
                messages.append({"role": "user", "content": output})
        return messages
