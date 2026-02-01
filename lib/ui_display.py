"""
UI Display System for Agentic Commit Analysis

Manages real-time display of agent activity in Streamlit.
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime


# Visual indicators
STATUS_ICONS = {
    "pending": "⏳",
    "running": "🔄",
    "success": "✅",
    "error": "❌",
    "cached": "💾",
}

TOOL_ICONS = {
    "git_log_search": "🔍",
    "git_show_commit": "📝",
    "git_blame_file": "👤",
    "git_file_history": "📜",
    "git_diff_commits": "🔀",
    "read_file": "📄",
    "list_directory": "📁",
    "search_in_files": "🔎",
    "find_function_definition": "🎯",
    "get_related_commits": "🔗",
}


class AgentUIDisplay:
    """Manages real-time agent activity display in Streamlit."""

    def __init__(self):
        self.timeline = []
        self.containers = {}
        self.current_tool = None

    def initialize(self):
        """Set up Streamlit containers for agent display."""

        # Main container
        with st.expander("🤖 Agent Activity", expanded=True):
            # Progress tracking
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                self.containers['status_text'] = st.empty()
            with col2:
                self.containers['tool_count'] = st.empty()
            with col3:
                self.containers['elapsed_time'] = st.empty()

            self.containers['progress'] = st.progress(0.0)

            st.markdown("---")

            # Current tool execution
            self.containers['current_tool'] = st.container()

            st.markdown("---")

            # Timeline container
            with st.expander("📋 Tool Execution History", expanded=False):
                self.containers['timeline'] = st.container()

    def update(self, event: Dict[str, Any]):
        """Handle UI update events from tool executor."""

        event_type = event.get('event')

        if event_type == 'tool_start':
            self._handle_tool_start(event)
        elif event_type == 'tool_success':
            self._handle_tool_success(event)
        elif event_type == 'tool_error':
            self._handle_tool_error(event)
        elif event_type == 'agent_thinking':
            self._handle_agent_thinking(event)
        elif event_type == 'agent_complete':
            self._handle_agent_complete(event)

    def _handle_tool_start(self, event: Dict[str, Any]):
        """Display tool execution start."""

        tool_name = event['tool_name']
        command = event.get('command', '')
        total_calls = event.get('total_calls', 0)

        # Update status
        if self.containers.get('status_text'):
            self.containers['status_text'].markdown(
                f"**Status:** {STATUS_ICONS['running']} Running `{tool_name}`"
            )

        if self.containers.get('tool_count'):
            self.containers['tool_count'].metric("Tools Used", total_calls)

        # Show current tool
        if self.containers.get('current_tool'):
            with self.containers['current_tool']:
                icon = TOOL_ICONS.get(tool_name, "🔧")

                cols = st.columns([1, 4, 1])
                cols[0].markdown(f"### {icon}")
                cols[1].markdown(f"**{self._format_tool_name(tool_name)}**")
                cols[2].markdown(f"{STATUS_ICONS['running']}")

                if command:
                    st.code(command, language='bash')

                # Show parameters
                if event.get('parameters'):
                    with st.expander("Parameters", expanded=False):
                        st.json(event['parameters'])

        # Add to timeline
        self.timeline.append({
            **event,
            'status': 'running',
            'timestamp': datetime.now()
        })

        self.current_tool = tool_name

    def _handle_tool_success(self, event: Dict[str, Any]):
        """Display tool execution success."""

        tool_name = event['tool_name']
        duration = event.get('duration', 0)
        result_preview = event.get('result_preview', '')

        # Update status
        if self.containers.get('status_text'):
            self.containers['status_text'].markdown(
                f"**Status:** {STATUS_ICONS['success']} Completed `{tool_name}` in {duration:.2f}s"
            )

        # Update current tool display
        if self.containers.get('current_tool'):
            with self.containers['current_tool']:
                icon = TOOL_ICONS.get(tool_name, "🔧")

                cols = st.columns([1, 4, 1])
                cols[0].markdown(f"### {icon}")
                cols[1].markdown(f"**{self._format_tool_name(tool_name)}**")
                cols[2].markdown(f"{STATUS_ICONS['success']}")

                st.success(f"✓ {result_preview} (took {duration:.2f}s)")

        # Update timeline
        if self.timeline and self.timeline[-1].get('tool_name') == tool_name:
            self.timeline[-1]['status'] = 'success'
            self.timeline[-1]['duration'] = duration
            self.timeline[-1]['result_preview'] = result_preview

        self._update_timeline_display()

    def _handle_tool_error(self, event: Dict[str, Any]):
        """Display tool execution error."""

        tool_name = event['tool_name']
        error = event.get('error', 'Unknown error')

        # Update status
        if self.containers.get('status_text'):
            self.containers['status_text'].markdown(
                f"**Status:** {STATUS_ICONS['error']} Failed `{tool_name}`"
            )

        # Update current tool display
        if self.containers.get('current_tool'):
            with self.containers['current_tool']:
                icon = TOOL_ICONS.get(tool_name, "🔧")

                cols = st.columns([1, 4, 1])
                cols[0].markdown(f"### {icon}")
                cols[1].markdown(f"**{self._format_tool_name(tool_name)}**")
                cols[2].markdown(f"{STATUS_ICONS['error']}")

                st.error(f"✗ Error: {error}")

        # Update timeline
        if self.timeline and self.timeline[-1].get('tool_name') == tool_name:
            self.timeline[-1]['status'] = 'error'
            self.timeline[-1]['error'] = error

        self._update_timeline_display()

    def _handle_agent_thinking(self, event: Dict[str, Any]):
        """Display agent thinking/reasoning."""

        message = event.get('message', 'Thinking...')

        if self.containers.get('status_text'):
            self.containers['status_text'].markdown(
                f"**Status:** 💭 {message}"
            )

    def _handle_agent_complete(self, event: Dict[str, Any]):
        """Display agent completion."""

        if self.containers.get('status_text'):
            self.containers['status_text'].markdown(
                f"**Status:** {STATUS_ICONS['success']} Analysis complete"
            )

        if self.containers.get('progress'):
            self.containers['progress'].progress(1.0)

    def _update_timeline_display(self):
        """Update the timeline display with all tool executions."""

        if not self.containers.get('timeline'):
            return

        with self.containers['timeline']:
            for i, item in enumerate(self.timeline):
                tool_name = item.get('tool_name', 'Unknown')
                status = item.get('status', 'pending')
                timestamp = item.get('timestamp', datetime.now())

                icon = TOOL_ICONS.get(tool_name, "🔧")
                status_icon = STATUS_ICONS.get(status, "⏳")

                # Create timeline entry
                cols = st.columns([1, 3, 2, 1])

                cols[0].markdown(f"{icon}")
                cols[1].markdown(f"**{self._format_tool_name(tool_name)}**")
                cols[2].caption(timestamp.strftime("%H:%M:%S"))
                cols[3].markdown(status_icon)

                # Show result preview or error
                if status == 'success' and item.get('result_preview'):
                    st.caption(f"↳ {item['result_preview']}")
                    if item.get('duration'):
                        st.caption(f"⏱️ {item['duration']:.2f}s")

                elif status == 'error' and item.get('error'):
                    st.caption(f"↳ ❌ {item['error']}")

                if i < len(self.timeline) - 1:
                    st.markdown("---")

    def update_progress(self, current: int, total: int):
        """Update progress bar."""

        if self.containers.get('progress'):
            progress = current / total if total > 0 else 0
            self.containers['progress'].progress(min(progress, 1.0))

        if self.containers.get('tool_count'):
            self.containers['tool_count'].metric("Tools Used", current)

    def update_elapsed_time(self, elapsed: float):
        """Update elapsed time display."""

        if self.containers.get('elapsed_time'):
            self.containers['elapsed_time'].metric("Time", f"{elapsed:.1f}s")

    def _format_tool_name(self, tool_name: str) -> str:
        """Format tool name for display."""

        # Convert snake_case to Title Case
        return ' '.join(word.capitalize() for word in tool_name.split('_'))

    def show_usage_summary(self, usage_data: Dict[str, Any]):
        """Display usage summary."""

        st.markdown("### 📊 Usage Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Tool Calls", usage_data.get('total_calls', 0))

        with col2:
            elapsed = usage_data.get('elapsed_time', 0)
            st.metric("Elapsed Time", f"{elapsed:.1f}s")

        with col3:
            remaining = usage_data.get('global_limit_remaining', 0)
            st.metric("Calls Remaining", remaining)

        # Per-tool usage
        if usage_data.get('per_tool_usage'):
            st.markdown("#### Tool Usage Breakdown")

            for tool_name, count in usage_data['per_tool_usage'].items():
                icon = TOOL_ICONS.get(tool_name, "🔧")
                remaining = usage_data.get('remaining_calls', {}).get(tool_name, 0)

                st.caption(f"{icon} {self._format_tool_name(tool_name)}: {count} calls ({remaining} remaining)")
